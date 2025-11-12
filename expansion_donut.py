#!/usr/bin/env python3
"""
EXPANSION_DONUT.PY - Enhanced Multi-Model Receipt Extraction Engine
Hybrid approach supporting multiple models with intelligent fallback
Integrates all SROIE fixes + advanced features
"""

import os
os.environ.update({'TF_ENABLE_ONEDNN_OPTS': '0', 'TF_CPP_MIN_LOG_LEVEL': '3', 'TRANSFORMERS_VERBOSITY': 'error'})

import sys
if getattr(sys, 'frozen', False):
    app_data = os.path.join(os.path.expanduser('~'), '.receipt-extractor')
    os.makedirs(app_data, exist_ok=True)
    os.environ.update({'TRANSFORMERS_CACHE': os.path.join(app_data, 'models'), 'HF_HOME': os.path.join(app_data, 'huggingface')})

import torch
import json
import re
import logging
import numpy as np
from transformers import (DonutProcessor, VisionEncoderDecoderModel,
                         AutoProcessor, AutoModelForCausalLM)
from PIL import Image, ImageEnhance, ImageFilter
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# ==================== ENHANCED CONFIGURATION ====================

# Quality thresholds
BRIGHTNESS_THRESHOLD = 100
CONTRAST_THRESHOLD = 40
PRICE_MIN = 0
PRICE_MAX = 9999
CONFIDENCE_WEIGHTS = {
    'items_per_item': 4.5,
    'items_max': 45,
    'store_name': 15,
    'total': 25,
    'coverage_perfect': 15,
    'coverage_good': 10,
    'date': 5,
    'tax': 3,
    'payment_method': 2
}

# Expanded model configurations with multiple options
MODEL_CONFIGS = {
    'sroie': {
        'name': 'philschmid/donut-base-sroie',
        'type': 'donut',
        'task_prompt': '<s_sroie>',
        'description': 'SROIE Donut - English receipts (4 fields: store, date, address, total)',
        'priority': 1
    },
    'florence2': {
        'name': 'microsoft/Florence-2-large',
        'type': 'florence',
        'task_prompt': '<OCR_WITH_REGION>',
        'description': 'Microsoft Florence-2 with OCR',
        'priority': 2
    },
    'cordv2': {
        'name': 'naver-clova-ix/donut-base-finetuned-cord-v2',
        'type': 'donut',
        'task_prompt': '<s_cord-v2>',
        'description': 'CORD-v2 Donut - Consolidated receipt dataset',
        'priority': 3
    },
    'docvqa': {
        'name': 'naver-clova-ix/donut-base-finetuned-docvqa',
        'type': 'donut',
        'task_prompt': '<s_docvqa><s_question>What is on this receipt?</s_question><s_answer>',
        'description': 'DocVQA Donut - Document visual question answering',
        'priority': 4
    }
}

# Receipt categories for classification
RECEIPT_CATEGORIES = {
    'grocery': ['grocery', 'supermarket', 'trader joe', 'whole foods', 'safeway', 'kroger', 'walmart'],
    'restaurant': ['restaurant', 'cafe', 'diner', 'bistro', 'grill', 'kitchen', 'pizza', 'burger'],
    'retail': ['store', 'shop', 'mall', 'outlet', 'boutique', 'mart'],
    'pharmacy': ['pharmacy', 'drug', 'cvs', 'walgreens', 'rite aid'],
    'gas': ['gas', 'fuel', 'shell', 'chevron', 'exxon', 'mobil', 'bp'],
    'hotel': ['hotel', 'inn', 'resort', 'motel', 'lodging'],
    'transport': ['taxi', 'uber', 'lyft', 'parking', 'toll', 'transit'],
    'other': []
}

# Payment method patterns
PAYMENT_PATTERNS = {
    'credit_card': [r'credit', r'visa', r'mastercard', r'amex', r'discover', r'\*\*\*\*\s*\d{4}'],
    'debit_card': [r'debit', r'pin'],
    'cash': [r'cash', r'currency', r'bills', r'coins'],
    'mobile': [r'apple\s*pay', r'google\s*pay', r'samsung\s*pay', r'paypal', r'venmo'],
    'check': [r'check', r'cheque', r'#\s*\d+'],
    'gift_card': [r'gift\s*card', r'store\s*credit']
}

# Tax patterns for enhanced extraction
TAX_PATTERNS = [
    r'(?:sales?\s*)?tax[\s:]*\$?\s*(\d+\.\d{2})',
    r'tax\s*amount[\s:]*\$?\s*(\d+\.\d{2})',
    r'vat[\s:]*\$?\s*(\d+\.\d{2})',
    r'gst[\s:]*\$?\s*(\d+\.\d{2})'
]

# ==================== DATA MODELS ====================

@dataclass
class LineItem:
    name: str
    quantity: int = 1
    unit_price: Optional[Decimal] = None
    total_price: Decimal = Decimal('0')
    category: Optional[str] = None  # NEW: Item category

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'quantity': self.quantity,
            'unit_price': str(self.unit_price) if self.unit_price else None,
            'total_price': str(self.total_price),
            'category': self.category
        }

@dataclass
class ReceiptData:
    store_name: Optional[str] = None
    store_address: Optional[str] = None
    store_phone: Optional[str] = None
    items: List[LineItem] = field(default_factory=list)
    subtotal: Optional[Decimal] = None
    tax: Optional[Decimal] = None  # NEW: Separate tax field
    total: Optional[Decimal] = None
    cash_tendered: Optional[Decimal] = None
    change_given: Optional[Decimal] = None
    transaction_date: Optional[str] = None
    payment_method: Optional[str] = None  # NEW: Payment method
    receipt_category: Optional[str] = None  # NEW: Receipt category
    model_used: str = "Donut"
    extraction_notes: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    language: str = "en"  # NEW: Language detection

    def to_dict(self) -> Dict:
        return {
            'store': {
                'name': self.store_name,
                'address': self.store_address,
                'phone': self.store_phone
            },
            'items': [item.to_dict() for item in self.items],
            'totals': {
                'subtotal': str(self.subtotal) if self.subtotal else None,
                'tax': str(self.tax) if self.tax else None,
                'total': str(self.total) if self.total else None,
                'cash': str(self.cash_tendered) if self.cash_tendered else None,
                'change': str(self.change_given) if self.change_given else None
            },
            'date': self.transaction_date,
            'payment_method': self.payment_method,
            'category': self.receipt_category,
            'item_count': len(self.items),
            'coverage': self._calculate_coverage(),
            'model': self.model_used,
            'notes': self.extraction_notes,
            'confidence': f"{self.confidence_score:.2f}",
            'language': self.language
        }

    def _calculate_coverage(self) -> str:
        if not self.total or not self.items:
            return "N/A"
        items_sum = sum(item.total_price for item in self.items)
        coverage = (items_sum / self.total * 100) if self.total > 0 else 0
        return f"{coverage:.1f}%"

# ==================== IMAGE PROCESSING ====================

class ImageProcessor:
    @staticmethod
    def enhance_image(image: Image.Image) -> List[tuple]:
        """Create multiple enhanced variants of the image"""
        variants = [('original', image.copy())]
        try:
            # Contrast enhancement
            variants.append(('contrast', ImageEnhance.Contrast(image).enhance(1.5)))
            # Sharpness
            variants.append(('sharp', image.filter(ImageFilter.SHARPEN)))
            # Brightness adjustment
            variants.append(('bright', ImageEnhance.Brightness(image).enhance(1.2)))
            # Combined enhancement
            enhanced = ImageEnhance.Contrast(image).enhance(1.5)
            enhanced = ImageEnhance.Sharpness(enhanced).enhance(1.3)
            variants.append(('combined', enhanced))
        except (OSError, ValueError) as e:
            logger.debug(f"Enhancement failed: {e}")
        return variants

    @staticmethod
    def analyze_quality(image: Image.Image) -> Dict:
        """Analyze image quality metrics"""
        try:
            img_array = np.array(image.convert('L'))
            brightness = float(np.mean(img_array))
            contrast = float(np.std(img_array))
            needs_enhancement = brightness < BRIGHTNESS_THRESHOLD or contrast < CONTRAST_THRESHOLD

            return {
                'brightness': brightness,
                'contrast': contrast,
                'needs_enhancement': needs_enhancement,
                'resolution': f"{image.width}x{image.height}",
                'aspect_ratio': round(image.width / image.height, 2)
            }
        except (ValueError, RuntimeError) as e:
            logger.warning(f"Quality analysis failed: {e}")
            return {'needs_enhancement': False}

# ==================== ENHANCED PARSER ====================

class ReceiptParser:
    SKIP_KEYWORDS = {'subtotal', 'total', 'cash', 'change', 'tax', 'payment', 'balance',
                     'thank', 'visit', 'welcome', 'receipt', 'cashier', 'card', 'approved'}

    @staticmethod
    def normalize_price(value) -> Optional[Decimal]:
        """Normalize price values to Decimal"""
        if value is None:
            return None
        try:
            price_str = str(value).replace('$', '').replace(',', '').strip()
            if price_str.startswith('-') or re.match(r'^\d{5}(-?\d{4})?$', price_str):
                return None
            val = Decimal(price_str)
            return val if PRICE_MIN <= val <= PRICE_MAX else None
        except (ValueError, ArithmeticError):
            return None

    @staticmethod
    def detect_payment_method(text: str) -> Optional[str]:
        """Detect payment method from receipt text"""
        text_lower = text.lower()
        for method, patterns in PAYMENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return method.replace('_', ' ').title()
        return None

    @staticmethod
    def classify_receipt(store_name: str, items: List[LineItem]) -> str:
        """Classify receipt into category"""
        if not store_name:
            return 'other'

        store_lower = store_name.lower()
        for category, keywords in RECEIPT_CATEGORIES.items():
            if any(kw in store_lower for kw in keywords):
                return category

        # Classify based on items if store name doesn't match
        if items:
            item_text = ' '.join([item.name.lower() for item in items[:5]])
            for category, keywords in RECEIPT_CATEGORIES.items():
                if category == 'other':
                    continue
                if any(kw in item_text for kw in keywords):
                    return category

        return 'other'

    @staticmethod
    def extract_tax(data: Dict, raw_text: str = '') -> Optional[Decimal]:
        """Extract tax amount from data or text"""
        # Try structured data first
        if isinstance(data, dict):
            tax_val = data.get('tax') or data.get('sales_tax') or data.get('vat')
            if tax_val:
                return ReceiptParser.normalize_price(tax_val)

        # Try patterns in raw text
        for pattern in TAX_PATTERNS:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                return ReceiptParser.normalize_price(match.group(1))

        return None

    @staticmethod
    def parse_json_output(json_str: str) -> Dict:
        """Parse JSON output with enhanced error handling"""
        try:
            json_str = json_str.strip()
            if json_str.startswith('```json'):
                json_str = json_str[7:]
            if json_str.endswith('```'):
                json_str = json_str[:-3]
            json_str = json_str.strip()
            return json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            try:
                match = re.search(r'\{.*\}', json_str, re.DOTALL)
                if match:
                    return json.loads(match.group(0))
            except (json.JSONDecodeError, ValueError) as e:
                logger.debug(f"Failed to extract JSON from text: {e}")
        return {}

    @staticmethod
    def parse_menu_items(data: Dict) -> List[LineItem]:
        """Parse items from various data structures"""
        items, seen_items = [], set()
        menu_data = (data.get('menu', []) or data.get('items', []) or
                    data.get('line_items', []) or data.get('products', []) or [])

        for item_data in menu_data:
            if isinstance(item_data, str):
                parts = item_data.split()
                if len(parts) >= 2:
                    try:
                        price_str = parts[-1].replace('$', '').replace(',', '')
                        price = Decimal(price_str)
                        name = ' '.join(parts[:-1])
                        item_data = {'name': name, 'price': str(price)}
                    except:
                        continue

            if not isinstance(item_data, dict):
                continue

            name = (item_data.get('nm') or item_data.get('name') or
                   item_data.get('description') or item_data.get('item_name') or
                   item_data.get('item') or item_data.get('product') or
                   str(item_data.get('text', '')))

            if not name or not isinstance(name, str):
                continue

            name = name.strip()
            name_lower = name.lower()

            if (len(name) < 2 or any(kw in name_lower for kw in ReceiptParser.SKIP_KEYWORDS) or
                name.startswith('*') or re.match(r'^\d+$', name)):
                continue

            quantity = item_data.get('cnt') or item_data.get('quantity') or item_data.get('qty') or item_data.get('count') or 1
            try:
                quantity = int(quantity)
            except:
                quantity = 1

            unit_price = ReceiptParser.normalize_price(item_data.get('unitprice') or item_data.get('unit_price'))
            total_price = ReceiptParser.normalize_price(
                item_data.get('price') or item_data.get('total') or
                item_data.get('total_price') or item_data.get('amount')
            )
            if total_price is None:
                total_price = Decimal('0')

            item_key = (name_lower, float(total_price))
            if item_key not in seen_items:
                seen_items.add(item_key)
                items.append(LineItem(name=name, quantity=quantity,
                                    unit_price=unit_price, total_price=total_price))

        return items

    @staticmethod
    def extract_store_info(data: Dict) -> Dict[str, Optional[str]]:
        """Extract store information"""
        store_info = {'name': None, 'address': None, 'phone': None}

        store_data = data.get('store', {})
        if isinstance(store_data, dict):
            raw_name = store_data.get('name') or store_data.get('company')
        else:
            raw_name = (data.get('store_name') or data.get('merchant') or
                       data.get('store') or data.get('company'))
        if raw_name:
            store_info['name'] = str(raw_name).strip()[:100]

        if isinstance(store_data, dict):
            raw_addr = store_data.get('address')
        else:
            raw_addr = data.get('address') or data.get('store_address') or data.get('store_addr')
        if raw_addr:
            store_info['address'] = str(raw_addr).strip()[:200]

        if isinstance(store_data, dict):
            raw_phone = store_data.get('phone')
        else:
            raw_phone = data.get('phone') or data.get('telephone') or data.get('tel')
        if raw_phone:
            store_info['phone'] = str(raw_phone).strip()[:20]

        return store_info

    @staticmethod
    def extract_totals(data: Dict) -> Dict[str, Optional[Decimal]]:
        """Extract all totals including tax"""
        totals_data = data.get('totals', {})
        if isinstance(totals_data, dict):
            return {
                'subtotal': ReceiptParser.normalize_price(totals_data.get('subtotal')),
                'tax': ReceiptParser.normalize_price(totals_data.get('tax')),
                'total': ReceiptParser.normalize_price(totals_data.get('total')),
                'cash': ReceiptParser.normalize_price(totals_data.get('cash')),
                'change': ReceiptParser.normalize_price(totals_data.get('change'))
            }

        return {
            'subtotal': ReceiptParser.normalize_price(
                data.get('subtotal') or data.get('sub_total') or data.get('subtotal_price')
            ),
            'tax': ReceiptParser.normalize_price(data.get('tax') or data.get('sales_tax')),
            'total': ReceiptParser.normalize_price(
                data.get('total') or data.get('total_price') or data.get('grand_total')
            ),
            'cash': ReceiptParser.normalize_price(data.get('cash') or data.get('cash_tendered')),
            'change': ReceiptParser.normalize_price(data.get('change') or data.get('change_due'))
        }

    @staticmethod
    def extract_date(data: Dict) -> Optional[str]:
        """Extract transaction date"""
        date_val = (data.get('date') or data.get('transaction_date') or
                   data.get('trans_date') or data.get('datetime'))
        return str(date_val).strip() if date_val else None

    @staticmethod
    def parse_florence_output(result: Dict) -> Dict:
        """Parse Florence-2 OCR output"""
        parsed_data = {'items': [], 'store': {}, 'totals': {}}
        ocr_text = result.get('<OCR_WITH_REGION>', {}).get('text', '')

        if not ocr_text:
            return parsed_data

        lines = ocr_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if 'total' in line.lower() and 'subtotal' not in line.lower():
                match = re.search(r'\$?(\d+\.\d{2})', line)
                if match:
                    parsed_data['totals']['total'] = match.group(1)
            elif 'subtotal' in line.lower():
                match = re.search(r'\$?(\d+\.\d{2})', line)
                if match:
                    parsed_data['totals']['subtotal'] = match.group(1)
            elif re.search(r'^[A-Z][A-Z\s]+$', line) and len(line) > 5:
                if not parsed_data['store'].get('name'):
                    parsed_data['store']['name'] = line
            else:
                match = re.match(r'^(.+?)\s+(\d+\.\d{2})$', line)
                if match:
                    name, price = match.groups()
                    parsed_data['items'].append({'name': name.strip(), 'price': price})

        return parsed_data

# ==================== HYBRID EXTRACTOR ====================

class HybridDonutExtractor:
    """Enhanced extractor with multi-model support and intelligent fallback"""

    def __init__(self, model_keys: List[str] = None, primary_model: str = 'sroie'):
        """
        Initialize with multiple models
        Args:
            model_keys: List of model keys to load (None = load primary only)
            primary_model: Primary model to use first
        """
        if model_keys is None:
            model_keys = [primary_model]

        self.models = {}
        self.primary_model = primary_model
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.parser = ReceiptParser()
        self.image_processor = ImageProcessor()

        print(f"🚀 Initializing Hybrid Receipt Extractor")
        print(f"   Device: {self.device}")
        print(f"   Primary Model: {primary_model}")
        print(f"   Models to load: {model_keys}\n")

        # Load models
        for key in model_keys:
            try:
                self._load_model(key)
            except Exception as e:
                logger.warning(f"Failed to load {key}: {e}")
                continue

        if not self.models:
            raise RuntimeError("No models loaded successfully!")

        print(f"\n✅ Loaded {len(self.models)} model(s) successfully\n")

    def _load_model(self, model_key: str):
        """Load a specific model"""
        if model_key not in MODEL_CONFIGS:
            raise ValueError(f"Unknown model: {model_key}")

        config = MODEL_CONFIGS[model_key]
        print(f"Loading {config['description']}...")

        try:
            if config['type'] == 'donut':
                processor = DonutProcessor.from_pretrained(config['name'])
                model = VisionEncoderDecoderModel.from_pretrained(config['name']).to(self.device)
                model.eval()
            elif config['type'] == 'florence':
                model = AutoModelForCausalLM.from_pretrained(
                    config['name'], trust_remote_code=True
                ).to(self.device)
                processor = AutoProcessor.from_pretrained(
                    config['name'], trust_remote_code=True
                )
                model.eval()
            else:
                raise ValueError(f"Unknown model type: {config['type']}")

            self.models[model_key] = {
                'model': model,
                'processor': processor,
                'config': config
            }
            print(f"   ✓ {model_key} loaded")

        except Exception as e:
            print(f"   ✗ {model_key} failed: {e}")
            raise

    def _run_inference(self, image: Image.Image, model_key: str, **kwargs) -> Union[Dict, str]:
        """Run inference on a specific model"""
        if model_key not in self.models:
            raise ValueError(f"Model {model_key} not loaded")

        model_data = self.models[model_key]
        model = model_data['model']
        processor = model_data['processor']
        config = model_data['config']

        if config['type'] == 'donut':
            pixel_values = processor(image, return_tensors="pt").pixel_values.to(self.device)
            decoder_input_ids = processor.tokenizer(
                config['task_prompt'],
                add_special_tokens=False,
                return_tensors="pt"
            ).input_ids.to(self.device)

            with torch.no_grad():
                outputs = model.generate(
                    pixel_values,
                    decoder_input_ids=decoder_input_ids,
                    max_length=model.decoder.config.max_position_embeddings,
                    pad_token_id=processor.tokenizer.pad_token_id,
                    eos_token_id=processor.tokenizer.eos_token_id,
                    use_cache=True,
                    bad_words_ids=[[processor.tokenizer.unk_token_id]],
                    return_dict_in_generate=True,
                    **kwargs
                )

            sequence = processor.batch_decode(outputs.sequences)[0]
            sequence = sequence.replace(processor.tokenizer.eos_token, "")
            sequence = sequence.replace(processor.tokenizer.pad_token, "")
            sequence = re.sub(r"<.*?>", "", sequence, count=1).strip()

            # Try token2json first (SROIE fix)
            try:
                result = processor.token2json(sequence)
                logger.debug(f"token2json result: {result}")
                return result
            except Exception as e:
                logger.debug(f"token2json failed: {e}, trying JSON parse")

            # Fallback to JSON parsing
            try:
                result = json.loads(sequence)
                return result
            except json.JSONDecodeError:
                return {'raw_text': sequence}

        elif config['type'] == 'florence':
            inputs = processor(text=config['task_prompt'], images=image, return_tensors="pt").to(self.device)
            with torch.no_grad():
                outputs = model.generate(**inputs, max_new_tokens=1024, do_sample=False)
            result = processor.batch_decode(outputs, skip_special_tokens=True)[0]
            parsed = processor.post_process_generation(
                result,
                task=config['task_prompt'],
                image_size=(image.width, image.height)
            )
            return self.parser.parse_florence_output(parsed)

    def extract_with_fallback(self, image_path: str, mode: str = 'fast') -> ReceiptData:
        """
        Extract with intelligent fallback across models
        """
        print(f"📄 Processing: {os.path.basename(image_path)}")
        image = Image.open(image_path).convert("RGB")

        # Analyze image quality
        quality = self.image_processor.analyze_quality(image)
        print(f"   📊 Image Quality: {quality.get('resolution')} | "
              f"Brightness: {quality.get('brightness', 0):.1f} | "
              f"Contrast: {quality.get('contrast', 0):.1f}")

        # Try models in priority order
        models_to_try = sorted(
            self.models.keys(),
            key=lambda k: MODEL_CONFIGS[k].get('priority', 999)
        )

        best_result = None
        best_confidence = 0

        for model_key in models_to_try:
            try:
                print(f"   🤖 Trying model: {model_key.upper()}")

                # Run inference
                if MODEL_CONFIGS[model_key]['type'] == 'donut':
                    if mode == 'quality':
                        raw_data = self._run_inference(
                            image, model_key,
                            num_beams=8,
                            length_penalty=1.8,
                            early_stopping=True
                        )
                    else:
                        raw_data = self._run_inference(
                            image, model_key,
                            num_beams=5,
                            length_penalty=1.5,
                            early_stopping=True
                        )
                else:
                    raw_data = self._run_inference(image, model_key)

                # Parse result
                receipt = self._parse_result(raw_data, model_key)
                receipt.model_used = model_key.upper()

                # Calculate confidence
                confidence = self._calculate_confidence(receipt)
                receipt.confidence_score = confidence

                print(f"      Items: {len(receipt.items)} | Confidence: {confidence:.1f}")

                # Update best result
                if confidence > best_confidence:
                    best_result = receipt
                    best_confidence = confidence

                # If we got great results, no need to try more models
                if confidence > 80 and len(receipt.items) > 3:
                    print(f"   ✅ Excellent results with {model_key}, stopping")
                    break

            except Exception as e:
                logger.warning(f"Model {model_key} failed: {e}")
                continue

        if best_result is None:
            raise RuntimeError("All models failed to extract data")

        # Add classification and payment detection
        best_result.receipt_category = self.parser.classify_receipt(
            best_result.store_name or '',
            best_result.items
        )

        print(f"\n   📊 Final Results:")
        print(f"      Model: {best_result.model_used}")
        print(f"      Store: {best_result.store_name or 'Unknown'}")
        print(f"      Items: {len(best_result.items)}")
        print(f"      Total: ${best_result.total or 0}")
        print(f"      Category: {best_result.receipt_category}")
        print(f"      Confidence: {best_result.confidence_score:.1f}\n")

        return best_result

    def _parse_result(self, raw_data: Dict, model_key: str) -> ReceiptData:
        """Parse raw model output into ReceiptData"""
        receipt = ReceiptData()

        # Handle SROIE format with enhanced parsing
        if 'company' in raw_data or 'date' in raw_data or 'address' in raw_data or model_key == 'sroie':
            receipt.store_name = raw_data.get('company', '').strip() if raw_data.get('company') else None
            receipt.store_address = raw_data.get('address', '').strip() if raw_data.get('address') else None
            receipt.transaction_date = raw_data.get('date', '').strip() if raw_data.get('date') else None
            receipt.total = self.parser.normalize_price(raw_data.get('total'))

            # Enhanced fallback parsing for SROIE
            if not any([receipt.store_name, receipt.store_address, receipt.transaction_date, receipt.total]):
                raw_text = raw_data.get('text_sequence') or raw_data.get('raw_text', '')
                if raw_text:
                    self._parse_sroie_text(receipt, raw_text)
        else:
            # Handle other formats
            receipt.items = self.parser.parse_menu_items(raw_data)
            store_info = self.parser.extract_store_info(raw_data)
            receipt.store_name = store_info['name']
            receipt.store_address = store_info['address']
            receipt.store_phone = store_info['phone']

            totals = self.parser.extract_totals(raw_data)
            receipt.subtotal = totals['subtotal']
            receipt.tax = totals['tax']
            receipt.total = totals['total']
            receipt.cash_tendered = totals['cash']
            receipt.change_given = totals['change']
            receipt.transaction_date = self.parser.extract_date(raw_data)

        # Enhance with payment method detection
        if raw_data:
            text_repr = json.dumps(raw_data, default=str)
            receipt.payment_method = self.parser.detect_payment_method(text_repr)

        # Add extraction notes
        if receipt.items:
            receipt.extraction_notes.append(f"Extracted {len(receipt.items)} items")
        if receipt.store_name:
            receipt.extraction_notes.append(f"Store: {receipt.store_name}")
        if receipt.total:
            receipt.extraction_notes.append(f"Total: ${receipt.total}")
        if receipt.payment_method:
            receipt.extraction_notes.append(f"Payment: {receipt.payment_method}")

        return receipt

    def _parse_sroie_text(self, receipt: ReceiptData, raw_text: str):
        """Enhanced SROIE text parsing with all fixes"""
        # Remove trailing tags
        raw_text = re.sub(r'</s_\w+>.*$', '', raw_text).strip()

        # Extract store name
        store_patterns = [
            r"^([A-Z][A-Z\s&']+?)(?:\s+\d+|\s+STORE|\s+SHOP|$)",
            r"^([A-Z][A-Za-z\s&']{3,30}?)(?:\s+\d+|\s+STORE|\s+SHOP)",
        ]

        for pattern in store_patterns:
            match = re.search(pattern, raw_text)
            if match:
                receipt.store_name = match.group(1).strip()
                break

        if not receipt.store_name:
            lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
            for line in lines[:3]:
                if not re.match(r'^\d', line) and 3 < len(line) < 50:
                    if sum(c.isalpha() or c.isspace() for c in line) / len(line) > 0.6:
                        receipt.store_name = line.split('\n')[0].split('  ')[0]
                        break

        # Extract address
        address_patterns = [
            r'(\d+\s+[A-Z][A-Z\s]+(?:AVE|AVENUE|ST|STREET|RD|ROAD|BLVD|DR|LN)[\s,]*[A-Z\s]*\d{5})',
            r'(\d+\s+[A-Z][A-Z\s]+(?:AVE|STREET|RD)[^\d\n]*(?:[A-Z]{2}\s+)?\d{5})',
        ]

        for pattern in address_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                receipt.store_address = match.group(1).strip()
                break

        # Extract phone
        phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', raw_text)
        if phone_match:
            receipt.store_phone = phone_match.group(0)

        # Extract tax
        receipt.tax = self.parser.extract_tax({}, raw_text)

        # Extract total
        total_patterns = [
            r'(?:total|amount|sum|balance|due)[\s:]*\$?\s*(\d+\.\d{2})',
            r'TOTAL[\s:]+(\d+\.\d{2})',
            r'(?:^|\n)TOTAL\s+(\d+\.\d{2})',
            r'\$\s*(\d+\.\d{2})\s*(?:total|TOTAL)?$'
        ]
        for pattern in total_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE | re.MULTILINE)
            if match:
                receipt.total = self.parser.normalize_price(match.group(1))
                break

        # Extract date
        date_patterns = [
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
            r'(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{2,4})'
        ]
        for pattern in date_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                receipt.transaction_date = match.group(1)
                break

        # Extract items
        lines = raw_text.split('\n')
        for line in lines:
            item_match = re.match(r'^([A-Z][A-Z\s\-]+?)\s+(\d+(?:\.\d{2})?)$', line.strip())
            if item_match:
                item_name = item_match.group(1).strip()
                price_str = item_match.group(2)
                if not any(skip in item_name.lower() for skip in ['subtotal', 'total', 'tax', 'change', 'cash']):
                    try:
                        price = Decimal(price_str)
                        if 0.01 <= price <= 999.99:
                            receipt.items.append(LineItem(name=item_name, total_price=price))
                    except:
                        pass

        # Detect payment method
        receipt.payment_method = self.parser.detect_payment_method(raw_text)

    def _calculate_confidence(self, receipt: ReceiptData) -> float:
        """Calculate confidence score with enhanced factors"""
        score = 0.0

        # SROIE-specific scoring
        if receipt.model_used.lower() == 'sroie':
            if receipt.store_name:
                score += 30
            if receipt.total:
                score += 30
            if receipt.store_address:
                score += 20
            if receipt.transaction_date:
                score += 20
            return min(100.0, score)

        # General scoring with items
        if receipt.items:
            score += min(CONFIDENCE_WEIGHTS['items_max'],
                        len(receipt.items) * CONFIDENCE_WEIGHTS['items_per_item'])
        if receipt.store_name:
            score += CONFIDENCE_WEIGHTS['store_name']
        if receipt.total:
            score += CONFIDENCE_WEIGHTS['total']
            try:
                coverage_str = receipt._calculate_coverage()
                if coverage_str != "N/A":
                    coverage = float(coverage_str.rstrip('%'))
                    if 95 <= coverage <= 105:
                        score += CONFIDENCE_WEIGHTS['coverage_perfect']
                    elif 85 <= coverage <= 115:
                        score += CONFIDENCE_WEIGHTS['coverage_good']
            except (ValueError, ArithmeticError):
                pass
        if receipt.transaction_date:
            score += CONFIDENCE_WEIGHTS['date']
        if receipt.tax:
            score += CONFIDENCE_WEIGHTS['tax']
        if receipt.payment_method:
            score += CONFIDENCE_WEIGHTS['payment_method']

        return min(100.0, score)

# ==================== CLI INTERFACE ====================

def main():
    if len(sys.argv) < 2:
        print("=" * 70)
        print("EXPANSION DONUT - Hybrid Multi-Model Receipt Extractor")
        print("=" * 70)
        print("\nUsage: python expansion_donut.py <image_path> [options]")
        print("\nOptions:")
        print("  --model MODEL       Primary model (sroie, florence2, cordv2, docvqa)")
        print("  --multi             Enable multi-model fallback")
        print("  --quality           Use quality mode (slower but better)")
        print("\nAvailable Models:")
        for key, config in MODEL_CONFIGS.items():
            print(f"  {key:12} - {config['description']}")
        print("\nExamples:")
        print("  python expansion_donut.py receipt.jpg")
        print("  python expansion_donut.py receipt.jpg --model florence2")
        print("  python expansion_donut.py receipt.jpg --multi --quality")
        print()
        sys.exit(1)

    image_path = sys.argv[1]
    primary_model = 'sroie'
    multi_model = False
    quality_mode = False

    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--model' and i + 1 < len(sys.argv):
            primary_model = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--multi':
            multi_model = True
            i += 1
        elif sys.argv[i] == '--quality':
            quality_mode = True
            i += 1
        else:
            i += 1

    if not os.path.exists(image_path):
        print(f"❌ Error: File not found: {image_path}")
        sys.exit(1)

    print("=" * 70)
    print(f"EXPANSION DONUT - HYBRID EXTRACTION")
    print("=" * 70 + "\n")

    try:
        # Initialize extractor
        models_to_load = list(MODEL_CONFIGS.keys()) if multi_model else [primary_model]
        extractor = HybridDonutExtractor(model_keys=models_to_load, primary_model=primary_model)

        # Extract
        mode = 'quality' if quality_mode else 'fast'
        receipt = extractor.extract_with_fallback(image_path, mode=mode)

        # Save results
        output = receipt.to_dict()
        model_suffix = 'hybrid' if multi_model else primary_model
        output_file = f"{os.path.splitext(image_path)[0]}_{model_suffix}.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)

        print("=" * 70)
        print("EXTRACTION COMPLETE")
        print("=" * 70)
        print(json.dumps(output, indent=2))
        print(f"\n💾 Saved to: {output_file}")

    except Exception as e:
        print(f"\n❌ Extraction failed: {e}")
        logger.exception("Full error:")
        sys.exit(1)

if __name__ == "__main__":
    main()
