"""
Tests for Spatial OCR with Multi-Method Analysis

Tests cover:
- Bounding box operations (IoU, overlap, alignment)
- Text region creation and management
- Spatial analysis (row grouping, column detection)
- Multi-engine result combination
- Duplicate detection and merging
"""

import pytest
from decimal import Decimal
from shared.models.spatial_ocr import (
    BoundingBox, TextRegion, SpatialAnalyzer, SpatialOCRProcessor
)


class TestBoundingBox:
    """Tests for BoundingBox class."""
    
    def test_bounding_box_creation(self):
        """Test basic bounding box creation."""
        bbox = BoundingBox(x=10, y=20, width=100, height=50)
        assert bbox.x == 10
        assert bbox.y == 20
        assert bbox.width == 100
        assert bbox.height == 50
    
    def test_bounding_box_properties(self):
        """Test computed properties."""
        bbox = BoundingBox(x=10, y=20, width=100, height=50)
        assert bbox.x2 == 110  # x + width
        assert bbox.y2 == 70   # y + height
        assert bbox.center_x == 60  # x + width/2
        assert bbox.center_y == 45  # y + height/2
        assert bbox.area == 5000  # width * height
    
    def test_iou_identical_boxes(self):
        """Test IoU of identical boxes."""
        bbox1 = BoundingBox(x=0, y=0, width=100, height=100)
        bbox2 = BoundingBox(x=0, y=0, width=100, height=100)
        assert bbox1.iou(bbox2) == 1.0
    
    def test_iou_no_overlap(self):
        """Test IoU of non-overlapping boxes."""
        bbox1 = BoundingBox(x=0, y=0, width=50, height=50)
        bbox2 = BoundingBox(x=100, y=100, width=50, height=50)
        assert bbox1.iou(bbox2) == 0.0
    
    def test_iou_partial_overlap(self):
        """Test IoU of partially overlapping boxes."""
        bbox1 = BoundingBox(x=0, y=0, width=100, height=100)
        bbox2 = BoundingBox(x=50, y=50, width=100, height=100)
        
        # Intersection: 50x50 = 2500
        # Union: 10000 + 10000 - 2500 = 17500
        # IoU: 2500 / 17500 ≈ 0.1429
        iou = bbox1.iou(bbox2)
        assert 0.14 < iou < 0.15
    
    def test_overlaps(self):
        """Test overlap detection."""
        bbox1 = BoundingBox(x=0, y=0, width=100, height=100)
        bbox2 = BoundingBox(x=50, y=50, width=100, height=100)
        bbox3 = BoundingBox(x=200, y=200, width=100, height=100)
        
        assert bbox1.overlaps(bbox2, threshold=0.1)
        assert not bbox1.overlaps(bbox3, threshold=0.1)
    
    def test_horizontal_alignment(self):
        """Test horizontal alignment detection."""
        # Same row (Y coordinates close)
        bbox1 = BoundingBox(x=0, y=100, width=50, height=20)
        bbox2 = BoundingBox(x=60, y=102, width=50, height=20)
        
        assert bbox1.is_aligned_horizontally(bbox2, tolerance=5.0)
        
        # Different rows
        bbox3 = BoundingBox(x=0, y=150, width=50, height=20)
        assert not bbox1.is_aligned_horizontally(bbox3, tolerance=5.0)
    
    def test_vertical_alignment(self):
        """Test vertical alignment detection."""
        # Same column (X coordinates close)
        bbox1 = BoundingBox(x=100, y=0, width=50, height=20)
        bbox2 = BoundingBox(x=102, y=30, width=50, height=20)
        
        assert bbox1.is_aligned_vertically(bbox2, tolerance=5.0)
        
        # Different columns
        bbox3 = BoundingBox(x=200, y=0, width=50, height=20)
        assert not bbox1.is_aligned_vertically(bbox3, tolerance=5.0)


class TestTextRegion:
    """Tests for TextRegion class."""
    
    def test_text_region_creation(self):
        """Test text region creation."""
        bbox = BoundingBox(x=10, y=20, width=100, height=30)
        region = TextRegion(
            text="Hello World",
            bbox=bbox,
            confidence=0.95,
            source="tesseract"
        )
        
        assert region.text == "Hello World"
        assert region.bbox == bbox
        assert region.confidence == 0.95
        assert region.source == "tesseract"
    
    def test_text_region_repr(self):
        """Test string representation."""
        bbox = BoundingBox(x=0, y=0, width=100, height=30)
        region = TextRegion(
            text="This is a very long text that should be truncated",
            bbox=bbox,
            confidence=0.85,
            source="easyocr"
        )
        
        repr_str = repr(region)
        assert "This is a very long" in repr_str
        assert "conf=0.85" in repr_str
        assert "src=easyocr" in repr_str


class TestSpatialAnalyzer:
    """Tests for SpatialAnalyzer class."""
    
    def test_add_region(self):
        """Test adding single region."""
        analyzer = SpatialAnalyzer()
        bbox = BoundingBox(x=0, y=0, width=100, height=30)
        region = TextRegion(text="Test", bbox=bbox, confidence=0.9, source="test")
        
        analyzer.add_region(region)
        assert len(analyzer.regions) == 1
    
    def test_add_regions(self):
        """Test adding multiple regions."""
        analyzer = SpatialAnalyzer()
        regions = [
            TextRegion(
                text=f"Text {i}",
                bbox=BoundingBox(x=i*50, y=i*30, width=100, height=30),
                confidence=0.9,
                source="test"
            )
            for i in range(5)
        ]
        
        analyzer.add_regions(regions)
        assert len(analyzer.regions) == 5
    
    def test_find_aligned_horizontal(self):
        """Test finding horizontally aligned regions."""
        analyzer = SpatialAnalyzer()
        
        # Create three regions: two in same row, one in different row
        region1 = TextRegion(
            text="Item 1",
            bbox=BoundingBox(x=0, y=100, width=50, height=20),
            confidence=0.9,
            source="test"
        )
        region2 = TextRegion(
            text="Price 1",
            bbox=BoundingBox(x=200, y=102, width=50, height=20),
            confidence=0.9,
            source="test"
        )
        region3 = TextRegion(
            text="Item 2",
            bbox=BoundingBox(x=0, y=130, width=50, height=20),
            confidence=0.9,
            source="test"
        )
        
        analyzer.add_regions([region1, region2, region3])
        
        # Find regions aligned with region1
        aligned = analyzer.find_aligned_regions(region1, orientation='horizontal')
        
        assert len(aligned) == 1
        assert aligned[0].text == "Price 1"
    
    def test_find_aligned_vertical(self):
        """Test finding vertically aligned regions."""
        analyzer = SpatialAnalyzer()
        
        # Create three regions: two in same column, one in different column
        region1 = TextRegion(
            text="Item 1",
            bbox=BoundingBox(x=100, y=0, width=50, height=20),
            confidence=0.9,
            source="test"
        )
        region2 = TextRegion(
            text="Item 2",
            bbox=BoundingBox(x=102, y=30, width=50, height=20),
            confidence=0.9,
            source="test"
        )
        region3 = TextRegion(
            text="Price",
            bbox=BoundingBox(x=200, y=0, width=50, height=20),
            confidence=0.9,
            source="test"
        )
        
        analyzer.add_regions([region1, region2, region3])
        
        # Find regions aligned with region1
        aligned = analyzer.find_aligned_regions(region1, orientation='vertical')
        
        assert len(aligned) == 1
        assert aligned[0].text == "Item 2"
    
    def test_group_by_rows(self):
        """Test grouping regions into rows."""
        analyzer = SpatialAnalyzer()
        
        # Create regions in two rows
        row1_regions = [
            TextRegion(
                text=f"R1C{i}",
                bbox=BoundingBox(x=i*60, y=100, width=50, height=20),
                confidence=0.9,
                source="test"
            )
            for i in range(3)
        ]
        
        row2_regions = [
            TextRegion(
                text=f"R2C{i}",
                bbox=BoundingBox(x=i*60, y=130, width=50, height=20),
                confidence=0.9,
                source="test"
            )
            for i in range(3)
        ]
        
        analyzer.add_regions(row1_regions + row2_regions)
        
        rows = analyzer.group_by_rows(tolerance=5.0)
        
        assert len(rows) == 2
        assert len(rows[0]) == 3
        assert len(rows[1]) == 3
        
        # Check that rows are sorted left to right
        assert rows[0][0].text == "R1C0"
        assert rows[0][1].text == "R1C1"
        assert rows[0][2].text == "R1C2"
    
    def test_merge_overlapping_regions(self):
        """Test merging overlapping regions."""
        analyzer = SpatialAnalyzer()
        
        # Create overlapping regions from different sources
        region1 = TextRegion(
            text="TOTAL",
            bbox=BoundingBox(x=100, y=200, width=100, height=30),
            confidence=0.85,
            source="tesseract"
        )
        
        region2 = TextRegion(
            text="TOTAL",
            bbox=BoundingBox(x=102, y=202, width=98, height=28),
            confidence=0.92,
            source="easyocr"
        )
        
        region3 = TextRegion(
            text="Item",
            bbox=BoundingBox(x=0, y=100, width=80, height=30),
            confidence=0.90,
            source="tesseract"
        )
        
        analyzer.add_regions([region1, region2, region3])
        
        merged = analyzer.merge_overlapping_regions(iou_threshold=0.5)
        
        # Should merge the two overlapping regions
        assert len(merged) == 2
        
        # Should keep the one with higher confidence (region2)
        total_regions = [r for r in merged if r.text == "TOTAL"]
        assert len(total_regions) == 1
        assert total_regions[0].confidence == 0.92
    
    def test_extract_structured_text(self):
        """Test extracting text in reading order."""
        analyzer = SpatialAnalyzer()
        
        # Create a simple receipt structure
        regions = [
            # Row 1: Store name
            TextRegion("WALMART", BoundingBox(0, 0, 100, 20), 0.9, "test"),
            
            # Row 2: Item and price
            TextRegion("MILK", BoundingBox(0, 50, 80, 20), 0.9, "test"),
            TextRegion("3.99", BoundingBox(200, 50, 50, 20), 0.9, "test"),
            
            # Row 3: Total
            TextRegion("TOTAL", BoundingBox(0, 100, 80, 20), 0.9, "test"),
            TextRegion("3.99", BoundingBox(200, 100, 50, 20), 0.9, "test"),
        ]
        
        analyzer.add_regions(regions)
        lines = analyzer.extract_structured_text()
        
        assert len(lines) == 3
        assert "WALMART" in lines[0]
        assert "MILK" in lines[1] and "3.99" in lines[1]
        assert "TOTAL" in lines[2] and "3.99" in lines[2]


class TestSpatialOCRProcessor:
    """Tests for SpatialOCRProcessor class."""
    
    def test_processor_initialization(self):
        """Test processor initialization."""
        processor = SpatialOCRProcessor()
        assert processor.analyzer is not None
    
    def test_combine_results_empty(self):
        """Test combining empty results."""
        processor = SpatialOCRProcessor()
        combined = processor.combine_results([])
        assert combined == []
    
    def test_combine_results_single_engine(self):
        """Test combining results from single engine."""
        processor = SpatialOCRProcessor()
        
        regions = [
            TextRegion("Text1", BoundingBox(0, 0, 100, 20), 0.9, "tesseract"),
            TextRegion("Text2", BoundingBox(0, 30, 100, 20), 0.9, "tesseract"),
        ]
        
        combined = processor.combine_results([regions])
        assert len(combined) == 2
    
    def test_combine_results_multiple_engines(self):
        """Test combining results from multiple engines."""
        processor = SpatialOCRProcessor()
        
        # Create overlapping detections from different engines
        tesseract_regions = [
            TextRegion("TOTAL", BoundingBox(100, 200, 100, 30), 0.85, "tesseract"),
            TextRegion("3.99", BoundingBox(250, 200, 50, 30), 0.90, "tesseract"),
        ]
        
        easyocr_regions = [
            TextRegion("TOTAL", BoundingBox(102, 202, 98, 28), 0.92, "easyocr"),
            TextRegion("3.99", BoundingBox(252, 202, 48, 28), 0.95, "easyocr"),
        ]
        
        combined = processor.combine_results([tesseract_regions, easyocr_regions])
        
        # Should merge overlapping regions
        assert len(combined) == 2
        
        # Should prefer higher confidence detections
        total_region = [r for r in combined if r.text == "TOTAL"][0]
        assert total_region.confidence >= 0.90
    
    def test_calculate_confidence_empty(self):
        """Test confidence calculation with empty regions."""
        processor = SpatialOCRProcessor()
        confidence = processor._calculate_confidence([])
        assert confidence == 0.0
    
    def test_calculate_confidence_single_region(self):
        """Test confidence calculation with single region."""
        processor = SpatialOCRProcessor()
        
        region = TextRegion("Test", BoundingBox(0, 0, 100, 20), 0.85, "test")
        confidence = processor._calculate_confidence([region])
        
        assert 84.0 < confidence < 86.0  # Should be around 85
    
    def test_calculate_confidence_multiple_regions(self):
        """Test confidence calculation with multiple regions."""
        processor = SpatialOCRProcessor()
        
        regions = [
            TextRegion("Short", BoundingBox(0, 0, 50, 20), 0.90, "test"),
            TextRegion("Very long text region", BoundingBox(0, 30, 200, 20), 0.80, "test"),
        ]
        
        confidence = processor._calculate_confidence(regions)
        
        # Longer text should be weighted more heavily
        # Expected: (5 * 0.90 + 21 * 0.80) / (5 + 21) ≈ 0.823
        assert 80.0 < confidence < 85.0


class TestIntegration:
    """Integration tests for spatial OCR."""
    
    def test_row_detection_preserves_order(self):
        """Test that row detection preserves left-to-right order."""
        analyzer = SpatialAnalyzer()
        
        # Create regions out of order
        regions = [
            TextRegion("C", BoundingBox(200, 100, 50, 20), 0.9, "test"),
            TextRegion("A", BoundingBox(0, 100, 50, 20), 0.9, "test"),
            TextRegion("B", BoundingBox(100, 100, 50, 20), 0.9, "test"),
        ]
        
        analyzer.add_regions(regions)
        rows = analyzer.group_by_rows()
        
        assert len(rows) == 1
        assert rows[0][0].text == "A"
        assert rows[0][1].text == "B"
        assert rows[0][2].text == "C"
    
    def test_multi_row_receipt_structure(self):
        """Test realistic multi-row receipt structure."""
        analyzer = SpatialAnalyzer()
        
        # Simulate a simple receipt
        regions = [
            # Header
            TextRegion("STORE NAME", BoundingBox(50, 0, 200, 30), 0.95, "test"),
            
            # Items
            TextRegion("Apples", BoundingBox(0, 50, 100, 20), 0.90, "test"),
            TextRegion("2.99", BoundingBox(250, 50, 50, 20), 0.92, "test"),
            
            TextRegion("Milk", BoundingBox(0, 80, 100, 20), 0.88, "test"),
            TextRegion("3.49", BoundingBox(250, 80, 50, 20), 0.91, "test"),
            
            # Total
            TextRegion("TOTAL", BoundingBox(0, 130, 100, 20), 0.93, "test"),
            TextRegion("6.48", BoundingBox(250, 130, 50, 20), 0.94, "test"),
        ]
        
        analyzer.add_regions(regions)
        lines = analyzer.extract_structured_text()
        
        # Should have 4 lines
        assert len(lines) == 4
        
        # Check content
        assert "STORE NAME" in lines[0]
        assert "Apples" in lines[1] and "2.99" in lines[1]
        assert "Milk" in lines[2] and "3.49" in lines[2]
        assert "TOTAL" in lines[3] and "6.48" in lines[3]
