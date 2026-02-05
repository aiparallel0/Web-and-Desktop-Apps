"""
Utilities Package - Cross-Cutting Concerns & Infrastructure

Modules:
- data.py      - Domain models (LineItem, ReceiptData, ExtractionResult)
- image.py     - Image manipulation and enhancement
- logging.py   - Centralized logging with context support
- helpers.py   - Error handling and caching
"""

try:
    from shared.circular_exchange.project_config import PROJECT_CONFIG, ModuleRegistration
    PROJECT_CONFIG.register_module(ModuleRegistration(
        module_id="shared.utils",
        file_path=__file__,
        description="Utilities Package",
        dependencies=["shared.circular_exchange"],
        exports=["LineItem", "ReceiptData", "ExtractionResult", "load_and_validate_image", "get_module_logger"]
    ))
except ImportError:
    pass

# Data structures
from .data import (
    LineItem, ReceiptData, ExtractionResult, StoreInfo,
    TransactionTotals, ExtractionStatus
)

# Image processing - lazy import to avoid numpy dependency at package init
# These functions will be imported only when actually used
try:
    from .image import (
        load_and_validate_image, enhance_image, assess_image_quality,
        preprocess_for_ocr, resize_if_needed, detect_text_regions, preprocess_multi_pass
    )
    _IMAGE_AVAILABLE = True
except ImportError as e:
    _IMAGE_AVAILABLE = False
    # Create stub functions that raise helpful errors
    def _image_not_available(*args, **kwargs):
        raise ImportError(
            "Image processing functions require numpy and Pillow. "
            "Install with: pip install numpy pillow"
        )
    load_and_validate_image = _image_not_available
    enhance_image = _image_not_available
    assess_image_quality = _image_not_available
    preprocess_for_ocr = _image_not_available
    resize_if_needed = _image_not_available
    detect_text_regions = _image_not_available
    preprocess_multi_pass = _image_not_available

# Logging
from .logging import (
    setup_logger, get_logger, get_module_logger, get_default_logger,
    log_with_context, log_operation, log_function_call,
    LogContext, LogLevel, generate_correlation_id,
    set_context, get_context, clear_context, logging_context,
    log_errors, ErrorHandler
)

# Error handling and caching (from helpers)
from .helpers import (
    ErrorCategory, ErrorCode, ReceiptExtractorError, ValidationError,
    ProcessingError, ExternalServiceError, RateLimitError,
    create_error_response, handle_exception,
    LRUCache, cache_result, get_cache_stats, clear_all_caches
)

# Also export as AuthenticationError and AuthorizationError aliases
AuthenticationError = ReceiptExtractorError
AuthorizationError = ReceiptExtractorError
NotFoundError = ReceiptExtractorError

__all__ = [
    'LineItem', 'ReceiptData', 'ExtractionResult', 'StoreInfo',
    'TransactionTotals', 'ExtractionStatus',
    'load_and_validate_image', 'enhance_image', 'assess_image_quality',
    'preprocess_for_ocr', 'resize_if_needed', 'detect_text_regions', 'preprocess_multi_pass',
    'setup_logger', 'get_logger', 'get_module_logger', 'get_default_logger',
    'log_with_context', 'log_operation', 'log_function_call',
    'LogContext', 'LogLevel', 'generate_correlation_id',
    'set_context', 'get_context', 'clear_context', 'logging_context',
    'log_errors', 'ErrorHandler',
    'ErrorCategory', 'ErrorCode', 'ReceiptExtractorError', 'ValidationError',
    'AuthenticationError', 'AuthorizationError', 'NotFoundError',
    'ProcessingError', 'ExternalServiceError', 'RateLimitError',
    'create_error_response', 'handle_exception',
    'LRUCache', 'cache_result', 'get_cache_stats', 'clear_all_caches'
]

__version__ = '2.0.0'
