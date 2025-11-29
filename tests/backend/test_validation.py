"""
Test suite for Pydantic validation schemas
Tests coverage for web-app/backend/validation/schemas.py
"""
import pytest
import sys
import os
from datetime import datetime, timedelta
from pydantic import ValidationError

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'web-app', 'backend'))

from validation.schemas import (
    UserRegisterSchema,
    UserLoginSchema,
    RefreshTokenSchema,
    PasswordResetRequestSchema,
    PasswordResetSchema,
    ReceiptUploadSchema,
    ReceiptUpdateSchema,
    APIKeyCreateSchema,
    FileUploadValidation,
    PaginationParams,
    DateRangeFilter,
    ReceiptSearchSchema
)


class TestUserRegisterSchema:
    """Test user registration validation"""

    def test_valid_user_registration(self):
        """Test valid user registration data"""
        data = {
            'email': 'test@example.com',
            'password': 'ValidPass123!',
            'full_name': 'Test User',
            'company': 'Test Company'
        }

        schema = UserRegisterSchema(**data)

        assert schema.email == 'test@example.com'
        assert schema.password == 'ValidPass123!'
        assert schema.full_name == 'Test User'
        assert schema.company == 'Test Company'

    def test_invalid_email_format(self):
        """Test that invalid email is rejected"""
        invalid_emails = [
            'not-an-email',
            'missing@domain',
            '@example.com',
            'user@',
            ''
        ]

        for email in invalid_emails:
            with pytest.raises(ValidationError):
                UserRegisterSchema(
                    email=email,
                    password='ValidPass123!'
                )

    def test_weak_password_validation(self):
        """Test password strength validation"""
        weak_passwords = [
            'short1!',  # Too short
            'nouppercase123!',  # No uppercase
            'NOLOWERCASE123!',  # No lowercase
            'NoNumbers!',  # No numbers
            'NoSpecial123',  # No special chars
        ]

        for password in weak_passwords:
            with pytest.raises(ValidationError):
                UserRegisterSchema(
                    email='test@example.com',
                    password=password
                )

    def test_disposable_email_blocked(self):
        """Test that disposable email domains are blocked"""
        disposable_emails = [
            'test@tempmail.com',
            'user@guerrillamail.com',
            'temp@10minutemail.com',
            'fake@mailinator.com',
            'throw@throwaway.email'
        ]

        for email in disposable_emails:
            with pytest.raises(ValidationError, match='[Dd]isposable'):
                UserRegisterSchema(
                    email=email,
                    password='ValidPass123!'
                )

    def test_email_case_normalization(self):
        """Test that email is normalized to lowercase"""
        schema = UserRegisterSchema(
            email='TeSt@ExAmPlE.CoM',
            password='ValidPass123!'
        )

        assert schema.email == 'test@example.com'

    def test_optional_fields(self):
        """Test that full_name and company are optional"""
        schema = UserRegisterSchema(
            email='test@example.com',
            password='ValidPass123!'
        )

        assert schema.full_name is None
        assert schema.company is None

    def test_password_minimum_length(self):
        """Test password minimum length requirement"""
        with pytest.raises(ValidationError):
            UserRegisterSchema(
                email='test@example.com',
                password='Short1!'  # 7 chars
            )

    def test_password_maximum_length(self):
        """Test password maximum length"""
        long_password = 'A' * 129 + '1!'

        with pytest.raises(ValidationError):
            UserRegisterSchema(
                email='test@example.com',
                password=long_password
            )


class TestUserLoginSchema:
    """Test user login validation"""

    def test_valid_login_schema(self):
        """Test valid login data"""
        schema = UserLoginSchema(
            email='test@example.com',
            password='any_password'
        )

        assert schema.email == 'test@example.com'
        assert schema.password == 'any_password'

    def test_login_missing_fields(self):
        """Test that missing fields are rejected"""
        with pytest.raises(ValidationError):
            UserLoginSchema(email='test@example.com')

        with pytest.raises(ValidationError):
            UserLoginSchema(password='password')

    def test_login_empty_password_rejected(self):
        """Test that empty password is rejected"""
        with pytest.raises(ValidationError):
            UserLoginSchema(
                email='test@example.com',
                password=''
            )

    def test_login_invalid_email(self):
        """Test that invalid email is rejected"""
        with pytest.raises(ValidationError):
            UserLoginSchema(
                email='not-an-email',
                password='password'
            )


class TestRefreshTokenSchema:
    """Test refresh token validation"""

    def test_valid_refresh_token(self):
        """Test valid refresh token"""
        schema = RefreshTokenSchema(
            refresh_token='valid_token_string_123'
        )

        assert schema.refresh_token == 'valid_token_string_123'

    def test_missing_refresh_token(self):
        """Test that missing token is rejected"""
        with pytest.raises(ValidationError):
            RefreshTokenSchema()


class TestPasswordResetRequestSchema:
    """Test password reset request validation"""

    def test_valid_password_reset_request(self):
        """Test valid password reset request"""
        schema = PasswordResetRequestSchema(
            email='test@example.com'
        )

        assert schema.email == 'test@example.com'

    def test_invalid_email_in_reset_request(self):
        """Test that invalid email is rejected"""
        with pytest.raises(ValidationError):
            PasswordResetRequestSchema(
                email='not-an-email'
            )


class TestPasswordResetSchema:
    """Test password reset validation"""

    def test_valid_password_reset(self):
        """Test valid password reset"""
        schema = PasswordResetSchema(
            token='reset_token_123',
            new_password='NewValidPass123!'
        )

        assert schema.token == 'reset_token_123'
        assert schema.new_password == 'NewValidPass123!'

    def test_password_reset_weak_password(self):
        """Test that weak password is rejected"""
        with pytest.raises(ValidationError):
            PasswordResetSchema(
                token='token',
                new_password='weak'
            )

    def test_password_reset_missing_uppercase(self):
        """Test that password without uppercase is rejected"""
        with pytest.raises(ValidationError):
            PasswordResetSchema(
                token='token',
                new_password='nouppercase123!'
            )

    def test_password_reset_missing_number(self):
        """Test that password without number is rejected"""
        with pytest.raises(ValidationError):
            PasswordResetSchema(
                token='token',
                new_password='NoNumbers!'
            )


class TestReceiptUploadSchema:
    """Test receipt upload validation"""

    def test_valid_receipt_upload(self):
        """Test valid receipt upload"""
        schema = ReceiptUploadSchema(
            model_id='easyocr'
        )

        assert schema.model_id == 'easyocr'

    def test_receipt_upload_optional_model(self):
        """Test that model_id is optional"""
        schema = ReceiptUploadSchema()

        assert schema.model_id is None

    def test_invalid_model_id_format(self):
        """Test that invalid model ID format is rejected"""
        invalid_ids = [
            'model with spaces',
            'model@special',
            'model#hash',
            'model/slash'
        ]

        for model_id in invalid_ids:
            with pytest.raises(ValidationError):
                ReceiptUploadSchema(model_id=model_id)

    def test_valid_model_id_formats(self):
        """Test various valid model ID formats"""
        valid_ids = [
            'easyocr',
            'donut-base',
            'paddle_ocr',
            'model123',
            'model-name_v2'
        ]

        for model_id in valid_ids:
            schema = ReceiptUploadSchema(model_id=model_id)
            assert schema.model_id == model_id

    def test_model_id_max_length(self):
        """Test model ID maximum length"""
        long_id = 'a' * 101

        with pytest.raises(ValidationError):
            ReceiptUploadSchema(model_id=long_id)


class TestReceiptUpdateSchema:
    """Test receipt update validation"""

    def test_valid_receipt_update(self):
        """Test valid receipt update"""
        schema = ReceiptUpdateSchema(
            extracted_data={'total': 25.99},
            status='completed'
        )

        assert schema.extracted_data == {'total': 25.99}
        assert schema.status == 'completed'

    def test_receipt_update_optional_fields(self):
        """Test that all fields are optional"""
        schema = ReceiptUpdateSchema()

        assert schema.extracted_data is None
        assert schema.status is None

    def test_validate_status_values(self):
        """Test that only valid status values are accepted"""
        valid_statuses = ['processing', 'completed', 'failed']

        for status in valid_statuses:
            schema = ReceiptUpdateSchema(status=status)
            assert schema.status == status

    def test_invalid_status_rejected(self):
        """Test that invalid status is rejected"""
        invalid_statuses = [
            'pending',
            'cancelled',
            'unknown'
        ]

        for status in invalid_statuses:
            with pytest.raises(ValidationError):
                ReceiptUpdateSchema(status=status)


class TestAPIKeyCreateSchema:
    """Test API key creation validation"""

    def test_valid_api_key_creation(self):
        """Test valid API key creation"""
        schema = APIKeyCreateSchema(
            name='My API Key'
        )

        assert schema.name == 'My API Key'

    def test_api_key_name_required(self):
        """Test that name is required"""
        with pytest.raises(ValidationError):
            APIKeyCreateSchema()

    def test_api_key_name_whitespace_normalization(self):
        """Test that whitespace is normalized"""
        schema = APIKeyCreateSchema(
            name='  Multiple   Spaces   Between  '
        )

        assert schema.name == 'Multiple Spaces Between'

    def test_api_key_empty_name_after_strip(self):
        """Test that empty name after stripping is rejected"""
        with pytest.raises(ValidationError):
            APIKeyCreateSchema(name='   ')

    def test_api_key_name_max_length(self):
        """Test API key name maximum length"""
        long_name = 'A' * 256

        with pytest.raises(ValidationError):
            APIKeyCreateSchema(name=long_name)


class TestFileUploadValidation:
    """Test file upload validation"""

    def test_validate_image_valid(self):
        """Test validating valid image"""
        is_valid, error = FileUploadValidation.validate_image(
            file_size=5 * 1024 * 1024,  # 5 MB
            mime_type='image/jpeg'
        )

        assert is_valid is True
        assert error is None

    def test_validate_image_too_large(self):
        """Test that file too large is rejected"""
        is_valid, error = FileUploadValidation.validate_image(
            file_size=15 * 1024 * 1024,  # 15 MB
            mime_type='image/jpeg'
        )

        assert is_valid is False
        assert 'exceeds maximum' in error

    def test_validate_image_invalid_mime_type(self):
        """Test that invalid MIME type is rejected"""
        invalid_types = [
            'application/pdf',
            'text/plain',
            'video/mp4',
            'application/zip'
        ]

        for mime_type in invalid_types:
            is_valid, error = FileUploadValidation.validate_image(
                file_size=1024,
                mime_type=mime_type
            )

            assert is_valid is False
            assert 'Invalid file type' in error

    def test_validate_image_all_allowed_types(self):
        """Test all allowed MIME types"""
        allowed_types = [
            'image/jpeg',
            'image/jpg',
            'image/png',
            'image/bmp',
            'image/tiff',
            'image/tif'
        ]

        for mime_type in allowed_types:
            is_valid, error = FileUploadValidation.validate_image(
                file_size=1024,
                mime_type=mime_type
            )

            assert is_valid is True
            assert error is None

    def test_file_size_limits(self):
        """Test file size limits"""
        assert FileUploadValidation.MAX_FILE_SIZE == 10 * 1024 * 1024  # 10 MB

    def test_allowed_mime_types_set(self):
        """Test allowed MIME types are properly defined"""
        assert len(FileUploadValidation.ALLOWED_MIME_TYPES) == 6
        assert 'image/jpeg' in FileUploadValidation.ALLOWED_MIME_TYPES


class TestPaginationParams:
    """Test pagination parameters"""

    def test_pagination_params_default(self):
        """Test default pagination parameters"""
        params = PaginationParams()

        assert params.page == 1
        assert params.per_page == 20

    def test_pagination_offset_calculation(self):
        """Test offset calculation"""
        params = PaginationParams(page=1, per_page=20)
        assert params.offset == 0

        params = PaginationParams(page=2, per_page=20)
        assert params.offset == 20

        params = PaginationParams(page=3, per_page=10)
        assert params.offset == 20

        params = PaginationParams(page=5, per_page=25)
        assert params.offset == 100

    def test_pagination_invalid_page(self):
        """Test that page < 1 is rejected"""
        with pytest.raises(ValidationError):
            PaginationParams(page=0)

        with pytest.raises(ValidationError):
            PaginationParams(page=-1)

    def test_pagination_invalid_per_page(self):
        """Test that invalid per_page is rejected"""
        with pytest.raises(ValidationError):
            PaginationParams(per_page=0)

        with pytest.raises(ValidationError):
            PaginationParams(per_page=-1)

        with pytest.raises(ValidationError):
            PaginationParams(per_page=101)  # Max is 100

    def test_pagination_custom_values(self):
        """Test custom pagination values"""
        params = PaginationParams(page=3, per_page=50)

        assert params.page == 3
        assert params.per_page == 50
        assert params.offset == 100


class TestDateRangeFilter:
    """Test date range filtering"""

    def test_date_range_valid(self):
        """Test valid date range"""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)

        filter_obj = DateRangeFilter(
            start_date=start,
            end_date=end
        )

        assert filter_obj.start_date == start
        assert filter_obj.end_date == end

    def test_date_range_end_before_start(self):
        """Test that end date before start date is rejected"""
        start = datetime(2024, 12, 31)
        end = datetime(2024, 1, 1)

        with pytest.raises(ValidationError, match='after start date'):
            DateRangeFilter(
                start_date=start,
                end_date=end
            )

    def test_date_range_optional_fields(self):
        """Test that both dates are optional"""
        filter_obj = DateRangeFilter()

        assert filter_obj.start_date is None
        assert filter_obj.end_date is None

    def test_date_range_only_start(self):
        """Test with only start date"""
        filter_obj = DateRangeFilter(
            start_date=datetime(2024, 1, 1)
        )

        assert filter_obj.start_date is not None
        assert filter_obj.end_date is None

    def test_date_range_only_end(self):
        """Test with only end date"""
        filter_obj = DateRangeFilter(
            end_date=datetime(2024, 12, 31)
        )

        assert filter_obj.start_date is None
        assert filter_obj.end_date is not None

    def test_date_range_same_date(self):
        """Test with same start and end date"""
        date = datetime(2024, 6, 15)

        filter_obj = DateRangeFilter(
            start_date=date,
            end_date=date
        )

        assert filter_obj.start_date == filter_obj.end_date


class TestReceiptSearchSchema:
    """Test receipt search validation"""

    def test_receipt_search_valid(self):
        """Test valid receipt search"""
        search = ReceiptSearchSchema(
            query='groceries',
            store_name='Walmart',
            min_amount=10.0,
            max_amount=100.0,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31)
        )

        assert search.query == 'groceries'
        assert search.store_name == 'Walmart'
        assert search.min_amount == 10.0
        assert search.max_amount == 100.0

    def test_receipt_search_all_optional(self):
        """Test that all search fields are optional"""
        search = ReceiptSearchSchema()

        assert search.query is None
        assert search.store_name is None
        assert search.min_amount is None
        assert search.max_amount is None
        assert search.start_date is None
        assert search.end_date is None

    def test_receipt_search_max_less_than_min(self):
        """Test that max amount less than min is rejected"""
        with pytest.raises(ValidationError, match='greater than minimum'):
            ReceiptSearchSchema(
                min_amount=100.0,
                max_amount=50.0
            )

    def test_receipt_search_negative_amounts(self):
        """Test that negative amounts are rejected"""
        with pytest.raises(ValidationError):
            ReceiptSearchSchema(min_amount=-10.0)

        with pytest.raises(ValidationError):
            ReceiptSearchSchema(max_amount=-50.0)

    def test_receipt_search_query_max_length(self):
        """Test query maximum length"""
        long_query = 'a' * 256

        with pytest.raises(ValidationError):
            ReceiptSearchSchema(query=long_query)

    def test_receipt_search_store_name_max_length(self):
        """Test store name maximum length"""
        long_name = 'a' * 256

        with pytest.raises(ValidationError):
            ReceiptSearchSchema(store_name=long_name)

    def test_receipt_search_equal_min_max(self):
        """Test with equal min and max amounts"""
        search = ReceiptSearchSchema(
            min_amount=50.0,
            max_amount=50.0
        )

        assert search.min_amount == search.max_amount

    def test_receipt_search_zero_amounts(self):
        """Test with zero amounts"""
        search = ReceiptSearchSchema(
            min_amount=0.0,
            max_amount=100.0
        )

        assert search.min_amount == 0.0


class TestSchemaSecurityConsiderations:
    """Test security aspects of validation schemas"""

    def test_sql_injection_attempts_sanitized(self):
        """Test that SQL injection attempts in strings are handled"""
        malicious_inputs = [
            "'; DROP TABLE users;--",
            "1' OR '1'='1",
            "admin'--",
        ]

        # These should either be rejected or properly escaped
        for malicious in malicious_inputs:
            # Should not crash, either validates or rejects
            try:
                ReceiptSearchSchema(query=malicious)
                ReceiptSearchSchema(store_name=malicious)
            except ValidationError:
                pass  # Rejection is acceptable

    def test_xss_attempts_in_text_fields(self):
        """Test that XSS attempts are handled"""
        xss_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
        ]

        # Should be accepted as plain text (will be escaped on output)
        for xss in xss_inputs:
            try:
                schema = ReceiptSearchSchema(query=xss)
                # Input is stored as-is, escaping happens on output
                assert xss in schema.query
            except ValidationError:
                pass  # Rejection is also acceptable

    def test_unicode_normalization(self):
        """Test that unicode is properly handled"""
        unicode_inputs = [
            "Café",
            "日本語",
            "Русский",
            "مرحبا"
        ]

        for text in unicode_inputs:
            schema = ReceiptSearchSchema(query=text)
            assert schema.query == text

    def test_email_validation_prevents_injection(self):
        """Test that email validation prevents header injection"""
        malicious_emails = [
            "test@example.com\nBcc:attacker@evil.com",
            "test@example.com\r\nBcc:attacker@evil.com",
            "test@example.com%0ABcc:attacker@evil.com"
        ]

        for email in malicious_emails:
            with pytest.raises(ValidationError):
                UserRegisterSchema(
                    email=email,
                    password='ValidPass123!'
                )

    def test_path_traversal_attempts(self):
        """Test that path traversal attempts are rejected"""
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "/etc/shadow"
        ]

        for path in malicious_paths:
            with pytest.raises(ValidationError):
                ReceiptUploadSchema(model_id=path)
