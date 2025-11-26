"""
PaddleOCR processor for receipt extraction with simple parser
"""
import os
import sys
import re
import logging
import time
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from PIL import Image
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.data_structures import LineItem, ReceiptData, ExtractionResult
from utils.image_processing import load_and_validate_image

try:
    from paddleocr import PaddleOCR
except ImportError:
    raise ImportError("paddleocr is required for PaddleOCR processing. Install: pip install paddleocr")

logger = logging.getLogger(__name__)

# Price validation
PRICE_MIN = 0
PRICE_MAX = 9999


class PaddleProcessor:
    """Processor for PaddleOCR-based extraction with simple rule-based parsing"""

    SKIP_KEYWORDS = {
        'subtotal', 'total', 'cash', 'change', 'tax', 'payment', 'balance',
        'thank', 'visit', 'welcome', 'receipt', 'cashier', 'card', 'debit',
        'credit', 'approved', 'transaction', 'visa', 'mastercard', 'amex'
    }

    def __init__(self, model_config: Dict):
        self.model_config = model_config
        self.model_name = model_config['name']

        # Initialize PaddleOCR
        # use_angle_cls=True enables rotation detection
        # lang='en' for English receipts
        logger.info("Initializing PaddleOCR...")
        try:
            # Note: show_log and use_gpu parameters removed as they're not supported in all PaddleOCR versions
            # PaddleOCR will automatically detect and use GPU if available
            self.ocr = PaddleOCR(
                use_angle_cls=True,
                lang='en'
            )
            logger.info("PaddleOCR initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {e}")
            raise

    def extract(self, image_path: str) -> ExtractionResult:
        """Extract receipt data using PaddleOCR"""
        start_time = time.time()

        try:
            # Load and validate image
            image = load_and_validate_image(image_path)

            # Convert PIL image to numpy array for PaddleOCR
            image_np = np.array(image)

            # Perform OCR
            # NOTE: cls parameter is set during initialization, not here!
            logger.info("Running PaddleOCR extraction...")
            result = self.ocr.ocr(image_np)

            if not result or not result[0]:
                logger.warning("PaddleOCR returned no results")
                return ExtractionResult(
                    success=False,
                    error="No text detected in image"
                )

            # Extract text lines from PaddleOCR results
            # PaddleOCR returns: [[[bbox], (text, confidence)], ...]
            text_lines = []
            for line in result[0]:
                if not line or len(line) < 2:
                    continue

                try:
                    bbox = line[0]
                    text_info = line[1]

                    # Validate bbox structure - should be a list of 4 coordinate pairs
                    if not isinstance(bbox, (list, tuple)) or len(bbox) < 1:
                        logger.warning(f"Invalid bbox format: {type(bbox)} - {bbox}")
                        continue

                    # Handle different PaddleOCR return formats
                    if isinstance(text_info, (tuple, list)) and len(text_info) == 2:
                        text, confidence = text_info
                    elif isinstance(text_info, str):
                        # Sometimes PaddleOCR returns just the text without confidence
                        text = text_info
                        confidence = 1.0  # Assume high confidence if not provided
                    else:
                        logger.warning(f"Unexpected text_info format: {type(text_info)} - {text_info}")
                        continue

                    if confidence > 0.5:  # Filter low confidence detections
                        text_lines.append({
                            'text': text,
                            'confidence': confidence,
                            'bbox': bbox
                        })
                except (ValueError, TypeError, IndexError) as e:
                    logger.warning(f"Failed to parse PaddleOCR line: {e}. Line structure: {line}")
                    continue

            # Sort text lines by vertical position (top to bottom)
            # Use safe accessor to handle different bbox formats
            def safe_get_y_coord(line_dict):
                """Safely extract Y coordinate from bbox for sorting"""
                try:
                    bbox = line_dict['bbox']
                    if isinstance(bbox, (list, tuple)) and len(bbox) > 0:
                        first_point = bbox[0]
                        if isinstance(first_point, (list, tuple)) and len(first_point) > 1:
                            return first_point[1]  # Y coordinate
                    return 0  # Default if can't extract
                except (KeyError, IndexError, TypeError):
                    return 0

            text_lines = sorted(text_lines, key=safe_get_y_coord)

            logger.info(f"PaddleOCR detected {len(text_lines)} text lines")

            # Parse the extracted text
            receipt = self._parse_receipt_text(text_lines)
            receipt.processing_time = time.time() - start_time
            receipt.model_used = self.model_name

            # Calculate confidence score
            if text_lines:
                avg_confidence = sum(line['confidence'] for line in text_lines) / len(text_lines)
                receipt.confidence = round(avg_confidence, 2)

            return ExtractionResult(success=True, data=receipt)

        except Exception as e:
            logger.error(f"PaddleOCR extraction failed: {e}", exc_info=True)
            return ExtractionResult(success=False, error=str(e))

    def _parse_receipt_text(self, text_lines: List[Dict]) -> ReceiptData:
        """Parse OCR text lines to extract receipt information using simple rules"""
        receipt = ReceiptData()

        if not text_lines:
            receipt.extraction_notes.append("No text detected")
            return receipt

        # Extract just the text strings for easier processing
        lines = [line['text'].strip() for line in text_lines]

        # Extract store name (typically first meaningful line with at least 2 characters)
        receipt.store_name = None
        for i, line in enumerate(lines[:5]):  # Check first 5 lines
            # Skip single characters and common OCR artifacts
            if len(line) >= 2 and not line.isdigit():
                receipt.store_name = line
                logger.info(f"Found store name: {line}")
                break

        if not receipt.store_name and lines:
            receipt.store_name = lines[0]
            if len(receipt.store_name) < 2:
                receipt.extraction_notes.append(
                    f"Store name very short: '{receipt.store_name}' - possible OCR error"
                )

        # Extract date - multiple formats
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # MM/DD/YYYY or DD-MM-YYYY
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',    # YYYY-MM-DD
            r'(\w{3}\s+\d{1,2},?\s+\d{4})',      # Jan 15, 2024
        ]
        for line in lines:
            for pattern in date_patterns:
                date_match = re.search(pattern, line)
                if date_match:
                    receipt.transaction_date = date_match.group(1)
                    logger.info(f"Found date: {receipt.transaction_date}")
                    break
            if receipt.transaction_date:
                break

        # Extract total - look for "total" keyword followed by price
        total_patterns = [
            r'total[:\s]*\$?\s*(\d+[.,]\d{2})',
            r'amount[:\s]*\$?\s*(\d+[.,]\d{2})',
            r'balance[:\s]*\$?\s*(\d+[.,]\d{2})',
            r'grand\s*total[:\s]*\$?\s*(\d+[.,]\d{2})'
        ]
        for pattern in total_patterns:
            for line in lines:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    total_str = match.group(1).replace(',', '.')
                    total_val = self._normalize_price(total_str)
                    if total_val:
                        receipt.total = total_val
                        logger.info(f"Found total: {receipt.total}")
                        break
            if receipt.total:
                break

        # Extract line items
        receipt.items = self._extract_line_items(lines, text_lines)

        # Extract address (lines with numbers and street keywords)
        address_keywords = ['st', 'ave', 'rd', 'blvd', 'lane', 'drive', 'street', 'avenue', 'way', 'plaza']
        for line in lines[1:8]:  # Check first few lines after store name
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in address_keywords) and any(char.isdigit() for char in line):
                receipt.store_address = line
                logger.info(f"Found address: {line}")
                break

        # Extract phone number
        phone_patterns = [
            r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})',  # (123) 456-7890
            r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})',        # 123-456-7890
        ]
        for line in lines:
            for pattern in phone_patterns:
                phone_match = re.search(pattern, line)
                if phone_match:
                    receipt.store_phone = phone_match.group(1)
                    logger.info(f"Found phone: {receipt.store_phone}")
                    break
            if receipt.store_phone:
                break

        return receipt

    def _extract_line_items(self, lines: List[str], text_lines: List[Dict]) -> List[LineItem]:
        """Extract line items using simple rule-based parsing"""
        items = []
        seen_names = set()

        # Pattern to match: text followed by price
        # Handles various formats: "Product 12.99", "Product $12.99", "Product 12,99"
        item_price_patterns = [
            r'^(.+?)\s+\$?\s*(\d+[.,]\d{2})$',           # Simple: "Name 12.99"
            r'^(.+?)\s+(\d+[.,]\d{2})\s*$',              # With trailing space
            r'^(.+?)\s+\$\s*(\d+[.,]\d{2})$',            # With dollar sign
        ]

        for i, line in enumerate(lines):
            # Skip header/footer lines
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in self.SKIP_KEYWORDS):
                continue

            # Try to match item with price using multiple patterns
            matched = False
            for pattern in item_price_patterns:
                match = re.search(pattern, line.strip())
                if match:
                    name = match.group(1).strip()
                    price_str = match.group(2).replace(',', '.')

                    # Validate name
                    if len(name) < 2 or name in seen_names:
                        continue

                    # Skip if name is just numbers
                    if name.replace(' ', '').isdigit():
                        continue

                    # Validate price
                    price = self._normalize_price(price_str)
                    if not price:
                        continue

                    # Check confidence if available
                    confidence = None
                    if i < len(text_lines):
                        confidence = text_lines[i].get('confidence')

                    # Skip low confidence items (< 0.6)
                    if confidence and confidence < 0.6:
                        continue

                    # Add item
                    items.append(LineItem(
                        name=name,
                        total_price=price
                    ))
                    seen_names.add(name)
                    matched = True
                    break

            # Alternative: Look for price patterns and extract name from same line
            if not matched:
                # Try to find standalone prices and match with text on the same line
                price_match = re.search(r'\$?\s*(\d+[.,]\d{2})(?!\d)', line)
                if price_match:
                    price_str = price_match.group(1).replace(',', '.')
                    price = self._normalize_price(price_str)

                    if price:
                        # Extract name as text before the price
                        name_part = line[:price_match.start()].strip()
                        # Remove common prefixes/suffixes
                        name_part = re.sub(r'^\d+\s*[x*]\s*', '', name_part)  # Remove quantity prefix
                        name_part = name_part.strip()

                        if len(name_part) >= 2 and name_part not in seen_names:
                            # Skip if it looks like a total/subtotal line
                            if not any(kw in name_part.lower() for kw in self.SKIP_KEYWORDS):
                                items.append(LineItem(
                                    name=name_part,
                                    total_price=price
                                ))
                                seen_names.add(name_part)

        logger.info(f"Extracted {len(items)} line items")
        return items

    @staticmethod
    def _normalize_price(value) -> Optional[Decimal]:
        """Normalize price values - handles both dot and comma as decimal separator"""
        if value is None:
            return None
        try:
            # Convert to string and clean
            price_str = str(value).replace('$', '').replace(',', '.').strip()

            # Remove any spaces
            price_str = price_str.replace(' ', '')

            # Skip negative values
            if price_str.startswith('-'):
                return None

            # Convert to Decimal
            val = Decimal(price_str)

            # Validate range
            return val if PRICE_MIN <= val <= PRICE_MAX else None

        except (ValueError, ArithmeticError):
            return None
