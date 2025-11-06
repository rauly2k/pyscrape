# excel_exporter.py - Export către Excel WooCommerce

import pandas as pd
from datetime import datetime
from typing import List, Dict, Any
from config import WOOCOMMERCE_COLUMNS
import os

class ExcelExporter:
    """Exportă produsele procesate către Excel în format WooCommerce"""
    
    def __init__(self, output_folder: str = "exports"):
        """
        Inițializează exporterul
        
        Args:
            output_folder: Folder unde se salvează fișierele
        """
        self.output_folder = output_folder
        
        # Creează folderul dacă nu există
        os.makedirs(output_folder, exist_ok=True)
    
    def products_to_woocommerce_format(self, products: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Convertește produsele procesate în format WooCommerce
        
        Args:
            products: Lista de produse procesate
            
        Returns:
            DataFrame WooCommerce
        """
        rows = []
        
        for product in products:
            row = {
                # Câmpuri WooCommerce standard
                'ID': '',  # WooCommerce va genera
                'Type': 'simple',
                'SKU': product['sku'],
                'Name': product['name'],
                'Published': 1,
                'Is featured?': 0,
                'Visibility in catalog': 'visible',
                'Short description': product['short_description'],
                'Description': product['description'],
                'Date sale price starts': '',
                'Date sale price ends': '',
                'Tax status': 'taxable',
                'Tax class': '',  # Default tax class
                'In stock?': 1,
                'Stock': '',  # Managed externally
                'Low stock amount': '',
                'Backorders allowed?': 0,
                'Sold individually?': 0,
                'Weight (kg)': '',
                'Length (cm)': '',
                'Width (cm)': '',
                'Height (cm)': '',
                'Allow customer reviews?': 1,
                'Purchase note': '',
                'Sale price': '',  # Nu folosim sale price
                'Regular price': product['price_sale_piece_vat'],  # Prețul bucată cu TVA
                'Categories': product['category'],
                'Tags': f"{product['brand']}, B2B",
                'Shipping class': '',
                'Images': product['images'],
                'Download limit': '',
                'Download expiry days': '',
                'Parent': '',
                'Grouped products': '',
                'Upsells': '',
                'Cross-sells': '',
                'External URL': '',
                'Button text': '',
                'Position': 0,
                
                # Atribute personalizate (pentru variații viitoare)
                'Attribute 1 name': 'Cantitate',
                'Attribute 1 value(s)': f"1 Bucată, 1 Cutie ({product['pieces_per_box']} buc)",
                'Attribute 1 visible': 1,
                'Attribute 1 global': 0,
                
                # Meta fields personalizate (date suplimentare)
                'Meta: _brand': product['brand'],
                'Meta: _eur_price_piece': product['price_eur_piece'],
                'Meta: _eur_price_box': product['price_eur_box'],
                'Meta: _lei_price_piece': product['price_lei_piece'],
                'Meta: _lei_price_box': product['price_lei_box'],
                'Meta: _pieces_per_box': product['pieces_per_box'],
                'Meta: _vat_rate': product['vat_rate'],
                'Meta: _margin_percent': product['margin_percent'],
                'Meta: _mix_order': 'yes' if product['mix_order'] else 'no',
                'Meta: _min_order_qty': product['min_order_qty'],
                'Meta: _zentrada_url': product['zentrada_url'],
                'Meta: _country_of_origin': product['country_of_origin'],
                'Meta: _ean': product['ean']
            }
            
            rows.append(row)
        
        # Creează DataFrame
        df = pd.DataFrame(rows)
        
        # Asigură-te că toate coloanele WooCommerce există
        for col in WOOCOMMERCE_COLUMNS:
            if col not in df.columns:
                df[col] = ''
        
        # Reordonează coloanele conform standardului WooCommerce
        df = df[WOOCOMMERCE_COLUMNS]
        
        return df
    
    def create_internal_excel(self, products: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Creează un Excel intern simplu cu toate datele pentru verificare

        Args:
            products: Lista de produse procesate

        Returns:
            DataFrame simplu pentru verificare
        """
        rows = []

        for product in products:
            row = {
                'Nr. Articol': product['article_number'],
                'SKU': product['sku'],
                'EAN': product['ean'],
                'Nume Produs': product['name'],
                'Categorie': product['category'],
                'Brand': product['brand'],
                'Țara Origine': product['country_of_origin'],
                'Buc/Cutie': product['pieces_per_box'],

                # Prețuri achiziție
                'Preț Ach. EUR/Buc': product['price_eur_piece'],
                'Preț Ach. EUR/Cutie': product['price_eur_box'],
                'Pret Ach LEI/Buc': product['price_lei_piece'],
                'Pret Ach LEI/Cutie': product['price_lei_box'],

                # Prețuri vânzare (cu marjă de profit)
                'Pret Vanzare LEI/Buc': product['price_sale_piece'],
                'Pret Vanzare LEI/Cutie': product['price_sale_box'],

                # TVA
                'TVA (19%)': '19%',

                # Prețuri vânzare cu TVA
                'Pret Vanzare LEI/Buc + TVA': product['price_sale_piece_vat'],
                'Pret Vanzare LEI/Cutie + TVA': product['price_sale_box_vat'],

                # Alte detalii
                'MixOrder': 'Da' if product['mix_order'] else 'Nu',
                'Cantitate Min.': product['min_order_qty'],
                'Brand Licentiat': 'Da' if product['is_licensed_brand'] else 'Nu',
                'URL Zentrada': product['zentrada_url']
            }

            rows.append(row)

        df = pd.DataFrame(rows)
        return df
    
    def export_woocommerce(self, products: List[Dict[str, Any]], 
                          filename: str = None) -> str:
        """
        Exportă produsele în format WooCommerce CSV
        
        Args:
            products: Lista de produse procesate
            filename: Numele fișierului (opțional, se generează automat)
            
        Returns:
            Calea către fișierul exportat
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"woocommerce_import_{timestamp}.csv"
        
        filepath = os.path.join(self.output_folder, filename)
        
        # Creează DataFrame WooCommerce
        df = self.products_to_woocommerce_format(products)
        
        # Exportă ca CSV (WooCommerce preferă CSV)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        print(f"✅ Export WooCommerce salvat: {filepath}")
        return filepath
    
    def export_internal(self, products: List[Dict[str, Any]], 
                       filename: str = None) -> str:
        """
        Exportă un Excel intern pentru verificare
        
        Args:
            products: Lista de produse procesate
            filename: Numele fișierului (opțional)
            
        Returns:
            Calea către fișierul exportat
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"verificare_produse_{timestamp}.xlsx"
        
        filepath = os.path.join(self.output_folder, filename)
        
        # Creează DataFrame intern
        df = self.create_internal_excel(products)
        
        # Exportă ca Excel cu formatare
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Produse')
            
            # Formatare automată
            worksheet = writer.sheets['Produse']
            
            # Auto-ajustează lățimea coloanelor
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        print(f"✅ Excel verificare salvat: {filepath}")
        return filepath
    
    def export_both(self, products: List[Dict[str, Any]]) -> tuple:
        """
        Exportă ambele formate (WooCommerce + Intern)
        
        Args:
            products: Lista de produse procesate
            
        Returns:
            Tuple (cale_woocommerce, cale_intern)
        """
        woo_path = self.export_woocommerce(products)
        internal_path = self.export_internal(products)
        
        return (woo_path, internal_path)