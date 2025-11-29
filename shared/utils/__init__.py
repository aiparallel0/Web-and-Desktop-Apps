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
    resize_if_needed
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
]
