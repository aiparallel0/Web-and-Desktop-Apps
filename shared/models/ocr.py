"""
Common OCR processing utilities shared across all OCR processors.

This module provides:
- Pre-compiled regex patterns for efficient matching
- Shared constants like SKIP_KEYWORDS
- Reusable text extraction utilities
- Text post-processing and cleaning utilities
- Integration with circular exchange framework via OCRConfig

Note: Price normalization (normalize_price) now imported from shared.utils.pricing
"""
import re
import logging
from decimal import Decimal
from typing import Optional, List, Tuple

# Import centralized pricing utilities
from shared.utils.pricing import normalize_price, PRICE_MIN, PRICE_MAX

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
            module_id="shared.models.ocr_common",
            file_path=__file__,
            description="Common OCR processing utilities with regex patterns and text extraction",
            dependencies=["shared.circular_exchange", "shared.utils.pricing"],
            exports=["normalize_price", "extract_date", "extract_total", "extract_phone",
                    "extract_line_items", "extract_line_items_with_codes", "merge_multiline_items",
                    "parse_receipt_text", "get_detection_config",
                    "record_detection_result", "fix_concatenated_text", "clean_item_name",
                    "is_garbage_text", "MAX_REALISTIC_ITEM_PRICE", "PRICE_MIN", "PRICE_MAX"]
        ))
    except Exception:
        pass  # Ignore registration errors during import

# Lazy import of OCRConfig to avoid circular imports
_ocr_config = None

def get_config():
    """Get the global OCR configuration (lazy loading)."""
    global _ocr_config
    if _ocr_config is None:
        try:
            from .ocr_config import get_ocr_config
            _ocr_config = get_ocr_config()
        except ImportError:
            logger.warning("OCRConfig not available, using defaults")
            _ocr_config = None
    return _ocr_config


def get_detection_config():
    """
    Get detection configuration from circular exchange framework.
    
    Returns a dictionary with all detection parameters that can be used
    by OCR processors for text detection. Parameters are dynamically
    managed via the circular exchange framework with auto-tuning support.
    
    Returns:
        Dictionary containing detection parameters or defaults if unavailable
    """
    config = get_config()
    if config:
        return config.get_detection_config()
    
    # Return defaults if config not available - lowered min_confidence for better detection
    return {
        'min_confidence': 0.20,
        'box_threshold': 0.25,
        'min_text_height': 6,
        'use_angle_cls': True,
        'multi_scale': True,
        'auto_retry': True,
        'enhance_contrast': True,
        'denoise_strength': 10
    }


def record_detection_result(text_regions_count: int, avg_confidence: float, 
                            success: bool, processing_time: float = 0.0) -> None:
    """
    Record a detection result for auto-tuning via circular exchange.
    
    This function should be called by OCR processors after text detection
    to enable automatic parameter adjustment based on detection success rates.
    
    Args:
        text_regions_count: Number of text regions detected
        avg_confidence: Average confidence of detected regions
        success: Whether detection was successful
        processing_time: Time taken for detection in seconds
    """
    config = get_config()
    if config:
        config.record_detection_result(
            text_regions_count=text_regions_count,
            avg_confidence=avg_confidence,
            success=success,
            processing_time=processing_time
        )

# Note: PRICE_MIN, PRICE_MAX now imported from shared.utils.pricing
# Maximum realistic price for a single grocery/retail item
# Items priced above this threshold are likely OCR errors
MAX_REALISTIC_ITEM_PRICE = Decimal('99.99')

# Garbage text detection thresholds
MIN_UNIQUE_CHAR_RATIO = 0.5  # Minimum ratio of unique chars to detect repeated char noise
MAX_SPECIAL_CHAR_RATIO = 0.2  # Maximum ratio of special chars in valid text
MIN_ALPHA_RATIO = 0.5  # Minimum ratio of alpha chars in non-space text
MIN_ALPHAS_FOR_CASE_CHECK = 6  # Minimum alpha count before checking case transitions
MAX_CASE_TRANSITIONS = 3  # Maximum case transitions before flagging as garbage
MIN_TEXT_LENGTH_FOR_SPECIAL_CHECK = 5  # Minimum text length before special char ratio check

# Keywords to skip when extracting line items
SKIP_KEYWORDS = frozenset({
    'subtotal', 'total', 'cash', 'change', 'tax', 'payment', 'balance',
    'thank', 'visit', 'welcome', 'receipt', 'cashier', 'card', 'debit',
    'credit', 'approved', 'transaction', 'visa', 'mastercard', 'amex'
})

# Additional keywords to skip in item names (store info, hours, etc.)
# Short patterns (2 chars) need word boundary matching to avoid false positives
ITEM_SKIP_PATTERNS = frozenset({
    'store', 'thank', 'visit', 'phone', 'fax', 'email', 
    'open', 'hours', 'daily'
})

# Time patterns that need word boundary matching (to avoid matching 'creamy', 'spam', etc.)
ITEM_SKIP_TIME_PATTERNS = [
    re.compile(r'\b\d{1,2}:\d{2}\s*(?:am|pm)\b', re.IGNORECASE),  # 9:00 AM, 12:30PM
    re.compile(r'\b(?:am|pm)\s+to\s+\d{1,2}(?::\d{2})?\b', re.IGNORECASE),  # AM TO 9:00, PM TO 5
]

# Pre-compiled regex patterns for performance
# Order matters - more specific patterns first
DATE_PATTERNS = [
    re.compile(r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})'),  # ISO format: 2024-01-15
    re.compile(r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})'),  # US format with 4-digit year: 12/25/2024
    re.compile(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2})'),  # US format with 2-digit year: 12/25/24
    re.compile(r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4})\b', re.IGNORECASE),  # Month format: Jan 15, 2024
]

TOTAL_PATTERNS = [
    # Handle reverse format where amount comes before TOTAL: "7.43 TOTAL PURCHASE"
    # This should be checked first as it's more reliable when present
    re.compile(r'\$?\s*(\d+)\s*[.,]\s*(\d{2})\s+total\s*(?:purchase|due|puri)?', re.IGNORECASE),
    # Standard format: "TOTAL 38.68" - requires decimal point or comma
    re.compile(r'(?<![a-z])total[:\s]*\$?\s*(\d+)\s*[.,]\s*(\d{2})\b', re.IGNORECASE),
    re.compile(r'amount[:\s]*\$?\s*(\d+)\s*[.,]?\s*(\d{2})\b', re.IGNORECASE),
    re.compile(r'balance[:\s]*\$?\s*(\d+)\s*[.,]?\s*(\d{2})\b', re.IGNORECASE),
    re.compile(r'grand\s*total[:\s]*\$?\s*(\d+)\s*[.,]?\s*(\d{2})\b', re.IGNORECASE),
]

PHONE_PATTERNS = [
    re.compile(r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'),
    re.compile(r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})'),
]

LINE_ITEM_PATTERNS = [
    # Walmart format: ITEM NAME SKU [F] PRICE TAX_CODE (most specific first)
    # Example: "SC_BCN CHDDR 007874202906 F 6.98 0"
    re.compile(r'^(.+?)\s+\d{10,14}\s*[FfTt]?\s*(\d+)\s*[.,]\s*(\d{2})\s*[FTNXOD0]$', re.IGNORECASE),
    # Walmart format without trailing tax code: ITEM NAME SKU PRICE
    re.compile(r'^(.+?)\s+\d{10,14}\s*[FfTt]?\s*(\d+)\s*[.,]\s*(\d{2})\s*$'),
    # Walmart format with semicolon: ITEM NAME SKU; PRICE T (handles OCR artifacts)
    # Example: "SW HRO FGHTR 06305094073; 6.94 T"
    re.compile(r'^(.+?)\s+\d{10,14}[;,]?\s*(\d+)\s*[.,]\s*(\d{2})\s*[FTNXOD0]?$', re.IGNORECASE),
    # Format with em-dash or dash separator: ITEM NAME — XX.XX or ITEM T — XX.XX
    re.compile(r'^(.+?)\s+[—–-]\s*(\d+)\s*[.,]\s*(\d{2})$'),
    # Format with tax code at end: ITEM NAME  XX.XX F/T/N/X/O/0
    re.compile(r'^(.+?)\s+(\d+)\s*[.,]\s*(\d{2})\s*[FTNXOD0]$', re.IGNORECASE),
    # Trader Joe's format: ITEM NAME XX.XX or ITEM NAME X.XX (simple)
    re.compile(r'^([A-Z][A-Z0-9\s/_-]{2,}?)\s+(\d+)\s*[.,]\s*(\d{2})$'),
    # Standard formats: ITEM NAME   $XX.XX or ITEM NAME XX.XX
    re.compile(r'^(.+?)\s+\$?\s*(\d+)\s*[.,]\s*(\d{2})$'),
    re.compile(r'^(.+?)\s+(\d+)\s*[.,]\s*(\d{2})\s*$'),
    re.compile(r'^(.+?)\s+\$\s*(\d+)\s*[.,]\s*(\d{2})$'),
    # Format with SKU at start: SKU  ITEM NAME  XX.XX (12-14 digit SKU)
    re.compile(r'^\d{12,14}\s+(.+?)\s+\$?\s*(\d+)\s*[.,]\s*(\d{2})$'),
    # Format with quantity: QTY x ITEM NAME  XX.XX
    re.compile(r'^(?:\d+\s*[xX*]\s*)?(.+?)\s+\$?\s*(\d+)\s*[.,]\s*(\d{2})$'),
    # Format with leading quote/garbage: "ITEM NAME SKU PRICE
    re.compile(r'^[\'"][^\'"]*(.{3,}?)\s+\d{10,14}\s+(\d+)\s*[.,]\s*(\d{2})'),
    # NEW: Simple item-price format with any whitespace
    re.compile(r'^([A-Za-z][A-Za-z0-9\s]{1,}?)\s{2,}(\d+)\s*[.,]\s*(\d{2})$'),
    # NEW: Item with price in parentheses or after colon
    re.compile(r'^(.+?)[:]\s*\$?\s*(\d+)\s*[.,]\s*(\d{2})$'),
    # NEW: Multi-word item names with price
    re.compile(r'^([A-Z][A-Za-z]+(?:\s+[A-Za-z]+)+)\s+(\d+)\s*[.,]\s*(\d{2})$'),
    # NEW: Lowercase item names (some receipts)
    re.compile(r'^([a-z][a-z0-9\s]{2,}?)\s+\$?\s*(\d+)\s*[.,]\s*(\d{2})$', re.IGNORECASE),
    # NEW: Item with unit price format (e.g., "MILK  2.99 EA")
    re.compile(r'^(.+?)\s+(\d+)\s*[.,]\s*(\d{2})\s*(?:EA|LB|OZ|CT|PK)?$', re.IGNORECASE),
]

# SKU pattern for receipt items (12-14 digits)
SKU_PATTERN = re.compile(r'\b\d{12,14}\b')

# Multi-line item pattern: SKU-only line with price
# Matches: "020108870398 F 3.98 0" or "053099656595 4.88 0"
# Uses 12-14 digits to be consistent with SKU_PATTERN
MULTILINE_SKU_PRICE_PATTERN = re.compile(
    r'^(\d{12,14})\s*[FfTt]?\s*(\d+)\s*[.,]\s*(\d{2})\s*[FTNXOD0]?$',
    re.IGNORECASE
)

# Pattern for potential item name lines (used in multi-line detection)
# These are lines that could be item names on their own
# Requires at least 3 characters (1 initial + 2 from range) to be consistent with merge validation
POTENTIAL_ITEM_NAME_PATTERN = re.compile(
    r'^[A-Z0-9][A-Z0-9\s\-_/\']{2,40}$',
    re.IGNORECASE
)

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
    'fotal': 'total',  # F misread as T
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
    'a =o': "TRADER JOE'S",
    'trader joes': "TRADER JOE'S",
    'trader joe': "TRADER JOE'S",
    'wa1mart': 'WALMART',
    'wa1-mart': 'WALMART',
    'wal-mart': 'WALMART',
    'wal*mart': 'WALMART',
    'walmart s': 'WALMART',
    'walmart': 'WALMART',
    'costc0': 'COSTCO',
    'target': 'TARGET',
    'who1e foods': 'WHOLE FOODS',
    'wholefoods': 'WHOLE FOODS',
    'kroger': 'KROGER',
    'safeway': 'SAFEWAY',
    'pub1ix': 'PUBLIX',
    'publix': 'PUBLIX',
}
# Note: normalize_price() function removed - now imported from shared.utils.pricing at top of file


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
    
    Handles OCR errors like "$38 .68" or "$38 68" (space instead of decimal).
    
    Args:
        lines: List of text lines
        
    Returns:
        Decimal total or None
    """
    for pattern in TOTAL_PATTERNS:
        for line in lines:
            match = pattern.search(line)
            if match:
                # Combine the two groups (dollars and cents)
                dollars = match.group(1)
                cents = match.group(2) if len(match.groups()) > 1 else '00'
                total_str = f"{dollars}.{cents}"
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
        # Check for address keywords and digits
        if any(kw in line_lower for kw in ADDRESS_KEYWORDS) and any(c.isdigit() for c in line):
            # Skip lines that look like product items (contain price patterns like X.XX)
            # An address might have numbers but shouldn't have price-like decimals
            if re.search(r'\d+[.,]\d{2}\s*$', line):
                continue
            # Skip lines that contain product-like words
            product_words = ['strawberr', 'apple', 'banana', 'milk', 'bread', 'cheese', 
                           'chicken', 'beef', 'fish', 'mahi', 'plum', 'egg', 'cottage']
            if any(pw in line_lower for pw in product_words):
                continue
            return line
    return None


def should_skip_line(line: str) -> bool:
    """
    Check if a line should be skipped when extracting items.
    
    Applies OCR corrections before checking for skip keywords.
    
    Args:
        line: Text line to check
        
    Returns:
        True if line should be skipped
    """
    line_lower = line.lower()
    
    # Apply word corrections to catch OCR-misread keywords like FOTAL -> TOTAL
    corrected_line = line_lower
    for wrong, correct in WORD_CORRECTIONS.items():
        if wrong in corrected_line:
            corrected_line = corrected_line.replace(wrong, correct)
    
    # Skip lines with common keywords (using corrected line)
    if any(kw in corrected_line for kw in SKIP_KEYWORDS):
        return True
    # Skip quantity lines like "2 @ 0.49" or "3FA @.0.29/EA"
    if re.match(r'^\d+\s*@', line) or re.match(r'^\d+[A-Z]*\s*[@—-]', line):
        return True
    return False


def should_skip_item_name(name: str) -> bool:
    """
    Check if an item name contains patterns that indicate it's not a product.
    
    Uses both substring matching for longer keywords and regex patterns
    for short words like 'am'/'pm' to avoid false positives (e.g., 'creamy').
    
    Args:
        name: Item name to check
        
    Returns:
        True if name should be skipped
    """
    name_lower = name.lower()
    
    # Check long patterns with simple substring match
    if any(pattern in name_lower for pattern in ITEM_SKIP_PATTERNS):
        return True
    
    # Check time patterns with word boundary matching
    for pattern in ITEM_SKIP_TIME_PATTERNS:
        if pattern.search(name_lower):
            return True
    
    return False


def fix_concatenated_text(text: str) -> str:
    """
    Fix text where OCR has concatenated words without spaces.
    
    This handles common OCR errors where adjacent text regions are merged:
    - "SHREDDED10" -> "SHREDDED 10" (number stuck to word)
    - "10OZ" -> "10 OZ" (unit stuck to number)
    - "TOMATOESWHOLE" patterns are harder - we try to split at case transitions
    
    Args:
        text: Raw OCR text with potential concatenation issues
        
    Returns:
        Text with spaces inserted at likely word boundaries
    """
    if not text:
        return text
    
    result = text
    
    # Insert space between letters and numbers: "SHREDDED10" -> "SHREDDED 10"
    # But avoid breaking things like "2%" or "A1" at the start
    result = re.sub(r'([A-Za-z]{2,})(\d)', r'\1 \2', result)
    
    # Insert space between numbers and letters: "10OZ" -> "10 OZ"
    # Common for units like OZ, LB, CT, EA
    result = re.sub(r'(\d)(OZ|LB|CT|EA|PK|BAG|DOZ)\b', r'\1 \2', result, flags=re.IGNORECASE)
    
    # Handle common OCR artifacts at word boundaries
    # Pattern: lowercase followed immediately by uppercase (likely word boundary)
    # "aTOMATOES" pattern - OCR picking up first letter incorrectly
    result = re.sub(r'^([a-z]{1,2})([A-Z]{2,})', r'\2', result)  # Strip leading lowercase noise
    
    # Insert spaces at case transitions that look like word boundaries
    # "TOMATOESWHOLE" - this is hard without a dictionary
    # We'll be conservative and only handle specific known patterns
    
    return result


def is_garbage_text(text: str) -> bool:
    """
    Detect if OCR text appears to be garbage/unreadable.
    
    This helps filter out low-quality OCR output that would result
    in meaningless item names like "oo )sprauteDCaSTYLE" or "eee -".
    
    Detection patterns:
    - Very short text (single characters that aren't valid items)
    - Excessive punctuation/special characters
    - No recognizable word patterns (random character sequences)
    - Mixed case chaos (not following normal word patterns)
    - Repeated characters suggesting OCR noise
    
    Args:
        text: Cleaned text to analyze
        
    Returns:
        True if text appears to be garbage, False if it seems valid
    """
    if not text:
        return True
    
    # Strip and normalize
    clean = text.strip()
    
    # Very short text (2 chars) is likely garbage - valid items are 3+ chars
    if len(clean) <= 2:
        return True
    
    # Calculate character type ratios
    total_chars = len(clean)
    alphas = sum(1 for c in clean if c.isalpha())
    specials = sum(1 for c in clean if not c.isalnum() and not c.isspace())
    spaces = sum(1 for c in clean if c.isspace())
    
    # Very short text with punctuation is likely garbage (e.g., ".- %", "eee -")
    if len(clean) <= MIN_TEXT_LENGTH_FOR_SPECIAL_CHECK:
        # Allow short valid items like "TEA", "GUM", "EGG" (3+ letters, all alpha)
        if clean.isalpha() and len(clean) >= 3:
            # Check for repeated characters (like "eee")
            if len(set(clean.lower())) < len(clean) * MIN_UNIQUE_CHAR_RATIO:
                return True  # Too many repeated chars
            return False
        # Otherwise too short with mixed chars is garbage
        if alphas < 3 or specials > 0:
            return True
    
    # Garbage detection: excessive special characters
    if total_chars > MIN_TEXT_LENGTH_FOR_SPECIAL_CHECK and specials > total_chars * MAX_SPECIAL_CHAR_RATIO:
        return True
    
    # Garbage detection: no letters at all (except for numbers with units)
    if alphas == 0:
        return True
    
    # Garbage detection: too few letters compared to total
    non_space_chars = total_chars - spaces
    if non_space_chars > 0 and alphas < non_space_chars * MIN_ALPHA_RATIO:
        return True
    
    # Garbage detection: isolated single letters like "LY" or "eet"
    # that aren't valid abbreviations
    words = clean.split()
    if words:
        short_words = [w for w in words if len(w) <= 2 and w.isalpha()]
        # If all words are very short alphabetic, likely garbage
        if len(words) <= 2 and len(short_words) == len(words):
            return True
    
    # Garbage detection: random mixed case without word structure
    # E.g., "oo )sprauteDCaSTYLE" - lowercase-uppercase transitions that don't make sense
    # Normal text has case transitions at word boundaries, not mid-word
    case_transitions = 0
    prev_upper = None
    for c in clean:
        if c.isalpha():
            is_upper = c.isupper()
            if prev_upper is not None and prev_upper != is_upper:
                case_transitions += 1
            prev_upper = is_upper
    
    # Too many case transitions for the length suggests OCR noise
    # Normal text: "TOMATOES WHOLE" has 0 mid-word transitions
    # Garbage: "oo )sprauteDCaSTYLE" has many mid-word transitions
    if alphas >= MIN_ALPHAS_FOR_CASE_CHECK and case_transitions >= MAX_CASE_TRANSITIONS:
        # More than threshold case transitions in text with sufficient letters is suspicious
        # Additionally check for words starting with lowercase followed by uppercase
        for word in words:
            if len(word) >= 4:
                letters_only = ''.join(c for c in word if c.isalpha())
                if letters_only and letters_only[0].islower():
                    # Word starts lowercase - check for uppercase later
                    has_upper = any(c.isupper() for c in letters_only[1:])
                    if has_upper:
                        return True
        return True
    
    return False


def clean_item_name(name: str) -> str:
    """
    Clean and correct common OCR errors in item names.
    
    Applies:
    - Removes leading apostrophes/quotes (common OCR artifact)
    - Fix concatenated text (OCR joining words without spaces)
    - Word-level corrections (e.g., FASHIUNED -> FASHIONED)
    - Unit abbreviation fixes (e.g., "10 02" -> "10 OZ")
    - Removes trailing periods and extra punctuation
    - Removes OCR noise and SKU-like patterns
    - Normalizes whitespace
    
    Args:
        name: Raw item name from OCR
        
    Returns:
        Cleaned item name
    """
    if not name:
        return name
    
    cleaned = name.strip()
    
    # Remove leading apostrophes/quotes (common OCR artifact)
    # E.g., "'BLACK. BEANS" -> "BLACK. BEANS", "CAGE 'FREE" -> "CAGE FREE"
    cleaned = re.sub(r"^['\"`]+\s*", '', cleaned)  # Leading quotes at start
    cleaned = re.sub(r"\s*['\"`]+\s+", ' ', cleaned)  # Quotes before words (with space after)
    cleaned = re.sub(r"(?<=\s)['\"`]+(?=[A-Z])", '', cleaned)  # Quote before uppercase letter
    
    # First, fix concatenated text issues from OCR
    cleaned = fix_concatenated_text(cleaned)
    
    # Apply unit corrections FIRST (before removing trailing letters)
    for wrong, correct in UNIT_CORRECTIONS.items():
        cleaned = cleaned.replace(wrong, correct)
    
    # Remove OCR noise patterns (random lowercase mixed with uppercase letters)
    # Pattern like "oo2igogqggi6" - mostly lowercase with occasional digits
    cleaned = re.sub(r'\s+[a-z0-9]{8,}\s*$', '', cleaned)  # Trailing noise
    cleaned = re.sub(r'\s+[oO0]+[a-z0-9]{6,}\s*$', '', cleaned)  # OCR O/0 confusion noise (min 6 chars)
    
    # Remove leading OCR noise (lowercase letters before uppercase words)
    # E.g., "f-Reasals" where "f-" is noise before "CARROTS"
    cleaned = re.sub(r'^[a-z][^A-Za-z]*(?=[A-Z])', '', cleaned)
    
    # Remove trailing single tax code letters (but not OZ, LB, CT etc.)
    cleaned = re.sub(r'\s+[FTNXD0]\s*$', '', cleaned, flags=re.IGNORECASE)
    
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


def extract_store_name(lines: list, max_lines: int = 10) -> Optional[str]:
    """
    Extract store name from text lines.
    
    Searches for known store patterns first, then falls back to 
    first valid line. Applies store name corrections for common OCR errors.
    
    Args:
        lines: List of text lines
        max_lines: Maximum lines to search
        
    Returns:
        Store name or None
    """
    # First, check for known store patterns in all lines
    known_stores = {
        'walmart': 'WALMART',
        'wal-mart': 'WALMART',
        'wal*mart': 'WALMART',
        'trader joe': "TRADER JOE'S",
        'costco': 'COSTCO',
        'target': 'TARGET',
        'whole foods': 'WHOLE FOODS',
        'kroger': 'KROGER',
        'safeway': 'SAFEWAY',
        'publix': 'PUBLIX',
        'cvs': 'CVS',
        'walgreens': 'WALGREENS',
        'home depot': 'HOME DEPOT',
        'lowes': "LOWE'S",
    }
    
    for line in lines[:max_lines]:
        line_lower = line.lower().strip()
        for pattern, store_name in known_stores.items():
            if pattern in line_lower:
                return store_name
    
    # Fallback to first valid line with correction
    for line in lines[:max_lines]:
        line = line.strip()
        if len(line) >= 2 and not line.isdigit():
            # Skip lines that look like addresses (end with RD., ST., AVE., etc.)
            line_lower = line.lower().rstrip('.')
            line_words = line_lower.split()
            if line_words:
                last_word = line_words[-1].rstrip('.,')
                if last_word in ADDRESS_KEYWORDS:
                    continue
            # Skip lines that contain price patterns (likely line items)
            if re.search(r'\d+[.,]\d{2}', line):
                continue
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
        re.compile(r'sub\s*total[:\s]*\$?\s*(\d+(?:[.,]\d{2})?)', re.IGNORECASE),
        re.compile(r'subtotal[:\s]*\$?\s*(\d+(?:[.,]\d{2})?)', re.IGNORECASE),
    ]
    
    for pattern in subtotal_patterns:
        for line in lines:
            match = pattern.search(line)
            if match:
                subtotal_val = normalize_price(match.group(1))
                if subtotal_val:
                    return subtotal_val
    return None


def extract_tax(lines: list) -> Optional[Decimal]:
    """
    Extract tax amount from a list of text lines.
    
    Handles various tax formats including:
    - "TAX 4.58" - Simple tax amount
    - "TAX1 4.58" or "TAX 1 4.58" - Tax with category code (common on Walmart receipts)
    - "SALES TAX 4.58" - Sales tax label
    
    For lines with tax category codes (e.g., TAX 1, TAX 2), the function
    extracts the last valid price on the line as the tax amount.
    
    Args:
        lines: List of text lines
        
    Returns:
        Decimal tax or None
    """
    # Pattern to match tax lines - captures the entire line for further processing
    # Match "TAX" optionally followed by digits (TAX1, TAX2) then word boundary
    # Using (?:\d+)? to match zero or more digits, then \b for word boundary
    # This avoids matching "taxation" or "taxable"
    tax_line_patterns = [
        re.compile(r'\btax(?:\d+)?\b', re.IGNORECASE),
        re.compile(r'sales\s*tax', re.IGNORECASE),
    ]
    
    # Pattern to find price values - handles both XX.XX and whole numbers
    # Matches prices with 1-2 decimal places or whole numbers followed by non-digit
    price_pattern = re.compile(r'\$?\s*(\d+(?:[.,]\d{1,2})?)\b')
    
    for line in lines:
        # Check if this is a tax line
        is_tax_line = any(pattern.search(line) for pattern in tax_line_patterns)
        if not is_tax_line:
            continue
        
        # Find all prices on the line
        prices = price_pattern.findall(line)
        if prices:
            # Use the last price on the line (handles "TAX 1 4.58" format)
            # The last price is typically the actual tax amount
            last_price = prices[-1]
            tax_val = normalize_price(last_price)
            if tax_val and tax_val > Decimal('0'):
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


def merge_multiline_items(lines: List[str]) -> List[str]:
    """
    Merge multi-line item entries common in Walmart and similar receipts.
    
    Some receipts split items across multiple lines:
    - Line 1: Item name (e.g., "6 WING PLATE")
    - Line 2: SKU + price (e.g., "020108870398 F 3.98 0")
    
    This function detects and merges such patterns into single lines
    that can be processed by standard item extraction patterns.
    
    Args:
        lines: List of OCR text lines
        
    Returns:
        List of lines with multi-line items merged
    """
    if not lines or len(lines) < 2:
        return lines
    
    merged = []
    i = 0
    
    while i < len(lines):
        current_line = lines[i].strip()
        
        # Skip empty lines
        if not current_line:
            merged.append(current_line)
            i += 1
            continue
        
        # Check if current line could be an item name (no price, no SKU, not a total line)
        is_potential_name = (
            POTENTIAL_ITEM_NAME_PATTERN.match(current_line) and
            not SKU_PATTERN.search(current_line) and
            not re.search(r'\d+[.,]\d{2}\s*$', current_line) and  # No price at end
            not should_skip_line(current_line) and
            len(current_line) >= 3
        )
        
        # If this looks like an item name and we have a next line
        if is_potential_name and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            
            # Check if next line matches the SKU+price pattern
            sku_price_match = MULTILINE_SKU_PRICE_PATTERN.match(next_line)
            if sku_price_match:
                # Merge the two lines
                sku = sku_price_match.group(1)
                dollars = sku_price_match.group(2)
                cents = sku_price_match.group(3)
                merged_line = f"{current_line} {sku} {dollars}.{cents}"
                merged.append(merged_line)
                i += 2  # Skip both lines
                continue
        
        # Default: add line as-is
        merged.append(current_line)
        i += 1
    
    return merged


def extract_line_items_with_codes(lines: List[str], text_metadata: Optional[List[dict]] = None,
                                   min_confidence: float = None, relaxed_mode: bool = None
                                   ) -> List[Tuple[str, Optional[str], Decimal, int]]:
    """
    Extract line items with item codes/SKUs from text lines.
    
    Enhanced version of extract_line_items that also extracts item codes.
    This is useful for receipts that include SKU/barcode numbers.
    
    Args:
        lines: List of text lines from OCR
        text_metadata: Optional list of metadata dicts with 'confidence' keys
        min_confidence: Minimum confidence threshold
        relaxed_mode: If True, use less strict validation rules
        
    Returns:
        List of tuples (name, code, price, quantity) representing line items.
        code is None if no SKU was found.
    """
    # First, try to merge multi-line items
    merged_lines = merge_multiline_items(lines)
    
    # Get configuration from circular exchange if not provided
    config = get_config()
    if min_confidence is None:
        min_confidence = config.min_confidence if config else 0.3
    if relaxed_mode is None:
        relaxed_mode = config.relaxed_mode if config else False
    
    max_price = config.max_price if config else 1000.0
    realistic_max_price = min(max_price, float(MAX_REALISTIC_ITEM_PRICE))
    
    items = []
    seen = set()
    min_name_length = 1 if relaxed_mode else 2
    
    for i, line in enumerate(merged_lines):
        if should_skip_line(line):
            continue
        
        matched = False
        
        # Try standard patterns
        for pattern in LINE_ITEM_PATTERNS:
            m = pattern.search(line.strip())
            if m:
                name = m.group(1).strip()
                name = clean_item_name(name)
                
                # Handle 3-group patterns (name, dollars, cents)
                if len(m.groups()) >= 3:
                    price_str = f"{m.group(2)}.{m.group(3)}"
                else:
                    price_str = m.group(2)
                
                price_str = price_str.replace(',', '.')
                
                # Validate item name
                if len(name) < min_name_length or name in seen:
                    continue
                
                if name.replace(' ', '').isdigit():
                    continue
                
                alphas = sum(1 for c in name if c.isalpha())
                digits = sum(1 for c in name if c.isdigit())
                if alphas == 0 and digits > 0:
                    continue
                
                if is_garbage_text(name):
                    continue
                
                price = normalize_price(price_str)
                if not price or price <= 0 or price > Decimal(str(realistic_max_price)):
                    continue
                
                if should_skip_item_name(name):
                    continue
                
                # Extract SKU/code from the original line
                sku_match = SKU_PATTERN.search(line)
                code = sku_match.group(0) if sku_match else None
                
                items.append((name, code, price, 1))
                seen.add(name)
                matched = True
                break
        
        # Fallback pattern matching
        if not matched:
            fallback_patterns = [
                r'\$?\s*(\d+[.,]\d{2})(?!\d)',
                r'(\d+[.,]\d{2})\s*$',
                r'(\d{1,3}[.,]\d{2})\s*[A-Z]?$',
            ]
            
            for fallback_pattern in fallback_patterns:
                pm = re.search(fallback_pattern, line)
                if pm:
                    price_str = pm.group(1).replace(',', '.')
                    price = normalize_price(price_str)
                    
                    if price and price > 0 and price <= Decimal(str(realistic_max_price)):
                        name_part = line[:pm.start()].strip()
                        name_part = re.sub(r'^\d+\s*[xX*]\s*', '', name_part).strip()
                        name_part = re.sub(r'\s+\d{10,14}\s*$', '', name_part).strip()
                        name_part = clean_item_name(name_part)
                        
                        if is_garbage_text(name_part):
                            continue
                        
                        if len(name_part) >= min_name_length and name_part not in seen:
                            if not should_skip_line(name_part) and not should_skip_item_name(name_part):
                                sku_match = SKU_PATTERN.search(line)
                                code = sku_match.group(0) if sku_match else None
                                items.append((name_part, code, price, 1))
                                seen.add(name_part)
                                break
    
    return items


def extract_line_items(lines: List[str], text_metadata: Optional[List[dict]] = None, 
                       min_confidence: float = None, relaxed_mode: bool = None) -> List[Tuple[str, Decimal, int]]:
    """
    Extract line items from text lines - shared implementation for all OCR processors.
    
    This is the consolidated implementation used by OCRProcessor, EasyOCRProcessor,
    and PaddleProcessor to avoid code duplication.
    
    Integrates with OCRConfig from the circular exchange framework for dynamic
    parameter management and auto-tuning.
    
    Args:
        lines: List of text lines from OCR
        text_metadata: Optional list of metadata dicts with 'confidence' keys
                      (used by PaddleProcessor for confidence filtering)
        min_confidence: Minimum confidence threshold (uses OCRConfig if None)
        relaxed_mode: If True, use less strict validation rules (uses OCRConfig if None)
        
    Returns:
        List of tuples (name, price, quantity) representing line items.
        Caller should convert to LineItem objects.
    """
    # Get configuration from circular exchange if not provided
    config = get_config()
    if min_confidence is None:
        min_confidence = config.min_confidence if config else 0.3
    if relaxed_mode is None:
        relaxed_mode = config.relaxed_mode if config else False
    
    # Get additional parameters from config
    max_price = config.max_price if config else 1000.0
    max_digit_ratio = config.max_digit_ratio if config else 2.0
    
    # Use realistic item price limit to filter out OCR errors
    # Prices like 200.49 are unrealistic for individual grocery items
    realistic_max_price = min(max_price, float(MAX_REALISTIC_ITEM_PRICE))
    
    # First, try to merge multi-line items (common in Walmart receipts)
    merged_lines = merge_multiline_items(lines)
    
    items = []
    seen = set()
    
    # In relaxed mode, use lower thresholds
    min_name_length = 1 if relaxed_mode else 2
    
    for i, line in enumerate(merged_lines):
        if should_skip_line(line):
            continue
        
        matched = False
        
        # Try standard patterns
        for pattern in LINE_ITEM_PATTERNS:
            m = pattern.search(line.strip())
            if m:
                name = m.group(1).strip()
                # Apply item name cleaning for OCR corrections
                name = clean_item_name(name)
                
                # Handle 3-group patterns (name, dollars, cents)
                if len(m.groups()) >= 3:
                    price_str = f"{m.group(2)}.{m.group(3)}"
                else:
                    price_str = m.group(2)
                
                price_str = price_str.replace(',', '.')
                
                # Validate item name - relaxed validation for better detection
                if len(name) < min_name_length or name in seen:
                    continue
                
                # Check for purely digit names (likely SKUs or garbage)
                if name.replace(' ', '').isdigit():
                    continue
                
                # More lenient digit/alpha ratio check - use configurable threshold
                alphas = sum(1 for c in name if c.isalpha())
                digits = sum(1 for c in name if c.isdigit())
                # Only skip if more than 70% digits and no alpha at all wouldn't make sense
                if alphas == 0 and digits > 0:
                    continue
                if not relaxed_mode and digits > alphas * max_digit_ratio and len(name) >= 3:
                    continue
                
                # Relaxed short name check - allow short names if they're mostly letters
                if not relaxed_mode and len(name) < 5 and not name.replace(' ', '').isalpha():
                    # Allow if at least half are letters
                    if alphas < len(name.replace(' ', '')) / 2:
                        continue
                
                # Check for garbage OCR text (unreadable/random characters)
                if is_garbage_text(name):
                    continue
                
                # Check confidence if metadata provided - use configurable threshold
                if text_metadata and i < len(text_metadata):
                    conf = text_metadata[i].get('confidence')
                    if conf and conf < min_confidence:
                        continue
                
                price = normalize_price(price_str)
                # Use realistic item price limit to filter OCR errors
                if not price or price <= 0 or price > Decimal(str(realistic_max_price)):
                    continue
                
                if should_skip_item_name(name):
                    continue
                
                items.append((name, price, 1))
                seen.add(name)
                matched = True
                break
        
        # Try fallback pattern for unmatched lines - more aggressive matching
        if not matched:
            # Try multiple fallback patterns for better coverage
            fallback_patterns = [
                r'\$?\s*(\d+[.,]\d{2})(?!\d)',  # Standard price
                r'(\d+[.,]\d{2})\s*$',  # Price at end
                r'(\d{1,3}[.,]\d{2})\s*[A-Z]?$',  # Price with optional tax code
            ]
            
            for fallback_pattern in fallback_patterns:
                pm = re.search(fallback_pattern, line)
                if pm:
                    price_str = pm.group(1).replace(',', '.')
                    price = normalize_price(price_str)
                    
                    # Use realistic item price limit for fallback matches too
                    if price and price > 0 and price <= Decimal(str(realistic_max_price)):
                        name_part = line[:pm.start()].strip()
                        # Remove quantity prefixes
                        name_part = re.sub(r'^\d+\s*[xX*]\s*', '', name_part).strip()
                        # Remove SKU-like patterns at the end
                        name_part = re.sub(r'\s+\d{10,14}\s*$', '', name_part).strip()
                        # Apply item name cleaning for OCR corrections
                        name_part = clean_item_name(name_part)
                        
                        # Skip garbage text
                        if is_garbage_text(name_part):
                            continue
                        
                        if len(name_part) >= min_name_length and name_part not in seen:
                            if not should_skip_line(name_part) and not should_skip_item_name(name_part):
                                items.append((name_part, price, 1))
                                seen.add(name_part)
                                break  # Found a match, stop trying fallback patterns
    
    return items


def parse_receipt_text(lines: List[str], text_metadata: Optional[List[dict]] = None,
                       min_confidence: float = None, relaxed_mode: bool = None) -> dict:
    """
    Parse raw text lines into structured receipt data - shared implementation.
    
    This is the consolidated implementation used by OCRProcessor, EasyOCRProcessor,
    and PaddleProcessor to avoid code duplication.
    
    Integrates with OCRConfig from the circular exchange framework for dynamic
    parameter management, auto-tuning, and extraction result tracking.
    
    Args:
        lines: List of text lines from OCR
        text_metadata: Optional list of metadata dicts with 'confidence' keys
        min_confidence: Minimum confidence threshold (uses OCRConfig if None)
        relaxed_mode: If True, use less strict validation (uses OCRConfig if None)
        
    Returns:
        Dictionary with extracted receipt fields:
        - store_name: str or None
        - transaction_date: str or None
        - total: Decimal or None
        - subtotal: Decimal or None  
        - tax: Decimal or None
        - items: List of tuples (name, price, quantity)
        - store_address: str or None
        - store_phone: str or None
        - extraction_notes: List of notes
    """
    # Get configuration from circular exchange if not provided
    config = get_config()
    if min_confidence is None:
        min_confidence = config.min_confidence if config else 0.3
    if relaxed_mode is None:
        relaxed_mode = config.relaxed_mode if config else False
    
    # Get auto-fallback setting from config
    auto_fallback = config.auto_fallback if config else True
    relaxed_confidence = config.relaxed_confidence if config else 0.2
    
    result = {
        'store_name': None,
        'transaction_date': None,
        'total': None,
        'subtotal': None,
        'tax': None,
        'items': [],
        'store_address': None,
        'store_phone': None,
        'extraction_notes': []
    }
    
    used_relaxed = False
    
    if not lines:
        result['extraction_notes'].append("No text")
        # Record empty extraction for auto-tuning
        if config:
            config.record_extraction_result(
                items_count=0,
                total_detected=None,
                confidence_avg=0.0,
                success=False,
                used_relaxed=False
            )
        return result
    
    # Extract structured data using shared functions
    result['store_name'] = extract_store_name(lines)
    result['transaction_date'] = extract_date(lines)
    result['total'] = extract_total(lines)
    result['subtotal'] = extract_subtotal(lines)
    result['tax'] = extract_tax(lines)
    # Use improved extraction with configurable thresholds
    result['items'] = extract_line_items(lines, text_metadata, min_confidence, relaxed_mode)
    result['store_address'] = extract_address(lines)
    result['store_phone'] = extract_phone(lines)
    
    # If no items found with standard mode, try relaxed mode (auto-fallback)
    if not result['items'] and not relaxed_mode and auto_fallback:
        result['items'] = extract_line_items(lines, text_metadata, min_confidence=relaxed_confidence, relaxed_mode=True)
        if result['items']:
            result['extraction_notes'].append("Used relaxed extraction mode")
            used_relaxed = True
    
    # Calculate subtotal from items if not found (Section III.C.3 of plan.txt)
    if result['subtotal'] is None and result['items']:
        calculated_subtotal = sum(item[1] for item in result['items'])  # item[1] is price
        if calculated_subtotal > 0:
            result['subtotal'] = calculated_subtotal
            result['extraction_notes'].append(f"Subtotal calculated from {len(result['items'])} items: ${calculated_subtotal}")
    
    # Validate tax: tax should never be greater than subtotal (unrealistic)
    # Tax values greater than subtotal are likely OCR errors
    if result['tax'] is not None and result['subtotal'] is not None:
        if result['tax'] > result['subtotal']:
            result['extraction_notes'].append(f"Tax {result['tax']} > subtotal {result['subtotal']} - rejected as OCR error")
            result['tax'] = None
    
    # Semantic validation: if we have subtotal and total but no tax, calculate tax
    if result['subtotal'] is not None and result['total'] is not None and result['tax'] is None:
        calculated_tax = result['total'] - result['subtotal']
        # Only accept calculated tax if it's reasonable (0-30% of subtotal)
        if calculated_tax >= 0 and (result['subtotal'] == 0 or calculated_tax <= result['subtotal'] * Decimal('0.30')):
            result['tax'] = calculated_tax
            result['extraction_notes'].append(f"Tax calculated: ${calculated_tax}")
    
    # Validate totals for accuracy
    validation = validate_receipt_totals(result['subtotal'], result['tax'], result['total'])
    if validation.get('notes'):
        for note in validation['notes']:
            result['extraction_notes'].append(note)
    
    # Calculate average confidence for recording
    avg_confidence = 0.0
    if text_metadata:
        confidences = [m.get('confidence', 0) for m in text_metadata if m.get('confidence')]
        avg_confidence = sum(confidences) / max(len(confidences), 1)
    
    # Record extraction result for auto-tuning via circular exchange
    if config:
        success = len(result['items']) > 0 or result['total'] is not None
        config.record_extraction_result(
            items_count=len(result['items']),
            total_detected=result['total'],
            confidence_avg=avg_confidence,
            success=success,
            used_relaxed=used_relaxed
        )
    
    return result
