"""
Configuration module for the Receipt Extractor application.

Provides centralized configuration management with environment-based settings.

Circular Exchange Framework Integration:
-----------------------------------------
Module ID: shared.config
Description: Centralized configuration management with environment-based settings
Dependencies: [shared.circular_exchange]
Exports: [AppConfig, ImageConfig, OCRConfig, APIConfig, SecurityConfig, get_config]
"""

from .settings import (
    AppConfig,
    ImageConfig,
    OCRConfig,
    APIConfig,
    SecurityConfig,
    get_config,
    reload_config,
    validate_file_extension,
    validate_file_size,
    validate_mime_type,
    get_rate_limit_for_plan
)

__all__ = [
    'AppConfig',
    'ImageConfig',
    'OCRConfig',
    'APIConfig',
    'SecurityConfig',
    'get_config',
    'reload_config',
    'validate_file_extension',
    'validate_file_size',
    'validate_mime_type',
    'get_rate_limit_for_plan'
]
