"""
Receipt-Specific Prompt Engineering Module

This module provides sophisticated prompt templates and extraction strategies
for commercial receipt OCR processing. It addresses the key challenges of:

1. Accurate monetary value extraction (totals, subtotals, taxes)
2. Reliable date parsing across multiple formats
3. Proper store/merchant identification
4. Line item extraction with correct pricing

The prompts are designed to guide OCR models toward more accurate and
validated receipt data extraction suitable for fiscal documentation.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal, InvalidOperation
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ============================================================================
# RECEIPT FIELD VALIDATION PATTERNS
# ============================================================================

# Strict patterns for validating extracted fields
STRICT_TOTAL_PATTERNS = [
    # Must have clear total indicator and valid price format
    re.compile(r'(?:TOTAL|GRAND\s*TOTAL|AMOUNT\s*DUE|BALANCE)\s*:?\s*\$?\s*(\d{1,4})[.,](\d{2})\b', re.IGNORECASE),
    # Reverse format: price TOTAL
    re.compile(r'\$?\s*(\d{1,4})[.,](\d{2})\s+(?:TOTAL|GRAND\s*TOTAL)\b', re.IGNORECASE),
]

STRICT_DATE_PATTERNS = [
    # ISO format YYYY-MM-DD
    re.compile(r'\b(20\d{2})[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12]\d|3[01])\b'),
    # US format MM/DD/YYYY
    re.compile(r'\b(0[1-9]|1[0-2])[-/](0[1-9]|[12]\d|3[01])[-/](20\d{2})\b'),
    # US format MM/DD/YY
    re.compile(r'\b(0?[1-9]|1[0-2])[-/](0?[1-9]|[12]\d|3[01])[-/](\d{2})\b'),
    # Month name format: Jan 15, 2024
    re.compile(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(\d{1,2}),?\s+(20\d{2})\b', re.IGNORECASE),
]

STRICT_PHONE_PATTERN = re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')

# Store name validation - must have at least 2 letters and be reasonable length
VALID_STORE_NAME_PATTERN = re.compile(r'^[A-Z][A-Za-z0-9\s\'\-&]{2,40}$')


# ============================================================================
# CONFIDENCE PENALTIES AND BONUSES
# ============================================================================

@dataclass
class ConfidencePenalty:
    """Represents a confidence penalty or bonus with reason."""
    reason: str
    adjustment: float  # Negative for penalty, positive for bonus
    severity: str = "warning"  # "info", "warning", "critical"


@dataclass
class ExtractionValidation:
    """Results of validating extracted receipt data."""
    is_valid: bool = True
    confidence_adjustments: List[ConfidencePenalty] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    validated_total: Optional[Decimal] = None
    validated_date: Optional[str] = None
    validated_store: Optional[str] = None
    math_validated: bool = False


# ============================================================================
# FIELD VALIDATORS
# ============================================================================

def validate_monetary_value(value: Any, field_name: str = "value") -> Tuple[Optional[Decimal], List[ConfidencePenalty]]:
    """
    Validate and parse a monetary value with confidence adjustments.
    
    Args:
        value: The value to validate (can be string, Decimal, float, etc.)
        field_name: Name of the field for error messages
        
    Returns:
        Tuple of (validated Decimal or None, list of confidence adjustments)
    """
    penalties = []
    
    if value is None:
        penalties.append(ConfidencePenalty(
            reason=f"{field_name} not found",
            adjustment=-0.15,
            severity="warning"
        ))
        return None, penalties
    
    try:
        # Convert to string and clean
        value_str = str(value).strip()
        
        # Remove currency symbols and extra whitespace
        clean_value = re.sub(r'[\$€£\s]', '', value_str)
        
        # Handle comma as decimal separator
        if re.match(r'^\d+,\d{2}$', clean_value):
            clean_value = clean_value.replace(',', '.')
        # Handle thousands separator
        elif re.match(r'^\d{1,3}(,\d{3})*\.\d{2}$', clean_value):
            clean_value = clean_value.replace(',', '')
        
        # Parse as Decimal
        decimal_value = Decimal(clean_value)
        
        # Validate range
        if decimal_value <= 0:
            penalties.append(ConfidencePenalty(
                reason=f"{field_name} is zero or negative: {decimal_value}",
                adjustment=-0.30,
                severity="critical"
            ))
            return None, penalties
        
        if decimal_value > Decimal('10000'):
            penalties.append(ConfidencePenalty(
                reason=f"{field_name} exceeds reasonable limit: {decimal_value}",
                adjustment=-0.25,
                severity="warning"
            ))
            # Still return the value but with penalty
        
        return decimal_value, penalties
        
    except (InvalidOperation, ValueError, TypeError) as e:
        penalties.append(ConfidencePenalty(
            reason=f"Failed to parse {field_name}: {value} ({e})",
            adjustment=-0.20,
            severity="critical"
        ))
        return None, penalties


def validate_date(date_str: Optional[str]) -> Tuple[Optional[str], List[ConfidencePenalty]]:
    """
    Validate a date string with confidence adjustments.
    
    Args:
        date_str: The date string to validate
        
    Returns:
        Tuple of (validated date string or None, list of confidence adjustments)
    """
    penalties = []
    
    if not date_str:
        penalties.append(ConfidencePenalty(
            reason="Date not found",
            adjustment=-0.10,
            severity="warning"
        ))
        return None, penalties
    
    date_str = str(date_str).strip()
    
    # Try each strict pattern
    for pattern in STRICT_DATE_PATTERNS:
        if pattern.search(date_str):
            # Valid date format found
            penalties.append(ConfidencePenalty(
                reason="Date format validated",
                adjustment=0.05,
                severity="info"
            ))
            return date_str, penalties
    
    # Date present but in unclear format
    if re.search(r'\d{1,4}[/-]\d{1,2}[/-]\d{1,4}', date_str):
        penalties.append(ConfidencePenalty(
            reason=f"Date format unclear: {date_str}",
            adjustment=-0.05,
            severity="warning"
        ))
        return date_str, penalties
    
    penalties.append(ConfidencePenalty(
        reason=f"Invalid date format: {date_str}",
        adjustment=-0.15,
        severity="warning"
    ))
    return None, penalties


def validate_store_name(store_name: Optional[str]) -> Tuple[Optional[str], List[ConfidencePenalty]]:
    """
    Validate a store name with confidence adjustments.
    
    Args:
        store_name: The store name to validate
        
    Returns:
        Tuple of (validated store name or None, list of confidence adjustments)
    """
    penalties = []
    
    if not store_name:
        penalties.append(ConfidencePenalty(
            reason="Store name not found",
            adjustment=-0.15,
            severity="warning"
        ))
        return None, penalties
    
    store_name = str(store_name).strip()
    
    # Too short
    if len(store_name) < 3:
        penalties.append(ConfidencePenalty(
            reason=f"Store name too short: '{store_name}'",
            adjustment=-0.15,
            severity="warning"
        ))
        return None, penalties
    
    # Too long (likely OCR garbage)
    if len(store_name) > 50:
        penalties.append(ConfidencePenalty(
            reason=f"Store name too long: {len(store_name)} chars",
            adjustment=-0.20,
            severity="warning"
        ))
        # Truncate and still return
        store_name = store_name[:50]
    
    # Check for garbage characters
    garbage_ratio = sum(1 for c in store_name if not c.isalnum() and not c.isspace() and c not in "'&-") / len(store_name)
    if garbage_ratio > 0.3:
        penalties.append(ConfidencePenalty(
            reason=f"Store name has excessive special characters: '{store_name}'",
            adjustment=-0.25,
            severity="critical"
        ))
        return None, penalties
    
    # Valid store name
    penalties.append(ConfidencePenalty(
        reason="Store name validated",
        adjustment=0.05,
        severity="info"
    ))
    return store_name, penalties


def validate_receipt_math(
    total: Optional[Decimal],
    subtotal: Optional[Decimal],
    tax: Optional[Decimal],
    items_sum: Optional[Decimal],
    tolerance: Decimal = Decimal('0.10')
) -> Tuple[bool, List[ConfidencePenalty]]:
    """
    Validate receipt math: subtotal + tax = total and items sum ≈ subtotal.
    
    This is a CRITICAL validation - if math doesn't check out, the extracted
    values are likely wrong, and confidence should be significantly reduced.
    
    Args:
        total: Extracted total
        subtotal: Extracted subtotal
        tax: Extracted tax
        items_sum: Sum of all extracted item prices
        tolerance: Maximum acceptable difference
        
    Returns:
        Tuple of (math_valid bool, list of confidence adjustments)
    """
    penalties = []
    math_valid = True
    
    if total is None:
        penalties.append(ConfidencePenalty(
            reason="Cannot validate math without total",
            adjustment=-0.30,
            severity="critical"
        ))
        return False, penalties
    
    # Check subtotal + tax = total
    if subtotal is not None and tax is not None:
        expected_total = subtotal + tax
        difference = abs(expected_total - total)
        
        if difference <= tolerance:
            penalties.append(ConfidencePenalty(
                reason="Subtotal + Tax = Total ✓",
                adjustment=0.15,  # Significant bonus for valid math
                severity="info"
            ))
        else:
            penalties.append(ConfidencePenalty(
                reason=f"Math error: {subtotal} + {tax} = {expected_total}, expected {total}",
                adjustment=-0.25,
                severity="critical"
            ))
            math_valid = False
    
    # Check items sum against subtotal or total
    if items_sum is not None and items_sum > 0:
        comparison_value = subtotal if subtotal else total
        if comparison_value:
            coverage = (items_sum / comparison_value) * 100
            
            if 95 <= coverage <= 105:
                penalties.append(ConfidencePenalty(
                    reason=f"Items sum matches total ({coverage:.1f}% coverage) ✓",
                    adjustment=0.10,
                    severity="info"
                ))
            elif 80 <= coverage <= 120:
                penalties.append(ConfidencePenalty(
                    reason=f"Items sum close to total ({coverage:.1f}% coverage)",
                    adjustment=0.03,
                    severity="info"
                ))
            else:
                penalties.append(ConfidencePenalty(
                    reason=f"Items sum mismatch: {items_sum} vs {comparison_value} ({coverage:.1f}%)",
                    adjustment=-0.15,
                    severity="warning"
                ))
                # Don't mark as invalid - items often partially extracted
    
    return math_valid, penalties


# ============================================================================
# COMPREHENSIVE VALIDATION
# ============================================================================

def validate_receipt_extraction(
    store_name: Optional[str],
    total: Optional[Decimal],
    subtotal: Optional[Decimal],
    tax: Optional[Decimal],
    transaction_date: Optional[str],
    items: List[Any],
    raw_text: str = ""
) -> ExtractionValidation:
    """
    Comprehensively validate extracted receipt data and calculate realistic confidence.
    
    This is the main validation function that should be called after OCR extraction
    to determine how confident we should be in the results.
    
    Args:
        store_name: Extracted store name
        total: Extracted total amount
        subtotal: Extracted subtotal
        tax: Extracted tax
        transaction_date: Extracted date
        items: List of extracted line items
        raw_text: Raw OCR text for additional validation
        
    Returns:
        ExtractionValidation with validated fields and confidence adjustments
    """
    validation = ExtractionValidation()
    
    # Validate store name
    validated_store, store_penalties = validate_store_name(store_name)
    validation.validated_store = validated_store
    validation.confidence_adjustments.extend(store_penalties)
    
    # Validate total (critical field)
    validated_total, total_penalties = validate_monetary_value(total, "total")
    validation.validated_total = validated_total
    validation.confidence_adjustments.extend(total_penalties)
    
    if validated_total is None:
        validation.errors.append("CRITICAL: Failed to extract valid total amount")
        validation.is_valid = False
    
    # Validate date
    validated_date, date_penalties = validate_date(transaction_date)
    validation.validated_date = validated_date
    validation.confidence_adjustments.extend(date_penalties)
    
    # Calculate items sum
    items_sum = None
    if items:
        try:
            items_sum = sum(
                Decimal(str(item.total_price if hasattr(item, 'total_price') else item.get('total_price', 0)))
                for item in items
                if item
            )
        except (InvalidOperation, TypeError, AttributeError):
            validation.warnings.append("Could not calculate items sum")
    
    # Validate math
    validated_subtotal, _ = validate_monetary_value(subtotal, "subtotal")
    validated_tax, _ = validate_monetary_value(tax, "tax")
    
    math_valid, math_penalties = validate_receipt_math(
        validated_total, validated_subtotal, validated_tax, items_sum
    )
    validation.math_validated = math_valid
    validation.confidence_adjustments.extend(math_penalties)
    
    # Additional validation: check if we have reasonable content
    if not items or len(items) == 0:
        validation.confidence_adjustments.append(ConfidencePenalty(
            reason="No line items extracted",
            adjustment=-0.10,
            severity="warning"
        ))
    elif len(items) > 50:
        validation.confidence_adjustments.append(ConfidencePenalty(
            reason=f"Unusually high item count: {len(items)}",
            adjustment=-0.05,
            severity="warning"
        ))
    else:
        validation.confidence_adjustments.append(ConfidencePenalty(
            reason=f"Extracted {len(items)} items",
            adjustment=min(0.10, len(items) * 0.02),
            severity="info"
        ))
    
    # Check raw text quality if provided (single pass for efficiency)
    if raw_text:
        text_len = len(raw_text)
        if text_len > 0:
            special_count = sum(1 for c in raw_text if not c.isalnum() and not c.isspace())
            special_char_ratio = special_count / text_len
            if special_char_ratio > 0.4:
                validation.confidence_adjustments.append(ConfidencePenalty(
                    reason=f"High OCR noise detected ({special_char_ratio:.1%} special chars)",
                    adjustment=-0.20,
                    severity="warning"
                ))
    
    return validation


def calculate_realistic_confidence(
    base_confidence: float,
    validation: ExtractionValidation
) -> float:
    """
    Calculate a realistic confidence score based on validation results.
    
    Unlike naive confidence that just counts present fields, this function
    applies penalties for validation failures and provides a more accurate
    assessment of extraction quality.
    
    Args:
        base_confidence: Initial confidence from OCR engine (0.0 to 1.0)
        validation: Validation results from validate_receipt_extraction
        
    Returns:
        Adjusted confidence score (0.0 to 1.0)
    """
    confidence = base_confidence
    
    # Apply all adjustments
    for adjustment in validation.confidence_adjustments:
        confidence += adjustment.adjustment
    
    # Additional penalty if validation failed
    if not validation.is_valid:
        confidence -= 0.20
    
    # Bonus for math validation
    if validation.math_validated:
        confidence += 0.05
    
    # Clamp to valid range
    confidence = max(0.0, min(1.0, confidence))
    
    logger.debug(
        f"Confidence calculation: base={base_confidence:.2f}, "
        f"adjustments={len(validation.confidence_adjustments)}, "
        f"final={confidence:.2f}"
    )
    
    return confidence


# ============================================================================
# RECEIPT EXTRACTION PROMPTS
# ============================================================================

# These are prompt templates that can be used with LLM-based models
# to guide receipt data extraction

RECEIPT_EXTRACTION_SYSTEM_PROMPT = """You are a precise receipt data extraction system. Your task is to extract structured information from commercial receipt text.

CRITICAL REQUIREMENTS:
1. TOTAL AMOUNT: The total/final amount is the most important field. Look for keywords: TOTAL, GRAND TOTAL, AMOUNT DUE, BALANCE DUE. It should be the largest monetary value on the receipt.

2. STORE NAME: Usually appears at the top of the receipt. Common stores: WALMART, TARGET, COSTCO, KROGER, SAFEWAY, TRADER JOE'S, WHOLE FOODS, CVS, WALGREENS.

3. DATE: Look for date patterns like MM/DD/YYYY, YYYY-MM-DD, or written dates like "Jan 15, 2024".

4. LINE ITEMS: Each item typically has a name and price. Format: "ITEM NAME  $X.XX"

5. SUBTOTAL: Sum before tax. Look for: SUBTOTAL, SUB TOTAL, MERCHANDISE TOTAL.

6. TAX: Look for: TAX, SALES TAX, ST TAX. Usually a smaller amount.

VALIDATION RULES:
- Total should equal Subtotal + Tax (within $0.10)
- All prices should be positive
- Store name should be 3-50 characters
- Date should be a valid date format

If you cannot confidently extract a field, indicate uncertainty rather than guessing."""

RECEIPT_PARSING_INSTRUCTIONS = """
Parse the following receipt text and extract:
1. store_name: The merchant/store name
2. transaction_date: The transaction date
3. total: The final total amount
4. subtotal: The pre-tax subtotal
5. tax: The tax amount
6. items: List of {name, price} for each line item

IMPORTANT: If math doesn't add up (subtotal + tax ≠ total), flag this as a potential OCR error.

Receipt Text:
{receipt_text}

Extract the data in JSON format:
"""


# ============================================================================
# HELPER FUNCTIONS FOR OCR PROCESSORS
# ============================================================================

def get_validated_extraction_with_confidence(
    receipt_data: Any,
    raw_text: str = "",
    base_confidence: float = 0.5
) -> Tuple[Any, float, ExtractionValidation]:
    """
    Validate receipt data and return realistic confidence.
    
    This is a convenience function for OCR processors to validate their
    extraction results and get a realistic confidence score.
    
    Args:
        receipt_data: ReceiptData object or similar
        raw_text: Raw OCR text
        base_confidence: Initial confidence from OCR
        
    Returns:
        Tuple of (receipt_data, adjusted_confidence, validation_results)
    """
    # Extract fields from receipt data
    store_name = getattr(receipt_data, 'store_name', None)
    total = getattr(receipt_data, 'total', None)
    subtotal = getattr(receipt_data, 'subtotal', None)
    tax = getattr(receipt_data, 'tax', None)
    transaction_date = getattr(receipt_data, 'transaction_date', None)
    items = getattr(receipt_data, 'items', [])
    
    # Run validation
    validation = validate_receipt_extraction(
        store_name=store_name,
        total=total,
        subtotal=subtotal,
        tax=tax,
        transaction_date=transaction_date,
        items=items,
        raw_text=raw_text
    )
    
    # Calculate realistic confidence
    realistic_confidence = calculate_realistic_confidence(base_confidence, validation)
    
    # Log validation summary
    if validation.errors:
        for error in validation.errors:
            logger.warning(f"Extraction error: {error}")
    if validation.warnings:
        for warning in validation.warnings:
            logger.info(f"Extraction warning: {warning}")
    
    return receipt_data, realistic_confidence, validation


__all__ = [
    'validate_receipt_extraction',
    'calculate_realistic_confidence',
    'get_validated_extraction_with_confidence',
    'ExtractionValidation',
    'ConfidencePenalty',
    'validate_monetary_value',
    'validate_date',
    'validate_store_name',
    'validate_receipt_math',
    'RECEIPT_EXTRACTION_SYSTEM_PROMPT',
    'RECEIPT_PARSING_INSTRUCTIONS',
]
