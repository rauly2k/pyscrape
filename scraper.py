"""Zentrada product scraper using Selenium - OPTIMIZED VERSION"""

import time
import random
import re
from typing import Dict, List, Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import config


class ZentradaScraper:
    """Modern Selenium 4 scraper for Zentrada with automatic ChromeDriver management"""

    def __init__(self, headless: bool = False):
        """
        Initialize scraper

        Args:
            headless: Run browser in headless mode (faster, no UI)
        """
        self.driver: Optional[webdriver.Chrome] = None
        self.is_logged_in = False
        self.headless = headless

    def start(self):
        """Initialize Chrome browser with modern Selenium 4 syntax"""
        print("🚀 Pornesc browser-ul...")

        # Chrome options
        options = Options()

        if self.headless:
            options.add_argument('--headless=new')  # New headless mode
            print("  Mode: Headless (fără UI)")
        else:
            print("  Mode: Normal (cu UI)")

        options.add_argument('--start-maximized')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--lang=en-US')

        # User agent to avoid detection
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        # Performance optimizations
        prefs = {
            'profile.default_content_setting_values': {
                'images': 2,  # Disable images for faster loading
                'plugins': 2,
                'popups': 2,
                'geolocation': 2,
                'notifications': 2,
                'media_stream': 2,
            }
        }
        options.add_experimental_option('prefs', prefs)
        options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)

        try:
            # Automatic ChromeDriver management with webdriver-manager
            print("  Verific ChromeDriver...")
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            print("✅ Browser pornit cu succes!")

            # Set timeouts
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)

        except Exception as e:
            print(f"❌ EROARE la pornirea browser-ului: {str(e)}")
            print("\nSoluții:")
            print("1. Instalează Chrome browser dacă nu e instalat")
            print("2. Rulează: pip install webdriver-manager --upgrade")
            print("3. Încearcă să ștergi cache-ul: pip cache purge")
            raise

    def login(self):
        """Login to Zentrada with optimized flow"""
        if not config.ZENTRADA_EMAIL or not config.ZENTRADA_PASSWORD:
            raise ValueError("❌ Adaugă credențialele Zentrada în config.py!")

        print("\n🔐 Autentificare Zentrada...")

        # Navigate to homepage
        print("  → Accesez zentrada.com...")
        self.driver.get("https://www.zentrada.com/eu/")
        time.sleep(2)

        # Accept cookies
        print("  → Accept cookies...")
        try:
            cookie_btn = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.cc-btn.cc-allow[aria-label="allow cookies"]'))
            )
            cookie_btn.click()
            print("    ✓ Cookies acceptate")
            time.sleep(1)
        except TimeoutException:
            print("    ⚠ Popup cookies nu a fost găsit (probabil deja acceptat)")

        # Click login button
        print("  → Deschid popup login...")
        try:
            login_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.nav-button.profile[data-cy="e2e-login-myzentrada-dialog-button"]'))
            )
            login_btn.click()
            print("    ✓ Popup deschis")
            time.sleep(2)
        except Exception as e:
            print(f"    ❌ Nu pot găsi butonul de login: {str(e)}")
            raise

        # Fill email
        print(f"  → Introduc email: {config.ZENTRADA_EMAIL}")
        try:
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="email"][data-cy="login-email-input"]'))
            )
            email_input.clear()
            email_input.send_keys(config.ZENTRADA_EMAIL)
            print("    ✓ Email introdus")
            time.sleep(0.5)
        except Exception as e:
            print(f"    ❌ Eroare la introducerea email-ului: {str(e)}")
            raise

        # Fill password
        print("  → Introduc parola...")
        try:
            password_input = self.driver.find_element(By.CSS_SELECTOR, 'input[name="password"][data-cy="login-password-input"]')
            password_input.clear()
            password_input.send_keys(config.ZENTRADA_PASSWORD)
            print("    ✓ Parolă introdusă")
            time.sleep(0.5)
        except Exception as e:
            print(f"    ❌ Eroare la introducerea parolei: {str(e)}")
            raise

        # Submit login
        print("  → Trimit formularul...")
        try:
            submit_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//button[contains(@class, "mat-mdc-raised-button") and contains(@class, "mat-primary")]//span[text()=" Login "]'))
            )
            submit_btn.click()
            print("    ✓ Formular trimis")
        except:
            # Fallback
            try:
                submit_btn = self.driver.find_element(By.CSS_SELECTOR, 'button.mat-mdc-raised-button.mat-primary')
                submit_btn.click()
                print("    ✓ Formular trimis (fallback)")
            except Exception as e:
                print(f"    ❌ Nu pot trimite formularul: {str(e)}")
                raise

        # Wait for login
        print("  → Aștept finalizarea autentificării...")
        time.sleep(5)

        # Check for errors
        try:
            error_elem = self.driver.find_element(By.XPATH, "//*[contains(text(), 'login has been denied') or contains(text(), 'protection systems')]")
            if error_elem:
                print("\n" + "="*70)
                print("⚠️  DETECTAT SISTEM ANTI-BOT")
                print("="*70)
                print("Site-ul a detectat automatizarea. Soluții:")
                print("1. Completează CAPTCHA-ul manual în browser")
                print("2. Apasă ENTER aici după ce te-ai logat manual")
                print("3. SAU folosește scraping manual: python main_manual.py urls.txt")
                print("="*70)
                input("\n👉 Apasă ENTER după login manual, sau Ctrl+C pentru a ieși...")
        except:
            pass  # No error, login successful

        current_url = self.driver.current_url
        print(f"    URL curent: {current_url}")

        self.is_logged_in = True
        print("✅ Autentificare reușită!\n")

    def scrape_product(self, url: str) -> Dict:
        """
        Scrape a single product page

        Args:
            url: Product URL

        Returns:
            Dictionary with product data
        """
        if not self.is_logged_in:
            self.login()

        print(f"📦 Scrap produs: {url}")

        try:
            # Navigate to product
            self.driver.get(url)
            time.sleep(3)  # Wait for page load

            # Get HTML
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'lxml')

            # Extract article number FIRST (needed for image filtering)
            article_number = self._extract_article_number(soup)

            # Extract all fields
            product_data = {
                'url': url,
                'product_name': self._extract_product_name(soup),
                'article_number': article_number,
                'brand': self._extract_brand(soup),
                'description': self._extract_description(soup),
                'price': self._extract_price(soup),
                'piece_per_pu': self._extract_piece_per_pu(soup),
                'mix_order': self._extract_mix_order(soup),
                'min_order_quantity': self._extract_min_order_quantity(soup),
                'ean_sku': self._extract_ean(soup),
                'pfi': self._extract_pfi(soup),
                'pu_per_pallet': self._extract_pu_per_pallet(soup),
                'pu_per_layer': self._extract_pu_per_layer(soup),
                'country_of_origin': self._extract_country_of_origin(soup),
                'images': self._extract_images(soup, article_number),  # Pass article_number
            }

            print(f"  ✓ {product_data['product_name'][:50]}...")

            # Random delay between requests
            delay = random.uniform(*config.DELAY_BETWEEN_REQUESTS)
            print(f"  ⏱️  Pauză {delay:.1f}s...")
            time.sleep(delay)

            return product_data

        except Exception as e:
            print(f"  ❌ Eroare scraping: {str(e)}")
            return {
                'url': url,
                'error': str(e),
                'product_name': '',
                'article_number': '',
                'brand': '',
                'description': '',
                'price': '',
                'piece_per_pu': '',
                'mix_order': False,
                'min_order_quantity': '',
                'ean_sku': '',
                'pfi': '',
                'pu_per_pallet': '',
                'pu_per_layer': '',
                'country_of_origin': '',
                'images': [],
            }

    # ========================================
    # EXTRACTION METHODS
    # ========================================

    def _extract_product_name(self, soup: BeautifulSoup) -> str:
        """Extract product name"""
        title = soup.find('h1', class_='product-title')
        if title:
            return title.get_text(strip=True)
        title = soup.find('h1')
        return title.get_text(strip=True) if title else ""

    def _extract_article_number(self, soup: BeautifulSoup) -> str:
        """Extract article number"""
        return self._extract_field(soup, ["Article number", "Art. No.", "Article No."])

    def _extract_brand(self, soup: BeautifulSoup) -> str:
        """Extract brand"""
        # Try Brand Line first
        info_rows = soup.find_all('div', class_='info-row')
        for row in info_rows:
            col1 = row.find('div', class_='info-col1')
            if col1 and 'Brand Line' in col1.get_text():
                col2 = row.find('div', class_='info-col2')
                if col2:
                    return col2.get_text(strip=True)

        # Fallback to generic brand field
        return self._extract_field(soup, ["Brand", "Manufacturer", "Brand Line"])

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract product description"""
        desc = soup.find('div', class_='prod-desc')
        if desc and 'translated-infos' not in desc.get('class', []):
            desc_text = desc.get_text(separator=' ', strip=True)
            desc_text = re.sub(r'\s+', ' ', desc_text)
            return desc_text
        return ""

    def _extract_price(self, soup: BeautifulSoup) -> str:
        """Extract price per piece"""
        price_elem = soup.find('h2', class_='price-per-piece')
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            # Remove "/Piece" suffix
            price_text = price_text.split('/')[0].strip()
            return price_text
        return ""

    def _extract_piece_per_pu(self, soup: BeautifulSoup) -> str:
        """Extract pieces per packaging unit"""
        return self._extract_field(soup, ["Piece per PU"])

    def _extract_mix_order(self, soup: BeautifulSoup) -> bool:
        """Check if MixOrder is available"""
        mix_elem = soup.find(class_='text-mix-order')
        if mix_elem and 'MixOrder' in mix_elem.get_text():
            return True
        page_text = soup.get_text()
        return "MixOrder" in page_text or "Mix Order" in page_text

    def _extract_min_order_quantity(self, soup: BeautifulSoup) -> str:
        """Extract minimum order quantity"""
        return self._extract_field(soup, ["min order quantity", "Minimum Order", "Min. Order"])

    def _extract_ean(self, soup: BeautifulSoup) -> str:
        """Extract EAN/SKU"""
        return self._extract_field(soup, ["EAN"])

    def _extract_pfi(self, soup: BeautifulSoup) -> str:
        """Extract PFI"""
        return self._extract_field(soup, ["PFI"])

    def _extract_pu_per_pallet(self, soup: BeautifulSoup) -> str:
        """Extract PU per pallet"""
        return self._extract_field(soup, ["PU per pallet", "PU/Pallet"])

    def _extract_pu_per_layer(self, soup: BeautifulSoup) -> str:
        """Extract PU per layer"""
        return self._extract_field(soup, ["PU per layer", "PU/Layer"])

    def _extract_country_of_origin(self, soup: BeautifulSoup) -> str:
        """Extract country of origin"""
        return self._extract_field(soup, ["Country of origin", "Origin"])

    def _extract_images(self, soup, article_number: str) -> List[str]:
        """
        Extract ALL product images, filtered by article number to avoid related products
        - Main product-image-output
        - Carousel/gallery images
        - small-img-holder (ALL thumbnails)
        - Fallback: get images from product container if article filtering fails

        Args:
            soup: BeautifulSoup object
            article_number: Article number to filter images

        Returns:
            List of image URLs (max MAX_IMAGES from config)
        """
        images = []
        seen_urls = set()  # Avoid duplicates

        # Normalize article number for matching
        article_num_clean = str(article_number).strip()

        # Find product container to limit scope
        product_container = soup.find('div', class_='product-container-img')
        if not product_container:
            product_container = soup  # Fallback to whole page

        # Collect ALL image sources first
        all_img_sources = []

        # 1. Main product image (product-image-output)
        main_imgs = product_container.find_all('img', class_='product-image-output')
        all_img_sources.extend(main_imgs)

        # 2. Carousel images (owl-carousel contains additional product images)
        carousel = product_container.find('owl-carousel-o')
        if carousel:
            all_img_sources.extend(carousel.find_all('img'))

        # 3. Small image holder - CRITICAL: Get ALL thumbnails
        # Try multiple ways to find small-img-holder to catch all variations
        small_holders = product_container.find_all('div', class_=lambda x: x and 'small-img-holder' in x)
        for holder in small_holders:
            holder_imgs = holder.find_all('img')
            all_img_sources.extend(holder_imgs)
            print(f"  📸 Found {len(holder_imgs)} images in small-img-holder")

        # Now process all found images with article number filtering
        filtered_images = []
        for img in all_img_sources:
            src = img.get('src', '')
            if self._is_valid_product_image(src, article_num_clean):
                # Convert to 600x600
                src_high_res = self._convert_to_high_res(src)
                if src_high_res not in seen_urls:
                    filtered_images.append(src_high_res)
                    seen_urls.add(src_high_res)

        # If we got images with article filtering, use them
        if filtered_images:
            images = filtered_images
            print(f"  ✓ Extracted {len(images)} images with article filter '{article_num_clean}'")
        else:
            # FALLBACK: No images found with article number filtering
            print(f"  ⚠️ No images with article '{article_num_clean}', using fallback...")

            # Try all sources again without article number filter
            for img in all_img_sources:
                src = img.get('src', '')
                # Only check for CDN domain and exclude logos (no article number check)
                if src and config.IMAGE_CDN_DOMAIN in src:
                    if 'salesroom.jpg' not in src and 'brands/' not in src and '/Logo' not in src:
                        src_high_res = self._convert_to_high_res(src)
                        if src_high_res not in seen_urls:
                            images.append(src_high_res)
                            seen_urls.add(src_high_res)
                            # Limit fallback to avoid getting too many unrelated images
                            if len(images) >= config.MAX_IMAGES:
                                break
            print(f"  ✓ Fallback extracted {len(images)} images")

        # Limit to MAX_IMAGES
        return images[:config.MAX_IMAGES]

    def _convert_to_high_res(self, src: str) -> str:
        """Convert image URL to 600x600 resolution"""
        # Handle various resolution parameters
        src = src.replace('w=210&h=210', 'w=600&h=600')
        src = src.replace('w=200&h=200', 'w=600&h=600')
        src = src.replace('w=150&h=150', 'w=600&h=600')
        # If already at 600x600 or higher, keep as is
        return src

    def _is_valid_product_image(self, src: str, article_number: str) -> bool:
        """
        Check if image URL is a valid product image
        - Must contain CDN domain
        - Must contain article number in filename OR path
        - Must not be a vendor logo or brand image

        Args:
            src: Image source URL
            article_number: Article number to match

        Returns:
            True if valid product image
        """
        if not src or config.IMAGE_CDN_DOMAIN not in src:
            return False

        # Exclude vendor/brand logos
        if 'salesroom.jpg' in src or 'brands/' in src or '/Logo' in src:
            return False

        # Skip if no article number provided
        if not article_number or len(article_number) < 3:
            return False

        # Must contain article number somewhere in the URL
        # Examples:
        # - /191624/image.jpg (in path)
        # - 13573.jpg, 13573_1.jpg (in filename)
        if article_number in src:
            return True

        return False

    def _extract_field(self, soup: BeautifulSoup, field_names: List[str]) -> str:
        """
        Generic method to extract a field from Product Information table

        Args:
            soup: BeautifulSoup object
            field_names: List of possible field names to search for

        Returns:
            Field value or empty string
        """
        info_tables = soup.find_all('div', class_='info-table-row')
        for table in info_tables:
            label_cell = table.find('div', class_='info-table-cell label')
            if label_cell:
                label_text = label_cell.get_text(strip=True)
                for field_name in field_names:
                    if field_name.lower() in label_text.lower():
                        value_cells = table.find_all('div', class_='info-table-cell')
                        if len(value_cells) >= 2:
                            return value_cells[1].get_text(strip=True)
        return ""

    def close(self):
        """Close browser and cleanup"""
        if self.driver:
            try:
                print("\n🔒 Închid browser-ul...")
                self.driver.quit()
                print("✅ Browser închis.\n")
            except:
                pass
