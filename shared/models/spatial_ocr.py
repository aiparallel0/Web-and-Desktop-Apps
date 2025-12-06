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

# Import ocr_common parsing functions and patterns
try:
    from .ocr_common import parse_receipt_text as _parse_receipt_text_shared
    OCR_COMMON_AVAILABLE = True
except ImportError:
    OCR_COMMON_AVAILABLE = False

# Import patterns for multi-line item detection from ocr module
try:
    from .ocr import (
        SKU_PATTERN,
        MULTILINE_SKU_PRICE_PATTERN,
        POTENTIAL_ITEM_NAME_PATTERN,
        should_skip_line
    )
    OCR_PATTERNS_AVAILABLE = True
except ImportError:
    OCR_PATTERNS_AVAILABLE = False
    # Define fallback patterns if imports fail
    SKU_PATTERN = re.compile(r'\b\d{12,14}\b')
    MULTILINE_SKU_PRICE_PATTERN = re.compile(
        r'^(\d{12,14})\s*[FfTt]?\s*(\d+)\s*[.,]\s*(\d{2})\s*[FTNXOD0]?$',
        re.IGNORECASE
    )
    POTENTIAL_ITEM_NAME_PATTERN = re.compile(
        r'^[A-Z0-9][A-Z0-9\s\-_/\']{2,40}$',
        re.IGNORECASE
    )
    
    # Fallback implementation with basic filtering
    # Based on common skip keywords from ocr.py
    FALLBACK_SKIP_KEYWORDS = frozenset({
        'subtotal', 'total', 'cash', 'change', 'tax', 'payment', 'balance',
        'thank', 'visit', 'welcome', 'receipt', 'cashier'
    })
    
    def should_skip_line(line: str) -> bool:
        """Fallback implementation with basic filtering."""
        if not line:
            return True
        line_lower = line.lower()
        # Skip lines with common keywords
        if any(kw in line_lower for kw in FALLBACK_SKIP_KEYWORDS):
            logger.debug(f"Fallback should_skip_line: skipping '{line}' (keyword match)")
            return True
        return False

logger = logging.getLogger(__name__)

# Source priority for conflict resolution when merging overlapping regions
# Higher values indicate higher priority/reliability
SOURCE_PRIORITY = {
    'easyocr': 3,      # Highest priority - typically most accurate
    'tesseract': 2,    # Medium priority - good for standard text
    'paddleocr': 1,    # Lower priority - but still useful
}

# Weights for scoring overlapping regions (confidence vs source priority)
CONFIDENCE_WEIGHT = 0.7  # Weight for confidence score (0-1)
PRIORITY_WEIGHT = 0.3    # Weight for source priority (0-1)

# Minimum confidence threshold for text extraction (95%)
MIN_CONFIDENCE_THRESHOLD = 0.95

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
        
        Optimized version with early termination to reduce unnecessary comparisons.
        
        Args:
            iou_threshold: IoU threshold for considering regions as duplicates
            
        Returns:
            List of merged regions
        """
        if not self.regions:
            return []
        
        # Sort by confidence (descending) - higher confidence regions processed first
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
                
                # Calculate IoU - this is the expensive operation
                iou = region.bbox.iou(other.bbox)
                if iou > iou_threshold:
                    overlaps.append((j, other))
            
            # If we have overlaps, take the best one based on confidence and source
            if overlaps:
                # Use global source priority mapping and weights
                candidates = [(i, region)] + overlaps
                best = max(candidates, key=lambda x: (
                    x[1].confidence * CONFIDENCE_WEIGHT + 
                    SOURCE_PRIORITY.get(x[1].source, 0) * PRIORITY_WEIGHT
                ))
                
                merged.append(best[1])
                used.add(best[0])
                # Mark all overlapping regions as used (early termination)
                for idx, _ in overlaps:
                    used.add(idx)
            else:
                # No overlaps, add region directly
                merged.append(region)
                used.add(i)
        
        return merged
    
    def merge_regions_unified(self, iou_threshold: float = 0.5, 
                             min_confidence: float = MIN_CONFIDENCE_THRESHOLD,
                             merge_multiline_items: bool = True) -> List[TextRegion]:
        """
        Unified method to merge text regions using both spatial and text-based analysis.
        
        This method combines:
        1. Spatial overlapping region detection (IoU-based)
        2. Multi-line item merging (text pattern-based)
        3. Confidence filtering (95% threshold)
        
        Args:
            iou_threshold: IoU threshold for considering regions as duplicates (default: 0.5)
            min_confidence: Minimum confidence threshold for accepting regions (default: 0.95)
            merge_multiline_items: Whether to merge multi-line item patterns (default: True)
            
        Returns:
            List of merged and filtered regions
        """
        if not self.regions:
            return []
        
        # Step 1: Filter regions by confidence threshold (95%)
        high_conf_regions = [r for r in self.regions if r.confidence >= min_confidence]
        
        # If no high-confidence regions, use all regions but log a warning
        if not high_conf_regions:
            logger.warning(f"No regions with confidence >= {min_confidence:.0%}, using all regions")
            high_conf_regions = self.regions
        
        # Step 2: Merge spatially overlapping regions
        analyzer_temp = SpatialAnalyzer()
        analyzer_temp.add_regions(high_conf_regions)
        spatially_merged = analyzer_temp.merge_overlapping_regions(iou_threshold)
        
        # Step 3: Merge multi-line items using spatial information
        if merge_multiline_items and OCR_PATTERNS_AVAILABLE:
            spatially_merged = self._merge_multiline_regions(spatially_merged)
        
        return spatially_merged
    
    def _merge_multiline_regions(self, regions: List[TextRegion]) -> List[TextRegion]:
        """
        Merge multi-line item entries using spatial and text pattern analysis.
        
        This detects patterns where:
        - Line 1: Item name (e.g., "6 WING PLATE")
        - Line 2: SKU + price (e.g., "020108870398 F 3.98 0")
        
        And merges them into a single region.
        
        Args:
            regions: List of text regions sorted by reading order
            
        Returns:
            List of regions with multi-line items merged
        """
        if not regions or len(regions) < 2:
            return regions
        
        # Group regions by rows for easier multi-line detection
        analyzer_temp = SpatialAnalyzer()
        analyzer_temp.add_regions(regions)
        rows = analyzer_temp.group_by_rows(tolerance=10.0)
        
        # Flatten rows back to a list while maintaining order
        sorted_regions = []
        for row in rows:
            sorted_regions.extend(row)
        
        merged = []
        i = 0
        
        while i < len(sorted_regions):
            current_region = sorted_regions[i]
            current_text = current_region.text.strip()
            
            # Skip empty regions
            if not current_text:
                merged.append(current_region)
                i += 1
                continue
            
            # Check if current region could be an item name
            is_potential_name = (
                POTENTIAL_ITEM_NAME_PATTERN.match(current_text) and
                not SKU_PATTERN.search(current_text) and
                not re.search(r'\d+[.,]\d{2}\s*$', current_text) and
                not should_skip_line(current_text) and
                len(current_text) >= 3
            )
            
            # If this looks like an item name and we have a next region
            if is_potential_name and i + 1 < len(sorted_regions):
                next_region = sorted_regions[i + 1]
                next_text = next_region.text.strip()
                
                # Check if next region matches the SKU+price pattern
                sku_price_match = MULTILINE_SKU_PRICE_PATTERN.match(next_text)
                if sku_price_match:
                    # Merge the two regions
                    sku = sku_price_match.group(1)
                    dollars = sku_price_match.group(2)
                    cents = sku_price_match.group(3)
                    merged_text = f"{current_text} {sku} {dollars}.{cents}"
                    
                    # Create a merged region with combined bounding box
                    merged_bbox = BoundingBox(
                        x=min(current_region.bbox.x, next_region.bbox.x),
                        y=min(current_region.bbox.y, next_region.bbox.y),
                        width=max(current_region.bbox.x2, next_region.bbox.x2) - 
                              min(current_region.bbox.x, next_region.bbox.x),
                        height=max(current_region.bbox.y2, next_region.bbox.y2) - 
                               min(current_region.bbox.y, next_region.bbox.y)
                    )
                    
                    # Use the higher confidence of the two regions
                    merged_confidence = max(current_region.confidence, next_region.confidence)
                    
                    merged_region = TextRegion(
                        text=merged_text,
                        bbox=merged_bbox,
                        confidence=merged_confidence,
                        source=current_region.source  # Use source from item name
                    )
                    
                    merged.append(merged_region)
                    i += 2  # Skip both regions
                    continue
            
            # Default: add region as-is
            merged.append(current_region)
            i += 1
        
        logger.info(f"Multi-line merging: {len(regions)} regions -> {len(merged)} regions")
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
    
    Performance optimizations:
    - Lazy initialization of OCR engines (only when needed)
    - Cached reader instances (reused across calls)
    
    Note: Class-level caches are designed for single-threaded use.
    For multi-threaded applications, consider using thread-local storage
    or adding synchronization mechanisms to the cache access.
    """
    
    # Class-level cache for OCR engine instances (shared across all instances)
    # NOTE: Not thread-safe - designed for single-threaded use
    # For multi-threaded use, consider threading.local() or proper locks
    _easyocr_reader_cache = None
    _paddleocr_cache = None
    
    def __init__(self, ocr_engines: Optional[List[Any]] = None):
        """
        Initialize the spatial OCR processor.
        
        Args:
            ocr_engines: List of OCR engine instances to use.
                        If None, will attempt to initialize available engines lazily.
        """
        self.ocr_engines = ocr_engines or []
        self.analyzer = SpatialAnalyzer()
        
        # Initialize availability flags (check imports, don't initialize yet)
        self.has_tesseract = False
        self.has_easyocr = False
        self.has_paddleocr = False
        
        # Check engine availability without initializing them
        if not self.ocr_engines:
            self._check_engine_availability()
    
    def _check_engine_availability(self):
        """
        Check which OCR engines are available without initializing them.
        
        This is much faster than _initialize_engines() as it only checks imports.
        Actual engine initialization is deferred until first use (lazy loading).
        """
        # Check Tesseract availability (no initialization needed - uses system binary)
        try:
            import pytesseract
            from PIL import Image
            self.has_tesseract = True
            logger.info("Tesseract OCR available")
        except ImportError:
            self.has_tesseract = False
            logger.warning("Tesseract OCR not available")
        
        # Check EasyOCR availability (don't create Reader yet - expensive)
        try:
            import easyocr
            self.has_easyocr = True
            logger.info("EasyOCR available")
        except ImportError:
            self.has_easyocr = False
            logger.warning("EasyOCR not available")
        
        # Check PaddleOCR availability (don't create instance yet - expensive)
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
        
        Uses a cached EasyOCR Reader instance for better performance.
        Creating a new Reader() for each call is very slow (~2-3 seconds).
        
        Args:
            image_path: Path to the image file
            
        Returns:
            List of text regions with bounding boxes
        """
        if not self.has_easyocr:
            return []
        
        try:
            import easyocr
            
            # Use cached reader instance if available (major performance improvement)
            if SpatialOCRProcessor._easyocr_reader_cache is None:
                logger.info("Initializing EasyOCR Reader (one-time setup)...")
                SpatialOCRProcessor._easyocr_reader_cache = easyocr.Reader(['en'], gpu=False)
            
            reader = SpatialOCRProcessor._easyocr_reader_cache
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
        
        Uses a cached PaddleOCR instance for better performance.
        Creating a new PaddleOCR() for each call is very slow.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            List of text regions with bounding boxes
        """
        if not self.has_paddleocr:
            return []
        
        try:
            from paddleocr import PaddleOCR
            
            # Use cached PaddleOCR instance if available (major performance improvement)
            if SpatialOCRProcessor._paddleocr_cache is None:
                logger.info("Initializing PaddleOCR (one-time setup)...")
                SpatialOCRProcessor._paddleocr_cache = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
            
            ocr = SpatialOCRProcessor._paddleocr_cache
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
    
    def combine_results(self, regions_list: List[List[TextRegion]], 
                       min_confidence: float = MIN_CONFIDENCE_THRESHOLD) -> List[TextRegion]:
        """
        Combine results from multiple OCR engines using unified spatial and text-based analysis.
        
        This method now uses the unified merging approach that combines:
        1. Spatial overlapping region detection
        2. Multi-line item merging
        3. 95% confidence filtering
        
        Args:
            regions_list: List of region lists from different engines
            min_confidence: Minimum confidence threshold (default: 0.95 = 95%)
            
        Returns:
            Combined and deduplicated list of text regions
        """
        # Flatten all regions into one list
        all_regions = []
        for regions in regions_list:
            all_regions.extend(regions)
        
        if not all_regions:
            return []
        
        # Create analyzer and use unified merging
        analyzer = SpatialAnalyzer()
        analyzer.add_regions(all_regions)
        
        # Use the new unified merging method
        merged_regions = analyzer.merge_regions_unified(
            iou_threshold=0.5,
            min_confidence=min_confidence,
            merge_multiline_items=True
        )
        
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
                f"Combined results from {len(regions_list)} OCR engines using unified spatial "
                f"and text-based merging with {MIN_CONFIDENCE_THRESHOLD:.0%} confidence threshold"
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


class EasyOCRSpatialProcessor(SpatialOCRProcessor):
    """
    EasyOCR processor with spatial bounding box analysis.
    
    This processor uses only EasyOCR for text extraction but applies
    spatial analysis for improved structure understanding.
    """
    
    def __init__(self, model_config: Optional[Dict] = None):
        """Initialize with EasyOCR only."""
        super().__init__()
        self.model_config = model_config or {}
        # Force initialization of EasyOCR only
        self._initialize_easyocr_only()
    
    def _initialize_easyocr_only(self):
        """Initialize only EasyOCR engine (check availability, don't create Reader yet)."""
        try:
            import easyocr
            self.has_easyocr = True
            self.has_tesseract = False
            self.has_paddleocr = False
            logger.info("EasyOCR Spatial processor initialized (lazy loading)")
        except ImportError:
            self.has_easyocr = False
            logger.warning("EasyOCR not available for spatial processing")
    
    def extract(self, image_path: str) -> ExtractionResult:
        """
        Extract receipt data using EasyOCR with spatial analysis.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            ExtractionResult containing extracted receipt data
        """
        try:
            # Extract with EasyOCR only
            regions_list = []
            
            if self.has_easyocr:
                easyocr_regions = self.extract_with_easyocr(image_path)
                if easyocr_regions:
                    regions_list.append(easyocr_regions)
            
            if not regions_list:
                return ExtractionResult(
                    success=False,
                    error="EasyOCR not available"
                )
            
            # Use unified merging on EasyOCR results
            combined_regions = regions_list[0]  # Only EasyOCR results
            
            # Apply unified spatial and text-based merging
            analyzer = SpatialAnalyzer()
            analyzer.add_regions(combined_regions)
            merged_regions = analyzer.merge_regions_unified(
                iou_threshold=0.5,
                min_confidence=MIN_CONFIDENCE_THRESHOLD,
                merge_multiline_items=True
            )
            
            # Extract structured text from merged regions
            analyzer_final = SpatialAnalyzer()
            analyzer_final.add_regions(merged_regions)
            structured_lines = analyzer_final.extract_structured_text()
            
            # Parse receipt data from structured text
            receipt_data = self._parse_receipt_from_lines(structured_lines)
            
            # Add metadata
            receipt_data.model_used = "EasyOCR with Unified Spatial and Text-based Merging"
            receipt_data.confidence_score = self._calculate_confidence(merged_regions)
            receipt_data.extraction_notes.append(
                f"EasyOCR with unified spatial and text-based merging, "
                f"{MIN_CONFIDENCE_THRESHOLD:.0%} confidence threshold applied"
            )
            
            return ExtractionResult(success=True, data=receipt_data)
            
        except Exception as e:
            logger.error(f"EasyOCR Spatial extraction failed: {e}", exc_info=True)
            return ExtractionResult(success=False, error=str(e))


class PaddleOCRSpatialProcessor(SpatialOCRProcessor):
    """
    PaddleOCR processor with spatial bounding box analysis.
    
    This processor uses only PaddleOCR for text extraction but applies
    spatial analysis for improved structure understanding.
    """
    
    def __init__(self, model_config: Optional[Dict] = None):
        """Initialize with PaddleOCR only."""
        super().__init__()
        self.model_config = model_config or {}
        # Force initialization of PaddleOCR only
        self._initialize_paddleocr_only()
    
    def _initialize_paddleocr_only(self):
        """Initialize only PaddleOCR engine (check availability, don't create instance yet)."""
        try:
            from paddleocr import PaddleOCR
            self.has_paddleocr = True
            self.has_tesseract = False
            self.has_easyocr = False
            logger.info("PaddleOCR Spatial processor initialized (lazy loading)")
        except ImportError:
            self.has_paddleocr = False
            logger.warning("PaddleOCR not available for spatial processing")
    
    def extract(self, image_path: str) -> ExtractionResult:
        """
        Extract receipt data using PaddleOCR with spatial analysis.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            ExtractionResult containing extracted receipt data
        """
        try:
            # Extract with PaddleOCR only
            regions_list = []
            
            if self.has_paddleocr:
                paddleocr_regions = self.extract_with_paddleocr(image_path)
                if paddleocr_regions:
                    regions_list.append(paddleocr_regions)
            
            if not regions_list:
                return ExtractionResult(
                    success=False,
                    error="PaddleOCR not available"
                )
            
            # Use unified merging on PaddleOCR results
            combined_regions = regions_list[0]  # Only PaddleOCR results
            
            # Apply unified spatial and text-based merging
            analyzer = SpatialAnalyzer()
            analyzer.add_regions(combined_regions)
            merged_regions = analyzer.merge_regions_unified(
                iou_threshold=0.5,
                min_confidence=MIN_CONFIDENCE_THRESHOLD,
                merge_multiline_items=True
            )
            
            # Extract structured text from merged regions
            analyzer_final = SpatialAnalyzer()
            analyzer_final.add_regions(merged_regions)
            structured_lines = analyzer_final.extract_structured_text()
            
            # Parse receipt data from structured text
            receipt_data = self._parse_receipt_from_lines(structured_lines)
            
            # Add metadata
            receipt_data.model_used = "PaddleOCR with Unified Spatial and Text-based Merging"
            receipt_data.confidence_score = self._calculate_confidence(merged_regions)
            receipt_data.extraction_notes.append(
                f"PaddleOCR with unified spatial and text-based merging, "
                f"{MIN_CONFIDENCE_THRESHOLD:.0%} confidence threshold applied"
            )
            
            return ExtractionResult(success=True, data=receipt_data)
            
        except Exception as e:
            logger.error(f"PaddleOCR Spatial extraction failed: {e}", exc_info=True)
            return ExtractionResult(success=False, error=str(e))


__all__ = [
    'SpatialOCRProcessor',
    'EasyOCRSpatialProcessor',
    'PaddleOCRSpatialProcessor',
    'BoundingBox',
    'TextRegion',
    'SpatialAnalyzer'
]
