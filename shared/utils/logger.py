"""
Enterprise Logging Framework - Re-export Module

This module re-exports logging functionality from centralized_logging.py
for backward compatibility. All new code should import directly from
shared.utils.centralized_logging.

Usage:
    from shared.utils.logger import setup_logger, get_logger, LogContext
    
    # Create application logger
    logger = setup_logger('receipt_extractor', level='INFO')
    
    # Use context for correlation
    with LogContext(request_id='abc123', user_id='user456'):
        logger.info('Processing receipt')
"""
from enum import Enum
import logging

# Circular Exchange Framework Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False

if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="shared.utils.logger",
            file_path=__file__,
            description="Re-export module for backward compatibility (use centralized_logging)",
            dependencies=["shared.utils.centralized_logging"],
            exports=["setup_logger", "get_logger", "LogContext", "LogLevel",
                    "log_with_context", "log_operation", "generate_correlation_id"]
        ))
    except Exception:
        pass

# Re-export from centralized_logging
from shared.utils.centralized_logging import (
    setup_logger,
    get_logger,
    get_module_logger,
    LogContext,
    log_with_context,
    log_operation,
    generate_correlation_id,
    log_function_call,
    StructuredJSONFormatter as StructuredFormatter,
    ColoredTextFormatter as ColoredFormatter,
    set_context,
    get_context,
    clear_context,
    logging_context,
    log_errors,
    ErrorHandler,
)

# Module-level default logger
_default_logger = None

def get_default_logger() -> logging.Logger:
    """Get or create the default application logger."""
    global _default_logger
    if _default_logger is None:
        _default_logger = setup_logger('receipt_extractor', level='INFO')
    return _default_logger

class LogLevel(Enum):
    """Standardized log levels."""
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'

__all__ = [
    'setup_logger',
    'get_logger',
    'get_module_logger',
    'get_default_logger',
    'LogContext',
    'LogLevel',
    'log_with_context',
    'log_operation',
    'log_function_call',
    'generate_correlation_id',
    'StructuredFormatter',
    'ColoredFormatter',
    'set_context',
    'get_context',
    'clear_context',
    'logging_context',
    'log_errors',
    'ErrorHandler',
]
