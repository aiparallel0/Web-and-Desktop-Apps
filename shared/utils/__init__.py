"""
=============================================================================
UTILITIES PACKAGE - Cross-Cutting Concerns & Infrastructure
=============================================================================

This package provides enterprise-grade utilities and cross-cutting concerns
for the Receipt Extraction System.

Modules:
├── data_structures.py  - Domain models (LineItem, ReceiptData, ExtractionResult)
├── image_processing.py - Image manipulation and enhancement
└── logger.py           - Enterprise logging framework

Design Principles:
- Single Responsibility: Each utility serves one purpose
- Dependency Injection: Utilities can be injected for testability
- Thread Safety: All utilities are thread-safe
- Performance: Optimized for high-throughput processing

=============================================================================
"""

from .data_structures import (
    LineItem,
    ReceiptData,
    ExtractionResult,
    StoreInfo,
    TransactionTotals,
    ExtractionStatus
)
from .image_processing import (
    load_and_validate_image,
    enhance_image,
    assess_image_quality,
    preprocess_for_ocr,
    resize_if_needed,
    detect_text_regions,
    preprocess_multi_pass
)
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

__all__ = [
    # Data Structures
    'LineItem',
    'ReceiptData',
    'ExtractionResult',
    'StoreInfo',
    'TransactionTotals',
    'ExtractionStatus',
    # Image Processing
from .centralized_logging import (
    get_module_logger,
    set_context,
    get_context,
    clear_context,
    logging_context,
    log_errors,
    log_with_context,
    ErrorHandler,
)
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
from .logger import setup_logger, get_logger, log_with_context

__all__ = [
    # Data structures
    'LineItem',
    'ReceiptData',
    'ExtractionResult',
    # Image processing
    'load_and_validate_image',
    'enhance_image',
    'assess_image_quality',
    'preprocess_for_ocr',
    'resize_if_needed',
    # Logging
    'setup_logger',
    'get_logger',
    'log_with_context',
    'log_function_call',
    'log_operation',
    'LogContext',
    'LogLevel',
    'generate_correlation_id',
    'get_default_logger'
    # Centralized logging - automatically available when importing from shared.utils
    'get_module_logger',
    'set_context',
    'get_context',
    'clear_context',
    'logging_context',
    'log_errors',
    'log_with_context',
    'ErrorHandler',
    'detect_text_regions',
    'preprocess_multi_pass',
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
    # Logging
    'setup_logger',
    'get_logger',
    'log_with_context'
]
