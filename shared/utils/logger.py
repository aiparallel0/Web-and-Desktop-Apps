"""
Logging Re-export Module (Backward Compatibility)

This module re-exports logging functionality from centralized_logging.py.
All new code should import directly from shared.utils.centralized_logging.
"""
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    PROJECT_CONFIG.register_module(ModuleRegistration(
        module_id="shared.utils.logger",
        file_path=__file__,
        description="Re-export module for backward compatibility",
        dependencies=["shared.utils.centralized_logging"],
        exports=["setup_logger", "get_logger", "LogContext", "LogLevel"]
    ))
except Exception:
    pass

from shared.utils.centralized_logging import (
    setup_logger, get_logger, get_module_logger, get_default_logger,
    LogContext, LogLevel, log_with_context, log_operation, log_function_call,
    generate_correlation_id, set_context, get_context, clear_context,
    logging_context, log_errors, ErrorHandler,
    StructuredJSONFormatter as StructuredFormatter,
    ColoredTextFormatter as ColoredFormatter,
)

__all__ = [
    'setup_logger', 'get_logger', 'get_module_logger', 'get_default_logger',
    'LogContext', 'LogLevel', 'log_with_context', 'log_operation',
    'log_function_call', 'generate_correlation_id', 'StructuredFormatter',
    'ColoredFormatter', 'set_context', 'get_context', 'clear_context',
    'logging_context', 'log_errors', 'ErrorHandler',
]
