"""
Scraper for PAGE 1 ONLY - Scrapes all products from first page
"""

import time
import json
import re
from datetime import datetime
from typing import Dict, List
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import config


def connect_to_chrome():
    """Connect to existing Chrome"""
    print("🔗 Conectare la Chrome...\n")
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    print("✅ Conectat!\n")
    return driver


def extract_product_name(soup) -> str:
    """Extract product name"""
    title = soup.find('h1', class_='product-title')
    if title:
        return title.get_text(strip=True)
    title = soup.find('h1')
    return title.get_text(strip=True) if title else ""


def extract_field(soup, field_names: List[str]) -> str:
    """Extract a field from product info table"""
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


def extract_article_number(soup) -> str:
    return extract_field(soup, ["Article number", "Art. No.", "Article No."])


def extract_brand(soup) -> str:
    """Extract brand"""
    info_rows = soup.find_all('div', class_='info-row')
    for row in info_rows:
        col1 = row.find('div', class_='info-col1')
        if col1 and 'Brand Line' in col1.get_text():
            col2 = row.find('div', class_='info-col2')
            if col2:
                return col2.get_text(strip=True)
    return extract_field(soup, ["Brand", "Manufacturer", "Brand Line"])


def extract_description(soup) -> str:
    """Extract description"""
    desc = soup.find('div', class_='prod-desc')
    if desc and 'translated-infos' not in desc.get('class', []):
        desc_text = desc.get_text(separator=' ', strip=True)
        desc_text = re.sub(r'\s+', ' ', desc_text)
        return desc_text
    return ""


def extract_price(soup) -> str:
    """Extract price"""
    price_elem = soup.find('h2', class_='price-per-piece')
    if price_elem:
        price_text = price_elem.get_text(strip=True)
        price_text = price_text.split('/')[0].strip()
        return price_text
    return ""


def extract_piece_per_pu(soup) -> str:
    return extract_field(soup, ["Piece per PU"])


def extract_mix_order(soup) -> bool:
    """Check if MixOrder available"""
    mix_elem = soup.find(class_='text-mix-order')
    if mix_elem and 'MixOrder' in mix_elem.get_text():
        return True
    page_text = soup.get_text()
    return "MixOrder" in page_text or "Mix Order" in page_text


def extract_min_order_quantity(soup) -> str:
    return extract_field(soup, ["min order quantity", "Minimum Order", "Min. Order"])


def extract_ean(soup) -> str:
    return extract_field(soup, ["EAN"])


def extract_pfi(soup) -> str:
    return extract_field(soup, ["PFI"])


def extract_pu_per_pallet(soup) -> str:
    return extract_field(soup, ["PU per pallet", "PU/Pallet"])


def extract_pu_per_layer(soup) -> str:
    return extract_field(soup, ["PU per layer", "PU/Layer"])


def extract_country_of_origin(soup) -> str:
    return extract_field(soup, ["Country of origin", "Origin"])


def extract_images(soup) -> List[str]:
    """Extract image URLs"""
    images = []
    for img in soup.find_all('img'):
        src = img.get('src', '')
        if config.IMAGE_CDN_DOMAIN in src:
            images.append(src)
            if len(images) >= config.MAX_IMAGES:
                break
    return images


def scrape_product(driver, product_url: str) -> Dict:
    """Scrape a single product"""
    try:
        # Open product in new tab
        driver.execute_script(f"window.open('{product_url}', '_blank');")
        time.sleep(1)

        # Switch to new tab
        driver.switch_to.window(driver.window_handles[-1])
        time.sleep(3)  # Wait for page load

        # Get HTML
        html = driver.page_source
        soup = BeautifulSoup(html, 'lxml')

        # Extract all data
        product_data = {
            'url': product_url,
            'product_name': extract_product_name(soup),
            'article_number': extract_article_number(soup),
            'brand': extract_brand(soup),
            'description': extract_description(soup),
            'price': extract_price(soup),
            'piece_per_pu': extract_piece_per_pu(soup),
            'mix_order': extract_mix_order(soup),
            'min_order_quantity': extract_min_order_quantity(soup),
            'ean_sku': extract_ean(soup),
            'pfi': extract_pfi(soup),
            'pu_per_pallet': extract_pu_per_pallet(soup),
            'pu_per_layer': extract_pu_per_layer(soup),
            'country_of_origin': extract_country_of_origin(soup),
            'images': extract_images(soup),
            'scraped_at': datetime.utcnow().isoformat() + 'Z'
        }

        # Close tab
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

        # Small delay
        time.sleep(2)

        return product_data

    except Exception as e:
        print(f"      ❌ Eroare: {str(e)}")
        # Try to close tab and return
        try:
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
        except:
            pass
        return None


def main():
    driver = connect_to_chrome()

    # Category URL
    category_url = "https://www.zentrada.com/eu/category/CAE248442A2BBE148BD9F280C58E39F6/Home--Living"

    print(f"📂 Deschid categoria: {category_url}\n")
    driver.get(category_url)

    print("⏳ Aștept 5 secunde ca pagina să se încarce...")
    time.sleep(5)

    print("\n🔍 Caut produse pe pagină...")

    # Find all product cards
    product_cards = driver.find_elements(By.CSS_SELECTOR, "div.custom-card.grid-list-element")

    print(f"✅ Am găsit {len(product_cards)} produse pe PAGINA 1!\n")
    print("=" * 70)

    all_products = []

    for i, product_card in enumerate(product_cards, 1):
        print(f"\n[{i}/{len(product_cards)}] ", end="")

        try:
            # Get product URL
            link = product_card.find_element(By.TAG_NAME, "a")
            product_url = link.get_attribute('href')

            print(f"📦 Scraping...")

            # Scrape the product
            product_data = scrape_product(driver, product_url)

            if product_data:
                all_products.append(product_data)
                print(f"    ✅ {product_data['product_name'][:60]}")
                print(f"    📌 SKU: {product_data['article_number']}")
                print(f"    💰 Preț: {product_data['price']}")
                print(f"    📦 Bucăți/cutie: {product_data['piece_per_pu']}")
            else:
                print(f"    ❌ Eroare la scraping")

        except Exception as e:
            print(f"    ❌ Nu pot extrage URL: {str(e)}")
            continue

    print("\n" + "=" * 70)
    print(f"✅ FINALIZAT! {len(all_products)} produse extrase cu succes!")
    print("=" * 70)

    # Save to JSON
    if all_products:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"page1_products_{timestamp}.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_products, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Produse salvate în: {output_file}")
        print(f"📊 Total produse: {len(all_products)}")

        # Show sample
        if all_products:
            print("\n📋 EXEMPLU PRODUS:")
            print("-" * 70)
            sample = all_products[0]
            print(f"Nume: {sample['product_name']}")
            print(f"SKU: {sample['article_number']}")
            print(f"Brand: {sample['brand']}")
            print(f"Preț: {sample['price']}")
            print(f"Bucăți/cutie: {sample['piece_per_pu']}")
            print(f"MixOrder: {sample['mix_order']}")
            print(f"Imagini: {len(sample['images'])} găsite")
    else:
        print("\n⚠️ Niciun produs nu a fost extras!")

    print("\n" + "=" * 70)
    print("Browser-ul tău rămâne deschis pentru verificare.")
    print("=" * 70)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ EROARE: {str(e)}")
        import traceback
        traceback.print_exc()
