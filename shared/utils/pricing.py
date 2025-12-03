"""
Pricing Utilities Module

Consolidated pricing-related utility functions for the Receipt Extractor application.
This module provides centralized price normalization and validation to eliminate
code duplication across multiple modules.

Created as part of code optimization initiative to consolidate duplicate
normalize_price() functions found in:
- shared/models/engine.py
- shared/models/ocr.py
"""
from decimal import Decimal
from typing import Optional
import logging

# Circular Exchange Framework Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False

logger = logging.getLogger(__name__)

# Register module with Circular Exchange
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="shared.utils.pricing",
            file_path=__file__,
            description="Centralized pricing utilities with price normalization and validation",
            dependencies=[],
            exports=["normalize_price", "PRICE_MIN", "PRICE_MAX"]
        ))
    except Exception:
        pass  # Ignore registration errors

# Price validation constants
PRICE_MIN = Decimal('0')
PRICE_MAX = Decimal('9999')
# Maximum realistic price for a single grocery/retail item
# Items priced above this threshold are likely OCR errors


def normalize_price(value) -> Optional[Decimal]:
    """
    Normalize a price value to a Decimal with comprehensive format support.

    Handles various international price formats:
    - $25.99 (US format with currency symbol)
    - 1,234.56 (US format with comma as thousand separator)
    - 12,50 (European format with comma as decimal separator)
    - 1234.56 (No separators)
    - Negative prices (rejected)
    - ZIP codes that look like prices (rejected)

    Args:
        value: Price value (string, number, Decimal, or None)

    Returns:
        Decimal price between PRICE_MIN and PRICE_MAX, or None if invalid

    Examples:
        >>> normalize_price("$25.99")
        Decimal('25.99')
        >>> normalize_price("1,234.56")
        Decimal('1234.56')
        >>> normalize_price("12,50")  # European format
        Decimal('12.50')
        >>> normalize_price("-5.00")  # Negative
        None
        >>> normalize_price("12345")  # Looks like ZIP code
        None
        >>> normalize_price("99999")  # Above PRICE_MAX
        None
    """
    if value is None:
        return None

    try:
        # Convert to string and remove currency symbols and spaces
        price_str = str(value).replace('$', '').replace(' ', '').strip()

        # Reject empty or negative prices
        if not price_str or price_str.startswith('-'):
            return None

        # Reject ZIP code format (5 digits or 5+4 digits)
        # e.g., "12345" or "12345-6789"
        import re
        if re.match(r'^\d{5}(-?\d{4})?$', price_str):
            return None

        # Handle thousands separator vs decimal separator
        # Complex logic to distinguish between US and European formats

        if ',' in price_str and '.' in price_str:
            # Both present: assume comma is thousands separator, remove all commas
            # e.g., "1,234.56" -> "1234.56"
            price_str = price_str.replace(',', '')

        elif ',' in price_str:
            # Only comma: could be thousands or decimal separator
            comma_count = price_str.count(',')
            parts = price_str.split(',')

            # Validate proper thousands separator format (groups of 3)
            if comma_count > 1:
                # Multiple commas: validate each segment has 3 digits
                # e.g., "1,234,567" -> valid, "1,23,4" -> invalid
                is_valid_thousands = (
                    len(parts[0]) >= 1 and
                    all(len(p) == 3 for p in parts[1:])
                )
                if is_valid_thousands:
                    price_str = price_str.replace(',', '')
                else:
                    return None  # Invalid format

            # If single comma with exactly 2 digits after, treat as decimal (e.g., "12,50")
            elif len(parts) == 2 and len(parts[1]) == 2:
                price_str = price_str.replace(',', '.')

            # If single comma with exactly 3 digits after, treat as thousands separator (e.g., "1,234")
            elif len(parts) == 2 and len(parts[1]) == 3:
                price_str = price_str.replace(',', '')

            else:
                # Ambiguous format - could be European decimal or invalid thousands
                # Default: treat as invalid to avoid incorrect conversions
                return None

        # Convert to Decimal
        val = Decimal(price_str)

        # Validate price is within realistic bounds
        return val if PRICE_MIN <= val <= PRICE_MAX else None

    except (ValueError, ArithmeticError):
        # Invalid numeric format
        return None


__all__ = ['normalize_price', 'PRICE_MIN', 'PRICE_MAX']
