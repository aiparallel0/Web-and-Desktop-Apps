# Shared modules for receipt extraction
#
# This module automatically initializes centralized logging when imported.
# New files that import from 'shared' will automatically get logging configured.
#
# Usage:
#   from shared.utils import get_module_logger, log_errors
#   logger = get_module_logger()
#   
#   @log_errors
#   def my_function():
#       logger.info("Processing...")

# Auto-initialize centralized logging on import
from shared.utils.centralized_logging import (
    get_module_logger,
    log_errors,
    logging_context,
    set_context,
    clear_context,
    ErrorHandler,
)

__all__ = [
    'get_module_logger',
    'log_errors',
    'logging_context',
    'set_context',
    'clear_context',
    'ErrorHandler',
]