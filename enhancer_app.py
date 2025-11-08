# enhancer_app.py - Aplicație Independentă pentru Procesare și Îmbunătățire Produse

import sys
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QProgressBar, QTabWidget, QSpinBox,
    QDoubleSpinBox, QGroupBox, QScrollArea, QCheckBox, QComboBox, QDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from config import *
from product_processor import ProductProcessor
from excel_exporter import ExcelExporter


# ===== DIALOG PENTRU SETĂRI PROCESARE =====
class ProcessingSettingsDialog(QDialog):
    """Dialog pentru a selecta categoria și marja de profit înainte de procesare"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Setări Procesare Produse")
        self.setMinimumWidth(500)
        self.setModal(True)

        self.selected_category = None
        self.selected_profit_margin = 30

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("🎯 Setează parametrii pentru procesare")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)

        # Info text
        info = QLabel("Toți produsele din acest batch vor folosi aceeași categorie și marjă de profit.")
        info.setWordWrap(True)
        info.setStyleSheet("padding: 10px; color: #666;")
        layout.addWidget(info)

        # Category selection
        category_group = QGroupBox("📂 Categorie Produse")
        category_layout = QVBoxLayout()

        category_layout.addWidget(QLabel("Selectează categoria pentru TOATE produsele:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(PRODUCT_CATEGORIES)
        self.category_combo.setCurrentIndex(0)
        category_layout.addWidget(self.category_combo)

        category_group.setLayout(category_layout)
        layout.addWidget(category_group)

        # Profit margin selection
        profit_group = QGroupBox("💰 Marjă de Profit")
        profit_layout = QHBoxLayout()

        profit_layout.addWidget(QLabel("Marjă de profit (%):"))
        self.profit_spinbox = QSpinBox()
        self.profit_spinbox.setRange(0, 200)
        self.profit_spinbox.setValue(30)
        self.profit_spinbox.setSuffix(" %")
        profit_layout.addWidget(self.profit_spinbox)
        profit_layout.addStretch()

        profit_group.setLayout(profit_layout)
        layout.addWidget(profit_group)

        # Preview
        preview_group = QGroupBox("📊 Preview Calcul Preț")
        preview_layout = QVBoxLayout()

        self.preview_label = QLabel()
        self.preview_label.setStyleSheet("padding: 10px; background: #f5f5f5; border-radius: 5px;")
        self.update_preview()
        preview_layout.addWidget(self.preview_label)

        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)

        # Connect profit spinbox to preview update
        self.profit_spinbox.valueChanged.connect(self.update_preview)

        # Buttons
        button_layout = QHBoxLayout()

        ok_btn = QPushButton("✅ Procesează Produse")
        ok_btn.setStyleSheet("padding: 10px; background: #4CAF50; color: white; font-weight: bold;")
        ok_btn.clicked.connect(self.accept)

        cancel_btn = QPushButton("❌ Anulează")
        cancel_btn.setStyleSheet("padding: 10px;")
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(ok_btn)

        layout.addLayout(button_layout)

    def update_preview(self):
        """Actualizează preview-ul calculului de preț"""
        margin = self.profit_spinbox.value()

        # Example calculation
        example_price_eur = 10.0
        example_price_lei = example_price_eur * DEFAULT_EUR_RON_RATE
        sale_price = example_price_lei * (1 + margin / 100)
        sale_price_vat = sale_price * 1.19

        preview_text = f"""
        <b>Exemplu calcul pentru 10 EUR:</b><br>
        <br>
        Preț achiziție: {example_price_lei:.2f} LEI<br>
        Marjă profit: {margin}%<br>
        Preț vânzare: <b>{sale_price:.2f} LEI</b><br>
        Preț vânzare + TVA (19%): <b>{sale_price_vat:.2f} LEI</b><br>
        """

        self.preview_label.setText(preview_text)

    def get_settings(self):
        """Returnează setările selectate"""
        return {
            'category': self.category_combo.currentText(),
            'profit_margin': self.profit_spinbox.value()
        }
# ==========================================


class ProcessingThread(QThread):
    """Thread pentru procesare produse în background"""
    progress = pyqtSignal(int, str)  # value, message
    product_processed = pyqtSignal(int, int, str)  # current, total, message
    finished = pyqtSignal(list, dict)
    error = pyqtSignal(str)

    def __init__(self, products, processor, use_ai, profit_margin, batch_size_api=20, forced_category=None):
        super().__init__()
        self.products = products
        self.processor = processor
        self.use_ai = use_ai
        self.profit_margin = profit_margin
        self.batch_size_api = batch_size_api
        self.forced_category = forced_category  # Categoria forțată pentru toate produsele

    def run(self):
        try:
            total = len(self.products)

            def report_progress(current, total_in_batch, message):
                # Calculează progresul general
                progress_value = int((self.processor.stats['processed_products'] + self.processor.stats['failed_products']) / total * 100)
                self.progress.emit(progress_value, message)

            # Procesează toate produsele, cu callback pentru progres
            all_processed = self.processor.process_batch(
                self.products,
                self.use_ai,
                self.profit_margin,
                report_progress,
                self.batch_size_api
            )

            # Aplică categoria forțată dacă este setată
            if self.forced_category:
                for product in all_processed:
                    product['category'] = self.forced_category

            self.progress.emit(100, "Procesare finalizată!")
            self.finished.emit(all_processed, self.processor.get_stats())

        except Exception as e:
            self.error.emit(str(e))


class ProductEnhancerApp(QMainWindow):
    """Aplicație pentru îmbunătățirea și procesarea produselor"""

    def __init__(self):
        super().__init__()

        self.products_data = []
        self.processed_products = []
        self.processor = None
        self.exporter = ExcelExporter()

        self.init_ui()

    def init_ui(self):
        """Inițializează interfața"""
        self.setWindowTitle("Product Enhancer - Procesare și Îmbunătățire Produse")
        self.setMinimumSize(1400, 900)

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

        # ===== MARJĂ DE PROFIT UNICĂ =====
        profit_group = QGroupBox("📊 Marjă de Profit")
        profit_layout = QHBoxLayout()

        profit_layout.addWidget(QLabel("Marjă de profit (%) pentru toate produsele:"))
        self.profit_margin_input = QSpinBox()
        self.profit_margin_input.setRange(0, 200)
        self.profit_margin_input.setValue(30)  # Default 30%
        self.profit_margin_input.setSuffix(" %")
        profit_layout.addWidget(self.profit_margin_input)
        profit_layout.addStretch()

        profit_group.setLayout(profit_layout)
        scroll_layout.addWidget(profit_group)

        # ===== BATCH SIZE =====
        batch_group = QGroupBox("⚙️ Setări Procesare")
        batch_layout = QHBoxLayout()

        batch_layout.addWidget(QLabel("Batch Size (produse pe lot):"))
        self.batch_size_input = QSpinBox()
        self.batch_size_input.setRange(5, 50)
        self.batch_size_input.setValue(BATCH_SIZE)
        self.batch_size_input.setSingleStep(1)
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
        self.results_table.setColumnCount(10)
        self.results_table.setHorizontalHeaderLabels([
            "SKU", "Nume Produs", "Categorie", "Brand",
            "Preț Vanz. LEI/Buc", "Preț Vanz. LEI/Cutie",
            "Preț Vanz. LEI/Buc + TVA", "Preț Vanz. LEI/Cutie + TVA",
            "Marjă %", "TVA %"
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

            self.products_data = data

            # Actualizează UI
            self.products_info_label.setText(
                f"✅ Încărcate {len(data)} produse din: {os.path.basename(file_path)}"
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

        # AFIȘEAZĂ DIALOG PENTRU SETĂRI
        settings_dialog = ProcessingSettingsDialog(self)
        if settings_dialog.exec() != QDialog.DialogCode.Accepted:
            # User a anulat
            return

        # Obține setările din dialog
        settings = settings_dialog.get_settings()
        forced_category = settings['category']
        profit_margin = settings['profit_margin']

        # Pregătește produsele
        products_to_process = self.products_data
        if self.limit_products_checkbox.isChecked():
            limit = self.limit_products_input.value()
            products_to_process = self.products_data[:limit]

        # Creează procesorul
        try:
            eur_ron_rate = self.eur_ron_input.value()

            self.processor = ProductProcessor(api_key, eur_ron_rate)

            # Pornește thread-ul de procesare
            self.process_btn.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)

            self.processing_thread = ProcessingThread(
                products_to_process,
                self.processor,
                self.use_ai_checkbox.isChecked(),
                profit_margin,
                self.batch_size_input.value(),
                forced_category  # Pasează categoria forțată
            )

            self.processing_thread.progress.connect(self.update_progress)
            self.processing_thread.finished.connect(self.processing_finished)
            self.processing_thread.error.connect(self.processing_error)

            self.processing_thread.start()

            self.log(f"🚀 Început procesare: {len(products_to_process)} produse")
            self.log(f"📂 Categorie forțată: {forced_category}")
            self.log(f"💰 Marjă profit: {profit_margin}%")

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
            self.results_table.setItem(i, 4, QTableWidgetItem(f"{product['price_sale_piece']:.2f} LEI"))
            self.results_table.setItem(i, 5, QTableWidgetItem(f"{product['price_sale_box']:.2f} LEI"))
            self.results_table.setItem(i, 6, QTableWidgetItem(f"{product['price_sale_piece_vat']:.2f} LEI"))
            self.results_table.setItem(i, 7, QTableWidgetItem(f"{product['price_sale_box_vat']:.2f} LEI"))
            self.results_table.setItem(i, 8, QTableWidgetItem(f"{product['margin_percent']}%"))
            self.results_table.setItem(i, 9, QTableWidgetItem(f"19%"))

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


def main():
    """Pornește aplicația"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Stil modern

    window = ProductEnhancerApp()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
