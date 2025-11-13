"""
Tesseract OCR processor for receipt extraction
"""
import os
import sys
import re
import logging
import time
import subprocess
from decimal import Decimal
from typing import Dict, List, Optional
from PIL import Image
import cv2
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.data_structures import LineItem, ReceiptData, ExtractionResult
from utils.image_processing import load_and_validate_image, preprocess_for_ocr

try:
    import pytesseract
except ImportError:
    raise ImportError("pytesseract is required for OCR processing. Install: pip install pytesseract")

logger = logging.getLogger(__name__)

# Price validation
PRICE_MIN = 0
PRICE_MAX = 9999


class OCRProcessor:
    """Processor for Tesseract OCR-based extraction"""

    SKIP_KEYWORDS = {
        'subtotal', 'total', 'cash', 'change', 'tax', 'payment', 'balance',
        'thank', 'visit', 'welcome', 'receipt', 'cashier', 'card', 'debit',
        'credit', 'approved', 'transaction'
    }

    def __init__(self, model_config: Dict):
        self.model_config = model_config
        self.model_name = model_config['name']
        self.tesseract_path = self._find_tesseract()

        if self.tesseract_path and self.tesseract_path != 'tesseract':
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
            logger.info(f"Using Tesseract at: {self.tesseract_path}")
        else:
            logger.info("Using Tesseract from system PATH")

    def _find_tesseract(self) -> Optional[str]:
        """Find Tesseract installation"""
        logger.info("Searching for Tesseract OCR...")

        windows_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            r'C:\Users\User\AppData\Local\Programs\Tesseract-OCR\tesseract.exe',
            r'C:\Tesseract-OCR\tesseract.exe',
        ]

        if sys.platform == 'win32':
            for path in windows_paths:
                if os.path.exists(path):
                    logger.info(f"Found Tesseract: {path}")
                    return path

        # Try system PATH
        try:
            result = subprocess.run(
                ['tesseract', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info("Found Tesseract in system PATH")
                return 'tesseract'
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        logger.warning("Tesseract not found. Please install from: https://github.com/UB-Mannheim/tesseract/wiki")
        return None

    def extract(self, image_path: str) -> ExtractionResult:
        """Extract receipt data using Tesseract OCR"""
        start_time = time.time()

        try:
            # Load and preprocess image
            image = load_and_validate_image(image_path)
            processed_image = preprocess_for_ocr(image)

            # Perform OCR with better configuration
            # Using config to improve accuracy
            custom_config = r'--oem 3 --psm 6'  # OEM 3 = Default, PSM 6 = Assume uniform block of text
            text = pytesseract.image_to_string(processed_image, lang='eng', config=custom_config)
            logger.info("OCR extraction complete")
            logger.info(f"Extracted text length: {len(text)} characters")

            # Parse the OCR text
            receipt = self._parse_receipt_text(text)
            receipt.processing_time = time.time() - start_time
            receipt.model_used = self.model_name

            return ExtractionResult(success=True, data=receipt)

        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return ExtractionResult(success=False, error=str(e))

    def _parse_receipt_text(self, text: str) -> ReceiptData:
        """Parse OCR text to extract receipt information"""
        receipt = ReceiptData()
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        if not lines:
            receipt.extraction_notes.append("No text detected")
            return receipt

        # Extract store name (typically first meaningful line with at least 2 characters)
        # Skip very short lines that are likely OCR artifacts
        receipt.store_name = None
        for line in lines[:5]:  # Check first 5 lines
            # Skip single characters and common OCR artifacts
            if len(line) >= 2 and not line.isdigit() and line not in ['D', 'I', 'O', 'l', '1', '|']:
                receipt.store_name = line
                logger.info(f"Found store name: {line}")
                break

        if not receipt.store_name:
            # If no meaningful store name found, still try the first line
            receipt.store_name = lines[0] if lines else None
            if receipt.store_name and len(receipt.store_name) < 2:
                receipt.extraction_notes.append(f"Store name very short: '{receipt.store_name}' - possible OCR error")

        # Extract date
        date_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        for line in lines:
            date_match = re.search(date_pattern, line)
            if date_match:
                receipt.transaction_date = date_match.group(1)
                break

        # Extract total
        total_patterns = [
            r'total[:\s]*\$?(\d+\.\d{2})',
            r'amount[:\s]*\$?(\d+\.\d{2})',
            r'balance[:\s]*\$?(\d+\.\d{2})'
        ]
        for pattern in total_patterns:
            for line in lines:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    total_val = self._normalize_price(match.group(1))
                    if total_val:
                        receipt.total = total_val
                        break
            if receipt.total:
                break

        # Extract line items
        receipt.items = self._extract_line_items(lines)

        # Extract address (lines with numbers and street keywords)
        address_keywords = ['st', 'ave', 'rd', 'blvd', 'lane', 'drive', 'street', 'avenue']
        for line in lines[1:6]:  # Check first few lines
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in address_keywords) and any(char.isdigit() for char in line):
                receipt.store_address = line
                break

        # Extract phone number
        phone_pattern = r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'
        for line in lines:
            phone_match = re.search(phone_pattern, line)
            if phone_match:
                receipt.store_phone = phone_match.group(1)
                break

        return receipt

    def _extract_line_items(self, lines: List[str]) -> List[LineItem]:
        """Extract line items from OCR text"""
        items = []
        seen_names = set()

        # Pattern to match: text followed by price
        # e.g., "Product Name 12.99" or "Product Name $12.99"
        item_price_pattern = r'^(.+?)\s+\$?(\d+\.\d{2})$'

        for line in lines:
            # Skip header/footer lines
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in self.SKIP_KEYWORDS):
                continue

            # Try to match item with price
            match = re.search(item_price_pattern, line)
            if match:
                name = match.group(1).strip()
                price_str = match.group(2)

                # Validate name
                if len(name) < 2 or name in seen_names:
                    continue

                # Validate price
                price = self._normalize_price(price_str)
                if not price:
                    continue

                # Add item
                items.append(LineItem(
                    name=name,
                    total_price=price
                ))
                seen_names.add(name)

        logger.info(f"Extracted {len(items)} line items")
        return items

    @staticmethod
    def _normalize_price(value) -> Optional[Decimal]:
        """Normalize price values"""
        if value is None:
            return None
        try:
            price_str = str(value).replace('$', '').replace(',', '').strip()
            if price_str.startswith('-'):
                return None
            val = Decimal(price_str)
            return val if PRICE_MIN <= val <= PRICE_MAX else None
        except (ValueError, ArithmeticError):
            return None
