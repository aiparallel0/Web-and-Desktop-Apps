from .data_structures import LineItem, ReceiptData, ExtractionResult
from .image_processing import (
    load_and_validate_image,
    enhance_image,
    assess_image_quality,
    preprocess_for_ocr,
    resize_if_needed,
    detect_text_regions,
    preprocess_multi_pass
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
