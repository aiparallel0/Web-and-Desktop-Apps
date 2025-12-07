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
from shared.utils.telemetry import get_tracer, set_span_attributes
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
        """
        Apply aggressive preprocessing for difficult images.
        
        Optimized to generate only the most effective preprocessing variants:
        - Reduced from 5 variants to 3 most effective ones
        - Removed redundant upscaling variations
        - Kept: Otsu threshold, Adaptive threshold, CLAHE
        
        Performance: 40% reduction in preprocessing time
        """
        preprocessed = []
        img_np = np.array(image)
        
        # Version 1: Upscale 2x with denoising and Otsu threshold
        # This is the most effective variant for faded/low-quality images
        upscaled = cv2.resize(img_np, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        gray1 = cv2.cvtColor(upscaled, cv2.COLOR_RGB2GRAY)
        denoised1 = cv2.fastNlMeansDenoising(gray1, h=10)
        _, thresh1 = cv2.threshold(denoised1, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        preprocessed.append(Image.fromarray(thresh1))
        
        # Version 2: Adaptive threshold (good for uneven lighting)
        # Essential for receipts with shadows or gradient lighting
        gray2 = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        adaptive = cv2.adaptiveThreshold(
            gray2, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        preprocessed.append(Image.fromarray(adaptive))
        
        # Version 3: CLAHE (Contrast Limited Adaptive Histogram Equalization)
        # Best for receipts with low contrast or faded text
        gray3 = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        clahe_img = clahe.apply(gray3)
        preprocessed.append(Image.fromarray(clahe_img))
        
        # Removed: High contrast enhancement (redundant with CLAHE)
        # Removed: Upscale 3x variant (diminishing returns, very slow)
        
        return preprocessed

    def extract(self, image_path: str) -> ExtractionResult:
        """
        Extract receipt data from image using Tesseract OCR.
        
        Uses multi-pass extraction with multiple PSM modes to find the best result.
        PSM 11 (sparse text) and PSM 3 (fully automatic) are prioritized as they
        often work better for receipt images with varied layouts.
        
        Detection configuration is managed via the circular exchange framework
        with lowered default thresholds for improved text detection rates.
        
        Args:
            image_path: Path to the image file to process.
            
        Returns:
            ExtractionResult containing the extracted receipt data on success,
            or error information on failure.
        """
        tracer = get_tracer()
        with tracer.start_as_current_span("ocr_processor.extract") as span:
            start_time = time.time()
            
            # Set span attributes
            set_span_attributes(span, {
                "operation.type": "ocr_processing",
                "model.id": "tesseract",
                "model.name": self.model_name
            })
            
            if not self.tesseract_path:
                span.set_attribute("error", True)
                return ExtractionResult(success=False, error="Tesseract not installed")
            
            try:
            # Get detection configuration from circular exchange framework
            detection_config = get_detection_config()
            # Note: min_confidence can be used for future filtering of low-confidence results
            
            image = load_and_validate_image(image_path)
            processed = preprocess_for_ocr(image, aggressive=True)
            
            # Try multiple PSM modes on both original and preprocessed images
            # PSM 11: Sparse text - find as much text as possible (best for receipts)
            # PSM 3: Fully automatic page segmentation (good fallback)
            # PSM 6: Assume uniform block of text
            # 
            # Optimized: Reduced from 5 PSM modes to 3 most effective ones
            # Removed PSM 4 (column) and PSM 1 (auto+osd) - rarely better than PSM 11/3
            # Performance: 40% reduction in initial OCR passes (10 -> 6 passes)
            
            # Priority order: PSM 11 and 3 first as they work best for receipts
            psm_configs = [
                (11, 'sparse'),   # Best for scattered/sparse text like receipts
                (3, 'auto'),      # Fully automatic - good general purpose
                (6, 'block'),     # Uniform text block - good for structured receipts
            ]
            
            ocr_results = []
            
            # Try each PSM mode on BOTH preprocessed AND original image
            # Sometimes preprocessing hurts more than helps
            # Each result stored as: (mode_name: str, text: str, receipt: ReceiptData, score: int)
            images_to_try = [
                ('preprocessed', processed),
                ('original', image.convert('L')),  # Grayscale original
            ]
            
            for img_name, img in images_to_try:
                for psm, desc in psm_configs:
                    try:
                        # Use preserve_interword_spaces to maintain word boundaries
                        config = f'--oem 3 --psm {psm} -c preserve_interword_spaces=1'
                        text = pytesseract.image_to_string(img, lang='eng', config=config)
                        
                        if not text or len(text.strip()) < 5:
                            continue
                            
                        receipt = self._parse_receipt_text(text)
                        score = self._score_result(receipt, text)
                        mode_name = f'PSM {psm} ({desc}) on {img_name}'
                        ocr_results.append((mode_name, text, receipt, score))
                        
                        logger.debug(f"{mode_name}: score={score}, len={len(text)}")
                        
                        # Early exit optimization: Stop if we get an excellent result early
                        # Saves time by avoiding unnecessary OCR passes
                        # Note: This only exits the PSM mode loop for the current image variant
                        # The outer loop will continue with the next image variant if needed
                        if score >= EXCELLENT_QUALITY_SCORE_THRESHOLD:
                            logger.info(f"Excellent result found early with {mode_name}, stopping PSM modes for this image variant")
                            break  # Exit inner loop (PSM modes)
                        
                    except Exception as e:
                        logger.debug(f"PSM {psm} on {img_name} failed: {e}")
                        continue
                
                # Break outer loop if excellent result found
                # Check if we just added a result with excellent score
                # Each ocr_results entry is: (mode_name, text, receipt, score)
                if ocr_results:
                    last_score = ocr_results[-1][3]  # Index 3 is the score
                    if last_score >= EXCELLENT_QUALITY_SCORE_THRESHOLD:
                        logger.info(f"Excellent result found, stopping all OCR passes")
                        break  # Exit outer loop (image variants)
            
            if not ocr_results:
                return ExtractionResult(success=False, error="All OCR modes failed")
            
            # Select best result by score (quality)
            best_mode, best_text, receipt, initial_score = max(ocr_results, key=lambda x: x[3])
            
            # Log all results for debugging
            logger.info(f"OCR tried {len(ocr_results)} mode combinations:")
            for mode, _, _, score in sorted(ocr_results, key=lambda x: x[3], reverse=True)[:5]:
                logger.info(f"  {mode}: score={score}")
            logger.info(f"Best: {best_mode} with score={initial_score}")
            
            # If we got a good result, return early
            if initial_score >= GOOD_QUALITY_SCORE_THRESHOLD:
                receipt.processing_time = time.time() - start_time
                receipt.model_used = f"{self.model_name} ({best_mode})"
                # Convert score to percentage (0-100) - don't exceed 100%
                receipt.confidence_score = min(100.0, (initial_score / 95) * 100)
                logger.info(f"Good result achieved with score: {initial_score}")
                return ExtractionResult(success=True, data=receipt)
            
            # Low quality result - try aggressive multi-pass extraction
            logger.info(f"Low score ({initial_score}) - trying aggressive preprocessing")
            
            preprocessed_versions = self._aggressive_preprocess(image)
            # Optimized: Try only PSM 11 and 3 in aggressive pass (most effective)
            # Reduced from 5 modes to 2 for faster processing
            psm_modes = [11, 3]  # Priority order for aggressive pass
            best_result, best_score = receipt, initial_score
            best_text_final = best_text  # Keep track of best text across all passes
            
            for v_idx, proc_img in enumerate(preprocessed_versions):
                for psm in psm_modes:
                    try:
                        config = f'--oem 3 --psm {psm} -c preserve_interword_spaces=1'
                        text = pytesseract.image_to_string(proc_img, lang='eng', config=config)
                        if not text or len(text.strip()) < 10:
                            continue
                        rec = self._parse_receipt_text(text)
                        score = self._score_result(rec, text)
                        if score > best_score:
                            best_score = score
                            best_result = rec
                            best_text_final = text
                            logger.info(f"Better result found: PSM {psm} on preproc v{v_idx+1}, score={score}")
                            # Early exit if we find an excellent result
                            if score >= EXCELLENT_QUALITY_SCORE_THRESHOLD:
                                logger.info(f"Excellent result with score {score}, stopping search")
                                break
                    except Exception:
                        continue
                # Break outer loop too if excellent result found
                if best_score >= EXCELLENT_QUALITY_SCORE_THRESHOLD:
                    break
            
            # Record detection result for auto-tuning via circular exchange
            text_regions = len(best_text_final.strip().split('\n')) if best_text_final else 0
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
            
            # Use realistic validation-based confidence instead of naive scoring
            try:
                from .receipt_prompts import get_validated_extraction_with_confidence
                _, realistic_confidence, validation = get_validated_extraction_with_confidence(
                    receipt_data=best_result,
                    raw_text=best_text_final,
                    base_confidence=min(1.0, best_score / 100)  # Convert score to base confidence
                )
                best_result.confidence_score = round(realistic_confidence * 100, 1)
                if validation.math_validated:
                    best_result.extraction_notes.append("Math validation passed ✓")
                elif validation.errors:
                    for error in validation.errors:
                        best_result.extraction_notes.append(f"ERROR: {error}")
            except ImportError:
                best_result.confidence_score = min(1.0, best_score / 95) * 100
            
            # Set success span attributes
            set_span_attributes(span, {
                "extraction.success": True,
                "extraction.confidence": best_result.confidence_score,
                "extraction.items_count": len(best_result.items) if best_result.items else 0,
                "extraction.total": float(best_result.total) if best_result.total else 0.0,
                "extraction.processing_time": time.time() - start_time
            })
            
            return ExtractionResult(success=True, data=best_result)
            
        except Exception as e:
            logger.error(f"OCR failed: {e}", exc_info=True)
            span.record_exception(e)
            try:
                from opentelemetry.trace import Status, StatusCode
                span.set_status(Status(StatusCode.ERROR, str(e)))
            except ImportError:
                pass
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
