"""
Enhanced Tesseract OCR Processor

This module provides an enhanced version of the Tesseract OCR processor with:
- Multi-strategy text extraction
- Better preprocessing
- Enhanced line item detection
- Improved receipt parsing
- Confidence scoring
"""

import os
import sys
import logging
import time
from typing import Dict, Any, List, Optional
from PIL import Image

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.utils.data import ReceiptData, ExtractionResult
from shared.models.processor_enhancements import (
    EnhancedReceiptParser,
    ConfidenceScorer
)

# Import pytesseract
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    pytesseract = None
    PYTESSERACT_AVAILABLE = False

logger = logging.getLogger(__name__)


class EnhancedTesseractProcessor:
    """
    Enhanced Tesseract OCR processor with comprehensive extraction capabilities.
    
    This processor uses multiple OCR passes with different PSM modes and
    preprocessing strategies to extract maximum text from receipts.
    """
    
    def __init__(self, model_config: Dict[str, Any]):
        """
        Initialize the enhanced Tesseract processor.
        
        Args:
            model_config: Model configuration dictionary
        """
        self.model_config = model_config
        self.model_name = model_config.get('name', 'Enhanced Tesseract OCR')
        
        if not PYTESSERACT_AVAILABLE:
            raise ImportError("pytesseract required: pip install pytesseract")
        
        # Find tesseract executable
        self.tesseract_path = self._find_tesseract()
        if self.tesseract_path and self.tesseract_path != 'tesseract':
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
        
        logger.info(f"Enhanced Tesseract processor initialized")
    
    def _find_tesseract(self) -> Optional[str]:
        """Find Tesseract executable."""
        # Try common locations
        common_paths = [
            'tesseract',
            '/usr/bin/tesseract',
            '/usr/local/bin/tesseract',
            'C:\\Program Files\\Tesseract-OCR\\tesseract.exe',
            'C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe',
        ]
        
        for path in common_paths:
            try:
                import subprocess
                result = subprocess.run(
                    [path, '--version'],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return path
            except:
                continue
        
        return None
    
    def extract(self, image_path: str) -> ExtractionResult:
        """
        Extract receipt data using enhanced Tesseract OCR.
        
        Args:
            image_path: Path to image file
            
        Returns:
            ExtractionResult with extracted data
        """
        start_time = time.time()
        
        if not self.tesseract_path:
            return ExtractionResult(
                success=False,
                error="Tesseract not installed or not found"
            )
        
        try:
            logger.info(f"Extracting with enhanced Tesseract: {image_path}")
            
            # Try multiple PSM modes for best results
            psm_modes = [
                (11, 'Sparse text'),
                (3, 'Fully automatic'),
                (6, 'Uniform block'),
                (4, 'Single column'),
            ]
            
            best_result = None
            best_score = 0
            
            for psm, desc in psm_modes:
                try:
                    # Configure Tesseract
                    config = f'--oem 3 --psm {psm} -c preserve_interword_spaces=1'
                    
                    # Extract text
                    text = pytesseract.image_to_string(
                        image_path,
                        lang='eng',
                        config=config
                    )
                    
                    if not text or len(text.strip()) < 5:
                        continue
                    
                    # Parse receipt
                    text_lines = [line.strip() for line in text.split('\n') if line.strip()]
                    receipt = EnhancedReceiptParser.parse_receipt(text_lines, extract_items=True)
                    
                    # Calculate score
                    score = self._score_result(receipt, text_lines)
                    
                    logger.debug(f"PSM {psm} ({desc}): score={score}, lines={len(text_lines)}")
                    
                    if score > best_score:
                        best_score = score
                        best_result = receipt
                    
                    # Early exit if excellent result
                    if score >= 80:
                        logger.info(f"Excellent result with PSM {psm}, stopping")
                        break
                        
                except Exception as e:
                    logger.debug(f"PSM {psm} failed: {e}")
                    continue
            
            # Check if we got a good result
            if best_result is None:
                return ExtractionResult(
                    success=False,
                    error="No text could be extracted"
                )
            
            # Calculate confidence
            confidence = ConfidenceScorer.score_receipt(best_result)
            
            # Set metadata
            best_result.processing_time = time.time() - start_time
            best_result.model_used = self.model_name
            
            logger.info(f"Extraction complete: score={best_score}, confidence={confidence:.2f}")
            
            return ExtractionResult(
                success=True,
                data=best_result,
                confidence_score=confidence,
                raw_text=None,
                processing_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Enhanced Tesseract extraction failed: {e}", exc_info=True)
            return ExtractionResult(
                success=False,
                error=str(e),
                processing_time=time.time() - start_time
            )
    
    def _score_result(self, receipt: ReceiptData, text_lines: List[str]) -> int:
        """
        Score the quality of extraction result.
        
        Args:
            receipt: Extracted receipt data
            text_lines: Original text lines
            
        Returns:
            Score from 0 to 100
        """
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
        
        # Bonus for text lines (shows good OCR)
        if len(text_lines) > 10:
            score += 5
        
        return min(score, 100)
