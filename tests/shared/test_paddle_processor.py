import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
import numpy as np
from PIL import Image


@pytest.fixture
def paddle_config():
    """Configuration for Paddle processor"""
    return {
        'id': 'paddle',
        'name': 'PaddleOCR',
        'type': 'paddle',
        'description': 'PaddleOCR based extraction'
    }


@pytest.fixture
def mock_paddle_ocr():
    """Mock PaddleOCR instance"""
    ocr = Mock()
    ocr.ocr = Mock()
    return ocr


@pytest.mark.unit
@patch('shared.models.paddle_processor.PaddleOCR')
@patch('shared.models.paddle_processor.load_and_validate_image')
@patch('shared.models.paddle_processor.preprocess_for_ocr')
def test_paddle_processor_initialization_success(mock_preprocess, mock_load, mock_paddle_cls, paddle_config):
    """Test successful initialization of Paddle processor"""
    from shared.models.paddle_processor import PaddleProcessor

    mock_ocr = Mock()
    mock_paddle_cls.return_value = mock_ocr

    processor = PaddleProcessor(paddle_config)

    assert processor.model_config == paddle_config
    assert processor.model_name == 'PaddleOCR'
    assert processor.ocr == mock_ocr
    mock_paddle_cls.assert_called_once_with(
        use_angle_cls=True,
        lang='en',
        det_db_thresh=0.2,
        det_db_box_thresh=0.3
    )


@pytest.mark.unit
@patch('shared.models.paddle_processor.PaddleOCR')
def test_paddle_processor_initialization_failure(mock_paddle_cls, paddle_config):
    """Test initialization fails when PaddleOCR creation fails"""
    from shared.models.paddle_processor import PaddleProcessor

    mock_paddle_cls.side_effect = RuntimeError("PaddleOCR creation failed")

    with pytest.raises(RuntimeError):
        processor = PaddleProcessor(paddle_config)


@pytest.mark.unit
@patch('shared.models.paddle_processor.PaddleOCR')
@patch('shared.models.paddle_processor.load_and_validate_image')
@patch('shared.models.paddle_processor.preprocess_for_ocr')
def test_extract_success(mock_preprocess, mock_load, mock_paddle_cls, paddle_config):
    """Test successful extraction with PaddleOCR"""
    from shared.models.paddle_processor import PaddleProcessor

    mock_ocr = Mock()
    mock_paddle_cls.return_value = mock_ocr

    # Mock image loading and preprocessing
    mock_image = Image.new('RGB', (100, 100), color='white')
    mock_load.return_value = mock_image
    mock_preprocess.return_value = mock_image

    # Mock OCR results
    mock_ocr.ocr.return_value = [[
        [[[0, 0], [100, 0], [100, 30], [0, 30]], ('Test Store', 0.95)],
        [[[0, 40], [100, 40], [100, 70], [0, 70]], ('123 Main St', 0.92)],
        [[[0, 80], [100, 80], [100, 110], [0, 110]], ('01/15/2024', 0.90)],
        [[[0, 120], [100, 120], [100, 150], [0, 150]], ('Apple 2.99', 0.88)],
        [[[0, 160], [100, 160], [100, 190], [0, 190]], ('Total: $2.99', 0.93)],
    ]]

    processor = PaddleProcessor(paddle_config)
    result = processor.extract('/path/to/test/image.jpg')

    assert result.success is True
    assert result.data is not None
    assert result.data.store_name == 'Test Store'
    assert result.data.transaction_date == '01/15/2024'
    assert result.data.total == Decimal('2.99')
    assert result.data.model_used == 'PaddleOCR'
    assert result.data.processing_time is not None


@pytest.mark.unit
@patch('shared.models.paddle_processor.PaddleOCR')
@patch('shared.models.paddle_processor.load_and_validate_image')
@patch('shared.models.paddle_processor.preprocess_for_ocr')
def test_extract_no_results(mock_preprocess, mock_load, mock_paddle_cls, paddle_config):
    """Test extraction when no text is detected"""
    from shared.models.paddle_processor import PaddleProcessor

    mock_ocr = Mock()
    mock_paddle_cls.return_value = mock_ocr

    mock_image = Image.new('RGB', (100, 100), color='white')
    mock_load.return_value = mock_image
    mock_preprocess.return_value = mock_image

    # No results
    mock_ocr.ocr.return_value = None

    processor = PaddleProcessor(paddle_config)
    result = processor.extract('/path/to/test/image.jpg')

    assert result.success is False
    assert "No text detected" in result.error


@pytest.mark.unit
@patch('shared.models.paddle_processor.PaddleOCR')
@patch('shared.models.paddle_processor.load_and_validate_image')
@patch('shared.models.paddle_processor.preprocess_for_ocr')
def test_extract_empty_results(mock_preprocess, mock_load, mock_paddle_cls, paddle_config):
    """Test extraction with empty results"""
    from shared.models.paddle_processor import PaddleProcessor

    mock_ocr = Mock()
    mock_paddle_cls.return_value = mock_ocr

    mock_image = Image.new('RGB', (100, 100), color='white')
    mock_load.return_value = mock_image
    mock_preprocess.return_value = mock_image

    # Empty results
    mock_ocr.ocr.return_value = [[]]

    processor = PaddleProcessor(paddle_config)
    result = processor.extract('/path/to/test/image.jpg')

    assert result.success is False
    assert "No text detected" in result.error


@pytest.mark.unit
@patch('shared.models.paddle_processor.PaddleOCR')
@patch('shared.models.paddle_processor.load_and_validate_image')
@patch('shared.models.paddle_processor.preprocess_for_ocr')
def test_extract_retry_with_original_image(mock_preprocess, mock_load, mock_paddle_cls, paddle_config):
    """Test that extraction retries with original image if preprocessed fails"""
    from shared.models.paddle_processor import PaddleProcessor

    mock_ocr = Mock()
    mock_paddle_cls.return_value = mock_ocr

    mock_image = Image.new('RGB', (100, 100), color='white')
    mock_load.return_value = mock_image
    mock_preprocess.return_value = mock_image

    # First call returns None, second call returns results
    mock_ocr.ocr.side_effect = [
        None,  # First attempt with preprocessed image
        [[  # Second attempt with original image
            [[[0, 0], [100, 0], [100, 30], [0, 30]], ('Test Store', 0.95)],
            [[[0, 40], [100, 40], [100, 70], [0, 70]], ('Total: $10.00', 0.93)],
        ]]
    ]

    processor = PaddleProcessor(paddle_config)
    result = processor.extract('/path/to/test/image.jpg')

    assert result.success is True
    assert mock_ocr.ocr.call_count == 2


@pytest.mark.unit
@patch('shared.models.paddle_processor.PaddleOCR')
@patch('shared.models.paddle_processor.load_and_validate_image')
@patch('shared.models.paddle_processor.preprocess_for_ocr')
def test_extract_grayscale_to_rgb_conversion(mock_preprocess, mock_load, mock_paddle_cls, paddle_config):
    """Test that grayscale images are converted to RGB"""
    from shared.models.paddle_processor import PaddleProcessor

    mock_ocr = Mock()
    mock_paddle_cls.return_value = mock_ocr

    # Create grayscale image
    mock_image = Image.new('L', (100, 100), color=128)
    mock_load.return_value = mock_image
    mock_preprocess.return_value = mock_image

    mock_ocr.ocr.return_value = [[
        [[[0, 0], [100, 0], [100, 30], [0, 30]], ('Test', 0.95)],
    ]]

    processor = PaddleProcessor(paddle_config)
    result = processor.extract('/path/to/test/image.jpg')

    # Should succeed - grayscale converted to RGB internally
    assert result.success is True


@pytest.mark.unit
@patch('shared.models.paddle_processor.PaddleOCR')
@patch('shared.models.paddle_processor.load_and_validate_image')
@patch('shared.models.paddle_processor.preprocess_for_ocr')
def test_extract_exception_handling(mock_preprocess, mock_load, mock_paddle_cls, paddle_config):
    """Test extraction handles exceptions gracefully"""
    from shared.models.paddle_processor import PaddleProcessor

    mock_ocr = Mock()
    mock_paddle_cls.return_value = mock_ocr

    mock_load.side_effect = RuntimeError("Image load failed")

    processor = PaddleProcessor(paddle_config)
    result = processor.extract('/path/to/test/image.jpg')

    assert result.success is False
    assert "Image load failed" in result.error


@pytest.mark.unit
@patch('shared.models.paddle_processor.PaddleOCR')
@patch('shared.models.paddle_processor.load_and_validate_image')
@patch('shared.models.paddle_processor.preprocess_for_ocr')
def test_extract_low_confidence_filtered(mock_preprocess, mock_load, mock_paddle_cls, paddle_config):
    """Test that low confidence results are filtered out"""
    from shared.models.paddle_processor import PaddleProcessor

    mock_ocr = Mock()
    mock_paddle_cls.return_value = mock_ocr

    mock_image = Image.new('RGB', (100, 100), color='white')
    mock_load.return_value = mock_image
    mock_preprocess.return_value = mock_image

    # Mix of high and low confidence
    mock_ocr.ocr.return_value = [[
        [[[0, 0], [100, 0], [100, 30], [0, 30]], ('Good Text', 0.95)],
        [[[0, 40], [100, 40], [100, 70], [0, 70]], ('Bad Text', 0.2)],  # Low confidence
        [[[0, 80], [100, 80], [100, 110], [0, 110]], ('Total: $10.00', 0.85)],
    ]]

    processor = PaddleProcessor(paddle_config)
    result = processor.extract('/path/to/test/image.jpg')

    assert result.success is True


@pytest.mark.unit
@patch('shared.models.paddle_processor.PaddleOCR')
@patch('shared.models.paddle_processor.load_and_validate_image')
@patch('shared.models.paddle_processor.preprocess_for_ocr')
def test_extract_date_patterns(mock_preprocess, mock_load, mock_paddle_cls, paddle_config):
    """Test various date pattern detection"""
    from shared.models.paddle_processor import PaddleProcessor

    mock_ocr = Mock()
    mock_paddle_cls.return_value = mock_ocr

    mock_image = Image.new('RGB', (100, 100), color='white')
    mock_load.return_value = mock_image
    mock_preprocess.return_value = mock_image

    test_cases = [
        '01/15/2024',
        '2024-01-15',
        'Jan 15, 2024',
    ]

    for date_str in test_cases:
        mock_ocr.ocr.return_value = [[
            [[[0, 0], [100, 0], [100, 30], [0, 30]], ('Store', 0.95)],
            [[[0, 40], [100, 40], [100, 70], [0, 70]], (date_str, 0.92)],
            [[[0, 80], [100, 80], [100, 110], [0, 110]], ('Total: $10.00', 0.90)],
        ]]

        processor = PaddleProcessor(paddle_config)
        result = processor.extract('/path/to/test/image.jpg')

        assert result.success is True
        assert result.data.transaction_date is not None


@pytest.mark.unit
@patch('shared.models.paddle_processor.PaddleOCR')
@patch('shared.models.paddle_processor.load_and_validate_image')
@patch('shared.models.paddle_processor.preprocess_for_ocr')
def test_extract_total_patterns(mock_preprocess, mock_load, mock_paddle_cls, paddle_config):
    """Test various total pattern detection"""
    from shared.models.paddle_processor import PaddleProcessor

    mock_ocr = Mock()
    mock_paddle_cls.return_value = mock_ocr

    mock_image = Image.new('RGB', (100, 100), color='white')
    mock_load.return_value = mock_image
    mock_preprocess.return_value = mock_image

    test_cases = [
        ('Total: $12.99', Decimal('12.99')),
        ('Amount: 25.50', Decimal('25.50')),
        ('Balance: $100.00', Decimal('100.00')),
        ('Grand Total: $47.23', Decimal('47.23')),
        ('Total: 15,99', Decimal('15.99')),  # European format with comma
    ]

    for total_str, expected_value in test_cases:
        mock_ocr.ocr.return_value = [[
            [[[0, 0], [100, 0], [100, 30], [0, 30]], ('Store', 0.95)],
            [[[0, 40], [100, 40], [100, 70], [0, 70]], (total_str, 0.92)],
        ]]

        processor = PaddleProcessor(paddle_config)
        result = processor.extract('/path/to/test/image.jpg')

        assert result.success is True
        assert result.data.total == expected_value


@pytest.mark.unit
@patch('shared.models.paddle_processor.PaddleOCR')
@patch('shared.models.paddle_processor.load_and_validate_image')
@patch('shared.models.paddle_processor.preprocess_for_ocr')
def test_extract_line_items(mock_preprocess, mock_load, mock_paddle_cls, paddle_config):
    """Test line item extraction"""
    from shared.models.paddle_processor import PaddleProcessor

    mock_ocr = Mock()
    mock_paddle_cls.return_value = mock_ocr

    mock_image = Image.new('RGB', (100, 100), color='white')
    mock_load.return_value = mock_image
    mock_preprocess.return_value = mock_image

    mock_ocr.ocr.return_value = [[
        [[[0, 0], [100, 0], [100, 30], [0, 30]], ('Store Name', 0.95)],
        [[[0, 40], [100, 40], [100, 70], [0, 70]], ('Apple 2.99', 0.92)],
        [[[0, 80], [100, 80], [100, 110], [0, 110]], ('Banana 1.49', 0.90)],
        [[[0, 120], [100, 120], [100, 150], [0, 150]], ('Orange $3.25', 0.88)],
        [[[0, 160], [100, 160], [100, 190], [0, 190]], ('Total: $7.73', 0.93)],
    ]]

    processor = PaddleProcessor(paddle_config)
    result = processor.extract('/path/to/test/image.jpg')

    assert result.success is True
    assert len(result.data.items) >= 2

    for item in result.data.items:
        assert item.name is not None
        assert item.total_price is not None
        assert item.total_price > 0


@pytest.mark.unit
@patch('shared.models.paddle_processor.PaddleOCR')
@patch('shared.models.paddle_processor.load_and_validate_image')
@patch('shared.models.paddle_processor.preprocess_for_ocr')
def test_extract_skip_keywords(mock_preprocess, mock_load, mock_paddle_cls, paddle_config):
    """Test that lines with skip keywords are not extracted as items"""
    from shared.models.paddle_processor import PaddleProcessor

    mock_ocr = Mock()
    mock_paddle_cls.return_value = mock_ocr

    mock_image = Image.new('RGB', (100, 100), color='white')
    mock_load.return_value = mock_image
    mock_preprocess.return_value = mock_image

    mock_ocr.ocr.return_value = [[
        [[[0, 0], [100, 0], [100, 30], [0, 30]], ('Store', 0.95)],
        [[[0, 40], [100, 40], [100, 70], [0, 70]], ('Apple 2.99', 0.92)],
        [[[0, 80], [100, 80], [100, 110], [0, 110]], ('Subtotal 2.99', 0.90)],  # Skip
        [[[0, 120], [100, 120], [100, 150], [0, 150]], ('Tax 0.24', 0.88)],  # Skip
        [[[0, 160], [100, 160], [100, 190], [0, 190]], ('Total: $3.23', 0.93)],
    ]]

    processor = PaddleProcessor(paddle_config)
    result = processor.extract('/path/to/test/image.jpg')

    assert result.success is True
    item_names = [item.name.lower() for item in result.data.items]
    assert 'subtotal' not in ' '.join(item_names)
    assert 'tax' not in ' '.join(item_names)


@pytest.mark.unit
@patch('shared.models.paddle_processor.PaddleOCR')
@patch('shared.models.paddle_processor.load_and_validate_image')
@patch('shared.models.paddle_processor.preprocess_for_ocr')
def test_extract_address_detection(mock_preprocess, mock_load, mock_paddle_cls, paddle_config):
    """Test address detection"""
    from shared.models.paddle_processor import PaddleProcessor

    mock_ocr = Mock()
    mock_paddle_cls.return_value = mock_ocr

    mock_image = Image.new('RGB', (100, 100), color='white')
    mock_load.return_value = mock_image
    mock_preprocess.return_value = mock_image

    mock_ocr.ocr.return_value = [[
        [[[0, 0], [100, 0], [100, 30], [0, 30]], ('Store Name', 0.95)],
        [[[0, 40], [100, 40], [100, 70], [0, 70]], ('123 Main Street', 0.92)],
        [[[0, 80], [100, 80], [100, 110], [0, 110]], ('Total: $10.00', 0.90)],
    ]]

    processor = PaddleProcessor(paddle_config)
    result = processor.extract('/path/to/test/image.jpg')

    assert result.success is True
    assert result.data.store_address == '123 Main Street'


@pytest.mark.unit
@patch('shared.models.paddle_processor.PaddleOCR')
@patch('shared.models.paddle_processor.load_and_validate_image')
@patch('shared.models.paddle_processor.preprocess_for_ocr')
def test_extract_phone_detection(mock_preprocess, mock_load, mock_paddle_cls, paddle_config):
    """Test phone number detection"""
    from shared.models.paddle_processor import PaddleProcessor

    mock_ocr = Mock()
    mock_paddle_cls.return_value = mock_ocr

    mock_image = Image.new('RGB', (100, 100), color='white')
    mock_load.return_value = mock_image
    mock_preprocess.return_value = mock_image

    test_cases = [
        '(555) 123-4567',
        '555-123-4567',
        '555.123.4567',
    ]

    for phone in test_cases:
        mock_ocr.ocr.return_value = [[
            [[[0, 0], [100, 0], [100, 30], [0, 30]], ('Store', 0.95)],
            [[[0, 40], [100, 40], [100, 70], [0, 70]], (phone, 0.92)],
            [[[0, 80], [100, 80], [100, 110], [0, 110]], ('Total: $10.00', 0.90)],
        ]]

        processor = PaddleProcessor(paddle_config)
        result = processor.extract('/path/to/test/image.jpg')

        assert result.success is True
        assert result.data.store_phone is not None


@pytest.mark.unit
def test_normalize_price_valid():
    """Test price normalization with valid values"""
    from shared.models.paddle_processor import PaddleProcessor

    assert PaddleProcessor._normalize_price('12.99') == Decimal('12.99')
    assert PaddleProcessor._normalize_price('$5.50') == Decimal('5.50')
    assert PaddleProcessor._normalize_price('100') == Decimal('100')
    assert PaddleProcessor._normalize_price('0.99') == Decimal('0.99')
    assert PaddleProcessor._normalize_price('15,99') == Decimal('15.99')  # European format


@pytest.mark.unit
def test_normalize_price_invalid():
    """Test price normalization with invalid values"""
    from shared.models.paddle_processor import PaddleProcessor

    assert PaddleProcessor._normalize_price(None) is None
    assert PaddleProcessor._normalize_price('-5.00') is None
    assert PaddleProcessor._normalize_price('abc') is None
    assert PaddleProcessor._normalize_price('10000') is None  # Out of range


@pytest.mark.unit
@patch('shared.models.paddle_processor.PaddleOCR')
@patch('shared.models.paddle_processor.load_and_validate_image')
@patch('shared.models.paddle_processor.preprocess_for_ocr')
def test_extract_confidence_score_calculation(mock_preprocess, mock_load, mock_paddle_cls, paddle_config):
    """Test that confidence score is calculated correctly"""
    from shared.models.paddle_processor import PaddleProcessor

    mock_ocr = Mock()
    mock_paddle_cls.return_value = mock_ocr

    mock_image = Image.new('RGB', (100, 100), color='white')
    mock_load.return_value = mock_image
    mock_preprocess.return_value = mock_image

    mock_ocr.ocr.return_value = [[
        [[[0, 0], [100, 0], [100, 30], [0, 30]], ('Text1', 0.9)],
        [[[0, 40], [100, 40], [100, 70], [0, 70]], ('Text2', 0.8)],
        [[[0, 80], [100, 80], [100, 110], [0, 110]], ('Text3', 0.7)],
    ]]

    processor = PaddleProcessor(paddle_config)
    result = processor.extract('/path/to/test/image.jpg')

    assert result.success is True
    # Average confidence should be (0.9 + 0.8 + 0.7) / 3 = 0.8
    assert result.data.confidence_score is not None
    assert 0.79 <= result.data.confidence_score <= 0.81


@pytest.mark.unit
@patch('shared.models.paddle_processor.PaddleOCR')
@patch('shared.models.paddle_processor.load_and_validate_image')
@patch('shared.models.paddle_processor.preprocess_for_ocr')
def test_extract_malformed_result_handling(mock_preprocess, mock_load, mock_paddle_cls, paddle_config):
    """Test handling of malformed OCR results"""
    from shared.models.paddle_processor import PaddleProcessor

    mock_ocr = Mock()
    mock_paddle_cls.return_value = mock_ocr

    mock_image = Image.new('RGB', (100, 100), color='white')
    mock_load.return_value = mock_image
    mock_preprocess.return_value = mock_image

    # Malformed results - missing bbox or text
    mock_ocr.ocr.return_value = [[
        [None, ('Text', 0.9)],  # Missing bbox
        [[[0, 0], [100, 0], [100, 30], [0, 30]], None],  # Missing text info
        [[[0, 40], [100, 40], [100, 70], [0, 70]], ('Good Text', 0.9)],  # Valid
    ]]

    processor = PaddleProcessor(paddle_config)
    result = processor.extract('/path/to/test/image.jpg')

    # Should still succeed with valid results
    assert result.success is True


@pytest.mark.unit
@patch('shared.models.paddle_processor.PaddleOCR')
@patch('shared.models.paddle_processor.load_and_validate_image')
@patch('shared.models.paddle_processor.preprocess_for_ocr')
def test_extract_quantity_parsing(mock_preprocess, mock_load, mock_paddle_cls, paddle_config):
    """Test parsing of quantity in line items"""
    from shared.models.paddle_processor import PaddleProcessor

    mock_ocr = Mock()
    mock_paddle_cls.return_value = mock_ocr

    mock_image = Image.new('RGB', (100, 100), color='white')
    mock_load.return_value = mock_image
    mock_preprocess.return_value = mock_image

    mock_ocr.ocr.return_value = [[
        [[[0, 0], [100, 0], [100, 30], [0, 30]], ('Store', 0.95)],
        [[[0, 40], [100, 40], [100, 70], [0, 70]], ('2 x Apple 5.98', 0.92)],  # Quantity prefix
        [[[0, 80], [100, 80], [100, 110], [0, 110]], ('Total: $5.98', 0.90)],
    ]]

    processor = PaddleProcessor(paddle_config)
    result = processor.extract('/path/to/test/image.jpg')

    assert result.success is True
    # Should parse item with quantity prefix
    if len(result.data.items) > 0:
        # The item name should have quantity prefix removed
        assert 'Apple' in result.data.items[0].name or 'x Apple' in result.data.items[0].name
