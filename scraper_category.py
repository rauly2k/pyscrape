"""
Zentrada Category Scraper - Scrapes all products from a category page
Uses your existing Chrome session (where you're already logged in)
"""

import time
import random
import re
import json
from datetime import datetime
from typing import Dict, List
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import config


class ZentradaCategoryScraper:
    """Scraper for Zentrada category pages"""

    def __init__(self):
        self.driver = None
        self.main_window = None

    def connect_to_existing_chrome(self):
        """Connect to existing Chrome instance with debugging enabled"""
        print("🔗 Conectare la Chrome-ul tău deschis...\n")

        options = Options()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.main_window = self.driver.current_window_handle
            print("✅ Conectat cu succes la Chrome!\n")
            return True
        except Exception as e:
            print(f"❌ Nu pot conecta la Chrome: {str(e)}\n")
            print("VERIFICĂ:")
            print("1. Ai deschis Chrome cu: chrome.exe --remote-debugging-port=9222")
            print("2. Ești logat pe Zentrada în acel Chrome")
            return False

    def scrape_category_page(self, category_url: str) -> List[Dict]:
        """
        Scrape all products from a category page (first page only for now)

        Args:
            category_url: URL to category page

        Returns:
            List of product data dictionaries
        """
        if not self.driver:
            print("❌ Browser-ul nu este conectat!")
            return []

        print(f"📂 Deschid categoria: {category_url}")

        # Navigate to category page
        self.driver.get(category_url)
        time.sleep(5)  # Wait for page to load completely

        # Find all product cards
        print("🔍 Caut produse pe pagină...\n")

        try:
            # Wait for products to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "custom-card"))
            )

            # Find all product elements
            product_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.custom-card.grid-list-element.can-hover.ng-star-inserted")

            print(f"✅ Găsite {len(product_elements)} produse pe pagină!\n")
            print("="*70)

            all_products = []

            for i, product_elem in enumerate(product_elements, 1):
                print(f"\n[{i}/{len(product_elements)}] ", end="")

                try:
                    # Get product URL from the element
                    # The link is usually in an <a> tag inside the card
                    link_elem = product_elem.find_element(By.CSS_SELECTOR, "a")
                    product_url = link_elem.get_attribute('href')

                    print(f"📦 {product_url}")

                    # Scrape the product
                    product_data = self.scrape_product(product_url)

                    if product_data and 'error' not in product_data:
                        all_products.append(product_data)
                        print(f"    ✅ {product_data.get('product_name', 'N/A')[:60]}")
                    else:
                        print(f"    ❌ Eroare la scraping")

                except Exception as e:
                    print(f"    ❌ Eroare la extragerea URL-ului: {str(e)}")
                    continue

            print("\n" + "="*70)
            print(f"✅ Finalizat! {len(all_products)} produse extrase cu succes")

            return all_products

        except Exception as e:
            print(f"❌ Eroare la găsirea produselor: {str(e)}")
            return []

    def scrape_product(self, url: str) -> Dict:
        """
        Scrape a single product by opening it in a new tab

        Args:
            url: Product URL

        Returns:
            Product data dictionary
        """
        try:
            # Open product in new tab
            self.driver.execute_script(f"window.open('{url}', '_blank');")
            time.sleep(1)

            # Switch to new tab
            self.driver.switch_to.window(self.driver.window_handles[-1])
            time.sleep(3)  # Wait for page load

            # Get HTML
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'lxml')

            # Extract data
            product_data = {
                'url': url,
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

            # Close tab and return to main window
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])

            # Random delay
            delay = random.uniform(*config.DELAY_BETWEEN_REQUESTS)
            time.sleep(delay)

            return product_data

        except Exception as e:
            print(f"      Eroare scraping: {str(e)}")
            # Try to close tab and return to main window
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
            except:
                pass
            return {'url': url, 'error': str(e)}

    # ========================================
    # EXTRACTION METHODS
    # ========================================

    def _extract_product_name(self, soup: BeautifulSoup) -> str:
        title = soup.find('h1', class_='product-title')
        if title:
            return title.get_text(strip=True)
        title = soup.find('h1')
        return title.get_text(strip=True) if title else ""

    def _extract_article_number(self, soup: BeautifulSoup) -> str:
        return self._extract_field(soup, ["Article number", "Art. No.", "Article No."])

    def _extract_brand(self, soup: BeautifulSoup) -> str:
        info_rows = soup.find_all('div', class_='info-row')
        for row in info_rows:
            col1 = row.find('div', class_='info-col1')
            if col1 and 'Brand Line' in col1.get_text():
                col2 = row.find('div', class_='info-col2')
                if col2:
                    return col2.get_text(strip=True)
        return self._extract_field(soup, ["Brand", "Manufacturer", "Brand Line"])

    def _extract_description(self, soup: BeautifulSoup) -> str:
        desc = soup.find('div', class_='prod-desc')
        if desc and 'translated-infos' not in desc.get('class', []):
            desc_text = desc.get_text(separator=' ', strip=True)
            desc_text = re.sub(r'\s+', ' ', desc_text)
            return desc_text
        return ""

    def _extract_price(self, soup: BeautifulSoup) -> str:
        price_elem = soup.find('h2', class_='price-per-piece')
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            price_text = price_text.split('/')[0].strip()
            return price_text
        return ""

    def _extract_piece_per_pu(self, soup: BeautifulSoup) -> str:
        return self._extract_field(soup, ["Piece per PU"])

    def _extract_mix_order(self, soup: BeautifulSoup) -> bool:
        mix_elem = soup.find(class_='text-mix-order')
        if mix_elem and 'MixOrder' in mix_elem.get_text():
            return True
        page_text = soup.get_text()
        return "MixOrder" in page_text or "Mix Order" in page_text

    def _extract_min_order_quantity(self, soup: BeautifulSoup) -> str:
        return self._extract_field(soup, ["min order quantity", "Minimum Order", "Min. Order"])

    def _extract_ean(self, soup: BeautifulSoup) -> str:
        return self._extract_field(soup, ["EAN"])

    def _extract_pfi(self, soup: BeautifulSoup) -> str:
        return self._extract_field(soup, ["PFI"])

    def _extract_pu_per_pallet(self, soup: BeautifulSoup) -> str:
        return self._extract_field(soup, ["PU per pallet", "PU/Pallet"])

    def _extract_pu_per_layer(self, soup: BeautifulSoup) -> str:
        return self._extract_field(soup, ["PU per layer", "PU/Layer"])

    def _extract_country_of_origin(self, soup: BeautifulSoup) -> str:
        return self._extract_field(soup, ["Country of origin", "Origin"])

    def _extract_images(self, soup: BeautifulSoup) -> List[str]:
        images = []
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if config.IMAGE_CDN_DOMAIN in src:
                images.append(src)
                if len(images) >= config.MAX_IMAGES:
                    break
        return images

    def _extract_field(self, soup: BeautifulSoup, field_names: List[str]) -> str:
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
        """Don't close the browser - user is using it!"""
        print("\n✅ Scraping finalizat! (Browser-ul tău rămâne deschis)")


def main():
    """Main function"""
    print("="*70)
    print("  ZENTRADA CATEGORY SCRAPER")
    print("  Extrage toate produsele dintr-o categorie")
    print("="*70)
    print()

    scraper = ZentradaCategoryScraper()

    if not scraper.connect_to_existing_chrome():
        return

    # Get category URL from user or command line
    import sys
    if len(sys.argv) > 1:
        category_url = sys.argv[1]
    else:
        category_url = input("Introdu URL-ul categoriei: ").strip()

    if not category_url:
        print("❌ Niciun URL introdus!")
        return

    print()
    print("="*70)

    # Scrape category
    products = scraper.scrape_category_page(category_url)

    if products:
        # Save to JSON
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"category_products_{timestamp}.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(products, f, indent=2, ensure_ascii=False)

        print(f"\n💾 {len(products)} produse salvate în: {output_file}")
    else:
        print("\n⚠️ Niciun produs nu a fost extras!")

    print("="*70)
    scraper.close()


if __name__ == '__main__':
    main()
