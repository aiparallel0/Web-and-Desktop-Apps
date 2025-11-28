import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from shared.models.easyocr_processor import EasyOCRProcessor


@pytest.fixture
def easyocr_config():
    """Configuration for EasyOCR processor"""
    return {
        'id': 'easyocr',
        'name': 'EasyOCR',
        'type': 'easyocr',
        'description': 'EasyOCR based extraction'
    }


@pytest.fixture
def mock_easyocr_reader():
    """Mock EasyOCR Reader"""
    reader = Mock()
    reader.readtext = Mock()
    return reader


@pytest.mark.unit
@patch('shared.models.easyocr_processor.easyocr')
def test_easyocr_processor_initialization_success(mock_easyocr, easyocr_config):
    """Test successful initialization of EasyOCR processor"""
    mock_reader = Mock()
    mock_easyocr.Reader.return_value = mock_reader

    processor = EasyOCRProcessor(easyocr_config)

    assert processor.model_config == easyocr_config
    assert processor.model_name == 'EasyOCR'
    assert processor.reader == mock_reader
    mock_easyocr.Reader.assert_called_once_with(['en'], gpu=False)


@pytest.mark.unit
@patch('shared.models.easyocr_processor.easyocr', None)
def test_easyocr_processor_initialization_no_module(easyocr_config):
    """Test initialization fails when easyocr is not installed"""
    with pytest.raises(ImportError) as exc_info:
        processor = EasyOCRProcessor(easyocr_config)

    assert "EasyOCR not installed" in str(exc_info.value)


@pytest.mark.unit
@patch('shared.models.easyocr_processor.easyocr')
def test_easyocr_processor_initialization_failure(mock_easyocr, easyocr_config):
    """Test initialization fails when Reader creation fails"""
    mock_easyocr.Reader.side_effect = RuntimeError("Reader creation failed")

    with pytest.raises(RuntimeError) as exc_info:
        processor = EasyOCRProcessor(easyocr_config)

    assert "EasyOCR init failed" in str(exc_info.value)


@pytest.mark.unit
@patch('shared.models.easyocr_processor.easyocr')
def test_extract_success(mock_easyocr, easyocr_config):
    """Test successful extraction with EasyOCR"""
    mock_reader = Mock()
    mock_easyocr.Reader.return_value = mock_reader

    # Mock OCR results
    mock_reader.readtext.return_value = [
        ([[0, 0], [100, 0], [100, 50], [0, 50]], 'Test Store', 0.95),
        ([[0, 60], [100, 60], [100, 90], [0, 90]], '123 Main St', 0.92),
        ([[0, 100], [100, 100], [100, 130], [0, 130]], '01/15/2024', 0.90),
        ([[0, 140], [100, 140], [100, 170], [0, 170]], 'Apple 2.99', 0.88),
        ([[0, 180], [100, 180], [100, 210], [0, 210]], 'Banana 1.49', 0.87),
        ([[0, 220], [100, 220], [100, 250], [0, 250]], 'Total: $4.48', 0.93),
    ]

    processor = EasyOCRProcessor(easyocr_config)
    result = processor.extract('/path/to/test/image.jpg')

    assert result.success is True
    assert result.data is not None
    assert result.data.store_name == 'Test Store'
    assert result.data.transaction_date == '01/15/2024'
    assert result.data.total == Decimal('4.48')
    assert result.data.model_used == 'EasyOCR'
    assert result.data.processing_time is not None
    mock_reader.readtext.assert_called_once()


@pytest.mark.unit
@patch('shared.models.easyocr_processor.easyocr')
def test_extract_no_text_detected(mock_easyocr, easyocr_config):
    """Test extraction when no text is detected"""
    mock_reader = Mock()
    mock_easyocr.Reader.return_value = mock_reader
    mock_reader.readtext.return_value = []

    processor = EasyOCRProcessor(easyocr_config)
    result = processor.extract('/path/to/test/image.jpg')

    assert result.success is False
    assert "No text detected" in result.error


@pytest.mark.unit
@patch('shared.models.easyocr_processor.easyocr')
def test_extract_low_confidence_filtered(mock_easyocr, easyocr_config):
    """Test that low confidence detections are filtered out"""
    mock_reader = Mock()
    mock_easyocr.Reader.return_value = mock_reader

    # Mix of high and low confidence results
    mock_reader.readtext.return_value = [
        ([[0, 0], [100, 0], [100, 50], [0, 50]], 'Good Text', 0.95),
        ([[0, 60], [100, 60], [100, 90], [0, 90]], 'Bad Text', 0.2),  # Low confidence
        ([[0, 100], [100, 100], [100, 130], [0, 130]], 'Total: $10.00', 0.85),
    ]

    processor = EasyOCRProcessor(easyocr_config)
    result = processor.extract('/path/to/test/image.jpg')

    assert result.success is True
    # Should have filtered out the low confidence text
    # Store name should be 'Good Text', not 'Bad Text'
    assert result.data.store_name == 'Good Text'


@pytest.mark.unit
@patch('shared.models.easyocr_processor.easyocr', None)
def test_extract_no_easyocr_module(easyocr_config):
    """Test extraction when easyocr module is not available"""
    # Can't create processor without easyocr, so test the extract logic directly
    # This tests the runtime check in extract()
    import sys
    from shared.models import easyocr_processor

    # Temporarily set easyocr to None
    original_easyocr = easyocr_processor.easyocr
    easyocr_processor.easyocr = None

    try:
        # Create processor will fail, so we can't test this path directly
        # The initialization already checks for easyocr
        pass
    finally:
        easyocr_processor.easyocr = original_easyocr


@pytest.mark.unit
@patch('shared.models.easyocr_processor.easyocr')
def test_extract_reader_not_initialized(mock_easyocr, easyocr_config):
    """Test extraction when reader is not initialized"""
    mock_easyocr.Reader.return_value = None

    processor = EasyOCRProcessor(easyocr_config)
    processor.reader = None  # Simulate reader not initialized

    result = processor.extract('/path/to/test/image.jpg')

    assert result.success is False
    assert "reader init failed" in result.error


@pytest.mark.unit
@patch('shared.models.easyocr_processor.easyocr')
def test_extract_exception_handling(mock_easyocr, easyocr_config):
    """Test extraction handles exceptions gracefully"""
    mock_reader = Mock()
    mock_easyocr.Reader.return_value = mock_reader
    mock_reader.readtext.side_effect = RuntimeError("OCR failed")

    processor = EasyOCRProcessor(easyocr_config)
    result = processor.extract('/path/to/test/image.jpg')

    assert result.success is False
    assert "OCR failed" in result.error


@pytest.mark.unit
@patch('shared.models.easyocr_processor.easyocr')
def test_parse_receipt_store_name_detection(mock_easyocr, easyocr_config):
    """Test store name detection logic"""
    mock_reader = Mock()
    mock_easyocr.Reader.return_value = mock_reader

    mock_reader.readtext.return_value = [
        ([[0, 0], [100, 0], [100, 50], [0, 50]], '12345', 0.95),  # Should skip numeric
        ([[0, 60], [100, 60], [100, 90], [0, 90]], 'Walmart', 0.92),  # Should use this
        ([[0, 100], [100, 100], [100, 130], [0, 130]], 'Total: $10.00', 0.90),
    ]

    processor = EasyOCRProcessor(easyocr_config)
    result = processor.extract('/path/to/test/image.jpg')

    assert result.success is True
    assert result.data.store_name == 'Walmart'


@pytest.mark.unit
@patch('shared.models.easyocr_processor.easyocr')
def test_parse_receipt_date_patterns(mock_easyocr, easyocr_config):
    """Test various date pattern detection"""
    mock_reader = Mock()
    mock_easyocr.Reader.return_value = mock_reader

    test_cases = [
        '01/15/2024',
        '1-15-24',
        '12-31-2024',
    ]

    for date_str in test_cases:
        mock_reader.readtext.return_value = [
            ([[0, 0], [100, 0], [100, 50], [0, 50]], 'Store', 0.95),
            ([[0, 60], [100, 60], [100, 90], [0, 90]], date_str, 0.92),
            ([[0, 100], [100, 100], [100, 130], [0, 130]], 'Total: $10.00', 0.90),
        ]

        processor = EasyOCRProcessor(easyocr_config)
        result = processor.extract('/path/to/test/image.jpg')

        assert result.success is True
        assert result.data.transaction_date is not None


@pytest.mark.unit
@patch('shared.models.easyocr_processor.easyocr')
def test_parse_receipt_total_patterns(mock_easyocr, easyocr_config):
    """Test various total amount pattern detection"""
    mock_reader = Mock()
    mock_easyocr.Reader.return_value = mock_reader

    test_cases = [
        ('Total: $12.99', Decimal('12.99')),
        ('Amount: 25.50', Decimal('25.50')),
        ('Balance: $100.00', Decimal('100.00')),
        ('Grand Total: $47.23', Decimal('47.23')),
    ]

    for total_str, expected_value in test_cases:
        mock_reader.readtext.return_value = [
            ([[0, 0], [100, 0], [100, 50], [0, 50]], 'Store', 0.95),
            ([[0, 60], [100, 60], [100, 90], [0, 90]], total_str, 0.92),
        ]

        processor = EasyOCRProcessor(easyocr_config)
        result = processor.extract('/path/to/test/image.jpg')

        assert result.success is True
        assert result.data.total == expected_value


@pytest.mark.unit
@patch('shared.models.easyocr_processor.easyocr')
def test_extract_line_items(mock_easyocr, easyocr_config):
    """Test line item extraction"""
    mock_reader = Mock()
    mock_easyocr.Reader.return_value = mock_reader

    mock_reader.readtext.return_value = [
        ([[0, 0], [100, 0], [100, 50], [0, 50]], 'Store Name', 0.95),
        ([[0, 60], [100, 60], [100, 90], [0, 90]], 'Apple 2.99', 0.92),
        ([[0, 100], [100, 100], [100, 130], [0, 130]], 'Banana 1.49', 0.90),
        ([[0, 140], [100, 140], [100, 170], [0, 170]], 'Orange $3.25', 0.88),
        ([[0, 180], [100, 180], [100, 210], [0, 210]], 'Total: $7.73', 0.93),
    ]

    processor = EasyOCRProcessor(easyocr_config)
    result = processor.extract('/path/to/test/image.jpg')

    assert result.success is True
    assert len(result.data.items) >= 2  # Should extract at least some items

    # Check that items have required fields
    for item in result.data.items:
        assert item.name is not None
        assert item.total_price is not None
        assert item.total_price > 0


@pytest.mark.unit
@patch('shared.models.easyocr_processor.easyocr')
def test_extract_skip_keywords(mock_easyocr, easyocr_config):
    """Test that lines with skip keywords are not extracted as items"""
    mock_reader = Mock()
    mock_easyocr.Reader.return_value = mock_reader

    mock_reader.readtext.return_value = [
        ([[0, 0], [100, 0], [100, 50], [0, 50]], 'Store Name', 0.95),
        ([[0, 60], [100, 60], [100, 90], [0, 90]], 'Apple 2.99', 0.92),
        ([[0, 100], [100, 100], [100, 130], [0, 130]], 'Subtotal 2.99', 0.90),  # Should skip
        ([[0, 140], [100, 140], [100, 170], [0, 170]], 'Tax 0.24', 0.88),  # Should skip
        ([[0, 180], [100, 180], [100, 210], [0, 210]], 'Total: $3.23', 0.93),
    ]

    processor = EasyOCRProcessor(easyocr_config)
    result = processor.extract('/path/to/test/image.jpg')

    assert result.success is True
    # Should not include 'Subtotal' or 'Tax' as items
    item_names = [item.name.lower() for item in result.data.items]
    assert 'subtotal' not in ' '.join(item_names)
    assert 'tax' not in ' '.join(item_names)


@pytest.mark.unit
@patch('shared.models.easyocr_processor.easyocr')
def test_extract_address_detection(mock_easyocr, easyocr_config):
    """Test address detection"""
    mock_reader = Mock()
    mock_easyocr.Reader.return_value = mock_reader

    mock_reader.readtext.return_value = [
        ([[0, 0], [100, 0], [100, 50], [0, 50]], 'Store Name', 0.95),
        ([[0, 60], [100, 60], [100, 90], [0, 90]], '123 Main Street', 0.92),
        ([[0, 100], [100, 100], [100, 130], [0, 130]], 'Total: $10.00', 0.90),
    ]

    processor = EasyOCRProcessor(easyocr_config)
    result = processor.extract('/path/to/test/image.jpg')

    assert result.success is True
    assert result.data.store_address == '123 Main Street'


@pytest.mark.unit
@patch('shared.models.easyocr_processor.easyocr')
def test_extract_phone_detection(mock_easyocr, easyocr_config):
    """Test phone number detection"""
    mock_reader = Mock()
    mock_easyocr.Reader.return_value = mock_reader

    test_cases = [
        '(555) 123-4567',
        '555-123-4567',
        '555.123.4567',
    ]

    for phone in test_cases:
        mock_reader.readtext.return_value = [
            ([[0, 0], [100, 0], [100, 50], [0, 50]], 'Store Name', 0.95),
            ([[0, 60], [100, 60], [100, 90], [0, 90]], phone, 0.92),
            ([[0, 100], [100, 100], [100, 130], [0, 130]], 'Total: $10.00', 0.90),
        ]

        processor = EasyOCRProcessor(easyocr_config)
        result = processor.extract('/path/to/test/image.jpg')

        assert result.success is True
        assert result.data.store_phone is not None


@pytest.mark.unit
def test_normalize_price_valid():
    """Test price normalization with valid values"""
    assert EasyOCRProcessor._normalize_price('12.99') == Decimal('12.99')
    assert EasyOCRProcessor._normalize_price('$5.50') == Decimal('5.50')
    assert EasyOCRProcessor._normalize_price('100') == Decimal('100')
    assert EasyOCRProcessor._normalize_price('0.99') == Decimal('0.99')


@pytest.mark.unit
def test_normalize_price_invalid():
    """Test price normalization with invalid values"""
    assert EasyOCRProcessor._normalize_price(None) is None
    assert EasyOCRProcessor._normalize_price('') is None
    assert EasyOCRProcessor._normalize_price('-5.00') is None
    assert EasyOCRProcessor._normalize_price('abc') is None
    assert EasyOCRProcessor._normalize_price('10000') is None  # Out of range


@pytest.mark.unit
@patch('shared.models.easyocr_processor.easyocr')
def test_extract_empty_text_lines(mock_easyocr, easyocr_config):
    """Test parsing with empty text lines after filtering"""
    mock_reader = Mock()
    mock_easyocr.Reader.return_value = mock_reader

    # All low confidence results
    mock_reader.readtext.return_value = [
        ([[0, 0], [100, 0], [100, 50], [0, 50]], 'Text', 0.1),
        ([[0, 60], [100, 60], [100, 90], [0, 90]], 'More', 0.2),
    ]

    processor = EasyOCRProcessor(easyocr_config)
    result = processor.extract('/path/to/test/image.jpg')

    assert result.success is False
    assert "No text detected" in result.error


@pytest.mark.unit
@patch('shared.models.easyocr_processor.easyocr')
def test_duplicate_items_filtered(mock_easyocr, easyocr_config):
    """Test that duplicate items are not added twice"""
    mock_reader = Mock()
    mock_easyocr.Reader.return_value = mock_reader

    mock_reader.readtext.return_value = [
        ([[0, 0], [100, 0], [100, 50], [0, 50]], 'Store Name', 0.95),
        ([[0, 60], [100, 60], [100, 90], [0, 90]], 'Apple 2.99', 0.92),
        ([[0, 100], [100, 100], [100, 130], [0, 130]], 'Apple 2.99', 0.90),  # Duplicate
        ([[0, 140], [100, 140], [100, 170], [0, 170]], 'Total: $5.98', 0.93),
    ]

    processor = EasyOCRProcessor(easyocr_config)
    result = processor.extract('/path/to/test/image.jpg')

    assert result.success is True
    # Should only have one 'Apple' item
    apple_items = [item for item in result.data.items if 'Apple' in item.name]
    assert len(apple_items) <= 1
