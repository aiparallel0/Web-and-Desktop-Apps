"""
Centralized configuration management for the Receipt Extractor application.

This module provides:
- Environment-based configuration
- Default values with environment overrides
- Type-safe configuration access
- Validation of configuration values

Integrated with Circular Exchange Framework for dynamic configuration.
"""
import os
import json
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

# Circular Exchange Framework Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration, PackageRegistry
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False

logger = logging.getLogger(__name__)

# Register module with Circular Exchange
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="shared.config.settings",
            file_path=__file__,
            description="Centralized configuration management with environment-based settings",
            dependencies=["shared.circular_exchange"],
            exports=["ImageConfig", "OCRConfig", "APIConfig", "Settings", "get_settings"]
        ))
    except Exception:
        pass  # Ignore registration errors

# Base paths
CONFIG_DIR = Path(__file__).parent
PROJECT_ROOT = CONFIG_DIR.parent.parent


@dataclass(frozen=True)
class ImageConfig:
    """Image processing configuration."""
    max_size_bytes: int = 100 * 1024 * 1024  # 100MB
    max_dimension: int = 4096
    min_dimension: int = 50
    allowed_extensions: frozenset = frozenset({'png', 'jpg', 'jpeg', 'bmp', 'tiff', 'tif', 'gif'})
    allowed_mime_types: frozenset = frozenset({
        'image/jpeg', 'image/jpg', 'image/png', 
        'image/bmp', 'image/tiff', 'image/tif', 'image/gif'
    })
    
    # Preprocessing settings
    upscale_threshold: int = 1000  # Upscale if max dimension < this
    upscale_target: int = 1500
    brightness_threshold: float = 100.0
    contrast_threshold: float = 40.0
    

@dataclass(frozen=True)
class OCRConfig:
    """OCR processing configuration."""
    default_language: str = 'en'
    supported_languages: frozenset = frozenset({'en', 'es', 'fr', 'de', 'it', 'pt', 'zh', 'ja', 'ko'})
    confidence_threshold: float = 0.3
    min_text_length: int = 2
    max_line_items: int = 100
    
    # Price validation
    price_min: float = 0.0
    price_max: float = 9999.0
    

@dataclass(frozen=True)
class APIConfig:
    """API server configuration."""
    host: str = '0.0.0.0'
    port: int = 5000
    debug: bool = False
    max_content_length: int = 100 * 1024 * 1024  # 100MB
    request_timeout: int = 3600
    
    # Rate limiting (per hour)
    rate_limit_default: int = 100
    rate_limit_free: int = 50
    rate_limit_pro: int = 1000
    rate_limit_business: int = 10000
    rate_limit_enterprise: int = 999999
    

@dataclass(frozen=True)
class SecurityConfig:
    """Security configuration."""
    jwt_algorithm: str = 'HS256'
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    bcrypt_rounds: int = 12
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30
    

@dataclass
class AppConfig:
    """Main application configuration."""
    
    # Environment
    env: str = field(default_factory=lambda: os.getenv('APP_ENV', 'development'))
    
    # Sub-configurations
    image: ImageConfig = field(default_factory=ImageConfig)
    ocr: OCRConfig = field(default_factory=OCRConfig)
    api: APIConfig = field(default_factory=APIConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    
    # Model configuration
    models_config_path: Path = field(default_factory=lambda: CONFIG_DIR / 'models_config.json')
    default_model: str = 'ocr_tesseract'
    max_loaded_models: int = 3
    
    # Logging
    log_level: str = field(default_factory=lambda: os.getenv('LOG_LEVEL', 'INFO'))
    log_format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Database
    database_url: str = field(default_factory=lambda: os.getenv(
        'DATABASE_URL',
        'postgresql://receipt_user:receipt_pass@localhost:5432/receipt_extractor'
    ))
    use_sqlite: bool = field(default_factory=lambda: os.getenv('USE_SQLITE', 'false').lower() == 'true')
    
    @classmethod
    def load(cls) -> 'AppConfig':
        """Load configuration from environment and files."""
        config = cls()
        
        # Override with environment variables
        if os.getenv('MAX_CONTENT_LENGTH'):
            config = cls(
                api=APIConfig(max_content_length=int(os.getenv('MAX_CONTENT_LENGTH')))
            )
        
        logger.info(f"Configuration loaded for environment: {config.env}")
        return config
    
    def get_models_config(self) -> Dict:
        """Load models configuration from JSON file."""
        try:
            with open(self.models_config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load models config: {e}")
            return {'available_models': {}, 'default_model': self.default_model}
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.env.lower() in ('production', 'prod')
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.env.lower() in ('development', 'dev', 'local')
    
    def is_testing(self) -> bool:
        """Check if running in test environment."""
        return self.env.lower() in ('testing', 'test') or os.getenv('TESTING', 'false').lower() == 'true'


# Singleton instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get the application configuration singleton."""
    global _config
    if _config is None:
        _config = AppConfig.load()
    return _config


def reload_config() -> AppConfig:
    """Reload the configuration (useful for testing)."""
    global _config
    _config = AppConfig.load()
    return _config


# Validation utilities
def validate_file_extension(filename: str, config: Optional[AppConfig] = None) -> bool:
    """Validate file extension against allowed list."""
    if config is None:
        config = get_config()
    
    if '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in config.image.allowed_extensions


def validate_file_size(size_bytes: int, config: Optional[AppConfig] = None) -> bool:
    """Validate file size against maximum limit."""
    if config is None:
        config = get_config()
    
    return 0 < size_bytes <= config.image.max_size_bytes


def validate_mime_type(mime_type: str, config: Optional[AppConfig] = None) -> bool:
    """Validate MIME type against allowed list."""
    if config is None:
        config = get_config()
    
    return mime_type.lower() in config.image.allowed_mime_types


def get_rate_limit_for_plan(plan: str, config: Optional[AppConfig] = None) -> int:
    """Get rate limit for a subscription plan."""
    if config is None:
        config = get_config()
    
    limits = {
        'free': config.api.rate_limit_free,
        'pro': config.api.rate_limit_pro,
        'business': config.api.rate_limit_business,
        'enterprise': config.api.rate_limit_enterprise,
    }
    
    return limits.get(plan.lower(), config.api.rate_limit_default)
