"""
Unit Tests for Text Detection Schemas

Tests the unified output schema for text detection algorithms,
including BoundingBox, DetectedText, and DetectionResult.
"""

import pytest
import json
from shared.models.schemas import (
    BoundingBox,
    DetectedText,
    DetectionResult,
    ErrorCode
)


class TestBoundingBox:
    """Test BoundingBox class."""
    
    def test_create_bbox(self):
        """Test basic BoundingBox creation."""
        bbox = BoundingBox(x=10, y=20, width=100, height=50)
        assert bbox.x == 10
        assert bbox.y == 20
        assert bbox.width == 100
        assert bbox.height == 50
    
    def test_bbox_area(self):
        """Test area calculation."""
        bbox = BoundingBox(x=0, y=0, width=100, height=50)
        assert bbox.area() == 5000
    
    def test_bbox_from_coords(self):
        """Test creation from coordinates."""
        bbox = BoundingBox.from_coords(10, 20, 110, 70)
        assert bbox.x == 10
        assert bbox.y == 20
        assert bbox.width == 100
        assert bbox.height == 50
    
    def test_bbox_from_coords_reversed(self):
        """Test creation from reversed coordinates."""
        bbox = BoundingBox.from_coords(110, 70, 10, 20)
        assert bbox.x == 10
        assert bbox.y == 20
        assert bbox.width == 100
        assert bbox.height == 50
    
    def test_bbox_iou_identical(self):
        """Test IoU with identical boxes."""
        bbox1 = BoundingBox(x=10, y=10, width=50, height=50)
        bbox2 = BoundingBox(x=10, y=10, width=50, height=50)
        assert bbox1.iou(bbox2) == 1.0
    
    def test_bbox_iou_no_overlap(self):
        """Test IoU with non-overlapping boxes."""
        bbox1 = BoundingBox(x=10, y=10, width=50, height=50)
        bbox2 = BoundingBox(x=100, y=100, width=50, height=50)
        assert bbox1.iou(bbox2) == 0.0
    
    def test_bbox_iou_partial_overlap(self):
        """Test IoU with partially overlapping boxes."""
        bbox1 = BoundingBox(x=10, y=10, width=50, height=50)
        bbox2 = BoundingBox(x=30, y=30, width=50, height=50)
        iou = bbox1.iou(bbox2)
        assert 0 < iou < 1  # Some overlap but not complete
    
    def test_bbox_to_dict(self):
        """Test serialization to dictionary."""
        bbox = BoundingBox(x=10, y=20, width=100, height=50)
        data = bbox.to_dict()
        assert data == {'x': 10, 'y': 20, 'width': 100, 'height': 50}
    
    def test_bbox_from_dict(self):
        """Test deserialization from dictionary."""
        data = {'x': 10, 'y': 20, 'width': 100, 'height': 50}
        bbox = BoundingBox.from_dict(data)
        assert bbox.x == 10
        assert bbox.y == 20
        assert bbox.width == 100
        assert bbox.height == 50


class TestDetectedText:
    """Test DetectedText class."""
    
    def test_create_detected_text(self):
        """Test basic DetectedText creation."""
        bbox = BoundingBox(x=10, y=20, width=100, height=50)
        text = DetectedText(
            text="Sample Text",
            confidence=0.95,
            bbox=bbox
        )
        assert text.text == "Sample Text"
        assert text.confidence == 0.95
        assert text.bbox == bbox
        assert text.language is None
    
    def test_detected_text_with_language(self):
        """Test DetectedText with language attribute."""
        bbox = BoundingBox(x=10, y=20, width=100, height=50)
        text = DetectedText(
            text="Hello",
            confidence=0.9,
            bbox=bbox,
            language="en"
        )
        assert text.language == "en"
    
    def test_detected_text_with_attributes(self):
        """Test DetectedText with custom attributes."""
        bbox = BoundingBox(x=10, y=20, width=100, height=50)
        text = DetectedText(
            text="Test",
            confidence=0.8,
            bbox=bbox,
            attributes={'font_size': 12, 'bold': True}
        )
        assert text.attributes['font_size'] == 12
        assert text.attributes['bold'] is True
    
    def test_detected_text_to_dict(self):
        """Test serialization to dictionary."""
        bbox = BoundingBox(x=10, y=20, width=100, height=50)
        text = DetectedText(
            text="Sample",
            confidence=0.95,
            bbox=bbox,
            language="en"
        )
        data = text.to_dict()
        assert data['text'] == "Sample"
        assert data['confidence'] == 0.95
        assert data['language'] == "en"
        assert 'bbox' in data
    
    def test_detected_text_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            'text': "Sample",
            'confidence': 0.95,
            'bbox': {'x': 10, 'y': 20, 'width': 100, 'height': 50},
            'language': 'en'
        }
        text = DetectedText.from_dict(data)
        assert text.text == "Sample"
        assert text.confidence == 0.95
        assert text.language == "en"
        assert text.bbox.x == 10


class TestDetectionResult:
    """Test DetectionResult class."""
    
    def test_create_detection_result(self):
        """Test basic DetectionResult creation."""
        bbox = BoundingBox(x=10, y=20, width=100, height=50)
        text = DetectedText(text="Test", confidence=0.9, bbox=bbox)
        
        result = DetectionResult(
            texts=[text],
            metadata={'model': 'test'},
            processing_time=1.5,
            model_id='test_model'
        )
        
        assert len(result.texts) == 1
        assert result.metadata['model'] == 'test'
        assert result.processing_time == 1.5
        assert result.model_id == 'test_model'
        assert result.success is True
        assert result.error_code is None
    
    def test_detection_result_empty(self):
        """Test DetectionResult with no texts."""
        result = DetectionResult(
            texts=[],
            metadata={},
            processing_time=0.5,
            model_id='test'
        )
        assert len(result.texts) == 0
        assert result.success is True
    
    def test_detection_result_to_dict(self):
        """Test serialization to dictionary."""
        bbox = BoundingBox(x=10, y=20, width=100, height=50)
        text = DetectedText(text="Test", confidence=0.9, bbox=bbox)
        
        result = DetectionResult(
            texts=[text],
            metadata={'model': 'test'},
            processing_time=1.5,
            model_id='test_model'
        )
        
        data = result.to_dict()
        assert 'texts' in data
        assert 'metadata' in data
        assert 'processing_time' in data
        assert 'model_id' in data
        assert 'success' in data
        assert data['success'] is True
    
    def test_detection_result_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            'texts': [{
                'text': 'Test',
                'confidence': 0.9,
                'bbox': {'x': 10, 'y': 20, 'width': 100, 'height': 50}
            }],
            'metadata': {'model': 'test'},
            'processing_time': 1.5,
            'model_id': 'test_model',
            'success': True
        }
        
        result = DetectionResult.from_dict(data)
        assert len(result.texts) == 1
        assert result.texts[0].text == 'Test'
        assert result.metadata['model'] == 'test'
        assert result.success is True
    
    def test_create_error_result(self):
        """Test error result creation."""
        result = DetectionResult.create_error(
            error_code=ErrorCode.TIMEOUT,
            error_message='Processing timeout',
            model_id='test_model',
            processing_time=30.0
        )
        
        assert result.success is False
        assert result.error_code == ErrorCode.TIMEOUT
        assert result.error_message == 'Processing timeout'
        assert len(result.texts) == 0
        assert result.processing_time == 30.0
    
    def test_error_result_serialization(self):
        """Test error result serialization."""
        result = DetectionResult.create_error(
            error_code=ErrorCode.INVALID_IMAGE,
            error_message='Invalid image format',
            model_id='test_model'
        )
        
        data = result.to_dict()
        assert data['success'] is False
        assert data['error_code'] == 'invalid_image'
        assert data['error_message'] == 'Invalid image format'


class TestErrorCode:
    """Test ErrorCode enum."""
    
    def test_error_codes_exist(self):
        """Test that all expected error codes exist."""
        assert ErrorCode.MODEL_NOT_READY.value == 'model_not_ready'
        assert ErrorCode.TIMEOUT.value == 'timeout'
        assert ErrorCode.INVALID_IMAGE.value == 'invalid_image'
        assert ErrorCode.PROCESSING_FAILED.value == 'processing_failed'
        assert ErrorCode.MISSING_DEPENDENCIES.value == 'missing_dependencies'
        assert ErrorCode.INSUFFICIENT_MEMORY.value == 'insufficient_memory'
        assert ErrorCode.UNKNOWN_ERROR.value == 'unknown_error'


class TestJSONSerialization:
    """Test JSON serialization/deserialization."""
    
    def test_full_round_trip(self):
        """Test full JSON round-trip serialization."""
        bbox = BoundingBox(x=10, y=20, width=100, height=50)
        text = DetectedText(
            text="Sample Text",
            confidence=0.95,
            bbox=bbox,
            language="en"
        )
        
        result = DetectionResult(
            texts=[text],
            metadata={'model': 'test', 'version': '1.0'},
            processing_time=1.5,
            model_id='test_model'
        )
        
        # Serialize to JSON
        json_str = json.dumps(result.to_dict())
        
        # Deserialize from JSON
        data = json.loads(json_str)
        restored = DetectionResult.from_dict(data)
        
        # Verify
        assert len(restored.texts) == 1
        assert restored.texts[0].text == "Sample Text"
        assert restored.texts[0].confidence == 0.95
        assert restored.texts[0].language == "en"
        assert restored.metadata['model'] == 'test'
        assert restored.processing_time == 1.5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
