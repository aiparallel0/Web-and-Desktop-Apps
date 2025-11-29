"""
=============================================================================
UTILITIES PACKAGE - Cross-Cutting Concerns & Infrastructure
=============================================================================

This package provides enterprise-grade utilities and cross-cutting concerns
for the Receipt Extraction System.

Modules:
├── data_structures.py      - Domain models (LineItem, ReceiptData, ExtractionResult)
├── image_processing.py     - Image manipulation and enhancement
├── logger.py               - Enterprise logging framework
├── centralized_logging.py  - Centralized logging with context support
├── errors.py               - Custom error types and error handling

Design Principles:
- Single Responsibility: Each utility serves one purpose
- Dependency Injection: Utilities can be injected for testability
- Thread Safety: All utilities are thread-safe
- Performance: Optimized for high-throughput processing

=============================================================================
"""

# Data structures
from .data_structures import (
    LineItem,
    ReceiptData,
    ExtractionResult,
    StoreInfo,
    TransactionTotals,
    ExtractionStatus
)

# Image processing
from .image_processing import (
    load_and_validate_image,
    enhance_image,
    assess_image_quality,
    preprocess_for_ocr,
    resize_if_needed,
    detect_text_regions,
    preprocess_multi_pass
)

# Logging
from .logger import (
    setup_logger,
    get_logger,
    log_with_context,
    log_function_call,
    log_operation,
    LogContext,
    LogLevel,
    generate_correlation_id,
    get_default_logger
)

# Centralized logging
from .centralized_logging import (
    get_module_logger,
    set_context,
    get_context,
    clear_context,
    logging_context,
    log_errors,
    ErrorHandler,
)

# Error handling
from .errors import (
    ReceiptExtractorError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ProcessingError,
    RateLimitError,
    ExternalServiceError,
    ErrorCode,
    ErrorCategory,
    create_error_response,
    handle_exception,
    register_error_handlers
)

__all__ = [
    # Data structures
    'LineItem',
    'ReceiptData',
    'ExtractionResult',
    'StoreInfo',
    'TransactionTotals',
    'ExtractionStatus',
    # Image processing
    'load_and_validate_image',
    'enhance_image',
    'assess_image_quality',
    'preprocess_for_ocr',
    'resize_if_needed',
    'detect_text_regions',
    'preprocess_multi_pass',
    # Logging
    'setup_logger',
    'get_logger',
    'log_with_context',
    'log_function_call',
    'log_operation',
    'LogContext',
    'LogLevel',
    'generate_correlation_id',
    'get_default_logger',
    # Centralized logging
    'get_module_logger',
    'set_context',
    'get_context',
    'clear_context',
    'logging_context',
    'log_errors',
    'ErrorHandler',
    # Error handling
    'ReceiptExtractorError',
    'ValidationError',
    'AuthenticationError',
    'AuthorizationError',
    'NotFoundError',
    'ProcessingError',
    'RateLimitError',
    'ExternalServiceError',
    'ErrorCode',
    'ErrorCategory',
    'create_error_response',
    'handle_exception',
    'register_error_handlers',
]
