"""Base scraper class with shared functionality"""

import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import platform
import os


class BaseScraper:
    """Base class for all scrapers with shared functionality"""
    
    def __init__(self, headless=True, debug=False, config=None):
        """Initialize base scraper"""
        self.headless = headless
        self.debug = debug
        self.config = config or {}
        self.driver = None
        
    def setup_driver(self):
        """Setup Chrome WebDriver with anti-detection options"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless=new')
        
        # Anti-detection measures
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Chrome preferences
        prefs = {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Standard arguments
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        chrome_options.add_argument('--log-level=3')
        
        try:
            print("🔧 Setting up ChromeDriver...")
            
            driver_path = ChromeDriverManager().install()
            
            if platform.system() == "Windows" and not driver_path.endswith('.exe'):
                possible_paths = [
                    os.path.join(driver_path, 'chromedriver.exe'),
                    os.path.join(driver_path, 'chromedriver-win32', 'chromedriver.exe'),
                    os.path.join(driver_path, 'chromedriver-win64', 'chromedriver.exe'),
                ]
                for path in possible_paths:
                    if os.path.exists(path):
                        driver_path = path
                        break
            
            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
        except Exception as e:
            print(f"❌ ERROR: Failed to initialize Chrome: {str(e)}")
            raise Exception("Could not start Chrome browser")
        
        # Remove webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("✅ Browser initialized successfully")
    
    def _random_delay(self, min_seconds, max_seconds):
        """Sleep for random duration"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def _safe_click(self, element, max_retries=2):
        """Safely click element with retry logic"""
        for attempt in range(max_retries):
            try:
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                self._random_delay(0.3, 0.6)
                element.click()
                return True
            except Exception as e:
                if attempt < max_retries - 1:
                    self._random_delay(1, 1.5)
                    try:
                        self.driver.execute_script("arguments[0].click();", element)
                        return True
                    except:
                        continue
                else:
                    if self.debug:
                        print(f"  ⚠️  Click failed after {max_retries} attempts: {str(e)}")
                    return False
        return False
    
    def close(self):
        """Close the WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
                print("\n✅ Browser closed")
            except:
                pass