"""
Tests for the shared OCR common utilities module.
"""
import pytest
from decimal import Decimal


class TestNormalizePrice:
    """Tests for normalize_price function"""

    def test_simple_price(self):
        from shared.models.ocr_common import normalize_price
        assert normalize_price('10.50') == Decimal('10.50')

    def test_dollar_sign(self):
        from shared.models.ocr_common import normalize_price
        assert normalize_price('$25.99') == Decimal('25.99')

    def test_thousands_separator(self):
        from shared.models.ocr_common import normalize_price
        assert normalize_price('1,234.56') == Decimal('1234.56')

    def test_european_format(self):
        from shared.models.ocr_common import normalize_price
        # Comma as decimal separator (e.g., 12,50 = 12.50)
        assert normalize_price('12,50') == Decimal('12.50')

    def test_negative_returns_none(self):
        from shared.models.ocr_common import normalize_price
        assert normalize_price('-5.00') is None

    def test_none_returns_none(self):
        from shared.models.ocr_common import normalize_price
        assert normalize_price(None) is None

    def test_empty_string_returns_none(self):
        from shared.models.ocr_common import normalize_price
        assert normalize_price('') is None

    def test_exceeds_max_returns_none(self):
        from shared.models.ocr_common import normalize_price
        assert normalize_price('99999.00') is None

    def test_numeric_input(self):
        from shared.models.ocr_common import normalize_price
        assert normalize_price(25.99) == Decimal('25.99')


class TestExtractDate:
    """Tests for extract_date function"""

    def test_us_format_with_4_digit_year(self):
        from shared.models.ocr_common import extract_date
        assert extract_date(['Store', '12/25/2024', 'Item']) == '12/25/2024'

    def test_iso_format(self):
        from shared.models.ocr_common import extract_date
        assert extract_date(['Store', '2024-01-15', 'Item']) == '2024-01-15'

    def test_us_format_with_2_digit_year(self):
        from shared.models.ocr_common import extract_date
        assert extract_date(['Store', '12/25/24', 'Item']) == '12/25/24'

    def test_no_date_returns_none(self):
        from shared.models.ocr_common import extract_date
        assert extract_date(['No date here']) is None

    def test_empty_list_returns_none(self):
        from shared.models.ocr_common import extract_date
        assert extract_date([]) is None


class TestExtractTotal:
    """Tests for extract_total function"""

    def test_simple_total(self):
        from shared.models.ocr_common import extract_total
        assert extract_total(['Item 5.99', 'Total: $15.99']) == Decimal('15.99')

    def test_uppercase_total(self):
        from shared.models.ocr_common import extract_total
        assert extract_total(['TOTAL $25.00']) == Decimal('25.00')

    def test_amount_keyword(self):
        from shared.models.ocr_common import extract_total
        assert extract_total(['Amount: 30.00']) == Decimal('30.00')

    def test_no_total_returns_none(self):
        from shared.models.ocr_common import extract_total
        assert extract_total(['Item 5.99', 'Tax 1.00']) is None


class TestSkipKeywords:
    """Tests for SKIP_KEYWORDS constant"""

    def test_contains_common_keywords(self):
        from shared.models.ocr_common import SKIP_KEYWORDS
        assert 'total' in SKIP_KEYWORDS
        assert 'subtotal' in SKIP_KEYWORDS
        assert 'tax' in SKIP_KEYWORDS
        assert 'cash' in SKIP_KEYWORDS
        assert 'change' in SKIP_KEYWORDS

    def test_contains_payment_keywords(self):
        from shared.models.ocr_common import SKIP_KEYWORDS
        assert 'visa' in SKIP_KEYWORDS
        assert 'mastercard' in SKIP_KEYWORDS
        assert 'amex' in SKIP_KEYWORDS
        assert 'credit' in SKIP_KEYWORDS
        assert 'debit' in SKIP_KEYWORDS

    def test_is_frozenset(self):
        from shared.models.ocr_common import SKIP_KEYWORDS
        assert isinstance(SKIP_KEYWORDS, frozenset)


class TestShouldSkipLine:
    """Tests for should_skip_line function"""

    def test_skip_total_line(self):
        from shared.models.ocr_common import should_skip_line
        assert should_skip_line('Total: $25.00') is True

    def test_skip_payment_line(self):
        from shared.models.ocr_common import should_skip_line
        assert should_skip_line('VISA **** 1234') is True

    def test_dont_skip_item_line(self):
        from shared.models.ocr_common import should_skip_line
        assert should_skip_line('Coffee $3.50') is False


class TestExtractStoreName:
    """Tests for extract_store_name function"""

    def test_first_valid_line(self):
        from shared.models.ocr_common import extract_store_name
        assert extract_store_name(['STORE NAME', '123 Main St']) == 'STORE NAME'

    def test_skip_digit_only_lines(self):
        from shared.models.ocr_common import extract_store_name
        assert extract_store_name(['123', 'STORE NAME']) == 'STORE NAME'

    def test_empty_list_returns_none(self):
        from shared.models.ocr_common import extract_store_name
        assert extract_store_name([]) is None


class TestExtractPhone:
    """Tests for extract_phone function"""

    def test_standard_format(self):
        from shared.models.ocr_common import extract_phone
        assert extract_phone(['Store', '(555) 123-4567']) == '(555) 123-4567'

    def test_no_parentheses(self):
        from shared.models.ocr_common import extract_phone
        assert extract_phone(['Store', '555-123-4567']) == '555-123-4567'

    def test_no_phone_returns_none(self):
        from shared.models.ocr_common import extract_phone
        assert extract_phone(['No phone here']) is None


class TestExtractAddress:
    """Tests for extract_address function"""

    def test_street_keyword(self):
        from shared.models.ocr_common import extract_address
        result = extract_address(['Store', '123 Main St', 'City'])
        assert result == '123 Main St'

    def test_avenue_keyword(self):
        from shared.models.ocr_common import extract_address
        result = extract_address(['Store', '456 Oak Ave', 'City'])
        assert result == '456 Oak Ave'

    def test_no_address_returns_none(self):
        from shared.models.ocr_common import extract_address
        result = extract_address(['Store', 'No address here'])
        assert result is None
