"""
EasyOCR processor for receipt extraction
EasyOCR is a ready-to-use OCR with 80+ supported languages
"""
import os
import sys
import re
import logging
import time
from decimal import Decimal
from typing import Dict, List, Optional
from PIL import Image

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.data_structures import LineItem, ReceiptData, ExtractionResult
from utils.image_processing import load_and_validate_image

try:
    import easyocr
except ImportError:
    easyocr = None

logger = logging.getLogger(__name__)

# Price validation
PRICE_MIN = 0
PRICE_MAX = 9999


class EasyOCRProcessor:
    """Processor for EasyOCR-based extraction"""

    SKIP_KEYWORDS = {
        'subtotal', 'total', 'cash', 'change', 'tax', 'payment', 'balance',
        'thank', 'visit', 'welcome', 'receipt', 'cashier', 'card', 'debit',
        'credit', 'approved', 'transaction'
    }

    def __init__(self, model_config: Dict):
        self.model_config = model_config
        self.model_name = model_config['name']
        self.reader = None

        if easyocr is None:
            logger.warning("EasyOCR not installed. Install with: pip install easyocr")
        else:
            try:
                # Initialize EasyOCR reader (downloads model on first run)
                logger.info("Initializing EasyOCR reader...")
                self.reader = easyocr.Reader(['en'], gpu=False)
                logger.info("EasyOCR reader initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize EasyOCR: {e}")
                self.reader = None

    def extract(self, image_path: str) -> ExtractionResult:
        """Extract receipt data using EasyOCR"""
        start_time = time.time()

        # Check if EasyOCR is available
        if easyocr is None:
            error_msg = (
                "EasyOCR is not installed. "
                "Please install EasyOCR: pip install easyocr"
            )
            logger.error(error_msg)
            return ExtractionResult(success=False, error=error_msg)

        if self.reader is None:
            error_msg = "EasyOCR reader failed to initialize"
            logger.error(error_msg)
            return ExtractionResult(success=False, error=error_msg)

        try:
            # Load and validate image
            image = load_and_validate_image(image_path)

            # Perform OCR
            logger.info("Running EasyOCR...")
            results = self.reader.readtext(image_path)

            # Extract text from results
            text_lines = [detection[1] for detection in results]
            text = '\n'.join(text_lines)

            logger.info("EasyOCR extraction complete")
            logger.info(f"Extracted {len(text_lines)} text lines")

            # Parse the OCR text
            receipt = self._parse_receipt_text(text, text_lines)
            receipt.processing_time = time.time() - start_time
            receipt.model_used = self.model_name

            return ExtractionResult(success=True, data=receipt)

        except Exception as e:
            logger.error(f"EasyOCR extraction failed: {e}")
            return ExtractionResult(success=False, error=str(e))

    def _parse_receipt_text(self, text: str, text_lines: List[str]) -> ReceiptData:
        """Parse OCR text to extract receipt information"""
        receipt = ReceiptData()
        lines = [line.strip() for line in text_lines if line.strip()]

        if not lines:
            receipt.extraction_notes.append("No text detected")
            return receipt

        # Extract store name (first meaningful line)
        receipt.store_name = None
        for line in lines[:5]:
            if len(line) >= 2 and not line.isdigit():
                receipt.store_name = line
                logger.info(f"Found store name: {line}")
                break

        if not receipt.store_name:
            receipt.store_name = lines[0] if lines else None

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

        # Extract address
        address_keywords = ['st', 'ave', 'rd', 'blvd', 'lane', 'drive', 'street', 'avenue']
        for line in lines[1:6]:
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
