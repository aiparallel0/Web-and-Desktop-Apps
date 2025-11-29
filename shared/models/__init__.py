"""
=============================================================================
CIRCULAR EXCHANGE COMPLIANT MODULE
=============================================================================

Module: shared.models
Path: shared/models/__init__.py
Description: OCR MODELS PACKAGE - AI/ML Model Management Infrastructure
Compliance Version: 2.0.0

CIRCULAR EXCHANGE INTEGRATION:
This module is integrated with the Circular Information Exchange Framework.
All changes are tracked and propagated through the reactive system.

Dependencies: shared.circular_exchange
Exports: BaseProcessor, ModelManager, OCRProcessor, DonutProcessor, FlorenceProcessor

AI AGENT INSTRUCTIONS:
- Use PROJECT_CONFIG for all configuration values
- Register this module with CircularExchange on import
- Use VariablePackages for shared data
- Subscribe to relevant change notifications

=============================================================================

OCR MODELS PACKAGE - AI/ML Model Management Infrastructure

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
    from shared.circular_exchange import CircularExchange, PROJECT_CONFIG
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

# =============================================================================
# CIRCULAR EXCHANGE INTEGRATION
# =============================================================================
try:
    from shared.circular_exchange.project_config import PROJECT_CONFIG, ModuleRegistration
    
    # Register this module with the circular exchange
    PROJECT_CONFIG.register_module(ModuleRegistration(
        module_id="shared.models",
        file_path="shared/models/__init__.py",
        description="AI/ML Model Management Infrastructure",
        dependencies=["shared.circular_exchange"],
        exports=[
            "BaseProcessor", "EasyOCRProcessor", "PaddleProcessor",
            "DonutProcessor", "FlorenceProcessor", "ModelManager",
            "OCRProcessor", "normalize_price", "clean_item_name"
        ],
        is_circular_exchange_compliant=True,
        compliance_version="2.0.0"
    ))
except ImportError:
    # Graceful fallback if circular exchange not available
    pass

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
    'normalize_price': ('ocr_common', 'normalize_price'),
    'SKIP_KEYWORDS': ('ocr_common', 'SKIP_KEYWORDS'),
    'clean_item_name': ('ocr_common', 'clean_item_name'),
    'correct_store_name': ('ocr_common', 'correct_store_name'),
    'WORD_CORRECTIONS': ('ocr_common', 'WORD_CORRECTIONS'),
    'UNIT_CORRECTIONS': ('ocr_common', 'UNIT_CORRECTIONS'),
    'STORE_NAME_CORRECTIONS': ('ocr_common', 'STORE_NAME_CORRECTIONS'),
}


def __getattr__(name: str):
    """
    Lazy import handler for model components.
    
    This pattern enables:
    - Fast initial imports
    - Graceful handling of missing optional dependencies
    - Reduced memory footprint until models are needed
    
    CIRCULAR EXCHANGE NOTE:
    This lazy loading integrates with the circular exchange by deferring
    module registration until actual use, reducing startup overhead.
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
    'ModelManager',
    # OCR Utilities
    'normalize_price',
    'SKIP_KEYWORDS',
    'clean_item_name',
    'correct_store_name',
    'WORD_CORRECTIONS',
    'UNIT_CORRECTIONS',
    'STORE_NAME_CORRECTIONS',
]

__version__ = '2.0.0'
