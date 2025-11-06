# Zentrada Processor - Importator Produse B2B

## 📋 Descriere

Aplicație desktop pentru procesarea automată a produselor Zentrada și importul lor în WooCommerce.

### Funcționalități Principale:

✅ Import produse din JSON (scrapat de pe Zentrada)
✅ Traducere automată în română cu Gemini AI
✅ Optimizare SEO pentru titluri și descrieri
✅ Categorizare automată inteligentă
✅ Calcul automat prețuri (EUR → LEI, TVA, Marje)
✅ Export format WooCommerce CSV
✅ Export Excel pentru verificare internă
✅ Procesare în batch-uri (50-100 produse)
✅ Interfață grafică user-friendly

---

## 🚀 Instalare

### Cerințe de Sistem:
- Windows 10/11
- Python 3.11 sau mai nou
- 4GB RAM minim
- Conexiune la internet (pentru API Gemini)

### Pași de Instalare:

#### 1. Instalează Python
Descarcă Python de la: https://www.python.org/downloads/

**IMPORTANT:** La instalare, bifează "Add Python to PATH"!

#### 2. Descarcă aplicația
Descarcă folderul `zentrada_processor` complet.

#### 3. Instalează dependențele
Deschide Command Prompt (cmd) în folderul aplicației și rulează:

```bash
pip install -r requirements.txt
```

#### 4. Obține un API Key Gemini
- Intră pe: https://aistudio.google.com/app/apikey
- Creează un API Key gratuit
- Copiază-l și păstrează-l pentru mai târziu

---

## 🎯 Utilizare

### 1. Pornește Aplicația

```bash
python main_app.py
```

### 2. Configurează Aplicația

**Tab "Configurări":**

1. **Introdu API Key-ul Gemini** (obligatoriu)
2. **Setează Cursul EUR/RON** (implicit 5.02, modifică dacă e necesar)
3. **Ajustează Marjele** pe categorii (opțional)
4. **Setează Batch Size** (câte produse să proceseze deodată)
5. Apasă **"Salvează Configurările"**

### 3. Import JSON

**Tab "Import & Procesare":**

1. Apasă **"Încarcă Fișier JSON"**
2. Selectează fișierul JSON cu produsele tale (de la scraper)
3. Vezi preview-ul produselor încărcate

### 4. Procesare Produse

**Opțiuni:**
- ☑️ **Folosește AI** - recomandat pentru rezultate optime
- ☐ **Limitează la primele X produse** - util pentru testare

Apasă **"PROCESEAZĂ PRODUSE"** și așteaptă!

**Timpul de procesare:**
- Cu AI: ~2-5 secunde/produs
- Fără AI: ~0.1 secunde/produs

### 5. Export Rezultate

**Tab "Rezultate":**

Ai 3 opțiuni de export:

1. **Export WooCommerce CSV** - pentru import direct în WooCommerce
2. **Export Excel Verificare** - pentru verificare manuală a datelor
3. **Export Ambele** - recomandabil!

Fișierele se salvează în folderul `exports/`.

---

## 📊 Categorii Produse

Aplicația folosește 9 categorii principale:

1. **Casă & Grădină** - articole casnice, decorațiuni, grădinărit
2. **Jucării & Copii** - jucării, jocuri educative
3. **Fashion & Accesorii** - îmbrăcăminte, bijuterii, genți
4. **Beauty & Îngrijire** - cosmetice, produse îngrijire personală
5. **Electronice & Birou** - gadgeturi, papetărie, birou
6. **Cadouri & Petreceri** - cadouri, decorațiuni petreceri
7. **Sport & Timp Liber** - articole sportive, hobby
8. **Alimente & Băuturi** - alimente, băuturi
9. **Branduri Licențiate** - Disney, Marvel, Pokemon, etc.

---

## 💰 Calcul Prețuri

### Formula Automată:

```
1. Preț Achizitie EUR/Buc (extrage din JSON)
2. Preț Achizitie EUR/Cutie = Preț/Buc × Bucăți/Cutie
3. Preț Achizitie LEI = Preț EUR × Curs (5.02)
4. Preț + TVA = Preț LEI × (1 + TVA%)
5. Preț Final = Preț + TVA × (1 + Marjă%)
```

### TVA pe Categorii:

- **Standard (19%)**: Majoritatea produselor
- **Redusă (9%)**: Alimente & Băuturi
- **Alte cote**: Se pot configura manual în `config.py`

### Marje Recomandate:

| Categorie | Marjă Implicită |
|-----------|-----------------|
| Jucării & Copii | 35% |
| Fashion & Accesorii | 40% |
| Branduri Licențiate | 45% |
| Electronice | 20% |
| Beauty & Îngrijire | 35% |
| Cadouri & Petreceri | 40% |
| Casă & Grădină | 30% |
| Sport & Timp Liber | 30% |
| Alimente & Băuturi | 25% |

*Poți ajusta marjele din tab-ul "Configurări"*

---

## 📁 Structura Fișierelor

```
zentrada_processor/
│
├── main_app.py              # Aplicația principală (GUI)
├── product_processor.py     # Logica de procesare produse
├── excel_exporter.py        # Export Excel/CSV
├── config.py                # Configurări (categorii, marje, TVA)
├── requirements.txt         # Dependențe Python
├── README.md               # Acest fișier
│
├── exports/                # Aici se salvează exporturile
│   ├── woocommerce_import_20241029_153045.csv
│   └── verificare_produse_20241029_153045.xlsx
│
└── processor.log           # Log-uri (dacă există erori)
```

---

## 🔧 Troubleshooting

### Problema: "API Key invalid"
**Soluție:** Verifică că ai introdus corect API Key-ul în tab "Configurări"

### Problema: "Module not found"
**Soluție:** Rulează din nou `pip install -r requirements.txt`

### Problema: Procesarea e foarte lentă
**Soluție:** 
- Dezactivează AI pentru teste rapide
- Folosește "Limitează la primele X produse" pentru batch-uri mici

### Problema: Prețurile nu sunt corecte
**Soluție:**
- Verifică cursul EUR/RON în Configurări
- Verifică marjele pe categorii
- Uită-te în Excel-ul de verificare pentru detalii

### Problema: Categoriile nu sunt corecte
**Soluție:**
- AI-ul poate greși uneori
- Poți edita manual produsele în WooCommerce după import
- SAU modifică mapping-ul în `config.py` → `ZENTRADA_CATEGORY_MAPPING`

---

## 📝 Format JSON Așteptat

Aplicația așteaptă un JSON cu produse în următorul format:

```json
[
  {
    "article_number": "3388780",
    "brand": "Minecraft",
    "country_of_origin": "CHINA",
    "description": ".",
    "ean_sku": "8721246991908",
    "images": ["url1", "url2", "url3"],
    "min_order_quantity": "1",
    "mix_order": true,
    "piece_per_pu": "24",
    "price": "1,84 EUR - 2,15 EUR",
    "product_name": "Minecraft 3D toppeez in Blindbox 6x6x6cm",
    "url": "https://www.zentrada.com/..."
  }
]
```

---

## 🎨 Personalizări

### Modifică Categoriile

Editează `config.py` → `PRODUCT_CATEGORIES`

### Modifică Marjele

Editează `config.py` → `CATEGORY_MARGINS` sau din interfață

### Modifică TVA-ul

Editează `config.py` → `CATEGORY_VAT_MAPPING`

### Adaugă Branduri Licențiate Noi

Editează `config.py` → `LICENSED_BRANDS`

---

## 📞 Suport

Pentru probleme tehnice:
1. Verifică log-urile în tab "Logs" din aplicație
2. Verifică fișierul `processor.log`
3. Verifică că toate dependențele sunt instalate corect

---

## 📄 Licență

Acest software este creat pentru uz personal/comercial.

---

## 🚀 Versiune

**v1.0.0** - Octombrie 2025

### Caracteristici:
✅ Import JSON
✅ AI Enhancement (Gemini)
✅ Calcule automate prețuri
✅ Export WooCommerce
✅ Interfață grafică

### Planuri viitoare:
- Import direct de pe Zentrada (fără scraper)
- Sincronizare automată stocuri
- Actualizare automată prețuri
- Integrare directă cu WooCommerce API

---

**Mult succes cu afacerea ta B2B! 🎉**