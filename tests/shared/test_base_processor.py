import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from shared.models.base_processor import (
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
