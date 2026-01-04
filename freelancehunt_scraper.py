"""Scraper module for parsing Freelancehunt projects."""
import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional, Union
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
import time
import logging
import config
from database import Database

logger = logging.getLogger(__name__)


class FreelancehuntScraper:
    """Scraper for Freelancehunt projects page."""
    
    def __init__(self, db: Database, session: requests.Session = None, browser=None):
        """Initialize scraper with database, session, and optional browser."""
        self.db = db
        self.session = session or requests.Session()
        self.browser = browser  # BrowserAutomation instance
        self.base_url = config.FREELANCEHUNT_URL
        self.projects_url = urljoin(self.base_url, "/projects")
        
        # Set headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def load_cookies(self):
        """Load cookies from file if exists."""
        import json
        from pathlib import Path
        
        cookies_path = config.COOKIES_PATH
        if cookies_path.exists():
            try:
                with open(cookies_path, 'r', encoding='utf-8') as f:
                    cookies_data = json.load(f)
                    # Handle both list and dict formats
                    if isinstance(cookies_data, list):
                        # List format (from Selenium)
                        for cookie in cookies_data:
                            try:
                                self.session.cookies.set(
                                    cookie.get('name', ''),
                                    cookie.get('value', ''),
                                    domain=cookie.get('domain', ''),
                                    path=cookie.get('path', '/')
                                )
                            except Exception:
                                pass
                    elif isinstance(cookies_data, dict):
                        # Dict format (domain-keyed)
                        for domain, cookie_list in cookies_data.items():
                            if isinstance(cookie_list, list):
                                for cookie in cookie_list:
                                    try:
                                        self.session.cookies.set(
                                            cookie.get('name', ''),
                                            cookie.get('value', ''),
                                            domain=cookie.get('domain', domain),
                                            path=cookie.get('path', '/')
                                        )
                                    except Exception:
                                        pass
            except Exception as e:
                print(f"Error loading cookies: {e}")
    
    def extract_project_id(self, url: str) -> Optional[str]:
        """Extract project ID from URL."""
        # Freelancehunt URLs typically look like: /project/title-slug/123456.html
        match = re.search(r'/(\d+)\.html', url)
        if match:
            return match.group(1)
        
        # Alternative format: /project/title-slug/123456
        match = re.search(r'/(\d+)/?$', url)
        if match:
            return match.group(1)
        
        return None
    
    def parse_budget(self, text: str) -> Optional[float]:
        """Parse budget from text."""
        if not text:
            return None
        
        # Remove currency symbols and whitespace
        text = re.sub(r'[^\d.,\s]', '', text)
        # Replace comma with dot for decimal
        text = text.replace(',', '.')
        
        # Extract numbers
        numbers = re.findall(r'\d+\.?\d*', text)
        if numbers:
            try:
                return float(numbers[0])
            except ValueError:
                return None
        
        return None
    
    def parse_deadline(self, text: str) -> Optional[int]:
        """Parse deadline in days from text."""
        if not text:
            return None
        
        # Look for numbers followed by day-related words
        match = re.search(r'(\d+)\s*(?:дн|день|дней|day|days)', text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        
        # Just extract first number
        numbers = re.findall(r'\d+', text)
        if numbers:
            try:
                return int(numbers[0])
            except ValueError:
                return None
        
        return None
    
    def parse_relative_time(self, time_text: str) -> datetime:
        """Parse relative time like '2 часа 17 минут назад' to datetime."""
        try:
            now = datetime.now()
            
            # Pattern: "X минут назад", "X часов Y минут назад", "X часов назад", "X дней назад"
            # Minutes
            minutes_match = re.search(r'(\d+)\s*минут\s*назад', time_text, re.I)
            if minutes_match:
                minutes = int(minutes_match.group(1))
                return (now - timedelta(minutes=minutes))
            
            # Hours and minutes: "2 часа 17 минут назад"
            hours_minutes_match = re.search(r'(\d+)\s*час(?:а|ов)?\s*(\d+)\s*минут\s*назад', time_text, re.I)
            if hours_minutes_match:
                hours = int(hours_minutes_match.group(1))
                minutes = int(hours_minutes_match.group(2))
                return (now - timedelta(hours=hours, minutes=minutes))
            
            # Just hours: "2 часа назад"
            hours_match = re.search(r'(\d+)\s*час(?:а|ов)?\s*назад', time_text, re.I)
            if hours_match:
                hours = int(hours_match.group(1))
                return (now - timedelta(hours=hours))
            
            # Days: "X дней назад"
            days_match = re.search(r'(\d+)\s*д(?:ень|ня|ней)\s*назад', time_text, re.I)
            if days_match:
                days = int(days_match.group(1))
                return (now - timedelta(days=days))
            
            return now
        except Exception as e:
            logger.warning(f"Error parsing relative time '{time_text}': {e}")
            return datetime.now()
    
    def parse_project_card(self, card_element) -> Optional[Dict]:
        """Parse a single project card element."""
        try:
            # Find project link - try multiple ways
            link_elem = card_element.find('a', href=re.compile(r'/project/'))
            if not link_elem:
                # Try finding any link with project in href
                all_links = card_element.find_all('a', href=True)
                for link in all_links:
                    if '/project/' in link.get('href', ''):
                        link_elem = link
                        break
            
            if not link_elem:
                return None
            
            href = link_elem.get('href', '')
            project_url = urljoin(self.base_url, href)
            project_id = self.extract_project_id(project_url)
            
            if not project_id:
                return None
            
            # Extract title - prefer title attribute, then text
            title = link_elem.get('title', '').strip()
            if not title:
                title = link_elem.get_text(strip=True)
            if not title:
                # Try finding title in parent or siblings
                parent = link_elem.find_parent(['td', 'div', 'span'])
                if parent:
                    title_elem = parent.find(['h1', 'h2', 'h3', 'h4', 'strong', 'b'])
                    if title_elem:
                        title = title_elem.get_text(strip=True)
            
            if not title:
                # Last resort: use URL slug
                title = href.split('/')[-2] if len(href.split('/')) > 2 else "Без названия"
            
            # Extract category - look for category links (/projects/skill/...)
            category = None
            category_links = card_element.find_all('a', href=re.compile(r'/projects/skill/'))
            if category_links:
                # Get text from category links
                categories = [link.get_text(strip=True) for link in category_links if link.get_text(strip=True)]
                if categories:
                    # Join multiple categories
                    category = ', '.join(categories[:2])  # Limit to 2 categories
            else:
                # Fallback: try to find category in other elements
                category_elem = card_element.find(['span', 'div', 'td'], class_=re.compile(r'category|tag|badge|label', re.I))
                if category_elem:
                    category = category_elem.get_text(strip=True)
            
            # If still not found, try looking for common category patterns in text
            if not category:
                text_content = card_element.get_text(' ', strip=True)
                # Match common category names
                category_match = re.search(r'(Программирование|Разработка|Дизайн|Маркетинг|Текст|Перевод|Веб-программирование)', text_content, re.I)
                if category_match:
                    category = category_match.group(1)
            
            # Extract budget - look for UAH or currency symbols
            budget = None
            card_text = card_element.get_text(' ', strip=True)
            
            # Try to find budget in a separate cell/column first
            budget_cell = card_element.find(['td', 'div', 'span'], string=re.compile(r'UAH|грн|₴', re.I))
            if budget_cell:
                budget_text = budget_cell.get_text(strip=True)
                budget = self.parse_budget(budget_text)
            else:
                # Search in the entire card text
                budget_match = re.search(r'(\d+(?:\s*\d+)*)\s*(?:UAH|грн|₴)', card_text, re.I)
                if budget_match:
                    budget_text = budget_match.group(1).replace(' ', '')
                    budget = self.parse_budget(budget_text)
            
            # Extract deadline
            deadline = None
            deadline_match = re.search(r'(\d+)\s*(?:дн|день|дней|day|days)', card_text, re.I)
            if deadline_match:
                deadline = int(deadline_match.group(1))
            
            # Extract creation time - look for relative time patterns
            created_at = None
            created_at_datetime = datetime.now()
            
            # Look for relative time patterns: "X минут назад", "X часов Y минут назад", etc.
            time_patterns = [
                r'(\d+)\s*час(?:а|ов)?\s*(\d+)\s*минут\s*назад',  # "2 часа 17 минут назад"
                r'(\d+)\s*минут\s*назад',  # "26 минут назад"
                r'(\d+)\s*час(?:а|ов)?\s*назад',  # "2 часа назад"
                r'(\d+)\s*д(?:ень|ня|ней)\s*назад',  # "X дней назад"
            ]
            
            time_text = None
            for pattern in time_patterns:
                time_match = re.search(pattern, card_text, re.I)
                if time_match:
                    # Get the full match
                    time_text = time_match.group(0)
                    created_at_datetime = self.parse_relative_time(time_text)
                    created_at = created_at_datetime.isoformat()
                    break
            
            # Fallback: try to find time element with datetime attribute
            if not created_at:
                time_elem = card_element.find(['time', 'span', 'td'], class_=re.compile(r'time|date|created|ago', re.I))
                if time_elem:
                    datetime_attr = time_elem.get('datetime')
                    if datetime_attr:
                        created_at = datetime_attr
                    else:
                        time_text_elem = time_elem.get_text(strip=True)
                        if time_text_elem:
                            created_at_datetime = self.parse_relative_time(time_text_elem)
                            created_at = created_at_datetime.isoformat()
            
            return {
                'id': project_id,
                'title': title,
                'category': category,
                'budget': budget,
                'deadline': deadline,
                'url': project_url,
                'created_at': created_at or datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error parsing project card: {e}")
            return None
    
    def get_html_via_browser(self, page: int = 1, load_cookies: bool = True) -> Optional[str]:
        """Get HTML content using browser automation."""
        if not self.browser:
            return None
        
        try:
            # Initialize browser if needed
            is_new_browser = False
            if not self.browser.driver:
                self.browser.driver = self.browser.init_driver()
                is_new_browser = True
            
            # Load cookies only if browser is new or explicitly requested
            if is_new_browser or load_cookies:
                self.browser.load_cookies()
            
            # Navigate to projects page (with page parameter if needed)
            url = self.projects_url if page == 1 else f"{self.projects_url}?page={page}"
            self.browser.driver.get(url)
            time.sleep(3)  # Wait for page to load
            
            # Get page HTML
            html = self.browser.driver.page_source
            return html
        except Exception as e:
            logger.error(f"Error getting HTML via browser (page {page}): {e}")
            return None
    
    def get_new_projects(self, categories: List[str] = None) -> List[Dict]:
        """Get new projects from Freelancehunt."""
        all_project_cards = []
        
        # Check first 2 pages (newest projects are usually on first pages)
        for page_num, page in enumerate([1, 2], 1):
            html_content = None
            
            # Try to get HTML via browser first (more reliable)
            if self.browser:
                logger.info(f"Using browser to fetch projects page {page}...")
                # Load cookies only on first page
                html_content = self.get_html_via_browser(page, load_cookies=(page_num == 1))
            
            # Fallback to requests if browser fails or not available
            if not html_content:
                logger.info(f"Falling back to requests for fetching projects page {page}...")
                self.load_cookies()
                try:
                    url = self.projects_url if page == 1 else f"{self.projects_url}?page={page}"
                    response = self.session.get(url, timeout=30)
                    response.raise_for_status()
                    html_content = response.text
                except requests.RequestException as e:
                    logger.error(f"Error fetching projects via requests (page {page}): {e}")
                    continue
            
            if not html_content:
                logger.warning(f"Failed to get HTML content for page {page}")
                continue
            
            try:
                soup = BeautifulSoup(html_content, 'lxml')
                
                # Find all project cards - try multiple selectors for better results
                project_cards = []
                
                # Try various selectors to find project cards
                # First, try to find table with projects
                project_table = soup.find('table')
                
                selectors_to_try = []
                if project_table:
                    # If table found, look for rows with project links
                    selectors_to_try.append(
                        [tr for tr in project_table.find_all('tr') if tr.find('a', href=re.compile(r'/project/'))]
                    )
                    selectors_to_try.append(project_table.find_all('tbody tr'))
                    selectors_to_try.append(project_table.select('tbody tr'))
                
                # Generic selectors
                selectors_to_try.extend([
                    soup.select('table.table-projects tbody tr'),
                    soup.select('tbody tr'),
                    # Table rows with project links (from all tables)
                    [tr for tr in soup.find_all('tr') if tr.find('a', href=re.compile(r'/project/'))],
                    # Alternative structures
                    soup.find_all('article', class_=re.compile(r'project|card', re.I)),
                    soup.find_all('div', class_=re.compile(r'project|card', re.I)),
                    soup.select('.project-item, .card-project, [class*="project"]'),
                ])
                
                for selector_result in selectors_to_try:
                    if selector_result:
                        project_cards = selector_result
                        logger.info(f"Found {len(project_cards)} project cards on page {page} using selector")
                        break
                
                all_project_cards.extend(project_cards)
                
            except Exception as e:
                logger.error(f"Error parsing projects page {page}: {e}")
                continue
        
        if not all_project_cards:
            logger.warning("No project cards found on any page")
            return []
        
        try:
            
            # Remove duplicates while preserving order
            seen_ids = set()
            unique_cards = []
            for card in all_project_cards:
                # Try to get a unique identifier for the card
                card_id = None
                try:
                    # Try data-project-id
                    card_id = card.get('data-project-id')
                    if not card_id:
                        # Try extracting from link
                        link = card.find('a', href=re.compile(r'/project/'))
                        if link:
                            href = link.get('href', '')
                            match = re.search(r'/(\d+)', href)
                            if match:
                                card_id = match.group(1)
                except:
                    pass
                
                if card_id and card_id not in seen_ids:
                    seen_ids.add(card_id)
                    unique_cards.append(card)
                elif not card_id:
                    # If no ID, add anyway (might be duplicates but better than missing projects)
                    unique_cards.append(card)
            
            project_cards = unique_cards
            logger.info(f"Processing {len(project_cards)} unique project cards")
            
            new_projects = []
            
            for card in project_cards:
                project = self.parse_project_card(card)
                if not project:
                    continue
                
                # Check if project is new (in both tables)
                project_id = project['id']
                if self.db.project_exists(project_id):
                    continue
                
                # Filter by categories if specified
                project_matches_category = True  # Default: if no categories, all projects match
                
                if categories and len(categories) > 0:
                    # Only filter if categories are specified
                    project_matches_category = False
                    
                    # Build search text from title, category, and description (if available)
                    search_text = (project.get('title', '') + ' ' + 
                                 (project.get('category', '') or '')).lower()
                    
                    # Check if any category keyword matches
                    for cat in categories:
                        if not cat:
                            continue
                        cat_lower = cat.lower()
                        # Check in category field
                        if project.get('category') and cat_lower in project['category'].lower():
                            project_matches_category = True
                            break
                        # Check in title/description (broader matching)
                        if cat_lower in search_text or any(
                            keyword in search_text 
                            for keyword in cat_lower.split()
                            if len(keyword) > 2
                        ):
                            project_matches_category = True
                            break
                
                # If project matches category or no categories specified, add to main projects
                if project_matches_category:
                    # Check if already in other_projects - if yes, skip (already processed)
                    conn = self.db.get_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1 FROM other_projects WHERE id = ?", (project_id,))
                    if not cursor.fetchone():
                        # Add to main database
                        if self.db.add_project(
                            project['id'],
                            project['title'],
                            project['category'],
                            project['budget'],
                            project['deadline'],
                            project['url'],
                            project['created_at']
                        ):
                            new_projects.append(project)
                else:
                    # Project doesn't match categories - add to other_projects
                    # Check if already exists in main projects
                    if not self.db.project_exists(project_id):
                        # Check if already in other_projects
                        conn = self.db.get_connection()
                        cursor = conn.cursor()
                        cursor.execute("SELECT 1 FROM other_projects WHERE id = ?", (project_id,))
                        if not cursor.fetchone():
                            # Add to other_projects
                            if self.db.add_other_project(
                                project['id'],
                                project['title'],
                                project.get('category', ''),
                                project.get('budget'),
                                project.get('deadline'),
                                project['url'],
                                project.get('created_at')
                            ):
                                # Will be notified by check_projects_callback
                                pass
            
            return new_projects
            
        except Exception as e:
            logger.error(f"Error parsing projects: {e}")
            return []

