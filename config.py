# config.py - Configurări Aplicație Zentrada Processor

# Cursul EUR/RON (editabil din interfață)
DEFAULT_EUR_RON_RATE = 5.02

# ============================================
# CATEGORII PRODUSE (9 categorii principale)
# ============================================
PRODUCT_CATEGORIES = [
    "Casă & Grădină",
    "Jucării & Copii",
    "Fashion & Accesorii",
    "Beauty & Îngrijire",
    "Electronice & Birou",
    "Cadouri & Petreceri",
    "Sport & Timp Liber",
    "Alimente & Băuturi",
    "Branduri Licențiate"
]

# ============================================
# MARJE DE PROFIT PE CATEGORII (%)
# ============================================
CATEGORY_MARGINS = {
    "Casă & Grădină": 30,
    "Jucării & Copii": 35,
    "Fashion & Accesorii": 40,
    "Beauty & Îngrijire": 35,
    "Electronice & Birou": 20,
    "Cadouri & Petreceri": 40,
    "Sport & Timp Liber": 30,
    "Alimente & Băuturi": 25,
    "Branduri Licențiate": 45
}

# ============================================
# COTE TVA ROMÂNIA (%)
# ============================================
VAT_RATES = {
    "Standard": 19,
    "Redusă 9%": 9,
    "Redusă 5%": 5,
    "Scutită": 0
}

# Mapping categorie produs → cotă TVA
CATEGORY_VAT_MAPPING = {
    "Casă & Grădină": 19,
    "Jucării & Copii": 19,
    "Fashion & Accesorii": 19,
    "Beauty & Îngrijire": 19,
    "Electronice & Birou": 19,
    "Cadouri & Petreceri": 19,
    "Sport & Timp Liber": 19,
    "Alimente & Băuturi": 9,  # Majoritatea alimentelor procesate
    "Branduri Licențiate": 19
}

# ============================================
# MAPPING ZENTRADA CATEGORIES → CATEGORIILE NOASTRE
# ============================================
ZENTRADA_CATEGORY_MAPPING = {
    "Home & Living": "Casă & Grădină",
    "Household & Kitchen": "Casă & Grădină",
    "Garden & DIY store": "Casă & Grădină",
    
    "Toys": "Jucării & Copii",
    "Licensed Products": "Branduri Licențiate",  # Poate fi și Jucării dacă nu e brand major
    
    "Fashion & Apparel": "Fashion & Accesorii",
    "Jewelry & Watches": "Fashion & Accesorii",
    "Bags & Travel accessories": "Fashion & Accesorii",
    
    "Drugstore & Beauty": "Beauty & Îngrijire",
    
    "Consumer Electronics": "Electronice & Birou",
    "Office and business supplies": "Electronice & Birou",
    
    "Gifts & Stationery": "Cadouri & Petreceri",
    "Party & Costumes": "Cadouri & Petreceri",
    
    "Sports & Leisure": "Sport & Timp Liber",
    "Pet supplies": "Casă & Grădină",
    
    "Food & Beverage": "Alimente & Băuturi",
    
    "Other": "Casă & Grădină"  # Default pentru necunoscute
}

# ============================================
# BRANDURI LICENȚIATE MAJORE
# ============================================
# Acestea vor fi categorizate automat ca "Branduri Licențiate"
LICENSED_BRANDS = [
    "Marvel", "Disney", "Star Wars", "Pixar", "Mickey Mouse", "Minnie Mouse",
    "Frozen", "Princess", "Cars", "Toy Story", "Spider-Man", "Avengers",
    "Batman", "Superman", "DC Comics", "Harry Potter", "Pokemon", "Pokémon",
    "Nintendo", "Super Mario", "Sonic", "Minecraft", "Fortnite",
    "Barbie", "Hot Wheels", "LEGO", "Paw Patrol", "Peppa Pig",
    "Hello Kitty", "Snoopy", "Looney Tunes", "Tom and Jerry",
    "Teenage Mutant Ninja Turtles", "TMNT", "Transformers",
    "My Little Pony", "Care Bears", "Winnie the Pooh"
]

# ============================================
# BATCH PROCESSING SETTINGS
# ============================================
BATCH_SIZE = 7  # Procesează câte 7 produse odată (limitat de max 8192 tokens output Gemini 2.5 Flash)
MAX_RETRIES = 3  # Retry-uri pentru API Gemini

# ============================================
# WOOCOMMERCE EXPORT COLUMNS
# ============================================
WOOCOMMERCE_COLUMNS = [
    "ID",
    "Type",  # simple, variable, etc.
    "SKU",
    "Name",
    "Published",
    "Is featured?",
    "Visibility in catalog",
    "Short description",
    "Description",
    "Date sale price starts",
    "Date sale price ends",
    "Tax status",
    "Tax class",
    "In stock?",
    "Stock",
    "Low stock amount",
    "Backorders allowed?",
    "Sold individually?",
    "Weight (kg)",
    "Length (cm)",
    "Width (cm)",
    "Height (cm)",
    "Allow customer reviews?",
    "Purchase note",
    "Sale price",
    "Regular price",
    "Categories",
    "Tags",
    "Shipping class",
    "Images",
    "Download limit",
    "Download expiry days",
    "Parent",
    "Grouped products",
    "Upsells",
    "Cross-sells",
    "External URL",
    "Button text",
    "Position",
    "Attribute 1 name",
    "Attribute 1 value(s)",
    "Attribute 1 visible",
    "Attribute 1 global",
    "Meta: _brand",  # Custom field pentru brand
    "Meta: _eur_price_piece",  # Preț EUR bucată
    "Meta: _eur_price_box",  # Preț EUR cutie
    "Meta: _lei_price_piece",  # Preț LEI bucată
    "Meta: _lei_price_box",  # Preț LEI cutie
    "Meta: _pieces_per_box",  # Bucăți per cutie
    "Meta: _vat_rate",  # Cotă TVA
    "Meta: _margin_percent",  # Marjă %
    "Meta: _mix_order",  # Mix order true/false
    "Meta: _min_order_qty",  # Cantitate minimă comandă
    "Meta: _zentrada_url",  # Link produs Zentrada
    "Meta: _country_of_origin",  # Țara de origine
    "Meta: _ean"  # Cod EAN
]

# ============================================
# GEMINI AI SETTINGS
# ============================================
GEMINI_MODEL = "gemini-2.5-flash"  # Gemini 2.5 Flash: 8192 output tokens max
GEMINI_TEMPERATURE = 0.6
GEMINI_MAX_OUTPUT_TOKENS = 8192  # For individual products (not used for batch - batch calculates dynamically)

# ============================================
# AI PROMPT TEMPLATE
# ============================================
AI_PROMPT_TEMPLATE = """
Ești un expert în descrieri de produse B2B pentru e-commerce în România.

PRODUSUL:
Brand: {brand}
Nume produs (EN): {product_name}
Descriere (EN): {description}
Țara de origine: {country_of_origin}

SARCINI:
1. `title_ro`: Traduce numele produsului în română. Fii concis și direct. NU adăuga informații de marketing sau SEO precum "B2B", "engros", "ideal pentru cadouri". Păstrează doar numele esențial al produsului.

2. `description_ro`: Creează o descriere PROFESIONALĂ B2B (40-60 cuvinte) într-un singur paragraf simplu, fără subtitluri bold.
   - TON PROFESIONAL: Scrie pentru profesioniști B2B, nu pentru consumatori finali
   - NU folosi limbaj consumer-focused: evită "dumneavoastră", "când aveți nevoie", "vă oferă", etc.
   - Fii DIRECT și FACTUAL: descrie ce este produsul și pentru ce este util
   - Format: "Nume produs - scurtă descriere tehnică. Utilizări/aplicații practice. Caracteristici cheie."
   - EXEMPLU BUN: "Set de 4 baterii Varta Super Heavy Duty Micro AAA - conceput pentru a oferi energie constantă și de lungă durată. Ideale pentru utilizare zilnică în telecomenzi, ceasuri, jucării și alte aparate electronice de mici dimensiuni, aceste baterii asigură funcționarea optimă."
   - EXEMPLU GREȘIT: "**Performanță Fiabilă**\\nAcest set vă oferă energie când aveți cea mai mare nevoie..."

3. `short_description_ro`: Creează 3-5 bullet points concise (5-15 cuvinte fiecare), separate prin `\n`. Acestea trebuie să descrie strict caracteristici tehnice, avantaje sau conținutul produsului. TON PROFESIONAL B2B.

4. Determină categoria cea mai potrivită din lista de mai jos
5. Verifică dacă brandul este licențiat (Disney, Marvel, etc.)

CATEGORII DISPONIBILE:
- Casă & Grădină
- Jucării & Copii
- Fashion & Accesorii
- Beauty & Îngrijire
- Electronice & Birou
- Cadouri & Petreceri
- Sport & Timp Liber
- Alimente & Băuturi
- Branduri Licențiate (doar pentru branduri majore: Disney, Marvel, Pokemon, etc.)

RĂSPUNDE STRICT ÎN FORMAT JSON:
{
  "title_ro": "Baterii Varta Super Heavy Duty Micro AAA",
  "description_ro": "Set de 4 baterii Varta Super Heavy Duty Micro AAA - conceput pentru a oferi energie constantă și de lungă durată. Ideale pentru utilizare zilnică în telecomenzi, ceasuri, jucării și alte aparate electronice de mici dimensiuni, aceste baterii asigură funcționarea optimă.",
  "short_description_ro": "Set de 4 baterii Micro AAA\\nEnergie constantă și de lungă durată\\nIdeale pentru telecomenzi, ceasuri și jucării\\nCompoziție chimică cu descărcare lentă",
  "category": "Electronice & Birou",
  "is_licensed_brand": false,
  "tags_ro": "baterii, aaa, varta, telecomenzi, jucarii, energie"
}

IMPORTANT:
- NU folosi subtitluri bold (ex: **Subtitlu**)
- NU folosi limbaj consumer (dumneavoastră, vă oferă, când aveți nevoie)
- Scrie SIMPLU, DIRECT, PROFESIONAL pentru B2B
- Folosește DOAR `\\n` pentru a separa bullet points
- Asigură-te că JSON-ul este VALID: escape toate ghilimelele (") din text cu backslash (\")
- NU folosi newline real în JSON, doar \\n ca string escape
- NU adăuga text înaintea sau după JSON. Doar JSON pur valid.
"""

# ============================================
# AI PROMPT BATCH TEMPLATE
# ============================================
AI_PROMPT_BATCH_TEMPLATE = """
Ești un expert în descrieri de produse B2B pentru e-commerce în România. Sarcina ta este să preiei o LISTĂ de produse în format JSON și să returnezi un DICȚIONAR JSON cu datele procesate pentru FIECARE produs.
Fiecare produs din input are un câmp "id". Trebuie să returnezi un DICȚIONAR JSON unde cheile sunt "id"-urile produselor din input.

LISTA DE PRODUSE (INPUT):
{product_list_json}

SARCINI PENTRU FIECARE PRODUS DIN LISTĂ:
1. `title_ro`: Traduce numele produsului în română. Fii concis și direct. NU adăuga informații de marketing sau SEO.

2. `description_ro`: Creează o descriere PROFESIONALĂ B2B (40-60 cuvinte) într-un singur paragraf simplu, fără subtitluri bold.
   - TON PROFESIONAL: Scrie pentru profesioniști B2B, nu pentru consumatori finali
   - NU folosi limbaj consumer-focused: evită "dumneavoastră", "când aveți nevoie", "vă oferă", etc.
   - Fii DIRECT și FACTUAL: descrie ce este produsul și pentru ce este util
   - Format simplu: "Nume produs - scurtă descriere tehnică. Utilizări practice. Caracteristici cheie."

3. `short_description_ro`: Creează 3-5 bullet points concise (5-15 cuvinte fiecare), separate prin `\\n`, care descriu caracteristici tehnice sau avantaje. TON PROFESIONAL B2B.

4. `category`: Alege categoria cea mai potrivită din lista de mai jos.
5. `is_licensed_brand`: Determină dacă brandul este unul licențiat major.
6. `tags_ro`: Generează 5-7 tag-uri SEO relevante, separate prin virgulă.

CATEGORII DISPONIBILE:
- Casă & Grădină
- Jucării & Copii
- Fashion & Accesorii
- Beauty & Îngrijire
- Electronice & Birou
- Cadouri & Petreceri
- Sport & Timp Liber
- Alimente & Băuturi
- Branduri Licențiate

RĂSPUNDE STRICT CU UN DICȚIONAR JSON VALID, FĂRĂ TEXT SUPLIMENTAR. Fiecare element din dicționar trebuie să aibă ca cheie "id"-ul produsului corespunzător din input.

EXEMPLU FORMAT:
{{
  "id_produs_1": {{
    "title_ro": "Baterii Varta Super Heavy Duty Micro AAA",
    "description_ro": "Set de 4 baterii Varta Super Heavy Duty Micro AAA - conceput pentru a oferi energie constantă și de lungă durată. Ideale pentru utilizare zilnică în telecomenzi, ceasuri, jucării și alte aparate electronice de mici dimensiuni, aceste baterii asigură funcționarea optimă.",
    "short_description_ro": "Set de 4 baterii Micro AAA\\nEnergie constantă și de lungă durată\\nIdeale pentru telecomenzi și jucării\\nCompoziție cu descărcare lentă",
    "category": "Electronice & Birou",
    "is_licensed_brand": false,
    "tags_ro": "baterii, aaa, varta, telecomenzi, jucarii"
  }}
}}

IMPORTANT:
- NU folosi subtitluri bold (ex: **Subtitlu**)
- NU folosi limbaj consumer (dumneavoastră, vă oferă, când aveți nevoie)
- Scrie SIMPLU, DIRECT, PROFESIONAL pentru B2B
- Descrieri scurte (40-60 cuvinte), într-un singur paragraf
- Folosește DOAR `\\n` pentru a separa bullet points
- JSON VALID: escape toate ghilimelele (") din text cu backslash (\")
"""

# ============================================
# UI SETTINGS
# ============================================
WINDOW_TITLE = "Zentrada Processor - Importator Produse B2B"
WINDOW_MIN_WIDTH = 1400
WINDOW_MIN_HEIGHT = 900

# ============================================
# FILE PATHS
# ============================================
DEFAULT_OUTPUT_FOLDER = "exports"
LOG_FILE = "processor.log"

# ============================================
# SETĂRI SCRAPER (Folosite de scraper.py)
# ============================================

# Date de autentificare Zentrada
ZENTRADA_EMAIL = "raulpavel95@gmail.com"
ZENTRADA_PASSWORD = "C48*FKk4zM2s4.F"

# Întârziere aleatorie între request-uri (min, max secunde)
DELAY_BETWEEN_REQUESTS = (2, 6)

# Numărul maxim de imagini de extras per produs
MAX_IMAGES = 5

# Domeniul CDN de unde se iau imaginile
IMAGE_CDN_DOMAIN = "evdo8pe.cloudimg.io"

# Timeout pentru request-uri (în milisecunde)
REQUEST_TIMEOUT = 30000