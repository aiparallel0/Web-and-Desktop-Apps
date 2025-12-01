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

# Circular Exchange Framework Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False

# Register module with Circular Exchange
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="shared.config",
            file_path=__file__,
            description="Configuration module with environment-based settings",
            dependencies=["shared.circular_exchange"],
            exports=["AppConfig", "ImageConfig", "OCRConfig", "APIConfig", 
                    "SecurityConfig", "get_config", "reload_config"]
        ))
    except Exception:
        pass  # Ignore registration errors during import

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
