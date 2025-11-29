"""
Tests for the error handling module.
"""
import pytest
import time


class TestErrorCategory:
    """Tests for ErrorCategory enum."""

    def test_all_categories_exist(self):
        from shared.utils.errors import ErrorCategory
        assert hasattr(ErrorCategory, 'VALIDATION')
        assert hasattr(ErrorCategory, 'AUTHENTICATION')
        assert hasattr(ErrorCategory, 'AUTHORIZATION')
        assert hasattr(ErrorCategory, 'NOT_FOUND')
        assert hasattr(ErrorCategory, 'PROCESSING')
        assert hasattr(ErrorCategory, 'INTERNAL')


class TestErrorCode:
    """Tests for ErrorCode enum."""

    def test_validation_codes(self):
        from shared.utils.errors import ErrorCode
        assert ErrorCode.INVALID_INPUT.value.startswith('E1')
        assert ErrorCode.MISSING_REQUIRED_FIELD.value.startswith('E1')
        assert ErrorCode.FILE_TOO_LARGE.value.startswith('E1')

    def test_authentication_codes(self):
        from shared.utils.errors import ErrorCode
        assert ErrorCode.INVALID_CREDENTIALS.value.startswith('E2')
        assert ErrorCode.TOKEN_EXPIRED.value.startswith('E2')

    def test_internal_codes(self):
        from shared.utils.errors import ErrorCode
        assert ErrorCode.INTERNAL_ERROR.value.startswith('E9')


class TestReceiptExtractorError:
    """Tests for base ReceiptExtractorError."""

    def test_basic_error(self):
        from shared.utils.errors import ReceiptExtractorError, ErrorCode, ErrorCategory
        error = ReceiptExtractorError("Test error")
        assert error.message == "Test error"
        assert error.code == ErrorCode.INTERNAL_ERROR
        assert error.category == ErrorCategory.INTERNAL
        assert error.http_status == 500

    def test_custom_error(self):
        from shared.utils.errors import ReceiptExtractorError, ErrorCode, ErrorCategory
        error = ReceiptExtractorError(
            message="Custom error",
            code=ErrorCode.INVALID_INPUT,
            category=ErrorCategory.VALIDATION,
            http_status=400
        )
        assert error.http_status == 400
        assert error.code == ErrorCode.INVALID_INPUT

    def test_to_dict(self):
        from shared.utils.errors import ReceiptExtractorError
        error = ReceiptExtractorError("Test error", details={'field': 'value'})
        result = error.to_dict()
        
        assert result['success'] is False
        assert 'error' in result
        assert result['error']['message'] == "Test error"
        assert 'timestamp' in result['error']
        assert result['error']['details'] == {'field': 'value'}

    def test_to_dict_with_suggestion(self):
        from shared.utils.errors import ReceiptExtractorError
        error = ReceiptExtractorError(
            "Test error",
            suggestion="Try again later"
        )
        result = error.to_dict()
        assert result['error']['suggestion'] == "Try again later"


class TestValidationError:
    """Tests for ValidationError."""

    def test_default_values(self):
        from shared.utils.errors import ValidationError, ErrorCode, ErrorCategory
        error = ValidationError("Invalid input")
        assert error.http_status == 400
        assert error.category == ErrorCategory.VALIDATION

    def test_with_details(self):
        from shared.utils.errors import ValidationError
        error = ValidationError(
            "Invalid email",
            details={'field': 'email', 'reason': 'format'}
        )
        result = error.to_dict()
        assert result['error']['details']['field'] == 'email'


class TestAuthenticationError:
    """Tests for AuthenticationError."""

    def test_default_values(self):
        from shared.utils.errors import AuthenticationError, ErrorCategory
        error = AuthenticationError()
        assert error.http_status == 401
        assert error.category == ErrorCategory.AUTHENTICATION
        assert error.message == "Authentication required"


class TestAuthorizationError:
    """Tests for AuthorizationError."""

    def test_default_values(self):
        from shared.utils.errors import AuthorizationError, ErrorCategory
        error = AuthorizationError()
        assert error.http_status == 403
        assert error.category == ErrorCategory.AUTHORIZATION


class TestNotFoundError:
    """Tests for NotFoundError."""

    def test_default_values(self):
        from shared.utils.errors import NotFoundError, ErrorCategory
        error = NotFoundError()
        assert error.http_status == 404
        assert error.category == ErrorCategory.NOT_FOUND

    def test_with_resource_info(self):
        from shared.utils.errors import NotFoundError
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
        from shared.utils.errors import ProcessingError, ErrorCategory
        error = ProcessingError("OCR failed")
        assert error.http_status == 500
        assert error.category == ErrorCategory.PROCESSING


class TestRateLimitError:
    """Tests for RateLimitError."""

    def test_default_values(self):
        from shared.utils.errors import RateLimitError, ErrorCategory
        error = RateLimitError()
        assert error.http_status == 429
        assert error.category == ErrorCategory.RATE_LIMIT

    def test_with_retry_info(self):
        from shared.utils.errors import RateLimitError
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
        from shared.utils.errors import ExternalServiceError, ErrorCategory
        error = ExternalServiceError("Service unavailable")
        assert error.http_status == 503
        assert error.category == ErrorCategory.EXTERNAL_SERVICE

    def test_with_service_name(self):
        from shared.utils.errors import ExternalServiceError
        error = ExternalServiceError(
            message="Cloud storage error",
            service_name="AWS S3"
        )
        result = error.to_dict()
        assert result['error']['details']['service'] == 'AWS S3'


class TestErrorResponseUtilities:
    """Tests for error response utility functions."""

    def test_create_error_response(self):
        from shared.utils.errors import ValidationError, create_error_response
        error = ValidationError("Test error")
        response, status_code = create_error_response(error)
        
        assert status_code == 400
        assert response['success'] is False
        assert 'error' in response

    def test_create_simple_error_response(self):
        from shared.utils.errors import create_simple_error_response
        response, status_code = create_simple_error_response(
            "Simple error",
            status_code=500
        )
        
        assert status_code == 500
        assert response['success'] is False
        assert response['error']['message'] == "Simple error"

    def test_handle_exception_custom_error(self):
        from shared.utils.errors import ValidationError, handle_exception
        error = ValidationError("Test validation error")
        response, status_code = handle_exception(error)
        
        assert status_code == 400
        assert 'validation' in response['error']['type']

    def test_handle_exception_generic_error(self):
        from shared.utils.errors import handle_exception
        error = ValueError("Generic Python error")
        response, status_code = handle_exception(error)
        
        # Should return generic 500 error
        assert status_code == 500
        assert response['success'] is False
