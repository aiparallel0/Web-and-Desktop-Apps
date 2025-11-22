"""
Tesseract OCR processor for receipt extraction - AGGRESSIVE MULTI-MODE VERSION
"""
import os
import sys
import re
import logging
import time
import subprocess
from decimal import Decimal
from typing import Dict, List, Optional
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.data_structures import LineItem, ReceiptData, ExtractionResult
from utils.image_processing import load_and_validate_image

try:
    import pytesseract
except ImportError:
    raise ImportError("pytesseract is required for OCR processing. Install: pip install pytesseract")

logger = logging.getLogger(__name__)

# Price validation
PRICE_MIN = 0
PRICE_MAX = 9999


class OCRProcessor:
    """Processor for Tesseract OCR-based extraction with AGGRESSIVE multi-mode approach"""

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

        # Try system PATH first
        try:
            result = subprocess.run(['tesseract', '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                logger.info("Found Tesseract in system PATH")
                return 'tesseract'
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.debug("Tesseract not found in PATH")

        # Windows paths
        if sys.platform == 'win32':
            windows_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                r'C:\Users\User\AppData\Local\Programs\Tesseract-OCR\tesseract.exe',
                r'C:\Tesseract-OCR\tesseract.exe',
            ]
            for path in windows_paths:
                if os.path.exists(path):
                    logger.info(f"Found Tesseract: {path}")
                    return path

        # macOS paths
        elif sys.platform == 'darwin':
            mac_paths = [
                '/usr/local/bin/tesseract',
                '/opt/homebrew/bin/tesseract',
                '/opt/local/bin/tesseract',
            ]
            for path in mac_paths:
                if os.path.exists(path):
                    logger.info(f"Found Tesseract: {path}")
                    return path

        # Linux paths
        else:
            linux_paths = ['/usr/bin/tesseract', '/usr/local/bin/tesseract']
            for path in linux_paths:
                if os.path.exists(path):
                    logger.info(f"Found Tesseract: {path}")
                    return path

        logger.warning("Tesseract not found!")
        return None

    def _aggressive_preprocess(self, image: Image.Image) -> List[Image.Image]:
        """Create MULTIPLE preprocessed versions to try different approaches"""
        preprocessed = []

        # Convert to numpy
        img_np = np.array(image)

        # Version 1: AGGRESSIVE upscaling + denoising + thresholding
        logger.info("Creating version 1: Aggressive upscale + denoise")
        upscaled = cv2.resize(img_np, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        gray1 = cv2.cvtColor(upscaled, cv2.COLOR_RGB2GRAY)
        denoised1 = cv2.fastNlMeansDenoising(gray1, h=10)
        _, thresh1 = cv2.threshold(denoised1, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        preprocessed.append(Image.fromarray(thresh1))

        # Version 2: Adaptive threshold
        logger.info("Creating version 2: Adaptive threshold")
        gray2 = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        adaptive = cv2.adaptiveThreshold(gray2, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        preprocessed.append(Image.fromarray(adaptive))

        # Version 3: Simple grayscale with high contrast
        logger.info("Creating version 3: High contrast grayscale")
        gray3 = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        enhanced = Image.fromarray(gray3)
        enhancer = ImageEnhance.Contrast(enhanced)
        enhanced = enhancer.enhance(2.0)
        preprocessed.append(enhanced)

        return preprocessed

    def extract(self, image_path: str) -> ExtractionResult:
        """Extract receipt data using Tesseract OCR - TRY MULTIPLE MODES"""
        start_time = time.time()

        if not self.tesseract_path:
            return ExtractionResult(
                success=False,
                error="Tesseract OCR not installed. Install from: https://github.com/UB-Mannheim/tesseract/wiki"
            )

        try:
            # Load image
            image = load_and_validate_image(image_path)

            # Get multiple preprocessed versions
            preprocessed_versions = self._aggressive_preprocess(image)

            # PSM modes to try (in order of preference for receipts)
            psm_modes = [
                6,   # Uniform block of text
                4,   # Single column of text
                11,  # Sparse text
                3,   # Fully automatic
            ]

            best_result = None
            best_score = 0

            logger.info(f"Trying {len(preprocessed_versions)} preprocessing methods with {len(psm_modes)} PSM modes")

            # Try each preprocessing version with each PSM mode
            for version_idx, processed_img in enumerate(preprocessed_versions):
                for psm in psm_modes:
                    try:
                        config = f'--oem 3 --psm {psm}'
                        logger.info(f"Trying version {version_idx+1}, PSM {psm}")

                        text = pytesseract.image_to_string(processed_img, lang='eng', config=config)

                        if not text or len(text.strip()) < 10:
                            continue

                        # Score the result based on how much useful data we can extract
                        receipt = self._parse_receipt_text(text)
                        score = self._score_result(receipt, text)

                        logger.info(f"  Result score: {score} (text length: {len(text)})")

                        if score > best_score:
                            best_score = score
                            best_result = receipt
                            logger.info(f"  ✓ New best result! Score: {score}")

                    except Exception as e:
                        logger.warning(f"PSM {psm} failed: {e}")
                        continue

            if best_result is None or best_score == 0:
                return ExtractionResult(
                    success=False,
                    error="Tesseract could not extract readable text. Try EasyOCR instead."
                )

            best_result.processing_time = time.time() - start_time
            best_result.model_used = self.model_name

            logger.info(f"Best result score: {best_score}, items: {len(best_result.items)}, total: ${best_result.total or 0}")
            return ExtractionResult(success=True, data=best_result)

        except Exception as e:
            logger.error(f"OCR extraction failed: {e}", exc_info=True)
            return ExtractionResult(success=False, error=str(e))

    def _score_result(self, receipt: ReceiptData, text: str) -> int:
        """Score extraction result quality"""
        score = 0

        # Points for each field extracted
        if receipt.store_name and len(receipt.store_name) > 2:
            score += 20
        if receipt.transaction_date:
            score += 15
        if receipt.total and receipt.total > 0:
            score += 30
        if receipt.items and len(receipt.items) > 0:
            score += 10 * len(receipt.items)
        if receipt.store_address:
            score += 10
        if receipt.store_phone:
            score += 10

        # Penalty for gibberish (lots of special characters)
        special_char_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / max(len(text), 1)
        if special_char_ratio > 0.3:
            score -= 20

        return max(0, score)

    def _parse_receipt_text(self, text: str) -> ReceiptData:
        """Parse OCR text to extract receipt information"""
        receipt = ReceiptData()
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        if not lines:
            return receipt

        # Extract store name
        for line in lines[:5]:
            if len(line) >= 3 and not line.isdigit():
                receipt.store_name = line
                break

        # Extract date
        date_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        for line in lines:
            match = re.search(date_pattern, line)
            if match:
                receipt.transaction_date = match.group(1)
                break

        # Extract total - AGGRESSIVE patterns
        total_patterns = [
            r'total[:\s]*\$?\s*(\d+\.?\d{0,2})',
            r'amount[:\s]*\$?\s*(\d+\.?\d{0,2})',
            r'balance[:\s]*\$?\s*(\d+\.?\d{0,2})',
            r'grand\s*total[:\s]*\$?\s*(\d+\.?\d{0,2})',
            r'\$\s*(\d+\.\d{2})\s*(?:total|amount)',
        ]
        for line in lines:
            for pattern in total_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    price = self._normalize_price(match.group(1))
                    if price and price > 0:
                        receipt.total = price
                        break
            if receipt.total:
                break

        # Extract line items
        receipt.items = self._extract_line_items(lines)

        # Extract address
        address_keywords = ['st', 'ave', 'rd', 'blvd', 'lane', 'drive', 'street', 'avenue']
        for line in lines[1:8]:
            line_lower = line.lower()
            if any(kw in line_lower for kw in address_keywords) and any(c.isdigit() for c in line):
                receipt.store_address = line
                break

        # Extract phone
        phone_pattern = r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'
        for line in lines:
            match = re.search(phone_pattern, line)
            if match:
                receipt.store_phone = match.group(1)
                break

        return receipt

    def _extract_line_items(self, lines: List[str]) -> List[LineItem]:
        """Extract line items from OCR text"""
        items = []
        seen_names = set()

        # Patterns for item with price
        item_patterns = [
            r'^(.+?)\s+\$?\s*(\d+\.?\d{0,2})$',
            r'^(.+?)\s+(\d+\.?\d{0,2})\s*$'
        ]

        for line in lines:
            line_lower = line.lower()
            if any(kw in line_lower for kw in self.SKIP_KEYWORDS):
                continue

            for pattern in item_patterns:
                match = re.search(pattern, line.strip())
                if match:
                    name = match.group(1).strip()
                    price_str = match.group(2)

                    if len(name) < 2 or name in seen_names:
                        continue

                    price = self._normalize_price(price_str)
                    if not price or price <= 0:
                        continue

                    items.append(LineItem(name=name, total_price=price, quantity=1))
                    seen_names.add(name)
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
