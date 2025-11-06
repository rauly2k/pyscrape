# Zentrada Processor - Ghid de Utilizare

## 📋 Rezumat Actualizări

### Îmbunătățiri Majore

1. **Aplicații Independente**: Acum poți rula scraper-ul și enhancer-ul simultan în ferestre separate
2. **Marjă de Profit Unică**: O singură marjă de profit pentru toate produsele (în loc de marje pe categorii)
3. **Coloane Noi de Prețuri**: Prețuri cu și fără TVA vizibile în export

---

## 🚀 Cum să Pornești Aplicația

### Opțiunea 1: Launcher (Recomandat)

Rulează `launcher.py` pentru a alege ce aplicație vrei să pornești:

```bash
python launcher.py
```

Vei avea 3 opțiuni:
- **Aplicație Completă** (Scraper + Enhancer în același loc)
- **Product Enhancer** (Doar procesare și îmbunătățire produse)
- **Pornește Ambele** (Scraper ȘI Enhancer în ferestre separate - pentru utilizare simultană)

### Opțiunea 2: Direct

#### Aplicație Completă (Scraper + Enhancer)
```bash
python main_app.py
```

#### Doar Product Enhancer
```bash
python enhancer_app.py
```

---

## 💰 Noua Structură de Prețuri

### Formula de Calcul

```
1. Preț Achiziție LEI/Buc = Preț EUR/Buc × Curs EUR/RON
2. Preț Vânzare LEI/Buc = Preț Achiziție LEI/Buc × (1 + Marjă Profit %)
3. Preț Vânzare LEI/Buc + TVA = Preț Vânzare LEI/Buc × 1.19
```

### Exemplu de Calcul

Presupunem:
- Preț achiziție: **2.15 EUR/buc**
- Curs EUR/RON: **5.02**
- Marjă profit: **30%**
- TVA: **19%**

**Calcul:**
1. Preț Ach. LEI/Buc = 2.15 × 5.02 = **10.79 LEI**
2. Preț Vânzare LEI/Buc = 10.79 × 1.30 = **14.03 LEI**
3. Preț Vânzare LEI/Buc + TVA = 14.03 × 1.19 = **16.70 LEI**

---

## 📊 Coloane în Excel Export

### Fișier: `verificare_produse_YYYYMMDD_HHMMSS.xlsx`

| Coloană | Descriere |
|---------|-----------|
| Nr. Articol | Număr articol din Zentrada |
| SKU | SKU pentru WooCommerce |
| EAN | Cod EAN |
| Nume Produs | Nume tradus în română de AI |
| Categorie | Categorie aleasă de AI |
| Brand | Brand produs |
| Țara Origine | Țara de origine |
| Buc/Cutie | Bucăți per cutie |
| Preț Ach. EUR/Buc | Preț achiziție în EUR per bucată |
| Preț Ach. EUR/Cutie | Preț achiziție în EUR per cutie |
| Pret Ach LEI/Buc | Preț achiziție în LEI per bucată |
| Pret Ach LEI/Cutie | Preț achiziție în LEI per cutie |
| **Pret Vanzare LEI/Buc** | **Preț vânzare cu marjă (fără TVA)** |
| **Pret Vanzare LEI/Cutie** | **Preț vânzare cu marjă per cutie (fără TVA)** |
| TVA (19%) | Cota de TVA aplicată |
| **Pret Vanzare LEI/Buc + TVA** | **Preț final cu TVA inclus per bucată** |
| **Pret Vanzare LEI/Cutie + TVA** | **Preț final cu TVA inclus per cutie** |
| MixOrder | Dacă produsul permite mix order |
| Cantitate Min. | Cantitatea minimă de comandă |
| Brand Licentiat | Dacă este brand licențiat (Disney, Marvel, etc.) |
| URL Zentrada | Link către produsul pe Zentrada |

---

## ⚙️ Setări și Configurări

### Tab Configurări

1. **Gemini API Key**: Cheia ta API pentru procesare AI
2. **Curs EUR/RON**: Cursul valutar (default: 5.02)
3. **Marjă de Profit**: Marja de profit pentru TOATE produsele (%)
4. **Batch Size**: Câte produse se procesează într-un apel AI (recomandat: 7)

### Marjă de Profit

În loc de marje diferite pe categorii, acum ai o **singură marjă** care se aplică tuturor produselor.

**Exemplu:**
- Setezi marjă: **30%**
- Toți produsele vor avea marjă de profit de 30%

---

## 🔄 Workflow Recomandat

### Utilizare Simultană (Scraper + Enhancer)

1. **Pornește launcher.py** și alege "Pornește Ambele"
2. În **main_app.py** (fereastra 1):
   - Configurează scraper-ul
   - Pornește scraping-ul categoriei
   - Produsele se salvează automat în JSON
3. În **enhancer_app.py** (fereastra 2):
   - Încarcă fișierul JSON salvat de scraper
   - Setează marja de profit
   - Procesează cu AI
   - Exportă în Excel/WooCommerce

**Avantaj**: Poți continua scraping-ul în timp ce procesezi alte produse!

---

## 🐛 Rezolvare Probleme

### "Nu găsesc modulul PyQt6"
```bash
pip install PyQt6
```

### "API Key invalid"
- Verifică că ai introdus cheia API corectă în tab-ul Configurări
- Sau setează în fișierul `.env`:
  ```
  GEMINI_API_KEY=your_api_key_here
  ```

### "Batch size prea mare - răspuns AI tăiat"
- Reduce batch size la 5-7 produse
- Gemini 2.5 Flash are limită de 8192 tokens output

---

## 📁 Structura Fișierelor

```
pyscrape/
├── launcher.py              # Launcher pentru alegerea aplicației
├── main_app.py              # Aplicație completă (Scraper + Enhancer)
├── enhancer_app.py          # Doar procesare/îmbunătățire produse
├── product_processor.py     # Logica de procesare și calcul prețuri
├── excel_exporter.py        # Export Excel și WooCommerce
├── config.py                # Configurări globale
├── scraper.py               # Scraper Zentrada (produs individual)
├── scraper_full.py          # Scraper categorie cu paginare
├── exports/                 # Folderul unde se salvează exporturile
└── USAGE_GUIDE.md           # Acest fișier
```

---

## 💡 Tips & Tricks

### 1. Procesare Rapidă
- Dezactivează AI dacă vrei doar să calculezi prețurile
- Produsele vor fi procesate instant (fără traducere/categorizare)

### 2. Batch Size Optim
- Pentru produse cu descrieri scurte: **7-10 produse**
- Pentru produse cu descrieri lungi: **5-7 produse**

### 3. Export Verificare
- Folosește "Export Excel Verificare" pentru a verifica calculele
- Toate coloanele sunt auto-formatate și lizibile

### 4. Utilizare Simultană
- Poți rula scraper-ul 24/7 pentru a colecta produse
- În paralel, procesezi produsele deja colectate cu AI

---

## 📞 Contact & Suport

Pentru probleme sau întrebări, verifică:
- Log-urile din tab-ul "Logs"
- Fișierele de export din folderul `exports/`
- Configurările din `config.py`

---

**Versiune**: 2.0
**Data**: 2025-11-06
**Autor**: Claude Agent SDK
