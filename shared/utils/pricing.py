"""
Pricing utilities for receipt processing

Consolidated from shared/models/ocr.py and shared/models/engine.py
This module provides price normalization and validation functions.
"""
import re
from decimal import Decimal
from typing import Optional

# Price constraints
PRICE_MIN = 0
PRICE_MAX = 9999


def normalize_price(value) -> Optional[Decimal]:
    """
    Normalize a price value to a Decimal.

    Handles various price formats:
    - $25.99
    - 1,234.56 (US format with comma as thousand separator)
    - 12,50 (European format with comma as decimal separator)
    - Rejects negative values and zip codes (5 or 9 digit numbers)

    Args:
        value: Price value (string, number, or None)

    Returns:
        Decimal price or None if invalid

    Examples:
        >>> normalize_price("$25.99")
        Decimal('25.99')
        >>> normalize_price("1,234.56")
        Decimal('1234.56')
        >>> normalize_price("12,50")
        Decimal('12.50')
        >>> normalize_price("-10.00")
        None
        >>> normalize_price("12345")  # Zip code
        None
    """
    if value is None:
        return None

    try:
        price_str = str(value).replace('$', '').replace(' ', '').strip()

        if not price_str or price_str.startswith('-'):
            return None

        # Reject zip codes (5 or 9 digit numbers like 12345 or 12345-6789)
        if re.match(r'^\d{5}(-?\d{4})?$', price_str):
            return None

        # Handle thousands separator vs decimal separator
        # If string has format like "1,234.56" - comma is thousands separator
        # If string has format like "12,50" - comma is decimal separator (European)
        if ',' in price_str and '.' in price_str:
            # Both present: assume comma is thousands separator, remove all commas
            price_str = price_str.replace(',', '')
        elif ',' in price_str:
            # Only comma: could be thousands or decimal separator
            comma_count = price_str.count(',')
            comma_pos = price_str.rfind(',')
            chars_after_comma = len(price_str) - comma_pos - 1

            if chars_after_comma == 2 and comma_count == 1:
                # Format like "12,50" - European decimal
                price_str = price_str.replace(',', '.')
            else:
                # Format like "1,234" or "1,234,567" - thousands separator
                price_str = price_str.replace(',', '')

        val = Decimal(price_str)
        return val if PRICE_MIN <= val <= PRICE_MAX else None

    except (ValueError, ArithmeticError):
        return None


def validate_price_range(price: Optional[Decimal], min_val: float = PRICE_MIN,
                        max_val: float = PRICE_MAX) -> bool:
    """
    Validate that a price is within the specified range.

    Args:
        price: Price to validate
        min_val: Minimum valid price
        max_val: Maximum valid price

    Returns:
        True if price is valid, False otherwise
    """
    if price is None:
        return False
    return min_val <= price <= max_val
