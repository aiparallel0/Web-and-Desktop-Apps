"""
=============================================================================
LOGGING CONFIGURATION - Structured JSON Logging
=============================================================================

Provides structured logging with JSON format for production environments.

Usage:
    from telemetry.logging_config import setup_logging, get_json_logger
    
    # Setup at app startup
    setup_logging(app)
    
    # Get logger
    logger = get_json_logger(__name__)
    logger.info("Message", extra={"user_id": "123", "action": "extraction"})

=============================================================================
"""

import os
import sys
import logging
import json
from datetime import datetime
from typing import Optional
from logging.handlers import RotatingFileHandler


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs as JSON.
    
    Includes:
    - Standard log fields (timestamp, level, message)
    - Extra fields passed to log calls
    - Exception information when available
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields
        extra_fields = [
            'user_id', 'request_id', 'session_id', 'model_id',
            'action', 'duration', 'status_code', 'endpoint',
            'error_type', 'properties'
        ]
        
        for field in extra_fields:
            if hasattr(record, field):
                log_data[field] = getattr(record, field)
        
        # Check for any other extra attributes
        for key, value in record.__dict__.items():
            if key not in logging.LogRecord.__dict__ and not key.startswith('_'):
                if key not in log_data and key not in ['message', 'args']:
                    try:
                        # Ensure value is JSON serializable
                        json.dumps(value)
                        log_data[key] = value
                    except (TypeError, ValueError):
                        log_data[key] = str(value)
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """
    Colored formatter for development console output.
    """
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Format with colors."""
        color = self.COLORS.get(record.levelname, '')
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        
        # Build message
        formatted = f"{color}{timestamp} [{record.levelname:8}]{self.RESET} {record.name}: {record.getMessage()}"
        
        # Add extra fields if present
        extra_parts = []
        for key in ['user_id', 'model_id', 'duration', 'action']:
            if hasattr(record, key):
                extra_parts.append(f"{key}={getattr(record, key)}")
        
        if extra_parts:
            formatted += f" ({', '.join(extra_parts)})"
        
        # Add exception
        if record.exc_info:
            formatted += '\n' + self.formatException(record.exc_info)
        
        return formatted


def setup_logging(
    app=None,
    level: str = None,
    format_type: str = None,
    log_file: str = None
) -> None:
    """
    Configure application logging.
    
    Args:
        app: Flask application instance (optional)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Format type ('json' or 'text')
        log_file: Path to log file (optional)
    """
    # Get configuration from environment or arguments
    log_level = level or os.getenv('LOG_LEVEL', 'INFO')
    log_format = format_type or os.getenv('LOG_FORMAT', 'text')
    log_file_path = log_file or os.getenv('LOG_FILE')
    
    # Convert level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    
    # Set formatter based on format type and environment
    is_production = os.getenv('FLASK_ENV') == 'production'
    
    if log_format.lower() == 'json' or is_production:
        formatter = JSONFormatter()
    else:
        # Use colored formatter for development
        formatter = ColoredFormatter()
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file_path:
        try:
            # Create directory if needed
            log_dir = os.path.dirname(log_file_path)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            
            file_handler = RotatingFileHandler(
                log_file_path,
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=5
            )
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(JSONFormatter())  # Always JSON for files
            root_logger.addHandler(file_handler)
            
            logging.info(f"File logging enabled: {log_file_path}")
        except Exception as e:
            logging.warning(f"Failed to setup file logging: {e}")
    
    # Configure Flask app logger if provided
    if app:
        app.logger.handlers = root_logger.handlers
        app.logger.setLevel(numeric_level)
    
    # Reduce noise from libraries
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    logging.info(
        f"Logging configured: level={log_level}, format={log_format}, "
        f"file={'enabled' if log_file_path else 'disabled'}"
    )


def get_json_logger(name: str) -> logging.Logger:
    """
    Get a logger configured for JSON output.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger
    """
    return logging.getLogger(name)


class LogContext:
    """
    Context manager for adding context to log messages.
    
    Usage:
        with LogContext(request_id="abc123", user_id="user1"):
            logger.info("Processing request")  # Will include request_id and user_id
    """
    
    _context = {}
    
    def __init__(self, **kwargs):
        """Initialize with context values."""
        self._old_context = LogContext._context.copy()
        LogContext._context.update(kwargs)
    
    def __enter__(self):
        """Enter context."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and restore previous values."""
        LogContext._context = self._old_context
        return False
    
    @classmethod
    def get(cls, key: str, default=None):
        """Get a context value."""
        return cls._context.get(key, default)
    
    @classmethod
    def get_all(cls) -> dict:
        """Get all context values."""
        return cls._context.copy()


# Custom log adapter that includes context
class ContextLogAdapter(logging.LoggerAdapter):
    """Logger adapter that automatically includes context."""
    
    def process(self, msg, kwargs):
        """Add context to log record."""
        extra = kwargs.get('extra', {})
        extra.update(LogContext.get_all())
        kwargs['extra'] = extra
        return msg, kwargs


def get_context_logger(name: str) -> ContextLogAdapter:
    """
    Get a logger that automatically includes context.
    
    Args:
        name: Logger name
        
    Returns:
        Logger adapter with context support
    """
    return ContextLogAdapter(logging.getLogger(name), {})
