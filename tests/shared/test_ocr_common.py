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

    def test_thousands_separator_single(self):
        from shared.models.ocr_common import normalize_price
        # 1,234 treated as thousands separator
        assert normalize_price('1,234') == Decimal('1234')

    def test_invalid_comma_format_returns_none(self):
        from shared.models.ocr_common import normalize_price
        # 1,23,4 is invalid format
        assert normalize_price('1,23,4') is None

    def test_ambiguous_comma_treated_as_decimal(self):
        from shared.models.ocr_common import normalize_price
        # 1,23 could be European format (1.23)
        assert normalize_price('1,23') == Decimal('1.23')


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

    def test_subtotal_not_matched_as_total(self):
        """Test that SUBTOTAL is not incorrectly extracted as TOTAL"""
        from shared.models.ocr_common import extract_total
        # When only SUBTOTAL present, should return None
        assert extract_total(['SUBTOTAL 100.00']) is None

    def test_total_extracted_correctly_with_subtotal_present(self):
        """Test that TOTAL is extracted correctly when SUBTOTAL also present"""
        from shared.models.ocr_common import extract_total
        # Should extract TOTAL, not SUBTOTAL
        assert extract_total(['SUBTOTAL 139.44', 'TOTAL 144.02']) == Decimal('144.02')


class TestExtractTax:
    """Tests for extract_tax function"""

    def test_simple_tax(self):
        from shared.models.ocr_common import extract_tax
        assert extract_tax(['TAX 4.58']) == Decimal('4.58')

    def test_tax_with_code_walmart_format(self):
        """Test Walmart-style tax format with tax code"""
        from shared.models.ocr_common import extract_tax
        # TAX 1 is tax category, 4.58 is the actual tax
        assert extract_tax(['TAX 1 4.58']) == Decimal('4.58')

    def test_tax_with_code_no_space(self):
        """Test tax format with code without space (TAX1)"""
        from shared.models.ocr_common import extract_tax
        assert extract_tax(['TAX1 4.58']) == Decimal('4.58')

    def test_tax_with_different_code(self):
        """Test tax with different tax category code"""
        from shared.models.ocr_common import extract_tax
        assert extract_tax(['TAX 2 10.50']) == Decimal('10.50')

    def test_sales_tax(self):
        from shared.models.ocr_common import extract_tax
        assert extract_tax(['SALES TAX 4.58']) == Decimal('4.58')

    def test_no_tax_returns_none(self):
        from shared.models.ocr_common import extract_tax
        assert extract_tax(['TOTAL 100.00']) is None

    def test_taxation_not_matched(self):
        """Test that 'taxation' is not incorrectly matched as 'tax'"""
        from shared.models.ocr_common import extract_tax
        assert extract_tax(['TAXATION info']) is None

    def test_taxable_not_matched(self):
        """Test that 'taxable' is not incorrectly matched as 'tax'"""
        from shared.models.ocr_common import extract_tax
        assert extract_tax(['TAXABLE items']) is None

    def test_whole_dollar_tax(self):
        """Test tax extraction with whole dollar amounts"""
        from shared.models.ocr_common import extract_tax
        assert extract_tax(['TAX 5']) == Decimal('5')
        assert extract_tax(['TAX 15']) == Decimal('15')

    def test_tax_code_with_whole_dollar(self):
        """Test tax code followed by whole dollar amount"""
        from shared.models.ocr_common import extract_tax
        assert extract_tax(['TAX 1 5']) == Decimal('5')


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


class TestItemSkipPatterns:
    """Tests for ITEM_SKIP_PATTERNS constant"""

    def test_contains_store_info_keywords(self):
        from shared.models.ocr_common import ITEM_SKIP_PATTERNS
        assert 'store' in ITEM_SKIP_PATTERNS
        assert 'phone' in ITEM_SKIP_PATTERNS
        assert 'fax' in ITEM_SKIP_PATTERNS
        assert 'email' in ITEM_SKIP_PATTERNS

    def test_contains_hours_keywords(self):
        from shared.models.ocr_common import ITEM_SKIP_PATTERNS
        assert 'open' in ITEM_SKIP_PATTERNS
        assert 'hours' in ITEM_SKIP_PATTERNS
        assert 'daily' in ITEM_SKIP_PATTERNS
        assert 'am' in ITEM_SKIP_PATTERNS
        assert 'pm' in ITEM_SKIP_PATTERNS


class TestShouldSkipItemName:
    """Tests for should_skip_item_name function"""

    def test_skip_store_name(self):
        from shared.models.ocr_common import should_skip_item_name
        assert should_skip_item_name('Store Hours') is True

    def test_skip_phone_info(self):
        from shared.models.ocr_common import should_skip_item_name
        assert should_skip_item_name('Phone: 555-1234') is True

    def test_dont_skip_product_name(self):
        from shared.models.ocr_common import should_skip_item_name
        assert should_skip_item_name('Coffee Large') is False


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


class TestCleanOcrText:
    """Tests for clean_ocr_text function"""

    def test_word_corrections(self):
        from shared.models.ocr_common import clean_ocr_text
        assert 'total' in clean_ocr_text('tota1 amount')
        assert 'subtotal' in clean_ocr_text('subt0tal')

    def test_whitespace_normalization(self):
        from shared.models.ocr_common import clean_ocr_text
        result = clean_ocr_text('too   many    spaces')
        assert '   ' not in result

    def test_punctuation_spacing(self):
        from shared.models.ocr_common import clean_ocr_text
        result = clean_ocr_text('word ,another')
        assert result == 'word, another'


class TestMergeTextLines:
    """Tests for merge_text_lines function"""

    def test_merge_continuation(self):
        from shared.models.ocr_common import merge_text_lines
        lines = ['This is a', 'continuation']
        result = merge_text_lines(lines)
        assert len(result) == 1
        assert 'continuation' in result[0]

    def test_no_merge_complete_sentences(self):
        from shared.models.ocr_common import merge_text_lines
        lines = ['Complete sentence.', 'Another sentence.']
        result = merge_text_lines(lines)
        assert len(result) == 2


class TestCalculateTextConfidence:
    """Tests for calculate_text_confidence function"""

    def test_normal_text(self):
        from shared.models.ocr_common import calculate_text_confidence
        conf = calculate_text_confidence('Hello World', 0.9)
        assert conf >= 0.9

    def test_special_chars_penalty(self):
        from shared.models.ocr_common import calculate_text_confidence
        conf = calculate_text_confidence('@#$%^&*()', 0.9)
        assert conf < 0.9

    def test_short_text_penalty(self):
        from shared.models.ocr_common import calculate_text_confidence
        conf = calculate_text_confidence('A', 0.9)
        assert conf < 0.9


class TestExtractEmail:
    """Tests for extract_email function"""

    def test_valid_email(self):
        from shared.models.ocr_common import extract_email
        result = extract_email(['Contact: test@example.com'])
        assert result == 'test@example.com'

    def test_no_email(self):
        from shared.models.ocr_common import extract_email
        result = extract_email(['No email here'])
        assert result is None


class TestExtractUrl:
    """Tests for extract_url function"""

    def test_https_url(self):
        from shared.models.ocr_common import extract_url
        result = extract_url(['Visit https://example.com'])
        assert result == 'https://example.com'

    def test_www_url(self):
        from shared.models.ocr_common import extract_url
        result = extract_url(['Visit www.example.com'])
        assert result == 'www.example.com'


class TestDetectLanguageHint:
    """Tests for detect_language_hint function"""

    def test_english_default(self):
        from shared.models.ocr_common import detect_language_hint
        result = detect_language_hint('Hello world')
        assert result == 'en'

    def test_spanish_detection(self):
        from shared.models.ocr_common import detect_language_hint
        result = detect_language_hint('el la de que en un es')
        assert result == 'es'


class TestCleanItemName:
    """Tests for clean_item_name function"""

    def test_fix_fashiuned_typo(self):
        from shared.models.ocr_common import clean_item_name
        result = clean_item_name('ORGANIC OLD FASHIUNED OATMEAL')
        assert 'FASHIONED' in result

    def test_fix_plpper_typo(self):
        from shared.models.ocr_common import clean_item_name
        result = clean_item_name('A-PLPPER BELL EACH XL RED')
        assert 'PEPPER' in result

    def test_fix_02_to_oz(self):
        from shared.models.ocr_common import clean_item_name
        result = clean_item_name('R-CARROTS SHREDDED 10 02')
        assert '10 OZ' in result

    def test_fix_xt_to_xl(self):
        from shared.models.ocr_common import clean_item_name
        result = clean_item_name('A-PEPPER BELL EACH Xt RED')
        assert 'XL' in result

    def test_remove_trailing_periods(self):
        from shared.models.ocr_common import clean_item_name
        result = clean_item_name('MINI-PEARL TOMATOES. .')
        assert not result.endswith('.')
        assert 'MINI-PEARL TOMATOES' in result

    def test_remove_trailing_pipe(self):
        from shared.models.ocr_common import clean_item_name
        result = clean_item_name('WHL WHT PITA BREAD |')
        assert not result.endswith('|')
        assert 'PITA BREAD' in result

    def test_normalize_whitespace(self):
        from shared.models.ocr_common import clean_item_name
        result = clean_item_name('EGGS  1  DOZ   ORGANIC')
        assert '  ' not in result

    def test_empty_string(self):
        from shared.models.ocr_common import clean_item_name
        result = clean_item_name('')
        assert result == ''

    def test_none_returns_none(self):
        from shared.models.ocr_common import clean_item_name
        result = clean_item_name(None)
        assert result is None


class TestCorrectStoreName:
    """Tests for correct_store_name function"""

    def test_trader_joes_correction(self):
        from shared.models.ocr_common import correct_store_name
        result = correct_store_name('a ae)')
        assert result == "TRADER JOE'S"

    def test_trader_joes_without_apostrophe(self):
        from shared.models.ocr_common import correct_store_name
        result = correct_store_name('trader joes')
        assert result == "TRADER JOE'S"

    def test_walmart_correction(self):
        from shared.models.ocr_common import correct_store_name
        result = correct_store_name('wa1mart')
        assert result == 'WALMART'

    def test_unknown_store_unchanged(self):
        from shared.models.ocr_common import correct_store_name
        result = correct_store_name('RANDOM STORE')
        assert result == 'RANDOM STORE'

    def test_empty_string(self):
        from shared.models.ocr_common import correct_store_name
        result = correct_store_name('')
        assert result == ''

    def test_none_returns_none(self):
        from shared.models.ocr_common import correct_store_name
        result = correct_store_name(None)
        assert result is None


class TestUnitCorrections:
    """Tests for UNIT_CORRECTIONS constant"""

    def test_oz_correction(self):
        from shared.models.ocr_common import UNIT_CORRECTIONS
        assert ' 02' in UNIT_CORRECTIONS
        assert UNIT_CORRECTIONS[' 02'] == ' OZ'

    def test_xl_correction(self):
        from shared.models.ocr_common import UNIT_CORRECTIONS
        assert 'Xt' in UNIT_CORRECTIONS
        assert UNIT_CORRECTIONS['Xt'] == 'XL'

    def test_ct_correction(self):
        from shared.models.ocr_common import UNIT_CORRECTIONS
        assert 'ct' in UNIT_CORRECTIONS
        assert UNIT_CORRECTIONS['ct'] == 'CT'


class TestStoreNameCorrections:
    """Tests for STORE_NAME_CORRECTIONS constant"""

    def test_contains_trader_joes(self):
        from shared.models.ocr_common import STORE_NAME_CORRECTIONS
        assert 'a ae)' in STORE_NAME_CORRECTIONS
        assert STORE_NAME_CORRECTIONS['a ae)'] == "TRADER JOE'S"

    def test_contains_walmart(self):
        from shared.models.ocr_common import STORE_NAME_CORRECTIONS
        assert 'wa1mart' in STORE_NAME_CORRECTIONS

    def test_contains_costco(self):
        from shared.models.ocr_common import STORE_NAME_CORRECTIONS
        assert 'costc0' in STORE_NAME_CORRECTIONS
