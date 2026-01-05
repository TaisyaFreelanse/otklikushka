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
            
            # Get card text early - we'll use it for multiple parsing operations
            card_text = card_element.get_text(' ', strip=True)
            
            # Extract category - look for category links (/projects/skill/...)
            category = None
            category_links = card_element.find_all('a', href=re.compile(r'/projects/skill/'))
            if category_links:
                # Get text from category links
                categories = [link.get_text(strip=True) for link in category_links if link.get_text(strip=True)]
                if categories:
                    # Join multiple categories (up to 3 for better matching)
                    category = ', '.join(categories[:3])
            
            # Also check for category text pattern like "3D моделирование и визуализация, Векторная графика"
            # This pattern appears after the title, before time
            if not category:
                # Look for text pattern: "Category1, Category2 - X минут назад"
                category_time_pattern = re.search(
                    r'([А-Яа-яA-Za-z\s]+(?:,\s*[А-Яа-яA-Za-z\s]+)*)\s*-\s*\d+\s*(?:минут|час|день|дней)',
                    card_text,
                    re.I
                )
                if category_time_pattern:
                    category = category_time_pattern.group(1).strip()
                    # Clean up - remove trailing dashes or extra spaces
                    category = re.sub(r'\s*-\s*$', '', category).strip()
            
            # Fallback: try to find category in other elements
            if not category:
                category_elem = card_element.find(['span', 'div', 'td'], class_=re.compile(r'category|tag|badge|label|skill', re.I))
                if category_elem:
                    category = category_elem.get_text(strip=True)
            
            # If still not found, try looking for common category patterns in text
            if not category:
                text_content = card_element.get_text(' ', strip=True)
                # Match common category names (expanded list)
                category_patterns = [
                    r'Программирование',
                    r'Веб-программирование',
                    r'Веб-разработка',
                    r'Разработка',
                    r'Дизайн',
                    r'Маркетинг',
                    r'Текст',
                    r'Перевод',
                    r'Backend',
                    r'Frontend',
                    r'Full Stack',
                    r'Мобильная разработка',
                    r'iOS',
                    r'Android',
                    r'Web Development',
                    r'Mobile Development',
                    r'3D моделирование',
                    r'Векторная графика',
                    r'AI и машинное обучение',
                    r'Разработка ботов',
                    r'Парсинг данных',
                ]
                for pattern in category_patterns:
                    category_match = re.search(pattern, text_content, re.I)
                    if category_match:
                        category = category_match.group(0)
                        break
            
            # Extract budget - look for UAH or currency symbols
            budget = None
            # card_text already defined above
            
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
            # Pattern matches: "Category1, Category2 - X минут назад" or just "X минут назад"
            time_patterns = [
                # Pattern with category prefix: "Category - X минут назад"
                r'-\s*(\d+)\s*минут\s*назад',  # "- 21 минута назад" (after category)
                r'-\s*(\d+)\s*час(?:а|ов)?\s*назад',  # "- 2 часа назад"
                r'-\s*(\d+)\s*д(?:ень|ня|ней)\s*назад',  # "- 1 день назад"
                # Direct patterns without prefix
                r'(\d+)\s*час(?:а|ов)?\s*(\d+)\s*минут\s*назад',  # "2 часа 17 минут назад"
                r'(\d+)\s*минут\s*назад',  # "26 минут назад"
                r'(\d+)\s*час(?:а|ов)?\s*назад',  # "2 часа назад"
                r'(\d+)\s*д(?:ень|ня|ней)\s*назад',  # "X дней назад"
            ]
            
            time_text = None
            for pattern in time_patterns:
                time_match = re.search(pattern, card_text, re.I)
                if time_match:
                    # Get the full match (with or without dash prefix)
                    time_text = time_match.group(0)
                    # Remove leading dash and spaces if present
                    time_text = re.sub(r'^-\s*', '', time_text).strip()
                    
                    # Parse relative time
                    created_at_datetime = self.parse_relative_time(time_text)
                    created_at = created_at_datetime.isoformat()
                    logger.debug(f"Parsed time '{time_text}' -> {created_at}")
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
            
            # Load cookies only if browser is NEW (not if driver already exists with cookies)
            # This avoids reloading cookies on every page request, which breaks Cloudflare session
            if is_new_browser:
                logger.info("New browser instance detected, loading cookies...")
                if not self.browser.load_cookies():
                    logger.warning("⚠️ Failed to load cookies for new browser instance")
            elif load_cookies:
                # Only reload if explicitly requested (should be rare)
                logger.debug("Explicit cookie reload requested")
                self.browser.load_cookies()
            
            # Navigate to projects page (with page parameter if needed)
            url = self.projects_url if page == 1 else f"{self.projects_url}?page={page}"
            
            # Add a small delay before navigation to appear more human-like
            import random
            time.sleep(random.uniform(1, 3))
            
            # Navigate with realistic behavior
            self.browser.driver.get(url)
            
            # Immediately simulate some human activity before Cloudflare check
            try:
                time.sleep(random.uniform(0.5, 1.5))
                # Move mouse slightly
                self.browser.driver.execute_script("""
                    var event = new MouseEvent('mousemove', {
                        bubbles: true,
                        cancelable: true,
                        view: window,
                        clientX: 100,
                        clientY: 100
                    });
                    document.dispatchEvent(event);
                """)
                time.sleep(random.uniform(0.3, 0.8))
            except:
                pass
            
            # Wait for Cloudflare challenge to complete (can take up to 120 seconds on server)
            logger.info(f"Waiting for page {page} to load (Cloudflare challenge may appear)...")
            max_wait = 120  # Increased to 120 seconds for Cloudflare challenge on server
            wait_interval = 3  # Check every 3 seconds
            waited = 0
            
            while waited < max_wait:
                html = self.browser.driver.page_source
                title = self.browser.driver.title
                
                # Check if Cloudflare challenge is still present
                is_cloudflare = (
                    "Just a moment" in html or 
                    "cf-browser-verification" in html or 
                    "challenge-platform" in html or
                    "Just a moment" in title
                )
                
                if is_cloudflare:
                    if waited % 15 == 0:  # Log every 15 seconds
                        logger.info(f"Cloudflare challenge detected, waiting... ({waited}s/{max_wait}s)")
                    
                    # Enhanced human-like interaction simulation to help Cloudflare verify
                    try:
                        import random
                        
                        # Random delay to make behavior less predictable (1-3 seconds)
                        human_delay = random.uniform(1, 3)
                        time.sleep(human_delay)
                        
                        # More realistic mouse movement pattern
                        mouse_x = random.randint(50, 200)
                        mouse_y = random.randint(50, 300)
                        self.browser.driver.execute_script(f"""
                            var event = new MouseEvent('mousemove', {{
                                bubbles: true,
                                cancelable: true,
                                view: window,
                                clientX: {mouse_x},
                                clientY: {mouse_y},
                                movementX: {random.randint(-10, 10)},
                                movementY: {random.randint(-10, 10)}
                            }});
                            document.dispatchEvent(event);
                        """)
                        
                        # Smooth scroll (human-like, not instant)
                        scroll_pos = random.randint(100, 500)
                        self.browser.driver.execute_script(f"""
                            window.scrollTo({{
                                top: {scroll_pos},
                                behavior: 'smooth'
                            }});
                        """)
                        time.sleep(random.uniform(0.5, 1.5))
                        
                        # Random mouse click every 20-30 seconds to simulate active user
                        if waited % 25 == 0:
                            click_x = random.randint(100, 400)
                            click_y = random.randint(100, 300)
                            self.browser.driver.execute_script(f"""
                                var clickEvent = new MouseEvent('click', {{
                                    bubbles: true,
                                    cancelable: true,
                                    view: window,
                                    clientX: {click_x},
                                    clientY: {click_y}
                                }});
                                document.elementFromPoint({click_x}, {click_y})?.dispatchEvent(clickEvent);
                            """)
                            time.sleep(random.uniform(0.5, 1))
                        
                        # Scroll back up occasionally
                        if waited % 40 == 0:
                            self.browser.driver.execute_script("window.scrollTo({top: 0, behavior: 'smooth'});")
                            time.sleep(random.uniform(1, 2))
                        
                        # Simulate keyboard activity occasionally
                        if waited % 35 == 0:
                            self.browser.driver.execute_script("""
                                var keyEvent = new KeyboardEvent('keydown', {
                                    bubbles: true,
                                    cancelable: true,
                                    key: 'Tab',
                                    code: 'Tab'
                                });
                                document.dispatchEvent(keyEvent);
                            """)
                            time.sleep(0.3)
                            
                    except Exception as e:
                        logger.debug(f"Error simulating interaction: {e}")
                    
                    # Add random wait to make timing less predictable
                    remaining_wait = wait_interval - human_delay if 'human_delay' in locals() else wait_interval
                    if remaining_wait > 0:
                        time.sleep(remaining_wait)
                    waited += wait_interval
                else:
                    # Page loaded successfully
                    logger.info(f"✅ Page {page} loaded successfully after {waited}s - Cloudflare passed!")
                    # Additional wait to ensure page is fully rendered
                    time.sleep(2)
                    break
            
            # Final check - if still Cloudflare, log warning but return HTML anyway
            final_html = self.browser.driver.page_source
            final_title = self.browser.driver.title
            still_cloudflare = (
                "Just a moment" in final_html or 
                "cf-browser-verification" in final_html or
                "Just a moment" in final_title
            )
            
            if still_cloudflare:
                logger.warning(f"⚠️ Cloudflare challenge still present on page {page} after {max_wait}s wait")
                logger.warning(f"   Page title: {final_title[:50]}")
            else:
                logger.info(f"✅ Page {page} appears to be fully loaded (title: {final_title[:50]})")
            
            return final_html
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
                
                # Debug: log page structure
                logger.debug(f"Page {page} HTML length: {len(html_content)}")
                
                # Find all project cards - try multiple selectors for better results
                project_cards = []
                
                # First, find all links to projects to understand structure
                all_project_links = soup.find_all('a', href=re.compile(r'/project/[^/]+/\d+'))
                logger.info(f"Found {len(all_project_links)} project links on page {page}")
                
                if all_project_links:
                    # Extract unique project rows/parents
                    project_elements = []
                    seen_ids = set()
                    for link in all_project_links:
                        # Try to find parent row or container
                        parent = link.find_parent('tr')
                        if not parent:
                            # Try other parent containers
                            parent = link.find_parent(['div', 'article', 'li', 'td'])
                        
                        if parent:
                            # Extract project ID from link
                            href = link.get('href', '')
                            project_id_match = re.search(r'/(\d+)', href)
                            if project_id_match:
                                project_id = project_id_match.group(1)
                                if project_id not in seen_ids:
                                    seen_ids.add(project_id)
                                    project_elements.append(parent)
                    
                    if project_elements:
                        project_cards = project_elements
                        logger.info(f"Found {len(project_cards)} project cards via parent elements on page {page}")
                
                # If no cards found, try table-based selectors
                if not project_cards:
                    project_table = soup.find('table')
                    logger.debug(f"Looking for table: {project_table is not None}")
                    
                    if project_table:
                        # Find all rows in table
                        all_rows = project_table.find_all('tr')
                        logger.debug(f"Found {len(all_rows)} rows in table")
                        
                        # Filter rows that contain project links
                        project_rows = [tr for tr in all_rows if tr.find('a', href=re.compile(r'/project/'))]
                        if project_rows:
                            project_cards = project_rows
                            logger.info(f"Found {len(project_cards)} project rows in table on page {page}")
                
                # Fallback: try generic selectors
                if not project_cards:
                    selectors_to_try = [
                        soup.select('table tbody tr'),
                        soup.find_all('tr', class_=re.compile(r'project|item', re.I)),
                        soup.find_all('article', class_=re.compile(r'project|card', re.I)),
                        soup.find_all('div', class_=re.compile(r'project|card', re.I)),
                    ]
                    
                    for selector_result in selectors_to_try:
                        if selector_result:
                            # Filter to only those with project links
                            filtered = [elem for elem in selector_result if elem.find('a', href=re.compile(r'/project/'))]
                            if filtered:
                                project_cards = filtered
                                logger.info(f"Found {len(project_cards)} project cards using fallback selector on page {page}")
                                break
                
                if project_cards:
                    logger.info(f"Successfully found {len(project_cards)} project cards on page {page}")
                    all_project_cards.extend(project_cards)
                else:
                    logger.warning(f"No project cards found on page {page}. HTML sample: {html_content[:500]}")
                
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
                
                # Filter by time FIRST - only projects created less than 1 hour ago
                created_at = project.get('created_at')
                if created_at:
                    try:
                        if isinstance(created_at, str):
                            # Parse ISO format datetime
                            created_at_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        else:
                            created_at_dt = created_at
                        
                        # Get current time (same timezone if available)
                        now = datetime.now(created_at_dt.tzinfo) if created_at_dt.tzinfo else datetime.now()
                        
                        # Calculate time difference
                        time_diff = now - created_at_dt
                        
                        # Skip projects older than 1 hour
                        if time_diff.total_seconds() > 3600:  # 1 hour in seconds
                            hours_ago = time_diff.total_seconds() / 3600
                            logger.debug(f"Skipping project {project['id']} - too old ({hours_ago:.1f} hours ago)")
                            continue
                    except Exception as e:
                        logger.warning(f"Error parsing created_at for project {project.get('id')}: {e}")
                        # Continue anyway if parsing fails
                
                # Check if project is new (in both tables)
                project_id = project['id']
                if self.db.project_exists(project_id):
                    continue
                
                # Exclude unwanted categories FIRST (before category matching)
                project_category = (project.get('category') or '').lower()
                excluded_categories_global = [
                    'интернет-магазины и электронная коммерция',
                    'интернет-магазины',
                    'электронная коммерция',
                    'дизайн визиток',
                    'визитки',
                    'фирменный стиль',
                    'брендинг',
                    'логотип',
                ]
                if any(excluded in project_category for excluded in excluded_categories_global):
                    logger.debug(f"Skipping project {project_id} due to excluded category: {project_category}")
                    continue
                
                # IMPORTANT: Only process projects that match specified categories
                # If no categories specified, skip ALL projects (no bids on projects outside categories)
                project_matches_category = False  # Default: NO match unless categories are specified and matched
                
                if categories and len(categories) > 0:
                    # Only filter if categories are specified
                    project_matches_category = False
                    
                    # Build search text from title, category, and description (if available)
                    search_text = (project.get('title', '') + ' ' + 
                                 (project.get('category', '') or '')).lower()
                    
                    # Check if any category keyword matches (project_category already set above)
                    
                    for cat in categories:
                        if not cat:
                            continue
                        cat_lower = cat.lower()
                        
                        # Direct category match (exact or contains)
                        if project_category and (
                            cat_lower in project_category or 
                            project_category in cat_lower or
                            any(word in project_category for word in cat_lower.split() if len(word) > 3)
                        ):
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
                        
                        # Special mappings for common variations
                        category_mappings = {
                            'веб-программирование': ['веб-программирование', 'web development', 'веб-разработка'],
                            'веб-разработка': ['веб-разработка', 'веб-программирование', 'web development'],
                            'backend': ['бэкенд', 'backend', 'back-end', 'бэк-энд'],
                            'frontend': ['фронтенд', 'frontend', 'front-end', 'фронт-энд'],
                            'программирование': ['программирование', 'разработка', 'development'],
                        }
                        
                        # Exclude unwanted categories
                        excluded_categories = [
                            'интернет-магазины и электронная коммерция',
                            'интернет-магазины',
                            'электронная коммерция',
                            'дизайн визиток',
                            'визитки',
                            'фирменный стиль',
                            'брендинг',
                            'логотип',
                        ]
                        if any(excluded in project_category.lower() for excluded in excluded_categories):
                            project_matches_category = False
                            break
                        
                        # Check if category matches any variation
                        if cat_lower in category_mappings:
                            for variation in category_mappings[cat_lower]:
                                if variation in project_category or variation in search_text:
                                    project_matches_category = True
                                    break
                            if project_matches_category:
                                break
                        
                        # Special mappings for common variations
                        category_mappings = {
                            'веб-программирование': ['веб-программирование', 'web development', 'web development', 'веб-разработка'],
                            'веб-разработка': ['веб-разработка', 'веб-программирование', 'web development'],
                            'backend': ['бэкенд', 'backend', 'back-end', 'бэк-энд'],
                            'frontend': ['фронтенд', 'frontend', 'front-end', 'фронт-энд'],
                            'программирование': ['программирование', 'разработка', 'development'],
                        }
                        
                        # Check if category matches any variation
                        if cat_lower in category_mappings:
                            for variation in category_mappings[cat_lower]:
                                if variation in project_category or variation in search_text:
                                    project_matches_category = True
                                    break
                            if project_matches_category:
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

