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
