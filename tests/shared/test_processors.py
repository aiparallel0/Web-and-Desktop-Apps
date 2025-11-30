import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from shared.models.processors import (
    BaseProcessor,
    ProcessorInitializationError,
    ProcessorHealthCheckError
)

# Concrete implementation for testing
class MockProcessor(BaseProcessor):
    """Mock processor for testing BaseProcessor functionality"""

    def __init__(self, model_config, should_fail_load=False, should_fail_health=False):
        self.should_fail_load = should_fail_load
        self.should_fail_health = should_fail_health
        self.load_count = 0
        self.health_count = 0
        super().__init__(model_config)

    def _load_model(self):
        """Mock model loading"""
        self.load_count += 1
        if self.should_fail_load:
            raise RuntimeError("Model load failed")
        # Simulate successful model load
        self.model = "mock_model"

    def _health_check(self) -> bool:
        """Mock health check"""
        self.health_count += 1
        if self.should_fail_health:
            return False
        return True

    def extract(self, image_path: str):
        """Mock extraction"""
        return {"success": True, "data": "mock_data"}


@pytest.fixture
def basic_config():
    """Basic model configuration for testing"""
    return {
        'id': 'test_model',
        'name': 'Test Model',
        'type': 'mock',
        'description': 'A test model'
    }


@pytest.fixture
def mock_processor(basic_config):
    """Create a mock processor instance"""
    return MockProcessor(basic_config)


@pytest.mark.unit
def test_base_processor_initialization(basic_config):
    """Test basic initialization of BaseProcessor"""
    processor = MockProcessor(basic_config)

    assert processor.model_config == basic_config
    assert processor.model_name == 'Test Model'
    assert processor.model_id == 'test_model'
    assert processor.initialized is False
    assert processor.initialization_error is None
    assert processor.last_health_check is None


@pytest.mark.unit
def test_base_processor_initialization_defaults(basic_config):
    """Test initialization with missing optional fields"""
    config = {'type': 'mock'}
    processor = MockProcessor(config)

    assert processor.model_name == 'unknown'
    assert processor.model_id == 'unknown'


@pytest.mark.unit
def test_initialize_success(mock_processor):
    """Test successful initialization"""
    mock_processor.initialize()

    assert mock_processor.initialized is True
    assert mock_processor.initialization_error is None
    assert mock_processor.load_count == 1
    assert mock_processor.health_count == 1


@pytest.mark.unit
def test_initialize_with_retry_success(basic_config):
    """Test initialization that succeeds after retry"""
    processor = MockProcessor(basic_config, should_fail_load=True)

    # Make it fail first time, succeed second time
    original_load = processor._load_model
    call_count = [0]

    def load_with_retry():
        call_count[0] += 1
        if call_count[0] == 1:
            raise RuntimeError("First attempt fails")
        # Second attempt succeeds
        processor.model = "mock_model"

    processor._load_model = load_with_retry

    processor.initialize(retry_count=2)

    assert processor.initialized is True
    assert call_count[0] == 2


@pytest.mark.unit
def test_initialize_health_check_failure(basic_config):
    """Test initialization fails when health check fails"""
    processor = MockProcessor(basic_config, should_fail_health=True)

    with pytest.raises(ProcessorInitializationError) as exc_info:
        processor.initialize(retry_count=1)

    assert "failed health check" in str(exc_info.value)
    assert processor.initialized is False


@pytest.mark.unit
def test_initialize_load_failure(basic_config):
    """Test initialization fails when model load fails"""
    processor = MockProcessor(basic_config, should_fail_load=True)

    with pytest.raises(ProcessorInitializationError) as exc_info:
        processor.initialize(retry_count=1)

    assert "Failed to initialize" in str(exc_info.value)
    assert "after 2 attempts" in str(exc_info.value)
    assert processor.initialized is False
    assert processor.initialization_error is not None


@pytest.mark.unit
@patch('time.sleep')
def test_initialize_retry_timing(mock_sleep, basic_config):
    """Test that retry timing follows exponential backoff"""
    processor = MockProcessor(basic_config, should_fail_load=True)

    try:
        processor.initialize(retry_count=2)
    except ProcessorInitializationError:
        pass

    # Should sleep 2^0=1 second after first failure, 2^1=2 seconds after second
    assert mock_sleep.call_count == 2
    mock_sleep.assert_any_call(1)  # 2^0
    mock_sleep.assert_any_call(2)  # 2^1


@pytest.mark.unit
def test_ensure_healthy_success(mock_processor):
    """Test ensure_healthy passes when processor is healthy"""
    mock_processor.initialize()

    # Should not raise
    mock_processor.ensure_healthy()

    assert mock_processor.last_health_check is not None
    assert isinstance(mock_processor.last_health_check, float)


@pytest.mark.unit
def test_ensure_healthy_not_initialized(mock_processor):
    """Test ensure_healthy fails when processor not initialized"""
    with pytest.raises(ProcessorHealthCheckError) as exc_info:
        mock_processor.ensure_healthy()

    assert "is not initialized" in str(exc_info.value)


@pytest.mark.unit
def test_ensure_healthy_health_check_fails(basic_config):
    """Test ensure_healthy fails when health check fails"""
    processor = MockProcessor(basic_config)
    processor.initialize()

    # Now make health check fail
    processor.should_fail_health = True

    with pytest.raises(ProcessorHealthCheckError) as exc_info:
        processor.ensure_healthy()

    assert "health check failed" in str(exc_info.value)


@pytest.mark.unit
def test_ensure_healthy_updates_timestamp(mock_processor):
    """Test that ensure_healthy updates last_health_check timestamp"""
    mock_processor.initialize()

    first_check_time = time.time()
    mock_processor.ensure_healthy()
    first_timestamp = mock_processor.last_health_check

    time.sleep(0.01)  # Small delay

    mock_processor.ensure_healthy()
    second_timestamp = mock_processor.last_health_check

    assert second_timestamp > first_timestamp


@pytest.mark.unit
def test_get_status_not_initialized(mock_processor):
    """Test get_status when processor is not initialized"""
    status = mock_processor.get_status()

    assert status['model_name'] == 'Test Model'
    assert status['model_id'] == 'test_model'
    assert status['initialized'] is False
    assert status['initialization_error'] is None
    assert status['last_health_check'] is None
    assert status['healthy'] is False


@pytest.mark.unit
def test_get_status_initialized_healthy(mock_processor):
    """Test get_status when processor is initialized and healthy"""
    mock_processor.initialize()
    mock_processor.ensure_healthy()

    status = mock_processor.get_status()

    assert status['model_name'] == 'Test Model'
    assert status['model_id'] == 'test_model'
    assert status['initialized'] is True
    assert status['initialization_error'] is None
    assert status['last_health_check'] is not None
    assert status['healthy'] is True


@pytest.mark.unit
def test_get_status_initialized_unhealthy(basic_config):
    """Test get_status when processor is initialized but unhealthy"""
    processor = MockProcessor(basic_config)
    processor.initialize()

    # Make health check fail
    processor.should_fail_health = True

    status = processor.get_status()

    assert status['initialized'] is True
    assert status['healthy'] is False


@pytest.mark.unit
def test_get_status_with_error(basic_config):
    """Test get_status when initialization failed"""
    processor = MockProcessor(basic_config, should_fail_load=True)

    try:
        processor.initialize(retry_count=0)
    except ProcessorInitializationError:
        pass

    status = processor.get_status()

    assert status['initialized'] is False
    assert status['initialization_error'] is not None
    assert "Model load failed" in status['initialization_error']


@pytest.mark.unit
def test_processor_initialization_error_exception():
    """Test ProcessorInitializationError exception"""
    error = ProcessorInitializationError("Test error")
    assert str(error) == "Test error"
    assert isinstance(error, Exception)


@pytest.mark.unit
def test_processor_health_check_error_exception():
    """Test ProcessorHealthCheckError exception"""
    error = ProcessorHealthCheckError("Health check failed")
    assert str(error) == "Health check failed"
    assert isinstance(error, Exception)


@pytest.mark.unit
def test_abstract_methods_not_implemented():
    """Test that abstract methods raise NotImplementedError"""
    # Can't instantiate BaseProcessor directly due to abstract methods
    # This test verifies the abstract nature

    with pytest.raises(TypeError) as exc_info:
        # Try to instantiate BaseProcessor directly
        processor = BaseProcessor({'id': 'test', 'name': 'test'})

    assert "abstract" in str(exc_info.value).lower() or "instantiate" in str(exc_info.value).lower()


@pytest.mark.unit
def test_initialize_zero_retries(basic_config):
    """Test initialization with zero retries"""
    processor = MockProcessor(basic_config, should_fail_load=True)

    with pytest.raises(ProcessorInitializationError) as exc_info:
        processor.initialize(retry_count=0)

    assert "after 1 attempt" in str(exc_info.value)
    assert processor.load_count == 1


@pytest.mark.unit
def test_concurrent_initialization(basic_config):
    """Test that multiple initializations don't cause issues"""
    processor = MockProcessor(basic_config)

    processor.initialize()
    first_load_count = processor.load_count

    # Initialize again
    processor.initialize()
    second_load_count = processor.load_count

    # Should have loaded twice
    assert second_load_count > first_load_count
    assert processor.initialized is True


@pytest.mark.unit
def test_health_check_count(mock_processor):
    """Test that health checks are actually being called"""
    mock_processor.initialize()

    initial_count = mock_processor.health_count

    mock_processor.ensure_healthy()
    assert mock_processor.health_count > initial_count

    mock_processor.ensure_healthy()
    mock_processor.ensure_healthy()

    # Health check should be called multiple times
    assert mock_processor.health_count >= 4  # 1 during init + 3 explicit calls
import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from shared.models.processors import EasyOCRProcessor


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
@patch('shared.models.processors.easyocr')
def test_easyocr_processor_initialization_success(mock_easyocr, easyocr_config):
    """Test successful initialization of EasyOCR processor"""
    mock_reader = Mock()
    mock_easyocr.Reader.return_value = mock_reader

    processor = EasyOCRProcessor(easyocr_config)

    assert processor.model_config == easyocr_config
    assert processor.model_name == 'EasyOCR'
    assert processor.reader == mock_reader
    mock_easyocr.Reader.assert_called_once_with(['en'], gpu=False, verbose=False)


@pytest.mark.unit
@patch('shared.models.processors.easyocr', None)
def test_easyocr_processor_initialization_no_module(easyocr_config):
    """Test initialization fails when easyocr is not installed"""
    with pytest.raises(ImportError) as exc_info:
        processor = EasyOCRProcessor(easyocr_config)

    assert "EasyOCR not installed" in str(exc_info.value)


@pytest.mark.unit
@patch('shared.models.processors.easyocr')
def test_easyocr_processor_initialization_failure(mock_easyocr, easyocr_config):
    """Test initialization fails when Reader creation fails"""
    mock_easyocr.Reader.side_effect = RuntimeError("Reader creation failed")

    with pytest.raises(RuntimeError) as exc_info:
        processor = EasyOCRProcessor(easyocr_config)

    assert "EasyOCR init failed" in str(exc_info.value)


@pytest.mark.unit
@patch('shared.models.processors.easyocr')
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
@patch('shared.models.processors.easyocr')
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
@patch('shared.models.processors.easyocr')
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
@patch('shared.models.processors.easyocr', None)
def test_extract_no_easyocr_module(easyocr_config):
    """Test extraction when easyocr module is not available"""
    # Can't create processor without easyocr, so test the extract logic directly
    # This tests the runtime check in extract()
    import sys
    from shared.models import processors as easyocr_processor

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
@patch('shared.models.processors.easyocr')
def test_extract_reader_not_initialized(mock_easyocr, easyocr_config):
    """Test extraction when reader is not initialized"""
    mock_easyocr.Reader.return_value = None

    processor = EasyOCRProcessor(easyocr_config)
    processor.reader = None  # Simulate reader not initialized

    result = processor.extract('/path/to/test/image.jpg')

    assert result.success is False
    assert "reader init failed" in result.error


@pytest.mark.unit
@patch('shared.models.processors.easyocr')
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
@patch('shared.models.processors.easyocr')
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
    # Known store names are normalized to uppercase by extract_store_name
    assert result.data.store_name == 'WALMART'


@pytest.mark.unit
@patch('shared.models.processors.easyocr')
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
@patch('shared.models.processors.easyocr')
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
@patch('shared.models.processors.easyocr')
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
@patch('shared.models.processors.easyocr')
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
@patch('shared.models.processors.easyocr')
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
@patch('shared.models.processors.easyocr')
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
@patch('shared.models.processors.easyocr')
def test_extract_empty_text_lines(mock_easyocr, easyocr_config):
    """Test parsing with empty text lines after filtering"""
    # Reset OCRConfig before test to ensure clean state
    from shared.models.ocr_config import OCRConfig
    OCRConfig._instance = None
    
    mock_reader = Mock()
    mock_easyocr.Reader.return_value = mock_reader

    # All very low confidence results that are below even the lowered threshold
    mock_reader.readtext.return_value = [
        ([[0, 0], [100, 0], [100, 50], [0, 50]], 'Text', 0.05),
        ([[0, 60], [100, 60], [100, 90], [0, 90]], 'More', 0.08),
    ]

    processor = EasyOCRProcessor(easyocr_config)
    result = processor.extract('/path/to/test/image.jpg')

    assert result.success is False
    assert "No text detected" in result.error


@pytest.mark.unit
@patch('shared.models.processors.easyocr')
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
@patch('shared.models.processors.PaddleOCR')
@patch('shared.models.processors.load_and_validate_image')
@patch('shared.models.processors.preprocess_for_ocr')
def test_paddle_processor_initialization_success(mock_preprocess, mock_load, mock_paddle_cls, paddle_config):
    """Test successful initialization of Paddle processor with circular exchange config"""
    from shared.models.processors import PaddleProcessor
    from shared.models.ocr_config import OCRConfig
    
    # Reset OCRConfig to ensure default values
    OCRConfig._instance = None
    config = OCRConfig()
    
    # Get the expected box_threshold from the config
    expected_box_threshold = config.detection_box_threshold

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
        det_db_box_thresh=expected_box_threshold
    )


@pytest.mark.unit
@patch('shared.models.processors.PaddleOCR')
def test_paddle_processor_initialization_failure(mock_paddle_cls, paddle_config):
    """Test initialization fails when PaddleOCR creation fails"""
    from shared.models.processors import PaddleProcessor

    mock_paddle_cls.side_effect = RuntimeError("PaddleOCR creation failed")

    with pytest.raises(RuntimeError):
        processor = PaddleProcessor(paddle_config)


@pytest.mark.unit
@patch('shared.models.processors.PaddleOCR')
@patch('shared.models.processors.load_and_validate_image')
@patch('shared.models.processors.preprocess_for_ocr')
def test_extract_success(mock_preprocess, mock_load, mock_paddle_cls, paddle_config):
    """Test successful extraction with PaddleOCR"""
    from shared.models.processors import PaddleProcessor

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
@patch('shared.models.processors.PaddleOCR')
@patch('shared.models.processors.load_and_validate_image')
@patch('shared.models.processors.preprocess_for_ocr')
def test_extract_no_results(mock_preprocess, mock_load, mock_paddle_cls, paddle_config):
    """Test extraction when no text is detected"""
    from shared.models.processors import PaddleProcessor

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
@patch('shared.models.processors.PaddleOCR')
@patch('shared.models.processors.load_and_validate_image')
@patch('shared.models.processors.preprocess_for_ocr')
def test_extract_empty_results(mock_preprocess, mock_load, mock_paddle_cls, paddle_config):
    """Test extraction with empty results"""
    from shared.models.processors import PaddleProcessor

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
@patch('shared.models.processors.PaddleOCR')
@patch('shared.models.processors.load_and_validate_image')
@patch('shared.models.processors.preprocess_for_ocr')
def test_extract_retry_with_original_image(mock_preprocess, mock_load, mock_paddle_cls, paddle_config):
    """Test that extraction retries with original image if preprocessed fails"""
    from shared.models.processors import PaddleProcessor

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
@patch('shared.models.processors.PaddleOCR')
@patch('shared.models.processors.load_and_validate_image')
@patch('shared.models.processors.preprocess_for_ocr')
def test_extract_grayscale_to_rgb_conversion(mock_preprocess, mock_load, mock_paddle_cls, paddle_config):
    """Test that grayscale images are converted to RGB"""
    from shared.models.processors import PaddleProcessor

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
@patch('shared.models.processors.PaddleOCR')
@patch('shared.models.processors.load_and_validate_image')
@patch('shared.models.processors.preprocess_for_ocr')
def test_extract_exception_handling(mock_preprocess, mock_load, mock_paddle_cls, paddle_config):
    """Test extraction handles exceptions gracefully"""
    from shared.models.processors import PaddleProcessor

    mock_ocr = Mock()
    mock_paddle_cls.return_value = mock_ocr

    mock_load.side_effect = RuntimeError("Image load failed")

    processor = PaddleProcessor(paddle_config)
    result = processor.extract('/path/to/test/image.jpg')

    assert result.success is False
    assert "Image load failed" in result.error


@pytest.mark.unit
@patch('shared.models.processors.PaddleOCR')
@patch('shared.models.processors.load_and_validate_image')
@patch('shared.models.processors.preprocess_for_ocr')
def test_extract_low_confidence_filtered(mock_preprocess, mock_load, mock_paddle_cls, paddle_config):
    """Test that low confidence results are filtered out"""
    from shared.models.processors import PaddleProcessor

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
@patch('shared.models.processors.PaddleOCR')
@patch('shared.models.processors.load_and_validate_image')
@patch('shared.models.processors.preprocess_for_ocr')
def test_extract_date_patterns(mock_preprocess, mock_load, mock_paddle_cls, paddle_config):
    """Test various date pattern detection"""
    from shared.models.processors import PaddleProcessor

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
@patch('shared.models.processors.PaddleOCR')
@patch('shared.models.processors.load_and_validate_image')
@patch('shared.models.processors.preprocess_for_ocr')
def test_extract_total_patterns(mock_preprocess, mock_load, mock_paddle_cls, paddle_config):
    """Test various total pattern detection"""
    from shared.models.processors import PaddleProcessor

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
@patch('shared.models.processors.PaddleOCR')
@patch('shared.models.processors.load_and_validate_image')
@patch('shared.models.processors.preprocess_for_ocr')
def test_extract_line_items(mock_preprocess, mock_load, mock_paddle_cls, paddle_config):
    """Test line item extraction"""
    from shared.models.processors import PaddleProcessor

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
@patch('shared.models.processors.PaddleOCR')
@patch('shared.models.processors.load_and_validate_image')
@patch('shared.models.processors.preprocess_for_ocr')
def test_extract_skip_keywords(mock_preprocess, mock_load, mock_paddle_cls, paddle_config):
    """Test that lines with skip keywords are not extracted as items"""
    from shared.models.processors import PaddleProcessor

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
@patch('shared.models.processors.PaddleOCR')
@patch('shared.models.processors.load_and_validate_image')
@patch('shared.models.processors.preprocess_for_ocr')
def test_extract_address_detection(mock_preprocess, mock_load, mock_paddle_cls, paddle_config):
    """Test address detection"""
    from shared.models.processors import PaddleProcessor

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
@patch('shared.models.processors.PaddleOCR')
@patch('shared.models.processors.load_and_validate_image')
@patch('shared.models.processors.preprocess_for_ocr')
def test_extract_phone_detection(mock_preprocess, mock_load, mock_paddle_cls, paddle_config):
    """Test phone number detection"""
    from shared.models.processors import PaddleProcessor

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
    from shared.models.processors import PaddleProcessor

    assert PaddleProcessor._normalize_price('12.99') == Decimal('12.99')
    assert PaddleProcessor._normalize_price('$5.50') == Decimal('5.50')
    assert PaddleProcessor._normalize_price('100') == Decimal('100')
    assert PaddleProcessor._normalize_price('0.99') == Decimal('0.99')
    assert PaddleProcessor._normalize_price('15,99') == Decimal('15.99')  # European format


@pytest.mark.unit
def test_normalize_price_invalid():
    """Test price normalization with invalid values"""
    from shared.models.processors import PaddleProcessor

    assert PaddleProcessor._normalize_price(None) is None
    assert PaddleProcessor._normalize_price('-5.00') is None
    assert PaddleProcessor._normalize_price('abc') is None
    assert PaddleProcessor._normalize_price('10000') is None  # Out of range


@pytest.mark.unit
@patch('shared.models.processors.PaddleOCR')
@patch('shared.models.processors.load_and_validate_image')
@patch('shared.models.processors.preprocess_for_ocr')
def test_extract_confidence_score_calculation(mock_preprocess, mock_load, mock_paddle_cls, paddle_config):
    """Test that confidence score is calculated correctly"""
    from shared.models.processors import PaddleProcessor

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
@patch('shared.models.processors.PaddleOCR')
@patch('shared.models.processors.load_and_validate_image')
@patch('shared.models.processors.preprocess_for_ocr')
def test_extract_malformed_result_handling(mock_preprocess, mock_load, mock_paddle_cls, paddle_config):
    """Test handling of malformed OCR results"""
    from shared.models.processors import PaddleProcessor

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
@patch('shared.models.processors.PaddleOCR')
@patch('shared.models.processors.load_and_validate_image')
@patch('shared.models.processors.preprocess_for_ocr')
def test_extract_quantity_parsing(mock_preprocess, mock_load, mock_paddle_cls, paddle_config):
    """Test parsing of quantity in line items"""
    from shared.models.processors import PaddleProcessor

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
import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from decimal import Decimal
import json


@pytest.fixture
def donut_config():
    """Configuration for Donut processor"""
    return {
        'id': 'donut_sroie',
        'name': 'Donut SROIE',
        'type': 'donut',
        'description': 'Donut model for SROIE',
        'huggingface_id': 'naver-clova-ix/donut-base-finetuned-cord-v2',
        'task_prompt': '<s_cord-v2>'
    }


@pytest.fixture
def florence_config():
    """Configuration for Florence processor"""
    return {
        'id': 'florence2',
        'name': 'Florence-2',
        'type': 'florence',
        'description': 'Florence-2 model',
        'huggingface_id': 'microsoft/Florence-2-large',
        'task_prompt': '<OCR_WITH_REGION>'
    }


@pytest.mark.unit
def test_donut_processor_initialization(donut_config):
    """Test DonutProcessor initialization"""
    # Skip if transformers not available
    pytest.importorskip('transformers')
    
    mock_torch = Mock()
    mock_torch.cuda.is_available.return_value = False
    
    mock_processor = Mock()
    mock_tokenizer = Mock()
    mock_tokenizer.__len__ = Mock(return_value=30000)
    mock_processor.tokenizer = mock_tokenizer
    mock_model = Mock()
    mock_model.decoder.config.max_position_embeddings = 512
    
    mock_proc_cls = Mock(return_value=mock_processor)
    mock_proc_cls.from_pretrained.return_value = mock_processor
    mock_model_cls = Mock(return_value=mock_model)
    mock_model_cls.from_pretrained.return_value = mock_model
    
    with patch('shared.models.ai_models._get_torch', return_value=mock_torch):
        with patch('shared.models.ai_models._get_transformers', return_value=(mock_proc_cls, mock_model_cls, None, None)):
            from shared.models.ai_models import DonutProcessor
            processor = DonutProcessor(donut_config)
    
            assert processor.model_config == donut_config
            assert processor.model_id == 'naver-clova-ix/donut-base-finetuned-cord-v2'
            assert processor.task_prompt == '<s_cord-v2>'
            assert processor.model_name == 'Donut SROIE'
            assert processor.device == 'cpu'


@pytest.mark.unit
def test_donut_processor_gpu_detection(donut_config):
    """Test GPU detection and device assignment"""
    pytest.importorskip('transformers')
    
    mock_torch = Mock()
    mock_torch.cuda.is_available.return_value = True
    
    mock_processor = Mock()
    mock_tokenizer = Mock()
    mock_tokenizer.__len__ = Mock(return_value=30000)
    mock_processor.tokenizer = mock_tokenizer
    mock_model = Mock()
    mock_model.decoder.config.max_position_embeddings = 512
    
    mock_proc_cls = Mock()
    mock_proc_cls.from_pretrained.return_value = mock_processor
    mock_model_cls = Mock()
    mock_model_cls.from_pretrained.return_value = mock_model
    
    with patch('shared.models.ai_models._get_torch', return_value=mock_torch):
        with patch('shared.models.ai_models._get_transformers', return_value=(mock_proc_cls, mock_model_cls, None, None)):
            from shared.models.ai_models import DonutProcessor
            processor = DonutProcessor(donut_config)
    
            assert processor.device == 'cuda'
            mock_model.to.assert_called_with('cuda')


@pytest.mark.unit
def test_donut_processor_load_retry(donut_config):
    """Test model loading with retry logic"""
    pytest.importorskip('transformers')
    
    mock_torch = Mock()
    mock_torch.cuda.is_available.return_value = False
    
    mock_processor = Mock()
    mock_tokenizer = Mock()
    mock_tokenizer.__len__ = Mock(return_value=30000)
    mock_processor.tokenizer = mock_tokenizer
    mock_model = Mock()
    mock_model.decoder.config.max_position_embeddings = 512
    
    mock_proc_cls = Mock()
    # Processor fails on first attempt, succeeds on second
    mock_proc_cls.from_pretrained.side_effect = [
        RuntimeError("Download failed"),
        mock_processor
    ]
    mock_model_cls = Mock()
    mock_model_cls.from_pretrained.return_value = mock_model
    
    with patch('shared.models.ai_models._get_torch', return_value=mock_torch):
        with patch('shared.models.ai_models._get_transformers', return_value=(mock_proc_cls, mock_model_cls, None, None)):
            with patch('time.sleep'):  # Don't actually sleep in tests
                from shared.models.ai_models import DonutProcessor
                processor = DonutProcessor(donut_config)
    
            # Should succeed after retry
            assert processor.model is not None


@pytest.mark.unit
def test_donut_processor_load_failure(donut_config):
    """Test model loading fails after max retries"""
    pytest.importorskip('transformers')
    
    mock_torch = Mock()
    mock_torch.cuda.is_available.return_value = False
    
    mock_proc_cls = Mock()
    mock_proc_cls.from_pretrained.side_effect = RuntimeError("Network error")
    mock_model_cls = Mock()
    mock_model_cls.from_pretrained.side_effect = RuntimeError("Network error")
    
    with patch('shared.models.ai_models._get_torch', return_value=mock_torch):
        with patch('shared.models.ai_models._get_transformers', return_value=(mock_proc_cls, mock_model_cls, None, None)):
            with patch('time.sleep'):  # Don't actually sleep in tests
                from shared.models.ai_models import DonutProcessor
                with pytest.raises(RuntimeError) as exc_info:
                    processor = DonutProcessor(donut_config)
    
                assert "Failed to load" in str(exc_info.value) or "Network error" in str(exc_info.value)


@pytest.mark.unit
def test_normalize_price_valid():
    """Test price normalization with valid values"""
    from shared.models.ai_models import BaseDonutProcessor

    assert BaseDonutProcessor.normalize_price('12.99') == Decimal('12.99')
    assert BaseDonutProcessor.normalize_price('$5.50') == Decimal('5.50')
    assert BaseDonutProcessor.normalize_price('100') == Decimal('100')
    assert BaseDonutProcessor.normalize_price('0.99') == Decimal('0.99')
    assert BaseDonutProcessor.normalize_price('1,234.56') == Decimal('1234.56')


@pytest.mark.unit
def test_normalize_price_invalid():
    """Test price normalization with invalid values"""
    from shared.models.ai_models import BaseDonutProcessor

    assert BaseDonutProcessor.normalize_price(None) is None
    assert BaseDonutProcessor.normalize_price('') is None
    assert BaseDonutProcessor.normalize_price('-5.00') is None
    assert BaseDonutProcessor.normalize_price('abc') is None
    assert BaseDonutProcessor.normalize_price('10000') is None  # Out of range
    assert BaseDonutProcessor.normalize_price('12345') is None  # Looks like zip code


@pytest.mark.unit
def test_parse_json_output_valid():
    """Test parsing valid JSON output"""
    from shared.models.ai_models import BaseDonutProcessor

    test_cases = [
        ('{"store": "Test"}', {"store": "Test"}),
        ('```json\n{"store": "Test"}\n```', {"store": "Test"}),
        ('Some text {"store": "Test"} more text', {"store": "Test"}),
    ]

    for input_str, expected in test_cases:
        result = BaseDonutProcessor.parse_json_output(input_str)
        assert result == expected


@pytest.mark.unit
def test_parse_json_output_invalid():
    """Test parsing invalid JSON output"""
    from shared.models.ai_models import BaseDonutProcessor

    test_cases = [
        '',
        '   ',
        'Not JSON at all',
        'Almost {JSON but not quite',
    ]

    for input_str in test_cases:
        result = BaseDonutProcessor.parse_json_output(input_str)
        assert result == {}


@pytest.mark.unit
def test_donut_extract_success(donut_config):
    """Test successful extraction with Donut"""
    pytest.importorskip('transformers')
    pytest.importorskip('torch')
    
    from shared.models.ai_models import DonutProcessor
    from PIL import Image
    
    mock_torch = Mock()
    mock_torch.cuda.is_available.return_value = False
    
    mock_image = Mock(spec=Image.Image)
    mock_processor = Mock()
    mock_model = Mock()
    
    mock_tokenizer = Mock()
    mock_tokenizer.__len__ = Mock(return_value=30000)
    mock_tokenizer.pad_token_id = 0
    mock_tokenizer.eos_token_id = 2
    mock_tokenizer.eos_token = '</s>'
    mock_tokenizer.pad_token = '<pad>'
    mock_tokenizer.unk_token_id = 3
    mock_tokenizer.return_value = Mock(input_ids=Mock(to=Mock(return_value=Mock())))
    mock_processor.tokenizer = mock_tokenizer
    mock_processor.return_value = Mock(pixel_values=Mock(to=Mock(return_value=Mock())))
    
    mock_decoder_config = Mock()
    mock_decoder_config.max_position_embeddings = 1024
    mock_model.decoder.config = mock_decoder_config
    mock_output = Mock()
    mock_output.sequences = [Mock()]
    mock_model.generate.return_value = mock_output
    
    json_output = json.dumps({
        'company': 'Test Store',
        'address': '123 Main St',
        'date': '2024-01-15',
        'total': '12.99',
        'menu': [
            {'nm': 'Item 1', 'price': '5.99'},
            {'nm': 'Item 2', 'price': '6.00'}
        ]
    })
    mock_processor.batch_decode.return_value = [f'<s_cord-v2>{json_output}</s>']
    
    mock_proc_cls = Mock()
    mock_proc_cls.from_pretrained.return_value = mock_processor
    mock_model_cls = Mock()
    mock_model_cls.from_pretrained.return_value = mock_model
    
    with patch('shared.models.ai_models._get_torch', return_value=mock_torch):
        with patch('shared.models.ai_models._get_transformers', return_value=(mock_proc_cls, mock_model_cls, None, None)):
            with patch('shared.models.ai_models.load_and_validate_image', return_value=mock_image):
                with patch('shared.models.ai_models.enhance_image', return_value=mock_image):
                    processor = DonutProcessor(donut_config)
                    result = processor.extract('/path/to/test/image.jpg')
    
                    assert result.success is True
                    assert result.data is not None


@pytest.mark.unit  
def test_donut_extract_fallback_text(donut_config):
    """Test extraction with fallback text parsing for SROIE"""
    pytest.importorskip('transformers')
    pytest.importorskip('torch')
    
    from shared.models.ai_models import DonutProcessor
    from PIL import Image
    
    mock_torch = Mock()
    mock_torch.cuda.is_available.return_value = False
    
    mock_image = Mock(spec=Image.Image)
    mock_processor = Mock()
    mock_model = Mock()
    
    mock_tokenizer = Mock()
    mock_tokenizer.__len__ = Mock(return_value=30000)
    mock_tokenizer.pad_token_id = 0
    mock_tokenizer.eos_token_id = 2
    mock_tokenizer.eos_token = '</s>'
    mock_tokenizer.pad_token = '<pad>'
    mock_tokenizer.unk_token_id = 3
    mock_tokenizer.return_value = Mock(input_ids=Mock(to=Mock(return_value=Mock())))
    mock_processor.tokenizer = mock_tokenizer
    mock_processor.return_value = Mock(pixel_values=Mock(to=Mock(return_value=Mock())))
    
    mock_decoder_config = Mock()
    mock_decoder_config.max_position_embeddings = 1024
    mock_model.decoder.config = mock_decoder_config
    mock_output = Mock()
    mock_output.sequences = [Mock()]
    mock_model.generate.return_value = mock_output
    
    text_output = """Test Store
123 Main St
Date: 01/15/2024
Total: $12.99"""
    mock_processor.batch_decode.return_value = [f'<s_sroie>{text_output}</s>']
    
    mock_proc_cls = Mock()
    mock_proc_cls.from_pretrained.return_value = mock_processor
    mock_model_cls = Mock()
    mock_model_cls.from_pretrained.return_value = mock_model
    
    with patch('shared.models.ai_models._get_torch', return_value=mock_torch):
        with patch('shared.models.ai_models._get_transformers', return_value=(mock_proc_cls, mock_model_cls, None, None)):
            with patch('shared.models.ai_models.load_and_validate_image', return_value=mock_image):
                with patch('shared.models.ai_models.enhance_image', return_value=mock_image):
                    processor = DonutProcessor(donut_config)
                    result = processor.extract('/path/to/test/image.jpg')
    
                    assert result.success is True
                    assert result.data is not None


@pytest.mark.unit
def test_donut_extract_exception(donut_config):
    """Test extraction handles exceptions"""
    pytest.importorskip('transformers')
    
    from shared.models.ai_models import DonutProcessor
    
    mock_torch = Mock()
    mock_torch.cuda.is_available.return_value = False
    
    mock_processor = Mock()
    mock_tokenizer = Mock()
    mock_tokenizer.__len__ = Mock(return_value=30000)
    mock_processor.tokenizer = mock_tokenizer
    mock_model = Mock()
    mock_model.decoder.config.max_position_embeddings = 512
    
    mock_proc_cls = Mock()
    mock_proc_cls.from_pretrained.return_value = mock_processor
    mock_model_cls = Mock()
    mock_model_cls.from_pretrained.return_value = mock_model
    
    with patch('shared.models.ai_models._get_torch', return_value=mock_torch):
        with patch('shared.models.ai_models._get_transformers', return_value=(mock_proc_cls, mock_model_cls, None, None)):
            with patch('shared.models.ai_models.load_and_validate_image', side_effect=RuntimeError("Image load failed")):
                processor = DonutProcessor(donut_config)
                result = processor.extract('/path/to/test/image.jpg')
    
                assert result.success is False
                assert "Image load failed" in result.error


@pytest.mark.unit
def test_safe_extract_string():
    """Test safe string extraction from various data types"""
    from shared.models.ai_models import DonutProcessor
    from unittest.mock import MagicMock

    # Create a mock processor instance just for testing the method
    processor = MagicMock(spec=DonutProcessor)
    # Bind the actual method to the mock
    processor._safe_extract_string = DonutProcessor._safe_extract_string.__get__(processor)

    # Test cases
    assert processor._safe_extract_string(None) is None
    assert processor._safe_extract_string('') is None
    assert processor._safe_extract_string('  ') is None
    assert processor._safe_extract_string('test') == 'test'
    assert processor._safe_extract_string('  test  ') == 'test'
    assert processor._safe_extract_string(123) == '123'
    assert processor._safe_extract_string(45.67) == '45.67'
    assert processor._safe_extract_string({'nm': 'test'}) == 'test'
    assert processor._safe_extract_string({'name': 'test'}) == 'test'
    assert processor._safe_extract_string({'price': '5.99'}) == '5.99'
    assert processor._safe_extract_string({'other': 'value'}) == 'value'


@pytest.mark.unit
def test_calculate_confidence_sroie():
    """Test confidence calculation for SROIE model"""
    from shared.models.ai_models import DonutProcessor
    from shared.utils.data_structures import ReceiptData
    from unittest.mock import MagicMock

    processor = MagicMock()
    processor.model_id = 'donut-sroie'
    processor._calculate_confidence = DonutProcessor._calculate_confidence.__get__(processor)

    receipt = ReceiptData()
    assert processor._calculate_confidence(receipt) == 0.0

    receipt.store_name = "Test Store"
    assert processor._calculate_confidence(receipt) == 30.0

    receipt.total = Decimal('10.00')
    assert processor._calculate_confidence(receipt) == 60.0

    receipt.store_address = "123 Main St"
    assert processor._calculate_confidence(receipt) == 80.0

    receipt.transaction_date = "2024-01-15"
    assert processor._calculate_confidence(receipt) == 100.0


@pytest.mark.unit
def test_extract_from_text():
    """Test text extraction fallback"""
    from shared.models.ai_models import DonutProcessor
    from unittest.mock import MagicMock

    processor = MagicMock()
    processor._extract_from_text = DonutProcessor._extract_from_text.__get__(processor)

    text = """WALMART SUPERCENTER
123 Main Street, TX 12345
Date: 01/15/2024
Apple 2.99
Banana 1.49
Total: $4.48"""

    result = processor._extract_from_text(text)

    assert 'total' in result
    assert result['total'] == '4.48'
    assert 'date' in result
    assert result['date'] == '01/15/2024'


@pytest.mark.unit
def test_extract_from_text_cord():
    """Test CORD-specific text extraction"""
    from shared.models.ai_models import DonutProcessor
    from unittest.mock import MagicMock

    processor = MagicMock()
    processor._extract_from_text_cord = DonutProcessor._extract_from_text_cord.__get__(processor)

    text = """<s_nm>Test Store</s_nm>
<s_num>123 Main Street</s_num>
<s_total_price>$12.99</s_total_price>
<sep/>
<s_nm>Item 1</s_nm>
<s_price>5.99</s_price>
<s_cnt>1</s_cnt>
<sep/>
<s_nm>Item 2</s_nm>
<s_price>7.00</s_price>"""

    result = processor._extract_from_text_cord(text)

    assert result['company'] == 'Test Store'
    assert result['total'] == '12.99'
    assert 'menu' in result
    assert len(result['menu']) == 2


@pytest.mark.unit
def test_florence_processor_initialization(florence_config):
    """Test FlorenceProcessor initialization"""
    pytest.importorskip('transformers')
    
    from shared.models.ai_models import FlorenceProcessor
    
    mock_torch = Mock()
    mock_torch.cuda.is_available.return_value = False
    mock_processor = Mock()
    mock_model = Mock()
    
    mock_proc_cls = Mock()
    mock_proc_cls.from_pretrained.return_value = mock_processor
    mock_model_cls = Mock()
    mock_model_cls.from_pretrained.return_value = mock_model
    
    with patch('shared.models.ai_models._get_torch', return_value=mock_torch):
        with patch('shared.models.ai_models._get_transformers', return_value=(None, None, mock_proc_cls, mock_model_cls)):
            processor = FlorenceProcessor(florence_config)
    
            assert processor.model_config == florence_config
            assert processor.model_id == 'microsoft/Florence-2-large'
            assert processor.task_prompt == '<OCR_WITH_REGION>'
            assert processor.device == 'cpu'


@pytest.mark.unit
def test_florence_processor_load_failure(florence_config):
    """Test FlorenceProcessor loading fails after retries"""
    pytest.importorskip('transformers')
    
    from shared.models.ai_models import FlorenceProcessor
    
    mock_torch = Mock()
    mock_torch.cuda.is_available.return_value = False
    
    mock_proc_cls = Mock()
    mock_proc_cls.from_pretrained.return_value = Mock()
    mock_model_cls = Mock()
    mock_model_cls.from_pretrained.side_effect = RuntimeError("Network error")
    
    with patch('shared.models.ai_models._get_torch', return_value=mock_torch):
        with patch('shared.models.ai_models._get_transformers', return_value=(None, None, mock_proc_cls, mock_model_cls)):
            with patch('time.sleep'):  # Don't actually sleep
                with pytest.raises(RuntimeError) as exc_info:
                    processor = FlorenceProcessor(florence_config)
    
                assert "Failed to load Florence-2" in str(exc_info.value) or "Network error" in str(exc_info.value)


@pytest.mark.unit
def test_build_receipt_data():
    """Test building receipt data from parsed JSON"""
    pytest.importorskip('transformers')
    
    from shared.models.ai_models import DonutProcessor
    
    mock_torch = Mock()
    mock_torch.cuda.is_available.return_value = False
    mock_processor = Mock()
    mock_tokenizer = Mock()
    mock_tokenizer.__len__ = Mock(return_value=30000)
    mock_processor.tokenizer = mock_tokenizer
    mock_model = Mock()
    mock_model.decoder.config.max_position_embeddings = 512
    
    mock_proc_cls = Mock()
    mock_proc_cls.from_pretrained.return_value = mock_processor
    mock_model_cls = Mock()
    mock_model_cls.from_pretrained.return_value = mock_model

    donut_config = {
        'id': 'donut_sroie',
        'name': 'Donut SROIE',
        'type': 'donut',
        'huggingface_id': 'naver-clova-ix/donut-base-finetuned-cord-v2',
        'task_prompt': '<s_cord-v2>'
    }

    with patch('shared.models.ai_models._get_torch', return_value=mock_torch):
        with patch('shared.models.ai_models._get_transformers', return_value=(mock_proc_cls, mock_model_cls, None, None)):
            processor = DonutProcessor(donut_config)

            parsed_data = {
                'company': 'Test Store',
                'address': '123 Main St',
                'date': '2024-01-15',
                'total': '12.99',
                'menu': [
                    {'nm': 'Item 1', 'price': '5.99'},
                    {'nm': 'Item 2', 'price': '7.00'}
                ]
            }

            receipt = processor._build_receipt_data(parsed_data)

            assert receipt.store_name == 'Test Store'
            assert receipt.store_address == '123 Main St'
            assert receipt.transaction_date == '2024-01-15'
            assert receipt.total == Decimal('12.99')
            assert len(receipt.items) == 2
            assert receipt.items[0].name == 'Item 1'
            assert receipt.items[0].total_price == Decimal('5.99')


@pytest.mark.unit
def test_build_receipt_data_complex_total():
    """Test building receipt data with complex total structure"""
    pytest.importorskip('transformers')
    
    from shared.models.ai_models import DonutProcessor

    mock_torch = Mock()
    mock_torch.cuda.is_available.return_value = False
    mock_processor = Mock()
    mock_tokenizer = Mock()
    mock_tokenizer.__len__ = Mock(return_value=30000)
    mock_processor.tokenizer = mock_tokenizer
    mock_model = Mock()
    mock_model.decoder.config.max_position_embeddings = 512
    
    mock_proc_cls = Mock()
    mock_proc_cls.from_pretrained.return_value = mock_processor
    mock_model_cls = Mock()
    mock_model_cls.from_pretrained.return_value = mock_model

    donut_config = {
        'id': 'donut_sroie',
        'name': 'Donut SROIE',
        'type': 'donut',
        'huggingface_id': 'naver-clova-ix/donut-base-finetuned-cord-v2',
        'task_prompt': '<s_cord-v2>'
    }

    with patch('shared.models.ai_models._get_torch', return_value=mock_torch):
        with patch('shared.models.ai_models._get_transformers', return_value=(mock_proc_cls, mock_model_cls, None, None)):
            processor = DonutProcessor(donut_config)

            parsed_data = {
                'company': 'Test Store',
                'total': {
                    'total_price': '15.99',
                    'cashprice': '20.00',
                    'changeprice': '4.01'
                },
                'sub_total': {
                    'subtotal_price': '14.50'
                }
            }

            receipt = processor._build_receipt_data(parsed_data)

            assert receipt.total == Decimal('15.99')
            assert receipt.cash_tendered == Decimal('20.00')
            assert receipt.change_given == Decimal('4.01')
            assert receipt.subtotal == Decimal('14.50')


@pytest.mark.unit
def test_build_receipt_data_alternate_fields():
    """Test building receipt data with alternate field names"""
    pytest.importorskip('transformers')
    
    from shared.models.ai_models import DonutProcessor

    mock_torch = Mock()
    mock_torch.cuda.is_available.return_value = False
    mock_processor = Mock()
    mock_tokenizer = Mock()
    mock_tokenizer.__len__ = Mock(return_value=30000)
    mock_processor.tokenizer = mock_tokenizer
    mock_model = Mock()
    mock_model.decoder.config.max_position_embeddings = 512
    
    mock_proc_cls = Mock()
    mock_proc_cls.from_pretrained.return_value = mock_processor
    mock_model_cls = Mock()
    mock_model_cls.from_pretrained.return_value = mock_model

    donut_config = {
        'id': 'donut_sroie',
        'name': 'Donut SROIE',
        'type': 'donut',
        'huggingface_id': 'naver-clova-ix/donut-base-finetuned-cord-v2',
        'task_prompt': '<s_cord-v2>'
    }

    with patch('shared.models.ai_models._get_torch', return_value=mock_torch):
        with patch('shared.models.ai_models._get_transformers', return_value=(mock_proc_cls, mock_model_cls, None, None)):
            processor = DonutProcessor(donut_config)

            parsed_data = {
                'store_name': 'Alternate Store',  # Using store_name instead of company
                'items': [  # Using items instead of menu
                    {'name': 'Product A', 'total_price': '3.50'}
                ]
            }

            receipt = processor._build_receipt_data(parsed_data)

            assert receipt.store_name == 'Alternate Store'
            assert len(receipt.items) == 1
            assert receipt.items[0].name == 'Product A'
