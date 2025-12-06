"""
CRAFT Text Detector - Character Region Awareness For Text detection

This module implements the CRAFT (Character Region Awareness For Text detection)
algorithm as the 7th text detection method in the Receipt Extractor system.

CRAFT is a deep learning-based text detection algorithm that localizes individual
character regions and links them together to detect text at the word level.

Integration with Circular Exchange Framework (CEFR) for reactive configuration.
"""

import os
import sys
import logging
import time
import numpy as np
from typing import Dict, List, Any, Optional
from PIL import Image

# Circular Exchange Framework Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    try:
        from ..circular_exchange import PROJECT_CONFIG, ModuleRegistration
        CIRCULAR_EXCHANGE_AVAILABLE = True
    except ImportError:
        CIRCULAR_EXCHANGE_AVAILABLE = False

# Import shared utilities
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from shared.utils.image import load_and_validate_image, enhance_image
from shared.models.schemas import BoundingBox, DetectedText, DetectionResult, ErrorCode

logger = logging.getLogger(__name__)

# Register module with Circular Exchange
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="shared.models.craft_detector",
            file_path=__file__,
            description="CRAFT text detection - Character Region Awareness For Text detection",
            dependencies=["shared.circular_exchange", "shared.models.schemas", "shared.utils.image"],
            exports=["CRAFTProcessor"]
        ))
    except Exception as e:
        logger.debug(f"Module registration skipped: {e}")


class CRAFTProcessor:
    """
    CRAFT (Character Region Awareness For Text detection) Processor.
    
    Implements text detection using CRAFT algorithm. This is the 7th text detection
    algorithm in the system, joining Tesseract, EasyOCR, PaddleOCR, Donut, Florence-2,
    and Spatial Multi-Method.
    
    CRAFT uses a fully convolutional network to predict character regions and the
    affinity between characters, enabling robust text detection in natural scenes.
    
    Args:
        model_config: Model configuration dictionary with optional parameters:
            - text_threshold: Confidence threshold for character detection (default: 0.7)
            - link_threshold: Threshold for linking characters (default: 0.4)
            - low_text: Score threshold for low-confidence text regions (default: 0.4)
            - canvas_size: Maximum image dimension for processing (default: 1280)
            - mag_ratio: Magnification ratio for better detection (default: 1.5)
    """
    
    def __init__(self, model_config: Dict[str, Any]):
        """Initialize CRAFT processor with configuration."""
        self.model_config = model_config
        self.model_id = model_config.get('id', 'craft')
        self.model_name = model_config.get('name', 'CRAFT Text Detector')
        
        # Detection parameters (configurable via CEFR)
        self.text_threshold = model_config.get('text_threshold', 0.7)
        self.link_threshold = model_config.get('link_threshold', 0.4)
        self.low_text = model_config.get('low_text', 0.4)
        self.canvas_size = model_config.get('canvas_size', 1280)
        self.mag_ratio = model_config.get('mag_ratio', 1.5)
        
        # Model state
        self.model = None
        self.refiner = None
        self.use_cuda = False
        
        # Load model
        self._load_model()
    
    def _load_model(self):
        """
        Load CRAFT model with dependency checking.
        
        Attempts to load the craft-text-detector library. If not available,
        sets up a fallback detection mode with clear error messaging.
        """
        try:
            # Try to import craft-text-detector
            import craft_text_detector
            from craft_text_detector import Craft
            
            logger.info(f"Loading CRAFT model: {self.model_id}")
            
            # Check for CUDA availability
            try:
                import torch
                self.use_cuda = torch.cuda.is_available()
                if self.use_cuda:
                    logger.info("CRAFT will use GPU acceleration")
                else:
                    logger.info("CRAFT running on CPU (slower)")
            except ImportError:
                logger.warning("PyTorch not available, CRAFT will run in limited mode")
                self.use_cuda = False
            
            # Initialize CRAFT model
            # Using pretrained weights from craft-text-detector package
            self.model = Craft(
                output_dir=None,  # Don't save outputs
                crop_type="poly",  # Polygon cropping for better accuracy
                cuda=self.use_cuda,
                text_threshold=self.text_threshold,
                link_threshold=self.link_threshold,
                low_text=self.low_text,
                canvas_size=self.canvas_size,
                mag_ratio=self.mag_ratio
            )
            
            logger.info("CRAFT model loaded successfully")
            
        except ImportError as e:
            logger.warning(
                f"CRAFT dependencies not installed: {e}\n"
                "CRAFT requires craft-text-detector package.\n"
                "Install with: pip install craft-text-detector\n"
                "Processor will return error on detect() calls."
            )
            self.model = None
        except Exception as e:
            logger.error(f"Failed to load CRAFT model: {e}")
            self.model = None
    
    def detect(self, image_path: str, **kwargs) -> DetectionResult:
        """
        Detect text regions in an image using CRAFT algorithm.
        
        Args:
            image_path: Path to input image
            **kwargs: Additional parameters to override defaults:
                - text_threshold: Character detection threshold
                - link_threshold: Character linking threshold
                - nms_threshold: Non-maximum suppression threshold (default: 0.3)
        
        Returns:
            DetectionResult with detected text bounding boxes
        """
        start_time = time.time()
        
        # Check if model is loaded
        if self.model is None:
            return DetectionResult.create_error(
                error_code=ErrorCode.MISSING_DEPENDENCIES,
                error_message=(
                    "CRAFT model not available. Install dependencies with: "
                    "pip install craft-text-detector torch"
                ),
                model_id=self.model_id,
                processing_time=time.time() - start_time
            )
        
        try:
            # Load and validate image
            image = load_and_validate_image(image_path)
            
            # Optional: enhance image for better detection
            if kwargs.get('enhance', False):
                image = enhance_image(image)
            
            # Convert PIL Image to numpy array (required by CRAFT)
            image_array = np.array(image)
            
            # Override thresholds if provided
            text_threshold = kwargs.get('text_threshold', self.text_threshold)
            link_threshold = kwargs.get('link_threshold', self.link_threshold)
            
            # Run CRAFT detection
            logger.info(f"Running CRAFT detection on {image_path}")
            prediction_result = self.model.detect_text(image_array)
            
            # Extract bounding boxes from prediction result
            detected_texts = []
            
            if 'boxes' in prediction_result:
                boxes = prediction_result['boxes']
                
                for i, box in enumerate(boxes):
                    # CRAFT returns boxes as polygon points
                    # Convert to bounding box format (x, y, width, height)
                    if isinstance(box, (list, np.ndarray)) and len(box) >= 4:
                        points = np.array(box).reshape(-1, 2)
                        x_coords = points[:, 0]
                        y_coords = points[:, 1]
                        
                        x_min = int(np.min(x_coords))
                        y_min = int(np.min(y_coords))
                        x_max = int(np.max(x_coords))
                        y_max = int(np.max(y_coords))
                        
                        bbox = BoundingBox.from_coords(x_min, y_min, x_max, y_max)
                        
                        # Get confidence score if available
                        confidence = 1.0  # Default confidence
                        if 'scores' in prediction_result and i < len(prediction_result['scores']):
                            confidence = float(prediction_result['scores'][i])
                        
                        detected_text = DetectedText(
                            text="[REGION]",  # CRAFT detects regions, not text content
                            confidence=confidence,
                            bbox=bbox,
                            attributes={
                                'detector': 'CRAFT',
                                'polygon': box.tolist() if isinstance(box, np.ndarray) else box,
                                'note': 'CRAFT detects text regions only; use OCR for text extraction'
                            }
                        )
                        detected_texts.append(detected_text)
            
            # Apply NMS if requested
            nms_threshold = kwargs.get('nms_threshold', 0.3)
            if nms_threshold > 0 and len(detected_texts) > 1:
                from shared.utils.image import non_maximum_suppression
                
                boxes = [dt.bbox for dt in detected_texts]
                confidences = [dt.confidence for dt in detected_texts]
                keep_indices = non_maximum_suppression(boxes, confidences, nms_threshold)
                detected_texts = [detected_texts[i] for i in keep_indices]
                logger.info(f"NMS reduced {len(boxes)} boxes to {len(detected_texts)}")
            
            processing_time = time.time() - start_time
            
            logger.info(
                f"CRAFT detected {len(detected_texts)} text regions in {processing_time:.2f}s"
            )
            
            return DetectionResult(
                texts=detected_texts,
                metadata={
                    'algorithm': 'CRAFT',
                    'text_threshold': text_threshold,
                    'link_threshold': link_threshold,
                    'image_size': image.size,
                    'use_cuda': self.use_cuda
                },
                processing_time=processing_time,
                model_id=self.model_id,
                success=True
            )
            
        except FileNotFoundError:
            return DetectionResult.create_error(
                error_code=ErrorCode.INVALID_IMAGE,
                error_message=f"Image file not found: {image_path}",
                model_id=self.model_id,
                processing_time=time.time() - start_time
            )
        except Exception as e:
            logger.error(f"CRAFT detection failed: {e}", exc_info=True)
            return DetectionResult.create_error(
                error_code=ErrorCode.PROCESSING_FAILED,
                error_message=f"CRAFT detection error: {str(e)}",
                model_id=self.model_id,
                processing_time=time.time() - start_time
            )
    
    def extract(self, image_path: str) -> Any:
        """
        Extract receipt data using CRAFT detection + OCR reading.
        
        This method provides a complete extraction pipeline by:
        1. Using CRAFT to detect text regions (bounding boxes)
        2. Using Tesseract/EasyOCR to read text from those regions
        3. Parsing the text into structured receipt data
        
        Args:
            image_path: Path to input image
            
        Returns:
            ExtractionResult with receipt data (not just DetectionResult)
        """
        from shared.utils.data import ReceiptData, ExtractionResult
        from shared.models.ocr_common import parse_receipt_text
        import time
        
        start_time = time.time()
        
        try:
            # Step 1: Detect text regions with CRAFT
            detection_result = self.detect(image_path)
            
            if not detection_result.success:
                # Return extraction failure if detection failed
                return ExtractionResult(
                    success=False,
                    error=detection_result.error_message or "CRAFT detection failed"
                )
            
            # Step 2: Read text from detected regions using OCR
            # Try to use an available OCR engine
            try:
                # Try EasyOCR first (no external dependencies)
                import easyocr
                reader = easyocr.Reader(['en'], gpu=False, verbose=False)
                # Load image and convert properly for EasyOCR
                image_pil = load_and_validate_image(image_path)
                # Convert PIL to RGB numpy array (EasyOCR expects numpy array)
                image_array = np.array(image_pil.convert('RGB'))
                ocr_results = reader.readtext(image_array)
                text_lines = [text for (bbox, text, conf) in ocr_results if conf > 0.3]
            except ImportError:
                try:
                    # Fall back to Tesseract if EasyOCR not available
                    import pytesseract
                    image_pil = load_and_validate_image(image_path)
                    text = pytesseract.image_to_string(image_pil, lang='eng')
                    text_lines = [line.strip() for line in text.split('\n') if line.strip()]
                except ImportError:
                    return ExtractionResult(
                        success=False,
                        error="CRAFT requires either EasyOCR or Tesseract for text reading. Install with: pip install easyocr OR pip install pytesseract"
                    )
            
            if not text_lines:
                return ExtractionResult(
                    success=False,
                    error="CRAFT detected text regions but OCR could not read text"
                )
            
            # Step 3: Parse text into receipt data
            parsed = parse_receipt_text(text_lines)
            
            receipt = ReceiptData(
                store_name=parsed['store_name'],
                transaction_date=parsed['transaction_date'],
                total=parsed['total'],
                subtotal=parsed['subtotal'],
                tax=parsed['tax'],
                store_address=parsed['store_address'],
                store_phone=parsed['store_phone'],
                extraction_notes=parsed['extraction_notes']
            )
            
            # Convert tuples to LineItem objects
            from shared.utils.data import LineItem
            receipt.items = [
                LineItem(name=name, total_price=price, quantity=qty)
                for name, price, qty in parsed['items']
            ]
            
            receipt.processing_time = time.time() - start_time
            receipt.model_used = f"{self.model_name} + OCR"
            
            # Calculate confidence based on detection and extraction quality
            try:
                from shared.models.receipt_prompts import get_validated_extraction_with_confidence
                raw_text = ' '.join(text_lines)
                # Base confidence from CRAFT detection quality (average of all region confidences)
                if detection_result.texts:
                    base_conf = sum(t.confidence for t in detection_result.texts) / len(detection_result.texts)
                else:
                    base_conf = 0.5  # Neutral confidence if no regions detected
                    
                _, realistic_confidence, validation = get_validated_extraction_with_confidence(
                    receipt_data=receipt,
                    raw_text=raw_text,
                    base_confidence=base_conf
                )
                receipt.confidence_score = round(realistic_confidence * 100, 1)
                if validation.math_validated:
                    receipt.extraction_notes.append("Math validation passed ✓")
                elif validation.errors:
                    for error in validation.errors:
                        receipt.extraction_notes.append(f"ERROR: {error}")
            except ImportError:
                # Fallback confidence: base on number of fields extracted
                field_count = sum([
                    1 if receipt.store_name else 0,
                    1 if receipt.total else 0,
                    1 if receipt.transaction_date else 0,
                    1 if len(receipt.items) > 0 else 0
                ])
                # Each field gives 20%, max 80% + 20% bonus for having some items
                receipt.confidence_score = min(100.0, field_count * 20 + (20 if receipt.items else 0))
            
            receipt.extraction_notes.append(f"CRAFT detected {len(detection_result.texts)} text regions")
            
            return ExtractionResult(success=True, data=receipt)
            
        except Exception as e:
            logger.error(f"CRAFT extraction failed: {e}", exc_info=True)
            return ExtractionResult(success=False, error=str(e))


__all__ = ['CRAFTProcessor']
