"""
Unified Output Schema for Text Detection Systems

This module provides standardized data structures for all text detection processors
to ensure consistent output formats across different algorithms (Tesseract, EasyOCR, 
PaddleOCR, Donut, Florence-2, CRAFT, Spatial Multi-Method).

Integration with Circular Exchange Framework (CEFR) for reactive updates.
"""

import logging
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from enum import Enum

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

logger = logging.getLogger(__name__)

# Register module with Circular Exchange
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="shared.models.schemas",
            file_path=__file__,
            description="Unified output schema for text detection algorithms",
            dependencies=["shared.circular_exchange"],
            exports=["BoundingBox", "DetectedText", "DetectionResult", "ErrorCode"]
        ))
    except Exception as e:
        logger.debug(f"Module registration skipped: {e}")


class ErrorCode(Enum):
    """Structured error codes for text detection operations."""
    MODEL_NOT_READY = "model_not_ready"
    TIMEOUT = "timeout"
    INVALID_IMAGE = "invalid_image"
    PROCESSING_FAILED = "processing_failed"
    MISSING_DEPENDENCIES = "missing_dependencies"
    INSUFFICIENT_MEMORY = "insufficient_memory"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class BoundingBox:
    """Represents a bounding box for detected text region."""
    x: int
    y: int
    width: int
    height: int
    
    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary format."""
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> 'BoundingBox':
        """Create BoundingBox from dictionary."""
        return cls(
            x=data['x'],
            y=data['y'],
            width=data['width'],
            height=data['height']
        )
    
    @classmethod
    def from_coords(cls, x1: int, y1: int, x2: int, y2: int) -> 'BoundingBox':
        """Create BoundingBox from coordinates (x1, y1, x2, y2)."""
        return cls(
            x=min(x1, x2),
            y=min(y1, y2),
            width=abs(x2 - x1),
            height=abs(y2 - y1)
        )
    
    def area(self) -> int:
        """Calculate bounding box area."""
        return self.width * self.height
    
    def iou(self, other: 'BoundingBox') -> float:
        """
        Calculate Intersection over Union (IoU) with another bounding box.
        
        Args:
            other: Another BoundingBox instance
            
        Returns:
            IoU value between 0 and 1
        """
        # Calculate intersection coordinates
        x1 = max(self.x, other.x)
        y1 = max(self.y, other.y)
        x2 = min(self.x + self.width, other.x + other.width)
        y2 = min(self.y + self.height, other.y + other.height)
        
        # Calculate intersection area
        if x2 < x1 or y2 < y1:
            return 0.0
        
        intersection = (x2 - x1) * (y2 - y1)
        
        # Calculate union area
        area1 = self.area()
        area2 = other.area()
        union = area1 + area2 - intersection
        
        if union == 0:
            return 0.0
        
        return intersection / union


@dataclass
class DetectedText:
    """Represents a single detected text region with metadata."""
    text: str
    confidence: float
    bbox: BoundingBox
    language: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        result = {
            'text': self.text,
            'confidence': self.confidence,
            'bbox': self.bbox.to_dict()
        }
        if self.language:
            result['language'] = self.language
        if self.attributes:
            result['attributes'] = self.attributes
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DetectedText':
        """Create DetectedText from dictionary."""
        return cls(
            text=data['text'],
            confidence=data['confidence'],
            bbox=BoundingBox.from_dict(data['bbox']),
            language=data.get('language'),
            attributes=data.get('attributes', {})
        )


@dataclass
class DetectionResult:
    """
    Unified result format for all text detection algorithms.
    
    This standardized schema ensures consistent output across:
    - Tesseract OCR
    - EasyOCR
    - PaddleOCR
    - Donut
    - Florence-2
    - CRAFT
    - Spatial Multi-Method
    """
    texts: List[DetectedText]
    metadata: Dict[str, Any]
    processing_time: float
    model_id: str
    success: bool = True
    error_code: Optional[ErrorCode] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        result = {
            'texts': [t.to_dict() for t in self.texts],
            'metadata': self.metadata,
            'processing_time': self.processing_time,
            'model_id': self.model_id,
            'success': self.success
        }
        if self.error_code:
            result['error_code'] = self.error_code.value
        if self.error_message:
            result['error_message'] = self.error_message
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DetectionResult':
        """Create DetectionResult from dictionary."""
        return cls(
            texts=[DetectedText.from_dict(t) for t in data['texts']],
            metadata=data['metadata'],
            processing_time=data['processing_time'],
            model_id=data['model_id'],
            success=data.get('success', True),
            error_code=ErrorCode(data['error_code']) if data.get('error_code') else None,
            error_message=data.get('error_message')
        )
    
    @classmethod
    def create_error(
        cls,
        error_code: ErrorCode,
        error_message: str,
        model_id: str,
        processing_time: float = 0.0
    ) -> 'DetectionResult':
        """Create an error result."""
        return cls(
            texts=[],
            metadata={},
            processing_time=processing_time,
            model_id=model_id,
            success=False,
            error_code=error_code,
            error_message=error_message
        )


__all__ = [
    'BoundingBox',
    'DetectedText',
    'DetectionResult',
    'ErrorCode'
]
