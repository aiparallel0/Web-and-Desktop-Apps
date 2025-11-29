"""
=============================================================================
OCR MODELS PACKAGE - AI/ML Model Management Infrastructure
=============================================================================

This package implements enterprise-grade AI/ML model management following
patterns from production machine learning systems at scale.

Architecture:
┌─────────────────────────────────────────────────────────────────────────┐
│                         Model Management Layer                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐  │
│  │   ModelManager   │    │  BaseProcessor   │    │  ModelConfig     │  │
│  │ (Central Control)│    │ (Abstract Base)  │    │  (Settings)      │  │
│  └────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘  │
│           │                       │                        │            │
│           ▼                       ▼                        ▼            │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    Processor Implementations                       │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │  │
│  │  │ EasyOCR  │  │ Paddle   │  │  Donut   │  │    Florence-2    │  │  │
│  │  │ Processor│  │ Processor│  │ Processor│  │    Processor     │  │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

Model Types:
- OCR Models: EasyOCR, PaddleOCR (Traditional OCR)
- AI Models: Donut, Florence-2 (Transformer-based)

Features:
- Lazy Loading: Models loaded on-demand to conserve memory
- LRU Caching: Automatic eviction of least-recently-used models
- GPU Detection: Automatic CUDA/CPU fallback
- Health Checks: Model health monitoring
- Retry Logic: Resilient model loading

Integration with Circular Exchange:
    from shared.circular_exchange import CircularExchange
    from shared.models import ModelManager
    
    exchange = CircularExchange.get_instance()
    manager = ModelManager()
    
    # Create reactive model state
    model_state = exchange.create_package('model_state', initial_value={
        'current_model': manager.get_current_model(),
        'loaded_models': []
    })

=============================================================================
"""

from typing import TYPE_CHECKING

# Lazy imports to avoid import errors when optional dependencies not installed
_LAZY_IMPORTS = {
    'BaseProcessor': ('processors', 'BaseProcessor'),
    'EasyOCRProcessor': ('processors', 'EasyOCRProcessor'),
    'PaddleProcessor': ('processors', 'PaddleProcessor'),
    'ProcessorInitializationError': ('processors', 'ProcessorInitializationError'),
    'ProcessorHealthCheckError': ('processors', 'ProcessorHealthCheckError'),
    'DonutProcessor': ('ai_models', 'DonutProcessor'),
    'FlorenceProcessor': ('ai_models', 'FlorenceProcessor'),
    'BaseDonutProcessor': ('ai_models', 'BaseDonutProcessor'),
    'ModelManager': ('model_manager', 'ModelManager'),
    'OCRProcessor': ('ocr_processor', 'OCRProcessor'),
}


def __getattr__(name: str):
    """
    Lazy import handler for model components.
    
    This pattern enables:
    - Fast initial imports
    - Graceful handling of missing optional dependencies
    - Reduced memory footprint until models are needed
    """
    if name in _LAZY_IMPORTS:
        module_name, class_name = _LAZY_IMPORTS[name]
        try:
            import importlib
            module = importlib.import_module(f'.{module_name}', package='shared.models')
            return getattr(module, class_name)
        except ImportError as e:
            raise ImportError(
                f"Could not import {name} from shared.models.{module_name}. "
                f"This may require additional dependencies. Error: {e}"
            )
    
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
    elif name == 'normalize_price':
        from .ocr_common import normalize_price
        return normalize_price
    elif name == 'SKIP_KEYWORDS':
        from .ocr_common import SKIP_KEYWORDS
        return SKIP_KEYWORDS
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Base Classes
    'BaseProcessor',
    'ProcessorInitializationError',
    'ProcessorHealthCheckError',
    # OCR Processors
    'EasyOCRProcessor',
    'PaddleProcessor',
    'OCRProcessor',
    # AI Processors
    'DonutProcessor',
    'FlorenceProcessor',
    'BaseDonutProcessor',
    # Management
    'ModelManager'
    'ModelManager',
    'OCRProcessor',
    'normalize_price',
    'SKIP_KEYWORDS'
]

__version__ = '2.0.0'
