"""
Common OCR processing utilities shared across all OCR processors.

This module provides:
- Pre-compiled regex patterns for efficient matching
- Shared constants like SKIP_KEYWORDS
- Common price normalization function
- Reusable text extraction utilities
- Text post-processing and cleaning utilities
"""
import re
from decimal import Decimal
from typing import Optional, List, Tuple

# Price validation constants
PRICE_MIN = Decimal('0')
PRICE_MAX = Decimal('9999')

# Keywords to skip when extracting line items
SKIP_KEYWORDS = frozenset({
    'subtotal', 'total', 'cash', 'change', 'tax', 'payment', 'balance',
    'thank', 'visit', 'welcome', 'receipt', 'cashier', 'card', 'debit',
    'credit', 'approved', 'transaction', 'visa', 'mastercard', 'amex'
})

# Additional keywords to skip in item names (store info, hours, etc.)
ITEM_SKIP_PATTERNS = frozenset({
    'store', 'thank', 'visit', 'phone', 'fax', 'email', 
    'open', 'hours', 'daily', 'am', 'pm'
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
    re.compile(r'total[:\s]*\$?\s*(\d+[.,]?\d{0,2})', re.IGNORECASE),
    re.compile(r'amount[:\s]*\$?\s*(\d+[.,]?\d{0,2})', re.IGNORECASE),
    re.compile(r'balance[:\s]*\$?\s*(\d+[.,]?\d{0,2})', re.IGNORECASE),
    re.compile(r'grand\s*total[:\s]*\$?\s*(\d+[.,]?\d{0,2})', re.IGNORECASE),
]

PHONE_PATTERNS = [
    re.compile(r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'),
    re.compile(r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})'),
]

LINE_ITEM_PATTERNS = [
    # Standard formats: ITEM NAME   $XX.XX or ITEM NAME XX.XX
    re.compile(r'^(.+?)\s+\$?\s*(\d+[.,]\d{2})$'),
    re.compile(r'^(.+?)\s+(\d+[.,]\d{2})\s*$'),
    re.compile(r'^(.+?)\s+\$\s*(\d+[.,]\d{2})$'),
    # Format with SKU: SKU  ITEM NAME  XX.XX (12-14 digit SKU)
    re.compile(r'^\d{12,14}\s+(.+?)\s+\$?\s*(\d+[.,]\d{2})$'),
    # Format with tax code: ITEM NAME  XX.XX F/T/N/X
    re.compile(r'^(.+?)\s+(\d+[.,]\d{2})\s*[FTNX]$'),
    # Format with quantity: QTY x ITEM NAME  XX.XX
    re.compile(r'^(?:\d+\s*[xX*]\s*)?(.+?)\s+\$?\s*(\d+[.,]\d{2})$'),
]

# SKU pattern for receipt items (12-14 digits)
SKU_PATTERN = re.compile(r'\b\d{12,14}\b')

# Address keywords for detection
ADDRESS_KEYWORDS = frozenset({
    'st', 'ave', 'rd', 'blvd', 'lane', 'drive', 'street',
    'avenue', 'way', 'plaza', 'court', 'circle'
})

# Common OCR error corrections (character substitutions)
OCR_CORRECTIONS = {
    '0': 'O',  # Zero vs letter O
    'O': '0',
    '1': 'I',  # One vs letter I
    'I': '1',
    'l': '1',  # lowercase L vs one
    '5': 'S',  # Five vs letter S
    'S': '5',
    '8': 'B',  # Eight vs letter B
    'B': '8',
}

# Common word corrections for OCR errors
WORD_CORRECTIONS = {
    'tota1': 'total',
    't0tal': 'total',
    'subt0tal': 'subtotal',
    'subtota1': 'subtotal',
    'ca5h': 'cash',
    'chang3': 'change',
    'rec3ipt': 'receipt',
    'reciept': 'receipt',
    'receiept': 'receipt',
    # Receipt item OCR errors
    'fashiuned': 'fashioned',
    'plpper': 'pepper',
    'peppper': 'pepper',
    'oatmea1': 'oatmeal',
}

# Unit abbreviation corrections (case-sensitive patterns)
UNIT_CORRECTIONS = {
    ' 02': ' OZ',      # "10 02" -> "10 OZ" (ounces)
    ' 0Z': ' OZ',      # "10 0Z" -> "10 OZ"
    ' Oz': ' OZ',      # "10 Oz" -> "10 OZ"
    'ct': 'CT',        # "4ct" -> "4CT" (count)
    'Xt': 'XL',        # "Xt" -> "XL" (extra large)
    'X1': 'XL',        # "X1" -> "XL"
}

# Known store name corrections
STORE_NAME_CORRECTIONS = {
    'a ae)': "TRADER JOE'S",
    'trader joes': "TRADER JOE'S",
    'trader joe': "TRADER JOE'S",
    'wa1mart': 'WALMART',
    'wa1-mart': 'WALMART',
    'wal-mart': 'WALMART',
    'costc0': 'COSTCO',
    'target': 'TARGET',
    'who1e foods': 'WHOLE FOODS',
    'wholefoods': 'WHOLE FOODS',
    'kroger': 'KROGER',
    'safeway': 'SAFEWAY',
    'pub1ix': 'PUBLIX',
    'publix': 'PUBLIX',
}


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
        # If string has format like "12,50" - comma is decimal separator (European)
        if ',' in price_str and '.' in price_str:
            # Both present: assume comma is thousands separator, remove all commas
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


def should_skip_item_name(name: str) -> bool:
    """
    Check if an item name contains patterns that indicate it's not a product.
    
    Args:
        name: Item name to check
        
    Returns:
        True if name should be skipped
    """
    name_lower = name.lower()
    return any(pattern in name_lower for pattern in ITEM_SKIP_PATTERNS)


def clean_item_name(name: str) -> str:
    """
    Clean and correct common OCR errors in item names.
    
    Applies:
    - Word-level corrections (e.g., FASHIUNED -> FASHIONED)
    - Unit abbreviation fixes (e.g., "10 02" -> "10 OZ")
    - Removes trailing periods and extra punctuation
    - Normalizes whitespace
    
    Args:
        name: Raw item name from OCR
        
    Returns:
        Cleaned item name
    """
    if not name:
        return name
    
    cleaned = name.strip()
    
    # Apply word-level corrections (case-preserving)
    for wrong, correct in WORD_CORRECTIONS.items():
        # Find all matches and replace preserving case of original
        def preserve_case(match):
            matched_text = match.group(0)
            if matched_text.isupper():
                return correct.upper()
            elif matched_text.islower():
                return correct.lower()
            elif matched_text[0].isupper():
                return correct.capitalize()
            # For other cases, default to uppercase for OCR text
            return correct.upper()
        # Use re.escape to safely handle any regex special characters in the pattern
        cleaned = re.sub(rf'\b{re.escape(wrong)}\b', preserve_case, cleaned, flags=re.IGNORECASE)
    
    # Apply unit corrections (case-sensitive replacements)
    for wrong, correct in UNIT_CORRECTIONS.items():
        cleaned = cleaned.replace(wrong, correct)
    
    # Remove trailing periods and dots (but keep decimal points in prices)
    # Handle patterns like ". ." or "..."
    cleaned = re.sub(r'[\s.]+$', '', cleaned)  # Remove trailing dots and spaces
    cleaned = re.sub(r'\s*\.\s+\.', '', cleaned)  # Remove ". ." patterns
    
    # Remove pipe characters often misread at line ends
    cleaned = re.sub(r'\s*\|+\s*$', '', cleaned)
    
    # Normalize whitespace
    cleaned = ' '.join(cleaned.split())
    
    return cleaned.strip()


def correct_store_name(name: str) -> str:
    """
    Apply known store name corrections for common OCR errors.
    
    Args:
        name: Potentially incorrectly recognized store name
        
    Returns:
        Corrected store name if a match is found, otherwise original
    """
    if not name:
        return name
    
    name_lower = name.lower().strip()
    
    # Check for exact match first
    if name_lower in STORE_NAME_CORRECTIONS:
        return STORE_NAME_CORRECTIONS[name_lower]
    
    # Check if any known error pattern is contained in the name
    for wrong, correct in STORE_NAME_CORRECTIONS.items():
        if wrong in name_lower:
            return correct
    
    return name


def extract_store_name(lines: list, max_lines: int = 5) -> Optional[str]:
    """
    Extract store name from the first few lines.
    
    Applies store name corrections for common OCR errors.
    
    Args:
        lines: List of text lines
        max_lines: Maximum lines to search
        
    Returns:
        Store name or None
    """
    for line in lines[:max_lines]:
        line = line.strip()
        if len(line) >= 2 and not line.isdigit():
            # Apply store name corrections
            return correct_store_name(line)
    return correct_store_name(lines[0]) if lines else None


def clean_ocr_text(text: str) -> str:
    """
    Clean and correct common OCR errors in text.
    
    Args:
        text: Raw OCR text
        
    Returns:
        Cleaned text with common errors corrected
    """
    if not text:
        return text
    
    # Apply word-level corrections
    cleaned = text
    for wrong, correct in WORD_CORRECTIONS.items():
        cleaned = re.sub(rf'\b{wrong}\b', correct, cleaned, flags=re.IGNORECASE)
    
    # Remove excessive whitespace
    cleaned = ' '.join(cleaned.split())
    
    # Fix common punctuation issues
    cleaned = re.sub(r'\s+([.,;:!?])', r'\1', cleaned)  # Remove space before punctuation
    cleaned = re.sub(r'([.,;:!?])(?=[^\s\d])', r'\1 ', cleaned)  # Add space after punctuation
    
    return cleaned.strip()


def merge_text_lines(lines: List[str], threshold: float = 0.8) -> List[str]:
    """
    Merge text lines that likely belong together.
    
    Uses heuristics to combine lines that were split incorrectly by OCR.
    
    Args:
        lines: List of text lines
        threshold: Similarity threshold for merging
        
    Returns:
        Merged list of text lines
    """
    if not lines or len(lines) < 2:
        return lines
    
    merged = []
    current_line = lines[0]
    
    for next_line in lines[1:]:
        # Check if lines should be merged
        should_merge = False
        
        # Case 1: Current line ends without sentence-ending punctuation
        # and next line starts with lowercase
        if (current_line and not current_line.rstrip()[-1:] in '.!?:' 
            and next_line and next_line[0].islower()):
            should_merge = True
        
        # Case 2: Current line is very short (likely partial)
        if len(current_line.strip()) < 10 and not current_line.rstrip()[-1:] in '.!?:':
            should_merge = True
        
        if should_merge:
            current_line = current_line.rstrip() + ' ' + next_line.lstrip()
        else:
            merged.append(current_line)
            current_line = next_line
    
    merged.append(current_line)
    return merged


def calculate_text_confidence(text: str, raw_confidence: float = 1.0) -> float:
    """
    Calculate adjusted confidence score for extracted text.
    
    Considers factors like:
    - Raw OCR confidence
    - Text coherence (word patterns)
    - Character validity
    
    Args:
        text: Extracted text
        raw_confidence: Raw confidence from OCR engine
        
    Returns:
        Adjusted confidence score (0.0 to 1.0)
    """
    if not text:
        return 0.0
    
    confidence = raw_confidence
    
    # Penalize for excessive special characters
    special_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / max(len(text), 1)
    if special_ratio > 0.3:
        confidence *= 0.7
    
    # Penalize for very short text
    if len(text) < 3:
        confidence *= 0.5
    
    # Boost for recognizable word patterns
    word_count = len(text.split())
    if word_count >= 2:
        confidence *= 1.1
    
    # Cap at 1.0
    return min(confidence, 1.0)


def extract_email(lines: list) -> Optional[str]:
    """
    Extract email address from a list of text lines.
    
    Args:
        lines: List of text lines
        
    Returns:
        Email address or None
    """
    email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    for line in lines:
        match = email_pattern.search(line)
        if match:
            return match.group(0)
    return None


def extract_url(lines: list) -> Optional[str]:
    """
    Extract URL from a list of text lines.
    
    Args:
        lines: List of text lines
        
    Returns:
        URL or None
    """
    url_pattern = re.compile(r'https?://[^\s]+|www\.[^\s]+')
    for line in lines:
        match = url_pattern.search(line)
        if match:
            return match.group(0)
    return None


def detect_language_hint(text: str) -> str:
    """
    Detect language hint from text content.
    
    Simple heuristic-based detection for common languages.
    
    Args:
        text: Text to analyze
        
    Returns:
        Language code hint (e.g., 'en', 'es', 'fr')
    """
    text_lower = text.lower()
    
    # Spanish indicators
    spanish_words = {'el', 'la', 'de', 'que', 'en', 'un', 'es', 'por', 'con', 'para'}
    # French indicators
    french_words = {'le', 'la', 'de', 'et', 'en', 'un', 'est', 'que', 'pour', 'dans'}
    # German indicators
    german_words = {'der', 'die', 'und', 'ist', 'von', 'ein', 'mit', 'auf', 'für'}
    
    words = set(text_lower.split())
    
    spanish_count = len(words & spanish_words)
    french_count = len(words & french_words)
    german_count = len(words & german_words)
    
    if spanish_count > french_count and spanish_count > german_count and spanish_count >= 2:
        return 'es'
    if french_count > spanish_count and french_count > german_count and french_count >= 2:
        return 'fr'
    if german_count > spanish_count and german_count > french_count and german_count >= 2:
        return 'de'
    
    return 'en'  # Default to English


def extract_sku(line: str) -> Optional[str]:
    """
    Extract SKU (12-14 digit code) from a line.
    
    Args:
        line: Text line to search
        
    Returns:
        SKU string or None
    """
    match = SKU_PATTERN.search(line)
    return match.group(0) if match else None


def extract_subtotal(lines: list) -> Optional[Decimal]:
    """
    Extract subtotal amount from a list of text lines.
    
    Args:
        lines: List of text lines
        
    Returns:
        Decimal subtotal or None
    """
    subtotal_patterns = [
        re.compile(r'sub\s*total[:\s]*\$?\s*(\d+[.,]?\d{0,2})', re.IGNORECASE),
        re.compile(r'subtotal[:\s]*\$?\s*(\d+[.,]?\d{0,2})', re.IGNORECASE),
    ]
    
    for pattern in subtotal_patterns:
        for line in lines:
            match = pattern.search(line)
            if match:
                subtotal_str = match.group(1).replace(',', '.')
                subtotal_val = normalize_price(subtotal_str)
                if subtotal_val:
                    return subtotal_val
    return None


def extract_tax(lines: list) -> Optional[Decimal]:
    """
    Extract tax amount from a list of text lines.
    
    Args:
        lines: List of text lines
        
    Returns:
        Decimal tax or None
    """
    tax_patterns = [
        re.compile(r'\btax[:\s]*\$?\s*(\d+[.,]?\d{0,2})', re.IGNORECASE),
        re.compile(r'sales\s*tax[:\s]*\$?\s*(\d+[.,]?\d{0,2})', re.IGNORECASE),
    ]
    
    for pattern in tax_patterns:
        for line in lines:
            match = pattern.search(line)
            if match:
                tax_str = match.group(1).replace(',', '.')
                tax_val = normalize_price(tax_str)
                if tax_val:
                    return tax_val
    return None


def validate_receipt_totals(subtotal: Optional[Decimal], tax: Optional[Decimal], 
                            total: Optional[Decimal], tolerance: Decimal = Decimal('0.05')) -> dict:
    """
    Validate that receipt totals are mathematically consistent.
    
    Checks: subtotal + tax = total (within tolerance)
    
    Args:
        subtotal: Extracted subtotal
        tax: Extracted tax
        total: Extracted total
        tolerance: Maximum acceptable difference
        
    Returns:
        Validation result dict with 'valid', 'confidence_adjustment', 'notes'
    """
    result = {
        'valid': True,
        'confidence_adjustment': 1.0,
        'notes': []
    }
    
    # Check if we have all required values
    if subtotal is None:
        result['notes'].append("Subtotal not found")
        result['confidence_adjustment'] *= 0.9
    
    if tax is None:
        result['notes'].append("Tax not found")
        result['confidence_adjustment'] *= 0.95
    
    if total is None:
        result['valid'] = False
        result['notes'].append("Total not found - CRITICAL")
        result['confidence_adjustment'] *= 0.3
        return result
    
    # Validate math: subtotal + tax = total
    if subtotal is not None and tax is not None and total is not None:
        expected_total = subtotal + tax
        difference = abs(expected_total - total)
        
        if difference <= tolerance:
            result['notes'].append("Math validation passed")
            result['confidence_adjustment'] *= 1.1  # Boost confidence
        else:
            result['valid'] = False
            result['notes'].append(f"Math validation failed: {subtotal} + {tax} = {expected_total}, expected {total}")
            result['confidence_adjustment'] *= 0.7
    
    return result


def validate_item_count(items: list, expected_count: Optional[int] = None) -> dict:
    """
    Validate extracted items for quality and consistency.
    
    Args:
        items: List of extracted items
        expected_count: Expected number of items (if known)
        
    Returns:
        Validation result dict with 'valid', 'confidence_adjustment', 'notes'
    """
    result = {
        'valid': True,
        'confidence_adjustment': 1.0,
        'notes': []
    }
    
    if not items:
        result['notes'].append("No items extracted")
        result['confidence_adjustment'] *= 0.5
    else:
        result['notes'].append(f"Extracted {len(items)} items")
        
        # Boost confidence for reasonable item counts
        if 1 <= len(items) <= 50:
            result['confidence_adjustment'] *= 1.05
        elif len(items) > 50:
            result['notes'].append("Unusually high item count - verify")
            result['confidence_adjustment'] *= 0.9
    
    # Validate against expected count if provided
    if expected_count is not None and items:
        if len(items) == expected_count:
            result['notes'].append("Item count matches expected")
            result['confidence_adjustment'] *= 1.1
        else:
            result['notes'].append(f"Item count mismatch: got {len(items)}, expected {expected_count}")
            result['confidence_adjustment'] *= 0.85
    
    return result


def calculate_overall_confidence(base_confidence: float, 
                                  receipt_data: dict,
                                  raw_text: str = "") -> float:
    """
    Calculate overall confidence score based on extraction quality.
    
    Considers:
    - Presence of required fields (store, total, items)
    - Math validation
    - Text quality indicators
    
    Args:
        base_confidence: Initial confidence from OCR engine
        receipt_data: Extracted receipt data dict
        raw_text: Raw OCR text for quality assessment
        
    Returns:
        Adjusted confidence score (0.0 to 1.0)
    """
    confidence = base_confidence
    
    # Check required fields
    store = receipt_data.get('store', {})
    if store.get('name'):
        confidence *= 1.1
    else:
        confidence *= 0.7
    
    totals = receipt_data.get('totals', {})
    if totals.get('total'):
        confidence *= 1.2
    else:
        confidence *= 0.4  # Critical field
    
    items = receipt_data.get('items', [])
    if items:
        confidence *= min(1.2, 1.0 + len(items) * 0.02)
    
    # Penalize for excessive special characters in raw text (OCR artifacts)
    if raw_text:
        special_ratio = sum(1 for c in raw_text if not c.isalnum() and not c.isspace()) / max(len(raw_text), 1)
        if special_ratio > 0.3:
            confidence *= 0.7
    
    # Cap at 1.0
    return min(1.0, max(0.0, confidence))
