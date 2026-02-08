"""
Enhanced EasyOCR Processor

Provides comprehensive EasyOCR integration with:
- Multiple confidence thresholds
- Spatial text analysis
- Enhanced line item extraction
- Better text ordering
"""

import os
import sys
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.utils.data import ReceiptData, ExtractionResult
from shared.models.processor_enhancements import (
    EnhancedReceiptParser,
    ConfidenceScorer
)

# Import EasyOCR
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    easyocr = None
    EASYOCR_AVAILABLE = False

logger = logging.getLogger(__name__)


class EnhancedEasyOCRProcessor:
    """Enhanced EasyOCR processor with advanced text extraction."""
    
    def __init__(self, model_config: Dict[str, Any]):
        """
        Initialize enhanced EasyOCR processor.
        
        Args:
            model_config: Model configuration dictionary
        """
        self.model_config = model_config
        self.model_name = model_config.get('name', 'Enhanced EasyOCR')
        self.reader = None
        
        if not EASYOCR_AVAILABLE:
            raise ImportError("EasyOCR not installed: pip install easyocr")
        
        try:
            logger.info("Initializing Enhanced EasyOCR...")
            self.reader = easyocr.Reader(['en'], gpu=False, verbose=False)
            logger.info("Enhanced EasyOCR initialized")
        except Exception as e:
            raise RuntimeError(f"EasyOCR initialization failed: {e}") from e
    
    def extract(self, image_path: str) -> ExtractionResult:
        """
        Extract receipt data using enhanced EasyOCR.
        
        Args:
            image_path: Path to image file
            
        Returns:
            ExtractionResult with extracted data
        """
        start_time = time.time()
        
        if not self.reader:
            return ExtractionResult(
                success=False,
                error="EasyOCR reader not initialized"
            )
        
        try:
            logger.info(f"Extracting with enhanced EasyOCR: {image_path}")
            
            # Read text with bounding boxes
            results = self.reader.readtext(image_path)
            
            if not results:
                return ExtractionResult(
                    success=False,
                    error="No text detected"
                )
            
            logger.info(f"Detected {len(results)} text regions")
            
            # Process results with multiple confidence levels
            text_lines_high = self._extract_with_confidence(results, threshold=0.5)
            text_lines_med = self._extract_with_confidence(results, threshold=0.3)
            text_lines_low = self._extract_with_confidence(results, threshold=0.1)
            
            # Try parsing with different confidence levels
            best_result = None
            best_score = 0
            
            for threshold, lines in [
                ('high', text_lines_high),
                ('medium', text_lines_med),
                ('low', text_lines_low)
            ]:
                if not lines:
                    continue
                
                receipt = EnhancedReceiptParser.parse_receipt(lines, extract_items=True)
                score = self._score_result(receipt, lines)
                
                logger.debug(f"Confidence {threshold}: score={score}, lines={len(lines)}")
                
                if score > best_score:
                    best_score = score
                    best_result = receipt
                
                # Early exit for excellent results
                if score >= 80:
                    break
            
            if best_result is None:
                return ExtractionResult(
                    success=False,
                    error="Could not extract valid receipt data"
                )
            
            # Calculate final confidence
            confidence = ConfidenceScorer.score_receipt(best_result)
            
            # Set metadata
            best_result.processing_time = time.time() - start_time
            best_result.model_used = self.model_name
            
            logger.info(f"Extraction complete: score={best_score}, confidence={confidence:.2f}")
            
            return ExtractionResult(
                success=True,
                data=best_result,
                confidence_score=confidence,
                processing_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Enhanced EasyOCR extraction failed: {e}", exc_info=True)
            return ExtractionResult(
                success=False,
                error=str(e),
                processing_time=time.time() - start_time
            )
    
    def _extract_with_confidence(self, results: List, threshold: float) -> List[str]:
        """
        Extract text lines with specific confidence threshold.
        
        Args:
            results: EasyOCR results
            threshold: Minimum confidence threshold
            
        Returns:
            List of text lines
        """
        text_lines = []
        
        # Sort by vertical position (y-coordinate)
        sorted_results = sorted(results, key=lambda x: x[0][0][1])
        
        for detection in sorted_results:
            if len(detection) >= 3:
                bbox, text, confidence = detection[0], detection[1], detection[2]
                if confidence >= threshold:
                    text_lines.append(text.strip())
        
        return text_lines
    
    def _score_result(self, receipt: ReceiptData, text_lines: List[str]) -> int:
        """Score the quality of extraction result."""
        score = 0
        
        # Store name (20 points)
        if receipt.store_name and len(receipt.store_name) > 2:
            score += 20
        
        # Total (25 points)
        if receipt.total and receipt.total > 0:
            score += 25
        
        # Date (10 points)
        if receipt.date:
            score += 10
        
        # Items (25 points)
        if receipt.items:
            if len(receipt.items) > 0:
                score += 15
            if len(receipt.items) >= 3:
                score += 5
            if len(receipt.items) >= 5:
                score += 5
        
        # Subtotal/Tax (10 points)
        if receipt.subtotal:
            score += 5
        if receipt.tax:
            score += 5
        
        # Contact info (10 points)
        if receipt.address:
            score += 5
        if receipt.phone:
            score += 5
        
        # Bonus for text lines
        if len(text_lines) > 10:
            score += 5
        
        return min(score, 100)


class EnhancedPaddleOCRProcessor:
    """Enhanced PaddleOCR processor with advanced text extraction."""
    
    def __init__(self, model_config: Dict[str, Any]):
        """
        Initialize enhanced PaddleOCR processor.
        
        Args:
            model_config: Model configuration dictionary
        """
        self.model_config = model_config
        self.model_name = model_config.get('name', 'Enhanced PaddleOCR')
        self.ocr = None
        
        try:
            from paddleocr import PaddleOCR
            PADDLEOCR_AVAILABLE = True
        except ImportError:
            raise ImportError("PaddleOCR not installed: pip install paddleocr")
        
        try:
            logger.info("Initializing Enhanced PaddleOCR...")
            self.ocr = PaddleOCR(
                use_angle_cls=True,
                lang='en',
                det_db_thresh=0.2,
                det_db_box_thresh=0.3,
                show_log=False
            )
            logger.info("Enhanced PaddleOCR initialized")
        except Exception as e:
            raise RuntimeError(f"PaddleOCR initialization failed: {e}") from e
    
    def extract(self, image_path: str) -> ExtractionResult:
        """
        Extract receipt data using enhanced PaddleOCR.
        
        Args:
            image_path: Path to image file
            
        Returns:
            ExtractionResult with extracted data
        """
        start_time = time.time()
        
        if not self.ocr:
            return ExtractionResult(
                success=False,
                error="PaddleOCR not initialized"
            )
        
        try:
            logger.info(f"Extracting with enhanced PaddleOCR: {image_path}")
            
            # Run OCR
            result = self.ocr.ocr(image_path, cls=True)
            
            if not result or not result[0]:
                return ExtractionResult(
                    success=False,
                    error="No text detected"
                )
            
            logger.info(f"Detected {len(result[0])} text regions")
            
            # Process results with multiple confidence levels
            text_lines_high = self._extract_with_confidence(result[0], threshold=0.6)
            text_lines_med = self._extract_with_confidence(result[0], threshold=0.4)
            text_lines_low = self._extract_with_confidence(result[0], threshold=0.2)
            
            # Try parsing with different confidence levels
            best_result = None
            best_score = 0
            
            for threshold, lines in [
                ('high', text_lines_high),
                ('medium', text_lines_med),
                ('low', text_lines_low)
            ]:
                if not lines:
                    continue
                
                receipt = EnhancedReceiptParser.parse_receipt(lines, extract_items=True)
                score = self._score_result(receipt, lines)
                
                logger.debug(f"Confidence {threshold}: score={score}, lines={len(lines)}")
                
                if score > best_score:
                    best_score = score
                    best_result = receipt
                
                # Early exit for excellent results
                if score >= 80:
                    break
            
            if best_result is None:
                return ExtractionResult(
                    success=False,
                    error="Could not extract valid receipt data"
                )
            
            # Calculate final confidence
            confidence = ConfidenceScorer.score_receipt(best_result)
            
            # Set metadata
            best_result.processing_time = time.time() - start_time
            best_result.model_used = self.model_name
            
            logger.info(f"Extraction complete: score={best_score}, confidence={confidence:.2f}")
            
            return ExtractionResult(
                success=True,
                data=best_result,
                confidence_score=confidence,
                processing_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Enhanced PaddleOCR extraction failed: {e}", exc_info=True)
            return ExtractionResult(
                success=False,
                error=str(e),
                processing_time=time.time() - start_time
            )
    
    def _extract_with_confidence(self, results: List, threshold: float) -> List[str]:
        """Extract text lines with specific confidence threshold."""
        text_lines = []
        
        for line in results:
            if not line or len(line) < 2:
                continue
            
            try:
                bbox = line[0]
                text_info = line[1]
                
                if isinstance(text_info, (tuple, list)) and len(text_info) == 2:
                    text, confidence = text_info
                elif isinstance(text_info, str):
                    text = text_info
                    confidence = 1.0
                else:
                    continue
                
                if confidence >= threshold:
                    text_lines.append(text.strip())
                    
            except Exception as e:
                logger.debug(f"Failed to process line: {e}")
                continue
        
        return text_lines
    
    def _score_result(self, receipt: ReceiptData, text_lines: List[str]) -> int:
        """Score the quality of extraction result."""
        score = 0
        
        # Store name (20 points)
        if receipt.store_name and len(receipt.store_name) > 2:
            score += 20
        
        # Total (25 points)
        if receipt.total and receipt.total > 0:
            score += 25
        
        # Date (10 points)
        if receipt.date:
            score += 10
        
        # Items (25 points)
        if receipt.items:
            if len(receipt.items) > 0:
                score += 15
            if len(receipt.items) >= 3:
                score += 5
            if len(receipt.items) >= 5:
                score += 5
        
        # Subtotal/Tax (10 points)
        if receipt.subtotal:
            score += 5
        if receipt.tax:
            score += 5
        
        # Contact info (10 points)
        if receipt.address:
            score += 5
        if receipt.phone:
            score += 5
        
        # Bonus for text lines
        if len(text_lines) > 10:
            score += 5
        
        return min(score, 100)
