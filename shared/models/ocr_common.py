"""
Compatibility module - re-exports from ocr.py.

This module exists for backwards compatibility with imports that expect
the module to be named 'ocr_common' rather than 'ocr'.
"""

# Re-export all public symbols from ocr.py
from .ocr import (
    SKIP_KEYWORDS,
    PRICE_MIN,
    PRICE_MAX,
    normalize_price,
    extract_date,
    extract_total,
    extract_phone,
    extract_address,
    should_skip_line,
    extract_store_name,
    LINE_ITEM_PATTERNS,
    clean_item_name,
    extract_line_items,
    parse_receipt_text,
    get_detection_config,
    record_detection_result,
    extract_subtotal,
    extract_tax,
    fix_concatenated_text,
    is_garbage_text,
    MAX_REALISTIC_ITEM_PRICE,
)

__all__ = [
    'SKIP_KEYWORDS',
    'PRICE_MIN',
    'PRICE_MAX',
    'normalize_price',
    'extract_date',
    'extract_total',
    'extract_phone',
    'extract_address',
    'should_skip_line',
    'extract_store_name',
    'LINE_ITEM_PATTERNS',
    'clean_item_name',
    'extract_line_items',
    'parse_receipt_text',
    'get_detection_config',
    'record_detection_result',
    'extract_subtotal',
    'extract_tax',
    'fix_concatenated_text',
    'is_garbage_text',
    'MAX_REALISTIC_ITEM_PRICE',
]
