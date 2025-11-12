import os
import sys
import json
import re
import subprocess
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from decimal import Decimal

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Constants
PRICE_MIN = 0
PRICE_MAX = 9999

try:
    import pytesseract
    from PIL import Image
    import cv2
    import numpy as np
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Install: pip install pytesseract pillow opencv-python")
    print("Download Tesseract: https://github.com/UB-Mannheim/tesseract/wiki")
    sys.exit(1)

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

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
    extraction_notes: List[str] = field(default_factory=list)
    
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
            'notes': self.extraction_notes
        }
    
    def _calculate_coverage(self) -> str:
        if not self.total or not self.items: return "N/A"
        items_sum = sum(item.total_price for item in self.items)
        coverage = (items_sum / self.total * 100) if self.total > 0 else 0
        return f"{coverage:.1f}%"

def find_tesseract() -> Optional[str]:
    print("Searching for Tesseract OCR...")
    windows_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        r'C:\Users\User\AppData\Local\Programs\Tesseract-OCR\tesseract.exe',
        r'C:\Tesseract-OCR\tesseract.exe',
        r'D:\Program Files\Tesseract-OCR\tesseract.exe',
    ]
    
    if sys.platform == 'win32':
        for path in windows_paths:
            if os.path.exists(path):
                print(f"Found: {path}\n")
                return path
    
    try:
        result = subprocess.run(['tesseract', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("Found in system PATH\n")
            return 'tesseract'
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        logger.debug(f"Tesseract not in PATH: {e}")

    print("Tesseract not found! Download: https://github.com/UB-Mannheim/tesseract/wiki\n")
    return None

class TesseractExtractor:
    STORE_PATTERNS = [r"trader\s*joe[''']?s", r"whole\s*foods", r"walmart", r"target", r"costco", 
                      r"safeway", r"kroger", r"publix", r"albertsons", r"cvs", r"walgreens", r"aldi", r"food\s*lion"]
    SKIP_KEYWORDS = {'subtotal', 'total', 'cash', 'change', 'tax', 'payment', 'balance', 'visa', 'mastercard',
                     'debit', 'credit', 'approved', 'transaction', 'thank', 'visit', 'welcome', 'cashier', 'receipt'}
    
    def __init__(self):
        print("Initializing Tesseract OCR...")
        if sys.platform == 'win32':
            tesseract_path = find_tesseract()
            if not tesseract_path:
                print("Cannot continue without Tesseract")
                sys.exit(1)
            if tesseract_path != 'tesseract':
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        try:
            version = pytesseract.get_tesseract_version()
            print(f"Tesseract {version} ready\n")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    def preprocess_image(self, image_path: str) -> Image.Image:
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        denoised = cv2.fastNlMeansDenoising(enhanced)
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return Image.fromarray(binary)
    
    def extract_text(self, image_path: str) -> List[str]:
        print(f"Reading: {os.path.basename(image_path)}")
        if not os.path.exists(image_path):
            print("   File not found")
            return []
        
        lines = []
        try:
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img, config='--psm 6')
            lines.extend([line.strip() for line in text.split('\n') if line.strip()])
            processed = self.preprocess_image(image_path)
            text2 = pytesseract.image_to_string(processed, config='--psm 6')
            lines.extend([line.strip() for line in text2.split('\n') if line.strip()])
        except Exception as e:
            print(f"   OCR failed: {e}")
            return []
        
        unique_lines = list(dict.fromkeys(lines))
        print(f"   Extracted {len(unique_lines)} text lines\n")
        return unique_lines
    
    def normalize_price(self, value: str) -> Optional[Decimal]:
        try:
            price_str = value.replace('$', '').replace(',', '').strip()
            if price_str.startswith('-'):
                return None
            # Common OCR misreads
            price_str = (price_str.replace('O', '0').replace('o', '0')
                        .replace('l', '1').replace('I', '1')
                        .replace('S', '5').replace('s', '5'))
            val = Decimal(price_str)
            return val if PRICE_MIN <= val <= PRICE_MAX else None
        except (ValueError, ArithmeticError):
            return None
    
    def extract_store_name(self, lines: List[str]) -> Optional[str]:
        for text in lines[:15]:
            for pattern in self.STORE_PATTERNS:
                match = re.search(pattern, text, re.IGNORECASE)
                if match: return match.group(0).strip().title()
        return None
    
    def parse_line_item(self, text: str) -> Optional[Dict]:
        text_lower = text.lower()
        if any(kw in text_lower for kw in self.SKIP_KEYWORDS) or len(text.strip()) < 3: return None
        
        patterns = [
            (r'^(.+?)\s+(\d+\.\d{2})$', False),
            (r'^(.+?)\s+\$(\d+\.\d{2})$', True),
            (r'^(.+?)\s{2,}(\d+\.\d{2})$', False)
        ]
        
        for pattern, has_dollar in patterns:
            match = re.match(pattern, text.strip())
            if match:
                name, price = match.groups()
                price_val = self.normalize_price(price)
                if price_val and price_val > 0:
                    return {'name': name.strip(), 'price': price_val}
        return None
    
    def extract_totals(self, lines: List[str]) -> Dict[str, Optional[Decimal]]:
        totals = {'subtotal': None, 'total': None, 'cash': None, 'change': None}
        for text in lines:
            text_upper = text.upper()
            if 'SUBTOTAL' in text_upper:
                match = re.search(r'\$?(\d+\.\d{2})', text)
                if match: totals['subtotal'] = self.normalize_price(match.group(1))
            if 'TOTAL' in text_upper and 'SUBTOTAL' not in text_upper:
                match = re.search(r'\$?(\d+\.\d{2})', text)
                if match: totals['total'] = self.normalize_price(match.group(1))
            if 'CASH' in text_upper or 'TENDERED' in text_upper:
                match = re.search(r'\$?(\d+\.\d{2})', text)
                if match: totals['cash'] = self.normalize_price(match.group(1))
            if 'CHANGE' in text_upper:
                match = re.search(r'\$?(\d+\.\d{2})', text)
                if match: totals['change'] = self.normalize_price(match.group(1))
        return totals
    
    def extract_date(self, lines: List[str]) -> Optional[str]:
        date_patterns = [r'\d{1,2}/\d{1,2}/\d{2,4}', r'\d{1,2}-\d{1,2}-\d{2,4}', r'\d{4}-\d{2}-\d{2}']
        for text in lines[:20]:
            for pattern in date_patterns:
                match = re.search(pattern, text)
                if match: return match.group(0)
        return None
    
    def extract_receipt(self, image_path: str) -> ReceiptData:
        receipt = ReceiptData()
        lines = self.extract_text(image_path)
        receipt.extraction_notes.append(f"Extracted {len(lines)} text lines")
        
        if not lines:
            receipt.extraction_notes.append("No text found")
            return receipt
        
        receipt.store_name = self.extract_store_name(lines)
        if receipt.store_name: receipt.extraction_notes.append(f"Store: {receipt.store_name}")
        
        seen_items = set()
        for text in lines:
            item = self.parse_line_item(text)
            if item:
                item_key = (item['name'].lower(), float(item['price']))
                if item_key not in seen_items:
                    seen_items.add(item_key)
                    receipt.items.append(LineItem(name=item['name'], total_price=item['price']))
        
        receipt.extraction_notes.append(f"Found {len(receipt.items)} items")
        totals = self.extract_totals(lines)
        receipt.subtotal, receipt.total = totals['subtotal'], totals['total']
        receipt.cash_tendered, receipt.change_given = totals['cash'], totals['change']
        receipt.transaction_date = self.extract_date(lines)
        
        if receipt.items and receipt.total:
            items_sum = sum(item.total_price for item in receipt.items)
            coverage = (items_sum / receipt.total * 100) if receipt.total > 0 else 0
            receipt.extraction_notes.append(f"Coverage: {coverage:.1f}%")
        
        print("Extraction complete")
        print(f"   Items: {len(receipt.items)}")
        if receipt.total: print(f"   Total: ${receipt.total}")
        print()
        return receipt

def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_ocr.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    print("=" * 60)
    print("RECEIPT EXTRACTOR - OCR (TESSERACT)")
    print("=" * 60 + "\n")
    
    try:
        extractor = TesseractExtractor()
        receipt = extractor.extract_receipt(image_path)
        
        print("=" * 60)
        print("RESULTS")
        print("=" * 60)
        output = receipt.to_dict()
        print(json.dumps(output, indent=2))
        
        output_file = f"{os.path.splitext(image_path)[0]}_ocr.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)
        
        print(f"\nSaved to: {output_file}")
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
