"""
OCR Processor Module with Circular Exchange Integration

This module provides Tesseract OCR-based receipt data extraction with:
- Dynamic parameter configuration via circular exchange framework
- Early-exit optimization for faster processing
- Multi-pass extraction for challenging images
- Auto-tuning based on detection results

The OCRProcessor class integrates with the circular exchange framework for
runtime parameter tuning and automatic optimization.
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

# Circular Exchange Framework Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration, PackageRegistry
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    try:
        from ..circular_exchange import PROJECT_CONFIG, ModuleRegistration, PackageRegistry
        CIRCULAR_EXCHANGE_AVAILABLE = True
    except ImportError:
        CIRCULAR_EXCHANGE_AVAILABLE = False

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from shared.utils.data import LineItem, ReceiptData, ExtractionResult
from shared.utils.image import load_and_validate_image, preprocess_for_ocr
from .ocr_common import (
    SKIP_KEYWORDS, PRICE_MIN, PRICE_MAX, normalize_price,
    extract_date, extract_total, extract_phone, extract_address,
    should_skip_line, should_skip_item_name, extract_store_name,
    LINE_ITEM_PATTERNS, clean_item_name, extract_subtotal, extract_tax,
    validate_receipt_totals, extract_sku,
    extract_line_items as _extract_line_items_shared,
    parse_receipt_text as _parse_receipt_text_shared,
    get_detection_config, record_detection_result
)

try:
    import pytesseract
except ImportError:
    pytesseract = None

logger = logging.getLogger(__name__)

# Register module with Circular Exchange
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="shared.models.ocr_processor",
            file_path=__file__,
            description="Tesseract OCR-based receipt data extraction with early-exit optimization",
            dependencies=["shared.utils.image_processing", "shared.models.ocr_common", "shared.models.ocr_config"],
            exports=["OCRProcessor"]
        ))
    except Exception:
        pass

# Score thresholds for early-exit optimization in OCR extraction
# Good quality threshold: has total + some other data (avoid aggressive preprocessing)
# Lowered from 40 to 25 to ensure more aggressive multi-pass extraction
GOOD_QUALITY_SCORE_THRESHOLD = 25
# Excellent quality threshold: high confidence result (stop searching immediately)
# Lowered from 80 to 60 to capture more text from challenging images
EXCELLENT_QUALITY_SCORE_THRESHOLD = 60


class OCRProcessor:
    """
    Tesseract OCR-based receipt processor with CEFR integration.
    
    This processor uses Tesseract OCR for text extraction with:
    - Early-exit optimization for faster processing
    - Multi-pass extraction for challenging images
    - Auto-tuning based on detection results via circular exchange
    """

    def __init__(self, model_config: Dict):
        """Initialize OCR processor with model configuration."""
        if pytesseract is None:
            raise ImportError("pytesseract required: pip install pytesseract")
        
        self.model_config = model_config
        self.model_name = model_config['name']
        self.tesseract_path = self._find_tesseract()
        if self.tesseract_path is None:
            raise EnvironmentError(
                "Tesseract not installed. Install: https://github.com/UB-Mannheim/tesseract/wiki"
            )
        if self.tesseract_path and self.tesseract_path != 'tesseract':
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
            logger.info(f"Tesseract: {self.tesseract_path}")
        self._verify_tesseract()

    def _verify_tesseract(self):
        """Verify Tesseract is working correctly."""
        try:
            version = pytesseract.get_tesseract_version()
            logger.info(f"Tesseract v{version}")
        except Exception as e:
            raise EnvironmentError(f"Tesseract not working: {e}") from e

    def _find_tesseract(self) -> Optional[str]:
        """Find Tesseract executable path."""
        logger.info("Searching Tesseract...")
        try:
            result = subprocess.run(
                ['tesseract', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return 'tesseract'
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        if sys.platform == 'win32':
            paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
            ]
            for p in paths:
                if os.path.exists(p):
                    return p
        elif sys.platform == 'darwin':
            paths = ['/usr/local/bin/tesseract', '/opt/homebrew/bin/tesseract']
            for p in paths:
                if os.path.exists(p):
                    return p
        else:
            paths = ['/usr/bin/tesseract', '/usr/local/bin/tesseract']
            for p in paths:
                if os.path.exists(p):
                    return p
        return None

    def _aggressive_preprocess(self, image: Image.Image) -> List[Image.Image]:
        """Apply aggressive preprocessing for difficult images."""
        preprocessed = []
        img_np = np.array(image)
        
        # Upscale and denoise
        upscaled = cv2.resize(img_np, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        gray1 = cv2.cvtColor(upscaled, cv2.COLOR_RGB2GRAY)
        denoised1 = cv2.fastNlMeansDenoising(gray1, h=10)
        _, thresh1 = cv2.threshold(denoised1, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        preprocessed.append(Image.fromarray(thresh1))
        
        # Adaptive threshold
        gray2 = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        adaptive = cv2.adaptiveThreshold(
            gray2, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        preprocessed.append(Image.fromarray(adaptive))
        
        # Contrast enhancement
        gray3 = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        enhanced = Image.fromarray(gray3)
        enhancer = ImageEnhance.Contrast(enhanced)
        preprocessed.append(enhancer.enhance(2.0))
        
        return preprocessed

    def extract(self, image_path: str) -> ExtractionResult:
        """
        Extract receipt data from image using Tesseract OCR.
        
        Uses early-exit strategy to avoid unnecessary OCR calls. Only performs
        aggressive multi-pass extraction when initial results are poor quality.
        Detection configuration is managed via the circular exchange framework
        with lowered default thresholds for improved text detection rates.
        
        Args:
            image_path: Path to the image file to process.
            
        Returns:
            ExtractionResult containing the extracted receipt data on success,
            or error information on failure.
        """
        start_time = time.time()
        if not self.tesseract_path:
            return ExtractionResult(success=False, error="Tesseract not installed")
        
        try:
            # Get detection configuration from circular exchange framework
            detection_config = get_detection_config()
            min_confidence = detection_config.get('min_confidence', 0.25)
            auto_retry = detection_config.get('auto_retry', True)
            
            image = load_and_validate_image(image_path)
            processed = preprocess_for_ocr(image, aggressive=True)
            
            # First pass: Try 2 PSM modes on preprocessed image
            ocr_results = []
            config1 = (
                r'--oem 3 --psm 6 -c tessedit_char_whitelist='
                r'0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz$.,:/\-#@()&% '
            )
            text1 = pytesseract.image_to_string(processed, lang='eng', config=config1)
            receipt1 = self._parse_receipt_text(text1)
            score1 = self._score_result(receipt1, text1)
            ocr_results.append(('PSM 6', text1, receipt1, score1))
            
            config2 = r'--oem 3 --psm 4'
            text2 = pytesseract.image_to_string(processed, lang='eng', config=config2)
            receipt2 = self._parse_receipt_text(text2)
            score2 = self._score_result(receipt2, text2)
            ocr_results.append(('PSM 4', text2, receipt2, score2))
            
            # Select best result by score (quality) rather than just length
            best_mode, best_text, receipt, initial_score = max(ocr_results, key=lambda x: x[3])
            
            logger.info(
                f"OCR complete: {best_mode}, len={len(best_text)}, "
                f"score={initial_score} (threshold: {min_confidence})"
            )
            
            # Early exit if initial result is good
            if initial_score >= GOOD_QUALITY_SCORE_THRESHOLD:
                receipt.processing_time = time.time() - start_time
                receipt.model_used = f"{self.model_name} ({best_mode})"
                receipt.confidence_score = min(1.0, initial_score / 95)
                logger.info(f"Early exit with good score: {initial_score}")
                return ExtractionResult(success=True, data=receipt)
            
            # Low quality result - try aggressive multi-pass extraction
            if len(best_text.strip()) < 50:
                logger.info("Low OCR output - trying aggressive preprocessing")
            
            preprocessed_versions = self._aggressive_preprocess(image)
            psm_modes = [6, 4, 11, 3]
            best_result, best_score = receipt, initial_score
            
            for v_idx, proc_img in enumerate(preprocessed_versions):
                for psm in psm_modes:
                    try:
                        config = f'--oem 3 --psm {psm}'
                        text = pytesseract.image_to_string(proc_img, lang='eng', config=config)
                        if not text or len(text.strip()) < 10:
                            continue
                        rec = self._parse_receipt_text(text)
                        score = self._score_result(rec, text)
                        if score > best_score:
                            best_score = score
                            best_result = rec
                            # Early exit if we find an excellent result
                            if score >= EXCELLENT_QUALITY_SCORE_THRESHOLD:
                                logger.info(f"Found excellent result with score {score}, stopping search")
                                break
                    except Exception:
                        continue
                # Break outer loop too if excellent result found
                if best_score >= EXCELLENT_QUALITY_SCORE_THRESHOLD:
                    break
            
            # Record detection result for auto-tuning via circular exchange
            text_regions = len(best_text.strip().split('\n')) if best_text else 0
            record_detection_result(
                text_regions_count=text_regions,
                avg_confidence=min(1.0, best_score / 100) if best_score else 0.0,
                success=best_result is not None and best_score > 0,
                processing_time=time.time() - start_time
            )
            
            if best_result is None or best_score == 0:
                return ExtractionResult(success=False, error="No readable text. Try EasyOCR.")
            
            best_result.processing_time = time.time() - start_time
            best_result.model_used = self.model_name
            best_result.confidence_score = min(1.0, best_score / 95)
            return ExtractionResult(success=True, data=best_result)
            
        except Exception as e:
            logger.error(f"OCR failed: {e}", exc_info=True)
            return ExtractionResult(success=False, error=str(e))

    def _score_result(self, receipt: ReceiptData, text: str) -> int:
        """Score the quality of an extraction result."""
        score = 0
        
        # Known store names get higher score
        known_stores = [
            'WALMART', "TRADER JOE'S", 'COSTCO', 'TARGET', 'WHOLE FOODS',
            'KROGER', 'SAFEWAY', 'PUBLIX', 'CVS', 'WALGREENS'
        ]
        if receipt.store_name:
            if receipt.store_name.upper() in known_stores:
                score += 40  # Bonus for recognized store
            elif len(receipt.store_name) > 2:
                score += 10
        
        if receipt.transaction_date:
            score += 15
        if receipt.total and receipt.total > 0:
            score += 30
        if receipt.items:
            score += 10 * len(receipt.items)
        if receipt.store_address:
            score += 10
        if receipt.store_phone:
            score += 10
        
        # Validate math: subtotal + tax should equal total
        if receipt.subtotal and receipt.tax and receipt.total:
            expected = receipt.subtotal + receipt.tax
            if abs(expected - receipt.total) < Decimal('0.10'):
                score += 50  # Big bonus for valid math
            else:
                score -= 30  # Penalty for invalid math
        
        # Penalize high special character ratio
        special_ratio = sum(
            1 for c in text if not c.isalnum() and not c.isspace()
        ) / max(len(text), 1)
        if special_ratio > 0.3:
            score -= 20
        
        return max(0, score)

    def _parse_receipt_text(self, text: str) -> ReceiptData:
        """Parse OCR text into structured receipt data."""
        receipt = ReceiptData()
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if not lines:
            return receipt
        
        # Use shared implementation
        parsed = _parse_receipt_text_shared(lines)
        receipt.store_name = parsed['store_name']
        receipt.transaction_date = parsed['transaction_date']
        receipt.total = parsed['total']
        receipt.subtotal = parsed['subtotal']
        receipt.tax = parsed['tax']
        # Convert tuples to LineItem objects
        receipt.items = [
            LineItem(name=name, total_price=price, quantity=qty)
            for name, price, qty in parsed['items']
        ]
        receipt.store_address = parsed['store_address']
        receipt.store_phone = parsed['store_phone']
        receipt.extraction_notes = parsed['extraction_notes']
        return receipt

    def _extract_line_items(self, lines: List[str]) -> List[LineItem]:
        """Extract line items from text lines."""
        # Use shared implementation and convert tuples to LineItem objects
        items_data = _extract_line_items_shared(lines)
        return [
            LineItem(name=name, total_price=price, quantity=qty)
            for name, price, qty in items_data
        ]


__all__ = ['OCRProcessor', 'GOOD_QUALITY_SCORE_THRESHOLD', 'EXCELLENT_QUALITY_SCORE_THRESHOLD']
