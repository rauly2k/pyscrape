#!/usr/bin/env python3
# launcher.py - Script de lansare pentru aplicații

import sys
from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QPushButton, QLabel, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class AppLauncher(QDialog):
    """Dialog pentru selectarea aplicației de pornit"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Inițializează interfața"""
        self.setWindowTitle("Zentrada Processor - Launcher")
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Selectează Aplicația")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(20)

        # Description
        desc = QLabel(
            "Alege ce aplicație vrei să pornești.\n"
            "Poți rula scraper-ul și enhancer-ul în același timp!"
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(desc)

        layout.addSpacing(30)

        # Combined App Button
        combined_btn = QPushButton("🔧 Aplicație Completă\n(Scraper + Enhancer)")
        combined_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 20px;
                background: #2196F3;
                color: white;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: #1976D2;
            }
        """)
        combined_btn.clicked.connect(self.launch_combined)
        layout.addWidget(combined_btn)

        layout.addSpacing(10)

        # Enhancer Only Button
        enhancer_btn = QPushButton("🎨 Product Enhancer\n(Doar procesare și îmbunătățire)")
        enhancer_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 20px;
                background: #4CAF50;
                color: white;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: #388E3C;
            }
        """)
        enhancer_btn.clicked.connect(self.launch_enhancer)
        layout.addWidget(enhancer_btn)

        layout.addSpacing(10)

        # Both Apps Button
        both_btn = QPushButton("🚀 Pornește Ambele\n(Scraper ȘI Enhancer separat)")
        both_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 20px;
                background: #FF9800;
                color: white;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: #F57C00;
            }
        """)
        both_btn.clicked.connect(self.launch_both)
        layout.addWidget(both_btn)

        layout.addSpacing(20)

        # Info
        info = QLabel(
            "💡 Tip: Pentru a folosi scraper-ul și enhancer-ul simultan,\n"
            "alege opțiunea 'Pornește Ambele' sau pornește manual\n"
            "aplicațiile din fișierele main_app.py și enhancer_app.py"
        )
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("color: #999; font-size: 10px;")
        layout.addWidget(info)

    def launch_combined(self):
        """Pornește aplicația completă (scraper + enhancer)"""
        self.close()
        from main_app import ZentradaProcessorApp, QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        window = ZentradaProcessorApp()
        window.show()
        sys.exit(app.exec())

    def launch_enhancer(self):
        """Pornește doar enhancer-ul"""
        self.close()
        from enhancer_app import ProductEnhancerApp, QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        window = ProductEnhancerApp()
        window.show()
        sys.exit(app.exec())

    def launch_both(self):
        """Pornește ambele aplicații în ferestre separate"""
        try:
            import subprocess
            import os

            # Get the current directory
            current_dir = os.path.dirname(os.path.abspath(__file__))

            # Launch main_app.py in a new process
            subprocess.Popen([sys.executable, os.path.join(current_dir, "main_app.py")])

            # Launch enhancer_app.py in a new process
            subprocess.Popen([sys.executable, os.path.join(current_dir, "enhancer_app.py")])

            # Show info message
            QMessageBox.information(
                self,
                "Aplicații Pornite",
                "Au fost pornite ambele aplicații în ferestre separate:\n\n"
                "1. Scraper + Enhancer (aplicația completă)\n"
                "2. Product Enhancer (doar procesare)\n\n"
                "Poți folosi ambele aplicații simultan!"
            )

            # Close launcher
            self.close()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Eroare",
                f"Eroare la pornirea aplicațiilor:\n{str(e)}"
            )


def main():
    """Pornește launcher-ul"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    launcher = AppLauncher()
    launcher.exec()


if __name__ == '__main__':
    main()
