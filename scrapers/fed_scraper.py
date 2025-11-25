"""Federal Reserve Economic Data (FEDS) papers scraper"""

import re
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper


class FedScraper(BaseScraper):
    """Scraper for Federal Reserve FEDS papers"""
    
    def __init__(self, headless=True, debug=False, config=None):
        """Initialize the scraper"""
        super().__init__(headless, debug, config)
        self.base_url = "https://www.federalreserve.gov/econres/feds/1996.htm"
        self.papers_data = []
        
    def navigate_to_year_selection(self):
        """Navigate to the year selection page"""
        try:
            print("\n📍 Navigating to FEDS papers main page...")
            self.driver.get(self.base_url)
            self._random_delay(2, 3)
            
            # Click on the year selection link
            year_link_selector = "#article > div.col-xs-12.col-md-12.col-sm-12.heading.feds-note > h5:nth-child(1) > a"
            year_link = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, year_link_selector))
            )
            
            print("  🔗 Clicking year selection link...")
            self._safe_click(year_link)
            self._random_delay(
                self.config.get('delays', {}).get('after_click_min', 1),
                self.config.get('delays', {}).get('after_click_max', 2)
            )
            
            print("  ✅ Successfully navigated to year selection page")
            return True
            
        except Exception as e:
            print(f"  ❌ ERROR: Failed to navigate to year selection: {str(e)}")
            return False
    
    def get_available_years(self):
        """Get list of available years from the page"""
        try:
            print("\n📅 Getting available years...")
            
            # Find all year links
            year_list_selector = "#article > div.panel.panel-unstyled > div > ul"
            year_list = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, year_list_selector))
            )
            
            year_elements = year_list.find_elements(By.TAG_NAME, "li")
            available_years = []
            
            for elem in year_elements:
                try:
                    year_text = elem.text.strip()
                    # Extract year from text (might be just year or "FEDS Notes 2024" etc)
                    year_match = re.search(r'\b(19\d{2}|20\d{2})\b', year_text)
                    if year_match:
                        available_years.append(int(year_match.group(1)))
                except:
                    continue
            
            available_years = sorted(list(set(available_years)))
            print(f"  ✅ Found {len(available_years)} years: {min(available_years)} to {max(available_years)}")
            return available_years
            
        except Exception as e:
            print(f"  ❌ ERROR: Failed to get available years: {str(e)}")
            return []
    
    def navigate_to_year(self, year):
        """Navigate to a specific year's page"""
        try:
            print(f"\n📆 Navigating to year {year}...")
            
            # Find the year link
            year_links = self.driver.find_elements(By.CSS_SELECTOR, "#article li a")
            
            for link in year_links:
                if str(year) in link.text:
                    print(f"  🔗 Clicking on year {year} link...")
                    self._safe_click(link)
                    self._random_delay(2, 3)
                    print(f"  ✅ Successfully navigated to year {year}")
                    return True
            
            print(f"  ⚠️  Year {year} not found in available years")
            return False
            
        except Exception as e:
            print(f"  ❌ ERROR: Failed to navigate to year {year}: {str(e)}")
            return False
    
    def scrape_year_papers(self, year, existing_feds_numbers=None):
        """Scrape all papers from a specific year"""
        papers = []
        existing_feds_numbers = existing_feds_numbers or set()
        
        try:
            print(f"\n📚 Scraping papers for year {year}...")
            
            # Get page source
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'lxml')
            
            # Find all paper divs
            paper_divs = soup.find_all('div', class_='col-xs-12 col-md-9 heading feds-note')
            
            if not paper_divs:
                print(f"  ⚠️  No papers found for year {year}")
                return papers
            
            print(f"  📄 Found {len(paper_divs)} papers to process")
            
            for idx, paper_div in enumerate(paper_divs, 1):
                try:
                    # Extract FEDS number first to check if already exists
                    feds_span = paper_div.find('span', class_='badge badge--feds')
                    if not feds_span:
                        continue
                    
                    feds_text = feds_span.get_text(strip=True)
                    feds_number = re.sub(r'^FEDS\s*', '', feds_text).strip()
                    
                    if feds_number in existing_feds_numbers:
                        print(f"  ⏭️  [{idx}/{len(paper_divs)}] Skipping {feds_number} (already exists)")
                        continue
                    
                    paper_data = self.extract_paper_data(paper_div, year)
                    
                    if paper_data:
                        papers.append(paper_data)
                        print(f"  ✅ [{idx}/{len(paper_divs)}] Extracted: {feds_number} - {paper_data['title'][:50]}...")
                    
                    # Delay between papers
                    if idx < len(paper_divs):
                        self._random_delay(
                            self.config.get('delays', {}).get('between_papers_min', 0.5),
                            self.config.get('delays', {}).get('between_papers_max', 1.5)
                        )
                        
                except Exception as e:
                    print(f"  ⚠️  [{idx}/{len(paper_divs)}] Error extracting paper: {str(e)}")
                    continue
            
            print(f"\n  ✅ Successfully scraped {len(papers)} new papers from year {year}")
            return papers
            
        except Exception as e:
            print(f"  ❌ ERROR: Failed to scrape year {year}: {str(e)}")
            if self.debug:
                import traceback
                traceback.print_exc()
            return papers
    
    def extract_paper_data(self, paper_div, year):
        """Extract data from a single paper div"""
        try:
            data = {
                'feds_number': '',
                'year': year,
                'publication_date': '',
                'title': '',
                'authors': '',
                'jel_codes': '',
                'field_category': '',
                'paper_url': self.driver.current_url,
                'abstract': '',
                'source': 'Federal Reserve',
                'scrape_timestamp': datetime.now().isoformat(),
                'pdf_url': ''
            }
            
            # Extract FEDS number
            feds_span = paper_div.find('span', class_='badge badge--feds')
            if feds_span:
                feds_text = feds_span.get_text(strip=True)
                data['feds_number'] = re.sub(r'^FEDS\s*', '', feds_text).strip()
            
            # Extract publication date
            time_elem = paper_div.find('time')
            if time_elem:
                date_text = time_elem.get_text(strip=True)
                data['publication_date'] = self.parse_publication_date(date_text)
                
                # Extract year from publication date if not already set
                year_match = re.search(r'(19\d{2}|20\d{2})', date_text)
                if year_match:
                    data['year'] = int(year_match.group(1))
            
            # Extract title
            title_elem = paper_div.find('h5')
            if title_elem:
                title_link = title_elem.find('a')
                if title_link:
                    data['title'] = title_link.get_text(strip=True)
            
            # Extract authors
            authors_div = paper_div.find('div', class_='authors')
            if authors_div:
                authors_p = authors_div.find('p')
                if authors_p:
                    # Clean up authors text
                    authors_text = authors_p.get_text(strip=True)
                    # Split by 'and' or comma
                    authors_text = re.sub(r'\s+and\s+', ', ', authors_text)
                    data['authors'] = authors_text
            
            # Try to extract abstract without clicking
            abstract_div = paper_div.find('div', class_='collapse')
            if abstract_div:
                # Look for abstract paragraph
                abstract_paras = abstract_div.find_all('p')
                for para in abstract_paras:
                    text = para.get_text(strip=True)
                    if text.startswith('Abstract:'):
                        data['abstract'] = text.replace('Abstract:', '').strip()
                    elif not text.startswith('Keywords:') and not text.startswith('Full paper'):
                        # This might be the abstract content
                        if not data['abstract'] and len(text) > 100:
                            data['abstract'] = text
                
                # Extract PDF/PS link
                pdf_link = abstract_div.find('a', href=True)
                if pdf_link and ('paper' in pdf_link.text.lower() or 'pdf' in pdf_link.text.lower()):
                    pdf_url = pdf_link['href']
                    if not pdf_url.startswith('http'):
                        pdf_url = f"https://www.federalreserve.gov{pdf_url}"
                    data['pdf_url'] = pdf_url
            
            return data
            
        except Exception as e:
            if self.debug:
                print(f"    ⚠️  Error extracting paper data: {str(e)}")
            return None
    
    def parse_publication_date(self, date_text):
        """Parse publication date to ISO format"""
        try:
            # Try to parse "Month Year" format
            month_year_match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(19\d{2}|20\d{2})', date_text)
            if month_year_match:
                month_str = month_year_match.group(1)
                year_str = month_year_match.group(2)
                
                months = {
                    'January': '01', 'February': '02', 'March': '03', 'April': '04',
                    'May': '05', 'June': '06', 'July': '07', 'August': '08',
                    'September': '09', 'October': '10', 'November': '11', 'December': '12'
                }
                
                month_num = months.get(month_str, '01')
                return f"{year_str}-{month_num}-01"
            
            # Try to extract just year
            year_match = re.search(r'(19\d{2}|20\d{2})', date_text)
            if year_match:
                return f"{year_match.group(1)}-01-01"
            
            return ''
            
        except:
            return ''
    
    def scrape_years_range(self, start_year, end_year, existing_feds_numbers=None):
        """Scrape papers for a range of years"""
        all_papers = []
        existing_feds_numbers = existing_feds_numbers or set()
        
        try:
            if not self.driver:
                self.setup_driver()
            
            # Navigate to year selection page
            if not self.navigate_to_year_selection():
                return all_papers
            
            # Get available years
            available_years = self.get_available_years()
            if not available_years:
                print("❌ No available years found")
                return all_papers
            
            # Filter years based on user range
            years_to_scrape = [y for y in range(start_year, end_year + 1) if y in available_years]
            
            if not years_to_scrape:
                print(f"⚠️  No years in range {start_year}-{end_year} are available")
                return all_papers
            
            print(f"\n📊 Will scrape {len(years_to_scrape)} years: {years_to_scrape}")
            
            for year_idx, year in enumerate(years_to_scrape, 1):
                print(f"\n{'='*60}")
                print(f"📅 YEAR [{year_idx}/{len(years_to_scrape)}]: {year}")
                print(f"{'='*60}")
                
                # Navigate back to year selection if not first year
                if year_idx > 1:
                    self.driver.back()
                    self._random_delay(2, 3)
                
                # Navigate to specific year
                if self.navigate_to_year(year):
                    # Scrape papers for this year
                    year_papers = self.scrape_year_papers(year, existing_feds_numbers)
                    all_papers.extend(year_papers)
                    
                    # Update existing FEDS numbers
                    for paper in year_papers:
                        existing_feds_numbers.add(paper['feds_number'])
                    
                    # Yield papers for incremental saving
                    if year_papers:
                        yield year, year_papers
                
                # Delay between years
                if year_idx < len(years_to_scrape):
                    delay = self._random_delay(
                        self.config.get('delays', {}).get('between_years_min', 3),
                        self.config.get('delays', {}).get('between_years_max', 5)
                    )
            
        except Exception as e:
            print(f"\n❌ FATAL ERROR: {str(e)}")
            if self.debug:
                import traceback
                traceback.print_exc()
        
        return all_papers