"""
=============================================================================
CIRCULAR EXCHANGE COMPLIANT MODULE
=============================================================================

Module: shared.utils
Path: shared/utils/__init__.py
Description: UTILITIES PACKAGE - Cross-Cutting Concerns & Infrastructure
Compliance Version: 2.0.0

CIRCULAR EXCHANGE INTEGRATION:
This module is integrated with the Circular Information Exchange Framework.
All changes are tracked and propagated through the reactive system.

Dependencies: shared.circular_exchange
Exports: LineItem, ReceiptData, ExtractionResult, image processing, logging, errors

AI AGENT INSTRUCTIONS:
- Use PROJECT_CONFIG for all configuration values
- Register this module with CircularExchange on import
- Use VariablePackages for shared data
- Subscribe to relevant change notifications

=============================================================================

UTILITIES PACKAGE - Cross-Cutting Concerns & Infrastructure

This package provides robust utilities and cross-cutting concerns
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
- Variable-Based Configuration: All settings from PROJECT_CONFIG

=============================================================================
"""

# =============================================================================
# CIRCULAR EXCHANGE INTEGRATION
# =============================================================================
try:
    from shared.circular_exchange.project_config import PROJECT_CONFIG, ModuleRegistration
    
    # Register this module with the circular exchange
    PROJECT_CONFIG.register_module(ModuleRegistration(
        module_id="shared.utils",
        file_path="shared/utils/__init__.py",
        description="Cross-Cutting Concerns & Infrastructure Utilities",
        dependencies=["shared.circular_exchange"],
        exports=[
            "LineItem", "ReceiptData", "ExtractionResult", "StoreInfo",
            "load_and_validate_image", "enhance_image", "setup_logger",
            "get_logger", "ReceiptExtractorError", "ValidationError"
        ],
        is_circular_exchange_compliant=True,
        compliance_version="2.0.0"
    ))
except ImportError:
    # Graceful fallback if circular exchange not available
    pass

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

__version__ = '2.0.0'
