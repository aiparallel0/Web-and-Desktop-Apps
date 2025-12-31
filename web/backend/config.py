"""
=============================================================================
CENTRALIZED CONFIGURATION MANAGEMENT
=============================================================================

This module provides centralized configuration management for the Flask backend.
It loads configuration from environment variables with sensible defaults and
integrates with the Circular Exchange Framework.

Usage:
    from config import Config, get_config
    
    # Get configuration singleton
    config = get_config()
    
    # Access configuration values
    database_url = config.DATABASE_URL
    jwt_secret = config.JWT_SECRET

=============================================================================
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from functools import lru_cache

logger = logging.getLogger(__name__)

# Try to import dotenv for .env file loading
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    logger.info("python-dotenv not available - using environment variables only")

def _get_bool(value: str, default: bool = False) -> bool:
    """Convert string to boolean."""
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return value.lower() in ('true', '1', 'yes', 'on')

def _get_int(value: str, default: int = 0) -> int:
    """Convert string to integer."""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

@dataclass
class Config:
    """
    Centralized configuration class for the application.
    
    All configuration values are loaded from environment variables
    with sensible defaults for development.
    """
    
    # =========================================================================
    # APPLICATION SETTINGS
    # =========================================================================
    
    # Flask Configuration
    FLASK_ENV: str = "development"
    FLASK_DEBUG: bool = False
    DEBUG: bool = False
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    
    # Server Configuration
    FLASK_HOST: str = "0.0.0.0"
    FLASK_PORT: int = 5000
    
    # Serverless mode
    SERVERLESS: bool = False
    
    # =========================================================================
    # DATABASE CONFIGURATION
    # =========================================================================
    
    DATABASE_URL: str = "sqlite:///./receipt_extractor.db"
    USE_SQLITE: bool = True
    TESTING: bool = False
    
    # Connection Pool Settings
    DB_POOL_SIZE: int = 5
    DB_POOL_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    SQL_ECHO: bool = False
    
    # =========================================================================
    # AUTHENTICATION & SECURITY
    # =========================================================================
    
    JWT_SECRET: str = "change-this-secret-in-production-use-env-var-min-32-chars"
    JWT_ACCESS_TOKEN_EXPIRES: int = 900  # 15 minutes
    JWT_REFRESH_TOKEN_EXPIRES: int = 2592000  # 30 days
    
    # =========================================================================
    # STRIPE PAYMENT INTEGRATION
    # =========================================================================
    
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    
    # =========================================================================
    # CLOUD STORAGE
    # =========================================================================
    
    # AWS S3
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_S3_BUCKET: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    
    # Google Drive
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_DRIVE_REDIRECT_URI: Optional[str] = None
    
    # Dropbox
    DROPBOX_APP_KEY: Optional[str] = None
    DROPBOX_APP_SECRET: Optional[str] = None
    
    # =========================================================================
    # CLOUD TRAINING PROVIDERS
    # =========================================================================
    
    HUGGINGFACE_TOKEN: Optional[str] = None
    REPLICATE_API_TOKEN: Optional[str] = None
    RUNPOD_API_KEY: Optional[str] = None
    
    # =========================================================================
    # ANALYTICS & MONITORING
    # =========================================================================
    
    OTEL_EXPORTER_OTLP_ENDPOINT: Optional[str] = None
    OTEL_SERVICE_NAME: str = "receipt-extractor"
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: str = "development"
    
    # =========================================================================
    # CIRCULAR EXCHANGE FRAMEWORK
    # =========================================================================
    
    CIRCULAR_EXCHANGE_ENABLED: bool = True
    CIRCULAR_EXCHANGE_LOG_LEVEL: str = "INFO"
    
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # =========================================================================
    # OCR & MODEL CONFIGURATION
    # =========================================================================
    
    MODEL_CACHE_DIR: str = "./models"
    TESSERACT_CMD: Optional[str] = None
    MAX_LOADED_MODELS: int = 3
    
    # =========================================================================
    # FILE UPLOAD SETTINGS
    # =========================================================================
    
    ALLOWED_EXTENSIONS: str = "png,jpg,jpeg,gif,bmp,tiff,webp,pdf"
    MAX_CONTENT_LENGTH: int = 16777216  # 16 MB
    UPLOAD_FOLDER: str = "./uploads"
    
    # =========================================================================
    # LOGGING CONFIGURATION
    # =========================================================================
    
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "text"
    LOG_FILE: Optional[str] = None
    
    # =========================================================================
    # CORS SETTINGS
    # =========================================================================
    
    CORS_ORIGINS: str = "*"
    CORS_ALLOW_CREDENTIALS: bool = True
    
    # =========================================================================
    # RATE LIMITING
    # =========================================================================
    
    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # =========================================================================
    # COMPUTED PROPERTIES
    # =========================================================================
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.FLASK_ENV == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.FLASK_ENV == "development"
    
    @property
    def allowed_extensions_set(self) -> set:
        """Get allowed extensions as a set."""
        return set(ext.strip().lower() for ext in self.ALLOWED_EXTENSIONS.split(','))
    
    @property
    def cors_origins_list(self) -> list:
        """Get CORS origins as a list."""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(',')]
    
    def get_database_url(self) -> str:
        """Get the appropriate database URL based on settings."""
        if self.TESTING:
            return "sqlite:///:memory:"
        # USE_SQLITE forces SQLite, ignoring any non-SQLite DATABASE_URL
        if self.USE_SQLITE:
            if self.DATABASE_URL.startswith("sqlite"):
                return self.DATABASE_URL
            return "sqlite:///./receipt_extractor.db"
        return self.DATABASE_URL
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (excluding secrets)."""
        db_url = self.get_database_url()
        # Hide credentials from database URL in output
        safe_db_url = db_url.split('@')[-1] if '@' in db_url else db_url
        return {
            'flask_env': self.FLASK_ENV,
            'debug': self.DEBUG,
            'database_url': safe_db_url,
            'use_sqlite': self.USE_SQLITE,
            'testing': self.TESTING,
            'is_production': self.is_production,
            'stripe_enabled': bool(self.STRIPE_SECRET_KEY),
            'cloud_storage_enabled': bool(self.AWS_ACCESS_KEY_ID or self.GOOGLE_CLIENT_ID or self.DROPBOX_APP_KEY),
            'huggingface_enabled': bool(self.HUGGINGFACE_TOKEN),
            'otel_enabled': bool(self.OTEL_EXPORTER_OTLP_ENDPOINT),
            'sentry_enabled': bool(self.SENTRY_DSN),
            'rate_limiting_enabled': self.RATE_LIMIT_ENABLED,
        }

def load_config() -> Config:
    """
    Load configuration from environment variables.
    
    Returns:
        Config instance with values from environment
    """
    # Load .env file if available
    if DOTENV_AVAILABLE:
        env_path = Path(__file__).parent.parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)
            logger.info(f"Loaded environment from {env_path}")
    
    config = Config(
        # Application Settings
        FLASK_ENV=os.getenv('FLASK_ENV', 'development'),
        FLASK_DEBUG=_get_bool(os.getenv('FLASK_DEBUG'), False),
        DEBUG=_get_bool(os.getenv('DEBUG'), False),
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production'),
        FLASK_HOST=os.getenv('FLASK_HOST', '0.0.0.0'),
        FLASK_PORT=_get_int(os.getenv('FLASK_PORT'), 5000),
        SERVERLESS=_get_bool(os.getenv('SERVERLESS'), False),
        
        # Database
        DATABASE_URL=os.getenv('DATABASE_URL', 'sqlite:///./receipt_extractor.db'),
        USE_SQLITE=_get_bool(os.getenv('USE_SQLITE'), True),
        TESTING=_get_bool(os.getenv('TESTING'), False),
        DB_POOL_SIZE=_get_int(os.getenv('DB_POOL_SIZE'), 5),
        DB_POOL_MAX_OVERFLOW=_get_int(os.getenv('DB_POOL_MAX_OVERFLOW'), 10),
        DB_POOL_TIMEOUT=_get_int(os.getenv('DB_POOL_TIMEOUT'), 30),
        DB_POOL_RECYCLE=_get_int(os.getenv('DB_POOL_RECYCLE'), 1800),
        SQL_ECHO=_get_bool(os.getenv('SQL_ECHO'), False),
        
        # Authentication
        JWT_SECRET=os.getenv('JWT_SECRET', 'change-this-secret-in-production-use-env-var-min-32-chars'),
        JWT_ACCESS_TOKEN_EXPIRES=_get_int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES'), 900),
        JWT_REFRESH_TOKEN_EXPIRES=_get_int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES'), 2592000),
        
        # Stripe
        STRIPE_SECRET_KEY=os.getenv('STRIPE_SECRET_KEY'),
        STRIPE_PUBLISHABLE_KEY=os.getenv('STRIPE_PUBLISHABLE_KEY'),
        STRIPE_WEBHOOK_SECRET=os.getenv('STRIPE_WEBHOOK_SECRET'),
        
        # AWS S3
        AWS_ACCESS_KEY_ID=os.getenv('AWS_ACCESS_KEY_ID'),
        AWS_SECRET_ACCESS_KEY=os.getenv('AWS_SECRET_ACCESS_KEY'),
        AWS_S3_BUCKET=os.getenv('AWS_S3_BUCKET'),
        AWS_REGION=os.getenv('AWS_REGION', 'us-east-1'),
        
        # Google Drive
        GOOGLE_CLIENT_ID=os.getenv('GOOGLE_CLIENT_ID'),
        GOOGLE_CLIENT_SECRET=os.getenv('GOOGLE_CLIENT_SECRET'),
        GOOGLE_DRIVE_REDIRECT_URI=os.getenv('GOOGLE_DRIVE_REDIRECT_URI'),
        
        # Dropbox
        DROPBOX_APP_KEY=os.getenv('DROPBOX_APP_KEY'),
        DROPBOX_APP_SECRET=os.getenv('DROPBOX_APP_SECRET'),
        
        # Training Providers
        HUGGINGFACE_TOKEN=os.getenv('HUGGINGFACE_TOKEN'),
        REPLICATE_API_TOKEN=os.getenv('REPLICATE_API_TOKEN'),
        RUNPOD_API_KEY=os.getenv('RUNPOD_API_KEY'),
        
        # Monitoring
        OTEL_EXPORTER_OTLP_ENDPOINT=os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT'),
        OTEL_SERVICE_NAME=os.getenv('OTEL_SERVICE_NAME', 'receipt-extractor'),
        SENTRY_DSN=os.getenv('SENTRY_DSN'),
        SENTRY_ENVIRONMENT=os.getenv('SENTRY_ENVIRONMENT', 'development'),
        
        # Circular Exchange
        CIRCULAR_EXCHANGE_ENABLED=_get_bool(os.getenv('CIRCULAR_EXCHANGE_ENABLED'), True),
        CIRCULAR_EXCHANGE_LOG_LEVEL=os.getenv('CIRCULAR_EXCHANGE_LOG_LEVEL', 'INFO'),
        
        # Redis
        REDIS_HOST=os.getenv('REDIS_HOST', 'localhost'),
        REDIS_PORT=_get_int(os.getenv('REDIS_PORT'), 6379),
        REDIS_DB=_get_int(os.getenv('REDIS_DB'), 0),
        REDIS_PASSWORD=os.getenv('REDIS_PASSWORD'),
        
        # OCR & Models
        MODEL_CACHE_DIR=os.getenv('MODEL_CACHE_DIR', './models'),
        TESSERACT_CMD=os.getenv('TESSERACT_CMD'),
        MAX_LOADED_MODELS=_get_int(os.getenv('MAX_LOADED_MODELS'), 3),
        
        # File Upload
        ALLOWED_EXTENSIONS=os.getenv('ALLOWED_EXTENSIONS', 'png,jpg,jpeg,gif,bmp,tiff,webp,pdf'),
        MAX_CONTENT_LENGTH=_get_int(os.getenv('MAX_CONTENT_LENGTH'), 16777216),
        UPLOAD_FOLDER=os.getenv('UPLOAD_FOLDER', './uploads'),
        
        # Logging
        LOG_LEVEL=os.getenv('LOG_LEVEL', 'INFO'),
        LOG_FORMAT=os.getenv('LOG_FORMAT', 'text'),
        LOG_FILE=os.getenv('LOG_FILE'),
        
        # CORS
        CORS_ORIGINS=os.getenv('CORS_ORIGINS', '*'),
        CORS_ALLOW_CREDENTIALS=_get_bool(os.getenv('CORS_ALLOW_CREDENTIALS'), True),
        
        # Rate Limiting
        RATE_LIMIT_ENABLED=_get_bool(os.getenv('RATE_LIMIT_ENABLED'), False),
        RATE_LIMIT_PER_MINUTE=_get_int(os.getenv('RATE_LIMIT_PER_MINUTE'), 100),
    )
    
    return config

@lru_cache(maxsize=1)
def get_config() -> Config:
    """
    Get the configuration singleton.
    
    Returns:
        Config instance (cached)
    """
    return load_config()

def reset_config():
    """Reset the configuration cache. Useful for testing."""
    get_config.cache_clear()

# Configuration validation
def validate_config(config: Config) -> list:
    """
    Validate configuration and return list of warnings.
    
    Args:
        config: Configuration to validate
        
    Returns:
        List of warning messages
    """
    warnings = []
    
    if config.is_production:
        if config.JWT_SECRET == "change-this-secret-in-production-use-env-var-min-32-chars":
            warnings.append("JWT_SECRET is using default value - change this in production!")
        
        if len(config.JWT_SECRET) < 32:
            warnings.append("JWT_SECRET should be at least 32 characters in production")
        
        if config.DEBUG:
            warnings.append("DEBUG is enabled in production - consider disabling")
        
        if config.USE_SQLITE:
            warnings.append("SQLite is enabled in production - consider using PostgreSQL")
        
        if not config.SENTRY_DSN:
            warnings.append("SENTRY_DSN not configured - error tracking is disabled")
    
    return warnings

def validate_on_startup():
    """
    Run configuration validation and log warnings.
    
    Call this during application startup rather than on import
    to avoid performance issues during testing.
    """
    config = get_config()
    warnings = validate_config(config)
    for warning in warnings:
        logger.warning(f"Configuration warning: {warning}")
    return warnings
