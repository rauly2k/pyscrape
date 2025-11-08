"""
Full Category Scraper with Pagination Support
Can scrape multiple pages from a category with parallel processing
"""

import time
import json
import re
from datetime import datetime
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
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
    """Scraper for Zentrada categories with pagination and parallel processing"""

    def __init__(self):
        self.driver: Optional[webdriver.Chrome] = None
        self._thread_local = threading.local()  # Thread-local storage for parallel drivers
        self._driver_lock = threading.Lock()  # Lock for driver access

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
                       progress_callback=None, products_per_page: int = 0,
                       parallel_workers: int = 5) -> List[Dict]:
        """
        Scrape products from category with parallel processing

        Args:
            category_url: Category URL
            max_pages: Maximum number of pages to scrape
            progress_callback: Optional callback function(current, total, message)
            products_per_page: Number of products to scrape per page (0 = all)
            parallel_workers: Number of parallel workers for product scraping

        Returns:
            List of product dictionaries
        """
        if not self.driver:
            raise Exception("Browser not connected!")

        if parallel_workers <= 1:
            # Sequential scraping (old method)
            return self._scrape_category_sequential(
                category_url, max_pages, progress_callback, products_per_page
            )

        # Parallel scraping
        all_products = []

        for page_num in range(1, max_pages + 1):
            if progress_callback:
                progress_callback(page_num, max_pages, f"🚀 Scraping page {page_num}/{max_pages} (parallel mode)...")

            # Navigate to page
            page_url = self._get_page_url(category_url, page_num)
            self.driver.get(page_url)
            time.sleep(3)  # Reduced wait time

            # Find products and collect URLs
            product_cards = self.driver.find_elements(By.CSS_SELECTOR, "div.custom-card.grid-list-element")

            if not product_cards:
                if progress_callback:
                    progress_callback(page_num, max_pages, f"No products on page {page_num}")
                break

            # Limit products per page if specified
            if products_per_page > 0:
                product_cards = product_cards[:products_per_page]

            # Extract all product URLs first
            product_urls = []
            for card in product_cards:
                try:
                    link = card.find_element(By.TAG_NAME, "a")
                    product_url = link.get_attribute('href')
                    product_urls.append(product_url)
                except Exception as e:
                    print(f"Error extracting product URL: {str(e)}")
                    continue

            if progress_callback:
                progress_callback(
                    page_num, max_pages,
                    f"Page {page_num}/{max_pages} - Found {len(product_urls)} products, scraping in parallel..."
                )

            # Scrape products in parallel
            page_products = self._scrape_products_parallel(
                product_urls, parallel_workers, page_num, max_pages, progress_callback
            )
            all_products.extend(page_products)

        return all_products

    def _scrape_category_sequential(self, category_url: str, max_pages: int,
                                    progress_callback=None, products_per_page: int = 0) -> List[Dict]:
        """Sequential scraping (fallback for parallel_workers=1)"""
        all_products = []

        for page_num in range(1, max_pages + 1):
            if progress_callback:
                progress_callback(page_num, max_pages, f"Scraping page {page_num}/{max_pages}...")

            page_url = self._get_page_url(category_url, page_num)
            self.driver.get(page_url)
            time.sleep(5)

            product_cards = self.driver.find_elements(By.CSS_SELECTOR, "div.custom-card.grid-list-element")

            if not product_cards:
                if progress_callback:
                    progress_callback(page_num, max_pages, f"No products on page {page_num}")
                break

            if products_per_page > 0:
                product_cards = product_cards[:products_per_page]

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

    def _scrape_products_parallel(self, product_urls: List[str], max_workers: int,
                                  page_num: int, max_pages: int, progress_callback=None) -> List[Dict]:
        """
        Scrape multiple products in parallel by batch-loading tabs
        Opens max_workers tabs at once, lets them load in parallel, then extracts data
        """
        products = []
        total = len(product_urls)

        # Process products in batches
        for batch_start in range(0, len(product_urls), max_workers):
            batch_urls = product_urls[batch_start:batch_start + max_workers]
            batch_num = batch_start // max_workers + 1

            if progress_callback:
                progress_callback(
                    page_num, max_pages,
                    f"Page {page_num}/{max_pages} - Batch {batch_num}: Loading {len(batch_urls)} products in parallel..."
                )

            # Open all tabs for this batch
            for url in batch_urls:
                try:
                    self.driver.execute_script(f"window.open('{url}', '_blank');")
                except Exception as e:
                    print(f"Error opening tab for {url}: {str(e)}")

            # Wait for all tabs to load
            time.sleep(3)  # Let all tabs load simultaneously

            # Now extract data from each tab
            batch_products = []
            for i, url in enumerate(batch_urls, 1):
                try:
                    # Switch to tab (skip first window which is the category page)
                    tab_index = i
                    if tab_index < len(self.driver.window_handles):
                        self.driver.switch_to.window(self.driver.window_handles[tab_index])

                        # Parse HTML
                        soup = BeautifulSoup(self.driver.page_source, 'lxml')

                        # Extract article number FIRST
                        article_number = self._extract_article_number(soup)

                        # Extract data
                        product = {
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
                            'images': self._extract_images(soup, article_number),
                            'scraped_at': datetime.utcnow().isoformat() + 'Z'
                        }

                        batch_products.append(product)
                except Exception as e:
                    print(f"Error extracting product data: {str(e)}")

            # Close all tabs except the first (category page)
            while len(self.driver.window_handles) > 1:
                self.driver.switch_to.window(self.driver.window_handles[-1])
                self.driver.close()

            # Switch back to category page
            self.driver.switch_to.window(self.driver.window_handles[0])

            products.extend(batch_products)

            if progress_callback:
                progress_callback(
                    page_num, max_pages,
                    f"Page {page_num}/{max_pages} - ✅ Batch {batch_num}: Scraped {len(batch_products)}/{len(batch_urls)} products (Total: {len(products)}/{total})"
                )

        return products

    def _get_page_url(self, base_url: str, page_num: int) -> str:
        """Generate URL for specific page number"""
        if page_num == 1:
            return base_url
        # Zentrada uses ?page=2 format
        separator = '&' if '?' in base_url else '?'
        return f"{base_url}{separator}page={page_num}"

    def _scrape_product(self, product_url: str) -> Optional[Dict]:
        """Scrape single product (thread-safe)"""
        # Use lock to ensure thread-safe access to shared driver
        with self._driver_lock:
            try:
                # Open in new tab
                self.driver.execute_script(f"window.open('{product_url}', '_blank');")
                time.sleep(0.5)  # Reduced wait time

                # Switch to new tab
                self.driver.switch_to.window(self.driver.window_handles[-1])
                time.sleep(2)  # Reduced wait time

                # Parse HTML
                soup = BeautifulSoup(self.driver.page_source, 'lxml')

                # Extract article number FIRST (needed for image filtering)
                article_number = self._extract_article_number(soup)

                # Extract data
                product = {
                    'url': product_url,
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
                    'scraped_at': datetime.utcnow().isoformat() + 'Z'
                }

                # Close tab
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])

                time.sleep(0.5)  # Reduced wait time
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

    def _extract_images(self, soup, article_number: str) -> List[str]:
        """
        Extract ALL product images, filtered by article number to avoid related products
        - Main product-image-output
        - Carousel/gallery images
        - Fallback: get images from product container if article filtering fails
        """
        images = []
        seen_urls = set()  # Avoid duplicates

        # Normalize article number for matching
        article_num_clean = str(article_number).strip()

        # Find product container to limit scope
        product_container = soup.find('div', class_='product-container-img')
        if not product_container:
            product_container = soup  # Fallback to whole page

        # 1. Main product image (product-image-output)
        main_imgs = product_container.find_all('img', class_='product-image-output')
        for img in main_imgs:
            src = img.get('src', '')
            if self._is_valid_product_image(src, article_num_clean):
                # Convert to 600x600
                src_high_res = src.replace('w=210&h=210', 'w=600&h=600')
                src_high_res = src_high_res.replace('w=600&h=600', 'w=600&h=600')  # Already converted
                if src_high_res not in seen_urls:
                    images.append(src_high_res)
                    seen_urls.add(src_high_res)

        # 2. Carousel images (owl-carousel contains additional product images)
        carousel = product_container.find('owl-carousel-o')
        if carousel:
            for img in carousel.find_all('img'):
                src = img.get('src', '')
                if self._is_valid_product_image(src, article_num_clean):
                    # Convert to 600x600
                    src_high_res = src.replace('w=210&h=210', 'w=600&h=600')
                    src_high_res = src_high_res.replace('w=600&h=600', 'w=600&h=600')
                    if src_high_res not in seen_urls:
                        images.append(src_high_res)
                        seen_urls.add(src_high_res)

        # 3. Look in small-img-holder (another common location for gallery)
        small_img_holder = product_container.find('div', class_='small-img-holder')
        if small_img_holder:
            for img in small_img_holder.find_all('img'):
                src = img.get('src', '')
                if self._is_valid_product_image(src, article_num_clean):
                    # Convert to 600x600
                    src_high_res = src.replace('w=210&h=210', 'w=600&h=600')
                    src_high_res = src_high_res.replace('w=600&h=600', 'w=600&h=600')
                    if src_high_res not in seen_urls:
                        images.append(src_high_res)
                        seen_urls.add(src_high_res)

        # FALLBACK: If no images found with article number filtering,
        # try to get images without article number check (but still exclude logos)
        if not images:
            print(f"  ⚠️ No images found with article filter '{article_num_clean}', trying fallback...")

            # Try all sources again without article number filter
            all_sources = []
            all_sources.extend(main_imgs)
            if carousel:
                all_sources.extend(carousel.find_all('img'))
            if small_img_holder:
                all_sources.extend(small_img_holder.find_all('img'))

            for img in all_sources:
                src = img.get('src', '')
                # Only check for CDN domain and exclude logos (no article number check)
                if src and config.IMAGE_CDN_DOMAIN in src:
                    if 'salesroom.jpg' not in src and 'brands/' not in src and '/Logo' not in src:
                        src_high_res = src.replace('w=210&h=210', 'w=600&h=600')
                        src_high_res = src_high_res.replace('w=600&h=600', 'w=600&h=600')
                        if src_high_res not in seen_urls:
                            images.append(src_high_res)
                            seen_urls.add(src_high_res)
                            # Limit fallback to first 5 images to avoid getting too many
                            if len(images) >= 5:
                                break

        # Limit to MAX_IMAGES
        return images[:config.MAX_IMAGES]

    def _is_valid_product_image(self, src: str, article_number: str) -> bool:
        """
        Check if image URL is a valid product image
        - Must contain CDN domain
        - Must contain article number in filename OR path
        - Must not be a vendor logo or brand image
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

    def close(self):
        """Close connection (don't close user's browser)"""
        pass
