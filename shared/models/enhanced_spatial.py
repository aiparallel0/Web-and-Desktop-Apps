"""
Enhanced Spatial OCR Processors

Provides spatial analysis and multi-method OCR extraction with:
- Coordinate-based text ordering
- Spatial relationship analysis
- Multi-engine consensus extraction
- Enhanced column detection
"""

import os
import sys
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.utils.data import ReceiptData, LineItem, ExtractionResult
from shared.models.processor_enhancements import (
    EnhancedReceiptParser,
    ConfidenceScorer,
    EnhancedLineItemExtractor
)

# Import OCR engines
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    easyocr = None
    EASYOCR_AVAILABLE = False

try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PaddleOCR = None
    PADDLEOCR_AVAILABLE = False

logger = logging.getLogger(__name__)


class SpatialTextAnalyzer:
    """Analyzes spatial relationships between text regions."""
    
    @staticmethod
    def order_by_reading_order(text_regions: List[Dict]) -> List[Dict]:
        """
        Order text regions in reading order (top-to-bottom, left-to-right).
        
        Args:
            text_regions: List of dicts with 'bbox' and 'text' keys
            
        Returns:
            Ordered list of text regions
        """
        if not text_regions:
            return []
        
        # Sort by vertical position first, then horizontal
        def get_sort_key(region):
            bbox = region['bbox']
            if isinstance(bbox, (list, tuple)) and len(bbox) >= 2:
                # Handle different bbox formats
                if isinstance(bbox[0], (list, tuple)):
                    # Format: [[x1, y1], [x2, y2], ...]
                    y = bbox[0][1]
                    x = bbox[0][0]
                else:
                    # Format: [x, y, width, height]
                    y = bbox[1] if len(bbox) > 1 else 0
                    x = bbox[0] if len(bbox) > 0 else 0
            else:
                y, x = 0, 0
            
            # Group by vertical position (with some tolerance)
            y_group = int(y / 20) * 20  # Group lines within 20 pixels
            return (y_group, x)
        
        try:
            ordered = sorted(text_regions, key=get_sort_key)
            return ordered
        except Exception as e:
            logger.error(f"Error ordering text regions: {e}")
            return text_regions
    
    @staticmethod
    def detect_columns(text_regions: List[Dict], min_gap: int = 50) -> List[List[Dict]]:
        """
        Detect text columns based on spatial distribution.
        
        Args:
            text_regions: List of text regions with bbox
            min_gap: Minimum horizontal gap to consider as column separator
            
        Returns:
            List of columns, each column is a list of text regions
        """
        if not text_regions:
            return []
        
        try:
            # Get x-coordinates of all regions
            x_coords = []
            for region in text_regions:
                bbox = region['bbox']
                if isinstance(bbox, (list, tuple)) and len(bbox) >= 1:
                    if isinstance(bbox[0], (list, tuple)):
                        x = bbox[0][0]
                    else:
                        x = bbox[0]
                    x_coords.append((x, region))
            
            if not x_coords:
                return [text_regions]
            
            # Sort by x-coordinate
            x_coords.sort(key=lambda t: t[0])
            
            # Detect column boundaries
            columns = []
            current_column = [x_coords[0][1]]
            last_x = x_coords[0][0]
            
            for x, region in x_coords[1:]:
                if x - last_x > min_gap:
                    # New column
                    columns.append(current_column)
                    current_column = [region]
                else:
                    current_column.append(region)
                last_x = x
            
            if current_column:
                columns.append(current_column)
            
            return columns if len(columns) > 1 else [text_regions]
            
        except Exception as e:
            logger.error(f"Error detecting columns: {e}")
            return [text_regions]
    
    @staticmethod
    def group_by_proximity(text_regions: List[Dict], max_distance: int = 30) -> List[List[Dict]]:
        """
        Group text regions that are close together.
        
        Args:
            text_regions: List of text regions
            max_distance: Maximum distance to group together
            
        Returns:
            List of groups
        """
        if not text_regions:
            return []
        
        groups = []
        used = set()
        
        for i, region1 in enumerate(text_regions):
            if i in used:
                continue
            
            group = [region1]
            used.add(i)
            
            for j, region2 in enumerate(text_regions):
                if j in used:
                    continue
                
                # Calculate distance between regions
                distance = SpatialTextAnalyzer._calculate_distance(
                    region1['bbox'],
                    region2['bbox']
                )
                
                if distance < max_distance:
                    group.append(region2)
                    used.add(j)
            
            groups.append(group)
        
        return groups
    
    @staticmethod
    def _calculate_distance(bbox1, bbox2) -> float:
        """Calculate distance between two bounding boxes."""
        try:
            # Get center points
            if isinstance(bbox1[0], (list, tuple)):
                x1 = sum(p[0] for p in bbox1) / len(bbox1)
                y1 = sum(p[1] for p in bbox1) / len(bbox1)
            else:
                x1, y1 = bbox1[0], bbox1[1]
            
            if isinstance(bbox2[0], (list, tuple)):
                x2 = sum(p[0] for p in bbox2) / len(bbox2)
                y2 = sum(p[1] for p in bbox2) / len(bbox2)
            else:
                x2, y2 = bbox2[0], bbox2[1]
            
            # Euclidean distance
            return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
            
        except Exception as e:
            logger.debug(f"Error calculating distance: {e}")
            return float('inf')


class EnhancedEasyOCRSpatialProcessor:
    """Enhanced EasyOCR with spatial analysis."""
    
    def __init__(self, model_config: Dict[str, Any]):
        """Initialize enhanced EasyOCR spatial processor."""
        self.model_config = model_config
        self.model_name = model_config.get('name', 'Enhanced EasyOCR Spatial')
        self.reader = None
        
        if not EASYOCR_AVAILABLE:
            raise ImportError("EasyOCR not installed: pip install easyocr")
        
        try:
            logger.info("Initializing Enhanced EasyOCR Spatial...")
            self.reader = easyocr.Reader(['en'], gpu=False, verbose=False)
            logger.info("Enhanced EasyOCR Spatial initialized")
        except Exception as e:
            raise RuntimeError(f"EasyOCR initialization failed: {e}") from e
    
    def extract(self, image_path: str) -> ExtractionResult:
        """Extract with spatial analysis."""
        start_time = time.time()
        
        if not self.reader:
            return ExtractionResult(
                success=False,
                error="EasyOCR reader not initialized"
            )
        
        try:
            logger.info(f"Extracting with enhanced EasyOCR Spatial: {image_path}")
            
            # Read text with bounding boxes
            results = self.reader.readtext(image_path)
            
            if not results:
                return ExtractionResult(
                    success=False,
                    error="No text detected"
                )
            
            logger.info(f"Detected {len(results)} text regions")
            
            # Convert to spatial text regions
            text_regions = []
            for detection in results:
                if len(detection) >= 3:
                    bbox, text, confidence = detection[0], detection[1], detection[2]
                    if confidence >= 0.3:  # Filter low confidence
                        text_regions.append({
                            'bbox': bbox,
                            'text': text.strip(),
                            'confidence': confidence
                        })
            
            # Apply spatial analysis
            ordered_regions = SpatialTextAnalyzer.order_by_reading_order(text_regions)
            
            # Detect columns
            columns = SpatialTextAnalyzer.detect_columns(ordered_regions)
            logger.info(f"Detected {len(columns)} column(s)")
            
            # Extract text lines in order
            text_lines = []
            for column in columns:
                for region in column:
                    text_lines.append(region['text'])
            
            # Parse receipt
            receipt = EnhancedReceiptParser.parse_receipt(text_lines, extract_items=True)
            
            # Add spatial metadata
            receipt.model_used = self.model_name
            receipt.processing_time = time.time() - start_time
            
            # Calculate confidence
            confidence = ConfidenceScorer.score_receipt(receipt)
            
            logger.info(f"Spatial extraction complete: confidence={confidence:.2f}")
            
            return ExtractionResult(
                success=True,
                data=receipt,
                confidence_score=confidence,
                processing_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Enhanced EasyOCR Spatial extraction failed: {e}", exc_info=True)
            return ExtractionResult(
                success=False,
                error=str(e),
                processing_time=time.time() - start_time
            )


class EnhancedPaddleOCRSpatialProcessor:
    """Enhanced PaddleOCR with spatial analysis."""
    
    def __init__(self, model_config: Dict[str, Any]):
        """Initialize enhanced PaddleOCR spatial processor."""
        self.model_config = model_config
        self.model_name = model_config.get('name', 'Enhanced PaddleOCR Spatial')
        self.ocr = None
        
        if not PADDLEOCR_AVAILABLE:
            raise ImportError("PaddleOCR not installed: pip install paddleocr")
        
        try:
            logger.info("Initializing Enhanced PaddleOCR Spatial...")
            self.ocr = PaddleOCR(
                use_angle_cls=True,
                lang='en',
                det_db_thresh=0.2,
                det_db_box_thresh=0.3,
                show_log=False
            )
            logger.info("Enhanced PaddleOCR Spatial initialized")
        except Exception as e:
            raise RuntimeError(f"PaddleOCR initialization failed: {e}") from e
    
    def extract(self, image_path: str) -> ExtractionResult:
        """Extract with spatial analysis."""
        start_time = time.time()
        
        if not self.ocr:
            return ExtractionResult(
                success=False,
                error="PaddleOCR not initialized"
            )
        
        try:
            logger.info(f"Extracting with enhanced PaddleOCR Spatial: {image_path}")
            
            # Run OCR
            result = self.ocr.ocr(image_path, cls=True)
            
            if not result or not result[0]:
                return ExtractionResult(
                    success=False,
                    error="No text detected"
                )
            
            logger.info(f"Detected {len(result[0])} text regions")
            
            # Convert to spatial text regions
            text_regions = []
            for line in result[0]:
                if not line or len(line) < 2:
                    continue
                
                try:
                    bbox = line[0]
                    text_info = line[1]
                    
                    if isinstance(text_info, (tuple, list)) and len(text_info) == 2:
                        text, confidence = text_info
                    else:
                        text = str(text_info)
                        confidence = 1.0
                    
                    if confidence >= 0.3:
                        text_regions.append({
                            'bbox': bbox,
                            'text': text.strip(),
                            'confidence': confidence
                        })
                        
                except Exception as e:
                    logger.debug(f"Failed to process line: {e}")
                    continue
            
            # Apply spatial analysis
            ordered_regions = SpatialTextAnalyzer.order_by_reading_order(text_regions)
            
            # Detect columns
            columns = SpatialTextAnalyzer.detect_columns(ordered_regions)
            logger.info(f"Detected {len(columns)} column(s)")
            
            # Extract text lines in order
            text_lines = []
            for column in columns:
                for region in column:
                    text_lines.append(region['text'])
            
            # Parse receipt
            receipt = EnhancedReceiptParser.parse_receipt(text_lines, extract_items=True)
            
            # Add spatial metadata
            receipt.model_used = self.model_name
            receipt.processing_time = time.time() - start_time
            
            # Calculate confidence
            confidence = ConfidenceScorer.score_receipt(receipt)
            
            logger.info(f"Spatial extraction complete: confidence={confidence:.2f}")
            
            return ExtractionResult(
                success=True,
                data=receipt,
                confidence_score=confidence,
                processing_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Enhanced PaddleOCR Spatial extraction failed: {e}", exc_info=True)
            return ExtractionResult(
                success=False,
                error=str(e),
                processing_time=time.time() - start_time
            )
