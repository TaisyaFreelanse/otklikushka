"""Scraper module for parsing Freelancehunt projects."""
import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional
from datetime import datetime
from urllib.parse import urljoin, urlparse
import time
import logging
import config
from database import Database
from database import Database

logger = logging.getLogger(__name__)


class FreelancehuntScraper:
    """Scraper for Freelancehunt projects page."""
    
    def __init__(self, db: Database, session: requests.Session = None):
        """Initialize scraper with database and session."""
        self.db = db
        self.session = session or requests.Session()
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
    
    def parse_project_card(self, card_element) -> Optional[Dict]:
        """Parse a single project card element."""
        try:
            # Find project link
            link_elem = card_element.find('a', href=re.compile(r'/project/'))
            if not link_elem:
                return None
            
            project_url = urljoin(self.base_url, link_elem.get('href', ''))
            project_id = self.extract_project_id(project_url)
            
            if not project_id:
                return None
            
            # Extract title
            title = link_elem.get_text(strip=True)
            if not title:
                title = link_elem.get('title', '').strip()
            
            # Extract category
            category = None
            category_elem = card_element.find(['span', 'div'], class_=re.compile(r'category|tag|badge', re.I))
            if category_elem:
                category = category_elem.get_text(strip=True)
            
            # Extract budget
            budget = None
            budget_elem = card_element.find(string=re.compile(r'UAH|грн|₴|\d+\s*\$', re.I))
            if budget_elem:
                budget_text = budget_elem if isinstance(budget_elem, str) else budget_elem.get_text()
                budget = self.parse_budget(budget_text)
            
            # Extract deadline if mentioned in preview
            deadline = None
            deadline_elem = card_element.find(string=re.compile(r'дн|день|дней|срок', re.I))
            if deadline_elem:
                deadline_text = deadline_elem if isinstance(deadline_elem, str) else deadline_elem.get_text()
                deadline = self.parse_deadline(deadline_text)
            
            # Extract creation time if available
            created_at = None
            time_elem = card_element.find(['time', 'span'], class_=re.compile(r'time|date|created', re.I))
            if time_elem:
                datetime_attr = time_elem.get('datetime')
                if datetime_attr:
                    created_at = datetime_attr
                else:
                    created_at = time_elem.get_text(strip=True)
            
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
            print(f"Error parsing project card: {e}")
            return None
    
    def get_new_projects(self, categories: List[str] = None) -> List[Dict]:
        """Get new projects from Freelancehunt."""
        self.load_cookies()
        
        try:
            response = self.session.get(self.projects_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Find all project cards - try multiple selectors for better results
            project_cards = []
            
            # Try various selectors to find project cards
            selectors_to_try = [
                # Modern structure
                soup.select('table.table-projects tbody tr'),
                soup.select('tbody tr[data-project-id]'),
                soup.find_all('tr', class_=re.compile(r'project|item', re.I)),
                # Generic table rows in projects table
                soup.select('table tbody tr'),
                # Alternative structures
                soup.find_all('article', class_=re.compile(r'project|card', re.I)),
                soup.find_all('div', class_=re.compile(r'project|card', re.I)),
                soup.select('.project-item, .card-project, [class*="project"]'),
            ]
            
            for selector_result in selectors_to_try:
                if selector_result:
                    project_cards = selector_result
                    logger.info(f"Found {len(project_cards)} project cards using selector")
                    break
            
            # Remove duplicates while preserving order
            seen_ids = set()
            unique_cards = []
            for card in project_cards:
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
                    if project.get('category'):
                        # Check if project category matches any of our categories
                        project_category = project['category'].lower()
                        project_matches_category = any(
                            cat.lower() in project_category or project_category in cat.lower()
                            for cat in categories if cat
                        )
                
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
            
        except requests.RequestException as e:
            print(f"Error fetching projects: {e}")
            return []
        except Exception as e:
            print(f"Error parsing projects: {e}")
            return []

