"""
TEST SCRAPER - Step by step testing
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def connect_to_chrome():
    """Connect to existing Chrome"""
    print("🔗 Conectare la Chrome...\n")

    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    print("✅ Conectat!\n")
    return driver


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

    print(f"✅ Am găsit {len(product_cards)} produse!\n")

    if len(product_cards) == 0:
        print("❌ Nu am găsit niciun produs!")
        print("\n🔍 Încerc să găsesc orice div cu clasa 'custom-card'...")
        product_cards = driver.find_elements(By.CSS_SELECTOR, "div.custom-card")
        print(f"   Găsite: {len(product_cards)} elemente cu 'custom-card'")

        if len(product_cards) == 0:
            print("\n❌ Tot nu găsesc produse!")
            print("Pagina s-a încărcat corect? Verifică în browser.")
            input("\nApasă ENTER pentru a încheia...")
            return

    # Get first product
    print("=" * 70)
    print("PRIMUL PRODUS:")
    print("=" * 70)

    first_product = product_cards[0]

    # Try to find the link inside
    try:
        link = first_product.find_element(By.TAG_NAME, "a")
        product_url = link.get_attribute('href')
        print(f"\n✅ URL găsit: {product_url}\n")
    except Exception as e:
        print(f"❌ Nu pot găsi link-ul: {str(e)}")
        print("\n🔍 Încerc să găsesc alt element clickabil...")

        # Try to find any clickable element
        try:
            clickable = first_product.find_element(By.CSS_SELECTOR, "[href]")
            product_url = clickable.get_attribute('href')
            print(f"✅ URL găsit (alternativ): {product_url}\n")
        except Exception as e2:
            print(f"❌ Nici alternativa nu funcționează: {str(e2)}")
            input("\nApasă ENTER pentru a încheia...")
            return

    # Open in new tab
    print("🚀 Deschid produsul într-un tab nou...")
    driver.execute_script(f"window.open('{product_url}', '_blank');")
    time.sleep(2)

    # Switch to new tab
    print("🔄 Schimb pe tab-ul nou...")
    driver.switch_to.window(driver.window_handles[-1])
    time.sleep(3)

    print(f"\n✅ SUCCES!")
    print(f"📍 Tab curent: {driver.current_url[:80]}...")
    print(f"📊 Total tab-uri deschise: {len(driver.window_handles)}")

    print("\n" + "=" * 70)
    print("🎉 TOTUL FUNCȚIONEAZĂ!")
    print("=" * 70)
    print("\nVerifică în browser că s-a deschis tab-ul cu produsul.")
    print("Dacă vezi produsul deschis, înseamnă că funcționează perfect!")

    input("\n👉 Apasă ENTER pentru a continua și închide tab-ul...")

    # Close product tab
    print("\n🔒 Închid tab-ul produsului...")
    driver.close()

    # Switch back to category page
    print("🔄 Mă întorc pe pagina categoriei...")
    driver.switch_to.window(driver.window_handles[0])
    time.sleep(1)

    print(f"✅ Înapoi pe categoria: {driver.current_url[:80]}...")

    print("\n" + "=" * 70)
    print("✅ TEST FINALIZAT CU SUCCES!")
    print("=" * 70)
    print("\nAcum putem continua să construim restul scraper-ului!")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ EROARE: {str(e)}")
        import traceback
        traceback.print_exc()
