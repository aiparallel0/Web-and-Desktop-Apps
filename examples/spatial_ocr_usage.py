"""
Example: Using the Spatial Multi-Method OCR Processor

This example demonstrates how to use the spatial OCR processor to extract
receipt data using multiple OCR engines with spatial bounding box analysis.
"""

from shared.models.spatial_ocr import SpatialOCRProcessor, BoundingBox, TextRegion
from shared.models.manager import ModelManager


def example_basic_usage():
    """Basic usage example of spatial OCR processor."""
    
    # Method 1: Direct instantiation
    print("=" * 60)
    print("Example 1: Direct instantiation of SpatialOCRProcessor")
    print("=" * 60)
    
    processor = SpatialOCRProcessor()
    
    # Check which OCR engines are available
    print(f"Tesseract available: {processor.has_tesseract}")
    print(f"EasyOCR available: {processor.has_easyocr}")
    print(f"PaddleOCR available: {processor.has_paddleocr}")
    print()


def example_via_model_manager():
    """Example using spatial OCR through model manager."""
    
    print("=" * 60)
    print("Example 2: Using Spatial OCR via Model Manager")
    print("=" * 60)
    
    manager = ModelManager()
    
    # List spatial model
    for model in manager.get_available_models():
        if model['id'] == 'spatial_multi':
            print(f"  ✓ {model['name']} - {model['description']}")
    print()


if __name__ == '__main__':
    example_basic_usage()
    example_via_model_manager()
