"""
Processors Re-export Module with CEFR Integration and Telemetry.

This module provides backward compatibility by re-exporting OCR processors
from the engine module where they are now consolidated. It ensures that imports
like `from shared.models.processors import EasyOCRProcessor` work correctly.

CEFR NOTE: This module was created to fix missing import errors. All OCR
processors are now consolidated in engine.py, but this re-export module
maintains backward compatibility with existing code that imports from processors.

Telemetry: Tracks module import and re-export operations for observability.

Module ID: shared.models.processors
"""
import logging

logger = logging.getLogger(__name__)

# Telemetry integration
try:
    from shared.utils.telemetry import get_tracer, set_span_attributes
    TELEMETRY_AVAILABLE = True
except ImportError:
    TELEMETRY_AVAILABLE = False

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

# Register module with Circular Exchange
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="shared.models.processors",
            file_path=__file__,
            description="Re-export module for OCR processors (EasyOCR, PaddleOCR) with telemetry",
            dependencies=["shared.models.engine"],
            exports=["BaseProcessor", "EasyOCRProcessor", "PaddleProcessor",
                    "ProcessorInitializationError", "ProcessorHealthCheckError"]
        ))
    except Exception as e:
        logger.debug(f"Module registration skipped: {e}")

# Re-export from engine module with telemetry tracking
if TELEMETRY_AVAILABLE:
    tracer = get_tracer()
    with tracer.start_as_current_span("processors.module_import") as span:
        try:
            set_span_attributes(span, {
                "operation.type": "module_reexport",
                "module.id": "shared.models.processors",
                "reexport.source": "shared.models.engine",
                "reexport.count": 5
            })
            
            from .engine import (
                BaseProcessor,
                EasyOCRProcessor,
                PaddleProcessor,
                ProcessorInitializationError,
                ProcessorHealthCheckError,
            )
            
            set_span_attributes(span, {
                "operation.success": True,
                "processors.available": True
            })
        except Exception as e:
            span.record_exception(e)
            set_span_attributes(span, {
                "operation.success": False,
                "error.type": type(e).__name__
            })
            raise
else:
    # Fallback without telemetry
    from .engine import (
        BaseProcessor,
        EasyOCRProcessor,
        PaddleProcessor,
        ProcessorInitializationError,
        ProcessorHealthCheckError,
    )

__all__ = [
    'BaseProcessor',
    'EasyOCRProcessor',
    'PaddleProcessor',
    'ProcessorInitializationError',
    'ProcessorHealthCheckError',
]
