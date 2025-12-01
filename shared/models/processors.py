"""
=============================================================================
PROCESSORS MODULE - Enterprise OCR Processing Framework
=============================================================================

This module provides the core OCR processor implementations for the Receipt
Extraction System. It follows the Strategy Pattern to enable interchangeable
processing engines.

Architecture:
    BaseProcessor (Abstract)
    ├── EasyOCRProcessor - High accuracy OCR using EasyOCR
    └── PaddleProcessor - Fast OCR using PaddleOCR

Design Principles:
    - Strategy Pattern: Interchangeable processing algorithms
    - Template Method: Common initialization and health check flow
    - Fail-Fast: Quick validation with clear error messages
    - Retry Logic: Exponential backoff for robustness

=============================================================================
"""

import os
import sys
import re
import logging
import time
from decimal import Decimal
from typing import Dict, List, Optional
from abc import ABC, abstractmethod

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.data_structures import LineItem, ReceiptData, ExtractionResult
from .ocr_common import (
    SKIP_KEYWORDS, PRICE_MIN, PRICE_MAX, normalize_price,
    extract_date, extract_total, extract_phone, extract_address,
    should_skip_line, extract_store_name, LINE_ITEM_PATTERNS, clean_item_name,
    extract_line_items as _extract_line_items_shared,
    parse_receipt_text as _parse_receipt_text_shared,
    get_detection_config, record_detection_result
)

# Conditional imports for optional dependencies
try:
    import easyocr
except ImportError:
    easyocr = None

logger = logging.getLogger(__name__)


# =============================================================================
# EXCEPTION CLASSES
# =============================================================================

class ProcessorInitializationError(Exception):
    """Raised when a processor fails to initialize."""
    pass


class ProcessorHealthCheckError(Exception):
    """Raised when a processor health check fails."""
    pass


# =============================================================================
# BASE PROCESSOR - Abstract Base Class
# =============================================================================

class BaseProcessor(ABC):
    """
    Abstract base class for OCR processors.
    
    Provides common functionality for processor initialization,
    health checks, and status reporting.
    
    Attributes:
        model_config: Configuration dictionary for the model
        model_name: Human-readable name of the model
        model_id: Unique identifier for the model
        initialized: Whether the processor has been initialized
        initialization_error: Error message if initialization failed
        last_health_check: Timestamp of last successful health check
    """

    def __init__(self, model_config: Dict):
        """
        Initialize the base processor.
        
        Args:
            model_config: Configuration dictionary containing model settings
        """
        self.model_config = model_config
        self.model_name = model_config.get('name', 'unknown')
        self.model_id = model_config.get('id', 'unknown')
        self.initialized = False
        self.initialization_error = None
        self.last_health_check = None

    @abstractmethod
    def _load_model(self):
        """Load the underlying model. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def _health_check(self) -> bool:
        """
        Perform health check on the processor.
        
        Returns:
            True if processor is healthy, False otherwise
        """
        pass

    @abstractmethod
    def extract(self, image_path: str) -> 'ExtractionResult':
        """
        Extract receipt data from an image.
        
        Args:
            image_path: Path to the receipt image
            
        Returns:
            ExtractionResult containing the extracted data or error
        """
        pass

    def initialize(self, retry_count: int = 2):
        """
        Initialize the processor with retry logic.
        
        Args:
            retry_count: Number of retry attempts
            
        Raises:
            ProcessorInitializationError: If initialization fails after all retries
        """
        for attempt in range(retry_count + 1):
            try:
                logger.info(f"Initializing {self.model_name} (attempt {attempt + 1}/{retry_count + 1})")
                self._load_model()
                
                if not self._health_check():
                    raise ProcessorInitializationError(
                        f"{self.model_name} loaded but failed health check"
                    )
                
                self.initialized = True
                self.initialization_error = None
                logger.info(f"{self.model_name} initialized successfully")
                return
                
            except Exception as e:
                logger.error(f"Initialization attempt {attempt + 1} failed: {e}")
                self.initialization_error = str(e)
                
                if attempt < retry_count:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    error_msg = (
                        f"Failed to initialize {self.model_name} after "
                        f"{retry_count + 1} attempts. Last error: {e}"
                    )
                    raise ProcessorInitializationError(error_msg) from e

    def ensure_healthy(self):
        """
        Ensure the processor is healthy before use.
        
        Raises:
            ProcessorHealthCheckError: If processor is not healthy
        """
        if not self.initialized:
            raise ProcessorHealthCheckError(
                f"{self.model_name} is not initialized. "
                f"Initialization error: {self.initialization_error}"
            )
        
        if not self._health_check():
            raise ProcessorHealthCheckError(
                f"{self.model_name} health check failed"
            )
        
        self.last_health_check = time.time()

    def get_status(self) -> Dict:
        """
        Get current processor status.
        
        Returns:
            Dictionary containing processor status information
        """
        return {
            'model_name': self.model_name,
            'model_id': self.model_id,
            'initialized': self.initialized,
            'initialization_error': self.initialization_error,
            'last_health_check': self.last_health_check,
            'healthy': self._health_check() if self.initialized else False
        }


# =============================================================================
# EASYOCR PROCESSOR
# =============================================================================

class EasyOCRProcessor:
    """
    OCR processor using EasyOCR library.
    
    EasyOCR provides high accuracy OCR with support for multiple languages.
    It uses deep learning models for text detection and recognition.
    
    Attributes:
        model_config: Configuration dictionary for the model
        model_name: Human-readable name of the model
        reader: EasyOCR Reader instance
    """

    def __init__(self, model_config: Dict):
        """
        Initialize the EasyOCR processor.
        
        Args:
            model_config: Configuration dictionary
            
        Raises:
            ImportError: If EasyOCR is not installed
            RuntimeError: If initialization fails
        """
        self.model_config = model_config
        self.model_name = model_config['name']
        self.reader = None
        
        if easyocr is None:
            raise ImportError("EasyOCR not installed: pip install easyocr")
        
        try:
            logger.info("Initializing EasyOCR...")
            # Set verbose=False to avoid UTF-8 encoding issues with progress bar
            # unicode characters (e.g., '\u2588') in certain environments
            self.reader = easyocr.Reader(['en'], gpu=False, verbose=False)
            logger.info("EasyOCR initialized")
        except Exception as e:
            raise RuntimeError(f"EasyOCR init failed: {e}") from e

    def extract(self, image_path: str) -> ExtractionResult:
        """
        Extract receipt data from an image using EasyOCR.
        
        Uses circular exchange framework for detection configuration with
        lowered default thresholds for improved text detection rates.
        
        Args:
            image_path: Path to the receipt image
            
        Returns:
            ExtractionResult containing extracted data or error
        """
        start_time = time.time()
        
        if easyocr is None:
            return ExtractionResult(success=False, error="EasyOCR not installed")
        
        if self.reader is None:
            return ExtractionResult(success=False, error="EasyOCR reader init failed")
        
        try:
            # Get detection configuration from circular exchange framework
            detection_config = get_detection_config()
            min_confidence = detection_config.get('min_confidence', 0.25)
            
            logger.info(f"EasyOCR: {image_path} (detection threshold: {min_confidence})")
            results = self.reader.readtext(image_path)
            logger.info(f"Detected {len(results)} regions")
            
            # Extract text with configurable confidence filtering
            text_lines = []
            total_confidence = 0.0
            for detection in results:
                if len(detection) >= 3:
                    bbox, text, confidence = detection[0], detection[1], detection[2]
                    if confidence > min_confidence:
                        text_lines.append(text)
                        total_confidence += confidence
            
            # Calculate average confidence for detection tracking
            avg_confidence = total_confidence / max(len(text_lines), 1)
            
            # Record detection result for auto-tuning
            record_detection_result(
                text_regions_count=len(text_lines),
                avg_confidence=avg_confidence,
                success=len(text_lines) > 0,
                processing_time=time.time() - start_time
            )
            
            if not text_lines:
                # Try with even lower threshold if auto-retry is enabled
                if detection_config.get('auto_retry', True):
                    logger.info("No text detected, retrying with lower threshold...")
                    lower_threshold = min_confidence * 0.5
                    for detection in results:
                        if len(detection) >= 3:
                            bbox, text, confidence = detection[0], detection[1], detection[2]
                            if confidence > lower_threshold:
                                text_lines.append(text)
                
                if not text_lines:
                    return ExtractionResult(success=False, error="No text detected")
            
            # Parse receipt data
            receipt = self._parse_receipt_text(text_lines)
            receipt.processing_time = time.time() - start_time
            receipt.model_used = self.model_name
            
            return ExtractionResult(success=True, data=receipt)
            
        except Exception as e:
            logger.error(f"EasyOCR failed: {e}", exc_info=True)
            return ExtractionResult(success=False, error=str(e))

    def _parse_receipt_text(self, text_lines: List[str]) -> ReceiptData:
        """
        Parse raw text lines into structured receipt data.
        
        Args:
            text_lines: List of text lines from OCR
            
        Returns:
            ReceiptData object with parsed information
        """
        receipt = ReceiptData()
        
        if not text_lines:
            receipt.extraction_notes.append("No text")
            return receipt
        
        # Use shared implementation
        parsed = _parse_receipt_text_shared(text_lines)
        receipt.store_name = parsed['store_name']
        receipt.transaction_date = parsed['transaction_date']
        receipt.total = parsed['total']
        receipt.subtotal = parsed['subtotal']
        receipt.tax = parsed['tax']
        # Convert tuples to LineItem objects
        receipt.items = [LineItem(name=name, total_price=price, quantity=qty) for name, price, qty in parsed['items']]
        receipt.store_address = parsed['store_address']
        receipt.store_phone = parsed['store_phone']
        receipt.extraction_notes = parsed['extraction_notes']
        
        return receipt

    def _extract_line_items(self, lines: List[str]) -> List[LineItem]:
        """
        Extract line items from text lines.
        
        Args:
            lines: List of text lines
            
        Returns:
            List of LineItem objects
        """
        # Use shared implementation and convert tuples to LineItem objects
        items_data = _extract_line_items_shared(lines)
        return [LineItem(name=name, total_price=price, quantity=qty) for name, price, qty in items_data]


# =============================================================================
# PADDLE OCR PROCESSOR
# =============================================================================

import numpy as np
from PIL import Image
from utils.image_processing import load_and_validate_image, preprocess_for_ocr

# Lazy import to allow mocking in tests
PaddleOCR = None


def _get_paddleocr():
    """
    Lazy load PaddleOCR to allow mocking in tests.
    
    Returns:
        PaddleOCR class
        
    Raises:
        ImportError: If paddleocr is not installed
    """
    global PaddleOCR
    if PaddleOCR is None:
        try:
            from paddleocr import PaddleOCR as _PaddleOCR
            PaddleOCR = _PaddleOCR
        except ImportError:
            raise ImportError("paddleocr required: pip install paddleocr")
    return PaddleOCR


class PaddleProcessor:
    """
    OCR processor using PaddleOCR library with circular exchange integration.
    
    PaddleOCR provides fast and accurate OCR with angle detection
    and multi-language support. Detection parameters are dynamically
    managed via the circular exchange framework for automatic tuning.
    
    Attributes:
        model_config: Configuration dictionary for the model
        model_name: Human-readable name of the model
        ocr: PaddleOCR instance
    """

    def __init__(self, model_config: Dict):
        """
        Initialize the PaddleOCR processor with circular exchange integration.
        
        Uses detection configuration from circular exchange framework for
        lowered default thresholds to improve text detection rates.
        
        Args:
            model_config: Configuration dictionary
            
        Raises:
            ImportError: If PaddleOCR is not installed
        """
        self.model_config = model_config
        self.model_name = model_config['name']
        
        # Get detection configuration from circular exchange framework
        detection_config = get_detection_config()
        use_angle_cls = detection_config.get('use_angle_cls', True)
        box_threshold = detection_config.get('box_threshold', 0.3)
        
        logger.info(f"Initializing PaddleOCR with box_threshold={box_threshold}")
        try:
            PaddleOCR = _get_paddleocr()
            self.ocr = PaddleOCR(
                use_angle_cls=use_angle_cls,
                lang='en',
                det_db_thresh=0.2,  # Lower threshold for better text region detection
                det_db_box_thresh=box_threshold
            )
            logger.info("PaddleOCR initialized with circular exchange config")
        except Exception as e:
            logger.error(f"PaddleOCR init failed: {e}")
            raise

    def extract(self, image_path: str) -> ExtractionResult:
        """
        Extract receipt data from an image using PaddleOCR.
        
        Uses circular exchange framework for detection configuration with
        lowered default thresholds for improved text detection rates.
        
        Args:
            image_path: Path to the receipt image
            
        Returns:
            ExtractionResult containing extracted data or error
        """
        start_time = time.time()
        
        try:
            # Get detection configuration from circular exchange framework
            detection_config = get_detection_config()
            min_confidence = detection_config.get('min_confidence', 0.25)
            auto_retry = detection_config.get('auto_retry', True)
            
            # Load and preprocess image
            image = load_and_validate_image(image_path)
            preprocessed = preprocess_for_ocr(image, aggressive=True)
            image_np = np.array(preprocessed)
            
            # Convert grayscale to RGB if needed
            if len(image_np.shape) == 2:
                image_np = np.stack([image_np] * 3, axis=-1)
                logger.info(f"Converted grayscale to RGB: {image_np.shape}")
            
            # Run OCR
            logger.info(f"Running PaddleOCR extraction (threshold: {min_confidence})...")
            result = self.ocr.ocr(image_np)
            logger.info(f"Result type:{type(result)}, len:{len(result) if result else 0}")
            
            if result and len(result) > 0:
                logger.info(f"First elem: type={type(result[0])}, len={len(result[0]) if result[0] else 0}")
            
            # Retry with original image if no results and auto_retry is enabled
            if (not result or not result[0]) and auto_retry:
                logger.warning("No results, retrying with original image")
                image_np = np.array(image)
                result = self.ocr.ocr(image_np)
            
            if not result or not result[0]:
                logger.warning("PaddleOCR: no text detected")
                # Record failed detection for auto-tuning
                record_detection_result(
                    text_regions_count=0,
                    avg_confidence=0.0,
                    success=False,
                    processing_time=time.time() - start_time
                )
                return ExtractionResult(success=False, error="No text detected")

            # Parse OCR results with configurable confidence filtering
            text_lines = []
            total_confidence = 0.0
            for line in result[0]:
                if not line or len(line) < 2:
                    continue
                
                try:
                    bbox = line[0]
                    text_info = line[1]
                    
                    if not isinstance(bbox, (list, tuple)) or len(bbox) < 1:
                        continue
                    
                    if isinstance(text_info, (tuple, list)) and len(text_info) == 2:
                        text, confidence = text_info
                    elif isinstance(text_info, str):
                        text = text_info
                        confidence = 1.0
                    else:
                        continue
                    
                    # Use configurable confidence threshold from circular exchange
                    if confidence > min_confidence:
                        text_lines.append({
                            'text': text,
                            'confidence': confidence,
                            'bbox': bbox
                        })
                        total_confidence += confidence
                        
                except (ValueError, TypeError, IndexError):
                    continue
            
            # Calculate average confidence for detection tracking
            avg_confidence = total_confidence / max(len(text_lines), 1)
            
            # Record detection result for auto-tuning
            record_detection_result(
                text_regions_count=len(text_lines),
                avg_confidence=avg_confidence,
                success=len(text_lines) > 0,
                processing_time=time.time() - start_time
            )
            
            # Sort by Y coordinate
            def safe_get_y(d):
                try:
                    bbox = d['bbox']
                    if isinstance(bbox, (list, tuple)) and len(bbox) > 0:
                        fp = bbox[0]
                        if isinstance(fp, (list, tuple)) and len(fp) > 1:
                            return fp[1]
                    return 0
                except (KeyError, TypeError, IndexError):
                    return 0
            
            text_lines = sorted(text_lines, key=safe_get_y)
            logger.info(f"Detected {len(text_lines)} lines")
            
            # Parse receipt data
            receipt = self._parse_receipt_text(text_lines)
            receipt.processing_time = time.time() - start_time
            receipt.model_used = self.model_name
            
            if text_lines:
                receipt.confidence_score = round(
                    sum(l['confidence'] for l in text_lines) / len(text_lines), 2
                )
            
            return ExtractionResult(success=True, data=receipt)
            
        except Exception as e:
            logger.error(f"Extraction failed: {e}", exc_info=True)
            return ExtractionResult(success=False, error=str(e))

    def _parse_receipt_text(self, text_lines: List[Dict]) -> ReceiptData:
        """
        Parse raw text lines into structured receipt data.
        
        Args:
            text_lines: List of dictionaries with text and metadata
            
        Returns:
            ReceiptData object with parsed information
        """
        receipt = ReceiptData()
        
        if not text_lines:
            receipt.extraction_notes.append("No text")
            return receipt
        
        lines = [l['text'].strip() for l in text_lines]
        
        # Use shared implementation with text metadata for confidence filtering
        parsed = _parse_receipt_text_shared(lines, text_lines)
        receipt.store_name = parsed['store_name']
        if receipt.store_name and len(receipt.store_name) < 2:
            receipt.extraction_notes.append(f"Short name: '{receipt.store_name}'")
        
        receipt.transaction_date = parsed['transaction_date']
        if receipt.transaction_date:
            logger.info(f"Date: {receipt.transaction_date}")
        
        receipt.total = parsed['total']
        if receipt.total:
            logger.info(f"Total: {receipt.total}")
        
        receipt.subtotal = parsed['subtotal']
        receipt.tax = parsed['tax']
        
        # Convert tuples to LineItem objects
        receipt.items = [LineItem(name=name, total_price=price, quantity=qty) for name, price, qty in parsed['items']]
        
        receipt.store_address = parsed['store_address']
        if receipt.store_address:
            logger.info(f"Address: {receipt.store_address}")
        
        receipt.store_phone = parsed['store_phone']
        if receipt.store_phone:
            logger.info(f"Phone: {receipt.store_phone}")
        
        receipt.extraction_notes.extend(parsed['extraction_notes'])
        
        return receipt

    def _extract_line_items(
        self, 
        lines: List[str], 
        text_lines: List[Dict]
    ) -> List[LineItem]:
        """
        Extract line items from text lines.
        
        Args:
            lines: List of text strings
            text_lines: List of dictionaries with text and confidence
            
        Returns:
            List of LineItem objects
        """
        # Use shared implementation with metadata for confidence filtering
        items_data = _extract_line_items_shared(lines, text_lines)
        logger.info(f"Extracted {len(items_data)} items")
        return [LineItem(name=name, total_price=price, quantity=qty) for name, price, qty in items_data]
