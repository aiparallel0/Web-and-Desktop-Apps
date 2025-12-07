"""
Tests for input validation utilities module
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from shared.utils.validation import (
    validate_email,
    validate_uuid,
    sanitize_filename,
    check_file_size,
    check_file_extension,
    check_mime_type,
    validate_params,
    MAX_FILE_SIZES
)


class TestValidateEmail:
    """Tests for email validation"""
    
    def test_valid_emails(self):
        """Test validation of valid email addresses"""
        valid_emails = [
            "user@example.com",
            "test.user@domain.co.uk",
            "user+tag@example.com",
            "123@example.com"
        ]
        
        for email in valid_emails:
            assert validate_email(email), f"Email {email} should be valid"
    
    def test_invalid_emails(self):
        """Test validation of invalid email addresses"""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user@domain",
            "",
            None,
            123
        ]
        
        for email in invalid_emails:
            assert not validate_email(email), f"Email {email} should be invalid"


class TestValidateUUID:
    """Tests for UUID validation"""
    
    def test_valid_uuids(self):
        """Test validation of valid UUIDs"""
        valid_uuids = [
            "123e4567-e89b-12d3-a456-426614174000",
            "550e8400-e29b-41d4-a716-446655440000",
            "A987FBC9-4BED-3078-CF07-9141BA07C9F3"
        ]
        
        for uuid_str in valid_uuids:
            assert validate_uuid(uuid_str), f"UUID {uuid_str} should be valid"
    
    def test_invalid_uuids(self):
        """Test validation of invalid UUIDs"""
        invalid_uuids = [
            "not-a-uuid",
            "123e4567-e89b-12d3-a456",
            "123e4567e89b12d3a456426614174000",  # No dashes
            "",
            None,
            123
        ]
        
        for uuid_str in invalid_uuids:
            assert not validate_uuid(uuid_str), f"UUID {uuid_str} should be invalid"


class TestSanitizeFilename:
    """Tests for filename sanitization"""
    
    def test_basic_sanitization(self):
        """Test basic filename sanitization"""
        assert sanitize_filename("test.txt") == "test.txt"
        assert sanitize_filename("file name.pdf") == "file name.pdf"
    
    def test_remove_path_components(self):
        """Test removal of path components"""
        assert sanitize_filename("/path/to/file.txt") == "file.txt"
        assert sanitize_filename("..\\..\\file.txt") == "file.txt"
        assert sanitize_filename("../../../etc/passwd") == "etcpasswd"
    
    def test_remove_dangerous_characters(self):
        """Test removal of dangerous characters"""
        assert sanitize_filename("file<>?.txt") == "file.txt"
        assert sanitize_filename("file|*.txt") == "file.txt"
    
    def test_length_limit(self):
        """Test filename length limiting"""
        long_name = "a" * 300 + ".txt"
        result = sanitize_filename(long_name, max_length=255)
        assert len(result) <= 255
        assert result.endswith(".txt")
    
    def test_empty_filename(self):
        """Test handling of empty filename"""
        assert sanitize_filename("") == "unnamed"
        assert sanitize_filename(None) == "unnamed"


class TestCheckFileSize:
    """Tests for file size validation"""
    
    def test_valid_file_size(self):
        """Test validation of valid file sizes"""
        is_valid, error = check_file_size(1024, 'default')
        assert is_valid
        assert error is None
    
    def test_oversized_file(self):
        """Test validation of oversized files"""
        is_valid, error = check_file_size(MAX_FILE_SIZES['default'] + 1, 'default')
        assert not is_valid
        assert "exceeds maximum" in error
    
    def test_different_file_types(self):
        """Test different file type limits"""
        # Image files
        is_valid, error = check_file_size(50 * 1024 * 1024, 'image')
        assert is_valid
        
        # Document files
        is_valid, error = check_file_size(40 * 1024 * 1024, 'document')
        assert is_valid


class TestCheckFileExtension:
    """Tests for file extension validation"""
    
    def test_valid_extensions(self):
        """Test validation of valid extensions"""
        allowed = {'jpg', 'png', 'pdf'}
        
        is_valid, error = check_file_extension("file.jpg", allowed)
        assert is_valid
        
        is_valid, error = check_file_extension("file.PNG", allowed)
        assert is_valid  # Case-insensitive
    
    def test_invalid_extensions(self):
        """Test validation of invalid extensions"""
        allowed = {'jpg', 'png'}
        
        is_valid, error = check_file_extension("file.txt", allowed)
        assert not is_valid
        assert "not allowed" in error
    
    def test_no_extension(self):
        """Test handling of files without extension"""
        is_valid, error = check_file_extension("file", {'jpg'})
        assert not is_valid
        assert "no extension" in error.lower()


class TestCheckMimeType:
    """Tests for MIME type validation"""
    
    def test_valid_mime_types(self):
        """Test validation of valid MIME types"""
        allowed = {'image/jpeg', 'image/png'}
        
        is_valid, error = check_mime_type("image/jpeg", allowed)
        assert is_valid
    
    def test_invalid_mime_types(self):
        """Test validation of invalid MIME types"""
        allowed = {'image/jpeg', 'image/png'}
        
        is_valid, error = check_mime_type("application/pdf", allowed)
        assert not is_valid
        assert "not allowed" in error
    
    def test_empty_mime_type(self):
        """Test handling of empty MIME type"""
        is_valid, error = check_mime_type("", {'image/jpeg'})
        assert not is_valid


class TestValidateParams:
    """Tests for validate_params decorator"""
    
    def test_valid_parameters(self):
        """Test decorator with valid parameters"""
        @validate_params({
            'name': {'type': str, 'required': True},
            'age': {'type': int, 'min': 0, 'max': 150}
        })
        def test_func(name, age):
            return f"{name} is {age}"
        
        result = test_func("John", 30)
        assert result == "John is 30"
    
    def test_missing_required_parameter(self):
        """Test decorator with missing required parameter"""
        @validate_params({
            'name': {'type': str, 'required': True}
        })
        def test_func(name=None):
            return name
        
        with pytest.raises(ValueError, match="required"):
            test_func()
    
    def test_type_validation(self):
        """Test type validation"""
        @validate_params({
            'age': {'type': int}
        })
        def test_func(age):
            return age
        
        with pytest.raises(ValueError, match="must be of type"):
            test_func("not an int")
    
    def test_range_validation(self):
        """Test min/max range validation"""
        @validate_params({
            'age': {'type': int, 'min': 0, 'max': 150}
        })
        def test_func(age):
            return age
        
        # Valid
        assert test_func(50) == 50
        
        # Too small
        with pytest.raises(ValueError, match="must be >="):
            test_func(-1)
        
        # Too large
        with pytest.raises(ValueError, match="must be <="):
            test_func(200)
    
    def test_choices_validation(self):
        """Test choices validation"""
        @validate_params({
            'plan': {'type': str, 'choices': ['free', 'pro', 'business']}
        })
        def test_func(plan):
            return plan
        
        # Valid
        assert test_func('pro') == 'pro'
        
        # Invalid choice
        with pytest.raises(ValueError, match="must be one of"):
            test_func('invalid')
    
    def test_email_format_validation(self):
        """Test email format validation"""
        @validate_params({
            'email': {'type': str, 'format': 'email'}
        })
        def test_func(email):
            return email
        
        # Valid
        assert test_func('user@example.com') == 'user@example.com'
        
        # Invalid
        with pytest.raises(ValueError, match="not a valid email"):
            test_func('notanemail')
    
    def test_string_length_validation(self):
        """Test string length validation"""
        @validate_params({
            'name': {'type': str, 'min_length': 3, 'max_length': 10}
        })
        def test_func(name):
            return name
        
        # Valid
        assert test_func('John') == 'John'
        
        # Too short
        with pytest.raises(ValueError, match="at least"):
            test_func('ab')
        
        # Too long
        with pytest.raises(ValueError, match="at most"):
            test_func('a' * 20)
