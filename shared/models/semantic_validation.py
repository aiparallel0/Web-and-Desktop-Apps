"""
=============================================================================
SEMANTIC VALIDATION PIPELINE - Receipt Data Validation
=============================================================================

Implements the semantic validation from the enhancement plan:
- Mathematical validation (subtotal + tax = total)
- Date/time validation (transaction date <= now)
- Price reasonableness checks
- Store name validation with fuzzy matching
- Automated error correction for common OCR errors

Usage:
    from semantic_validation import SemanticValidator, validate_receipt
    
    validator = SemanticValidator()
    validation_result = validator.validate(receipt_data)
    
    if validation_result.is_valid:
        print("Receipt validated successfully")
    else:
        for error in validation_result.errors:
            print(f"Error: {error}")

=============================================================================
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""
    ERROR = "error"          # Critical issue, likely incorrect data
    WARNING = "warning"      # Possible issue, needs manual review
    INFO = "info"            # Minor issue or suggestion


class ValidationType(str, Enum):
    """Types of validation checks."""
    MATH = "math_validation"
    DATE = "date_validation"
    PRICE = "price_validation"
    STORE = "store_validation"
    FORMAT = "format_validation"
    COMPLETENESS = "completeness_validation"


@dataclass
class ValidationIssue:
    """Represents a single validation issue."""
    field: str
    message: str
    severity: ValidationSeverity
    validation_type: ValidationType
    original_value: Any = None
    suggested_correction: Any = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            'field': self.field,
            'message': self.message,
            'severity': self.severity.value,
            'type': self.validation_type.value
        }
        if self.original_value is not None:
            result['original'] = self.original_value
        if self.suggested_correction is not None:
            result['suggestion'] = self.suggested_correction
        return result


@dataclass
class ValidationResult:
    """Result of semantic validation."""
    is_valid: bool = True
    math_validated: bool = False
    date_validated: bool = False
    store_validated: bool = False
    completeness_score: float = 0.0
    issues: List[ValidationIssue] = field(default_factory=list)
    corrections_applied: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def errors(self) -> List[str]:
        """Get list of error messages."""
        return [
            issue.message for issue in self.issues 
            if issue.severity == ValidationSeverity.ERROR
        ]
    
    @property
    def warnings(self) -> List[str]:
        """Get list of warning messages."""
        return [
            issue.message for issue in self.issues 
            if issue.severity == ValidationSeverity.WARNING
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'is_valid': self.is_valid,
            'math_validated': self.math_validated,
            'date_validated': self.date_validated,
            'store_validated': self.store_validated,
            'completeness_score': round(self.completeness_score, 2),
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'issues': [issue.to_dict() for issue in self.issues],
            'corrections': self.corrections_applied
        }


# =============================================================================
# KNOWN STORE DATABASE
# =============================================================================

# Comprehensive store name database for validation
KNOWN_STORES = {
    # Major retailers
    'WALMART', 'TARGET', 'COSTCO', 'SAM\'S CLUB', 'KROGER',
    'SAFEWAY', 'ALBERTSONS', 'PUBLIX', 'WHOLE FOODS', 'TRADER JOE\'S',
    'ALDI', 'LIDL', 'FOOD LION', 'GIANT', 'STOP & SHOP',
    'HARRIS TEETER', 'MEIJER', 'FOOD 4 LESS', 'RALPHS', 'VONS',
    
    # Convenience stores
    'CVS', 'WALGREENS', 'RITE AID', '7-ELEVEN', 'CIRCLE K',
    'WAWA', 'SHEETZ', 'SPEEDWAY', 'CASEY\'S', 'RACETRAC',
    
    # Big box stores
    'BEST BUY', 'HOME DEPOT', 'LOWE\'S', 'MENARDS', 'ACE HARDWARE',
    'BED BATH & BEYOND', 'STAPLES', 'OFFICE DEPOT', 'MICHAELS',
    
    # Department stores
    'MACY\'S', 'NORDSTROM', 'KOHL\'S', 'JC PENNEY', 'DILLARD\'S',
    'TJ MAXX', 'MARSHALLS', 'ROSS', 'BURLINGTON',
    
    # Warehouse clubs
    'BJ\'S', 'SAM\'S CLUB',
    
    # Fast food
    'MCDONALD\'S', 'BURGER KING', 'WENDY\'S', 'TACO BELL',
    'CHICK-FIL-A', 'SUBWAY', 'CHIPOTLE', 'FIVE GUYS',
    'PANDA EXPRESS', 'KFC', 'POPEYES', 'ARBY\'S',
    
    # Coffee shops
    'STARBUCKS', 'DUNKIN', 'DUNKIN DONUTS', 'PEET\'S COFFEE',
    'CARIBOU COFFEE', 'TIM HORTONS',
    
    # Gas stations
    'SHELL', 'CHEVRON', 'EXXON', 'MOBIL', 'BP', 'TEXACO',
    'CITGO', 'MARATHON', 'VALERO', 'SUNOCO', 'PHILLIPS 66',
    
    # Pharmacies
    'CVS PHARMACY', 'WALGREENS', 'RITE AID', 'WALMART PHARMACY',
    
    # Dollar stores
    'DOLLAR GENERAL', 'DOLLAR TREE', 'FAMILY DOLLAR', 'FIVE BELOW',
    
    # Pet stores
    'PETCO', 'PETSMART', 'PET SUPPLIES PLUS',
    
    # Auto parts
    'AUTOZONE', 'O\'REILLY', 'ADVANCE AUTO PARTS', 'NAPA',
}


# =============================================================================
# SEMANTIC VALIDATOR
# =============================================================================

class SemanticValidator:
    """
    Validates receipt data using semantic rules.
    
    Performs comprehensive validation including:
    - Mathematical validation of totals
    - Date/time validation
    - Price reasonableness checks
    - Store name verification
    - Format validation
    """
    
    def __init__(
        self,
        math_tolerance: Decimal = Decimal('0.05'),
        min_price: Decimal = Decimal('0.01'),
        max_price: Decimal = Decimal('9999.99'),
        max_date_future_days: int = 1,
        auto_correct: bool = True
    ):
        """
        Initialize the semantic validator.
        
        Args:
            math_tolerance: Allowed difference for math validation
            min_price: Minimum valid price
            max_price: Maximum valid price
            max_date_future_days: Maximum days in future for transaction date
            auto_correct: Whether to automatically correct common errors
        """
        self.math_tolerance = math_tolerance
        self.min_price = min_price
        self.max_price = max_price
        self.max_date_future_days = max_date_future_days
        self.auto_correct = auto_correct
    
    def validate(self, receipt_data: Dict[str, Any]) -> ValidationResult:
        """
        Perform comprehensive validation of receipt data.
        
        Args:
            receipt_data: Dictionary containing receipt fields
            
        Returns:
            ValidationResult with all issues found
        """
        result = ValidationResult()
        
        # Run all validation checks
        self._validate_math(receipt_data, result)
        self._validate_date(receipt_data, result)
        self._validate_prices(receipt_data, result)
        self._validate_store(receipt_data, result)
        self._validate_completeness(receipt_data, result)
        
        # Apply auto-corrections if enabled
        if self.auto_correct:
            self._apply_corrections(receipt_data, result)
        
        # Determine overall validity
        result.is_valid = all(
            issue.severity != ValidationSeverity.ERROR 
            for issue in result.issues
        )
        
        return result
    
    def _validate_math(
        self,
        data: Dict[str, Any],
        result: ValidationResult
    ) -> None:
        """Validate mathematical relationships."""
        try:
            total = self._to_decimal(data.get('total'))
            subtotal = self._to_decimal(data.get('subtotal'))
            tax = self._to_decimal(data.get('tax'))
            
            if total is None:
                result.issues.append(ValidationIssue(
                    field='total',
                    message='Total amount is missing',
                    severity=ValidationSeverity.WARNING,
                    validation_type=ValidationType.MATH
                ))
                return
            
            # Validate subtotal + tax = total
            if subtotal is not None and tax is not None:
                expected = subtotal + tax
                difference = abs(expected - total)
                
                if difference <= self.math_tolerance:
                    result.math_validated = True
                    logger.info(f"Math validation passed: {subtotal} + {tax} = {total}")
                else:
                    result.issues.append(ValidationIssue(
                        field='total',
                        message=f'Math validation failed: subtotal ({subtotal}) + tax ({tax}) = {expected}, but total is {total}',
                        severity=ValidationSeverity.WARNING,
                        validation_type=ValidationType.MATH,
                        original_value={'subtotal': str(subtotal), 'tax': str(tax), 'total': str(total)},
                        suggested_correction={'total': str(expected)}
                    ))
            
            # Validate items sum to subtotal
            items = data.get('items', [])
            if items and subtotal is not None:
                items_total = Decimal('0')
                for item in items:
                    item_price = self._to_decimal(item.get('total_price') or item.get('price'))
                    if item_price:
                        items_total += item_price
                
                if items_total > 0:
                    diff = abs(items_total - subtotal)
                    if diff > self.math_tolerance:
                        result.issues.append(ValidationIssue(
                            field='items',
                            message=f'Items sum ({items_total}) differs from subtotal ({subtotal})',
                            severity=ValidationSeverity.INFO,
                            validation_type=ValidationType.MATH
                        ))
                    else:
                        logger.info(f"Items sum validation passed: {items_total}")
            
        except Exception as e:
            logger.warning(f"Math validation error: {e}")
    
    def _validate_date(
        self,
        data: Dict[str, Any],
        result: ValidationResult
    ) -> None:
        """Validate transaction date."""
        date_str = data.get('transaction_date') or data.get('date')
        
        if not date_str:
            result.issues.append(ValidationIssue(
                field='transaction_date',
                message='Transaction date is missing',
                severity=ValidationSeverity.INFO,
                validation_type=ValidationType.DATE
            ))
            return
        
        try:
            # Parse date (handle various formats)
            parsed_date = self._parse_date(date_str)
            
            if parsed_date:
                now = datetime.now()
                max_future = now + timedelta(days=self.max_date_future_days)
                min_past = now - timedelta(days=365 * 10)  # 10 years max
                
                if parsed_date > max_future:
                    result.issues.append(ValidationIssue(
                        field='transaction_date',
                        message=f'Transaction date ({date_str}) is in the future',
                        severity=ValidationSeverity.ERROR,
                        validation_type=ValidationType.DATE,
                        original_value=date_str
                    ))
                elif parsed_date < min_past:
                    result.issues.append(ValidationIssue(
                        field='transaction_date',
                        message=f'Transaction date ({date_str}) is too old',
                        severity=ValidationSeverity.WARNING,
                        validation_type=ValidationType.DATE,
                        original_value=date_str
                    ))
                else:
                    result.date_validated = True
                    
        except Exception as e:
            logger.warning(f"Date validation error: {e}")
            result.issues.append(ValidationIssue(
                field='transaction_date',
                message=f'Could not parse date: {date_str}',
                severity=ValidationSeverity.WARNING,
                validation_type=ValidationType.DATE,
                original_value=date_str
            ))
    
    def _validate_prices(
        self,
        data: Dict[str, Any],
        result: ValidationResult
    ) -> None:
        """Validate price reasonableness."""
        # Check total
        total = self._to_decimal(data.get('total'))
        if total is not None:
            if total < self.min_price:
                result.issues.append(ValidationIssue(
                    field='total',
                    message=f'Total ({total}) is below minimum ({self.min_price})',
                    severity=ValidationSeverity.WARNING,
                    validation_type=ValidationType.PRICE,
                    original_value=str(total)
                ))
            elif total > self.max_price:
                result.issues.append(ValidationIssue(
                    field='total',
                    message=f'Total ({total}) exceeds maximum ({self.max_price})',
                    severity=ValidationSeverity.WARNING,
                    validation_type=ValidationType.PRICE,
                    original_value=str(total)
                ))
        
        # Check item prices
        items = data.get('items', [])
        for i, item in enumerate(items):
            price = self._to_decimal(item.get('total_price') or item.get('price'))
            if price is not None:
                if price < self.min_price:
                    result.issues.append(ValidationIssue(
                        field=f'items[{i}].price',
                        message=f'Item price ({price}) is below minimum',
                        severity=ValidationSeverity.WARNING,
                        validation_type=ValidationType.PRICE,
                        original_value=str(price)
                    ))
                elif price > self.max_price:
                    result.issues.append(ValidationIssue(
                        field=f'items[{i}].price',
                        message=f'Item price ({price}) exceeds maximum',
                        severity=ValidationSeverity.WARNING,
                        validation_type=ValidationType.PRICE,
                        original_value=str(price)
                    ))
    
    def _validate_store(
        self,
        data: Dict[str, Any],
        result: ValidationResult
    ) -> None:
        """Validate store name."""
        store_name = data.get('store_name')
        
        if not store_name:
            result.issues.append(ValidationIssue(
                field='store_name',
                message='Store name is missing',
                severity=ValidationSeverity.INFO,
                validation_type=ValidationType.STORE
            ))
            return
        
        # Normalize for comparison
        normalized = store_name.upper().strip()
        
        # Check known stores
        if normalized in KNOWN_STORES:
            result.store_validated = True
            return
        
        # Try fuzzy matching
        best_match, score = self._fuzzy_match_store(normalized)
        
        if score >= 0.8:
            result.store_validated = True
            if best_match != normalized:
                result.issues.append(ValidationIssue(
                    field='store_name',
                    message=f'Store name might be: {best_match}',
                    severity=ValidationSeverity.INFO,
                    validation_type=ValidationType.STORE,
                    original_value=store_name,
                    suggested_correction=best_match
                ))
        else:
            # Unknown store - just note it, not an error
            result.issues.append(ValidationIssue(
                field='store_name',
                message=f'Unknown store: {store_name}',
                severity=ValidationSeverity.INFO,
                validation_type=ValidationType.STORE,
                original_value=store_name
            ))
    
    def _validate_completeness(
        self,
        data: Dict[str, Any],
        result: ValidationResult
    ) -> None:
        """Validate data completeness."""
        fields_present = 0
        total_fields = 6  # store, date, items, subtotal, tax, total
        
        if data.get('store_name'):
            fields_present += 1
        if data.get('transaction_date') or data.get('date'):
            fields_present += 1
        if data.get('items') and len(data['items']) > 0:
            fields_present += 1
        if data.get('subtotal') is not None:
            fields_present += 1
        if data.get('tax') is not None:
            fields_present += 1
        if data.get('total') is not None:
            fields_present += 1
        
        result.completeness_score = fields_present / total_fields
        
        if result.completeness_score < 0.5:
            result.issues.append(ValidationIssue(
                field='_completeness',
                message=f'Low data completeness ({result.completeness_score:.0%})',
                severity=ValidationSeverity.WARNING,
                validation_type=ValidationType.COMPLETENESS
            ))
    
    def _apply_corrections(
        self,
        data: Dict[str, Any],
        result: ValidationResult
    ) -> None:
        """Apply automatic corrections for common errors."""
        # Price format normalization
        for field in ['total', 'subtotal', 'tax']:
            value = data.get(field)
            if isinstance(value, str):
                corrected = self._normalize_price_format(value)
                if corrected != value:
                    data[field] = corrected
                    result.corrections_applied.append({
                        'field': field,
                        'original': value,
                        'corrected': corrected,
                        'type': 'price_format'
                    })
        
        # Item price normalization
        items = data.get('items', [])
        for i, item in enumerate(items):
            for field in ['price', 'total_price']:
                value = item.get(field)
                if isinstance(value, str):
                    corrected = self._normalize_price_format(value)
                    if corrected != value:
                        item[field] = corrected
                        result.corrections_applied.append({
                            'field': f'items[{i}].{field}',
                            'original': value,
                            'corrected': corrected,
                            'type': 'price_format'
                        })
        
        # Date format standardization
        date_val = data.get('transaction_date') or data.get('date')
        if date_val:
            parsed = self._parse_date(date_val)
            if parsed:
                standardized = parsed.strftime('%Y-%m-%d')
                if standardized != date_val:
                    if 'transaction_date' in data:
                        data['transaction_date'] = standardized
                    else:
                        data['date'] = standardized
                    result.corrections_applied.append({
                        'field': 'transaction_date',
                        'original': date_val,
                        'corrected': standardized,
                        'type': 'date_format'
                    })
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _to_decimal(self, value: Any) -> Optional[Decimal]:
        """Convert value to Decimal safely."""
        if value is None:
            return None
        try:
            if isinstance(value, Decimal):
                return value
            if isinstance(value, (int, float)):
                return Decimal(str(value))
            if isinstance(value, str):
                # Clean the string
                cleaned = value.replace('$', '').replace(',', '').strip()
                if cleaned:
                    return Decimal(cleaned)
            return None
        except (InvalidOperation, ValueError):
            return None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string in various formats."""
        if not date_str:
            return None
        
        # Common date formats
        formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%m/%d/%y',
            '%d/%m/%Y',
            '%d/%m/%y',
            '%m-%d-%Y',
            '%m-%d-%y',
            '%B %d, %Y',
            '%b %d, %Y',
            '%d %B %Y',
            '%d %b %Y',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        
        return None
    
    def _normalize_price_format(self, value: str) -> str:
        """Normalize price format."""
        if not value:
            return value
        
        # Remove currency symbols
        cleaned = value.replace('$', '').replace('€', '').replace('£', '')
        
        # Handle common OCR errors in digit recognition
        # Note: Only apply digit corrections, not letter 'S' which could be valid in item names
        cleaned = cleaned.replace(' ', '')
        cleaned = cleaned.replace('O', '0').replace('o', '0')  # Letter O -> digit 0
        cleaned = cleaned.replace('l', '1').replace('I', '1')  # Letter l/I -> digit 1
        
        # Handle dash as decimal (e.g., "1-99" -> "1.99")
        cleaned = re.sub(r'(\d)-(\d{2})$', r'\1.\2', cleaned)
        
        # Ensure proper decimal format for prices without decimals
        if cleaned and '.' not in cleaned and len(cleaned) >= 3:
            # Insert decimal before last two digits
            cleaned = cleaned[:-2] + '.' + cleaned[-2:]
        
        return cleaned
    
    def _fuzzy_match_store(self, name: str) -> Tuple[str, float]:
        """Find best matching store name using fuzzy matching."""
        best_match = name
        best_score = 0.0
        
        for known in KNOWN_STORES:
            score = self._levenshtein_ratio(name, known)
            if score > best_score:
                best_score = score
                best_match = known
        
        return best_match, best_score
    
    def _levenshtein_ratio(self, s1: str, s2: str) -> float:
        """Calculate Levenshtein similarity ratio."""
        if not s1 or not s2:
            return 0.0
        
        len1, len2 = len(s1), len(s2)
        
        if len1 < len2:
            s1, s2 = s2, s1
            len1, len2 = len2, len1
        
        distances = range(len2 + 1)
        for i, c1 in enumerate(s1):
            new_distances = [i + 1]
            for j, c2 in enumerate(s2):
                if c1 == c2:
                    new_distances.append(distances[j])
                else:
                    new_distances.append(1 + min((distances[j], distances[j + 1], new_distances[-1])))
            distances = new_distances
        
        distance = distances[-1]
        max_len = max(len1, len2)
        return 1 - (distance / max_len)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def validate_receipt(receipt_data: Dict[str, Any]) -> ValidationResult:
    """
    Convenience function to validate receipt data.
    
    Args:
        receipt_data: Dictionary containing receipt fields
        
    Returns:
        ValidationResult with all issues found
    """
    validator = SemanticValidator()
    return validator.validate(receipt_data)


def get_validation_summary(result: ValidationResult) -> Dict[str, Any]:
    """
    Get a summary of validation results.
    
    Args:
        result: ValidationResult to summarize
        
    Returns:
        Dictionary with summary information
    """
    return {
        'is_valid': result.is_valid,
        'checks_passed': {
            'math': result.math_validated,
            'date': result.date_validated,
            'store': result.store_validated
        },
        'completeness': f'{result.completeness_score:.0%}',
        'errors': len(result.errors),
        'warnings': len(result.warnings),
        'corrections': len(result.corrections_applied)
    }


# Global validator instance
semantic_validator = SemanticValidator()
