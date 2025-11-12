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
                         PaliGemmaForConditionalGeneration, AutoProcessor,
                         AutoModelForCausalLM)
from PIL import Image, ImageEnhance, ImageFilter
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, field
from decimal import Decimal

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

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
    'date': 5
}

MODEL_CONFIGS = {
    'sroie': {
        'name': 'philschmid/donut-base-sroie',
        'type': 'donut',
        'task_prompt': '<s_sroie>',
        'description': 'SROIE Donut - English receipts (4 fields: store, date, address, total)'
    },
    'florence2': {
        'name': 'microsoft/Florence-2-large',
        'type': 'florence',
        'task_prompt': '<OCR_WITH_REGION>',
        'description': 'Microsoft Florence-2 with OCR'
    }
}

@dataclass
class LineItem:
    name: str
    quantity: int = 1
    unit_price: Optional[Decimal] = None
    total_price: Decimal = Decimal('0')
    
    def to_dict(self) -> Dict:
        return {'name': self.name, 'quantity': self.quantity,
                'unit_price': str(self.unit_price) if self.unit_price else None,
                'total_price': str(self.total_price)}

@dataclass
class ReceiptData:
    store_name: Optional[str] = None
    store_address: Optional[str] = None
    store_phone: Optional[str] = None
    items: List[LineItem] = field(default_factory=list)
    subtotal: Optional[Decimal] = None
    total: Optional[Decimal] = None
    cash_tendered: Optional[Decimal] = None
    change_given: Optional[Decimal] = None
    transaction_date: Optional[str] = None
    model_used: str = "Donut"
    extraction_notes: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'store': {'name': self.store_name, 'address': self.store_address, 'phone': self.store_phone},
            'items': [item.to_dict() for item in self.items],
            'totals': {
                'subtotal': str(self.subtotal) if self.subtotal else None,
                'total': str(self.total) if self.total else None,
                'cash': str(self.cash_tendered) if self.cash_tendered else None,
                'change': str(self.change_given) if self.change_given else None
            },
            'date': self.transaction_date,
            'item_count': len(self.items),
            'coverage': self._calculate_coverage(),
            'model': self.model_used,
            'notes': self.extraction_notes,
            'confidence': f"{self.confidence_score:.2f}"
        }
    
    def _calculate_coverage(self) -> str:
        if not self.total or not self.items:
            return "N/A"
        items_sum = sum(item.total_price for item in self.items)
        coverage = (items_sum / self.total * 100) if self.total > 0 else 0
        return f"{coverage:.1f}%"

class ImageProcessor:
    @staticmethod
    def enhance_image(image: Image.Image) -> List[tuple]:
        variants = [('original', image.copy())]
        try:
            variants.append(('contrast', ImageEnhance.Contrast(image).enhance(1.5)))
        except (OSError, ValueError) as e:
            logger.debug(f"Contrast enhancement failed: {e}")
        try:
            variants.append(('sharp', image.filter(ImageFilter.SHARPEN)))
        except (OSError, ValueError) as e:
            logger.debug(f"Sharpening failed: {e}")
        return variants

    @staticmethod
    def analyze_quality(image: Image.Image) -> Dict:
        try:
            img_array = np.array(image.convert('L'))
            brightness, contrast = float(np.mean(img_array)), float(np.std(img_array))
            needs_enhancement = brightness < BRIGHTNESS_THRESHOLD or contrast < CONTRAST_THRESHOLD
            return {'brightness': brightness, 'contrast': contrast, 'needs_enhancement': needs_enhancement}
        except (ValueError, RuntimeError) as e:
            logger.warning(f"Quality analysis failed: {e}")
            return {'needs_enhancement': False}

class ReceiptParser:
    SKIP_KEYWORDS = {'subtotal', 'total', 'cash', 'change', 'tax', 'payment', 'balance', 
                     'thank', 'visit', 'welcome', 'receipt', 'cashier', 'card'}
    
    @staticmethod
    def normalize_price(value) -> Optional[Decimal]:
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
    def parse_json_output(json_str: str) -> Dict:
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
        items, seen_items = [], set()
        menu_data = data.get('menu', []) or data.get('items', []) or data.get('line_items', []) or data.get('products', []) or []
        
        for item_data in menu_data:
            if isinstance(item_data, str):
                parts = item_data.split()
                if len(parts) >= 2:
                    try:
                        price_str = parts[-1].replace('$', '').replace(',', '')
                        price = Decimal(price_str)
                        name = ' '.join(parts[:-1])
                        item_data = {'name': name, 'price': str(price)}
                    except: continue
            
            if not isinstance(item_data, dict): continue
            name = (item_data.get('nm') or item_data.get('name') or item_data.get('description') or 
                   item_data.get('item_name') or item_data.get('item') or item_data.get('product') or str(item_data.get('text', '')))
            if not name or not isinstance(name, str): continue
            
            name, name_lower = name.strip(), name.lower()
            if (len(name) < 2 or any(kw in name_lower for kw in ReceiptParser.SKIP_KEYWORDS) or 
                name.startswith('*') or re.match(r'^\d+$', name)): continue
            
            quantity = item_data.get('cnt') or item_data.get('quantity') or item_data.get('qty') or item_data.get('count') or 1
            try: quantity = int(quantity)
            except: quantity = 1
            
            unit_price = ReceiptParser.normalize_price(item_data.get('unitprice') or item_data.get('unit_price'))
            total_price = ReceiptParser.normalize_price(item_data.get('price') or item_data.get('total') or 
                                                        item_data.get('total_price') or item_data.get('amount'))
            if total_price is None: total_price = Decimal('0')
            
            item_key = (name_lower, float(total_price))
            if item_key not in seen_items:
                seen_items.add(item_key)
                items.append(LineItem(name=name, quantity=quantity, unit_price=unit_price, total_price=total_price))
        return items
    
    @staticmethod
    def extract_store_info(data: Dict) -> Dict[str, Optional[str]]:
        store_info = {'name': None, 'address': None, 'phone': None}
        
        store_data = data.get('store', {})
        if isinstance(store_data, dict):
            raw_name = store_data.get('name') or store_data.get('company')
        else:
            raw_name = data.get('store_name') or data.get('merchant') or data.get('store') or data.get('company')
        if raw_name: store_info['name'] = str(raw_name).strip()[:100]
        
        if isinstance(store_data, dict):
            raw_addr = store_data.get('address')
        else:
            raw_addr = data.get('address') or data.get('store_address') or data.get('store_addr')
        if raw_addr: store_info['address'] = str(raw_addr).strip()[:200]
        
        if isinstance(store_data, dict):
            raw_phone = store_data.get('phone')
        else:
            raw_phone = data.get('phone') or data.get('telephone') or data.get('tel')
        if raw_phone: store_info['phone'] = str(raw_phone).strip()[:20]
        
        return store_info
    
    @staticmethod
    def extract_totals(data: Dict) -> Dict[str, Optional[Decimal]]:
        totals_data = data.get('totals', {})
        if isinstance(totals_data, dict):
            return {
                'subtotal': ReceiptParser.normalize_price(totals_data.get('subtotal')),
                'total': ReceiptParser.normalize_price(totals_data.get('total')),
                'cash': ReceiptParser.normalize_price(totals_data.get('cash')),
                'change': ReceiptParser.normalize_price(totals_data.get('change'))
            }
        return {
            'subtotal': ReceiptParser.normalize_price(data.get('subtotal') or data.get('sub_total') or data.get('subtotal_price')),
            'total': ReceiptParser.normalize_price(data.get('total') or data.get('total_price') or data.get('grand_total')),
            'cash': ReceiptParser.normalize_price(data.get('cash') or data.get('cash_tendered')),
            'change': ReceiptParser.normalize_price(data.get('change') or data.get('change_due'))
        }
    
    @staticmethod
    def extract_date(data: Dict) -> Optional[str]:
        date_val = data.get('date') or data.get('transaction_date') or data.get('trans_date') or data.get('datetime')
        return str(date_val).strip() if date_val else None
    
    @staticmethod
    def parse_florence_output(result: Dict) -> Dict:
        parsed_data = {'items': [], 'store': {}, 'totals': {}}
        ocr_text = result.get('<OCR_WITH_REGION>', {}).get('text', '')
        
        if not ocr_text:
            return parsed_data
        
        lines = ocr_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line: continue
            
            if 'total' in line.lower() and not 'subtotal' in line.lower():
                match = re.search(r'\$?(\d+\.\d{2})', line)
                if match: parsed_data['totals']['total'] = match.group(1)
            elif 'subtotal' in line.lower():
                match = re.search(r'\$?(\d+\.\d{2})', line)
                if match: parsed_data['totals']['subtotal'] = match.group(1)
            elif re.search(r'^[A-Z][A-Z\s]+$', line) and len(line) > 5:
                if not parsed_data['store'].get('name'):
                    parsed_data['store']['name'] = line
            else:
                match = re.match(r'^(.+?)\s+(\d+\.\d{2})$', line)
                if match:
                    name, price = match.groups()
                    parsed_data['items'].append({'name': name.strip(), 'price': price})
        
        return parsed_data

class DonutExtractor:
    def __init__(self, model_key: str = 'adamcodd'):
        if model_key not in MODEL_CONFIGS:
            raise ValueError(f"Unknown model: {model_key}. Choose from: {list(MODEL_CONFIGS.keys())}")

        self.model_key = model_key
        self.config = MODEL_CONFIGS[model_key]
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.parser = ReceiptParser()
        self.image_processor = ImageProcessor()

        print(f"Loading {self.config['description']}...")
        print(f"Model: {self.config['name']}")
        print("This may take 2-5 minutes on first run (downloading ~1GB model)...")
        print("Please wait...\n")

        try:
            if self.config['type'] == 'donut':
                print("Downloading processor...")
                self.processor = DonutProcessor.from_pretrained(self.config['name'], resume_download=None)
                print("Downloading model...")
                self.model = VisionEncoderDecoderModel.from_pretrained(self.config['name'], resume_download=None).to(self.device)
                self.model.eval()
            elif self.config['type'] == 'paligemma':
                print("Downloading model...")
                self.model = PaliGemmaForConditionalGeneration.from_pretrained(self.config['name'], resume_download=None).to(self.device)
                print("Downloading processor...")
                self.processor = AutoProcessor.from_pretrained(self.config['name'], resume_download=None)
                self.model.eval()
            elif self.config['type'] == 'florence':
                print("Downloading model...")
                self.model = AutoModelForCausalLM.from_pretrained(self.config['name'], trust_remote_code=True, resume_download=None).to(self.device)
                print("Downloading processor...")
                self.processor = AutoProcessor.from_pretrained(self.config['name'], trust_remote_code=True, resume_download=None)
                self.model.eval()

            print(f"\nÃ¢Å“â€œ Model loaded successfully!")
            print(f"Ã¢Å“â€œ Running on: {self.device}")
            print(f"Ã¢Å“â€œ Ready to extract receipts\n")
        except Exception as e:
            error_msg = str(e).lower()
            print(f"\n{'='*60}")
            print("ERROR: Cannot Access AI Model")
            print(f"{'='*60}\n")
            print(f"Model: {self.config['name']}")
            print(f"Error: {e}\n")

            if model_key == 'paligemma':
                print("PALIGEMMA MODEL ACCESS ISSUE")
                print("-" * 60)
                print("This model requires:")
                print("1. Accept Gemma license at: https://huggingface.co/google/gemma-2b")
                print("2. The specific model may not exist or is private")
                print("\nTo fix:")
                print("  Ã¢â‚¬Â¢ Visit https://huggingface.co/google/gemma-2b and accept license")
                print("  Ã¢â‚¬Â¢ Login with: huggingface-cli login")
                print("  Ã¢â‚¬Â¢ Or try SROIE model: --model sroie")
                print("  Ã¢â‚¬Â¢ Or try Florence-2 model: --model florence2\n")

            elif model_key == 'adamcodd':
                print("ADAMCODD MODEL ACCESS ISSUE")
                print("-" * 60)
                print("This model requires access approval.")
                print("\nTo fix:")
                print("  1. Visit: https://huggingface.co/AdamCodd/donut-receipts-extract")
                print("  2. Request access from the model owner")
                print("  3. Login with: huggingface-cli login")
                print("\nAlternatives:")
                print("  Ã¢â‚¬Â¢ SROIE model (public): --model sroie")
                print("  Ã¢â‚¬Â¢ Florence-2 (Microsoft): --model florence2\n")

            elif 'http' in error_msg or '401' in error_msg or '403' in error_msg:
                print("AUTHENTICATION ISSUE")
                print("-" * 60)
                print("You need to authenticate with Hugging Face.")
                print("\nTo fix:")
                print("  1. Get token from: https://huggingface.co/settings/tokens")
                print("  2. Run: huggingface-cli login")
                print("  3. Or set HF_TOKEN environment variable\n")

            else:
                print("MODEL LOADING FAILED")
                print("-" * 60)
                print("Possible issues:")
                print("  Ã¢â‚¬Â¢ Model requires authentication")
                print("  Ã¢â‚¬Â¢ Model doesn't exist or was removed")
                print("  Ã¢â‚¬Â¢ Network connectivity issues")
                print("  Ã¢â‚¬Â¢ Insufficient disk space for model cache")
                print("\nRecommended alternatives (no auth required):")
                print("  Ã¢â‚¬Â¢ SROIE: --model sroie")
                print("  Ã¢â‚¬Â¢ Florence-2: --model florence2\n")

            print(f"{'='*60}\n")
            raise
    
    def _run_inference(self, image: Image.Image, **kwargs) -> Union[Dict, str]:
        if self.config['type'] == 'donut':
            pixel_values = self.processor(image, return_tensors="pt").pixel_values.to(self.device)
            decoder_input_ids = self.processor.tokenizer(self.config['task_prompt'], add_special_tokens=False, return_tensors="pt").input_ids.to(self.device)
            
            with torch.no_grad():
                outputs = self.model.generate(pixel_values, decoder_input_ids=decoder_input_ids,
                                             max_length=self.model.decoder.config.max_position_embeddings,
                                             pad_token_id=self.processor.tokenizer.pad_token_id,
                                             eos_token_id=self.processor.tokenizer.eos_token_id,
                                             use_cache=True, bad_words_ids=[[self.processor.tokenizer.unk_token_id]],
                                             return_dict_in_generate=True, **kwargs)
            
            sequence = self.processor.batch_decode(outputs.sequences)[0]
            sequence = sequence.replace(self.processor.tokenizer.eos_token, "").replace(self.processor.tokenizer.pad_token, "")
            sequence = re.sub(r"<.*?>", "", sequence, count=1).strip()

            # Try token2json first (handles SROIE format better)
            try:
                result = self.processor.token2json(sequence)
                logger.debug(f"token2json result: {result}")
                return result
            except Exception as e:
                logger.debug(f"token2json failed: {e}, trying JSON parse")
            
            # Fallback to JSON parsing
            try:
                result = json.loads(sequence)
                return result
            except json.JSONDecodeError as e:
                logger.debug(f"JSON decode error: {e}")
                # Return the raw sequence wrapped so we can debug
                return {'raw_text': sequence}
        
        elif self.config['type'] == 'paligemma':
            inputs = self.processor(text=self.config['task_prompt'], images=image, return_tensors="pt").to(self.device)
            with torch.no_grad():
                outputs = self.model.generate(**inputs, max_new_tokens=512, do_sample=False)
            result = self.processor.decode(outputs[0], skip_special_tokens=True)
            return self.parser.parse_json_output(result)
        
        elif self.config['type'] == 'florence':
            inputs = self.processor(text=self.config['task_prompt'], images=image, return_tensors="pt").to(self.device)
            with torch.no_grad():
                outputs = self.model.generate(**inputs, max_new_tokens=1024, do_sample=False)
            result = self.processor.batch_decode(outputs, skip_special_tokens=True)[0]
            parsed = self.processor.post_process_generation(result, task=self.config['task_prompt'], 
                                                           image_size=(image.width, image.height))
            return self.parser.parse_florence_output(parsed)
    
    def extract_fast(self, image_path: str) -> ReceiptData:
        print(f"Processing: {os.path.basename(image_path)}")
        image = Image.open(image_path).convert("RGB")
        print("   Strategy: Fast")
        print("   Running AI model inference...")

        if self.config['type'] == 'donut':
            raw_data = self._run_inference(image, num_beams=5, length_penalty=1.5, early_stopping=True)
        else:
            raw_data = self._run_inference(image)

        print(f"   Raw extraction result: {raw_data}")

        receipt = self._parse_result(raw_data)
        receipt.model_used = self.model_key.upper()
        receipt.confidence_score = self._calculate_confidence(receipt)

        # Check if we extracted any meaningful data
        has_data = any([
            len(receipt.items) > 0,
            receipt.store_name,
            receipt.store_address,
            receipt.store_phone,
            receipt.total,
            receipt.transaction_date
        ])
        
        if not has_data:
            print(f"   Ã¢Å¡Â  WARNING: No data extracted from image")
            print(f"   This could mean:")
            print(f"     - Image quality is too low")
            print(f"     - Receipt text is not visible")
            print(f"     - Wrong model for this receipt type")
            print(f"   Try: --model florence2 for better results")

        print(f"Extracted {len(receipt.items)} items (confidence: {receipt.confidence_score:.0f})\n")
        return receipt
    
    def extract_quality(self, image_path: str) -> Dict:
        print(f"Processing: {os.path.basename(image_path)}")
        print("   Mode: Quality\n")
        image = Image.open(image_path).convert("RGB")
        
        if self.config['type'] == 'donut':
            strategies = [
                {'name': 'Fast', 'num_beams': 3, 'length_penalty': 1.2},
                {'name': 'Balanced', 'num_beams': 5, 'length_penalty': 1.5},
                {'name': 'Thorough', 'num_beams': 8, 'length_penalty': 1.8},
            ]
        else:
            strategies = [{'name': 'Standard', 'params': {}}]
        
        results = []
        for strategy in strategies:
            print(f"Testing: {strategy['name']}")
            try:
                if self.config['type'] == 'donut':
                    raw_data = self._run_inference(image, early_stopping=True, **{k: v for k, v in strategy.items() if k != 'name'})
                else:
                    raw_data = self._run_inference(image)
                
                receipt = self._parse_result(raw_data)
                receipt.model_used = self.model_key.upper()
                confidence = self._calculate_confidence(receipt)
                receipt.confidence_score = confidence
                results.append({'strategy': strategy['name'], 'receipt': receipt.to_dict(),
                              'item_count': len(receipt.items), 'confidence': confidence, 'success': len(receipt.items) > 0})
                print(f"   {len(receipt.items)} items (confidence: {confidence:.0f})")
            except Exception as e:
                print(f"   Failed: {str(e)}")
                results.append({'strategy': strategy['name'], 'success': False, 'error': str(e)})
        
        successful = [r for r in results if r.get('success', False)]
        if successful:
            best = max(successful, key=lambda r: (r['confidence'] * 10 + r['item_count'] * 15))
            print(f"\nBest result: {best['strategy']} ({best['item_count']} items, confidence: {best['confidence']:.0f})\n")
        else:
            best = max(results, key=lambda r: r.get('item_count', 0))
        return {'best_result': best, 'all_results': results}
    
    def _parse_result(self, raw_data: Dict) -> ReceiptData:
        receipt = ReceiptData()
        
        # Handle SROIE format (company, date, address, total)
        if 'company' in raw_data or 'date' in raw_data or 'address' in raw_data or self.model_key == 'sroie':
            receipt.store_name = raw_data.get('company', '').strip() if raw_data.get('company') else None
            receipt.store_address = raw_data.get('address', '').strip() if raw_data.get('address') else None
            receipt.transaction_date = raw_data.get('date', '').strip() if raw_data.get('date') else None
            receipt.total = self.parser.normalize_price(raw_data.get('total'))
            
            # If we got text_sequence or raw_text but no structured fields, try to parse it
            if not any([receipt.store_name, receipt.store_address, receipt.transaction_date, receipt.total]):
                raw_text = raw_data.get('text_sequence') or raw_data.get('raw_text', '')
                if raw_text:
                    logger.info(f"Parsing unstructured text from SROIE model: {raw_text[:100]}...")
                    
                    # Remove trailing tags
                    raw_text = re.sub(r'</s_\w+>.*$', '', raw_text).strip()
                    
                    # Extract store name - look for business name patterns at the start
                    # Store names are typically: short, uppercase/title case, no numbers at start
                    store_patterns = [
                        r"^([A-Z][A-Z\s&']+?)(?:\s+\d+|\s+STORE|\s+SHOP|$)",  # TRADER JOE'S, WALMART, etc.
                        r"^([A-Z][A-Za-z\s&']{3,30}?)(?:\s+\d+|\s+STORE|\s+SHOP)",  # Mixed case
                    ]
                    
                    for pattern in store_patterns:
                        match = re.search(pattern, raw_text)
                        if match:
                            receipt.store_name = match.group(1).strip()
                            break
                    
                    # If no match, try first meaningful line
                    if not receipt.store_name:
                        lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
                        for line in lines[:3]:
                            # Skip if starts with number or has lots of numbers
                            if not re.match(r'^\d', line) and len(line) > 3 and len(line) < 50:
                                # Check if it's mostly letters
                                if sum(c.isalpha() or c.isspace() for c in line) / len(line) > 0.6:
                                    receipt.store_name = line.split('\n')[0].split('  ')[0]
                                    break
                    
                    # Extract address (line with street number and name)
                    address_patterns = [
                        r'(\d+\s+[A-Z][A-Z\s]+(?:AVE|AVENUE|ST|STREET|RD|ROAD|BLVD|BOULEVARD|DR|DRIVE|LN|LANE)[\s,]*[A-Z\s]*\d{5})',
                        r'(\d+\s+[A-Z][A-Z\s]+(?:AVE|AVENUE|ST|STREET|RD|ROAD)[^\d\n]*(?:[A-Z]{2}\s+)?\d{5})',
                    ]
                    
                    for pattern in address_patterns:
                        address_match = re.search(pattern, raw_text, re.IGNORECASE)
                        if address_match:
                            receipt.store_address = address_match.group(1).strip()
                            break
                    
                    # Extract phone
                    phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', raw_text)
                    if phone_match:
                        receipt.store_phone = phone_match.group(0)
                    
                    # Try to find total with various patterns
                    total_patterns = [
                        r'(?:total|amount|sum|balance|due)[\s:]*\$?\s*(\d+\.\d{2})',
                        r'TOTAL[\s:]+(\d+\.\d{2})',
                        r'(?:^|\n)TOTAL\s+(\d+\.\d{2})',
                        r'\$\s*(\d+\.\d{2})\s*(?:total|TOTAL)?$'
                    ]
                    for pattern in total_patterns:
                        total_match = re.search(pattern, raw_text, re.IGNORECASE | re.MULTILINE)
                        if total_match:
                            receipt.total = self.parser.normalize_price(total_match.group(1))
                            break
                    
                    # Try to find date
                    date_patterns = [
                        r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                        r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
                        r'(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{2,4})'
                    ]
                    for pattern in date_patterns:
                        date_match = re.search(pattern, raw_text, re.IGNORECASE)
                        if date_match:
                            receipt.transaction_date = date_match.group(1)
                            break
                    
                    # Extract items from the text (basic parsing for SROIE)
                    item_lines = []
                    lines = raw_text.split('\n')
                    for line in lines:
                        # Look for lines with item name and price pattern
                        # Example: "R-CARROTS SHREDDED 10 OZ 1.29"
                        item_match = re.match(r'^([A-Z][A-Z\s\-]+?)\s+(\d+(?:\.\d{2})?)$', line.strip())
                        if item_match:
                            item_name = item_match.group(1).strip()
                            price_str = item_match.group(2)
                            # Skip common non-items
                            if not any(skip in item_name.lower() for skip in ['subtotal', 'total', 'tax', 'change', 'cash']):
                                try:
                                    price = Decimal(price_str)
                                    if 0.01 <= price <= 999.99:
                                        receipt.items.append(LineItem(name=item_name, total_price=price))
                                except:
                                    pass
        else:
            # Handle other formats
            receipt.items = self.parser.parse_menu_items(raw_data)
            store_info = self.parser.extract_store_info(raw_data)
            receipt.store_name, receipt.store_address, receipt.store_phone = store_info['name'], store_info['address'], store_info['phone']
            totals = self.parser.extract_totals(raw_data)
            receipt.subtotal, receipt.total = totals['subtotal'], totals['total']
            receipt.cash_tendered, receipt.change_given = totals['cash'], totals['change']
            receipt.transaction_date = self.parser.extract_date(raw_data)
        
        if receipt.items: receipt.extraction_notes.append(f"Extracted {len(receipt.items)} items")
        if receipt.store_name: receipt.extraction_notes.append(f"Store: {receipt.store_name}")
        if receipt.total: receipt.extraction_notes.append(f"Total: ${receipt.total}")
        return receipt
    
    def _calculate_confidence(self, receipt: ReceiptData) -> float:
        score = 0.0

        # For models like SROIE that only extract basic fields (no items)
        if self.model_key == 'sroie':
            if receipt.store_name:
                score += 30
            if receipt.total:
                score += 30
            if receipt.store_address:
                score += 20
            if receipt.transaction_date:
                score += 20
            return min(100.0, score)

        # For models with item extraction
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
        return min(100.0, score)

def check_huggingface_auth():
    """Check if Hugging Face authentication is set up."""
    hf_token = os.environ.get('HF_TOKEN') or os.environ.get('HUGGING_FACE_HUB_TOKEN')
    hf_home = os.environ.get('HF_HOME', os.path.join(os.path.expanduser('~'), '.cache', 'huggingface'))
    token_path = os.path.join(hf_home, 'token')

    return hf_token is not None or os.path.exists(token_path)

def print_model_info():
    """Print information about available models."""
    print("\nAVAILABLE MODELS:")
    print("-" * 60)
    for key, config in MODEL_CONFIGS.items():
        print(f"  {key:12} - {config['description']}")
    print()

def main():
    if len(sys.argv) < 2:
        print("=" * 60)
        print("RECEIPT EXTRACTOR - AI-Powered Receipt Data Extraction")
        print("=" * 60)
        print("\nUsage: python extract_donut.py <image_path> [--model MODEL] [--quality]")
        print_model_info()
        print("\nEXAMPLES:")
        print("  python extract_donut.py receipt.jpg")
        print("  python extract_donut.py receipt.jpg --model sroie")
        print("  python extract_donut.py receipt.jpg --model florence2 --quality")
        print("\nAll models are public and work without authentication.")
        print()
        sys.exit(1)

    image_path = sys.argv[1]
    model_key = 'sroie'  # Default to public Donut model
    quality_mode = False

    for i in range(2, len(sys.argv)):
        if sys.argv[i] == '--model' and i + 1 < len(sys.argv):
            model_key = sys.argv[i + 1]
        elif sys.argv[i] == '--quality':
            quality_mode = True

    if not os.path.exists(image_path):
        print(f"Error: File not found: {image_path}")
        sys.exit(1)

    print("=" * 60)
    print(f"RECEIPT EXTRACTOR - {model_key.upper()}")
    print("=" * 60 + "\n")

    try:
        extractor = DonutExtractor(model_key)
        if quality_mode:
            result = extractor.extract_quality(image_path)
            output = result['best_result']['receipt']
            output_file = f"{os.path.splitext(image_path)[0]}_{model_key}_quality.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2)
        else:
            receipt = extractor.extract_fast(image_path)
            output = receipt.to_dict()
            output_file = f"{os.path.splitext(image_path)[0]}_{model_key}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2)

        print("=" * 60)
        print("RESULTS")
        print("=" * 60)
        print(json.dumps(output, indent=2))
        print(f"\nSaved to: {output_file}")
        print("\nExtraction complete")
    except Exception as e:
        print(f"\nFailed to complete extraction.")
        print("\nTROUBLESHOOTING:")
        print("-" * 60)
        print("1. Try a different model:")
        print(f"   python extract_donut.py {image_path} --model sroie")
        print(f"   python extract_donut.py {image_path} --model florence2")
        print("\n2. Check image quality and format (JPG, PNG supported)")
        print("\n3. For error details, see message above")
        print()
        sys.exit(1)

if __name__ == "__main__":
    main()
