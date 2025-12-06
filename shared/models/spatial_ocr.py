"""
Multi-Method OCR with Spatial Bounding Box Analysis

This module provides advanced OCR capabilities by:
- Combining results from multiple OCR engines (Tesseract, EasyOCR, PaddleOCR)
- Analyzing spatial relationships between text regions using bounding boxes
- Using geometric analysis to improve accuracy and structure understanding
- Resolving conflicts between OCR engines using spatial consensus

The spatial analysis helps with:
- Identifying line items that are vertically aligned
- Detecting table structures in receipts
- Improving text region association (e.g., prices with items)
- Filtering OCR artifacts by spatial consistency
"""

import logging
import re
from decimal import Decimal
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from collections import defaultdict
import numpy as np

# Circular Exchange Framework Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False

from shared.utils.data import LineItem, ReceiptData, ExtractionResult

# Import ocr_common parsing functions
try:
    from .ocr_common import parse_receipt_text as _parse_receipt_text_shared
    OCR_COMMON_AVAILABLE = True
except ImportError:
    OCR_COMMON_AVAILABLE = False

logger = logging.getLogger(__name__)

# Source priority for conflict resolution when merging overlapping regions
# Higher values indicate higher priority/reliability
SOURCE_PRIORITY = {
    'easyocr': 3,      # Highest priority - typically most accurate
    'tesseract': 2,    # Medium priority - good for standard text
    'paddleocr': 1,    # Lower priority - but still useful
}

# Register module with Circular Exchange
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="shared.models.spatial_ocr",
            file_path=__file__,
            description="Multi-method OCR with spatial bounding box analysis for improved accuracy",
            dependencies=["shared.models.ocr_processor", "shared.utils.data"],
            exports=["SpatialOCRProcessor", "BoundingBox", "TextRegion", "SpatialAnalyzer"]
        ))
    except Exception:
        pass


@dataclass
class BoundingBox:
    """Represents a bounding box for a text region."""
    x: float  # Left coordinate
    y: float  # Top coordinate
    width: float  # Width
    height: float  # Height
    
    @property
    def x2(self) -> float:
        """Right coordinate."""
        return self.x + self.width
    
    @property
    def y2(self) -> float:
        """Bottom coordinate."""
        return self.y + self.height
    
    @property
    def center_x(self) -> float:
        """Horizontal center."""
        return self.x + self.width / 2
    
    @property
    def center_y(self) -> float:
        """Vertical center."""
        return self.y + self.height / 2
    
    @property
    def area(self) -> float:
        """Area of the bounding box."""
        return self.width * self.height
    
    def iou(self, other: 'BoundingBox') -> float:
        """
        Calculate Intersection over Union (IoU) with another bounding box.
        
        Args:
            other: Another bounding box
            
        Returns:
            IoU score (0.0 to 1.0)
        """
        # Calculate intersection
        x_left = max(self.x, other.x)
        y_top = max(self.y, other.y)
        x_right = min(self.x2, other.x2)
        y_bottom = min(self.y2, other.y2)
        
        if x_right < x_left or y_bottom < y_top:
            return 0.0
        
        intersection = (x_right - x_left) * (y_bottom - y_top)
        union = self.area + other.area - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def overlaps(self, other: 'BoundingBox', threshold: float = 0.1) -> bool:
        """Check if this box overlaps with another box."""
        return self.iou(other) > threshold
    
    def horizontal_distance(self, other: 'BoundingBox') -> float:
        """Calculate horizontal distance between box centers."""
        return abs(self.center_x - other.center_x)
    
    def vertical_distance(self, other: 'BoundingBox') -> float:
        """Calculate vertical distance between box centers."""
        return abs(self.center_y - other.center_y)
    
    def is_aligned_horizontally(self, other: 'BoundingBox', tolerance: float = 5.0) -> bool:
        """Check if boxes are horizontally aligned (same row)."""
        return self.vertical_distance(other) < tolerance
    
    def is_aligned_vertically(self, other: 'BoundingBox', tolerance: float = 5.0) -> bool:
        """Check if boxes are vertically aligned (same column)."""
        return self.horizontal_distance(other) < tolerance


@dataclass
class TextRegion:
    """Represents a text region with spatial information."""
    text: str
    bbox: BoundingBox
    confidence: float
    source: str  # Which OCR engine detected this region
    
    def __repr__(self) -> str:
        return f"TextRegion('{self.text[:20]}...', conf={self.confidence:.2f}, src={self.source})"


class SpatialAnalyzer:
    """Analyzes spatial relationships between text regions."""
    
    def __init__(self):
        """Initialize the spatial analyzer."""
        self.regions: List[TextRegion] = []
    
    def add_region(self, region: TextRegion):
        """Add a text region for analysis."""
        self.regions.append(region)
    
    def add_regions(self, regions: List[TextRegion]):
        """Add multiple text regions."""
        self.regions.extend(regions)
    
    def find_aligned_regions(self, region: TextRegion, 
                            orientation: str = 'horizontal',
                            tolerance: float = 5.0) -> List[TextRegion]:
        """
        Find regions aligned with the given region.
        
        Args:
            region: Reference text region
            orientation: 'horizontal' for same row, 'vertical' for same column
            tolerance: Alignment tolerance in pixels
            
        Returns:
            List of aligned regions
        """
        aligned = []
        
        for other in self.regions:
            if other == region:
                continue
            
            if orientation == 'horizontal':
                if region.bbox.is_aligned_horizontally(other.bbox, tolerance):
                    aligned.append(other)
            elif orientation == 'vertical':
                if region.bbox.is_aligned_vertically(other.bbox, tolerance):
                    aligned.append(other)
        
        return aligned
    
    def group_by_rows(self, tolerance: float = 5.0) -> List[List[TextRegion]]:
        """
        Group text regions into rows based on vertical alignment.
        
        Args:
            tolerance: Vertical alignment tolerance in pixels
            
        Returns:
            List of rows, where each row is a list of aligned regions
        """
        if not self.regions:
            return []
        
        # Sort regions by vertical position
        sorted_regions = sorted(self.regions, key=lambda r: r.bbox.center_y)
        
        rows = []
        current_row = [sorted_regions[0]]
        
        for region in sorted_regions[1:]:
            # Check if this region aligns with the current row
            if region.bbox.is_aligned_horizontally(current_row[0].bbox, tolerance):
                current_row.append(region)
            else:
                # Start a new row
                rows.append(sorted(current_row, key=lambda r: r.bbox.center_x))
                current_row = [region]
        
        # Add the last row
        if current_row:
            rows.append(sorted(current_row, key=lambda r: r.bbox.center_x))
        
        return rows
    
    def merge_overlapping_regions(self, iou_threshold: float = 0.5) -> List[TextRegion]:
        """
        Merge overlapping text regions, keeping the one with higher confidence.
        
        Args:
            iou_threshold: IoU threshold for considering regions as duplicates
            
        Returns:
            List of merged regions
        """
        if not self.regions:
            return []
        
        # Sort by confidence (descending)
        sorted_regions = sorted(self.regions, key=lambda r: r.confidence, reverse=True)
        
        merged = []
        used = set()
        
        for i, region in enumerate(sorted_regions):
            if i in used:
                continue
            
            # Check for overlapping regions
            overlaps = []
            for j, other in enumerate(sorted_regions[i + 1:], start=i + 1):
                if j in used:
                    continue
                
                if region.bbox.iou(other.bbox) > iou_threshold:
                    overlaps.append((j, other))
            
            # If we have overlaps, take the best one based on confidence and source
            if overlaps:
                # Use global source priority mapping
                candidates = [(i, region)] + overlaps
                best = max(candidates, key=lambda x: (
                    x[1].confidence * 0.7 + 
                    SOURCE_PRIORITY.get(x[1].source, 0) * 0.3
                ))
                
                merged.append(best[1])
                used.add(best[0])
                for idx, _ in overlaps:
                    used.add(idx)
            else:
                merged.append(region)
                used.add(i)
        
        return merged
    
    def extract_structured_text(self) -> List[str]:
        """
        Extract text in reading order using spatial analysis.
        
        Returns:
            List of text lines in reading order
        """
        # Group by rows
        rows = self.group_by_rows()
        
        # Extract text from each row
        lines = []
        for row in rows:
            # Concatenate text from left to right
            line_text = ' '.join(region.text for region in row)
            lines.append(line_text.strip())
        
        return lines


class SpatialOCRProcessor:
    """
    Multi-method OCR processor with spatial bounding box analysis.
    
    This processor combines results from multiple OCR engines and uses
    spatial analysis to improve accuracy and structure understanding.
    """
    
    def __init__(self, ocr_engines: Optional[List[Any]] = None):
        """
        Initialize the spatial OCR processor.
        
        Args:
            ocr_engines: List of OCR engine instances to use.
                        If None, will attempt to initialize available engines.
        """
        self.ocr_engines = ocr_engines or []
        self.analyzer = SpatialAnalyzer()
        
        # Initialize availability flags
        self.has_tesseract = False
        self.has_easyocr = False
        self.has_paddleocr = False
        
        # Initialize engines if not provided
        if not self.ocr_engines:
            self._initialize_engines()
    
    def _initialize_engines(self):
        """Initialize available OCR engines."""
        # Try to import and initialize Tesseract
        try:
            import pytesseract
            from PIL import Image
            self.has_tesseract = True
            logger.info("Tesseract OCR available")
        except ImportError:
            self.has_tesseract = False
            logger.warning("Tesseract OCR not available")
        
        # Try to import EasyOCR
        try:
            import easyocr
            self.has_easyocr = True
            logger.info("EasyOCR available")
        except ImportError:
            self.has_easyocr = False
            logger.warning("EasyOCR not available")
        
        # Try to import PaddleOCR
        try:
            from paddleocr import PaddleOCR
            self.has_paddleocr = True
            logger.info("PaddleOCR available")
        except ImportError:
            self.has_paddleocr = False
            logger.warning("PaddleOCR not available")
    
    def extract_with_tesseract(self, image_path: str) -> List[TextRegion]:
        """
        Extract text regions using Tesseract with bounding box information.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            List of text regions with bounding boxes
        """
        if not self.has_tesseract:
            return []
        
        try:
            import pytesseract
            from PIL import Image
            
            image = Image.open(image_path)
            
            # Use image_to_data to get bounding box information
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            regions = []
            n_boxes = len(data['text'])
            
            for i in range(n_boxes):
                text = data['text'][i].strip()
                
                # Skip empty text
                if not text or data['conf'][i] < 0:
                    continue
                
                # Create bounding box
                bbox = BoundingBox(
                    x=float(data['left'][i]),
                    y=float(data['top'][i]),
                    width=float(data['width'][i]),
                    height=float(data['height'][i])
                )
                
                # Create text region
                region = TextRegion(
                    text=text,
                    bbox=bbox,
                    confidence=float(data['conf'][i]) / 100.0,  # Convert to 0-1 range
                    source='tesseract'
                )
                
                regions.append(region)
            
            logger.info(f"Tesseract extracted {len(regions)} text regions")
            return regions
            
        except Exception as e:
            logger.error(f"Tesseract extraction failed: {e}")
            return []
    
    def extract_with_easyocr(self, image_path: str) -> List[TextRegion]:
        """
        Extract text regions using EasyOCR with bounding box information.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            List of text regions with bounding boxes
        """
        if not self.has_easyocr:
            return []
        
        try:
            import easyocr
            
            reader = easyocr.Reader(['en'], gpu=False)
            results = reader.readtext(image_path)
            
            regions = []
            
            for bbox_points, text, confidence in results:
                # EasyOCR returns 4 corner points, convert to x, y, width, height
                xs = [p[0] for p in bbox_points]
                ys = [p[1] for p in bbox_points]
                
                x = min(xs)
                y = min(ys)
                width = max(xs) - x
                height = max(ys) - y
                
                bbox = BoundingBox(x=x, y=y, width=width, height=height)
                
                region = TextRegion(
                    text=text,
                    bbox=bbox,
                    confidence=confidence,
                    source='easyocr'
                )
                
                regions.append(region)
            
            logger.info(f"EasyOCR extracted {len(regions)} text regions")
            return regions
            
        except Exception as e:
            logger.error(f"EasyOCR extraction failed: {e}")
            return []
    
    def extract_with_paddleocr(self, image_path: str) -> List[TextRegion]:
        """
        Extract text regions using PaddleOCR with bounding box information.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            List of text regions with bounding boxes
        """
        if not self.has_paddleocr:
            return []
        
        try:
            from paddleocr import PaddleOCR
            
            ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
            results = ocr.ocr(image_path, cls=True)
            
            regions = []
            
            if results and results[0]:
                for line in results[0]:
                    bbox_points = line[0]
                    text_info = line[1]
                    text = text_info[0]
                    confidence = text_info[1]
                    
                    # Convert points to bounding box
                    xs = [p[0] for p in bbox_points]
                    ys = [p[1] for p in bbox_points]
                    
                    x = min(xs)
                    y = min(ys)
                    width = max(xs) - x
                    height = max(ys) - y
                    
                    bbox = BoundingBox(x=x, y=y, width=width, height=height)
                    
                    region = TextRegion(
                        text=text,
                        bbox=bbox,
                        confidence=confidence,
                        source='paddleocr'
                    )
                    
                    regions.append(region)
            
            logger.info(f"PaddleOCR extracted {len(regions)} text regions")
            return regions
            
        except Exception as e:
            logger.error(f"PaddleOCR extraction failed: {e}")
            return []
    
    def combine_results(self, regions_list: List[List[TextRegion]]) -> List[TextRegion]:
        """
        Combine results from multiple OCR engines using spatial analysis.
        
        Args:
            regions_list: List of region lists from different engines
            
        Returns:
            Combined and deduplicated list of text regions
        """
        # Flatten all regions into one list
        all_regions = []
        for regions in regions_list:
            all_regions.extend(regions)
        
        if not all_regions:
            return []
        
        # Create analyzer and merge overlapping regions
        analyzer = SpatialAnalyzer()
        analyzer.add_regions(all_regions)
        
        merged_regions = analyzer.merge_overlapping_regions(iou_threshold=0.5)
        
        logger.info(f"Combined {len(all_regions)} regions into {len(merged_regions)} unique regions")
        
        return merged_regions
    
    def extract(self, image_path: str) -> ExtractionResult:
        """
        Extract receipt data using multi-method OCR with spatial analysis.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            ExtractionResult containing extracted receipt data
        """
        try:
            # Extract with all available engines
            regions_list = []
            
            if self.has_tesseract:
                tesseract_regions = self.extract_with_tesseract(image_path)
                if tesseract_regions:
                    regions_list.append(tesseract_regions)
            
            if self.has_easyocr:
                easyocr_regions = self.extract_with_easyocr(image_path)
                if easyocr_regions:
                    regions_list.append(easyocr_regions)
            
            if self.has_paddleocr:
                paddleocr_regions = self.extract_with_paddleocr(image_path)
                if paddleocr_regions:
                    regions_list.append(paddleocr_regions)
            
            if not regions_list:
                return ExtractionResult(
                    success=False,
                    error="No OCR engines available"
                )
            
            # Combine results using spatial analysis
            combined_regions = self.combine_results(regions_list)
            
            # Analyze spatial structure
            analyzer = SpatialAnalyzer()
            analyzer.add_regions(combined_regions)
            
            # Extract structured text
            structured_lines = analyzer.extract_structured_text()
            
            # Parse receipt data from structured text
            receipt_data = self._parse_receipt_from_lines(structured_lines)
            
            # Add metadata
            receipt_data.model_used = f"Multi-method ({len(regions_list)} engines)"
            receipt_data.confidence_score = self._calculate_confidence(combined_regions)
            receipt_data.extraction_notes.append(
                f"Combined results from {len(regions_list)} OCR engines using spatial analysis"
            )
            
            return ExtractionResult(success=True, data=receipt_data)
            
        except Exception as e:
            logger.error(f"Spatial OCR extraction failed: {e}", exc_info=True)
            return ExtractionResult(success=False, error=str(e))
    
    def _parse_receipt_from_lines(self, lines: List[str]) -> ReceiptData:
        """
        Parse receipt data from structured text lines.
        
        Args:
            lines: List of text lines in reading order
            
        Returns:
            ReceiptData object
        """
        # Use the shared parsing logic from ocr_common if available
        if not OCR_COMMON_AVAILABLE:
            logger.warning("ocr_common module not available, returning empty receipt")
            return ReceiptData()
        
        parsed = _parse_receipt_text_shared(lines)
        
        receipt = ReceiptData()
        receipt.store_name = parsed['store_name']
        receipt.transaction_date = parsed['transaction_date']
        receipt.total = parsed['total']
        receipt.subtotal = parsed['subtotal']
        receipt.tax = parsed['tax']
        receipt.items = [
            LineItem(name=name, total_price=price, quantity=qty)
            for name, price, qty in parsed['items']
        ]
        receipt.store_address = parsed['store_address']
        receipt.store_phone = parsed['store_phone']
        receipt.extraction_notes = parsed['extraction_notes']
        
        return receipt
    
    def _calculate_confidence(self, regions: List[TextRegion]) -> float:
        """
        Calculate overall confidence score from text regions.
        
        Args:
            regions: List of text regions
            
        Returns:
            Overall confidence score (0.0 to 100.0)
        """
        if not regions:
            return 0.0
        
        # Calculate weighted average confidence
        total_weight = 0.0
        weighted_sum = 0.0
        
        for region in regions:
            # Weight by text length (longer text is more important)
            weight = len(region.text)
            weighted_sum += region.confidence * weight
            total_weight += weight
        
        avg_confidence = weighted_sum / total_weight if total_weight > 0 else 0.0
        
        return round(avg_confidence * 100, 1)


__all__ = [
    'SpatialOCRProcessor',
    'BoundingBox',
    'TextRegion',
    'SpatialAnalyzer'
]
