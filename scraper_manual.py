"""
Zentrada Scraper - Manual Mode
Uses YOUR existing Chrome browser session (where you're already logged in)
No automated login needed!
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
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import config


class ZentradaManualScraper:
    """
    Scraper that connects to your existing Chrome browser.

    SETUP (One-time):
    1. Close ALL Chrome windows
    2. Open Chrome with remote debugging:
       Windows: chrome.exe --remote-debugging-port=9222 --user-data-dir="C:/ChromeDebug"
       Mac: /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir="/tmp/ChromeDebug"
    3. Login to Zentrada manually in that Chrome window
    4. Run this script - it will connect to your Chrome session!
    """

    def __init__(self):
        self.driver = None

    def connect_to_existing_chrome(self):
        """Connect to existing Chrome instance"""
        print("🔗 Conectare la Chrome-ul tău deschis...\n")

        options = Options()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            print("✅ Conectat cu succes la Chrome!\n")
            return True
        except Exception as e:
            print(f"❌ Nu pot conecta la Chrome: {str(e)}\n")
            print("INSTRUCȚIUNI SETUP:")
            print("="*70)
            print("1. Închide TOATE ferestrele Chrome")
            print("2. Deschide Command Prompt și rulează:")
            print('   cd "C:\\Program Files\\Google\\Chrome\\Application"')
            print('   chrome.exe --remote-debugging-port=9222 --user-data-dir="C:/ChromeDebug"')
            print("3. În Chrome care s-a deschis, loghează-te pe Zentrada")
            print("4. Rulează din nou acest script")
            print("="*70)
            return False

    def scrape_product(self, url: str) -> Dict:
        """Scrape a single product"""
        if not self.driver:
            print("❌ Browser-ul nu este conectat!")
            return {}

        print(f"📦 Scrap produs: {url}")

        try:
            # Open URL in new tab
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

            print(f"  ✓ {product_data['product_name'][:60]}")

            # Close tab
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])

            # Random delay
            delay = random.uniform(*config.DELAY_BETWEEN_REQUESTS)
            print(f"  ⏱️  Pauză {delay:.1f}s...\n")
            time.sleep(delay)

            return product_data

        except Exception as e:
            print(f"  ❌ Eroare: {str(e)}\n")
            # Try to close tab and return to main window
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
            except:
                pass
            return {'url': url, 'error': str(e)}

    # ========================================
    # EXTRACTION METHODS (same as before)
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
    """Example usage"""
    print("="*70)
    print("  ZENTRADA MANUAL SCRAPER")
    print("  Folosește Chrome-ul tău deschis (unde ești deja logat)")
    print("="*70)
    print()

    scraper = ZentradaManualScraper()

    if not scraper.connect_to_existing_chrome():
        return

    # Example: scrape from a file
    import sys
    if len(sys.argv) < 2:
        print("Usage: python scraper_manual.py <url_file.txt>")
        print("Example: python scraper_manual.py urls.txt")
        return

    url_file = sys.argv[1]

    try:
        with open(url_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"❌ Fișierul {url_file} nu a fost găsit!")
        return

    print(f"📋 Găsite {len(urls)} URL-uri\n")
    print("="*70)

    all_products = []
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] ", end="")
        product = scraper.scrape_product(url)
        if product and 'error' not in product:
            all_products.append(product)

    # Save to JSON
    output_file = f"scraped_products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_products, f, indent=2, ensure_ascii=False)

    print("="*70)
    print(f"✅ Finalizat! {len(all_products)} produse salvate în {output_file}")
    print("="*70)

    scraper.close()


if __name__ == '__main__':
    main()
