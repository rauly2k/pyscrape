"""
Full Category Scraper with Pagination Support
Can scrape multiple pages from a category
"""

import time
import json
import re
from datetime import datetime
from typing import Dict, List, Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import config


class CategoryScraper:
    """Scraper for Zentrada categories with pagination"""

    def __init__(self):
        self.driver: Optional[webdriver.Chrome] = None

    def connect_to_chrome(self) -> bool:
        """Connect to existing Chrome with debugging enabled"""
        try:
            options = Options()
            options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            return True
        except Exception as e:
            print(f"❌ Nu pot conecta la Chrome: {str(e)}")
            return False

    def scrape_category(self, category_url: str, max_pages: int = 1,
                       progress_callback=None) -> List[Dict]:
        """
        Scrape products from category

        Args:
            category_url: Category URL
            max_pages: Maximum number of pages to scrape
            progress_callback: Optional callback function(current, total, message)

        Returns:
            List of product dictionaries
        """
        if not self.driver:
            raise Exception("Browser not connected!")

        all_products = []

        for page_num in range(1, max_pages + 1):
            if progress_callback:
                progress_callback(page_num, max_pages, f"Scraping page {page_num}/{max_pages}...")

            # Navigate to page
            page_url = self._get_page_url(category_url, page_num)
            self.driver.get(page_url)
            time.sleep(5)  # Wait for load

            # Find products
            product_cards = self.driver.find_elements(By.CSS_SELECTOR, "div.custom-card.grid-list-element")

            if not product_cards:
                if progress_callback:
                    progress_callback(page_num, max_pages, f"No products on page {page_num}")
                break

            # Scrape each product
            for i, card in enumerate(product_cards, 1):
                try:
                    link = card.find_element(By.TAG_NAME, "a")
                    product_url = link.get_attribute('href')

                    if progress_callback:
                        progress_callback(
                            page_num, max_pages,
                            f"Page {page_num}/{max_pages} - Product {i}/{len(product_cards)}"
                        )

                    product = self._scrape_product(product_url)
                    if product:
                        all_products.append(product)

                except Exception as e:
                    print(f"Error scraping product {i}: {str(e)}")
                    continue

        return all_products

    def _get_page_url(self, base_url: str, page_num: int) -> str:
        """Generate URL for specific page number"""
        if page_num == 1:
            return base_url
        # Zentrada uses ?page=2 format
        separator = '&' if '?' in base_url else '?'
        return f"{base_url}{separator}page={page_num}"

    def _scrape_product(self, product_url: str) -> Optional[Dict]:
        """Scrape single product"""
        try:
            # Open in new tab
            self.driver.execute_script(f"window.open('{product_url}', '_blank');")
            time.sleep(1)

            # Switch to new tab
            self.driver.switch_to.window(self.driver.window_handles[-1])
            time.sleep(3)

            # Parse HTML
            soup = BeautifulSoup(self.driver.page_source, 'lxml')

            # Extract data
            product = {
                'url': product_url,
                'product_name': self._extract_product_name(soup),
                'article_number': self._extract_article_number(soup),
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
                'images': self._extract_images(soup),
                'scraped_at': datetime.utcnow().isoformat() + 'Z'
            }

            # Close tab
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])

            time.sleep(2)
            return product

        except Exception as e:
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
            except:
                pass
            return None

    # ========================================
    # EXTRACTION METHODS
    # ========================================

    def _extract_product_name(self, soup) -> str:
        title = soup.find('h1', class_='product-title')
        if title:
            return title.get_text(strip=True)
        title = soup.find('h1')
        return title.get_text(strip=True) if title else ""

    def _extract_field(self, soup, field_names: List[str]) -> str:
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

    def _extract_article_number(self, soup) -> str:
        return self._extract_field(soup, ["Article number", "Art. No.", "Article No."])

    def _extract_brand(self, soup) -> str:
        info_rows = soup.find_all('div', class_='info-row')
        for row in info_rows:
            col1 = row.find('div', class_='info-col1')
            if col1 and 'Brand Line' in col1.get_text():
                col2 = row.find('div', class_='info-col2')
                if col2:
                    return col2.get_text(strip=True)
        return self._extract_field(soup, ["Brand", "Manufacturer", "Brand Line"])

    def _extract_description(self, soup) -> str:
        desc = soup.find('div', class_='prod-desc')
        if desc and 'translated-infos' not in desc.get('class', []):
            desc_text = desc.get_text(separator=' ', strip=True)
            desc_text = re.sub(r'\s+', ' ', desc_text)
            return desc_text
        return ""

    def _extract_price(self, soup) -> str:
        price_elem = soup.find('h2', class_='price-per-piece')
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            price_text = price_text.split('/')[0].strip()
            return price_text
        return ""

    def _extract_piece_per_pu(self, soup) -> str:
        return self._extract_field(soup, ["Piece per PU"])

    def _extract_mix_order(self, soup) -> bool:
        mix_elem = soup.find(class_='text-mix-order')
        if mix_elem and 'MixOrder' in mix_elem.get_text():
            return True
        page_text = soup.get_text()
        return "MixOrder" in page_text or "Mix Order" in page_text

    def _extract_min_order_quantity(self, soup) -> str:
        return self._extract_field(soup, ["min order quantity", "Minimum Order", "Min. Order"])

    def _extract_ean(self, soup) -> str:
        return self._extract_field(soup, ["EAN"])

    def _extract_pfi(self, soup) -> str:
        return self._extract_field(soup, ["PFI"])

    def _extract_pu_per_pallet(self, soup) -> str:
        return self._extract_field(soup, ["PU per pallet", "PU/Pallet"])

    def _extract_pu_per_layer(self, soup) -> str:
        return self._extract_field(soup, ["PU per layer", "PU/Layer"])

    def _extract_country_of_origin(self, soup) -> str:
        return self._extract_field(soup, ["Country of origin", "Origin"])

    def _extract_images(self, soup) -> List[str]:
        """
        Extract only product images (with class 'product-image-output')
        Excludes vendor logos, category images, etc.
        """
        images = []
        # First try to find images with the product-image-output class
        product_imgs = soup.find_all('img', class_='product-image-output')
        for img in product_imgs:
            src = img.get('src', '')
            if config.IMAGE_CDN_DOMAIN in src:
                images.append(src)
                if len(images) >= config.MAX_IMAGES:
                    break

        # Fallback: if no product-image-output found, try images in product container
        if not images:
            container = soup.find('div', class_='product-container-img')
            if container:
                for img in container.find_all('img'):
                    src = img.get('src', '')
                    # Skip vendor banner images
                    if config.IMAGE_CDN_DOMAIN in src and 'salesroom.jpg' not in src:
                        images.append(src)
                        if len(images) >= config.MAX_IMAGES:
                            break

        return images

    def close(self):
        """Close connection (don't close user's browser)"""
        pass
