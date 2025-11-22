"""
EasyOCR processor for receipt extraction
Using proven pattern from working examples
"""
import os
import sys
import re
import logging
import time
from decimal import Decimal
from typing import Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.data_structures import LineItem, ReceiptData, ExtractionResult

try:
    import easyocr
except ImportError:
    easyocr = None

logger = logging.getLogger(__name__)

# Price validation
PRICE_MIN = 0
PRICE_MAX = 9999


class EasyOCRProcessor:
    """Processor for EasyOCR-based extraction using proven pattern"""

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
            logger.error("EasyOCR not installed!")
            return

        try:
            # Initialize EasyOCR reader - PROVEN PATTERN FROM WEB
            logger.info("Initializing EasyOCR reader...")
            self.reader = easyocr.Reader(['en'], gpu=False)
            logger.info("EasyOCR reader initialized successfully!")
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR: {e}")
            self.reader = None

    def extract(self, image_path: str) -> ExtractionResult:
        """Extract receipt data using EasyOCR - PROVEN WORKING PATTERN"""
        start_time = time.time()

        # Check if EasyOCR is available
        if easyocr is None:
            return ExtractionResult(
                success=False,
                error="EasyOCR not installed. Install: pip install easyocr"
            )

        if self.reader is None:
            return ExtractionResult(
                success=False,
                error="EasyOCR reader failed to initialize"
            )

        try:
            logger.info(f"Running EasyOCR on: {image_path}")

            # PROVEN PATTERN: reader.readtext(image_path)
            results = self.reader.readtext(image_path)

            logger.info(f"EasyOCR detected {len(results)} text regions")

            # Extract text and confidence from results
            # EasyOCR returns: [[bbox, text, confidence], ...]
            text_lines = []
            for detection in results:
                if len(detection) >= 3:
                    bbox, text, confidence = detection[0], detection[1], detection[2]
                    if confidence > 0.3:  # Filter low confidence
                        text_lines.append(text)
                        logger.info(f"  {text} (conf: {confidence:.2f})")

            if not text_lines:
                return ExtractionResult(
                    success=False,
                    error="No text detected in image"
                )

            # Parse the text
            receipt = self._parse_receipt_text(text_lines)
            receipt.processing_time = time.time() - start_time
            receipt.model_used = self.model_name

            logger.info(f"Extraction complete in {receipt.processing_time:.1f}s")
            return ExtractionResult(success=True, data=receipt)

        except Exception as e:
            logger.error(f"EasyOCR extraction failed: {e}", exc_info=True)
            return ExtractionResult(success=False, error=str(e))

    def _parse_receipt_text(self, text_lines: List[str]) -> ReceiptData:
        """Parse OCR text to extract receipt information"""
        receipt = ReceiptData()

        if not text_lines:
            receipt.extraction_notes.append("No text detected")
            return receipt

        logger.info(f"Parsing {len(text_lines)} text lines")

        # Extract store name (first meaningful line)
        receipt.store_name = None
        for line in text_lines[:5]:
            line = line.strip()
            if len(line) >= 2 and not line.isdigit():
                receipt.store_name = line
                logger.info(f"Store: {line}")
                break

        if not receipt.store_name and text_lines:
            receipt.store_name = text_lines[0]

        # Extract date
        date_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        for line in text_lines:
            match = re.search(date_pattern, line)
            if match:
                receipt.transaction_date = match.group(1)
                logger.info(f"Date: {receipt.transaction_date}")
                break

        # Extract total - AGGRESSIVE PATTERN MATCHING
        total_patterns = [
            r'total[:\s]*\$?\s*(\d+\.?\d{0,2})',
            r'amount[:\s]*\$?\s*(\d+\.?\d{0,2})',
            r'balance[:\s]*\$?\s*(\d+\.?\d{0,2})',
            r'grand\s*total[:\s]*\$?\s*(\d+\.?\d{0,2})'
        ]

        for line in text_lines:
            for pattern in total_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    price_str = match.group(1)
                    price = self._normalize_price(price_str)
                    if price and price > 0:
                        receipt.total = price
                        logger.info(f"Total: ${receipt.total}")
                        break
            if receipt.total:
                break

        # Extract line items
        receipt.items = self._extract_line_items(text_lines)

        # Extract address
        address_keywords = ['st', 'ave', 'rd', 'blvd', 'lane', 'drive', 'street', 'avenue']
        for line in text_lines[1:8]:
            line_lower = line.lower()
            if any(kw in line_lower for kw in address_keywords) and any(c.isdigit() for c in line):
                receipt.store_address = line
                logger.info(f"Address: {line}")
                break

        # Extract phone
        phone_pattern = r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'
        for line in text_lines:
            match = re.search(phone_pattern, line)
            if match:
                receipt.store_phone = match.group(1)
                logger.info(f"Phone: {receipt.store_phone}")
                break

        logger.info(f"Parsed receipt: {len(receipt.items)} items, total: ${receipt.total or 0}")
        return receipt

    def _extract_line_items(self, lines: List[str]) -> List[LineItem]:
        """Extract line items from text"""
        items = []
        seen_names = set()

        # Pattern: "Item Name 12.99" or "Item Name $12.99"
        item_patterns = [
            r'^(.+?)\s+\$?\s*(\d+\.?\d{0,2})$',
            r'^(.+?)\s+(\d+\.?\d{0,2})\s*$'
        ]

        for line in lines:
            # Skip keywords
            line_lower = line.lower()
            if any(kw in line_lower for kw in self.SKIP_KEYWORDS):
                continue

            # Try patterns
            for pattern in item_patterns:
                match = re.search(pattern, line.strip())
                if match:
                    name = match.group(1).strip()
                    price_str = match.group(2)

                    # Validate
                    if len(name) < 2 or name in seen_names:
                        continue

                    price = self._normalize_price(price_str)
                    if not price or price <= 0:
                        continue

                    # Add item
                    items.append(LineItem(
                        name=name,
                        total_price=price,
                        quantity=1
                    ))
                    seen_names.add(name)
                    logger.info(f"Item: {name} ${price}")
                    break

        return items

    @staticmethod
    def _normalize_price(value) -> Optional[Decimal]:
        """Normalize price values"""
        if value is None:
            return None
        try:
            price_str = str(value).replace('$', '').replace(',', '').strip()
            if not price_str or price_str.startswith('-'):
                return None
            val = Decimal(price_str)
            return val if PRICE_MIN <= val <= PRICE_MAX else None
        except (ValueError, ArithmeticError):
            return None
