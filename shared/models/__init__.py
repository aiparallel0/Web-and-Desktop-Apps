# Only import ModelManager by default to avoid dependency issues
# Other processors will be imported dynamically by ModelManager when needed
from .model_manager import ModelManager

__all__ = ['ModelManager']

# Lazy imports for processors (imported by ModelManager when needed)
def _get_processor_class(processor_type):
    """Dynamically import processor classes to avoid dependency issues"""
    if processor_type in ('donut', 'florence'):
        from .donut_processor import DonutProcessor, FlorenceProcessor
        return DonutProcessor if processor_type == 'donut' else FlorenceProcessor
    elif processor_type == 'ocr':
        from .ocr_processor import OCRProcessor
        return OCRProcessor
    elif processor_type == 'paddle':
        from .paddle_processor import PaddleProcessor
        return PaddleProcessor
    elif processor_type == 'easyocr':
        from .easyocr_processor import EasyOCRProcessor
        return EasyOCRProcessor
    else:
        raise ValueError(f"Unknown processor type: {processor_type}")
