"""
Analytics module for Receipt Extractor

Provides event tracking, conversion funnel analysis, and metrics collection.
"""
import logging

# Circular Exchange Framework Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False

logger = logging.getLogger(__name__)

# Register module
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="web.backend.analytics",
            file_path=__file__,
            description="Analytics module for event tracking and conversion funnels",
            dependencies=[],
            exports=["events", "tracker", "conversion_funnel"]
        ))
    except Exception:
        pass

__all__ = [
    'events',
    'tracker',
    'conversion_funnel'
]
