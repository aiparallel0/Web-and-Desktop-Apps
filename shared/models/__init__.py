"""
OCR Models Package - Consolidated
Contains all OCR processors and AI model utilities
"""

# Lazy imports to avoid import errors when optional deps not installed
def __getattr__(name):
    if name == 'BaseProcessor':
        from .processors import BaseProcessor
        return BaseProcessor
    elif name == 'EasyOCRProcessor':
        from .processors import EasyOCRProcessor
        return EasyOCRProcessor
    elif name == 'PaddleProcessor':
        from .processors import PaddleProcessor
        return PaddleProcessor
    elif name == 'DonutProcessor':
        from .ai_models import DonutProcessor
        return DonutProcessor
    elif name == 'ModelManager':
        from .model_manager import ModelManager
        return ModelManager
    elif name == 'OCRProcessor':
        from .ocr_processor import OCRProcessor
        return OCRProcessor
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    'BaseProcessor',
    'EasyOCRProcessor', 
    'PaddleProcessor',
    'DonutProcessor',
    'ModelManager',
    'OCRProcessor'
]
