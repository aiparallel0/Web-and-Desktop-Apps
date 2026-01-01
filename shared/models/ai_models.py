"""
AI Models Re-export Module with CEFR Integration.

This module provides backward compatibility by re-exporting AI model processors
from the engine module where they are now consolidated. It ensures that imports
like `from shared.models.ai_models import DonutProcessor` work correctly.

CEFR NOTE: This module was created to fix missing import errors. All AI model
processors are now consolidated in engine.py, but this re-export module maintains
backward compatibility with existing code that imports from ai_models.

Module ID: shared.models.ai_models
"""
import logging

logger = logging.getLogger(__name__)

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

# Re-export from engine module
from .engine import (
    BaseDonutProcessor,
    DonutProcessor,
    FlorenceProcessor,
)

__all__ = [
    'BaseDonutProcessor',
    'DonutProcessor',
    'FlorenceProcessor',
]
