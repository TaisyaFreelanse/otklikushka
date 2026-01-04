"""Browser automation module for Freelancehunt auto-bidding."""
import json
import time
import random
import os
import sys
from glob import glob
from pathlib import Path
from typing import Optional, Dict, Tuple, Union, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException
)
import config
from database import Database
import logging

logger = logging.getLogger(__name__)


class BrowserAutomation:
    """Browser automation for Freelancehunt bidding."""
    
    def __init__(self, db: Database):
        """Initialize browser automation."""
        self.db = db
        self.driver: Optional[Union[webdriver.Edge, webdriver.Chrome]] = None
        self.base_url = config.FREELANCEHUNT_URL
        self.cookies_path = config.COOKIES_PATH
        
    def init_driver(self) -> Union[webdriver.Edge, webdriver.Chrome]:
        """Initialize browser WebDriver (Chrome or Edge)."""
        browser_type = config.BROWSER_TYPE.lower()
        
        # Common options for both browsers
        common_args = [
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-blink-features=AutomationControlled',
            '--window-size=1920,1080',
            '--disable-gpu',
        ]
        
        if config.HEADLESS_BROWSER:
            common_args.append('--headless=new')
        
        # Try Chrome first (better for Linux servers)
        # Default to Chrome if not explicitly set to edge
        if browser_type != "edge":
            try:
                return self._init_chrome(common_args)
            except Exception as e:
                logger.warning(f"Failed to initialize Chrome, trying Edge: {e}")
                # Fallback to Edge if Chrome fails
                try:
                    return self._init_edge(common_args)
                except Exception as e2:
                    logger.error(f"Failed to initialize Edge as fallback: {e2}")
                    raise Exception(f"Не удалось инициализировать браузер (Chrome и Edge). Попробуйте проверить установку.")
        else:
            # Try Edge first
            try:
                return self._init_edge(common_args)
            except Exception as e:
                logger.warning(f"Failed to initialize Edge, trying Chrome: {e}")
                # Fallback to Chrome if Edge fails
                try:
                    return self._init_chrome(common_args)
                except Exception as e2:
                    logger.error(f"Failed to initialize Chrome as fallback: {e2}")
                    raise Exception(f"Не удалось инициализировать браузер (Edge и Chrome). Попробуйте проверить установку.")
    
    def _init_chrome(self, common_args: List[str]) -> webdriver.Chrome:
        """Initialize Chrome WebDriver using undetected-chromedriver to bypass Cloudflare."""
        driver = None
        
        # Try undetected-chromedriver first (best for bypassing Cloudflare)
        try:
            import undetected_chromedriver as uc
            
            logger.info("Trying to initialize Chrome with undetected-chromedriver...")
            
            # Create options for undetected-chromedriver
            # NOTE: Do NOT use add_experimental_option with undetected-chromedriver!
            # It handles stealth options internally and they conflict.
            uc_options = uc.ChromeOptions()
            
            # Use persistent profile directory to maintain session between restarts
            profile_dir = str(config.DATA_DIR / "chrome_profile")
            os.makedirs(profile_dir, exist_ok=True)
            uc_options.user_data_dir = profile_dir
            logger.info(f"Using Chrome profile directory: {profile_dir}")
            
            # Apply common arguments (skip headless and automation-related - UC handles these)
            for arg in common_args:
                # Skip headless and automation-related args - UC handles these internally
                if 'headless' not in arg.lower() and 'AutomationControlled' not in arg:
                    uc_options.add_argument(arg)
            
            # IMPORTANT: For Cloudflare bypass, prefer non-headless mode when possible
            # Cloudflare easily detects headless browsers, even with stealth patches
            # Check if we have DISPLAY available (from Xvfb on Linux servers)
            display_available = os.environ.get('DISPLAY') is not None
            display_value = os.environ.get('DISPLAY', 'NOT SET')
            is_linux = sys.platform.startswith('linux')
            
            logger.info(f"DISPLAY environment variable: {display_value}")
            logger.info(f"Platform: {sys.platform}, HEADLESS_BROWSER setting: {config.HEADLESS_BROWSER}")
            
            # On Linux servers with Xvfb: use non-headless if DISPLAY is available
            # On Windows/Mac local: respect HEADLESS_BROWSER setting
            if is_linux and display_available:
                # Linux server with Xvfb - use non-headless for better Cloudflare bypass
                logger.info("✅ Using non-headless mode (Linux server with DISPLAY) - better for Cloudflare bypass")
                # DO NOT add --headless argument - this is critical!
            elif config.HEADLESS_BROWSER:
                # Headless mode requested (local Windows/Mac or server without Xvfb)
                logger.info("Using headless mode as configured")
                uc_options.add_argument('--headless=new')
                uc_options.add_argument('--disable-gpu')
                # Additional options for headless mode
                uc_options.add_argument('--disable-software-rasterizer')
            else:
                # Non-headless mode requested (local testing)
                logger.info("Using non-headless mode (HEADLESS_BROWSER=false)")
            
            # Add window size (important for proper rendering)
            uc_options.add_argument('--window-size=1920,1080')
            uc_options.add_argument('--start-maximized')
            
            # Try to find Chrome binary
            chrome_paths = [
                '/usr/bin/google-chrome-stable',
                '/usr/bin/google-chrome',
                '/usr/bin/chromium',
                '/usr/bin/chromium-browser',
            ]
            chrome_binary = None
            for path in chrome_paths:
                if os.path.exists(path):
                    chrome_binary = path
                    logger.info(f"Found Chrome binary at: {path}")
                    break
            
            # Initialize undetected-chromedriver with version_main for stability
            try:
                if chrome_binary:
                    driver = uc.Chrome(
                        options=uc_options,
                        browser_executable_path=chrome_binary,
                        use_subprocess=False,
                        version_main=None,  # Auto-detect version
                        no_sandbox=True  # Required for Docker/containers
                    )
                else:
                    driver = uc.Chrome(
                        options=uc_options,
                        use_subprocess=False,
                        version_main=None,
                        no_sandbox=True
                    )
            except Exception as e:
                logger.error(f"Error initializing undetected-chromedriver: {e}")
                raise
            
            logger.info("Successfully initialized Chrome with undetected-chromedriver")
            return driver
            
        except ImportError:
            logger.warning("undetected-chromedriver not available, falling back to standard Chrome")
        except Exception as e:
            logger.warning(f"Failed to initialize undetected-chromedriver: {e}, falling back to standard Chrome")
        
        # Fallback to standard Chrome
        chrome_options = ChromeOptions()
        
        for arg in common_args:
            chrome_options.add_argument(arg)
        
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Method 1: Try with automatic driver management (Selenium 4+)
        try:
            driver = webdriver.Chrome(options=chrome_options)
        except Exception:
            # Method 2: Try using webdriver-manager
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                driver_path = ChromeDriverManager().install()
                service = ChromeService(executable_path=driver_path)
                driver = webdriver.Chrome(service=service, options=chrome_options)
            except Exception:
                # Method 3: Try system chrome/chromium with explicit binary location
                try:
                    chrome_paths = [
                        '/usr/bin/google-chrome-stable',
                        '/usr/bin/google-chrome',
                        '/usr/bin/chromium',
                        '/usr/bin/chromium-browser',
                        '/opt/google/chrome/google-chrome',
                    ]
                    chrome_binary = None
                    for path in chrome_paths:
                        if os.path.exists(path):
                            chrome_binary = path
                            logger.info(f"Found Chrome binary at: {path}")
                            break
                    
                    if chrome_binary:
                        chrome_options.binary_location = chrome_binary
                        try:
                            from webdriver_manager.chrome import ChromeDriverManager
                            driver_path = ChromeDriverManager().install()
                            service = ChromeService(executable_path=driver_path)
                            driver = webdriver.Chrome(service=service, options=chrome_options)
                        except:
                            driver = webdriver.Chrome(options=chrome_options)
                    else:
                        raise Exception("Chrome binary not found in common paths")
                except Exception as e:
                    logger.error(f"Chrome initialization failed: {e}")
                    raise Exception(f"Не удалось инициализировать ChromeDriver: {e}")
        
        # Remove webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def _init_edge(self, common_args: List[str]) -> webdriver.Edge:
        """Initialize Edge WebDriver."""
        edge_options = EdgeOptions()
        
        for arg in common_args:
            edge_options.add_argument(arg)
        
        edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        edge_options.add_experimental_option('useAutomationExtension', False)
        edge_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0')
        
        driver = None
        
        # Method 1: Try with automatic driver management (Selenium 4+)
        try:
            driver = webdriver.Edge(options=edge_options)
        except Exception:
            # Method 2: Try using webdriver-manager
            try:
                from webdriver_manager.microsoft import EdgeChromiumDriverManager
                driver_path = EdgeChromiumDriverManager().install()
                service = EdgeService(executable_path=driver_path)
                driver = webdriver.Edge(service=service, options=edge_options)
            except Exception:
                # Method 3: Try to find EdgeDriver in common locations
                try:
                    edge_paths = [
                        os.path.join(os.environ.get('ProgramFiles', ''), 'Microsoft', 'Edge', 'Application'),
                        os.path.join(os.environ.get('ProgramFiles(x86)', ''), 'Microsoft', 'Edge', 'Application'),
                    ]
                    
                    possible_paths = []
                    for edge_path in edge_paths:
                        if os.path.exists(edge_path):
                            driver_in_edge = os.path.join(edge_path, 'msedgedriver.exe')
                            if os.path.exists(driver_in_edge):
                                possible_paths.append(driver_in_edge)
                    
                    possible_paths.extend([
                        os.path.join(os.path.expanduser('~'), '.wdm', 'drivers', 'edgedriver', '*', 'msedgedriver.exe'),
                        os.path.join(os.getcwd(), 'msedgedriver.exe'),
                        'msedgedriver.exe',
                    ])
                    
                    driver_path = None
                    for path in possible_paths:
                        if '*' in path:
                            matches = glob(path)
                            if matches:
                                driver_path = matches[0]
                                break
                        elif os.path.exists(path):
                            driver_path = path
                            break
                    
                    if driver_path:
                        service = EdgeService(executable_path=driver_path)
                        driver = webdriver.Edge(service=service, options=edge_options)
                    else:
                        raise Exception("EdgeDriver не найден")
                except Exception as e:
                    raise Exception(f"Не удалось инициализировать EdgeDriver: {e}")
        
        # Remove webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def load_cookies(self):
        """Load cookies from file."""
        if not self.driver or not self.cookies_path.exists():
            return False
        
        try:
            self.driver.get(self.base_url)
            # Wait for Cloudflare challenge to complete (can take 20-40 seconds)
            logger.info("Waiting for Cloudflare challenge to complete after loading base URL...")
            
            # Wait and check for Cloudflare with user interaction simulation
            max_wait = 40
            waited = 0
            while waited < max_wait:
                page_source = self.driver.page_source
                if "Just a moment" in page_source or "cf-browser-verification" in page_source:
                    if waited % 10 == 0:
                        logger.info(f"Cloudflare challenge on base URL, waiting... ({waited}s/{max_wait}s)")
                    # Try to interact with page to help Cloudflare verify
                    try:
                        self.driver.execute_script("window.scrollTo(0, 100);")
                        time.sleep(1)
                        self.driver.execute_script("window.scrollTo(0, 0);")
                    except:
                        pass
                    time.sleep(3)
                    waited += 3
                else:
                    logger.info(f"✅ Base URL loaded successfully after {waited}s - Cloudflare passed!")
                    break
            
            if waited >= max_wait:
                logger.warning("⚠️ Cloudflare challenge may still be present on base URL")
                # Continue anyway - sometimes cookies can still be loaded
            
            # Check cookies file
            if not self.cookies_path.exists():
                logger.error(f"Cookies file not found at {self.cookies_path}")
                return False
            
            logger.info(f"Loading cookies from {self.cookies_path}")
            with open(self.cookies_path, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
                
            # If cookies are in list format (from Selenium)
            if isinstance(cookies, list):
                for cookie in cookies:
                    try:
                        # Ensure domain is correct format
                        cookie_dict = dict(cookie)
                        # Remove 'expiry' if it's too large (Selenium compatibility)
                        if 'expiry' in cookie_dict and cookie_dict['expiry']:
                            try:
                                expiry = int(cookie_dict['expiry'])
                                if expiry > 2147483647:  # Max 32-bit integer
                                    cookie_dict.pop('expiry', None)
                            except (ValueError, TypeError):
                                cookie_dict.pop('expiry', None)
                        self.driver.add_cookie(cookie_dict)
                    except Exception as e:
                        print(f"Error adding cookie: {e}")
            # If cookies are in domain-keyed format
            elif isinstance(cookies, dict):
                for domain, cookie_list in cookies.items():
                    if isinstance(cookie_list, list):
                        for cookie in cookie_list:
                            try:
                                cookie_dict = dict(cookie)
                                # Remove domain prefix if present
                                if cookie_dict.get('domain', '').startswith('.'):
                                    cookie_dict['domain'] = cookie_dict['domain'][1:]
                                # Handle expiry
                                if 'expiry' in cookie_dict and cookie_dict['expiry']:
                                    try:
                                        expiry = int(cookie_dict['expiry'])
                                        if expiry > 2147483647:
                                            cookie_dict.pop('expiry', None)
                                    except (ValueError, TypeError):
                                        cookie_dict.pop('expiry', None)
                                self.driver.add_cookie(cookie_dict)
                            except Exception as e:
                                print(f"Error adding cookie: {e}")
            
            # Refresh to apply cookies
            self.driver.refresh()
            time.sleep(2)
            return True
        except Exception as e:
            print(f"Error loading cookies: {e}")
            return False
    
    def save_cookies(self):
        """Save current cookies to file."""
        if not self.driver:
            return False
        
        try:
            cookies = self.driver.get_cookies()
            with open(self.cookies_path, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving cookies: {e}")
            return False
    
    def wait_for_element(self, by: By, value: str, timeout: int = 10):
        """Wait for element to be present and clickable."""
        if not self.driver:
            return None
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
        except TimeoutException:
            return None
    
    def wait_for_clickable(self, by: By, value: str, timeout: int = 10):
        """Wait for element to be clickable."""
        if not self.driver:
            return None
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
        except TimeoutException:
            return None
    
    def safe_click(self, element, retries: int = 3):
        """Safely click element with retries."""
        for attempt in range(retries):
            try:
                # Scroll into view
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", element)
                time.sleep(1)
                
                # Try to remove overlays
                try:
                    # Hide common overlay elements
                    self.driver.execute_script("""
                        var overlays = document.querySelectorAll('.pushContent, .modal-backdrop, .overlay, [class*="overlay"]');
                        overlays.forEach(function(el) {
                            el.style.display = 'none';
                        });
                    """)
                    time.sleep(0.5)
                except:
                    pass
                
                # Try JavaScript click first (more reliable)
                try:
                    self.driver.execute_script("arguments[0].click();", element)
                    time.sleep(1)
                    return True
                except:
                    # Fallback to regular click
                    element.click()
                    time.sleep(1)
                    return True
                    
            except (ElementClickInterceptedException, StaleElementReferenceException) as e:
                if attempt < retries - 1:
                    # Wait a bit longer and try to remove overlays
                    time.sleep(2)
                    try:
                        self.driver.execute_script("""
                            var overlays = document.querySelectorAll('.pushContent, .modal-backdrop, .overlay, [class*="overlay"]');
                            overlays.forEach(function(el) {
                                el.style.display = 'none';
                                el.remove();
                            });
                        """)
                    except:
                        pass
                    continue
                print(f"Error clicking element after {retries} attempts: {e}")
                return False
        return False
    
    def _handle_push_notification(self):
        """Handle push notification popup if present."""
        try:
            # Look for "СПАСИБО, ПОЗЖЕ" or similar buttons
            notification_selectors = [
                "//button[contains(text(), 'СПАСИБО, ПОЗЖЕ')]",
                "//button[contains(text(), 'Спасибо, позже')]",
                "//button[contains(text(), 'Thanks, later')]",
                "//a[contains(text(), 'СПАСИБО, ПОЗЖЕ')]",
                "//a[contains(text(), 'Спасибо, позже')]",
                "//*[contains(text(), 'СПАСИБО, ПОЗЖЕ')]",
                "//*[contains(@class, 'push') and .//*[contains(text(), 'СПАСИБО')]]",
            ]
            
            for selector in notification_selectors:
                try:
                    element = self.wait_for_element(By.XPATH, selector, timeout=2)
                    if element:
                        print("🔔 Обнаружено уведомление, закрываю...")
                        self.safe_click(element)
                        time.sleep(1)
                        return True
                except:
                    continue
        except Exception as e:
            pass
        return False
    
    def calculate_bid_amount(self, project_budget: Optional[float]) -> float:
        """Calculate bid amount based on project budget, rounded to thousands."""
        # Preferred round amounts for better appearance
        preferred_amounts = [5000, 7000, 10000, 12000, 15000, 17000, 20000, 22000, 25000, 27000]
        
        if project_budget:
            # Use project budget but cap at MAX_BID_AMOUNT
            bid_amount = min(project_budget, config.MAX_BID_AMOUNT)
            # Add small random variation (±5%)
            variation = bid_amount * 0.05
            bid_amount = bid_amount + random.uniform(-variation, variation)
            bid_amount = max(5000, min(bid_amount, config.MAX_BID_AMOUNT))
        else:
            # Random amount between 5000 and MAX_BID_AMOUNT
            bid_amount = random.uniform(5000, config.MAX_BID_AMOUNT)
        
        # Round to nearest thousand (remove hundreds and tens)
        bid_amount_rounded = round(bid_amount / 1000) * 1000
        
        # Try to use preferred amount if close
        for preferred in preferred_amounts:
            if abs(bid_amount_rounded - preferred) <= 1000:
                bid_amount_rounded = preferred
                break
        
        # Ensure minimum and maximum
        bid_amount_rounded = max(5000, min(bid_amount_rounded, config.MAX_BID_AMOUNT))
        
        return float(bid_amount_rounded)
    
    def calculate_deadline(self, project_deadline: Optional[int]) -> int:
        """Calculate deadline in days based on project deadline."""
        if project_deadline:
            # Use project deadline if specified
            deadline = project_deadline
            # Add small variation (±2 days)
            deadline = deadline + random.randint(-2, 2)
            deadline = max(1, deadline)
        else:
            # Default to 14 days with variation
            deadline = 14 + random.randint(-3, 7)
            deadline = max(7, deadline)
        
        return int(deadline)
    
    def submit_bid(self, project_url: str, project_budget: Optional[float] = None, 
                   project_deadline: Optional[int] = None) -> Tuple[bool, str, float, int]:
        """
        Submit a bid on a project.
        Returns: (success, message, bid_amount, bid_deadline)
        """
        if not self.driver:
            self.driver = self.init_driver()
            self.load_cookies()
        
        try:
            # Navigate to project page
            self.driver.get(project_url)
            time.sleep(2 + random.uniform(0, 1))
            
            # Handle push notification popup if present
            self._handle_push_notification()
            
            # Find and click "Сделать ставку" button
            # Try multiple possible selectors
            bid_button_selectors = [
                "//button[contains(text(), 'Сделать ставку')]",
                "//a[contains(text(), 'Сделать ставку')]",
                "//button[contains(text(), 'Make a bid')]",
                "//a[contains(text(), 'Make a bid')]",
                "//button[contains(@class, 'bid')]",
                "//a[contains(@class, 'bid')]",
                "//button[contains(@class, 'submit-bid')]",
            ]
            
            bid_button = None
            for selector in bid_button_selectors:
                try:
                    bid_button = self.wait_for_clickable(By.XPATH, selector, timeout=5)
                    if bid_button:
                        break
                except:
                    continue
            
            if not bid_button:
                return (False, "Не удалось найти кнопку 'Сделать ставку'", 0, 0)
            
            if not self.safe_click(bid_button):
                return (False, "Не удалось нажать кнопку 'Сделать ставку'", 0, 0)
            
            # Wait for form to load
            print("⏳ Ожидание загрузки формы...")
            time.sleep(3 + random.uniform(1, 2))
            
            # Handle push notification popup if appears again
            self._handle_push_notification()
            
            # Wait a bit more for form elements
            time.sleep(2)
            
            # Find and click "Сгенерировать" button for AI generation (MUST BE FIRST AFTER OPENING FORM)
            # Based on screenshot, it's an <a> tag with class 'bid-suggestion-block__action'
            generate_button_selectors = [
                # Most specific - link with exact class (from screenshot)
                "//a[contains(@class, 'bid-suggestion-block__action')]",
                "//a[contains(@class, 'bid-suggestion-link')]",
                "//a[contains(@class, 'bid-suggestion') and contains(@class, 'action')]",
                # Link with text
                "//a[contains(text(), 'Сгенерировать')]",
                "//a[normalize-space(text())='Сгенерировать']",
                # Button variants
                "//button[contains(text(), 'Сгенерировать')]",
                "//button[contains(@class, 'bid-suggestion-block__action')]",
                "//button[contains(@class, 'bid-suggestion')]",
                # Generic
                "//*[contains(@class, 'bid-suggestion-block__action')]",
                "//*[contains(@class, 'bid-suggestion-link')]",
                "//*[contains(text(), 'Сгенерировать') and (self::a or self::button)]",
                "//button[contains(text(), 'Generate')]",
                "//a[contains(text(), 'Generate')]",
            ]
            
            generate_button = None
            for selector in generate_button_selectors:
                try:
                    print(f"🔍 Поиск кнопки генерации: {selector[:60]}...")
                    generate_button = self.wait_for_clickable(By.XPATH, selector, timeout=5)
                    if generate_button:
                        print(f"✅ Найдена кнопка генерации!")
                        break
                except Exception as e:
                    continue
            
            if not generate_button:
                # Try one more time with longer wait and debug info
                print("⏳ Повторная попытка поиска кнопки генерации...")
                time.sleep(3)
                
                # Try to find any element containing "Сгенерировать"
                try:
                    all_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Сгенерировать')]")
                    print(f"🔍 Найдено элементов с текстом 'Сгенерировать': {len(all_elements)}")
                    for elem in all_elements:
                        try:
                            if elem.is_displayed() and elem.is_enabled():
                                print(f"   - Элемент: {elem.tag_name}, классы: {elem.get_attribute('class')}")
                                generate_button = elem
                                break
                        except:
                            continue
                except:
                    pass
                
                # Try selectors again
                for selector in generate_button_selectors[:8]:  # Try first 8 most specific
                    try:
                        generate_button = self.wait_for_clickable(By.XPATH, selector, timeout=3)
                        if generate_button:
                            print(f"✅ Найдена кнопка генерации при повторной попытке!")
                            break
                    except:
                        continue
            
            if not generate_button:
                return (False, "Не удалось найти кнопку 'Сгенерировать'. Убедитесь, что форма открыта и у вас премиум аккаунт.", 0, 0)
            
            if not self.safe_click(generate_button):
                return (False, "Не удалось нажать кнопку 'Сгенерировать'", 0, 0)
            
            # Wait for AI generation to complete - check if comment field is filled
            print("⏳ Ожидание генерации комментария...")
            comment_generated = False
            for attempt in range(15):  # Wait up to 15 seconds
                time.sleep(1)
                try:
                    # Check if comment/description field has content
                    comment_selectors = [
                        "//textarea[@name='comment']",
                        "//textarea[@name='description']",
                        "//textarea[@name='message']",
                        "//textarea[contains(@class, 'comment')]",
                        "//textarea[contains(@class, 'description')]",
                    ]
                    
                    for selector in comment_selectors:
                        try:
                            comment_field = self.driver.find_element(By.XPATH, selector)
                            if comment_field and comment_field.get_attribute('value'):
                                comment_generated = True
                                break
                        except:
                            continue
                    
                    if comment_generated:
                        print("✅ Комментарий сгенерирован")
                        break
                except:
                    pass
            
            if not comment_generated:
                print("⚠️ Комментарий не сгенерирован автоматически, продолжаем...")
            
            time.sleep(1)
            
            # Calculate bid amount and deadline
            bid_amount = self.calculate_bid_amount(project_budget)
            bid_deadline = self.calculate_deadline(project_deadline)
            
            # NOW fill in deadline FIRST, then amount
            # Fill in deadline
            deadline_selectors = [
                "//input[@name='deadline']",
                "//input[@name='days']",
                "//input[@name='duration']",
                "//input[contains(@placeholder, 'дн')]",
                "//input[contains(@placeholder, 'days')]",
                "//input[@type='number' and contains(@class, 'deadline')]",
                "//input[@type='number' and contains(@class, 'days')]",
                "//input[contains(@id, 'deadline')]",
                "//input[contains(@id, 'days')]",
            ]
            
            deadline_input = None
            for selector in deadline_selectors:
                try:
                    deadline_input = self.wait_for_element(By.XPATH, selector, timeout=5)
                    if deadline_input:
                        break
                except:
                    continue
            
            if deadline_input:
                deadline_input.clear()
                deadline_input.send_keys(str(bid_deadline))
                print(f"📅 Заполнен срок: {bid_deadline} дней")
                time.sleep(0.5 + random.uniform(0, 0.5))
            else:
                print("⚠️ Не найдено поле для срока выполнения")
            
            # Fill in bid amount
            amount_selectors = [
                "//input[@name='amount']",
                "//input[@name='cost']",
                "//input[@name='price']",
                "//input[contains(@placeholder, 'UAH')]",
                "//input[contains(@placeholder, 'грн')]",
                "//input[@type='number' and contains(@class, 'amount')]",
            ]
            
            amount_input = None
            for selector in amount_selectors:
                try:
                    amount_input = self.wait_for_element(By.XPATH, selector, timeout=5)
                    if amount_input:
                        break
                except:
                    continue
            
            if amount_input:
                amount_input.clear()
                amount_input.send_keys(str(int(bid_amount)))
                print(f"💰 Заполнена стоимость: {int(bid_amount)} грн")
                time.sleep(0.5 + random.uniform(0, 0.5))
            else:
                print("⚠️ Не найдено поле для стоимости")
            
            # Submit the bid form
            submit_selectors = [
                "//button[@type='submit']",
                "//button[contains(text(), 'Отправить')]",
                "//button[contains(text(), 'Submit')]",
                "//button[contains(text(), 'Отправить ставку')]",
                "//button[contains(@class, 'submit')]",
            ]
            
            submit_button = None
            for selector in submit_selectors:
                try:
                    submit_button = self.wait_for_clickable(By.XPATH, selector, timeout=5)
                    if submit_button:
                        break
                except:
                    continue
            
            if not submit_button:
                return (False, "Не удалось найти кнопку отправки ставки", bid_amount, bid_deadline)
            
            if not self.safe_click(submit_button):
                return (False, "Не удалось отправить ставку", bid_amount, bid_deadline)
            
            time.sleep(2 + random.uniform(0, 1))
            
            # Check if bid was successful (look for success message or redirect)
            # This is a basic check - may need adjustment based on actual site behavior
            current_url = self.driver.current_url
            if 'project' not in current_url.lower() or 'success' in current_url.lower():
                return (True, "Ставка успешно отправлена", bid_amount, bid_deadline)
            
            # Look for error messages
            error_selectors = [
                "//div[contains(@class, 'error')]",
                "//div[contains(@class, 'alert-danger')]",
                "//span[contains(@class, 'error')]",
            ]
            
            for selector in error_selectors:
                try:
                    error_elem = self.driver.find_element(By.XPATH, selector)
                    if error_elem.is_displayed():
                        error_text = error_elem.text[:100]
                        return (False, f"Ошибка при отправке: {error_text}", bid_amount, bid_deadline)
                except:
                    continue
            
            # If no error found, assume success
            return (True, "Ставка отправлена", bid_amount, bid_deadline)
            
        except Exception as e:
            return (False, f"Ошибка при выполнении: {str(e)}", 0, 0)
    
    def close(self):
        """Close browser and save cookies."""
        if self.driver:
            try:
                self.save_cookies()
            except:
                pass
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
    
    def __enter__(self):
        """Context manager entry."""
        if not self.driver:
            self.driver = self.init_driver()
            self.load_cookies()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

