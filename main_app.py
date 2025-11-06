# main_app.py - Interfață Grafică Principală

import sys
import os
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QProgressBar, QTabWidget, QSpinBox,
    QDoubleSpinBox, QGroupBox, QScrollArea, QCheckBox, QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from config import *
from product_processor import ProductProcessor
from excel_exporter import ExcelExporter

# ===== IMPORTURI NOI PENTRU SCRAPER =====
try:
    from scraper import ZentradaScraper
    import config as scraper_config
except ImportError:
    print("EROARE: Nu gasesc scraper.py sau config.py. Asigura-te ca sunt in acelasi folder.")
    # Putem arata o eroare in UI mai tarziu

# ========================================


class ProcessingThread(QThread):
    """Thread pentru procesare produse în background"""
    progress = pyqtSignal(int, str) # value, message
    product_processed = pyqtSignal(int, int, str) # current, total, message
    finished = pyqtSignal(list, dict)
    error = pyqtSignal(str)
    
    def __init__(self, products, processor, use_ai, default_category=None, batch_size_api=20):
        super().__init__()
        self.products = products
        self.processor = processor
        self.use_ai = use_ai
        self.default_category = default_category
        self.batch_size_api = batch_size_api
    
    def run(self):
        try:
            total = len(self.products)

            def report_progress(current, total_in_batch, message):
                # Calculează progresul general
                progress_value = int((self.processor.stats['processed_products'] + self.processor.stats['failed_products']) / total * 100)
                self.progress.emit(progress_value, message)

            # Procesează toate produsele, cu callback pentru progres
            all_processed = self.processor.process_batch(self.products, self.use_ai, self.default_category, report_progress, self.batch_size_api)
            
            self.progress.emit(100, "Procesare finalizată!")
            self.finished.emit(all_processed, self.processor.get_stats())
            
        except Exception as e:
            self.error.emit(str(e))


# ===== THREAD NOU PENTRU SCRAPER =====
class ScraperThread(QThread):
    """Thread pentru a rula scraper-ul în background"""
    log_message = pyqtSignal(str)
    finished_login = pyqtSignal(bool, str)
    
    def __init__(self):
        super().__init__()
        self.scraper = None

    def run(self):
        try:
            self.log_message.emit("Pornesc browser-ul...")
            
            # Verifică dacă credentialele sunt setate in config.py
            if not scraper_config.ZENTRADA_EMAIL or not scraper_config.ZENTRADA_PASSWORD:
                raise ValueError("Email-ul sau parola ZENTRADA nu sunt setate în config.py!")

            self.scraper = ZentradaScraper()
            self.scraper.start()
            
            self.log_message.emit("Browser pornit. Încep autentificarea...")
            
            # Transmite log-urile din scraper
            def scraper_log_handler(msg):
                self.log_message.emit(f"[Scraper] {msg}")
            
            # Suprascriem funcția print din scraper (dacă am avea acces)
            # Alternativ, ne bazăm pe logica din scraper.py
            # Deoarece scraper.py folosește print, va trebui să le interceptăm
            # Dar pentru acest test, trimitem mesaje de aici
            
            self.log_message.emit(f"Folosesc email: {scraper_config.ZENTRADA_EMAIL}")
            self.scraper.login() # Această funcție conține pașii de login
            
            self.log_message.emit("✅ Autentificare reușită!")
            self.log_message.emit("Browser-ul va rămâne deschis 10 secunde pentru verificare...")
            time.sleep(10)
            
            self.finished_login.emit(True, "Autentificare reușită!")
            
        except Exception as e:
            self.log_message.emit(f"❌ EROARE la autentificare: {str(e)}")
            self.finished_login.emit(False, str(e))
        finally:
            if self.scraper:
                self.log_message.emit("Închid browser-ul...")
                self.scraper.close()
                self.log_message.emit("Browser închis.")
# =======================================


# ===== THREAD PENTRU CATEGORY SCRAPING =====
class CategoryScrapingThread(QThread):
    """Thread pentru scraping categorie cu paginare"""
    progress = pyqtSignal(int, int, str)  # current_page, total_pages, message
    finished = pyqtSignal(list)  # products list
    error = pyqtSignal(str)
    log_message = pyqtSignal(str)

    def __init__(self, category_url: str, max_pages: int):
        super().__init__()
        self.category_url = category_url
        self.max_pages = max_pages
        self.scraper = None

    def run(self):
        try:
            from scraper_full import CategoryScraper

            self.log_message.emit("🔗 Conectare la Chrome-ul tău deschis...")
            self.scraper = CategoryScraper()

            if not self.scraper.connect_to_chrome():
                self.error.emit("Nu pot conecta la Chrome! Asigură-te că ai Chrome deschis cu:\nchrome.exe --remote-debugging-port=9222")
                return

            self.log_message.emit("✅ Conectat la Chrome!")
            self.log_message.emit(f"📂 Încep scraping: {self.category_url}")
            self.log_message.emit(f"📄 Pagini de extras: {self.max_pages}")
            self.log_message.emit("")

            def progress_callback(current, total, message):
                self.progress.emit(current, total, message)
                self.log_message.emit(message)

            products = self.scraper.scrape_category(
                self.category_url,
                self.max_pages,
                progress_callback
            )

            self.log_message.emit("")
            self.log_message.emit(f"✅ Finalizat! {len(products)} produse extrase")
            self.finished.emit(products)

        except Exception as e:
            self.log_message.emit(f"❌ EROARE: {str(e)}")
            self.error.emit(str(e))
        finally:
            if self.scraper:
                self.scraper.close()
# =======================================


class ZentradaProcessorApp(QMainWindow):
    """Aplicația principală"""
    
    def __init__(self):
        super().__init__()

        self.products_data = []
        self.processed_products = []
        self.processor = None
        self.exporter = ExcelExporter()
        self.scraper_thread = None # Referință pentru thread-ul scraper-ului
        self.default_category = None # Categoria prestabilită pentru toate produsele

        self.init_ui()
    
    def init_ui(self):
        """Inițializează interfața"""
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        
        # Widget central cu tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Tab 1: Configurări
        self.create_config_tab()
        
        # Tab 2: Import & Procesare
        self.create_process_tab()
        
        # Tab 3: Rezultate
        self.create_results_tab()
        
        # ===== TAB NOU PENTRU SCRAPER =====
        self.create_scraper_tab()
        # ===================================
        
        # Tab 4: Logs
        self.create_logs_tab()
    
    def create_config_tab(self):
        """Tab cu configurări"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Scroll area pentru configurări
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # ===== API KEY =====
        api_group = QGroupBox("🔑 Gemini API Key")
        api_layout = QVBoxLayout()
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Introdu API Key-ul Gemini aici...")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)

        # Load API key from .env if available
        api_key_from_env = os.getenv('GEMINI_API_KEY', '')
        if api_key_from_env:
            self.api_key_input.setText(api_key_from_env)
        api_layout.addWidget(self.api_key_input)
        
        show_api_btn = QPushButton("Arată/Ascunde API Key")
        show_api_btn.clicked.connect(self.toggle_api_visibility)
        api_layout.addWidget(show_api_btn)
        
        api_group.setLayout(api_layout)
        scroll_layout.addWidget(api_group)
        
        # ===== CURS EUR/RON =====
        currency_group = QGroupBox("💱 Curs Valutar")
        currency_layout = QHBoxLayout()
        
        currency_layout.addWidget(QLabel("Curs EUR/RON:"))
        self.eur_ron_input = QDoubleSpinBox()
        self.eur_ron_input.setRange(4.0, 6.0)
        self.eur_ron_input.setSingleStep(0.01)
        self.eur_ron_input.setValue(DEFAULT_EUR_RON_RATE)
        self.eur_ron_input.setDecimals(2)
        currency_layout.addWidget(self.eur_ron_input)
        currency_layout.addStretch()
        
        currency_group.setLayout(currency_layout)
        scroll_layout.addWidget(currency_group)
        
        # ===== MARJE PE CATEGORII =====
        margins_group = QGroupBox("📊 Marje de Profit (%)")
        margins_layout = QVBoxLayout()
        
        self.margin_inputs = {}
        for category, default_margin in CATEGORY_MARGINS.items():
            row = QHBoxLayout()
            row.addWidget(QLabel(category))
            
            spinbox = QSpinBox()
            spinbox.setRange(0, 200)
            spinbox.setValue(default_margin)
            spinbox.setSuffix(" %")
            self.margin_inputs[category] = spinbox
            row.addWidget(spinbox)
            row.addStretch()
            
            margins_layout.addLayout(row)
        
        margins_group.setLayout(margins_layout)
        scroll_layout.addWidget(margins_group)
        
        # ===== BATCH SIZE =====
        batch_group = QGroupBox("⚙️ Setări Procesare")
        batch_layout = QHBoxLayout()
        
        batch_layout.addWidget(QLabel("Batch Size (produse pe lot):"))
        self.batch_size_input = QSpinBox()
        self.batch_size_input.setRange(5, 50)  # Allow 5-50 (Gemini 2.5 Flash limit ~7-8 products max)
        self.batch_size_input.setValue(BATCH_SIZE)
        self.batch_size_input.setSingleStep(1)  # Increment by 1 for fine control
        batch_layout.addWidget(self.batch_size_input)

        # Add warning label
        batch_warning = QLabel("⚠️ Recomandat: 7 produse (limita Gemini 2.5 Flash)")
        batch_warning.setStyleSheet("color: #ff9800; font-size: 9px;")
        batch_layout.addWidget(batch_warning)
        batch_layout.addStretch()
        
        batch_group.setLayout(batch_layout)
        scroll_layout.addWidget(batch_group)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Buton salvare configurări
        save_btn = QPushButton("💾 Salvează Configurările")
        save_btn.clicked.connect(self.save_config)
        layout.addWidget(save_btn)
        
        self.tabs.addTab(tab, "⚙️ Configurări")
    
    def create_process_tab(self):
        """Tab pentru import și procesare"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Buton încărcare JSON
        load_btn = QPushButton("📂 Încarcă Fișier JSON")
        load_btn.clicked.connect(self.load_json_file)
        load_btn.setStyleSheet("font-size: 14px; padding: 10px;")
        layout.addWidget(load_btn)
        
        # Info produse încărcate
        self.products_info_label = QLabel("Niciun fișier încărcat")
        self.products_info_label.setStyleSheet("font-size: 12px; padding: 10px; background: #f0f0f0; border-radius: 5px;")
        layout.addWidget(self.products_info_label)
        
        # Preview produse
        preview_group = QGroupBox("👀 Preview Produse Încărcate")
        preview_layout = QVBoxLayout()
        
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(6)
        self.preview_table.setHorizontalHeaderLabels([
            "Nr. Articol", "Brand", "Nume Produs", "Preț", "Buc/Cutie", "Mix Order"
        ])
        preview_layout.addWidget(self.preview_table)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Opțiuni procesare
        options_layout = QHBoxLayout()
        
        self.use_ai_checkbox = QCheckBox("Folosește AI pentru traducere și categorizare")
        self.use_ai_checkbox.setChecked(True)
        options_layout.addWidget(self.use_ai_checkbox)
        
        options_layout.addStretch()
        
        self.limit_products_checkbox = QCheckBox("Limitează la primele:")
        self.limit_products_input = QSpinBox()
        self.limit_products_input.setRange(1, 10000)
        self.limit_products_input.setValue(50)
        self.limit_products_input.setEnabled(False)
        self.limit_products_checkbox.stateChanged.connect(
            lambda: self.limit_products_input.setEnabled(self.limit_products_checkbox.isChecked())
        )
        options_layout.addWidget(self.limit_products_checkbox)
        options_layout.addWidget(self.limit_products_input)
        options_layout.addWidget(QLabel("produse"))
        
        layout.addLayout(options_layout)
        
        # Buton procesare
        self.process_btn = QPushButton("🚀 PROCESEAZĂ PRODUSE")
        self.process_btn.clicked.connect(self.start_processing)
        self.process_btn.setEnabled(False)
        self.process_btn.setStyleSheet("font-size: 16px; padding: 15px; background: #4CAF50; color: white;")
        layout.addWidget(self.process_btn)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress_label)
        
        self.tabs.addTab(tab, "📥 Import & Procesare")
    
    def create_results_tab(self):
        """Tab cu rezultate"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Info statistici
        self.stats_label = QLabel("Niciun produs procesat încă")
        self.stats_label.setStyleSheet("font-size: 12px; padding: 10px; background: #e3f2fd; border-radius: 5px;")
        layout.addWidget(self.stats_label)
        
        # Tabel rezultate
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(8)
        self.results_table.setHorizontalHeaderLabels([
            "SKU", "Nume Produs", "Categorie", "Brand", "Preț Final/Buc (LEI)", 
            "Preț Final/Cutie (LEI)", "Marjă %", "TVA %"
        ])
        layout.addWidget(self.results_table)
        
        # Butoane export
        export_layout = QHBoxLayout()
        
        export_woo_btn = QPushButton("📤 Export WooCommerce CSV")
        export_woo_btn.clicked.connect(self.export_woocommerce)
        export_layout.addWidget(export_woo_btn)
        
        export_internal_btn = QPushButton("📊 Export Excel Verificare")
        export_internal_btn.clicked.connect(self.export_internal)
        export_layout.addWidget(export_internal_btn)
        
        export_both_btn = QPushButton("💾 Export Ambele")
        export_both_btn.clicked.connect(self.export_both)
        export_layout.addWidget(export_both_btn)
        
        layout.addLayout(export_layout)
        
        self.tabs.addTab(tab, "📊 Rezultate")
    
    # ===== FUNCȚIE NOUĂ PENTRU TAB-UL SCRAPER =====
    def create_scraper_tab(self):
        """Tab pentru scraping Zentrada"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Setări Scraper
        scraper_settings_group = QGroupBox("⚙️ Setări Scraper")
        settings_layout = QVBoxLayout(scraper_settings_group)
        
        # URL Categorie
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("URL Categorie:"))
        self.category_url_input = QLineEdit()
        self.category_url_input.setPlaceholderText("https://www.zentrada.com/eu/shop/Gifts-Stationery/...")
        url_layout.addWidget(self.category_url_input)
        settings_layout.addLayout(url_layout)
        
        # Număr Pagini
        pages_layout = QHBoxLayout()
        pages_layout.addWidget(QLabel("Număr pagini de extras:"))
        self.pages_to_scrape_input = QSpinBox()
        self.pages_to_scrape_input.setRange(1, 100)
        self.pages_to_scrape_input.setValue(1)
        pages_layout.addWidget(self.pages_to_scrape_input)
        pages_layout.addStretch()
        settings_layout.addLayout(pages_layout)
        
        layout.addWidget(scraper_settings_group)
        
        # Butoane Acțiune
        action_layout = QHBoxLayout()
        self.test_login_btn = QPushButton("🔑 Testează Autentificarea")
        self.test_login_btn.clicked.connect(self.start_login_test)
        self.test_login_btn.setStyleSheet("font-size: 14px; padding: 10px; background: #0277bd; color: white;")
        action_layout.addWidget(self.test_login_btn)
        
        self.start_scraping_btn = QPushButton("🚀 Începe Scraping")
        self.start_scraping_btn.setEnabled(True)
        self.start_scraping_btn.clicked.connect(self.start_scraping)
        self.start_scraping_btn.setStyleSheet("font-size: 14px; padding: 10px; background: #4CAF50; color: white;")
        action_layout.addWidget(self.start_scraping_btn)
        
        layout.addLayout(action_layout)

        # Log Scraper
        log_group = QGroupBox("📋 Log Scraper")
        log_layout = QVBoxLayout(log_group)
        self.scraper_log_text = QTextEdit()
        self.scraper_log_text.setReadOnly(True)
        self.scraper_log_text.setStyleSheet("font-family: 'Courier New'; font-size: 10px;")
        log_layout.addWidget(self.scraper_log_text)
        
        layout.addWidget(log_group)
        
        self.tabs.addTab(tab, "🕷️ Scraper")
    # ===============================================

    def create_logs_tab(self):
        """Tab cu logs"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        layout.addWidget(QLabel("📋 Log Procesare:"))
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("font-family: 'Courier New'; font-size: 10px;")
        layout.addWidget(self.log_text)
        
        clear_btn = QPushButton("🗑️ Șterge Log")
        clear_btn.clicked.connect(self.log_text.clear)
        layout.addWidget(clear_btn)
        
        self.tabs.addTab(tab, "📋 Logs")
    
    def toggle_api_visibility(self):
        """Toggle vizibilitate API Key"""
        if self.api_key_input.echoMode() == QLineEdit.EchoMode.Password:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
    
    def save_config(self):
        """Salvează configurările"""
        # Actualizează marjele în config
        for category, spinbox in self.margin_inputs.items():
            CATEGORY_MARGINS[category] = spinbox.value()
        
        self.log("✅ Configurări salvate cu succes!")
        QMessageBox.information(self, "Succes", "Configurările au fost salvate!")
    
    def load_json_file(self):
        """Încarcă fișierul JSON"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selectează fișierul JSON",
            "",
            "JSON Files (*.json)"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Transformă în listă dacă e dict
            if isinstance(data, dict):
                data = [data]

            # Ask user if they want to set a default category for all products
            reply = QMessageBox.question(
                self,
                "Setare Categorie",
                f"Ai încărcat {len(data)} produse.\n\n"
                "Vrei să setezi o categorie prestabilită pentru TOATE produsele?\n\n"
                "Dacă DA: Toate produsele vor avea categoria selectată (AI nu va mai alege categoria)\n"
                "Dacă NU: AI va alege categoria pentru fiecare produs individual",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            self.default_category = None

            if reply == QMessageBox.StandardButton.Yes:
                # Show category selection dialog
                from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QDialogButtonBox

                dialog = QDialog(self)
                dialog.setWindowTitle("Selectează Categoria")
                dialog.setMinimumWidth(400)

                layout = QVBoxLayout(dialog)

                layout.addWidget(QLabel("Selectează categoria pentru toate produsele:"))

                category_combo = QComboBox()
                category_combo.addItems(PRODUCT_CATEGORIES)
                layout.addWidget(category_combo)

                # Add buttons
                buttons = QDialogButtonBox(
                    QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
                )
                buttons.accepted.connect(dialog.accept)
                buttons.rejected.connect(dialog.reject)
                layout.addWidget(buttons)

                if dialog.exec() == QDialog.DialogCode.Accepted:
                    self.default_category = category_combo.currentText()
                    self.log(f"📁 Categorie prestabilită: {self.default_category}")
                    QMessageBox.information(
                        self,
                        "Categorie Setată",
                        f"Toate produsele vor fi procesate în categoria:\n\n{self.default_category}"
                    )
                else:
                    # User cancelled
                    return

            self.products_data = data

            # Actualizează UI
            category_info = f" (Categorie: {self.default_category})" if self.default_category else ""
            self.products_info_label.setText(
                f"✅ Încărcate {len(data)} produse din: {os.path.basename(file_path)}{category_info}"
            )
            self.process_btn.setEnabled(True)

            # Preview
            self.update_preview_table()

            self.log(f"📂 Încărcate {len(data)} produse din {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Eroare", f"Eroare la încărcarea JSON:\n{str(e)}")
            self.log(f"❌ Eroare încărcare JSON: {str(e)}")
    
    def update_preview_table(self):
        """Actualizează tabelul de preview"""
        self.preview_table.setRowCount(min(len(self.products_data), 20))
        
        for i, product in enumerate(self.products_data[:20]):
            self.preview_table.setItem(i, 0, QTableWidgetItem(product.get('article_number', '')))
            self.preview_table.setItem(i, 1, QTableWidgetItem(product.get('brand', '')))
            self.preview_table.setItem(i, 2, QTableWidgetItem(product.get('product_name', '')))
            self.preview_table.setItem(i, 3, QTableWidgetItem(product.get('price', '')))
            self.preview_table.setItem(i, 4, QTableWidgetItem(product.get('piece_per_pu', '')))
            self.preview_table.setItem(i, 5, QTableWidgetItem('Da' if product.get('mix_order') else 'Nu'))
    
    def start_processing(self):
        """Pornește procesarea produselor"""
        # Validări
        api_key = self.api_key_input.text().strip()
        if not api_key and self.use_ai_checkbox.isChecked():
            QMessageBox.warning(self, "Atenție", "Introdu API Key-ul Gemini în tab-ul Configurări!")
            return
        
        if not self.products_data:
            QMessageBox.warning(self, "Atenție", "Nu ai încărcat niciun fișier JSON!")
            return
        
        # Pregătește produsele
        products_to_process = self.products_data
        if self.limit_products_checkbox.isChecked():
            limit = self.limit_products_input.value()
            products_to_process = self.products_data[:limit]
        
        # Creează procesorul
        try:
            eur_ron_rate = self.eur_ron_input.value()
            self.processor = ProductProcessor(api_key, eur_ron_rate)
            
            # Actualizează marjele
            for category, spinbox in self.margin_inputs.items():
                CATEGORY_MARGINS[category] = spinbox.value()
            
            # Pornește thread-ul de procesare
            self.process_btn.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            self.processing_thread = ProcessingThread(
                products_to_process,
                self.processor,
                self.use_ai_checkbox.isChecked(),
                self.default_category,
                self.batch_size_input.value() # Pass the batch size from the UI
            )
            
            self.processing_thread.progress.connect(self.update_progress)
            self.processing_thread.finished.connect(self.processing_finished)
            self.processing_thread.error.connect(self.processing_error)
            
            self.processing_thread.start()
            
            self.log(f"🚀 Început procesare: {len(products_to_process)} produse")
            
        except Exception as e:
            QMessageBox.critical(self, "Eroare", f"Eroare la inițializarea procesării:\n{str(e)}")
            self.log(f"❌ Eroare: {str(e)}")
    
    def update_progress(self, value, message):
        """Actualizează progress bar"""
        self.progress_bar.setValue(value)
        self.progress_label.setText(message)
        self.log(message)
    
    def processing_finished(self, processed_products, stats):
        """Procesare finalizată"""
        self.processed_products = processed_products
        
        # Actualizează UI
        self.progress_bar.setVisible(False)
        self.progress_label.setText("")
        self.process_btn.setEnabled(True)
        
        # Afișează statistici
        stats_text = f"""
        ✅ Procesare finalizată!
        
        📊 Total produse încărcate: {stats['total_products']}
        ✅ Produse procesate cu succes: {stats['processed_products']}
        ❌ Produse cu erori: {stats['failed_products']}
        🤖 Apeluri AI: {stats['ai_calls']}
        """
        
        self.stats_label.setText(stats_text)
        self.log(stats_text)
        
        # Actualizează tabelul de rezultate
        self.update_results_table()
        
        # Switch la tab-ul rezultate
        self.tabs.setCurrentIndex(2)
        
        QMessageBox.information(self, "Succes", f"Procesare finalizată!\n\n{stats['processed_products']} produse procesate cu succes!")
    
    def processing_error(self, error_message):
        """Eroare la procesare"""
        self.progress_bar.setVisible(False)
        self.progress_label.setText("")
        self.process_btn.setEnabled(True)
        
        QMessageBox.critical(self, "Eroare", f"Eroare la procesare:\n{error_message}")
        self.log(f"❌ EROARE: {error_message}")
    
    def update_results_table(self):
        """Actualizează tabelul de rezultate"""
        self.results_table.setRowCount(len(self.processed_products))
        
        for i, product in enumerate(self.processed_products):
            self.results_table.setItem(i, 0, QTableWidgetItem(product['sku']))
            self.results_table.setItem(i, 1, QTableWidgetItem(product['name']))
            self.results_table.setItem(i, 2, QTableWidgetItem(product['category']))
            self.results_table.setItem(i, 3, QTableWidgetItem(product['brand']))
            self.results_table.setItem(i, 4, QTableWidgetItem(f"{product['price_final_piece']:.2f} LEI"))
            self.results_table.setItem(i, 5, QTableWidgetItem(f"{product['price_final_box']:.2f} LEI"))
            self.results_table.setItem(i, 6, QTableWidgetItem(f"{product['margin_percent']}%"))
            self.results_table.setItem(i, 7, QTableWidgetItem(f"{product['vat_rate']}%"))
    
    def export_woocommerce(self):
        """Export WooCommerce CSV"""
        if not self.processed_products:
            QMessageBox.warning(self, "Atenție", "Nu ai produse procesate pentru export!")
            return
        
        try:
            filepath = self.exporter.export_woocommerce(self.processed_products)
            self.log(f"✅ Export WooCommerce: {filepath}")
            QMessageBox.information(self, "Succes", f"Export WooCommerce salvat:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Eroare", f"Eroare la export:\n{str(e)}")
            self.log(f"❌ Eroare export: {str(e)}")
    
    def export_internal(self):
        """Export Excel intern"""
        if not self.processed_products:
            QMessageBox.warning(self, "Atenție", "Nu ai produse procesate pentru export!")
            return
        
        try:
            filepath = self.exporter.export_internal(self.processed_products)
            self.log(f"✅ Export Excel verificare: {filepath}")
            QMessageBox.information(self, "Succes", f"Excel verificare salvat:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Eroare", f"Eroare la export:\n{str(e)}")
            self.log(f"❌ Eroare export: {str(e)}")
    
    def export_both(self):
        """Export ambele formate"""
        if not self.processed_products:
            QMessageBox.warning(self, "Atenție", "Nu ai produse procesate pentru export!")
            return
        
        try:
            woo_path, internal_path = self.exporter.export_both(self.processed_products)
            self.log(f"✅ Export WooCommerce: {woo_path}")
            self.log(f"✅ Export Excel verificare: {internal_path}")
            QMessageBox.information(
                self, 
                "Succes", 
                f"Exporturi salvate:\n\n1. WooCommerce CSV:\n{woo_path}\n\n2. Excel Verificare:\n{internal_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Eroare", f"Eroare la export:\n{str(e)}")
            self.log(f"❌ Eroare export: {str(e)}")
    
    def log(self, message):
        """Adaugă mesaj în log"""
        self.log_text.append(message)

    # ===== FUNCȚII NOI PENTRU SCRAPER =====
    def log_scraper(self, message):
        """Adaugă mesaj în log-ul scraper-ului"""
        self.scraper_log_text.append(message)

    def start_login_test(self):
        """Pornește testul de autentificare în thread"""
        self.test_login_btn.setEnabled(False)
        self.test_login_btn.setText("Se testează...")
        self.scraper_log_text.clear()
        
        self.scraper_thread = ScraperThread()
        self.scraper_thread.log_message.connect(self.log_scraper)
        self.scraper_thread.finished_login.connect(self.on_login_test_finished)
        self.scraper_thread.start()

    def on_login_test_finished(self, success, message):
        """Se execută la finalul testului de login"""
        self.test_login_btn.setEnabled(True)
        self.test_login_btn.setText("🔑 Testează Autentificarea")
        
        if success:
            QMessageBox.information(self, "Succes", "Autentificare reușită!")
            # Am putea activa butonul de scraping
            # self.start_scraping_btn.setEnabled(True)
            # self.start_scraping_btn.setStyleSheet("font-size: 14px; padding: 10px; background: #4CAF50; color: white;")
        else:
            QMessageBox.critical(self, "Eroare Autentificare", f"Autentificarea a eșuat:\n{message}\n\nVerifică credentialele în config.py și conexiunea la internet.")
    # =======================================

    def start_scraping(self):
        """Pornește scraping-ul categoriei"""
        # Validări
        category_url = self.category_url_input.text().strip()
        if not category_url:
            QMessageBox.warning(self, "Atenție", "Introdu URL-ul categoriei!")
            return

        max_pages = self.pages_to_scrape_input.value()

        # Verifică că Chrome e deschis cu debugging
        reply = QMessageBox.question(
            self,
            "Verificare Chrome",
            "Ai deschis Chrome cu debugging activat?\n\n"
            "Comanda necesară:\n"
            'chrome.exe --remote-debugging-port=9222 --user-data-dir="C:/ChromeDebug"\n\n'
            "Ești logat pe Zentrada în acel Chrome?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.No:
            return

        # Disable button și clear log
        self.start_scraping_btn.setEnabled(False)
        self.start_scraping_btn.setText("⏳ Scraping în curs...")
        self.scraper_log_text.clear()

        # Pornește thread-ul
        self.category_scraping_thread = CategoryScrapingThread(category_url, max_pages)
        self.category_scraping_thread.log_message.connect(self.log_scraper)
        self.category_scraping_thread.progress.connect(self.on_scraping_progress)
        self.category_scraping_thread.finished.connect(self.on_scraping_finished)
        self.category_scraping_thread.error.connect(self.on_scraping_error)
        self.category_scraping_thread.start()

    def on_scraping_progress(self, current, total, message):
        """Actualizare progres scraping"""
        self.log_scraper(f"[{current}/{total}] {message}")

    def on_scraping_finished(self, products):
        """Scraping finalizat"""
        self.start_scraping_btn.setEnabled(True)
        self.start_scraping_btn.setText("🚀 Începe Scraping")

        if products:
            # Salvează în JSON
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"scraped_category_{timestamp}.json"

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(products, f, indent=2, ensure_ascii=False)

            self.log_scraper(f"\n💾 {len(products)} produse salvate în: {output_file}")

            QMessageBox.information(
                self,
                "Scraping Finalizat",
                f"✅ Succes!\n\n{len(products)} produse extrase și salvate în:\n{output_file}\n\nVrei să le procesezi acum cu AI?"
            )

            # Încarcă automat produsele în tab-ul de procesare
            self.products_data = products
            self.products_info_label.setText(
                f"✅ Încărcate {len(products)} produse din scraping"
            )
            self.process_btn.setEnabled(True)
            self.update_preview_table()

        else:
            QMessageBox.warning(self, "Atenție", "Niciun produs nu a fost extras!")

    def on_scraping_error(self, error_message):
        """Eroare la scraping"""
        self.start_scraping_btn.setEnabled(True)
        self.start_scraping_btn.setText("🚀 Începe Scraping")
        QMessageBox.critical(self, "Eroare", f"Eroare la scraping:\n{error_message}")
    # =======================================


def main():
    """Pornește aplicația"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Stil modern
    
    window = ZentradaProcessorApp()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()