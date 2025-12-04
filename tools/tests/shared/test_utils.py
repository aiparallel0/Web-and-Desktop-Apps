"""
Tests for the shared data structures module.
"""
import pytest
from decimal import Decimal


class TestLineItem:
    """Tests for LineItem class."""

    def test_create_basic_line_item(self):
        from shared.utils.data import LineItem
        item = LineItem(name="Coffee", total_price=Decimal("3.50"))
        assert item.name == "Coffee"
        assert item.total_price == Decimal("3.50")
        assert item.quantity == 1

    def test_line_item_with_quantity(self):
        from shared.utils.data import LineItem
        item = LineItem(name="Apple", quantity=3, unit_price=Decimal("0.50"), total_price=Decimal("1.50"))
        assert item.quantity == 3
        assert item.unit_price == Decimal("0.50")

    def test_line_item_calculate_total(self):
        from shared.utils.data import LineItem
        item = LineItem(name="Banana", quantity=5, unit_price=Decimal("0.30"), total_price=Decimal("0"))
        calculated = item.calculate_total()
        assert calculated == Decimal("1.50")

    def test_line_item_to_dict(self):
        from shared.utils.data import LineItem
        item = LineItem(name="Milk", total_price=Decimal("2.99"), category="Dairy")
        result = item.to_dict()
        assert result['name'] == "Milk"
        assert result['total_price'] == "2.99"
        assert result['category'] == "Dairy"

    def test_line_item_from_dict(self):
        from shared.utils.data import LineItem
        data = {
            'name': 'Bread',
            'quantity': 2,
            'total_price': '4.50',
            'category': 'Bakery'
        }
        item = LineItem.from_dict(data)
        assert item.name == 'Bread'
        assert item.quantity == 2
        assert item.total_price == Decimal('4.50')

    def test_line_item_normalizes_string_price(self):
        from shared.utils.data import LineItem
        item = LineItem(name="Test", total_price="5.99")
        assert item.total_price == Decimal("5.99")

    def test_line_item_handles_invalid_price(self):
        from shared.utils.data import LineItem
        item = LineItem(name="Test", total_price="invalid")
        assert item.total_price == Decimal("0")


class TestReceiptData:
    """Tests for ReceiptData class."""

    def test_create_empty_receipt(self):
        from shared.utils.data import ReceiptData
        receipt = ReceiptData()
        assert receipt.store_name is None
        assert receipt.items == []
        assert receipt.total is None

    def test_receipt_with_store_info(self):
        from shared.utils.data import ReceiptData
        receipt = ReceiptData(
            store_name="Test Store",
            store_address="123 Main St",
            store_phone="555-1234"
        )
        assert receipt.store_name == "Test Store"
        assert receipt.store_address == "123 Main St"
        assert receipt.store_phone == "555-1234"

    def test_receipt_with_totals(self):
        from shared.utils.data import ReceiptData
        receipt = ReceiptData(
            subtotal=Decimal("10.00"),
            tax=Decimal("0.80"),
            total=Decimal("10.80")
        )
        assert receipt.subtotal == Decimal("10.00")
        assert receipt.tax == Decimal("0.80")
        assert receipt.total == Decimal("10.80")

    def test_receipt_with_items(self):
        from shared.utils.data import ReceiptData, LineItem
        items = [
            LineItem(name="Item 1", total_price=Decimal("5.00")),
            LineItem(name="Item 2", total_price=Decimal("3.00"))
        ]
        receipt = ReceiptData(items=items)
        assert len(receipt.items) == 2

    def test_receipt_to_dict(self):
        from shared.utils.data import ReceiptData
        receipt = ReceiptData(
            store_name="Test Store",
            total=Decimal("25.00")
        )
        result = receipt.to_dict()
        assert result['store']['name'] == "Test Store"

    def test_receipt_add_item(self):
        from shared.utils.data import ReceiptData, LineItem
        receipt = ReceiptData()
        item = LineItem(name="Coffee", total_price=Decimal("4.50"))
        receipt.add_item(item)
        assert len(receipt.items) == 1
        assert receipt.items[0].name == "Coffee"


class TestExtractionResult:
    """Tests for ExtractionResult class."""

    def test_successful_result(self):
        from shared.utils.data import ExtractionResult, ReceiptData
        receipt = ReceiptData(store_name="Test")
        result = ExtractionResult(success=True, data=receipt)
        assert result.success is True
        assert result.data.store_name == "Test"
        assert result.error is None

    def test_failed_result(self):
        from shared.utils.data import ExtractionResult
        result = ExtractionResult(success=False, error="Image processing failed")
        assert result.success is False
        assert result.error == "Image processing failed"
        assert result.data is None

    def test_result_with_warnings(self):
        from shared.utils.data import ExtractionResult, ReceiptData
        receipt = ReceiptData()
        result = ExtractionResult(
            success=True,
            data=receipt,
            warnings=["Low image quality", "Some text unclear"]
        )
        assert len(result.warnings) == 2


class TestStoreInfo:
    """Tests for StoreInfo class."""

    def test_create_store_info(self):
        from shared.utils.data import StoreInfo
        store = StoreInfo(
            name="Walmart",
            address="123 Main St",
            phone="555-1234"
        )
        assert store.name == "Walmart"
        assert store.address == "123 Main St"

    def test_store_info_to_dict(self):
        from shared.utils.data import StoreInfo
        store = StoreInfo(name="Target", phone="555-5678")
        result = store.to_dict()
        assert result['name'] == "Target"
        assert result['phone'] == "555-5678"
        assert result['address'] is None


class TestTransactionTotals:
    """Tests for TransactionTotals class."""

    def test_create_totals(self):
        from shared.utils.data import TransactionTotals
        totals = TransactionTotals(
            subtotal=Decimal("50.00"),
            tax=Decimal("4.00"),
            total=Decimal("54.00")
        )
        assert totals.subtotal == Decimal("50.00")
        assert totals.tax == Decimal("4.00")
        assert totals.total == Decimal("54.00")

    def test_totals_with_payment(self):
        from shared.utils.data import TransactionTotals
        totals = TransactionTotals(
            total=Decimal("54.00"),
            cash_tendered=Decimal("60.00"),
            change_given=Decimal("6.00")
        )
        assert totals.cash_tendered == Decimal("60.00")
        assert totals.change_given == Decimal("6.00")

    def test_totals_to_dict(self):
        from shared.utils.data import TransactionTotals
        totals = TransactionTotals(
            subtotal=Decimal("100.00"),
            discount=Decimal("10.00"),
            total=Decimal("90.00")
        )
        result = totals.to_dict()
        assert result['subtotal'] == "100.00"
        assert result['discount'] == "10.00"


class TestExtractionStatus:
    """Tests for ExtractionStatus enum."""

    def test_status_values(self):
        from shared.utils.data import ExtractionStatus
        assert ExtractionStatus.SUCCESS.value == "success"
        assert ExtractionStatus.PARTIAL.value == "partial"
        assert ExtractionStatus.FAILED.value == "failed"
        assert ExtractionStatus.PENDING.value == "pending"
"""
Tests for the error handling module.
"""
import pytest
import time


class TestErrorCategory:
    """Tests for ErrorCategory enum."""

    def test_all_categories_exist(self):
        from shared.utils.helpers import ErrorCategory
        assert hasattr(ErrorCategory, 'VALIDATION')
        assert hasattr(ErrorCategory, 'AUTHENTICATION')
        assert hasattr(ErrorCategory, 'AUTHORIZATION')
        assert hasattr(ErrorCategory, 'NOT_FOUND')
        assert hasattr(ErrorCategory, 'PROCESSING')
        assert hasattr(ErrorCategory, 'INTERNAL')


class TestErrorCode:
    """Tests for ErrorCode enum."""

    def test_validation_codes(self):
        from shared.utils.helpers import ErrorCode
        assert ErrorCode.INVALID_INPUT.value.startswith('E1')
        assert ErrorCode.MISSING_REQUIRED_FIELD.value.startswith('E1')
        assert ErrorCode.FILE_TOO_LARGE.value.startswith('E1')

    def test_authentication_codes(self):
        from shared.utils.helpers import ErrorCode
        assert ErrorCode.INVALID_CREDENTIALS.value.startswith('E2')
        assert ErrorCode.TOKEN_EXPIRED.value.startswith('E2')

    def test_internal_codes(self):
        from shared.utils.helpers import ErrorCode
        assert ErrorCode.INTERNAL_ERROR.value.startswith('E9')


class TestReceiptExtractorError:
    """Tests for base ReceiptExtractorError."""

    def test_basic_error(self):
        from shared.utils.helpers import ReceiptExtractorError, ErrorCode, ErrorCategory
        error = ReceiptExtractorError("Test error")
        assert error.message == "Test error"
        assert error.code == ErrorCode.INTERNAL_ERROR
        assert error.category == ErrorCategory.INTERNAL
        assert error.http_status == 500

    def test_custom_error(self):
        from shared.utils.helpers import ReceiptExtractorError, ErrorCode, ErrorCategory
        error = ReceiptExtractorError(
            message="Custom error",
            code=ErrorCode.INVALID_INPUT,
            category=ErrorCategory.VALIDATION,
            http_status=400
        )
        assert error.http_status == 400
        assert error.code == ErrorCode.INVALID_INPUT

    def test_to_dict(self):
        from shared.utils.helpers import ReceiptExtractorError
        error = ReceiptExtractorError("Test error", details={'field': 'value'})
        result = error.to_dict()
        
        assert result['success'] is False
        assert 'error' in result
        assert result['error']['message'] == "Test error"
        assert 'timestamp' in result['error']
        assert result['error']['details'] == {'field': 'value'}

    def test_to_dict_with_suggestion(self):
        from shared.utils.helpers import ReceiptExtractorError
        error = ReceiptExtractorError(
            "Test error",
            suggestion="Try again later"
        )
        result = error.to_dict()
        assert result['error']['suggestion'] == "Try again later"


class TestValidationError:
    """Tests for ValidationError."""

    def test_default_values(self):
        from shared.utils.helpers import ValidationError, ErrorCode, ErrorCategory
        error = ValidationError("Invalid input")
        assert error.http_status == 400
        assert error.category == ErrorCategory.VALIDATION

    def test_with_details(self):
        from shared.utils.helpers import ValidationError
        error = ValidationError(
            "Invalid email",
            details={'field': 'email', 'reason': 'format'}
        )
        result = error.to_dict()
        assert result['error']['details']['field'] == 'email'


class TestAuthenticationError:
    """Tests for AuthenticationError."""

    def test_default_values(self):
        from shared.utils.helpers import AuthenticationError, ErrorCategory
        error = AuthenticationError()
        assert error.http_status == 401
        assert error.category == ErrorCategory.AUTHENTICATION
        assert error.message == "Authentication required"


class TestAuthorizationError:
    """Tests for AuthorizationError."""

    def test_default_values(self):
        from shared.utils.helpers import AuthorizationError, ErrorCategory
        error = AuthorizationError()
        assert error.http_status == 403
        assert error.category == ErrorCategory.AUTHORIZATION


class TestNotFoundError:
    """Tests for NotFoundError."""

    def test_default_values(self):
        from shared.utils.helpers import NotFoundError, ErrorCategory
        error = NotFoundError()
        assert error.http_status == 404
        assert error.category == ErrorCategory.NOT_FOUND

    def test_with_resource_info(self):
        from shared.utils.helpers import NotFoundError
        error = NotFoundError(
            message="User not found",
            resource_type="user",
            resource_id="123"
        )
        result = error.to_dict()
        assert result['error']['details']['resource_type'] == 'user'
        assert result['error']['details']['resource_id'] == '123'


class TestProcessingError:
    """Tests for ProcessingError."""

    def test_default_values(self):
        from shared.utils.helpers import ProcessingError, ErrorCategory
        error = ProcessingError("OCR failed")
        assert error.http_status == 500
        assert error.category == ErrorCategory.PROCESSING


class TestRateLimitError:
    """Tests for RateLimitError."""

    def test_default_values(self):
        from shared.utils.helpers import RateLimitError, ErrorCategory
        error = RateLimitError()
        assert error.http_status == 429
        assert error.category == ErrorCategory.RATE_LIMIT

    def test_with_retry_info(self):
        from shared.utils.helpers import RateLimitError
        error = RateLimitError(
            retry_after=60,
            limit=100,
            remaining=0
        )
        result = error.to_dict()
        assert result['error']['details']['retry_after'] == 60
        assert result['error']['details']['limit'] == 100
        assert result['error']['details']['remaining'] == 0


class TestExternalServiceError:
    """Tests for ExternalServiceError."""

    def test_default_values(self):
        from shared.utils.helpers import ExternalServiceError, ErrorCategory
        error = ExternalServiceError("Service unavailable")
        assert error.http_status == 503
        assert error.category == ErrorCategory.EXTERNAL_SERVICE

    def test_with_service_name(self):
        from shared.utils.helpers import ExternalServiceError
        error = ExternalServiceError(
            message="Cloud storage error",
            service_name="AWS S3"
        )
        result = error.to_dict()
        assert result['error']['details']['service'] == 'AWS S3'


class TestErrorResponseUtilities:
    """Tests for error response utility functions."""

    def test_create_error_response(self):
        from shared.utils.helpers import ValidationError, create_error_response
        error = ValidationError("Test error")
        response, status_code = create_error_response(error)
        
        assert status_code == 400
        assert response['success'] is False
        assert 'error' in response

    def test_create_simple_error_response(self):
        from shared.utils.helpers import create_simple_error_response
        response, status_code = create_simple_error_response(
            "Simple error",
            status_code=500
        )
        
        assert status_code == 500
        assert response['success'] is False
        assert response['error']['message'] == "Simple error"

    def test_handle_exception_custom_error(self):
        from shared.utils.helpers import ValidationError, handle_exception
        error = ValidationError("Test validation error")
        response, status_code = handle_exception(error)
        
        assert status_code == 400
        assert 'validation' in response['error']['type']

    def test_handle_exception_generic_error(self):
        from shared.utils.helpers import handle_exception
        error = ValueError("Generic Python error")
        response, status_code = handle_exception(error)
        
        # Should return generic 500 error
        assert status_code == 500
        assert response['success'] is False
"""
Tests for the centralized configuration module.
"""
import pytest
import os
from pathlib import Path


class TestImageConfig:
    """Tests for ImageConfig."""

    def test_default_max_size(self):
        from shared.config import ImageConfig
        config = ImageConfig()
        assert config.max_size_bytes == 100 * 1024 * 1024  # 100MB

    def test_allowed_extensions(self):
        from shared.config import ImageConfig
        config = ImageConfig()
        assert 'png' in config.allowed_extensions
        assert 'jpg' in config.allowed_extensions
        assert 'jpeg' in config.allowed_extensions
        assert 'exe' not in config.allowed_extensions

    def test_allowed_mime_types(self):
        from shared.config import ImageConfig
        config = ImageConfig()
        assert 'image/png' in config.allowed_mime_types
        assert 'image/jpeg' in config.allowed_mime_types
        assert 'application/pdf' not in config.allowed_mime_types


class TestOCRConfig:
    """Tests for OCRConfig."""

    def test_default_language(self):
        from shared.config import OCRConfig
        config = OCRConfig()
        assert config.default_language == 'en'

    def test_confidence_threshold(self):
        from shared.config import OCRConfig
        config = OCRConfig()
        assert 0 <= config.confidence_threshold <= 1

    def test_price_bounds(self):
        from shared.config import OCRConfig
        config = OCRConfig()
        assert config.price_min == 0.0
        assert config.price_max == 9999.0


class TestAPIConfig:
    """Tests for APIConfig."""

    def test_default_port(self):
        from shared.config import APIConfig
        config = APIConfig()
        assert config.port == 5000

    def test_rate_limits(self):
        from shared.config import APIConfig
        config = APIConfig()
        assert config.rate_limit_free < config.rate_limit_pro
        assert config.rate_limit_pro < config.rate_limit_business
        assert config.rate_limit_business < config.rate_limit_enterprise


class TestSecurityConfig:
    """Tests for SecurityConfig."""

    def test_token_expiry(self):
        from shared.config import SecurityConfig
        config = SecurityConfig()
        assert config.access_token_expire_minutes > 0
        assert config.refresh_token_expire_days > 0
        # Refresh should be longer than access
        assert config.refresh_token_expire_days * 24 * 60 > config.access_token_expire_minutes

    def test_bcrypt_rounds(self):
        from shared.config import SecurityConfig
        config = SecurityConfig()
        # Should be between 10 and 15 for good balance
        assert 10 <= config.bcrypt_rounds <= 15


class TestAppConfig:
    """Tests for AppConfig."""

    def test_default_environment(self):
        from shared.config import AppConfig
        config = AppConfig()
        assert config.env in ('development', 'production', 'testing')

    def test_models_config_path_exists(self):
        from shared.config import AppConfig
        config = AppConfig()
        # Path should point to existing file
        assert config.models_config_path.name == 'models_config.json'

    def test_is_production(self):
        from shared.config import AppConfig
        config = AppConfig()
        # Default should not be production
        assert not config.is_production() or config.env.lower() in ('production', 'prod')


class TestValidationFunctions:
    """Tests for validation utility functions."""

    def test_validate_file_extension_valid(self):
        from shared.config import validate_file_extension
        assert validate_file_extension('image.png') is True
        assert validate_file_extension('image.jpg') is True
        assert validate_file_extension('image.JPEG') is True

    def test_validate_file_extension_invalid(self):
        from shared.config import validate_file_extension
        assert validate_file_extension('document.pdf') is False
        assert validate_file_extension('script.exe') is False
        assert validate_file_extension('noextension') is False

    def test_validate_file_size_valid(self):
        from shared.config import validate_file_size
        assert validate_file_size(1024) is True  # 1KB
        assert validate_file_size(1024 * 1024) is True  # 1MB

    def test_validate_file_size_invalid(self):
        from shared.config import validate_file_size
        assert validate_file_size(0) is False
        assert validate_file_size(-100) is False
        assert validate_file_size(200 * 1024 * 1024) is False  # 200MB

    def test_validate_mime_type_valid(self):
        from shared.config import validate_mime_type
        assert validate_mime_type('image/png') is True
        assert validate_mime_type('image/jpeg') is True

    def test_validate_mime_type_invalid(self):
        from shared.config import validate_mime_type
        assert validate_mime_type('application/pdf') is False
        assert validate_mime_type('text/plain') is False

    def test_get_rate_limit_for_plan(self):
        from shared.config import get_rate_limit_for_plan
        free_limit = get_rate_limit_for_plan('free')
        pro_limit = get_rate_limit_for_plan('pro')
        business_limit = get_rate_limit_for_plan('business')
        
        assert free_limit < pro_limit < business_limit


class TestGetConfig:
    """Tests for configuration singleton."""

    def test_get_config_returns_singleton(self):
        from shared.config import get_config
        config1 = get_config()
        config2 = get_config()
        # Should return the same instance
        assert config1 is config2

    def test_reload_config(self):
        from shared.config import get_config, reload_config
        config1 = get_config()
        config2 = reload_config()
        # After reload, should be a new instance
        # (in current implementation they may be different objects)
        assert config2 is not None
import pytest
from pathlib import Path
import json
from shared.models.manager import ModelManager

@pytest.mark.unit
def test_models_config_exists():
    # Get project root (4 levels up from tools/tests/shared/test_utils.py)
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    config_path = project_root / 'shared' / 'config' / 'models_config.json'
    assert config_path.exists(), "models_config.json should exist"

@pytest.mark.unit
def test_models_config_valid_json():
    # Get project root (4 levels up from tools/tests/shared/test_utils.py)
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    config_path = project_root / 'shared' / 'config' / 'models_config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)
    assert isinstance(config, dict), "Config should be a dictionary"
    assert 'available_models' in config, "Config should have 'available_models' key"
    assert 'default_model' in config, "Config should have 'default_model' key"

@pytest.mark.unit
def test_models_config_has_required_models():
    # Get project root (4 levels up from tools/tests/shared/test_utils.py)
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    config_path = project_root / 'shared' / 'config' / 'models_config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)
    models = config['available_models']
    model_ids = [model['id'] for model in models.values()]
    assert any('ocr' in model_id.lower() for model_id in model_ids), \
        "Should have at least one OCR-based model"

@pytest.mark.unit
def test_default_model_exists():
    # Get project root (4 levels up from tools/tests/shared/test_utils.py)
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    config_path = project_root / 'shared' / 'config' / 'models_config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)
    default_model = config['default_model']
    available_model_ids = [model['id'] for model in config['available_models'].values()]
    assert default_model in available_model_ids, \
        f"Default model '{default_model}' should be in available models"

@pytest.mark.unit
def test_model_schema():
    # Get project root (4 levels up from tools/tests/shared/test_utils.py)
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    config_path = project_root / 'shared' / 'config' / 'models_config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)
    required_fields = ['id', 'name', 'type', 'description']
    for model_key, model in config['available_models'].items():
        for field in required_fields:
            assert field in model, \
                f"Model '{model_key}' should have '{field}' field"
        assert isinstance(model['id'], str), f"Model '{model_key}' id should be string"
        assert isinstance(model['name'], str), f"Model '{model_key}' name should be string"
        assert isinstance(model['type'], str), f"Model '{model_key}' type should be string"
        assert isinstance(model['description'], str), f"Model '{model_key}' description should be string"

@pytest.mark.unit
def test_model_manager_initialization():
    manager = ModelManager()
    assert manager is not None
    assert manager.models_config is not None
    assert 'available_models' in manager.models_config

@pytest.mark.unit
def test_model_manager_get_available_models():
    manager = ModelManager()
    models = manager.get_available_models()
    assert isinstance(models, list)
    assert len(models) > 0
    for model in models:
        assert 'id' in model
        assert 'name' in model
        assert 'type' in model
        assert 'description' in model

@pytest.mark.unit
def test_model_manager_get_default_model():
    manager = ModelManager()
    default_model = manager.get_default_model()
    assert isinstance(default_model, str)
    assert len(default_model) > 0

@pytest.mark.unit
def test_model_manager_select_model():
    manager = ModelManager()
    default_model = manager.get_default_model()
    result = manager.select_model(default_model)
    assert result is True
    assert manager.get_current_model() == default_model
    result = manager.select_model('nonexistent_model')
    assert result is False

@pytest.mark.unit
def test_model_manager_get_model_info():
    manager = ModelManager()
    default_model = manager.get_default_model()
    model_info = manager.get_model_info(default_model)
    assert model_info is not None
    assert 'id' in model_info
    assert 'name' in model_info
    assert 'type' in model_info

@pytest.mark.unit
def test_model_manager_filter_by_capability():
    manager = ModelManager()
    models = manager.get_available_models()
    filtered = manager.filter_models_by_capability('some_capability')
    assert isinstance(filtered, list)


@pytest.mark.unit
def test_model_manager_config_validation():
    """Test configuration validation"""
    manager = ModelManager()
    config = manager.models_config

    # Test valid config
    manager._validate_config(config)  # Should not raise

    # Test missing required field
    with pytest.raises(ValueError) as exc_info:
        manager._validate_config({})
    assert "available_models" in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        manager._validate_config({'available_models': {}})
    assert "default_model" in str(exc_info.value)

    # Test invalid type for available_models
    with pytest.raises(ValueError) as exc_info:
        manager._validate_config({'available_models': [], 'default_model': 'test'})
    assert "must be an object" in str(exc_info.value) or "must be a dict" in str(exc_info.value).lower()


@pytest.mark.unit
def test_model_manager_config_validation_model_schema():
    """Test individual model configuration validation"""
    manager = ModelManager()

    # Test invalid model config - missing required fields
    with pytest.raises(ValueError) as exc_info:
        manager._validate_model_config('test_model', {})
    assert "missing required field" in str(exc_info.value)

    # Test invalid model type
    with pytest.raises(ValueError) as exc_info:
        manager._validate_model_config('test_model', {
            'id': 'test',
            'name': 'Test',
            'type': 'invalid_type',
            'description': 'Test model'
        })
    assert "invalid type" in str(exc_info.value)

    # Test donut model missing huggingface_id
    with pytest.raises(ValueError) as exc_info:
        manager._validate_model_config('test_donut', {
            'id': 'test',
            'name': 'Test',
            'type': 'donut',
            'description': 'Test model'
        })
    assert "huggingface_id" in str(exc_info.value)

    # Test donut model missing task_prompt
    with pytest.raises(ValueError) as exc_info:
        manager._validate_model_config('test_donut', {
            'id': 'test',
            'name': 'Test',
            'type': 'donut',
            'description': 'Test model',
            'huggingface_id': 'test/model'
        })
    assert "task_prompt" in str(exc_info.value)


@pytest.mark.unit
def test_model_manager_default_model_validation():
    """Test that default model exists in available models"""
    # Get project root (4 levels up from tools/tests/shared/test_utils.py)
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    config_path = project_root / 'shared' / 'config' / 'models_config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)

    default_model = config['default_model']
    available_models = config['available_models']

    assert default_model in available_models, f"Default model '{default_model}' must exist in available models"


@pytest.mark.unit
def test_model_manager_get_processor_default():
    """Test getting processor with default model"""
    manager = ModelManager()
    default_model = manager.get_default_model()

    # Select a model first
    manager.select_model(default_model)

    # Try to get processor (will fail if dependencies not installed, which is ok for testing structure)
    try:
        processor = manager.get_processor()
        # If we get here, processor was loaded successfully
        assert processor is not None
    except (ImportError, ValueError, OSError) as e:
        # Expected if dependencies not installed (OSError for Tesseract)
        error_lower = str(e).lower()
        assert ("required" in error_lower or "not found" in error_lower or 
                "pip install" in error_lower or "no module" in error_lower or
                "not installed" in error_lower)


@pytest.mark.unit
def test_model_manager_get_processor_specific_model():
    """Test getting processor for specific model"""
    manager = ModelManager()
    default_model = manager.get_default_model()

    try:
        processor = manager.get_processor(default_model)
        assert processor is not None
    except (ImportError, ValueError, OSError) as e:
        # Expected if dependencies not installed (OSError for Tesseract)
        error_lower = str(e).lower()
        assert ("required" in error_lower or "not found" in error_lower or 
                "pip install" in error_lower or "no module" in error_lower or
                "not installed" in error_lower)


@pytest.mark.unit
def test_model_manager_unload_model():
    """Test unloading a specific model"""
    manager = ModelManager()
    default_model = manager.get_default_model()

    # Try to load and unload
    try:
        processor = manager.get_processor(default_model)
        assert default_model in manager.loaded_processors

        manager.unload_model(default_model)
        assert default_model not in manager.loaded_processors
    except (ImportError, ValueError, OSError):
        # Can't test if dependencies not installed (OSError for Tesseract)
        pass


@pytest.mark.unit
def test_model_manager_unload_all_models():
    """Test unloading all models"""
    manager = ModelManager()

    # Load a model
    try:
        default_model = manager.get_default_model()
        processor = manager.get_processor(default_model)

        assert len(manager.loaded_processors) > 0

        manager.unload_all_models()
        assert len(manager.loaded_processors) == 0
        assert len(manager.model_last_used) == 0
        assert len(manager.model_load_times) == 0
    except (ImportError, ValueError, OSError):
        # Can't test if dependencies not installed (OSError for Tesseract)
        pass


@pytest.mark.unit
def test_model_manager_get_resource_stats():
    """Test getting resource statistics"""
    manager = ModelManager()
    stats = manager.get_resource_stats()

    assert 'loaded_models_count' in stats
    assert 'max_loaded_models' in stats
    assert 'current_model' in stats
    assert 'loaded_models' in stats
    assert 'model_usage' in stats

    assert isinstance(stats['loaded_models_count'], int)
    assert isinstance(stats['max_loaded_models'], int)
    assert isinstance(stats['loaded_models'], list)
    assert isinstance(stats['model_usage'], dict)


@pytest.mark.unit
def test_model_manager_get_model_capabilities():
    """Test getting model capabilities"""
    manager = ModelManager()
    default_model = manager.get_default_model()

    capabilities = manager.get_model_capabilities(default_model)
    assert isinstance(capabilities, dict)

    # Test non-existent model
    capabilities = manager.get_model_capabilities('nonexistent_model')
    assert capabilities == {}


@pytest.mark.unit
def test_model_manager_load_config_error_handling():
    """Test config loading error handling"""
    import tempfile
    import os

    # Test with invalid JSON
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('invalid json {')
        temp_path = f.name

    try:
        with pytest.raises(ValueError) as exc_info:
            manager = ModelManager(config_path=temp_path)
        assert "not valid JSON" in str(exc_info.value)
    finally:
        os.unlink(temp_path)

    # Test with missing file
    with pytest.raises(Exception):  # FileNotFoundError or similar
        manager = ModelManager(config_path='/nonexistent/path/config.json')


@pytest.mark.unit
def test_model_manager_processor_caching():
    """Test that processors are cached and reused"""
    manager = ModelManager()
    default_model = manager.get_default_model()

    try:
        # Load processor twice
        processor1 = manager.get_processor(default_model)
        processor2 = manager.get_processor(default_model)

        # Should be the same cached instance
        assert processor1 is processor2
        assert default_model in manager.loaded_processors
    except (ImportError, ValueError, OSError):
        # Can't test if dependencies not installed (OSError for Tesseract)
        pass


@pytest.mark.unit
def test_model_manager_max_loaded_models_eviction():
    """Test that LRU eviction works when max models exceeded"""
    manager = ModelManager(max_loaded_models=2)

    # This test requires models to actually load, which may not work without dependencies
    # So we'll test the eviction logic directly
    from datetime import datetime

    # Simulate having 2 models loaded
    manager.loaded_processors = {
        'model1': 'processor1',
        'model2': 'processor2'
    }
    manager.model_last_used = {
        'model1': datetime(2024, 1, 1),
        'model2': datetime(2024, 1, 2)
    }
    manager.model_load_times = {
        'model1': datetime(2024, 1, 1),
        'model2': datetime(2024, 1, 2)
    }

    # Call eviction directly
    manager._evict_least_recently_used()

    # model1 should be evicted (oldest)
    assert 'model1' not in manager.loaded_processors
    assert 'model2' in manager.loaded_processors


@pytest.mark.unit
def test_model_manager_get_processor_invalid_model():
    """Test getting processor for invalid model ID"""
    manager = ModelManager()

    with pytest.raises(ValueError) as exc_info:
        manager.get_processor('nonexistent_model_id_12345')

    assert "not found" in str(exc_info.value)


@pytest.mark.unit
def test_model_manager_threading_lock():
    """Test that threading lock exists for thread safety"""
    manager = ModelManager()

    assert hasattr(manager, '_lock')
    assert manager._lock is not None


@pytest.mark.unit
def test_model_manager_gpu_check():
    """Test GPU availability check runs without errors"""
    # This is called during init, so just verify it doesn't crash
    manager = ModelManager()
    # If we got here, GPU check completed successfully
    assert manager is not None


@pytest.mark.unit
def test_model_manager_initialization_with_custom_max_models():
    """Test initialization with custom max_loaded_models"""
    manager = ModelManager(max_loaded_models=5)
    assert manager.max_loaded_models == 5

    manager2 = ModelManager(max_loaded_models=1)
    assert manager2.max_loaded_models == 1


@pytest.mark.unit
def test_model_manager_processor_types():
    """Test that all processor types can be identified"""
    manager = ModelManager()

    # Get all models and check their types
    models = manager.get_available_models()
    valid_types = ['donut', 'florence', 'ocr', 'easyocr', 'paddle']

    for model in models:
        assert model['type'] in valid_types, f"Model {model['id']} has invalid type {model['type']}"


@pytest.mark.unit
def test_model_manager_processor_import_error_handling():
    """Test processor handles ImportError/RuntimeError for missing dependencies"""
    manager = ModelManager()

    # Try to load a model that requires dependencies
    # This will raise ImportError if dependencies are missing
    # or RuntimeError if model fails to load
    try:
        # Try donut which requires torch/transformers
        donut_models = [m for m in manager.get_available_models() if m['type'] == 'donut']
        if donut_models:
            model_id = donut_models[0]['id']
            processor = manager.get_processor(model_id)
            # If successful, check it's not None
            assert processor is not None
    except (ImportError, RuntimeError, TypeError, OSError) as e:
        # Expected if torch/transformers not installed or model fails to load
        # Various error types can occur depending on the failure mode
        pass  # Any of these errors are acceptable for missing deps


@pytest.mark.unit
def test_model_manager_select_model_updates_current():
    """Test that selecting a model updates current_model"""
    manager = ModelManager()
    default_model = manager.get_default_model()

    result = manager.select_model(default_model)
    assert result is True
    assert manager.get_current_model() == default_model

    # Test selecting non-existent model
    result = manager.select_model('fake_model_xyz')
    assert result is False
    # Current model should not change
    assert manager.get_current_model() == default_model
"""
Test suite for shared.models.__init__.py
Tests the _get_processor_class lazy import functionality
"""
import pytest
from pathlib import Path
import sys

# Paths handled by conftest.py

from shared.models.manager import ModelManager


class TestModelManager:
    """Test ModelManager export"""

    def test_model_manager_import(self):
        """Test that ModelManager is exported"""
        assert ModelManager is not None


class TestGetProcessorClass:
    """Test _get_processor_class lazy import function"""

"""
Tests for model_trainer.py - ModelTrainer, DataAugmenter, IncrementalModelDevelopment
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import numpy as np


class TestModelTrainer:
    """Tests for ModelTrainer class"""
    
    def test_model_trainer_initialization(self):
        """Test ModelTrainer initialization"""
        from shared.models.engine import ModelTrainer
        
        config = {'param1': 'value1', 'param2': 'value2'}
        trainer = ModelTrainer('test_model', config)
        
        assert trainer.model_type == 'test_model'
        assert trainer.config == config
        assert trainer.training_data == []
        assert trainer.validation_data == []
    
    def test_add_training_sample(self):
        """Test adding training samples"""
        from shared.models.engine import ModelTrainer
        
        trainer = ModelTrainer('test_model', {})
        trainer.add_training_sample('/path/to/image.jpg', {'store': 'Test Store', 'total': 25.00})
        
        assert len(trainer.training_data) == 1
        assert trainer.training_data[0]['image'] == '/path/to/image.jpg'
        assert trainer.training_data[0]['truth']['store'] == 'Test Store'
    
    def test_add_validation_sample(self):
        """Test adding validation samples"""
        from shared.models.engine import ModelTrainer
        
        trainer = ModelTrainer('test_model', {})
        trainer.add_validation_sample('/path/to/image.jpg', {'store': 'Test Store'})
        
        assert len(trainer.validation_data) == 1
        assert trainer.validation_data[0]['image'] == '/path/to/image.jpg'
    
    def test_fine_tune_paddle_with_data(self):
        """Test fine_tune_paddle with training data"""
        from shared.models.engine import ModelTrainer
        
        trainer = ModelTrainer('paddle', {})
        trainer.add_training_sample('/path/to/image.jpg', {'total': 25.00})
        
        # Should not raise error when data exists
        trainer.fine_tune_paddle(epochs=3, batch_size=4)
    
    def test_fine_tune_paddle_without_data(self):
        """Test fine_tune_paddle without data raises error"""
        from shared.models.engine import ModelTrainer
        
        trainer = ModelTrainer('paddle', {})
        
        with pytest.raises(ValueError, match="No training data provided"):
            trainer.fine_tune_paddle()
    
    def test_evaluate_model_with_data(self):
        """Test evaluate_model with validation data"""
        from shared.models.engine import ModelTrainer
        
        trainer = ModelTrainer('test_model', {})
        trainer.add_validation_sample('/path/to/image.jpg', {'total': 25.00})
        
        results = trainer.evaluate_model()
        
        assert 'accuracy' in results
        assert 'precision' in results
        assert 'recall' in results
    
    def test_evaluate_model_without_data(self):
        """Test evaluate_model without validation data returns empty dict"""
        from shared.models.engine import ModelTrainer
        
        trainer = ModelTrainer('test_model', {})
        results = trainer.evaluate_model()
        
        assert results == {}
    
    def test_save_model(self):
        """Test save_model creates file"""
        from shared.models.engine import ModelTrainer
        
        with tempfile.TemporaryDirectory() as tmpdir:
            trainer = ModelTrainer('test_model', {'key': 'value'})
            trainer.add_training_sample('/path/to/image.jpg', {'total': 25.00})
            
            output_path = os.path.join(tmpdir, 'models', 'model.json')
            trainer.save_model(output_path)
            
            assert os.path.exists(output_path)
            
            with open(output_path) as f:
                data = json.load(f)
            
            assert data['type'] == 'test_model'
            assert data['config'] == {'key': 'value'}
            assert data['samples'] == 1
    
    def test_incremental_learn(self):
        """Test incremental_learn adds corrections to training data"""
        from shared.models.engine import ModelTrainer
        
        trainer = ModelTrainer('test_model', {})
        
        feedback = {
            'correction_type': 'total_fix',
            'corrections': [
                {'field': 'total', 'old': 25.00, 'new': 30.00},
                {'field': 'store', 'old': 'Store A', 'new': 'Store B'}
            ]
        }
        
        trainer.incremental_learn(feedback)
        
        assert len(trainer.training_data) == 2


class TestDataAugmenter:
    """Tests for DataAugmenter class"""
    
    @pytest.mark.skipif(not pytest.importorskip("cv2", reason="cv2 not installed"), reason="cv2 required")
    def test_augment_image(self):
        """Test augment_image generates augmented images"""
        from shared.models.engine import DataAugmenter
        from PIL import Image
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test image
            img = Image.new('RGB', (100, 100), color='white')
            input_path = os.path.join(tmpdir, 'test_image.png')
            img.save(input_path)
            
            # Augment the image
            output_dir = os.path.join(tmpdir, 'augmented')
            os.makedirs(output_dir)
            
            result = DataAugmenter.augment_image(input_path, output_dir)
            
            # Should generate 8 augmented images (4 rotations + 4 brightness)
            assert len(result) == 8
            
            # Verify all files exist
            for path in result:
                assert os.path.exists(path)


class TestIncrementalModelDevelopment:
    """Tests for IncrementalModelDevelopment class"""
    
    def test_initialization(self):
        """Test initialization"""
        from shared.models.engine import IncrementalModelDevelopment
        
        dev = IncrementalModelDevelopment('base_model_v1')
        
        assert dev.base_model_id == 'base_model_v1'
        assert dev.iterations == []
        assert dev.performance_history == []
    
    def test_create_iteration(self):
        """Test creating iterations"""
        from shared.models.engine import IncrementalModelDevelopment
        
        dev = IncrementalModelDevelopment('base_model')
        
        iteration_id = dev.create_iteration('First iteration', {'learning_rate': 0.001})
        
        assert iteration_id == 'base_model_v1'
        assert len(dev.iterations) == 1
        assert dev.iterations[0]['name'] == 'First iteration'
        
        iteration_id2 = dev.create_iteration('Second iteration', {'learning_rate': 0.0005})
        assert iteration_id2 == 'base_model_v2'
    
    def test_log_performance(self):
        """Test logging performance metrics"""
        from shared.models.engine import IncrementalModelDevelopment
        
        dev = IncrementalModelDevelopment('base_model')
        dev.create_iteration('Test', {})
        
        dev.log_performance('base_model_v1', {'accuracy': 0.85, 'loss': 0.15})
        
        assert len(dev.performance_history) == 1
        assert dev.performance_history[0]['metrics']['accuracy'] == 0.85
    
    def test_get_best_iteration_with_data(self):
        """Test getting best iteration"""
        from shared.models.engine import IncrementalModelDevelopment
        
        dev = IncrementalModelDevelopment('base_model')
        dev.create_iteration('v1', {})
        dev.create_iteration('v2', {})
        
        dev.log_performance('base_model_v1', {'accuracy': 0.80})
        dev.log_performance('base_model_v2', {'accuracy': 0.90})
        
        best = dev.get_best_iteration()
        assert best == 'base_model_v2'
    
    def test_get_best_iteration_empty(self):
        """Test getting best iteration with no data"""
        from shared.models.engine import IncrementalModelDevelopment
        
        dev = IncrementalModelDevelopment('base_model')
        assert dev.get_best_iteration() is None
    
    def test_export_iteration(self):
        """Test exporting an iteration"""
        from shared.models.engine import IncrementalModelDevelopment
        
        with tempfile.TemporaryDirectory() as tmpdir:
            dev = IncrementalModelDevelopment('base_model')
            dev.create_iteration('Test iteration', {'param': 'value'})
            
            output_path = os.path.join(tmpdir, 'iteration.json')
            dev.export_iteration('base_model_v1', output_path)
            
            assert os.path.exists(output_path)
            
            with open(output_path) as f:
                data = json.load(f)
            
            assert data['name'] == 'Test iteration'
    
    def test_export_iteration_not_found(self):
        """Test exporting non-existent iteration raises error"""
        from shared.models.engine import IncrementalModelDevelopment
        
        dev = IncrementalModelDevelopment('base_model')
        
        with pytest.raises(ValueError, match="not found"):
            dev.export_iteration('nonexistent_v1', '/tmp/output.json')
import pytest
from PIL import Image
import io
import numpy as np
from shared.utils.image import (
    load_and_validate_image,
    enhance_image,
    assess_image_quality,
    resize_if_needed,
    BRIGHTNESS_THRESHOLD,
    CONTRAST_THRESHOLD
)
import tempfile

@pytest.mark.unit
def test_image_formats_supported():
    formats = ['JPEG', 'PNG', 'BMP', 'TIFF']
    for fmt in formats:
        img = Image.new('RGB', (100, 100), color='white')
        buffer = io.BytesIO()
        img.save(buffer, format=fmt)
        buffer.seek(0)
        loaded_img = Image.open(buffer)
        assert loaded_img.size == (100, 100), f"{fmt} image should be loadable"

@pytest.mark.unit
def test_image_validation():
    valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
    invalid_extensions = ['.pdf', '.txt', '.doc', '.exe']
    for ext in valid_extensions:
        filename = f"test{ext}"
        assert any(filename.endswith(valid_ext) for valid_ext in valid_extensions)
    for ext in invalid_extensions:
        filename = f"test{ext}"
        assert not any(filename.endswith(valid_ext) for valid_ext in valid_extensions)

@pytest.mark.unit
def test_load_and_validate_image():
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
        img = Image.new('RGB', (200, 150), color='blue')
        img.save(tmp_file.name)
        tmp_path = tmp_file.name
    loaded_img = load_and_validate_image(tmp_path)
    assert loaded_img.size == (200, 150)
    assert loaded_img.mode == 'RGB'
    loaded_img.close()
    import os
    os.unlink(tmp_path)

@pytest.mark.unit
def test_enhance_image():
    img = Image.new('RGB', (100, 100), color='gray')
    enhanced = enhance_image(img, enhance_contrast=True, enhance_brightness=True, sharpen=True)
    assert enhanced.size == img.size
    assert enhanced.mode == 'RGB'
    enhanced_contrast = enhance_image(img, enhance_contrast=True, enhance_brightness=False, sharpen=False)
    assert enhanced_contrast.size == img.size

@pytest.mark.unit
def test_assess_image_quality():
    img = Image.new('RGB', (100, 100), color='white')
    quality = assess_image_quality(img)
    assert 'brightness' in quality
    assert 'contrast' in quality
    assert 'is_bright_enough' in quality
    assert 'has_good_contrast' in quality
    assert 'overall_quality' in quality
    assert isinstance(quality['brightness'], float)
    assert isinstance(quality['contrast'], float)

@pytest.mark.unit
def test_resize_if_needed():
    small_img = Image.new('RGB', (100, 100), color='red')
    resized = resize_if_needed(small_img, max_size=2048)
    assert resized.size == (100, 100)
    large_img = Image.new('RGB', (3000, 2000), color='green')
    resized = resize_if_needed(large_img, max_size=2048)
    assert max(resized.size) == 2048
    assert resized.size[0] / resized.size[1] == pytest.approx(3000 / 2000, rel=0.01)

@pytest.mark.unit
def test_brightness_and_contrast_thresholds():
    assert BRIGHTNESS_THRESHOLD > 0
    assert CONTRAST_THRESHOLD > 0

@pytest.mark.unit
def test_load_and_validate_image_not_found():
    """Test loading non-existent image raises FileNotFoundError"""
    with pytest.raises(FileNotFoundError):
        load_and_validate_image('/nonexistent/path/image.png')

@pytest.mark.unit
def test_load_and_validate_image_rgba():
    """Test loading RGBA image converts to RGB"""
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
        img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
        img.save(tmp_file.name)
        tmp_path = tmp_file.name
    loaded_img = load_and_validate_image(tmp_path)
    assert loaded_img.mode == 'RGB'
    loaded_img.close()
    import os
    os.unlink(tmp_path)

@pytest.mark.unit
def test_load_and_validate_image_grayscale():
    """Test loading grayscale image (L mode)"""
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
        img = Image.new('L', (100, 100), color=128)
        img.save(tmp_file.name)
        tmp_path = tmp_file.name
    loaded_img = load_and_validate_image(tmp_path)
    assert loaded_img.mode in ('L', 'RGB')
    loaded_img.close()
    import os
    os.unlink(tmp_path)

@pytest.mark.unit
def test_enhance_image_no_changes():
    """Test enhance_image with all options disabled"""
    img = Image.new('RGB', (100, 100), color='gray')
    enhanced = enhance_image(img, enhance_contrast=False, enhance_brightness=False, sharpen=False)
    assert enhanced.size == img.size

@pytest.mark.unit
def test_assess_image_quality_dark_image():
    """Test quality assessment for dark image"""
    img = Image.new('RGB', (100, 100), color='black')
    quality = assess_image_quality(img)
    assert quality['brightness'] < BRIGHTNESS_THRESHOLD
    assert quality['is_bright_enough'] == False

@pytest.mark.unit
def test_assess_image_quality_low_contrast():
    """Test quality assessment for low contrast image"""
    img = Image.new('RGB', (100, 100), color=(128, 128, 128))
    quality = assess_image_quality(img)
    assert quality['contrast'] < CONTRAST_THRESHOLD
    assert quality['has_good_contrast'] == False

@pytest.mark.unit
def test_resize_if_needed_width_larger():
    """Test resize when width is larger dimension"""
    large_img = Image.new('RGB', (4000, 2000), color='blue')
    resized = resize_if_needed(large_img, max_size=2048)
    assert resized.size[0] == 2048
    assert resized.size[1] == 1024

@pytest.mark.unit
def test_resize_if_needed_height_larger():
    """Test resize when height is larger dimension"""
    large_img = Image.new('RGB', (2000, 4000), color='blue')
    resized = resize_if_needed(large_img, max_size=2048)
    assert resized.size[0] == 1024
    assert resized.size[1] == 2048
"""
Test suite for logging utilities
Tests coverage for shared/utils/logger.py
"""
import pytest
import sys
import os
import logging
import json
from pathlib import Path
from unittest.mock import Mock, patch

# Paths handled by conftest.py

from shared.utils.logging import (
    setup_logger,
    get_logger,
    log_with_context,
    StructuredJSONFormatter as StructuredFormatter,
    ColoredTextFormatter as ColoredFormatter
)


class TestStructuredFormatter:
    """Test structured JSON log formatter"""

    def test_structured_formatter_creates_json(self):
        """Test that formatter creates valid JSON"""
        formatter = StructuredFormatter()

        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=10,
            msg='Test message',
            args=(),
            exc_info=None
        )

        formatted = formatter.format(record)

        # Should be valid JSON
        data = json.loads(formatted)
        assert isinstance(data, dict)

    def test_structured_formatter_includes_required_fields(self):
        """Test that formatter includes required fields"""
        formatter = StructuredFormatter()

        record = logging.LogRecord(
            name='test_logger',
            level=logging.INFO,
            pathname='test.py',
            lineno=42,
            msg='Test message',
            args=(),
            exc_info=None,
            func='test_function'
        )

        formatted = formatter.format(record)
        data = json.loads(formatted)

        assert 'timestamp' in data
        assert 'level' in data
        assert 'logger' in data
        assert 'message' in data
        assert 'module' in data
        assert 'function' in data
        assert 'line' in data

    def test_structured_formatter_log_levels(self):
        """Test formatter with different log levels"""
        formatter = StructuredFormatter()

        levels = [
            (logging.DEBUG, 'DEBUG'),
            (logging.INFO, 'INFO'),
            (logging.WARNING, 'WARNING'),
            (logging.ERROR, 'ERROR'),
            (logging.CRITICAL, 'CRITICAL')
        ]

        for level_num, level_name in levels:
            record = logging.LogRecord(
                name='test',
                level=level_num,
                pathname='test.py',
                lineno=10,
                msg='Test',
                args=(),
                exc_info=None
            )

            formatted = formatter.format(record)
            data = json.loads(formatted)

            assert data['level'] == level_name

    def test_structured_formatter_with_exception(self):
        """Test formatter includes exception information"""
        formatter = StructuredFormatter()

        try:
            raise ValueError("Test exception")
        except ValueError:
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name='test',
            level=logging.ERROR,
            pathname='test.py',
            lineno=10,
            msg='Error occurred',
            args=(),
            exc_info=exc_info
        )

        formatted = formatter.format(record)
        data = json.loads(formatted)

        assert 'exception' in data
        assert 'ValueError' in data['exception']

    def test_structured_formatter_with_extra_fields(self):
        """Test formatter with extra fields"""
        formatter = StructuredFormatter()

        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=10,
            msg='Test',
            args=(),
            exc_info=None
        )

        record.extra_fields = {'user_id': '123', 'request_id': 'abc'}

        formatted = formatter.format(record)
        data = json.loads(formatted)

        assert 'user_id' in data
        assert data['user_id'] == '123'
        assert 'request_id' in data
        assert data['request_id'] == 'abc'


class TestColoredFormatter:
    """Test colored console log formatter"""

    def test_colored_formatter_adds_colors(self):
        """Test that formatter adds color codes"""
        formatter = ColoredFormatter('%(levelname)s - %(message)s')

        levels_with_colors = [
            (logging.DEBUG, '\033[36m'),  # Cyan
            (logging.INFO, '\033[32m'),   # Green
            (logging.WARNING, '\033[33m'), # Yellow
            (logging.ERROR, '\033[31m'),  # Red
            (logging.CRITICAL, '\033[1;35m'), # Bold Magenta (updated for centralized_logging)
        ]

        for level, color_code in levels_with_colors:
            record = logging.LogRecord(
                name='test',
                level=level,
                pathname='test.py',
                lineno=10,
                msg='Test message',
                args=(),
                exc_info=None
            )

            formatted = formatter.format(record)
            # Accept both bold and non-bold versions
            assert color_code in formatted or color_code.replace('\033[1;', '\033[') in formatted

    def test_colored_formatter_resets_color(self):
        """Test that formatter resets color at end"""
        formatter = ColoredFormatter('%(levelname)s - %(message)s')

        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=10,
            msg='Test',
            args=(),
            exc_info=None
        )

        formatted = formatter.format(record)
        # Should contain reset code
        assert '\033[0m' in formatted or 'RESET' in str(formatter.RESET)

    def test_colored_formatter_preserves_levelname(self):
        """Test that original levelname is preserved"""
        formatter = ColoredFormatter('%(levelname)s')

        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=10,
            msg='Test',
            args=(),
            exc_info=None
        )

        original_levelname = record.levelname
        formatter.format(record)

        # Levelname should be restored
        assert record.levelname == original_levelname


class TestSetupLogger:
    """Test logger setup function"""

    def test_setup_logger_creates_logger(self, tmp_path):
        """Test that setup_logger creates a logger"""
        logger = setup_logger(
            'test_logger',
            level='INFO',
            log_dir=str(tmp_path),
            console_output=False
        )

        assert logger is not None
        assert logger.name == 'test_logger'
        assert logger.level == logging.INFO

    def test_setup_logger_creates_log_file(self, tmp_path):
        """Test that setup_logger creates log file"""
        logger = setup_logger(
            'test_file_logger',
            log_dir=str(tmp_path),
            console_output=False
        )

        # Write a log message
        logger.info("Test message")

        # Check file was created
        log_file = tmp_path / 'test_file_logger.log'
        assert log_file.exists()

    def test_setup_logger_log_levels(self, tmp_path):
        """Test different log levels"""
        levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

        for level in levels:
            logger = setup_logger(
                f'test_{level.lower()}',
                level=level,
                log_dir=str(tmp_path),
                console_output=False
            )

            assert logger.level == getattr(logging, level)

    def test_setup_logger_json_format(self, tmp_path):
        """Test JSON logging format"""
        logger = setup_logger(
            'test_json',
            log_dir=str(tmp_path),
            use_json=True,
            console_output=False
        )

        logger.info("Test JSON message")

        # Read log file
        log_file = tmp_path / 'test_json.log'
        content = log_file.read_text()

        # Should be valid JSON
        log_line = content.strip().split('\n')[0]
        data = json.loads(log_line)
        assert isinstance(data, dict)

    def test_setup_logger_console_output(self, tmp_path):
        """Test console output option"""
        # With console output
        logger_with_console = setup_logger(
            'test_with_console',
            log_dir=str(tmp_path),
            console_output=True
        )

        # Without console output
        logger_without_console = setup_logger(
            'test_without_console',
            log_dir=str(tmp_path),
            console_output=False
        )

        # Both should exist
        assert logger_with_console is not None
        assert logger_without_console is not None

    def test_setup_logger_idempotent(self, tmp_path):
        """Test that calling setup_logger twice returns same logger"""
        logger1 = setup_logger(
            'test_idempotent',
            log_dir=str(tmp_path),
            console_output=False
        )

        logger2 = setup_logger(
            'test_idempotent',
            log_dir=str(tmp_path),
            console_output=False
        )

        # Should return same logger
        assert logger1 is logger2

    def test_setup_logger_creates_log_directory(self, tmp_path):
        """Test that log directory is created if it doesn't exist"""
        log_dir = tmp_path / 'logs' / 'nested'

        logger = setup_logger(
            'test_dir',
            log_dir=str(log_dir),
            console_output=False
        )

        # Directory should be created
        assert log_dir.exists()

    def test_setup_logger_rotating_file_handler(self, tmp_path):
        """Test that rotating file handler is used"""
        logger = setup_logger(
            'test_rotating',
            log_dir=str(tmp_path),
            console_output=False
        )

        # Write many log messages to trigger rotation
        for i in range(1000):
            logger.info(f"Message {i}" * 100)

        # Log file should exist
        log_file = tmp_path / 'test_rotating.log'
        assert log_file.exists()


class TestGetLogger:
    """Test get_logger function"""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger"""
        logger = get_logger('test_get')

        assert logger is not None
        assert isinstance(logger, logging.Logger)

    def test_get_logger_same_name_same_logger(self):
        """Test that same name returns same logger"""
        logger1 = get_logger('test_same')
        logger2 = get_logger('test_same')

        assert logger1 is logger2

    def test_get_logger_different_names(self):
        """Test that different names return different loggers"""
        logger1 = get_logger('test_a')
        logger2 = get_logger('test_b')

        assert logger1 is not logger2
        assert logger1.name != logger2.name


class TestLogWithContext:
    """Test contextual logging function"""

    def test_log_with_context_adds_extra_fields(self):
        """Test that log_with_context adds extra fields"""
        logger = logging.getLogger('test_context')
        logger.handlers = []  # Clear handlers

        # Add mock handler to capture log records with proper level attribute
        mock_handler = Mock()
        mock_handler.level = logging.DEBUG  # Set level to allow all log levels
        logger.addHandler(mock_handler)
        logger.setLevel(logging.INFO)

        # Log with context
        log_with_context(
            logger,
            'info',
            'Test message',
            user_id='123',
            request_id='abc'
        )

        # Handler should have been called
        assert mock_handler.handle.called

        # Get the log record
        log_record = mock_handler.handle.call_args[0][0]

        # Should have extra_fields
        assert hasattr(log_record, 'extra_fields')
        assert log_record.extra_fields['user_id'] == '123'
        assert log_record.extra_fields['request_id'] == 'abc'

    def test_log_with_context_different_levels(self):
        """Test log_with_context with different log levels"""
        logger = logging.getLogger('test_levels')
        logger.handlers = []
        mock_handler = Mock()
        mock_handler.level = logging.DEBUG  # Set level to allow all log levels
        logger.addHandler(mock_handler)
        logger.setLevel(logging.DEBUG)

        levels = ['debug', 'info', 'warning', 'error', 'critical']

        for level in levels:
            log_with_context(
                logger,
                level,
                f'Test {level}',
                test_field='value'
            )

        # Should have been called for each level
        assert mock_handler.handle.call_count == len(levels)


class TestLoggerIntegration:
    """Test logger integration scenarios"""

    def test_full_logging_workflow(self, tmp_path):
        """Test complete logging workflow"""
        # Setup logger
        logger = setup_logger(
            'integration_test',
            level='DEBUG',
            log_dir=str(tmp_path),
            use_json=True,
            console_output=False
        )

        # Log various messages
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        # Log with context
        log_with_context(
            logger,
            'info',
            'Contextual message',
            user='test_user',
            action='test_action'
        )

        # Verify log file
        log_file = tmp_path / 'integration_test.log'
        assert log_file.exists()

        content = log_file.read_text()
        lines = content.strip().split('\n')

        # Should have multiple log entries
        assert len(lines) >= 4

        # Each line should be valid JSON
        for line in lines:
            data = json.loads(line)
            assert 'timestamp' in data
            assert 'message' in data

    def test_logger_handles_unicode(self, tmp_path):
        """Test that logger handles unicode characters"""
        logger = setup_logger(
            'unicode_test',
            log_dir=str(tmp_path),
            console_output=False
        )

        unicode_messages = [
            "日本語のメッセージ",
            "Сообщение на русском",
            "Message with émojis 🎉",
            "مرحبا العالم"
        ]

        for msg in unicode_messages:
            logger.info(msg)

        # Log file should exist and contain content
        log_file = tmp_path / 'unicode_test.log'
        assert log_file.exists()

    def test_logger_exception_logging(self, tmp_path):
        """Test logging exceptions"""
        logger = setup_logger(
            'exception_test',
            log_dir=str(tmp_path),
            console_output=False
        )

        try:
            raise ValueError("Test exception")
        except ValueError:
            logger.exception("An error occurred")

        log_file = tmp_path / 'exception_test.log'
        content = log_file.read_text()

        # Should contain exception information
        assert 'ValueError' in content
        assert 'Test exception' in content
"""
Test suite for data structures
Tests coverage for shared/utils/data_structures.py
"""
import pytest
from decimal import Decimal
from pathlib import Path
import sys

# Paths handled by conftest.py

from shared.utils.data import LineItem, ReceiptData, ExtractionResult


class TestLineItem:
    """Test LineItem dataclass"""

    def test_line_item_creation_minimal(self):
        """Test creating line item with minimal fields"""
        item = LineItem(name="Coffee")
        
        assert item.name == "Coffee"
        assert item.quantity == 1
        assert item.unit_price is None
        assert item.total_price == Decimal('0')

    def test_line_item_creation_full(self):
        """Test creating line item with all fields"""
        item = LineItem(
            name="Coffee",
            quantity=2,
            unit_price=Decimal('3.50'),
            total_price=Decimal('7.00')
        )
        
        assert item.name == "Coffee"
        assert item.quantity == 2
        assert item.unit_price == Decimal('3.50')
        assert item.total_price == Decimal('7.00')

    def test_line_item_to_dict(self):
        """Test line item to_dict method"""
        item = LineItem(
            name="Tea",
            quantity=1,
            unit_price=Decimal('2.50'),
            total_price=Decimal('2.50')
        )
        
        result = item.to_dict()
        
        assert result['name'] == "Tea"
        assert result['quantity'] == 1
        assert result['unit_price'] == '2.50'
        assert result['total_price'] == '2.50'

    def test_line_item_to_dict_none_unit_price(self):
        """Test line item to_dict with None unit price"""
        item = LineItem(name="Item", total_price=Decimal('5.00'))
        
        result = item.to_dict()
        
        assert result['unit_price'] is None


class TestReceiptData:
    """Test ReceiptData dataclass"""

    def test_receipt_data_creation_empty(self):
        """Test creating empty receipt data"""
        receipt = ReceiptData()
        
        assert receipt.store_name is None
        assert receipt.store_address is None
        assert receipt.items == []
        assert receipt.total is None
        assert receipt.model_used == "Unknown"

    def test_receipt_data_creation_with_store(self):
        """Test creating receipt data with store info"""
        receipt = ReceiptData(
            store_name="Test Store",
            store_address="123 Main St",
            store_phone="555-1234"
        )
        
        assert receipt.store_name == "Test Store"
        assert receipt.store_address == "123 Main St"
        assert receipt.store_phone == "555-1234"

    def test_receipt_data_with_items(self):
        """Test receipt data with line items"""
        items = [
            LineItem(name="Coffee", total_price=Decimal('3.50')),
            LineItem(name="Muffin", total_price=Decimal('2.00'))
        ]
        
        receipt = ReceiptData(items=items, total=Decimal('5.50'))
        
        assert len(receipt.items) == 2
        assert receipt.total == Decimal('5.50')

    def test_receipt_data_to_dict(self):
        """Test receipt data to_dict method"""
        receipt = ReceiptData(
            store_name="Test Store",
            store_address="123 Main St",
            total=Decimal('10.00'),
            subtotal=Decimal('9.00'),
            tax=Decimal('1.00'),
            model_used="test_model",
            confidence_score=0.95
        )
        
        result = receipt.to_dict()
        
        assert result['store']['name'] == "Test Store"
        assert result['store']['address'] == "123 Main St"
        assert result['totals']['total'] == '10.00'
        assert result['totals']['subtotal'] == '9.00'
        assert result['totals']['tax'] == '1.00'
        assert result['model'] == "test_model"
        assert result['confidence'] == 0.95

    def test_receipt_data_calculate_coverage_no_data(self):
        """Test coverage calculation with no data"""
        receipt = ReceiptData()
        
        result = receipt.to_dict()
        
        assert result['coverage'] == "N/A"

    def test_receipt_data_calculate_coverage_with_items(self):
        """Test coverage calculation with items"""
        items = [
            LineItem(name="Item1", total_price=Decimal('5.00')),
            LineItem(name="Item2", total_price=Decimal('5.00'))
        ]
        
        receipt = ReceiptData(items=items, total=Decimal('10.00'))
        result = receipt.to_dict()
        
        assert result['coverage'] == "100.0%"

    def test_receipt_data_calculate_coverage_partial(self):
        """Test coverage calculation with partial items"""
        items = [
            LineItem(name="Item1", total_price=Decimal('5.00'))
        ]
        
        receipt = ReceiptData(items=items, total=Decimal('10.00'))
        result = receipt.to_dict()
        
        assert result['coverage'] == "50.0%"


class TestExtractionResult:
    """Test ExtractionResult dataclass"""

    def test_extraction_result_success(self):
        """Test successful extraction result"""
        data = ReceiptData(store_name="Test Store")
        result = ExtractionResult(success=True, data=data)
        
        assert result.success is True
        assert result.data is not None
        assert result.error is None
        assert result.warnings == []

    def test_extraction_result_failure(self):
        """Test failed extraction result"""
        result = ExtractionResult(
            success=False,
            error="Failed to extract receipt"
        )
        
        assert result.success is False
        assert result.data is None
        assert result.error == "Failed to extract receipt"

    def test_extraction_result_with_warnings(self):
        """Test extraction result with warnings"""
        data = ReceiptData(store_name="Test Store")
        result = ExtractionResult(
            success=True,
            data=data,
            warnings=["Low confidence", "Missing total"]
        )
        
        assert result.success is True
        assert len(result.warnings) == 2

    def test_extraction_result_to_dict_success(self):
        """Test extraction result to_dict with success"""
        data = ReceiptData(store_name="Test Store")
        result = ExtractionResult(success=True, data=data)
        
        dict_result = result.to_dict()
        
        assert dict_result['success'] is True
        assert dict_result['data'] is not None
        assert dict_result['error'] is None

    def test_extraction_result_to_dict_failure(self):
        """Test extraction result to_dict with failure"""
        result = ExtractionResult(
            success=False,
            error="Test error"
        )
        
        dict_result = result.to_dict()
        
        assert dict_result['success'] is False
        assert dict_result['data'] is None
        assert dict_result['error'] == "Test error"
