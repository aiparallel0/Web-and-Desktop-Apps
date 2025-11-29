"""
Common OCR processing utilities shared across all OCR processors.

This module provides:
- Pre-compiled regex patterns for efficient matching
- Shared constants like SKIP_KEYWORDS
- Common price normalization function
- Reusable text extraction utilities
"""
import re
from decimal import Decimal
from typing import Optional

# Price validation constants
PRICE_MIN = Decimal('0')
PRICE_MAX = Decimal('9999')

# Keywords to skip when extracting line items
SKIP_KEYWORDS = frozenset({
    'subtotal', 'total', 'cash', 'change', 'tax', 'payment', 'balance',
    'thank', 'visit', 'welcome', 'receipt', 'cashier', 'card', 'debit',
    'credit', 'approved', 'transaction', 'visa', 'mastercard', 'amex'
})

# Pre-compiled regex patterns for performance
# Order matters - more specific patterns first
DATE_PATTERNS = [
    re.compile(r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})'),  # ISO format: 2024-01-15
    re.compile(r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})'),  # US format with 4-digit year: 12/25/2024
    re.compile(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2})'),  # US format with 2-digit year: 12/25/24
    re.compile(r'(\w{3}\s+\d{1,2},?\s+\d{4})'),    # Month format: Jan 15, 2024
]

TOTAL_PATTERNS = [
    re.compile(r'total[:\s]*\$?\s*(\d+[.,]\d{2})', re.IGNORECASE),
    re.compile(r'amount[:\s]*\$?\s*(\d+[.,]\d{2})', re.IGNORECASE),
    re.compile(r'balance[:\s]*\$?\s*(\d+[.,]\d{2})', re.IGNORECASE),
    re.compile(r'grand\s*total[:\s]*\$?\s*(\d+[.,]\d{2})', re.IGNORECASE),
]

PHONE_PATTERNS = [
    re.compile(r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'),
    re.compile(r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})'),
]

LINE_ITEM_PATTERNS = [
    re.compile(r'^(.+?)\s+\$?\s*(\d+[.,]\d{2})$'),
    re.compile(r'^(.+?)\s+(\d+[.,]\d{2})\s*$'),
    re.compile(r'^(.+?)\s+\$\s*(\d+[.,]\d{2})$'),
]

# Address keywords for detection
ADDRESS_KEYWORDS = frozenset({
    'st', 'ave', 'rd', 'blvd', 'lane', 'drive', 'street',
    'avenue', 'way', 'plaza', 'court', 'circle'
})


def normalize_price(value) -> Optional[Decimal]:
    """
    Normalize a price value to a Decimal.
    
    Handles various price formats:
    - $25.99
    - 1,234.56 (US format with comma as thousand separator)
    - 12,50 (European format with comma as decimal separator)
    
    Args:
        value: Price value (string, number, or None)
        
    Returns:
        Decimal price or None if invalid
    """
    if value is None:
        return None
    try:
        price_str = str(value).replace('$', '').replace(' ', '').strip()
        if not price_str or price_str.startswith('-'):
            return None
        # Handle thousands separator vs decimal separator
        # If string has format like "1,234.56" - comma is thousands separator
        # If string has format like "12,50" - comma is decimal separator
        if ',' in price_str and '.' in price_str:
            # Both present: assume comma is thousands separator
            price_str = price_str.replace(',', '')
        elif ',' in price_str:
            # Only comma: could be thousands or decimal separator
            # If exactly 2 digits after comma, treat as decimal
            parts = price_str.split(',')
            if len(parts) == 2 and len(parts[1]) == 2:
                price_str = price_str.replace(',', '.')
            else:
                # Otherwise treat comma as thousands separator
                price_str = price_str.replace(',', '')
        val = Decimal(price_str)
        return val if PRICE_MIN <= val <= PRICE_MAX else None
    except (ValueError, ArithmeticError):
        return None


def extract_date(lines: list) -> Optional[str]:
    """
    Extract date from a list of text lines.
    
    Args:
        lines: List of text lines
        
    Returns:
        Date string or None
    """
    for line in lines:
        for pattern in DATE_PATTERNS:
            match = pattern.search(line)
            if match:
                return match.group(1)
    return None


def extract_total(lines: list) -> Optional[Decimal]:
    """
    Extract total amount from a list of text lines.
    
    Args:
        lines: List of text lines
        
    Returns:
        Decimal total or None
    """
    for pattern in TOTAL_PATTERNS:
        for line in lines:
            match = pattern.search(line)
            if match:
                total_str = match.group(1).replace(',', '.')
                total_val = normalize_price(total_str)
                if total_val:
                    return total_val
    return None


def extract_phone(lines: list) -> Optional[str]:
    """
    Extract phone number from a list of text lines.
    
    Args:
        lines: List of text lines
        
    Returns:
        Phone number string or None
    """
    for line in lines:
        for pattern in PHONE_PATTERNS:
            match = pattern.search(line)
            if match:
                return match.group(1)
    return None


def extract_address(lines: list, start_index: int = 1, end_index: int = 8) -> Optional[str]:
    """
    Extract address from a list of text lines.
    
    Args:
        lines: List of text lines
        start_index: Start index to search from
        end_index: End index to search until
        
    Returns:
        Address string or None
    """
    for line in lines[start_index:end_index]:
        line_lower = line.lower()
        if any(kw in line_lower for kw in ADDRESS_KEYWORDS) and any(c.isdigit() for c in line):
            return line
    return None


def should_skip_line(line: str) -> bool:
    """
    Check if a line should be skipped when extracting items.
    
    Args:
        line: Text line to check
        
    Returns:
        True if line should be skipped
    """
    line_lower = line.lower()
    return any(kw in line_lower for kw in SKIP_KEYWORDS)


def extract_store_name(lines: list, max_lines: int = 5) -> Optional[str]:
    """
    Extract store name from the first few lines.
    
    Args:
        lines: List of text lines
        max_lines: Maximum lines to search
        
    Returns:
        Store name or None
    """
    for line in lines[:max_lines]:
        line = line.strip()
        if len(line) >= 2 and not line.isdigit():
            return line
    return lines[0] if lines else None
