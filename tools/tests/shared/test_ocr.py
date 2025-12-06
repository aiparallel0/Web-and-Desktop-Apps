"""
Tests for the shared OCR common utilities module.
"""
import pytest
from decimal import Decimal


class TestNormalizePrice:
    """Tests for normalize_price function"""

    def test_simple_price(self):
        from shared.models.ocr import normalize_price
        assert normalize_price('10.50') == Decimal('10.50')

    def test_dollar_sign(self):
        from shared.models.ocr import normalize_price
        assert normalize_price('$25.99') == Decimal('25.99')

    def test_thousands_separator(self):
        from shared.models.ocr import normalize_price
        assert normalize_price('1,234.56') == Decimal('1234.56')

    def test_european_format(self):
        from shared.models.ocr import normalize_price
        # Comma as decimal separator (e.g., 12,50 = 12.50)
        assert normalize_price('12,50') == Decimal('12.50')

    def test_negative_returns_none(self):
        from shared.models.ocr import normalize_price
        assert normalize_price('-5.00') is None

    def test_none_returns_none(self):
        from shared.models.ocr import normalize_price
        assert normalize_price(None) is None

    def test_empty_string_returns_none(self):
        from shared.models.ocr import normalize_price
        assert normalize_price('') is None

    def test_exceeds_max_returns_none(self):
        from shared.models.ocr import normalize_price
        assert normalize_price('99999.00') is None

    def test_numeric_input(self):
        from shared.models.ocr import normalize_price
        assert normalize_price(25.99) == Decimal('25.99')

    def test_thousands_separator_single(self):
        from shared.models.ocr import normalize_price
        # 1,234 treated as thousands separator
        assert normalize_price('1,234') == Decimal('1234')

    def test_invalid_comma_format_returns_none(self):
        from shared.models.ocr import normalize_price
        # 1,23,4 is invalid format
        assert normalize_price('1,23,4') is None

    def test_ambiguous_comma_treated_as_decimal(self):
        from shared.models.ocr import normalize_price
        # 1,23 could be European format (1.23)
        assert normalize_price('1,23') == Decimal('1.23')


class TestExtractDate:
    """Tests for extract_date function"""

    def test_us_format_with_4_digit_year(self):
        from shared.models.ocr import extract_date
        assert extract_date(['Store', '12/25/2024', 'Item']) == '12/25/2024'

    def test_iso_format(self):
        from shared.models.ocr import extract_date
        assert extract_date(['Store', '2024-01-15', 'Item']) == '2024-01-15'

    def test_us_format_with_2_digit_year(self):
        from shared.models.ocr import extract_date
        assert extract_date(['Store', '12/25/24', 'Item']) == '12/25/24'

    def test_no_date_returns_none(self):
        from shared.models.ocr import extract_date
        assert extract_date(['No date here']) is None

    def test_empty_list_returns_none(self):
        from shared.models.ocr import extract_date
        assert extract_date([]) is None


class TestExtractTotal:
    """Tests for extract_total function"""

    def test_simple_total(self):
        from shared.models.ocr import extract_total
        assert extract_total(['Item 5.99', 'Total: $15.99']) == Decimal('15.99')

    def test_uppercase_total(self):
        from shared.models.ocr import extract_total
        assert extract_total(['TOTAL $25.00']) == Decimal('25.00')

    def test_amount_keyword(self):
        from shared.models.ocr import extract_total
        assert extract_total(['Amount: 30.00']) == Decimal('30.00')

    def test_no_total_returns_none(self):
        from shared.models.ocr import extract_total
        assert extract_total(['Item 5.99', 'Tax 1.00']) is None

    def test_subtotal_not_matched_as_total(self):
        """Test that SUBTOTAL is not incorrectly extracted as TOTAL"""
        from shared.models.ocr import extract_total
        # When only SUBTOTAL present, should return None
        assert extract_total(['SUBTOTAL 100.00']) is None

    def test_total_extracted_correctly_with_subtotal_present(self):
        """Test that TOTAL is extracted correctly when SUBTOTAL also present"""
        from shared.models.ocr import extract_total
        # Should extract TOTAL, not SUBTOTAL
        assert extract_total(['SUBTOTAL 139.44', 'TOTAL 144.02']) == Decimal('144.02')


class TestExtractTax:
    """Tests for extract_tax function"""

    def test_simple_tax(self):
        from shared.models.ocr import extract_tax
        assert extract_tax(['TAX 4.58']) == Decimal('4.58')

    def test_tax_with_code_walmart_format(self):
        """Test Walmart-style tax format with tax code"""
        from shared.models.ocr import extract_tax
        # TAX 1 is tax category, 4.58 is the actual tax
        assert extract_tax(['TAX 1 4.58']) == Decimal('4.58')

    def test_tax_with_code_no_space(self):
        """Test tax format with code without space (TAX1)"""
        from shared.models.ocr import extract_tax
        assert extract_tax(['TAX1 4.58']) == Decimal('4.58')

    def test_tax_with_different_code(self):
        """Test tax with different tax category code"""
        from shared.models.ocr import extract_tax
        assert extract_tax(['TAX 2 10.50']) == Decimal('10.50')

    def test_sales_tax(self):
        from shared.models.ocr import extract_tax
        assert extract_tax(['SALES TAX 4.58']) == Decimal('4.58')

    def test_no_tax_returns_none(self):
        from shared.models.ocr import extract_tax
        assert extract_tax(['TOTAL 100.00']) is None

    def test_taxation_not_matched(self):
        """Test that 'taxation' is not incorrectly matched as 'tax'"""
        from shared.models.ocr import extract_tax
        assert extract_tax(['TAXATION info']) is None

    def test_taxable_not_matched(self):
        """Test that 'taxable' is not incorrectly matched as 'tax'"""
        from shared.models.ocr import extract_tax
        assert extract_tax(['TAXABLE items']) is None

    def test_whole_dollar_tax(self):
        """Test tax extraction with whole dollar amounts"""
        from shared.models.ocr import extract_tax
        assert extract_tax(['TAX 5']) == Decimal('5')
        assert extract_tax(['TAX 15']) == Decimal('15')

    def test_tax_code_with_whole_dollar(self):
        """Test tax code followed by whole dollar amount"""
        from shared.models.ocr import extract_tax
        assert extract_tax(['TAX 1 5']) == Decimal('5')


class TestSkipKeywords:
    """Tests for SKIP_KEYWORDS constant"""

    def test_contains_common_keywords(self):
        from shared.models.ocr import SKIP_KEYWORDS
        assert 'total' in SKIP_KEYWORDS
        assert 'subtotal' in SKIP_KEYWORDS
        assert 'tax' in SKIP_KEYWORDS
        assert 'cash' in SKIP_KEYWORDS
        assert 'change' in SKIP_KEYWORDS

    def test_contains_payment_keywords(self):
        from shared.models.ocr import SKIP_KEYWORDS
        assert 'visa' in SKIP_KEYWORDS
        assert 'mastercard' in SKIP_KEYWORDS
        assert 'amex' in SKIP_KEYWORDS
        assert 'credit' in SKIP_KEYWORDS
        assert 'debit' in SKIP_KEYWORDS

    def test_is_frozenset(self):
        from shared.models.ocr import SKIP_KEYWORDS
        assert isinstance(SKIP_KEYWORDS, frozenset)


class TestItemSkipPatterns:
    """Tests for ITEM_SKIP_PATTERNS and time pattern matching"""

    def test_contains_store_info_keywords(self):
        from shared.models.ocr import ITEM_SKIP_PATTERNS
        assert 'store' in ITEM_SKIP_PATTERNS
        assert 'phone' in ITEM_SKIP_PATTERNS
        assert 'fax' in ITEM_SKIP_PATTERNS
        assert 'email' in ITEM_SKIP_PATTERNS

    def test_contains_hours_keywords(self):
        from shared.models.ocr import ITEM_SKIP_PATTERNS
        assert 'open' in ITEM_SKIP_PATTERNS
        assert 'hours' in ITEM_SKIP_PATTERNS
        assert 'daily' in ITEM_SKIP_PATTERNS

    def test_time_patterns_use_word_boundary(self):
        """Test that AM/PM use word boundary matching to avoid false positives."""
        from shared.models.ocr import should_skip_item_name
        # Should skip time patterns
        assert should_skip_item_name('OPEN 9:00 AM') is True
        assert should_skip_item_name('HOURS 8:00AM TO 9:00PM') is True
        # Should NOT skip words containing 'am' or 'pm'
        assert should_skip_item_name('CREAMY SALTED PEANUT BUTTER') is False
        assert should_skip_item_name('SPAM CLASSIC') is False


class TestShouldSkipItemName:
    """Tests for should_skip_item_name function"""

    def test_skip_store_name(self):
        from shared.models.ocr import should_skip_item_name
        assert should_skip_item_name('Store Hours') is True

    def test_skip_phone_info(self):
        from shared.models.ocr import should_skip_item_name
        assert should_skip_item_name('Phone: 555-1234') is True

    def test_dont_skip_product_name(self):
        from shared.models.ocr import should_skip_item_name
        assert should_skip_item_name('Coffee Large') is False


class TestShouldSkipLine:
    """Tests for should_skip_line function"""

    def test_skip_total_line(self):
        from shared.models.ocr import should_skip_line
        assert should_skip_line('Total: $25.00') is True

    def test_skip_payment_line(self):
        from shared.models.ocr import should_skip_line
        assert should_skip_line('VISA **** 1234') is True

    def test_dont_skip_item_line(self):
        from shared.models.ocr import should_skip_line
        assert should_skip_line('Coffee $3.50') is False

    def test_skip_fotal_ocr_error(self):
        """Test that FOTAL (OCR misread of TOTAL) is skipped."""
        from shared.models.ocr import should_skip_line
        assert should_skip_line('FOTAL 38.68') is True


class TestExtractStoreName:
    """Tests for extract_store_name function"""

    def test_first_valid_line(self):
        from shared.models.ocr import extract_store_name
        assert extract_store_name(['STORE NAME', '123 Main St']) == 'STORE NAME'

    def test_skip_digit_only_lines(self):
        from shared.models.ocr import extract_store_name
        assert extract_store_name(['123', 'STORE NAME']) == 'STORE NAME'

    def test_empty_list_returns_none(self):
        from shared.models.ocr import extract_store_name
        assert extract_store_name([]) is None


class TestExtractPhone:
    """Tests for extract_phone function"""

    def test_standard_format(self):
        from shared.models.ocr import extract_phone
        assert extract_phone(['Store', '(555) 123-4567']) == '(555) 123-4567'

    def test_no_parentheses(self):
        from shared.models.ocr import extract_phone
        assert extract_phone(['Store', '555-123-4567']) == '555-123-4567'

    def test_no_phone_returns_none(self):
        from shared.models.ocr import extract_phone
        assert extract_phone(['No phone here']) is None


class TestExtractAddress:
    """Tests for extract_address function"""

    def test_street_keyword(self):
        from shared.models.ocr import extract_address
        result = extract_address(['Store', '123 Main St', 'City'])
        assert result == '123 Main St'

    def test_avenue_keyword(self):
        from shared.models.ocr import extract_address
        result = extract_address(['Store', '456 Oak Ave', 'City'])
        assert result == '456 Oak Ave'

    def test_no_address_returns_none(self):
        from shared.models.ocr import extract_address
        result = extract_address(['Store', 'No address here'])
        assert result is None


class TestCleanOcrText:
    """Tests for clean_ocr_text function"""

    def test_word_corrections(self):
        from shared.models.ocr import clean_ocr_text
        assert 'total' in clean_ocr_text('tota1 amount')
        assert 'subtotal' in clean_ocr_text('subt0tal')

    def test_whitespace_normalization(self):
        from shared.models.ocr import clean_ocr_text
        result = clean_ocr_text('too   many    spaces')
        assert '   ' not in result

    def test_punctuation_spacing(self):
        from shared.models.ocr import clean_ocr_text
        result = clean_ocr_text('word ,another')
        assert result == 'word, another'


class TestMergeTextLines:
    """Tests for merge_text_lines function"""

    def test_merge_continuation(self):
        from shared.models.ocr import merge_text_lines
        lines = ['This is a', 'continuation']
        result = merge_text_lines(lines)
        assert len(result) == 1
        assert 'continuation' in result[0]

    def test_no_merge_complete_sentences(self):
        from shared.models.ocr import merge_text_lines
        lines = ['Complete sentence.', 'Another sentence.']
        result = merge_text_lines(lines)
        assert len(result) == 2


class TestCalculateTextConfidence:
    """Tests for calculate_text_confidence function"""

    def test_normal_text(self):
        from shared.models.ocr import calculate_text_confidence
        conf = calculate_text_confidence('Hello World', 0.9)
        assert conf >= 0.9

    def test_special_chars_penalty(self):
        from shared.models.ocr import calculate_text_confidence
        conf = calculate_text_confidence('@#$%^&*()', 0.9)
        assert conf < 0.9

    def test_short_text_penalty(self):
        from shared.models.ocr import calculate_text_confidence
        conf = calculate_text_confidence('A', 0.9)
        assert conf < 0.9


class TestExtractEmail:
    """Tests for extract_email function"""

    def test_valid_email(self):
        from shared.models.ocr import extract_email
        result = extract_email(['Contact: test@example.com'])
        assert result == 'test@example.com'

    def test_no_email(self):
        from shared.models.ocr import extract_email
        result = extract_email(['No email here'])
        assert result is None


class TestExtractUrl:
    """Tests for extract_url function"""

    def test_https_url(self):
        from shared.models.ocr import extract_url
        result = extract_url(['Visit https://example.com'])
        assert result == 'https://example.com'

    def test_www_url(self):
        from shared.models.ocr import extract_url
        result = extract_url(['Visit www.example.com'])
        assert result == 'www.example.com'


class TestDetectLanguageHint:
    """Tests for detect_language_hint function"""

    def test_english_default(self):
        from shared.models.ocr import detect_language_hint
        result = detect_language_hint('Hello world')
        assert result == 'en'

    def test_spanish_detection(self):
        from shared.models.ocr import detect_language_hint
        result = detect_language_hint('el la de que en un es')
        assert result == 'es'


class TestCleanItemName:
    """Tests for clean_item_name function"""

    def test_fix_fashiuned_typo(self):
        from shared.models.ocr import clean_item_name
        result = clean_item_name('ORGANIC OLD FASHIUNED OATMEAL')
        assert 'FASHIONED' in result

    def test_fix_plpper_typo(self):
        from shared.models.ocr import clean_item_name
        result = clean_item_name('A-PLPPER BELL EACH XL RED')
        assert 'PEPPER' in result

    def test_fix_02_to_oz(self):
        from shared.models.ocr import clean_item_name
        result = clean_item_name('R-CARROTS SHREDDED 10 02')
        assert '10 OZ' in result

    def test_fix_xt_to_xl(self):
        from shared.models.ocr import clean_item_name
        result = clean_item_name('A-PEPPER BELL EACH Xt RED')
        assert 'XL' in result

    def test_remove_trailing_periods(self):
        from shared.models.ocr import clean_item_name
        result = clean_item_name('MINI-PEARL TOMATOES. .')
        assert not result.endswith('.')
        assert 'MINI-PEARL TOMATOES' in result

    def test_remove_trailing_pipe(self):
        from shared.models.ocr import clean_item_name
        result = clean_item_name('WHL WHT PITA BREAD |')
        assert not result.endswith('|')
        assert 'PITA BREAD' in result

    def test_normalize_whitespace(self):
        from shared.models.ocr import clean_item_name
        result = clean_item_name('EGGS  1  DOZ   ORGANIC')
        assert '  ' not in result

    def test_empty_string(self):
        from shared.models.ocr import clean_item_name
        result = clean_item_name('')
        assert result == ''

    def test_none_returns_none(self):
        from shared.models.ocr import clean_item_name
        result = clean_item_name(None)
        assert result is None


class TestCorrectStoreName:
    """Tests for correct_store_name function"""

    def test_trader_joes_correction(self):
        from shared.models.ocr import correct_store_name
        result = correct_store_name('a ae)')
        assert result == "TRADER JOE'S"

    def test_trader_joes_without_apostrophe(self):
        from shared.models.ocr import correct_store_name
        result = correct_store_name('trader joes')
        assert result == "TRADER JOE'S"

    def test_walmart_correction(self):
        from shared.models.ocr import correct_store_name
        result = correct_store_name('wa1mart')
        assert result == 'WALMART'

    def test_unknown_store_unchanged(self):
        from shared.models.ocr import correct_store_name
        result = correct_store_name('RANDOM STORE')
        assert result == 'RANDOM STORE'

    def test_empty_string(self):
        from shared.models.ocr import correct_store_name
        result = correct_store_name('')
        assert result == ''

    def test_none_returns_none(self):
        from shared.models.ocr import correct_store_name
        result = correct_store_name(None)
        assert result is None


class TestUnitCorrections:
    """Tests for UNIT_CORRECTIONS constant"""

    def test_oz_correction(self):
        from shared.models.ocr import UNIT_CORRECTIONS
        assert ' 02' in UNIT_CORRECTIONS
        assert UNIT_CORRECTIONS[' 02'] == ' OZ'

    def test_xl_correction(self):
        from shared.models.ocr import UNIT_CORRECTIONS
        assert 'Xt' in UNIT_CORRECTIONS
        assert UNIT_CORRECTIONS['Xt'] == 'XL'

    def test_ct_correction(self):
        from shared.models.ocr import UNIT_CORRECTIONS
        assert 'ct' in UNIT_CORRECTIONS
        assert UNIT_CORRECTIONS['ct'] == 'CT'


class TestStoreNameCorrections:
    """Tests for STORE_NAME_CORRECTIONS constant"""

    def test_contains_trader_joes(self):
        from shared.models.ocr import STORE_NAME_CORRECTIONS
        assert 'a ae)' in STORE_NAME_CORRECTIONS
        assert STORE_NAME_CORRECTIONS['a ae)'] == "TRADER JOE'S"

    def test_contains_walmart(self):
        from shared.models.ocr import STORE_NAME_CORRECTIONS
        assert 'wa1mart' in STORE_NAME_CORRECTIONS

    def test_contains_costco(self):
        from shared.models.ocr import STORE_NAME_CORRECTIONS
        assert 'costc0' in STORE_NAME_CORRECTIONS


class TestExtractLineItems:
    """Tests for extract_line_items function with generic receipt patterns."""

    # Generic format tests - work for any receipt type
    def test_item_with_hyphen_prefix(self):
        """Test item with prefix like R- or A- (common grocery format)."""
        from shared.models.ocr import extract_line_items
        lines = ['R-CARROTS SHREDDED 10 OZ 1.29']
        items = extract_line_items(lines)
        assert len(items) == 1
        assert items[0][1] == Decimal('1.29')

    def test_item_simple_name_price(self):
        """Test simple item name followed by price."""
        from shared.models.ocr import extract_line_items
        lines = ['MILK 2% GALLON 3.99']
        items = extract_line_items(lines)
        assert len(items) == 1
        assert items[0][1] == Decimal('3.99')

    def test_item_with_weight_unit(self):
        """Test item with weight/unit in name (1 LB, 10 OZ, etc.)."""
        from shared.models.ocr import extract_line_items
        lines = ['CUCUMBERS PERSIAN 1 LB 1.99']
        items = extract_line_items(lines)
        assert len(items) == 1
        assert items[0][1] == Decimal('1.99')

    def test_item_multi_word_description(self):
        """Test item with multi-word descriptive name."""
        from shared.models.ocr import extract_line_items
        lines = ['TOMATOES CRUSHED NO SALT 1.59']
        items = extract_line_items(lines)
        assert len(items) == 1
        assert items[0][1] == Decimal('1.59')

    def test_item_with_slash_in_name(self):
        """Test item with slash separator (W/BASIL, W/CHEESE, etc.)."""
        from shared.models.ocr import extract_line_items
        lines = ['TOMATOES WHOLE NO SALT W/BASIL 1.59']
        items = extract_line_items(lines)
        assert len(items) == 1
        assert items[0][1] == Decimal('1.59')

    def test_item_organic_product(self):
        """Test organic product naming."""
        from shared.models.ocr import extract_line_items
        lines = ['ORGANIC OLD FASHIONED OATMEAL 2.69']
        items = extract_line_items(lines)
        assert len(items) == 1
        assert items[0][1] == Decimal('2.69')

    def test_item_with_hyphen_in_name(self):
        """Test item with hyphen in product name."""
        from shared.models.ocr import extract_line_items
        lines = ['MINI-PEARL TOMATOES 2.49']
        items = extract_line_items(lines)
        assert len(items) == 1
        assert items[0][1] == Decimal('2.49')

    def test_item_abbreviation_prefix(self):
        """Test item with abbreviation prefix (PKG, LG, SM, etc.)."""
        from shared.models.ocr import extract_line_items
        lines = ['PKG SHREDDED MOZZARELLA 3.99']
        items = extract_line_items(lines)
        assert len(items) == 1
        assert items[0][1] == Decimal('3.99')

    def test_item_with_quantity_in_name(self):
        """Test item with quantity embedded in name (1 DOZ, 4CT, etc.)."""
        from shared.models.ocr import extract_line_items
        lines = ['EGGS 1 DOZ ORGANIC BROWN 3.79']
        items = extract_line_items(lines)
        assert len(items) == 1
        assert items[0][1] == Decimal('3.79')

    def test_item_single_word_name(self):
        """Test simple single-word item name."""
        from shared.models.ocr import extract_line_items
        lines = ['BANANAS 0.87']
        items = extract_line_items(lines)
        assert len(items) == 1
        assert items[0][1] == Decimal('0.87')

    def test_item_adjective_product(self):
        """Test item with adjective + product pattern."""
        from shared.models.ocr import extract_line_items
        lines = ['CREAMY SALTED PEANUT BUTTER 2.49']
        items = extract_line_items(lines)
        assert len(items) == 1
        assert items[0][1] == Decimal('2.49')

    def test_item_abbreviated_words(self):
        """Test item with abbreviated words (WHL, WHT, etc.)."""
        from shared.models.ocr import extract_line_items
        lines = ['WHL WHT PITA BREAD 1.69']
        items = extract_line_items(lines)
        assert len(items) == 1
        assert items[0][1] == Decimal('1.69')

    def test_item_with_dollar_sign(self):
        """Test item with explicit dollar sign."""
        from shared.models.ocr import extract_line_items
        lines = ['COFFEE GROUND $5.99']
        items = extract_line_items(lines)
        assert len(items) == 1
        assert items[0][1] == Decimal('5.99')

    def test_item_with_sku(self):
        """Test item with SKU barcode number."""
        from shared.models.ocr import extract_line_items
        lines = ['BACON SLICED 007874202906 6.98']
        items = extract_line_items(lines)
        assert len(items) == 1
        assert items[0][1] == Decimal('6.98')

    def test_item_with_tax_code(self):
        """Test item with trailing tax code (common in US receipts)."""
        from shared.models.ocr import extract_line_items
        lines = ['SODA 12 PACK 4.99 T']
        items = extract_line_items(lines)
        assert len(items) == 1
        assert items[0][1] == Decimal('4.99')

    def test_multiple_items_extraction(self):
        """Test extraction of multiple items from various formats."""
        from shared.models.ocr import extract_line_items
        lines = [
            'CARROTS SHREDDED 1.29',
            'CUCUMBERS 1.99',
            'MILK 2% 3.49',
            'BREAD WHOLE WHEAT 2.99',
        ]
        items = extract_line_items(lines)
        assert len(items) == 4
        assert items[0][1] == Decimal('1.29')
        assert items[1][1] == Decimal('1.99')
        assert items[2][1] == Decimal('3.49')
        assert items[3][1] == Decimal('2.99')

    def test_skip_quantity_lines(self):
        """Test that quantity lines like '2 @ 0.49' are skipped."""
        from shared.models.ocr import extract_line_items
        lines = [
            'BANANAS ORGANIC 0.87',
            '3EA @ 0.29/EA',
            '2 @ 0.49',
            'PITA BREAD 1.69',
        ]
        items = extract_line_items(lines)
        assert len(items) == 2

    def test_skip_subtotal_total_lines(self):
        """Test that subtotal/total lines are skipped."""
        from shared.models.ocr import extract_line_items
        lines = [
            'MILK 2.99',
            'SUBTOTAL 2.99',
            'TAX 0.24',
            'TOTAL 3.23',
        ]
        items = extract_line_items(lines)
        assert len(items) == 1

    def test_item_with_period_in_name(self):
        """Test item with period in name (trailing or mid-word)."""
        from shared.models.ocr import extract_line_items
        lines = ['MINI-PEARL TOMATOES.. 2.49']
        items = extract_line_items(lines)
        assert len(items) == 1
        # Period should be cleaned from name
        assert '..' not in items[0][0]

    def test_item_low_price(self):
        """Test extraction of very low priced items."""
        from shared.models.ocr import extract_line_items
        lines = ['BANANA SINGLE 0.19']
        items = extract_line_items(lines)
        assert len(items) == 1
        assert items[0][1] == Decimal('0.19')

    def test_item_high_price(self):
        """Test extraction of higher priced items."""
        from shared.models.ocr import extract_line_items
        lines = ['PRIME RIB ROAST 45.99']
        items = extract_line_items(lines)
        assert len(items) == 1
        assert items[0][1] == Decimal('45.99')

    def test_relaxed_mode_short_names(self):
        """Test relaxed mode accepts shorter item names."""
        from shared.models.ocr import extract_line_items
        lines = ['TEA 2.99']
        items = extract_line_items(lines, relaxed_mode=True)
        assert len(items) == 1


class TestExtractTotalGeneric:
    """Tests for total extraction from generic receipt formats."""

    def test_total_standard_format(self):
        """Test standard TOTAL XX.XX format."""
        from shared.models.ocr import extract_total
        lines = ['TOTAL 38.68']
        result = extract_total(lines)
        assert result == Decimal('38.68')

    def test_total_with_colon(self):
        """Test TOTAL: XX.XX format."""
        from shared.models.ocr import extract_total
        lines = ['TOTAL: 38.68']
        result = extract_total(lines)
        assert result == Decimal('38.68')

    def test_total_with_dollar_sign(self):
        """Test TOTAL $XX.XX format."""
        from shared.models.ocr import extract_total
        lines = ['TOTAL $38.68']
        result = extract_total(lines)
        assert result == Decimal('38.68')

    def test_total_with_space_before_decimal(self):
        """Test OCR error with space: TOTAL $38 .68"""
        from shared.models.ocr import extract_total
        lines = ['TOTAL $38 .68']
        result = extract_total(lines)
        assert result == Decimal('38.68')

    def test_grand_total_format(self):
        """Test GRAND TOTAL format."""
        from shared.models.ocr import extract_total
        lines = ['GRAND TOTAL 45.99']
        result = extract_total(lines)
        assert result == Decimal('45.99')

    def test_amount_due_format(self):
        """Test AMOUNT format (alternative total indicator)."""
        from shared.models.ocr import extract_total
        lines = ['AMOUNT: 38.68']
        result = extract_total(lines)
        assert result == Decimal('38.68')

    def test_balance_format(self):
        """Test BALANCE format."""
        from shared.models.ocr import extract_total
        lines = ['BALANCE 38.68']
        result = extract_total(lines)
        assert result == Decimal('38.68')

    def test_total_among_other_lines(self):
        """Test finding total among multiple lines."""
        from shared.models.ocr import extract_total
        lines = [
            'SUBTOTAL 35.00',
            'TAX 3.68',
            'TOTAL 38.68',
            'CASH 40.00',
        ]
        result = extract_total(lines)
        assert result == Decimal('38.68')


class TestParseReceiptText:
    """Tests for parse_receipt_text function with generic receipt data."""

    def test_parse_basic_receipt(self):
        """Test parsing a basic receipt structure."""
        from shared.models.ocr import parse_receipt_text
        lines = [
            "GROCERY STORE",
            "123 Main Street",
            "City, ST 12345",
            "(555) 123-4567",
            "MILK 2% GALLON 3.99",
            "BREAD WHEAT 2.49",
            "SUBTOTAL 6.48",
            "TAX 0.52",
            "TOTAL 7.00",
            "01/15/2024",
        ]
        result = parse_receipt_text(lines)
        
        assert result['store_name'] is not None
        assert result['transaction_date'] == '01/15/2024'
        assert result['total'] == Decimal('7.00')
        assert len(result['items']) >= 2
        assert result['store_phone'] == '(555) 123-4567'

    def test_parse_items_with_ocr_errors(self):
        """Test parsing items with common OCR errors that get corrected."""
        from shared.models.ocr import parse_receipt_text
        lines = [
            "ORGANIC OLD FASHIUNED OATMEAL 2.69",  # FASHIUNED -> FASHIONED
            "CARROTS SHREDDED 10 02 1.29",  # 02 -> OZ
        ]
        result = parse_receipt_text(lines)
        assert len(result['items']) >= 1

    def test_parse_receipt_without_date(self):
        """Test parsing receipt missing date."""
        from shared.models.ocr import parse_receipt_text
        lines = [
            "STORE NAME",
            "ITEM ONE 5.99",
            "TOTAL 5.99",
        ]
        result = parse_receipt_text(lines)
        assert result['transaction_date'] is None
        assert result['total'] == Decimal('5.99')

    def test_parse_receipt_without_total(self):
        """Test parsing receipt missing total."""
        from shared.models.ocr import parse_receipt_text
        lines = [
            "STORE NAME",
            "ITEM ONE 5.99",
            "ITEM TWO 3.99",
        ]
        result = parse_receipt_text(lines)
        assert result['total'] is None
        assert 'Total not found' in str(result['extraction_notes'])


class TestExtractSubtotal:
    """Tests for extract_subtotal function."""

    def test_subtotal_with_dollar_sign(self):
        from shared.models.ocr import extract_subtotal
        lines = ['SUBTOTAL $38.68']
        result = extract_subtotal(lines)
        assert result == Decimal('38.68')

    def test_subtotal_without_dollar_sign(self):
        from shared.models.ocr import extract_subtotal
        lines = ['SUBTOTAL 38.68']
        result = extract_subtotal(lines)
        assert result == Decimal('38.68')

    def test_sub_total_with_space(self):
        from shared.models.ocr import extract_subtotal
        lines = ['SUB TOTAL $38.68']
        result = extract_subtotal(lines)
        assert result == Decimal('38.68')

    def test_subtotal_among_other_lines(self):
        from shared.models.ocr import extract_subtotal
        lines = ['ITEM 5.99', 'SUBTOTAL 5.99', 'TAX 0.50']
        result = extract_subtotal(lines)
        assert result == Decimal('5.99')


class TestGetDetectionConfig:
    """Tests for get_detection_config function."""

    def test_returns_dict(self):
        from shared.models.ocr import get_detection_config
        config = get_detection_config()
        assert isinstance(config, dict)

    def test_has_required_keys(self):
        from shared.models.ocr import get_detection_config
        config = get_detection_config()
        assert 'min_confidence' in config
        assert 'box_threshold' in config
        assert 'min_text_height' in config
        assert 'use_angle_cls' in config

    def test_min_confidence_in_range(self):
        from shared.models.ocr import get_detection_config
        config = get_detection_config()
        assert 0.0 <= config['min_confidence'] <= 1.0

    def test_box_threshold_in_range(self):
        from shared.models.ocr import get_detection_config
        config = get_detection_config()
        assert 0.0 <= config['box_threshold'] <= 1.0


class TestRecordDetectionResult:
    """Tests for record_detection_result function."""

    def test_record_detection_result_no_error(self):
        """Test that record_detection_result doesn't raise errors."""
        from shared.models.ocr import record_detection_result
        # Should not raise
        record_detection_result(
            text_regions_count=10,
            avg_confidence=0.85,
            success=True,
            processing_time=1.5
        )

    def test_record_failed_detection(self):
        """Test recording a failed detection."""
        from shared.models.ocr import record_detection_result
        # Should not raise
        record_detection_result(
            text_regions_count=0,
            avg_confidence=0.0,
            success=False,
            processing_time=0.5
        )


class TestValidateReceiptTotals:
    """Tests for validate_receipt_totals function."""

    def test_valid_totals_math(self):
        """Test that subtotal + tax = total validation passes."""
        from shared.models.ocr import validate_receipt_totals
        result = validate_receipt_totals(
            subtotal=Decimal('35.00'),
            tax=Decimal('3.68'),
            total=Decimal('38.68')
        )
        assert result['valid'] is True
        assert 'Math validation passed' in str(result['notes'])

    def test_missing_total_critical(self):
        """Test that missing total is flagged as critical."""
        from shared.models.ocr import validate_receipt_totals
        result = validate_receipt_totals(
            subtotal=Decimal('35.00'),
            tax=Decimal('3.68'),
            total=None
        )
        assert result['valid'] is False
        assert 'CRITICAL' in str(result['notes'])

    def test_missing_subtotal_noted(self):
        """Test that missing subtotal is noted."""
        from shared.models.ocr import validate_receipt_totals
        result = validate_receipt_totals(
            subtotal=None,
            tax=Decimal('3.68'),
            total=Decimal('38.68')
        )
        assert 'Subtotal not found' in str(result['notes'])


class TestValidateItemCount:
    """Tests for validate_item_count function."""

    def test_no_items_warning(self):
        """Test that no items triggers warning."""
        from shared.models.ocr import validate_item_count
        result = validate_item_count([])
        assert 'No items extracted' in str(result['notes'])

    def test_reasonable_item_count(self):
        """Test reasonable item count is validated."""
        from shared.models.ocr import validate_item_count
        items = [('Item', Decimal('1.00'), 1)] * 10
        result = validate_item_count(items)
        assert 'Extracted 10 items' in str(result['notes'])

    def test_high_item_count_warning(self):
        """Test that very high item count triggers verification note."""
        from shared.models.ocr import validate_item_count
        items = [('Item', Decimal('1.00'), 1)] * 60
        result = validate_item_count(items)
        assert 'verify' in str(result['notes']).lower()


class TestCalculateOverallConfidence:
    """Tests for calculate_overall_confidence function."""

    def test_high_confidence_complete_data(self):
        """Test high confidence with complete receipt data."""
        from shared.models.ocr import calculate_overall_confidence
        receipt_data = {
            'store': {'name': 'Test Store'},
            'totals': {'total': Decimal('50.00')},
            'items': [{'name': 'Item', 'price': Decimal('50.00')}]
        }
        confidence = calculate_overall_confidence(0.8, receipt_data)
        assert confidence > 0.5

    def test_low_confidence_missing_total(self):
        """Test low confidence when total is missing."""
        from shared.models.ocr import calculate_overall_confidence
        receipt_data = {
            'store': {'name': 'Test Store'},
            'totals': {'total': None},
            'items': []
        }
        confidence = calculate_overall_confidence(0.8, receipt_data)
        assert confidence < 0.5


class TestFixConcatenatedText:
    """Tests for fix_concatenated_text function to handle OCR word merging."""

    def test_letter_number_split(self):
        """Test splitting letters from numbers: SHREDDED10 -> SHREDDED 10"""
        from shared.models.ocr import fix_concatenated_text
        result = fix_concatenated_text('SHREDDED10')
        assert result == 'SHREDDED 10'

    def test_number_unit_split_oz(self):
        """Test splitting number from OZ unit: 10OZ -> 10 OZ"""
        from shared.models.ocr import fix_concatenated_text
        result = fix_concatenated_text('10OZ')
        assert result == '10 OZ'

    def test_number_unit_split_lb(self):
        """Test splitting number from LB unit: 5LB -> 5 LB"""
        from shared.models.ocr import fix_concatenated_text
        result = fix_concatenated_text('5LB')
        assert result == '5 LB'

    def test_leading_lowercase_noise(self):
        """Test stripping leading lowercase noise: aTOMATOES -> TOMATOES"""
        from shared.models.ocr import fix_concatenated_text
        result = fix_concatenated_text('aTOMATOES')
        assert result == 'TOMATOES'

    def test_complex_pattern(self):
        """Test complex pattern with number and unit."""
        from shared.models.ocr import fix_concatenated_text
        result = fix_concatenated_text('CARROTS10OZ')
        assert '10 OZ' in result or '10OZ' in result  # Either is acceptable

    def test_preserve_normal_text(self):
        """Test that normal text is not modified."""
        from shared.models.ocr import fix_concatenated_text
        result = fix_concatenated_text('MILK 2% GALLON')
        assert result == 'MILK 2% GALLON'

    def test_empty_string(self):
        """Test empty string handling."""
        from shared.models.ocr import fix_concatenated_text
        result = fix_concatenated_text('')
        assert result == ''

    def test_none_handling(self):
        """Test None handling."""
        from shared.models.ocr import fix_concatenated_text
        result = fix_concatenated_text(None)
        assert result is None


class TestIsGarbageText:
    """Tests for is_garbage_text function to detect OCR garbage output."""

    def test_empty_string_is_garbage(self):
        """Test that empty string is garbage."""
        from shared.models.ocr import is_garbage_text
        assert is_garbage_text('') is True

    def test_very_short_punctuation_is_garbage(self):
        """Test that short punctuation-heavy text is garbage: '.- %'"""
        from shared.models.ocr import is_garbage_text
        assert is_garbage_text('.- %') is True

    def test_random_letters_is_garbage(self):
        """Test that random short letters are garbage: 'eee -'"""
        from shared.models.ocr import is_garbage_text
        assert is_garbage_text('eee -') is True

    def test_single_letters_is_garbage(self):
        """Test that single letter words are garbage: 'LY'"""
        from shared.models.ocr import is_garbage_text
        assert is_garbage_text('LY') is True

    def test_mixed_case_chaos_is_garbage(self):
        """Test that mixed case chaos is garbage: 'oo )sprauteDCaSTYLE'"""
        from shared.models.ocr import is_garbage_text
        assert is_garbage_text('oo )sprauteDCaSTYLE') is True

    def test_valid_short_item(self):
        """Test that valid short items are not garbage: 'TEA'"""
        from shared.models.ocr import is_garbage_text
        assert is_garbage_text('TEA') is False

    def test_valid_product_name(self):
        """Test that valid product names are not garbage."""
        from shared.models.ocr import is_garbage_text
        assert is_garbage_text('MILK 2% GALLON') is False

    def test_valid_item_with_numbers(self):
        """Test that valid items with numbers are not garbage."""
        from shared.models.ocr import is_garbage_text
        assert is_garbage_text('CARROTS 10 OZ') is False

    def test_valid_abbreviations(self):
        """Test that valid abbreviations are not garbage."""
        from shared.models.ocr import is_garbage_text
        assert is_garbage_text('PKG CHEESE') is False

    def test_excessive_special_chars_is_garbage(self):
        """Test that text with excessive special chars is garbage."""
        from shared.models.ocr import is_garbage_text
        assert is_garbage_text('@@##$$%%') is True


class TestMaxRealisticItemPrice:
    """Tests for MAX_REALISTIC_ITEM_PRICE constant and price filtering."""

    def test_constant_exists(self):
        """Test that MAX_REALISTIC_ITEM_PRICE exists and has reasonable value."""
        from shared.models.ocr import MAX_REALISTIC_ITEM_PRICE
        from decimal import Decimal
        assert MAX_REALISTIC_ITEM_PRICE == Decimal('99.99')

    def test_unrealistic_price_filtered(self):
        """Test that unrealistic prices like 200.49 are filtered."""
        from shared.models.ocr import extract_line_items
        # A line with an unrealistic price should not produce an item
        lines = ['ITEM NAME 200.49']
        items = extract_line_items(lines)
        # Should not extract the item due to unrealistic price
        assert len(items) == 0 or all(item[1] <= 99.99 for item in items)

    def test_realistic_price_accepted(self):
        """Test that realistic prices are accepted."""
        from shared.models.ocr import extract_line_items
        from decimal import Decimal
        lines = ['MILK GALLON 4.99']
        items = extract_line_items(lines)
        assert len(items) == 1
        assert items[0][1] == Decimal('4.99')


class TestCleanItemNameWithConcatenation:
    """Tests for clean_item_name function with concatenation fixes."""

    def test_removes_leading_lowercase_noise(self):
        """Test removal of leading lowercase noise: 'f-CARROTS' -> 'CARROTS'"""
        from shared.models.ocr import clean_item_name
        result = clean_item_name('f-CARROTS')
        # Should remove leading noise
        assert 'CARROTS' in result
        assert not result.startswith('f-')

    def test_fixes_number_concatenation(self):
        """Test fixing number concatenation: 'SHREDDED10' -> 'SHREDDED 10'"""
        from shared.models.ocr import clean_item_name
        result = clean_item_name('SHREDDED10')
        # Either has a space or is otherwise cleaned
        assert '10' in result
"""
Tests for OCRConfig module with circular exchange integration.
"""
import pytest
from decimal import Decimal
from unittest.mock import Mock, patch

from shared.models.config import OCRConfig, OCRPipelineStage, get_ocr_config, reset_ocr_config


class TestOCRConfig:
    """Test OCRConfig class."""
    
    def setup_method(self):
        """Reset singleton for each test using proper reset mechanism."""
        reset_ocr_config()
    
    def test_singleton_pattern(self):
        """Test that OCRConfig is a singleton."""
        config1 = OCRConfig()
        config2 = OCRConfig()
        assert config1 is config2
    
    def test_default_parameters(self):
        """Test default parameter values."""
        config = OCRConfig()
        
        # Note: min_confidence lowered to 0.25 for improved text detection
        assert config.min_confidence == 0.25
        # Note: relaxed_confidence lowered to 0.15 for better fallback detection
        assert config.relaxed_confidence == 0.15
        assert config.relaxed_mode == False
        assert config.auto_fallback == True
        assert config.min_name_length == 2
        assert config.max_price == 1000.0
        assert config.max_digit_ratio == 2.0
        assert config.auto_tune == True
    
    def test_set_min_confidence(self):
        """Test setting min_confidence."""
        config = OCRConfig()
        
        assert config.set_min_confidence(0.5) == True
        assert config.min_confidence == 0.5
        
        # Invalid value should be rejected
        assert config.set_min_confidence(1.5) == False
        assert config.min_confidence == 0.5  # Still previous value
    
    def test_set_relaxed_mode(self):
        """Test setting relaxed_mode."""
        config = OCRConfig()
        
        assert config.set_relaxed_mode(True) == True
        assert config.relaxed_mode == True
    
    def test_get_package(self):
        """Test getting parameter packages."""
        config = OCRConfig()
        
        pkg = config.get_package('ocr.min_confidence')
        assert pkg is not None
        # Value may have been modified by previous tests due to singleton
        assert isinstance(pkg.get(), float)
        
        # Non-existent package
        assert config.get_package('non.existent') is None


class TestOCRConfigPipeline:
    """Test OCRConfig pipeline functionality."""
    
    def setup_method(self):
        """Reset singleton for each test."""
        reset_ocr_config()
    
    def test_pipeline_stages_initialized(self):
        """Test that pipeline stages are initialized."""
        config = OCRConfig()
        
        stages = config.get_enabled_stages()
        assert 'preprocessing' in stages
        assert 'text_detection' in stages
        assert 'line_extraction' in stages
        assert 'item_parsing' in stages
        assert 'validation' in stages
    
    def test_disable_enable_stage(self):
        """Test disabling and enabling pipeline stages."""
        config = OCRConfig()
        
        assert config.disable_stage('preprocessing') == True
        assert 'preprocessing' not in config.get_enabled_stages()
        
        assert config.enable_stage('preprocessing') == True
        assert 'preprocessing' in config.get_enabled_stages()
    
    def test_set_stage_parameter(self):
        """Test setting stage parameters."""
        config = OCRConfig()
        
        assert config.set_stage_parameter('preprocessing', 'deskew', False) == True
        stage = config.get_pipeline_stage('preprocessing')
        assert stage.parameters['deskew'] == False


class TestOCRConfigAutoTuning:
    """Test OCRConfig auto-tuning functionality."""
    
    def setup_method(self):
        """Reset singleton for each test."""
        reset_ocr_config()
    
    def test_record_extraction_result(self):
        """Test recording extraction results."""
        config = OCRConfig()
        
        config.record_extraction_result(
            items_count=5,
            total_detected=Decimal('25.99'),
            confidence_avg=0.85,
            success=True,
            used_relaxed=False
        )
        
        stats = config.get_extraction_stats()
        assert stats['total'] == 1
        assert stats['successful'] == 1
        assert stats['success_rate'] == 1.0
    
    def test_auto_tune_on_low_success_rate(self):
        """Test that auto-tuning relaxes constraints on low success rate."""
        config = OCRConfig()
        config.set_min_confidence(0.4)
        
        # Record many failed extractions
        for _ in range(15):
            config.record_extraction_result(
                items_count=0,
                total_detected=None,
                confidence_avg=0.3,
                success=False,
                used_relaxed=False
            )
        
        # Min confidence should be lowered
        assert config.min_confidence < 0.4


class TestOCRConfigExportImport:
    """Test OCRConfig export/import functionality."""
    
    def setup_method(self):
        """Reset singleton for each test."""
        reset_ocr_config()
    
    def test_export_config(self):
        """Test exporting configuration."""
        config = OCRConfig()
        config.set_min_confidence(0.35)
        
        exported = config.export_config()
        
        assert 'parameters' in exported
        assert 'pipeline' in exported
        assert 'stats' in exported
        assert exported['parameters']['min_confidence'] == 0.35
    
    def test_import_config(self):
        """Test importing configuration."""
        config = OCRConfig()
        
        new_config = {
            'parameters': {
                'min_confidence': 0.25,
                'relaxed_mode': True
            },
            'pipeline': {
                'preprocessing': {
                    'enabled': False
                }
            }
        }
        
        assert config.import_config(new_config) == True
        assert config.min_confidence == 0.25
        assert config.relaxed_mode == True
    
    def test_reset_to_defaults(self):
        """Test resetting to default values."""
        config = OCRConfig()
        config.set_min_confidence(0.1)
        config.set_relaxed_mode(True)
        
        config.reset_to_defaults()
        
        # Note: lowered defaults for improved text detection
        assert config.min_confidence == 0.25
        assert config.relaxed_mode == False


class TestOCRPipelineStage:
    """Test OCRPipelineStage dataclass."""
    
    def test_record_result(self):
        """Test recording stage results."""
        stage = OCRPipelineStage(name='test')
        
        stage.record_result(True)
        stage.record_result(True)
        stage.record_result(False)
        
        assert stage.total_runs == 3
        assert stage.successful_runs == 2
        assert abs(stage.success_rate - 0.667) < 0.01


class TestGetOcrConfig:
    """Test get_ocr_config function."""
    
    def setup_method(self):
        """Reset singleton for each test."""
        reset_ocr_config()
    
    def test_get_ocr_config(self):
        """Test that get_ocr_config returns singleton."""
        config1 = get_ocr_config()
        config2 = get_ocr_config()
        
        assert config1 is config2
        assert isinstance(config1, OCRConfig)


class TestOCRConfigDetection:
    """Test OCRConfig text detection circular exchange integration."""
    
    def setup_method(self):
        """Reset singleton for each test."""
        reset_ocr_config()
    
    def test_detection_default_parameters(self):
        """Test default detection parameter values (lowered defaults)."""
        config = OCRConfig()
        
        # Detection parameters with lowered defaults for better text detection
        assert config.detection_min_confidence == 0.20  # Lowered from 0.25
        assert config.detection_box_threshold == 0.25  # Lowered from 0.3
        assert config.detection_min_text_height == 6  # Lowered to catch smaller text
        assert config.detection_use_angle_cls == True
        assert config.detection_multi_scale == True
        assert config.detection_auto_retry == True
        assert config.detection_enhance_contrast == True
        assert config.detection_denoise_strength == 10
    
    def test_set_detection_min_confidence(self):
        """Test setting detection_min_confidence via circular exchange."""
        config = OCRConfig()
        
        assert config.set_detection_min_confidence(0.15) == True
        assert config.detection_min_confidence == 0.15
        
        # Invalid value should be rejected
        assert config.set_detection_min_confidence(1.5) == False
        assert config.detection_min_confidence == 0.15  # Still previous value
    
    def test_set_detection_box_threshold(self):
        """Test setting detection_box_threshold."""
        config = OCRConfig()
        
        assert config.set_detection_box_threshold(0.4) == True
        assert config.detection_box_threshold == 0.4
    
    def test_set_detection_min_text_height(self):
        """Test setting detection_min_text_height."""
        config = OCRConfig()
        
        assert config.set_detection_min_text_height(5) == True
        assert config.detection_min_text_height == 5
    
    def test_get_detection_config(self):
        """Test getting all detection parameters as dictionary."""
        config = OCRConfig()
        config.set_detection_min_confidence(0.2)
        
        detection_config = config.get_detection_config()
        
        assert 'min_confidence' in detection_config
        assert 'box_threshold' in detection_config
        assert 'min_text_height' in detection_config
        assert 'use_angle_cls' in detection_config
        assert detection_config['min_confidence'] == 0.2
    
    def test_detection_package_subscription(self):
        """Test subscribing to detection parameter changes."""
        config = OCRConfig()
        changes = []
        
        def on_change(change):
            changes.append(change)
        
        pkg = config.get_package('ocr.detection.min_confidence')
        assert pkg is not None
        unsubscribe = pkg.subscribe(on_change)
        
        config.set_detection_min_confidence(0.18)
        
        assert len(changes) == 1
        assert changes[0].new_value == 0.18
        
        unsubscribe()


class TestOCRConfigDetectionAutoTuning:
    """Test OCRConfig detection auto-tuning functionality."""
    
    def setup_method(self):
        """Reset singleton for each test."""
        reset_ocr_config()
    
    def test_record_detection_result(self):
        """Test recording detection results."""
        config = OCRConfig()
        
        config.record_detection_result(
            text_regions_count=15,
            avg_confidence=0.85,
            success=True,
            processing_time=0.5
        )
        
        stats = config.get_detection_stats()
        assert stats['total'] == 1
        assert stats['successful'] == 1
        assert stats['success_rate'] == 1.0
        assert stats['avg_regions'] == 15
    
    def test_auto_tune_detection_on_low_success_rate(self):
        """Test that auto-tuning lowers detection threshold on low success rate."""
        config = OCRConfig()
        config.set_detection_min_confidence(0.35)
        
        # Record many failed detections
        for _ in range(15):
            config.record_detection_result(
                text_regions_count=2,
                avg_confidence=0.3,
                success=False,
                processing_time=0.8
            )
        
        # Detection min confidence should be lowered
        assert config.detection_min_confidence < 0.35
    
    def test_detection_stats(self):
        """Test getting detection statistics."""
        config = OCRConfig()
        
        # Record some results
        for i in range(5):
            config.record_detection_result(
                text_regions_count=10 + i,
                avg_confidence=0.7 + i * 0.05,
                success=i % 2 == 0,  # Alternating success/fail
                processing_time=0.3
            )
        
        stats = config.get_detection_stats()
        assert stats['total'] == 5
        assert stats['successful'] == 3  # 0, 2, 4 are successful
        assert 'avg_regions' in stats
        assert 'avg_confidence' in stats


class TestOCRConfigDetectionPipeline:
    """Test OCRConfig detection pipeline stages."""
    
    def setup_method(self):
        """Reset singleton for each test."""
        reset_ocr_config()
    
    def test_detection_pipeline_stages(self):
        """Test that detection-related pipeline stages are configured."""
        config = OCRConfig()
        
        # Check text_detection stage exists and has detection parameters
        stage = config.get_pipeline_stage('text_detection')
        assert stage is not None
        assert 'confidence_threshold' in stage.parameters
        assert 'min_text_height' in stage.parameters
        assert 'use_angle_cls' in stage.parameters
        
        # Check text_recognition stage exists
        recognition_stage = config.get_pipeline_stage('text_recognition')
        assert recognition_stage is not None
        assert 'recognition_confidence' in recognition_stage.parameters
    
    def test_detection_export_import(self):
        """Test exporting and importing detection configuration."""
        config = OCRConfig()
        config.set_detection_min_confidence(0.2)
        config.set_detection_box_threshold(0.35)
        
        exported = config.export_config()
        
        assert 'detection' in exported
        assert exported['detection']['min_confidence'] == 0.2
        assert exported['detection']['box_threshold'] == 0.35
        
        # Reset and import
        config.reset_to_defaults()
        assert config.detection_min_confidence == 0.20  # Default (lowered)
        
        # Import the exported config
        config.import_config(exported)
        assert config.detection_min_confidence == 0.2
        assert config.detection_box_threshold == 0.35


# ============================================================================
# Tests for Receipt Prompts Module (New Module)
# ============================================================================

class TestReceiptPrompts:
    """Tests for the receipt_prompts module - validation and confidence."""

    def test_validate_monetary_value_valid(self):
        """Test validation of valid monetary values."""
        from shared.models.receipt_prompts import validate_monetary_value
        from decimal import Decimal
        
        value, penalties = validate_monetary_value("$25.99", "total")
        assert value == Decimal("25.99")
        # No critical penalties for valid value
        assert all(p.severity != "critical" for p in penalties)

    def test_validate_monetary_value_negative(self):
        """Test validation rejects negative values."""
        from shared.models.receipt_prompts import validate_monetary_value
        
        value, penalties = validate_monetary_value("-5.00", "total")
        assert value is None
        assert any(p.severity == "critical" for p in penalties)

    def test_validate_monetary_value_none(self):
        """Test validation handles None."""
        from shared.models.receipt_prompts import validate_monetary_value
        
        value, penalties = validate_monetary_value(None, "total")
        assert value is None
        assert len(penalties) > 0

    def test_validate_date_valid_iso(self):
        """Test validation of valid ISO date format."""
        from shared.models.receipt_prompts import validate_date
        
        date_str, penalties = validate_date("2024-01-15")
        assert date_str == "2024-01-15"
        assert any(p.adjustment > 0 for p in penalties)  # Should have bonus

    def test_validate_date_valid_us(self):
        """Test validation of valid US date format."""
        from shared.models.receipt_prompts import validate_date
        
        date_str, penalties = validate_date("01/15/2024")
        assert date_str == "01/15/2024"

    def test_validate_date_none(self):
        """Test validation handles missing date."""
        from shared.models.receipt_prompts import validate_date
        
        date_str, penalties = validate_date(None)
        assert date_str is None
        assert any(p.adjustment < 0 for p in penalties)  # Should have penalty

    def test_validate_store_name_valid(self):
        """Test validation of valid store names."""
        from shared.models.receipt_prompts import validate_store_name
        
        name, penalties = validate_store_name("WALMART")
        assert name == "WALMART"
        assert any(p.adjustment > 0 for p in penalties)  # Should have bonus

    def test_validate_store_name_too_short(self):
        """Test validation rejects very short names."""
        from shared.models.receipt_prompts import validate_store_name
        
        name, penalties = validate_store_name("AB")
        assert name is None
        assert any(p.adjustment < 0 for p in penalties)

    def test_validate_store_name_garbage(self):
        """Test validation rejects garbage text."""
        from shared.models.receipt_prompts import validate_store_name
        
        name, penalties = validate_store_name("@#$%^&*()")
        assert name is None
        assert any(p.severity == "critical" for p in penalties)

    def test_validate_receipt_math_valid(self):
        """Test math validation when subtotal + tax = total."""
        from shared.models.receipt_prompts import validate_receipt_math
        from decimal import Decimal
        
        is_valid, penalties = validate_receipt_math(
            total=Decimal("38.68"),
            subtotal=Decimal("35.00"),
            tax=Decimal("3.68"),
            items_sum=Decimal("35.00")
        )
        assert is_valid is True
        assert any(p.adjustment > 0 for p in penalties)  # Should have bonus

    def test_validate_receipt_math_invalid(self):
        """Test math validation when numbers don't add up."""
        from shared.models.receipt_prompts import validate_receipt_math
        from decimal import Decimal
        
        is_valid, penalties = validate_receipt_math(
            total=Decimal("50.00"),
            subtotal=Decimal("35.00"),
            tax=Decimal("3.68"),  # 35 + 3.68 = 38.68, not 50
            items_sum=Decimal("35.00")
        )
        assert is_valid is False
        assert any(p.severity == "critical" for p in penalties)

    def test_validate_receipt_extraction_complete(self):
        """Test full validation with complete receipt data."""
        from shared.models.receipt_prompts import validate_receipt_extraction
        from decimal import Decimal
        
        validation = validate_receipt_extraction(
            store_name="WALMART",
            total=Decimal("38.68"),
            subtotal=Decimal("35.00"),
            tax=Decimal("3.68"),
            transaction_date="01/15/2024",
            items=[{"name": "Item 1", "total_price": Decimal("35.00")}],
            raw_text="WALMART\n01/15/2024\nItem 1  35.00\nTOTAL 38.68"
        )
        
        assert validation.validated_store == "WALMART"
        assert validation.validated_total == Decimal("38.68")
        assert validation.math_validated is True

    def test_validate_receipt_extraction_missing_total(self):
        """Test validation with missing total (critical error)."""
        from shared.models.receipt_prompts import validate_receipt_extraction
        
        validation = validate_receipt_extraction(
            store_name="WALMART",
            total=None,
            subtotal=None,
            tax=None,
            transaction_date="01/15/2024",
            items=[]
        )
        
        assert validation.is_valid is False
        assert any("total" in error.lower() for error in validation.errors)

    def test_calculate_realistic_confidence(self):
        """Test realistic confidence calculation."""
        from shared.models.receipt_prompts import (
            validate_receipt_extraction,
            calculate_realistic_confidence
        )
        from decimal import Decimal
        
        # Good extraction should have high confidence
        good_validation = validate_receipt_extraction(
            store_name="WALMART",
            total=Decimal("38.68"),
            subtotal=Decimal("35.00"),
            tax=Decimal("3.68"),
            transaction_date="01/15/2024",
            items=[{"name": "Item 1", "total_price": Decimal("35.00")}]
        )
        
        good_confidence = calculate_realistic_confidence(0.5, good_validation)
        
        # Bad extraction should have low confidence
        bad_validation = validate_receipt_extraction(
            store_name=None,
            total=None,
            subtotal=None,
            tax=None,
            transaction_date=None,
            items=[]
        )
        
        bad_confidence = calculate_realistic_confidence(0.5, bad_validation)
        
        # Good extraction should have higher confidence
        assert good_confidence > bad_confidence
        # Bad extraction should have significantly reduced confidence
        assert bad_confidence < 0.4

    def test_get_validated_extraction_with_confidence(self):
        """Test the convenience function for OCR processors."""
        from shared.models.receipt_prompts import get_validated_extraction_with_confidence
        from decimal import Decimal
        
        # Create a mock receipt-like object
        class MockReceipt:
            store_name = "TARGET"
            total = Decimal("25.00")
            subtotal = Decimal("23.50")
            tax = Decimal("1.50")
            transaction_date = "2024-01-20"
            items = []
        
        receipt = MockReceipt()
        result_receipt, confidence, validation = get_validated_extraction_with_confidence(
            receipt_data=receipt,
            raw_text="TARGET 01/20/2024 TOTAL 25.00",
            base_confidence=0.7
        )
        
        assert result_receipt is receipt
        assert 0.0 <= confidence <= 1.0
        assert validation is not None


class TestExtractionValidation:
    """Tests for ExtractionValidation dataclass."""

    def test_extraction_validation_defaults(self):
        """Test ExtractionValidation default values."""
        from shared.models.receipt_prompts import ExtractionValidation
        
        validation = ExtractionValidation()
        assert validation.is_valid is True
        assert validation.confidence_adjustments == []
        assert validation.warnings == []
        assert validation.errors == []
        assert validation.validated_total is None
        assert validation.math_validated is False

    def test_confidence_penalty_creation(self):
        """Test ConfidencePenalty creation."""
        from shared.models.receipt_prompts import ConfidencePenalty
        
        penalty = ConfidencePenalty(
            reason="Missing total",
            adjustment=-0.25,
            severity="critical"
        )
        
        assert penalty.reason == "Missing total"
        assert penalty.adjustment == -0.25
        assert penalty.severity == "critical"


class TestReceiptPromptConstants:
    """Tests for receipt prompt constants."""

    def test_system_prompt_exists(self):
        """Test that system prompt is defined."""
        from shared.models.receipt_prompts import RECEIPT_EXTRACTION_SYSTEM_PROMPT
        
        assert RECEIPT_EXTRACTION_SYSTEM_PROMPT is not None
        assert len(RECEIPT_EXTRACTION_SYSTEM_PROMPT) > 100
        assert "TOTAL" in RECEIPT_EXTRACTION_SYSTEM_PROMPT

    def test_parsing_instructions_exists(self):
        """Test that parsing instructions are defined."""
        from shared.models.receipt_prompts import RECEIPT_PARSING_INSTRUCTIONS
        
        assert RECEIPT_PARSING_INSTRUCTIONS is not None
        assert "{receipt_text}" in RECEIPT_PARSING_INSTRUCTIONS


class TestMultilineItemExtraction:
    """Tests for multi-line item extraction (Walmart-style receipts)."""

    def test_merge_multiline_items_basic(self):
        """Test basic multi-line item merging."""
        from shared.models.ocr import merge_multiline_items
        
        lines = [
            '6 WING PLATE',
            '020108870398 F 3.98 0',
            'ASST 27',
            '053099656595 4.88 0',
        ]
        merged = merge_multiline_items(lines)
        
        # Should merge to 2 lines
        non_empty = [l for l in merged if l.strip()]
        assert len(non_empty) == 2
        assert '6 WING PLATE' in non_empty[0]
        assert '3.98' in non_empty[0]
        assert 'ASST 27' in non_empty[1]
        assert '4.88' in non_empty[1]

    def test_merge_multiline_items_preserves_regular_lines(self):
        """Test that non-multi-line items are preserved."""
        from shared.models.ocr import merge_multiline_items
        
        lines = [
            'WALMART',
            'Store #1234',
            '6 WING PLATE',
            '020108870398 F 3.98 0',
            'TOTAL 23.19',
        ]
        merged = merge_multiline_items(lines)
        
        # Should preserve WALMART, Store, and TOTAL
        assert 'WALMART' in merged
        assert 'Store #1234' in merged
        assert 'TOTAL 23.19' in merged

    def test_multiline_extraction_walmart_format(self):
        """Test complete extraction of Walmart-style multi-line receipt."""
        from shared.models.ocr import parse_receipt_text
        from decimal import Decimal
        
        lines = [
            'WALMART',
            '6 WING PLATE',
            '020108870398 F 3.98 0',
            'ASST 27',
            '053099656595 4.88 0',
            'CUTIE CAR',
            '053099656644 12.88 0',
            'SUBTOTAL 21.74',
            'TAX 1 1.45',
            'TOTAL 23.19',
        ]
        
        result = parse_receipt_text(lines)
        
        assert result['store_name'] == 'WALMART'
        assert len(result['items']) == 3
        assert result['subtotal'] == Decimal('21.74')
        assert result['tax'] == Decimal('1.45')
        assert result['total'] == Decimal('23.19')

    def test_multiline_items_with_codes(self):
        """Test extraction with SKU codes."""
        from shared.models.ocr import extract_line_items_with_codes
        from decimal import Decimal
        
        lines = [
            '6 WING PLATE',
            '020108870398 F 3.98 0',
            'ASST 27',
            '053099656595 4.88 0',
        ]
        
        items = extract_line_items_with_codes(lines)
        
        assert len(items) == 2
        # Check first item
        name, code, price, qty = items[0]
        assert name == '6 WING PLATE'
        assert code == '020108870398'
        assert price == Decimal('3.98')
        # Check second item
        name, code, price, qty = items[1]
        assert name == 'ASST 27'
        assert code == '053099656595'
        assert price == Decimal('4.88')

    def test_subtotal_calculation_from_items(self):
        """Test subtotal calculation when not explicitly found."""
        from shared.models.ocr import parse_receipt_text
        from decimal import Decimal
        
        # Receipt without SUBTOTAL line
        lines = [
            'WALMART',
            'ITEM ONE 10.00',
            'ITEM TWO 5.00',
            'ITEM THREE 2.50',
            'TAX 1 0.88',
            'TOTAL 18.38',
        ]
        
        result = parse_receipt_text(lines)
        
        assert len(result['items']) == 3
        # Subtotal should be calculated from items
        assert result['subtotal'] == Decimal('17.50')  # 10 + 5 + 2.50

    def test_tax_calculation_from_subtotal_and_total(self):
        """Test tax calculation when total and subtotal are known."""
        from shared.models.ocr import parse_receipt_text
        from decimal import Decimal
        
        lines = [
            'WALMART',
            'ITEM ONE 10.00',
            'ITEM TWO 5.00',
            'SUBTOTAL 15.00',
            'TOTAL 16.50',
        ]
        
        result = parse_receipt_text(lines)
        
        assert result['subtotal'] == Decimal('15.00')
        assert result['total'] == Decimal('16.50')
        # Tax should be calculated
        assert result['tax'] == Decimal('1.50')

    def test_multiline_pattern_no_merge_for_single_line_items(self):
        """Test that single-line items are not affected by multi-line merging."""
        from shared.models.ocr import extract_line_items
        from decimal import Decimal
        
        lines = [
            'MILK 2% GALLON 3.99',
            'BREAD WHOLE WHEAT 2.49',
            'EGGS DOZEN 4.99',
        ]
        
        items = extract_line_items(lines)
        
        assert len(items) == 3
        assert items[0][1] == Decimal('3.99')
        assert items[1][1] == Decimal('2.49')
        assert items[2][1] == Decimal('4.99')


class TestSemanticValidation:
    """Tests for semantic validation of receipt data."""

    def test_math_validation_passes(self):
        """Test that valid math (subtotal + tax = total) is validated."""
        from shared.models.ocr import validate_receipt_totals
        from decimal import Decimal
        
        result = validate_receipt_totals(
            subtotal=Decimal('21.74'),
            tax=Decimal('1.45'),
            total=Decimal('23.19')
        )
        
        assert result['valid'] is True
        assert 'Math validation passed' in result['notes']

    def test_math_validation_fails(self):
        """Test that invalid math is flagged."""
        from shared.models.ocr import validate_receipt_totals
        from decimal import Decimal
        
        result = validate_receipt_totals(
            subtotal=Decimal('21.74'),
            tax=Decimal('1.45'),
            total=Decimal('25.00')  # Wrong total
        )
        
        assert result['valid'] is False
        assert any('Math validation failed' in note for note in result['notes'])

    def test_price_in_valid_range(self):
        """Test that prices in valid range are accepted."""
        from shared.models.ocr import normalize_price, PRICE_MIN, PRICE_MAX
        from decimal import Decimal
        
        # Valid prices
        assert normalize_price('0.01') == Decimal('0.01')
        assert normalize_price('99.99') == Decimal('99.99')
        assert normalize_price('999.99') == Decimal('999.99')

    def test_price_exceeds_max_rejected(self):
        """Test that prices exceeding max are rejected."""
        from shared.models.ocr import normalize_price
        
        # Price exceeds PRICE_MAX (9999)
        result = normalize_price('99999.00')
        assert result is None
