"""
Unit Tests for NMS (Non-Maximum Suppression) Algorithm

Tests the NMS implementation in shared/utils/image.py
"""

import pytest
import numpy as np
from shared.utils.image import non_maximum_suppression
from shared.models.schemas import BoundingBox


class TestNMS:
    """Test Non-Maximum Suppression algorithm."""
    
    def test_nms_empty_list(self):
        """Test NMS with empty box list."""
        result = non_maximum_suppression([], [])
        assert result == []
    
    def test_nms_single_box(self):
        """Test NMS with single box."""
        boxes = [[10, 10, 50, 50]]
        confidences = [0.9]
        result = non_maximum_suppression(boxes, confidences)
        assert result == [0]
    
    def test_nms_no_overlap(self):
        """Test NMS with non-overlapping boxes."""
        boxes = [
            [10, 10, 50, 50],
            [100, 100, 50, 50],
            [200, 200, 50, 50]
        ]
        confidences = [0.9, 0.8, 0.7]
        result = non_maximum_suppression(boxes, confidences, overlap_threshold=0.3)
        # All boxes should be kept
        assert len(result) == 3
        assert set(result) == {0, 1, 2}
    
    def test_nms_complete_overlap(self):
        """Test NMS with completely overlapping boxes."""
        boxes = [
            [10, 10, 50, 50],
            [10, 10, 50, 50],  # Identical box
            [10, 10, 50, 50]   # Identical box
        ]
        confidences = [0.9, 0.7, 0.8]
        result = non_maximum_suppression(boxes, confidences, overlap_threshold=0.3)
        # Only highest confidence box should be kept
        assert len(result) == 1
        assert result[0] == 0  # Highest confidence
    
    def test_nms_partial_overlap(self):
        """Test NMS with partially overlapping boxes."""
        boxes = [
            [10, 10, 50, 50],   # Box 1
            [15, 15, 50, 50],   # Box 2 (overlaps with 1)
            [100, 100, 30, 30], # Box 3 (separate)
            [12, 12, 50, 50]    # Box 4 (overlaps with 1 and 2)
        ]
        confidences = [0.9, 0.7, 0.8, 0.6]
        result = non_maximum_suppression(boxes, confidences, overlap_threshold=0.3)
        
        # Box 1 (highest confidence among overlapping) and Box 3 should be kept
        assert len(result) == 2
        assert 0 in result  # Box 1
        assert 2 in result  # Box 3
    
    def test_nms_with_bboxes(self):
        """Test NMS with BoundingBox objects."""
        boxes = [
            BoundingBox(x=10, y=10, width=50, height=50),
            BoundingBox(x=15, y=15, width=50, height=50),
            BoundingBox(x=100, y=100, width=30, height=30)
        ]
        confidences = [0.9, 0.7, 0.8]
        result = non_maximum_suppression(boxes, confidences, overlap_threshold=0.3)
        
        assert len(result) == 2
        assert 0 in result
        assert 2 in result
    
    def test_nms_no_confidences(self):
        """Test NMS without confidence scores."""
        boxes = [
            [10, 10, 50, 50],
            [15, 15, 50, 50],
            [100, 100, 30, 30]
        ]
        # Should use default confidences (all equal)
        result = non_maximum_suppression(boxes, None, overlap_threshold=0.3)
        
        # First box and third box should be kept
        assert len(result) == 2
    
    def test_nms_threshold_zero(self):
        """Test NMS with zero threshold (keep all)."""
        boxes = [
            [10, 10, 50, 50],
            [15, 15, 50, 50],
            [20, 20, 50, 50]
        ]
        confidences = [0.9, 0.8, 0.7]
        result = non_maximum_suppression(boxes, confidences, overlap_threshold=0.0)
        
        # Only highest confidence should be kept
        assert len(result) == 1
        assert result[0] == 0
    
    def test_nms_threshold_one(self):
        """Test NMS with threshold of 1.0 (keep all)."""
        boxes = [
            [10, 10, 50, 50],
            [10, 10, 50, 50],  # Identical
            [10, 10, 50, 50]   # Identical
        ]
        confidences = [0.9, 0.8, 0.7]
        result = non_maximum_suppression(boxes, confidences, overlap_threshold=1.0)
        
        # All boxes should be kept
        assert len(result) == 3
    
    def test_nms_confidence_order(self):
        """Test that NMS respects confidence ordering."""
        boxes = [
            [10, 10, 50, 50],
            [15, 15, 50, 50],
            [20, 20, 50, 50]
        ]
        # Box 2 has highest confidence
        confidences = [0.7, 0.9, 0.8]
        result = non_maximum_suppression(boxes, confidences, overlap_threshold=0.3)
        
        # Box with highest confidence should be kept
        assert 1 in result
    
    def test_nms_mixed_formats(self):
        """Test NMS with mixed box formats."""
        boxes = [
            [10, 10, 50, 50],
            (15, 15, 50, 50),  # Tuple format
            [100, 100, 30, 30]
        ]
        confidences = [0.9, 0.7, 0.8]
        result = non_maximum_suppression(boxes, confidences, overlap_threshold=0.3)
        
        assert len(result) >= 1
        assert isinstance(result, list)
    
    def test_nms_invalid_boxes(self):
        """Test NMS with invalid box in the list."""
        boxes = [
            [10, 10, 50, 50],
            [15, 15],  # Invalid - too few elements
            [100, 100, 30, 30]
        ]
        confidences = [0.9, 0.7, 0.8]
        # Should skip invalid box
        result = non_maximum_suppression(boxes, confidences, overlap_threshold=0.3)
        
        # Should process valid boxes only
        assert isinstance(result, list)
    
    def test_nms_edge_case_touching_boxes(self):
        """Test NMS with boxes that just touch (no overlap)."""
        boxes = [
            [0, 0, 50, 50],
            [50, 0, 50, 50],  # Touches right edge
            [0, 50, 50, 50]   # Touches bottom edge
        ]
        confidences = [0.9, 0.8, 0.7]
        result = non_maximum_suppression(boxes, confidences, overlap_threshold=0.3)
        
        # All boxes should be kept (no overlap)
        assert len(result) == 3


class TestNMSPerformance:
    """Test NMS performance characteristics."""
    
    def test_nms_large_number_boxes(self):
        """Test NMS with large number of boxes."""
        np.random.seed(42)
        n_boxes = 1000
        
        # Generate random boxes
        boxes = []
        for _ in range(n_boxes):
            x = np.random.randint(0, 500)
            y = np.random.randint(0, 500)
            w = np.random.randint(10, 100)
            h = np.random.randint(10, 100)
            boxes.append([x, y, w, h])
        
        confidences = np.random.random(n_boxes).tolist()
        
        # Should complete without error
        result = non_maximum_suppression(boxes, confidences, overlap_threshold=0.5)
        
        assert isinstance(result, list)
        assert len(result) <= n_boxes
        assert len(result) > 0  # Should keep at least some boxes
    
    def test_nms_deterministic(self):
        """Test that NMS is deterministic."""
        boxes = [
            [10, 10, 50, 50],
            [15, 15, 50, 50],
            [100, 100, 30, 30]
        ]
        confidences = [0.9, 0.7, 0.8]
        
        # Run twice
        result1 = non_maximum_suppression(boxes, confidences, overlap_threshold=0.3)
        result2 = non_maximum_suppression(boxes, confidences, overlap_threshold=0.3)
        
        # Results should be identical
        assert result1 == result2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
