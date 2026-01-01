"""
Marketing automation module for Receipt Extractor

This module provides email marketing, automation workflows, and campaign management.
"""
import logging

logger = logging.getLogger(__name__)

# CEFR integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False

# Register module
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="web.backend.marketing",
            file_path=__file__,
            description="Marketing automation module for email sequences and campaigns",
            dependencies=[],
            exports=["email_sequences", "email_sender", "automation"]
        ))
    except Exception as e:
        logger.debug(f"Module registration failed: {e}")
        pass

__all__ = [
    'email_sequences',
    'email_sender',
    'automation'
]
