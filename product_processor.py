# product_processor.py - Logica de procesare produse

import time
import json
import re
from typing import Dict, List, Any, Optional
import google.generativeai as genai
from config import *

class ProductProcessor:
    """Procesează produsele din JSON către format Excel WooCommerce"""
    
    def __init__(self, gemini_api_key: str, eur_ron_rate: float = DEFAULT_EUR_RON_RATE):
        """
        Inițializează procesorul
        
        Args:
            gemini_api_key: API key pentru Gemini AI
            eur_ron_rate: Cursul EUR/RON
        """
        self.eur_ron_rate = eur_ron_rate
        self.gemini_api_key = gemini_api_key
        
        # Configurare Gemini AI
        genai.configure(api_key=gemini_api_key)
        # Am mutat setările de siguranță direct în constructorul modelului
        # pentru a asigura aplicarea lor la toate apelurile.
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            }
        ]
        self.model = genai.GenerativeModel(GEMINI_MODEL, safety_settings=self.safety_settings)

        self.stats = {
            'total_products': 0,
            'processed_products': 0,
            'failed_products': 0,
            'ai_calls': 0
        }
    
    def load_json(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Încarcă și validează fișierul JSON
        
        Args:
            file_path: Calea către fișierul JSON
            
        Returns:
            Lista de produse
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Dacă e un singur produs, transformă în listă
        if isinstance(data, dict):
            data = [data]
        
        self.stats['total_products'] = len(data)
        return data
    
    def extract_max_price(self, price_str: str) -> float:
        """
        Extrage prețul maxim dintr-un string de preț
        
        Examples:
            "2,15 EUR" -> 2.15
            "1,84 EUR - 2,15 EUR" -> 2.15
            "1.84 - 2.15 EUR" -> 2.15
        
        Args:
            price_str: String cu prețul
            
        Returns:
            Prețul maxim ca float
        """
        # Înlocuiește virgula cu punct pentru conversie
        price_str = price_str.replace(',', '.')
        
        # Extrage toate numerele din string
        numbers = re.findall(r'\d+\.?\d*', price_str)
        
        if not numbers:
            return 0.0
        
        # Returnează maximul
        prices = [float(n) for n in numbers]
        return max(prices)
    
    def is_licensed_brand(self, brand: str) -> bool:
        """
        Verifică dacă brandul este un brand licențiat major
        
        Args:
            brand: Numele brandului
            
        Returns:
            True dacă e brand licențiat
        """
        if not brand:
            return False
        
        brand_lower = brand.lower()
        return any(licensed.lower() in brand_lower for licensed in LICENSED_BRANDS)
    
    def _enhance_batch_with_ai(self, products: List[Dict[str, Any]]) -> Optional[Dict[str, Dict[str, str]]]:
        """
        Procesează un batch de produse cu AI într-un singur apel

        Args:
            products: Lista de produse de procesat

        Returns:
            Dicționar cu cheia = article_number și valoarea = rezultatul AI pentru acel produs
            Returnează None dacă procesarea eșuează
        """
        if not products:
            return {}

        # Construim un prompt pentru toate produsele folosind template-ul din config
        products_data = []
        for product in products:
            products_data.append({
                "id": product.get('article_number', 'N/A'),
                "brand": product.get('brand', 'N/A'),
                "product_name": product.get('product_name', 'N/A'),
                "description": product.get('description', 'N/A'),
                "country_of_origin": product.get('country_of_origin', 'N/A')
            })

        # Folosim template-ul din config
        batch_prompt = AI_PROMPT_BATCH_TEMPLATE.format(
            product_list_json=json.dumps(products_data, ensure_ascii=False, indent=2)
        )

        print(f"🤖 Trimit batch de {len(products)} produse către AI...")

        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.stats['ai_calls'] += 1

                # Calculate tokens needed: ~1000 tokens per product for Romanian descriptions + overhead
                # Gemini 2.5 Flash supports up to 8192 output tokens
                tokens_per_product = 1000
                tokens_needed = len(products) * tokens_per_product
                max_tokens = min(tokens_needed + 2000, 8192)  # Add 2000 buffer, but cap at model limit

                print(f"   Tokens solicitați: {max_tokens} (estimat {tokens_per_product} per produs)")

                response = self.model.generate_content(
                    batch_prompt,
                    generation_config={
                        'temperature': GEMINI_TEMPERATURE,
                        'max_output_tokens': max_tokens
                        # NOTE: Removed 'response_mime_type': 'application/json' because it was causing malformed responses
                    }
                )

                if not response.parts:
                    finish_reason = response.candidates[0].finish_reason if response.candidates else "UNKNOWN"
                    block_reason = response.prompt_feedback.block_reason if response.prompt_feedback else "N/A"
                    raise ValueError(f"Response blocked. Finish reason: {finish_reason}, Block reason: {block_reason}")

                response_text = response.text.strip()

                # Remove markdown code blocks if present
                if response_text.startswith('```'):
                    response_text = re.sub(r'```json\s*|\s*```', '', response_text).strip()

                # Parse JSON
                try:
                    result = json.loads(response_text)
                except json.JSONDecodeError as json_err:
                    print(f"❌ Eroare decodare JSON batch. Motiv: {json_err}")
                    print(f"--- Răspuns AI (primele 1000 caractere) ---")
                    print(response_text[:1000])
                    print(f"--- Ultimele 500 caractere ---")
                    print(response_text[-500:])
                    print(f"-------------------------------------------")

                    # Check if response was cut off (incomplete JSON)
                    if "Expecting ',' delimiter" in str(json_err) or "Unterminated string" in str(json_err):
                        print(f"⚠️ Răspunsul AI pare tăiat (prea puține token-uri). Batch prea mare!")
                        print(f"   Recomandat: Reduceți batch_size la {len(products) // 2} produse")

                    raise ValueError(f"AI-ul a returnat JSON invalid. Eroare: {json_err}")

                # Validate structure
                if not isinstance(result, dict):
                    raise ValueError(f"AI a returnat {type(result).__name__} în loc de dict. Conținut: {str(result)[:200]}")

                # Validate each product result
                validated_results = {}
                for article_num, product_data in result.items():
                    if not isinstance(product_data, dict):
                        print(f"⚠️ Produsul '{article_num}' are date invalide (tip: {type(product_data).__name__}). Se va ignora.")
                        continue

                    # Check required fields
                    required_fields = ['title_ro', 'description_ro', 'short_description_ro', 'category', 'is_licensed_brand', 'tags_ro']
                    if all(field in product_data for field in required_fields):
                        validated_results[article_num] = product_data
                    else:
                        missing = [f for f in required_fields if f not in product_data]
                        print(f"⚠️ Produsul '{article_num}' lipsește câmpurile: {missing}. Se va ignora.")

                if not validated_results:
                    raise ValueError("Niciun produs valid în răspunsul AI")

                print(f"✅ Batch AI SUCCESS: {len(validated_results)}/{len(products)} produse procesate")
                return validated_results

            except Exception as e:
                print(f"❌ Eroare AI batch (încercarea {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    print(f"   Aștept {wait_time}s înainte de reîncercare...")
                    time.sleep(wait_time)
                else:
                    print(f"⚠️ Eșec final AI pentru batch după {max_retries} încercări.")
                    return None

        return None

    def enhance_with_ai(self, product: Dict[str, Any]) -> Dict[str, str]:
        """
        Folosește Gemini AI pentru a îmbunătăți produsul

        Args:
            product: Dicționar cu datele produsului

        Returns:
            Dicționar cu: title_ro, description_ro, category, is_licensed_brand
        """
        prompt = AI_PROMPT_TEMPLATE.format(
            brand=product.get('brand', 'N/A'),
            product_name=product.get('product_name', 'N/A'),
            description=product.get('description', 'N/A'),
            country_of_origin=product.get('country_of_origin', 'N/A')
        )

        print(f"🤖 Trimit 1 produs către AI: {product.get('article_number', 'N/A')}")

        # Mecanism de reîncercare
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.stats['ai_calls'] += 1

                response = self.model.generate_content(
                    prompt,
                    generation_config={
                        'temperature': GEMINI_TEMPERATURE,
                        'max_output_tokens': GEMINI_MAX_OUTPUT_TOKENS
                        # NOTE: Removed 'response_mime_type': 'application/json' because it was causing malformed responses
                    }
                )

                if not response.parts:
                    finish_reason = response.candidates[0].finish_reason if response.candidates else "UNKNOWN"
                    block_reason = response.prompt_feedback.block_reason if response.prompt_feedback else "N/A"
                    raise ValueError(f"Response blocked. Finish reason: {finish_reason}, Block reason: {block_reason}")

                response_text = response.text.strip()

                # Debug: Log what we received
                print(f"\n{'='*60}")
                print(f"📥 RAW AI RESPONSE pentru {product.get('article_number', 'N/A')}:")
                print(f"{'='*60}")
                print(response_text)
                print(f"{'='*60}\n")

                if response_text.startswith('```'):
                    print("🔧 Removing markdown code blocks...")
                    response_text = re.sub(r'```json\s*|\s*```', '', response_text).strip()

                print(f"📋 Cleaned response (first 300 chars): {response_text[:300]}")

                try:
                    result = json.loads(response_text)
                    print(f"✅ JSON parsed successfully. Type: {type(result).__name__}")
                    print(f"   Keys in result: {list(result.keys()) if isinstance(result, dict) else 'NOT A DICT'}")
                except json.JSONDecodeError as json_err:
                    print(f"❌ Eroare decodare JSON de la AI. Motiv: {json_err}")
                    print(f"--- JSON Primit (Invalid) ---\n{response_text[:500]}\n--------------------------")
                    raise ValueError(f"AI-ul a returnat JSON invalid. Eroare: {json_err}")

                # CRITICAL: Validate that result is a dictionary, not a string or other type
                if not isinstance(result, dict):
                    print(f"❌ AI a returnat {type(result).__name__} în loc de dicționar!")
                    print(f"--- Conținut primit ---\n{str(result)[:500]}\n--------------------------")
                    raise ValueError(f"AI a returnat tip invalid: {type(result).__name__}")

                # Validate required fields exist
                required_fields = ['title_ro', 'description_ro', 'short_description_ro', 'category', 'is_licensed_brand', 'tags_ro']
                missing_fields = [f for f in required_fields if f not in result]
                if missing_fields:
                    print(f"❌ Lipsesc câmpurile: {missing_fields}")
                    print(f"--- JSON primit ---\n{json.dumps(result, ensure_ascii=False, indent=2)[:500]}\n--------------------------")
                    raise ValueError(f"Lipsesc câmpurile obligatorii: {missing_fields}")

                # Validare și returnare
                return {
                    'title_ro': result.get('title_ro', product.get('product_name', 'Produs')),
                    'description_ro': result.get('description_ro', 'Descriere indisponibilă.'),
                    'short_description_ro': result.get('short_description_ro', 'Produs de calitate'),
                    'category': result.get('category', 'Casă & Grădină'),
                    'is_licensed_brand': result.get('is_licensed_brand', False),
                    'tags_ro': result.get('tags_ro', '')
                }

            except Exception as e:
                print(f"❌ Eroare AI (încercarea {attempt + 1}/{max_retries}) pentru {product.get('article_number', 'N/A')}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2)  # Așteaptă 2 secunde înainte de a reîncerca
                else:
                    # A eșuat și ultima încercare, folosim fallback
                    print(f"⚠️ Eșec final AI pentru {product.get('article_number', 'N/A')}. Se folosesc date de fallback.")
                    break # Ieși din bucla de reîncercări

        # Fallback dacă toate încercările AI eșuează
        category = "Branduri Licențiate" if self.is_licensed_brand(product.get('brand', '')) else "Casă & Grădină"
        brand = product.get('brand', 'N/A')
        tags = f"{brand}, B2B" if brand != 'N/A' else "B2B"

        # Return a complete dictionary to match the successful AI response structure
        return {
            'title_ro': product.get('product_name', 'Produs'),
            'description_ro': f"Produs {brand} de calitate. " + product.get('description', ''),
            'short_description_ro': f"Produs de calitate\nBrand: {brand}\nOrigine: {product.get('country_of_origin', 'N/A')}",
            'category': category,
            'is_licensed_brand': self.is_licensed_brand(brand),
            'tags_ro': tags # Ensure this key is present
        }
    
    def _calculate_prices(self, price_eur_piece: float, pieces_per_box: int, 
                        category: str) -> Dict[str, float]:
        """
        Calculează toate prețurile pentru un produs
        
        Args:
            price_eur_piece: Prețul în EUR per bucată
            pieces_per_box: Număr bucăți per cutie
            category: Categoria produsului
            
        Returns:
            Dicționar cu toate prețurile calculate
        """
        # Preț EUR cutie
        price_eur_box = price_eur_piece * pieces_per_box
        
        # Conversie în LEI
        price_lei_piece = price_eur_piece * self.eur_ron_rate
        price_lei_box = price_eur_box * self.eur_ron_rate
        
        # TVA
        vat_rate = CATEGORY_VAT_MAPPING.get(category, 19) / 100
        price_lei_piece_vat = price_lei_piece * (1 + vat_rate)
        price_lei_box_vat = price_lei_box * (1 + vat_rate)
        
        # Marjă
        margin_percent = CATEGORY_MARGINS.get(category, 30) / 100
        price_final_piece = price_lei_piece_vat * (1 + margin_percent)
        price_final_box = price_lei_box_vat * (1 + margin_percent)
        
        return {
            'price_eur_piece': round(price_eur_piece, 2),
            'price_eur_box': round(price_eur_box, 2),
            'price_lei_piece': round(price_lei_piece, 2),
            'price_lei_box': round(price_lei_box, 2),
            'vat_rate': int(vat_rate * 100),
            'price_lei_piece_vat': round(price_lei_piece_vat, 2),
            'price_lei_box_vat': round(price_lei_box_vat, 2),
            'margin_percent': int(margin_percent * 100),
            'price_final_piece': round(price_final_piece, 2),
            'price_final_box': round(price_final_box, 2)
        }
    
    def process_product(self, product: Dict[str, Any], use_ai: bool = True,
                        default_category: str = None, preloaded_ai_result: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
        """
        Procesează un singur produs complet

        Args:
            product: Date produs din JSON
            use_ai: Dacă să folosească AI pentru enhancement
            default_category: Categoria prestabilită (dacă e setată, AI nu mai alege categoria)
            preloaded_ai_result: Rezultat AI pre-încărcat (pentru procesare batch)

        Returns:
            Produs procesat cu toate câmpurile
        """
        try:
            # 1. Extrage prețul maxim
            price_str = product.get('price', '0')
            price_eur_piece = self.extract_max_price(price_str)

            # 2. Bucăți per cutie - handle empty or invalid values
            pieces_per_box_raw = product.get('piece_per_pu', '1')
            if not pieces_per_box_raw or pieces_per_box_raw == '':
                pieces_per_box = 1
            else:
                try:
                    pieces_per_box = int(pieces_per_box_raw)
                    if pieces_per_box == 0:
                        pieces_per_box = 1
                except (ValueError, TypeError):
                    pieces_per_box = 1

            # 3. AI Enhancement (opțional)
            if preloaded_ai_result:
                # Use preloaded AI result from batch processing
                ai_result = preloaded_ai_result
            elif use_ai:
                # Make an individual AI call
                ai_result = self.enhance_with_ai(product)
            else:
                # No AI - use defaults
                category = default_category if default_category else ("Branduri Licențiate" if self.is_licensed_brand(product.get('brand', '')) else "Casă & Grădină")
                ai_result = {
                    'title_ro': product.get('product_name', 'Produs'),
                    'description_ro': product.get('description', 'Descriere indisponibilă.'),
                    'short_description_ro': f"Produs de calitate\nBrand: {product.get('brand', 'N/A')}\nOrigine: {product.get('country_of_origin', 'N/A')}",
                    'category': category,
                    'is_licensed_brand': self.is_licensed_brand(product.get('brand', '')),
                    'tags_ro': f"{product.get('brand', 'N/A')}, B2B"
                }

            # CRITICAL: Validate ai_result is a dictionary before using it
            if not isinstance(ai_result, dict):
                print(f"🚨 EROARE CRITICĂ: ai_result este {type(ai_result).__name__}, nu dict!")
                print(f"   Conținut: {str(ai_result)[:200]}")
                print(f"   Se folosește fallback...")
                # Force fallback
                category = default_category if default_category else ("Branduri Licențiate" if self.is_licensed_brand(product.get('brand', '')) else "Casă & Grădină")
                brand = product.get('brand', 'N/A')
                ai_result = {
                    'title_ro': product.get('product_name', 'Produs'),
                    'description_ro': f"Produs {brand} de calitate. " + product.get('description', ''),
                    'short_description_ro': f"Produs de calitate\nBrand: {brand}\nOrigine: {product.get('country_of_origin', 'N/A')}",
                    'category': category,
                    'is_licensed_brand': self.is_licensed_brand(brand),
                    'tags_ro': f"{brand}, B2B" if brand != 'N/A' else "B2B"
                }

            # Suprascrie categoria dacă este setată una implicită
            if default_category and isinstance(ai_result, dict):
                ai_result['category'] = default_category

            # 4. Calculează prețurile
            prices = self._calculate_prices(price_eur_piece, pieces_per_box, ai_result.get('category', 'Casă & Grădină'))
            
            # 5. Pregătește imaginile - convert toate la 600x600
            images = product.get('images', [])
            if isinstance(images, list):
                # Convertește toate imaginile la 600x600
                high_res_images = []
                for img in images:
                    # Înlocuiește w=210&h=210 cu w=600&h=600
                    high_res_img = img.replace('w=210&h=210', 'w=600&h=600')
                    high_res_images.append(high_res_img)

                # Separator cu virgulă pentru WooCommerce
                images_str = ', '.join(high_res_images)
            else:
                images_str = str(images)
            
            # 6. Construiește produsul procesat
            processed = {
                'article_number': product.get('article_number', ''),
                'ean': product.get('ean_sku', ''),
                'sku': product.get('article_number', ''),  # WooCommerce SKU
                'name': ai_result.get('title_ro', product.get('product_name', 'N/A')),
                'description': ai_result.get('description_ro', product.get('description', '')),
                'short_description': ai_result.get('short_description_ro', ''),
                'category': ai_result.get('category', 'Casă & Grădină'),
                'brand': product.get('brand', ''),
                'country_of_origin': product.get('country_of_origin', ''),
                'pieces_per_box': pieces_per_box,
                'images': images_str,
                'zentrada_url': product.get('url', ''),
                'mix_order': product.get('mix_order', False),
                'min_order_qty': product.get('min_order_quantity', 1),
                'is_licensed_brand': ai_result.get('is_licensed_brand', False),
                'tags': ai_result.get('tags_ro', ''),
                **prices  # Adaugă toate prețurile
            }
            
            self.stats['processed_products'] += 1
            return processed
            
        except Exception as e:
            print(f"❌ Eroare procesare produs {product.get('article_number', 'N/A')}: {str(e)}")
            self.stats['failed_products'] += 1
            return None
    
    def process_batch(self, products: List[Dict[str, Any]], use_ai: bool = True, default_category: str = None, progress_callback=None, batch_size_api: int = 15) -> List[Dict[str, Any]]:
        """
        Procesează un batch de produse

        Args:
            products: Lista de produse de procesat
            use_ai: Dacă să folosească AI
            default_category: Categoria prestabilită pentru toate produsele
            progress_callback: Funcție callback pentru a raporta progresul
            batch_size_api: Dimensiunea lotului pentru apelurile API către AI

        Returns:
            Lista de produse procesate
        """
        processed_products = []
        total_to_process = len(products)
        self.stats['total_products'] = total_to_process

        # Batch AI processing enabled - processes multiple products per AI call
        # NOTE: Now works even with default_category (just overrides the AI's category choice)
        if use_ai:
            print(f"📦 Mod BATCH activat: procesez în loturi de {batch_size_api} produse")
            if default_category:
                print(f"   Categoria prestabilită: {default_category}")

            # Process in batches
            for batch_start in range(0, total_to_process, batch_size_api):
                batch_end = min(batch_start + batch_size_api, total_to_process)
                product_batch = products[batch_start:batch_end]

                current_progress = len(processed_products)
                if progress_callback:
                    progress_callback(
                        current_progress,
                        total_to_process,
                        f"🤖 Procesez lot {batch_start+1}-{batch_end} din {total_to_process}..."
                    )

                # Try batch AI processing first
                ai_results = self._enhance_batch_with_ai(product_batch)

                if ai_results:
                    # Batch processing succeeded
                    print(f"✅ Lot {batch_start+1}-{batch_end}: {len(ai_results)} rezultate de la AI")

                    for product in product_batch:
                        article_number = product.get('article_number', '')
                        ai_result = ai_results.get(article_number)

                        if ai_result:
                            # Validate ai_result is a dictionary before using it
                            if not isinstance(ai_result, dict):
                                print(f"⚠️ Produs {article_number}: rezultat AI invalid (tip: {type(ai_result).__name__}). Procesez individual...")
                                print(f"   Conținut invalid: {str(ai_result)[:200]}")
                                # Fallback to individual processing
                                processed = self.process_product(product, use_ai=True, default_category=default_category)
                            else:
                                # Use preloaded AI result
                                processed = self.process_product(
                                    product,
                                    use_ai=True,
                                    default_category=default_category,
                                    preloaded_ai_result=ai_result
                                )
                            if processed:
                                processed_products.append(processed)
                        else:
                            # Article number not found in AI results - fallback to individual
                            print(f"⚠️ Produsul {article_number} lipsește din răspunsul AI. Procesez individual...")
                            processed = self.process_product(product, use_ai=True, default_category=default_category)
                            if processed:
                                processed_products.append(processed)
                else:
                    # Batch processing failed - fallback to individual processing
                    print(f"🔄 Lot {batch_start+1}-{batch_end}: Batch EȘUAT, procesez individual...")
                    for i, product in enumerate(product_batch, start=1):
                        article_number = product.get('article_number', 'N/A')
                        if progress_callback:
                            progress_callback(
                                batch_start + i,
                                total_to_process,
                                f"📦 Individual {batch_start + i}/{total_to_process}: {article_number}"
                            )

                        processed = self.process_product(product, use_ai=True, default_category=default_category)
                        if processed:
                            processed_products.append(processed)
        else:
            # Individual processing (no AI or with default category)
            print(f"📦 Mod INDIVIDUAL: procesez unul câte unul")
            for i, product in enumerate(products, 1):
                article_number = product.get('article_number', 'N/A')
                if progress_callback:
                    progress_callback(i, total_to_process, f"📦 Procesez {i}/{total_to_process}: {article_number}")

                processed = self.process_product(product, use_ai, default_category)
                if processed:
                    processed_products.append(processed)

        return processed_products
    
    def get_stats(self) -> Dict[str, int]:
        """Returnează statisticile de procesare"""
        return self.stats.copy()