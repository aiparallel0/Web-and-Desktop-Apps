"""
Centralized Logging and Error Handling System

This module provides automatic logging injection and error handling for the entire
application. It follows industry best practices used by companies like Amazon and Meta:

1. **Automatic Logger Injection**: When any module imports `get_module_logger()`,
   it automatically receives a pre-configured logger with the correct module name.

2. **Structured Logging**: All logs are formatted as JSON for easy parsing and
   aggregation in log management systems (ELK, Splunk, CloudWatch, etc.)

3. **Automatic Error Handling**: Decorators automatically capture and log errors
   with full context (request ID, user info, etc.)

4. **Zero-Configuration**: New files automatically get logging by importing from
   this module - no manual setup required.

Usage in any Python file:
    from shared.utils.centralized_logging import get_module_logger, log_errors

    logger = get_module_logger()  # Automatically uses __name__ of calling module

    @log_errors
    def my_function():
        logger.info("Processing...")
        # ... function code ...

Environment Variables:
    LOG_LEVEL: Set global log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    LOG_FORMAT: Set format type ('json' or 'text')
    LOG_DIR: Directory for log files (default: 'logs')
    LOG_TO_CONSOLE: Whether to log to console ('true'/'false')
    LOG_TO_FILE: Whether to log to file ('true'/'false')
"""

import logging
import logging.handlers
import os
import sys
import json
import functools
import traceback
import uuid
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any, Callable, Dict, TypeVar, Union
from contextlib import contextmanager

# Thread-local storage for request context
_context = threading.local()

# Global configuration - can be overridden via environment variables
_CONFIG = {
    'level': os.getenv('LOG_LEVEL', 'INFO').upper(),
    'format': os.getenv('LOG_FORMAT', 'json'),  # 'json' or 'text'
    'log_dir': os.getenv('LOG_DIR', 'logs'),
    'console_output': os.getenv('LOG_TO_CONSOLE', 'true').lower() == 'true',
    'file_output': os.getenv('LOG_TO_FILE', 'true').lower() == 'true',
    'max_bytes': int(os.getenv('LOG_MAX_BYTES', 10 * 1024 * 1024)),  # 10MB
    'backup_count': int(os.getenv('LOG_BACKUP_COUNT', 5)),
}

# Type variable for generic decorator
F = TypeVar('F', bound=Callable[..., Any])


class StructuredJSONFormatter(logging.Formatter):
    """
    Formatter that produces structured JSON logs.
    
    Output includes:
    - timestamp: ISO 8601 format
    - level: Log level name
    - logger: Logger name (module)
    - message: The log message
    - module/function/line: Source location
    - context: Any additional context (request_id, user_id, etc.)
    - exception: Full traceback if an exception occurred
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add any extra fields from the record
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        # Add thread-local context (request_id, user_id, etc.)
        context = get_context()
        if context:
            log_data['context'] = context
        
        return json.dumps(log_data, default=str)


class ColoredTextFormatter(logging.Formatter):
    """
    Formatter that produces colored console output for better readability.
    
    Colors:
    - DEBUG: Cyan
    - INFO: Green
    - WARNING: Yellow
    - ERROR: Red
    - CRITICAL: Magenta with bold
    """
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[1;35m', # Bold Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        # Save original levelname
        original_levelname = record.levelname
        
        # Add color to levelname
        color = self.COLORS.get(record.levelname, '')
        if color:
            record.levelname = f"{color}{record.levelname}{self.RESET}"
        
        # Format the message
        formatted = super().format(record)
        
        # Restore original levelname
        record.levelname = original_levelname
        
        # Add context if available
        context = get_context()
        if context:
            context_str = ' '.join(f'{k}={v}' for k, v in context.items())
            formatted = f"{formatted} [{context_str}]"
        
        return formatted


class CentralizedLoggingManager:
    """
    Singleton manager for centralized logging configuration.
    
    This class ensures that:
    1. All loggers share the same configuration
    2. Handlers are created only once
    3. Log files are properly managed with rotation
    """
    
    _instance = None
    _lock = threading.Lock()
    _configured = False
    _loggers: Dict[str, logging.Logger] = {}
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def configure(self, force: bool = False) -> None:
        """Configure the root logger and handlers."""
        if self._configured and not force:
            return
        
        with self._lock:
            if self._configured and not force:
                return
            
            # Get or create root logger for our app
            root_logger = logging.getLogger('receipt_extractor')
            root_logger.setLevel(getattr(logging, _CONFIG['level']))
            
            # Clear existing handlers
            root_logger.handlers.clear()
            
            # Create formatters
            if _CONFIG['format'] == 'json':
                file_formatter = StructuredJSONFormatter()
                console_formatter = StructuredJSONFormatter()
            else:
                file_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                console_formatter = ColoredTextFormatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%H:%M:%S'
                )
            
            # Add console handler
            if _CONFIG['console_output']:
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setFormatter(console_formatter)
                root_logger.addHandler(console_handler)
            
            # Add file handler with rotation
            if _CONFIG['file_output']:
                log_dir = Path(_CONFIG['log_dir'])
                log_dir.mkdir(parents=True, exist_ok=True)
                
                log_file = log_dir / 'application.log'
                file_handler = logging.handlers.RotatingFileHandler(
                    log_file,
                    maxBytes=_CONFIG['max_bytes'],
                    backupCount=_CONFIG['backup_count']
                )
                file_handler.setFormatter(file_formatter)
                root_logger.addHandler(file_handler)
            
            self._configured = True
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get or create a logger with the given name."""
        self.configure()
        
        if name in self._loggers:
            return self._loggers[name]
        
        # Create logger as child of our root logger
        if not name.startswith('receipt_extractor'):
            full_name = f'receipt_extractor.{name}'
        else:
            full_name = name
        
        logger = logging.getLogger(full_name)
        self._loggers[name] = logger
        return logger


# Global manager instance
_manager = CentralizedLoggingManager()


def get_module_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger for the calling module.
    
    This function automatically determines the calling module's name
    and returns a properly configured logger.
    
    Usage:
        from shared.utils.centralized_logging import get_module_logger
        logger = get_module_logger()
        logger.info("This is logged with the correct module name")
    
    Args:
        name: Optional explicit name. If not provided, uses the calling module's __name__
    
    Returns:
        A configured logging.Logger instance
    """
    if name is None:
        # Get the calling module's name from the call stack
        import inspect
        frame = inspect.currentframe()
        if frame and frame.f_back:
            name = frame.f_back.f_globals.get('__name__', 'unknown')
        else:
            name = 'unknown'
    
    return _manager.get_logger(name)


def set_context(**kwargs) -> None:
    """
    Set thread-local context that will be included in all log messages.
    
    Usage:
        set_context(request_id='abc123', user_id='user456')
        logger.info("Processing request")  # Will include request_id and user_id
    """
    if not hasattr(_context, 'data'):
        _context.data = {}
    _context.data.update(kwargs)


def get_context() -> Dict[str, Any]:
    """Get the current thread-local context."""
    return getattr(_context, 'data', {})


def clear_context() -> None:
    """Clear all thread-local context."""
    if hasattr(_context, 'data'):
        _context.data.clear()


@contextmanager
def logging_context(**kwargs):
    """
    Context manager for temporary logging context.
    
    Usage:
        with logging_context(request_id='abc123'):
            logger.info("This will include request_id")
        logger.info("This will NOT include request_id")
    """
    old_context = getattr(_context, 'data', {}).copy()
    set_context(**kwargs)
    try:
        yield
    finally:
        _context.data = old_context


def log_errors(
    logger: Optional[logging.Logger] = None,
    level: int = logging.ERROR,
    reraise: bool = True,
    message: Optional[str] = None
) -> Callable[[F], F]:
    """
    Decorator for automatic error logging.
    
    This decorator catches all exceptions, logs them with full context,
    and optionally re-raises them.
    
    Usage:
        @log_errors
        def my_function():
            # ... code that might raise exceptions
            pass
        
        @log_errors(reraise=False, message="Operation failed")
        def my_safe_function():
            # Exceptions are logged but not re-raised
            pass
    
    Args:
        logger: Logger to use. If None, uses the module's logger.
        level: Log level for errors (default: ERROR)
        reraise: Whether to re-raise the exception (default: True)
        message: Custom message prefix for the error log
    
    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            _logger = logger or get_module_logger(func.__module__)
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Build error context
                error_context = {
                    'function': func.__name__,
                    'module': func.__module__,
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                }
                
                # Include argument info (sanitized)
                if args:
                    error_context['args_count'] = len(args)
                if kwargs:
                    error_context['kwargs_keys'] = list(kwargs.keys())
                
                # Generate error ID for tracking
                error_id = str(uuid.uuid4())[:8]
                error_context['error_id'] = error_id
                
                # Log the error
                msg = message or f"Error in {func.__name__}"
                _logger.log(
                    level,
                    f"{msg} [error_id={error_id}]: {e}",
                    exc_info=True,
                    extra={'extra_fields': error_context}
                )
                
                if reraise:
                    raise
                return None
        return wrapper  # type: ignore
    
    # Handle @log_errors with and without parentheses
    if callable(logger):
        # @log_errors used without parentheses
        func = logger
        logger = None
        return decorator(func)  # type: ignore
    
    return decorator


def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    **kwargs
) -> None:
    """
    Log a message with additional context fields.
    
    Usage:
        log_with_context(logger, 'info', 'Receipt processed',
                        receipt_id='12345', processing_time=2.5)
    """
    extra = {'extra_fields': kwargs}
    log_method = getattr(logger, level.lower())
    log_method(message, extra=extra)


class ErrorHandler:
    """
    Centralized error handler that can be used as a context manager.
    
    Usage:
        with ErrorHandler(logger, "Processing receipt"):
            # ... code that might fail
            pass
    """
    
    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        operation: str = "Operation",
        reraise: bool = True,
        default_return: Any = None
    ):
        self.logger = logger or get_module_logger()
        self.operation = operation
        self.reraise = reraise
        self.default_return = default_return
        self.error: Optional[Exception] = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is not None:
            self.error = exc_val
            error_id = str(uuid.uuid4())[:8]
            
            self.logger.error(
                f"{self.operation} failed [error_id={error_id}]: {exc_val}",
                exc_info=True,
                extra={'extra_fields': {
                    'error_id': error_id,
                    'error_type': exc_type.__name__ if exc_type else 'Unknown',
                    'operation': self.operation
                }}
            )
            
            if not self.reraise:
                return True  # Suppress the exception
        return False


# Module initialization
def _init_module():
    """Initialize the centralized logging system when this module is imported."""
    _manager.configure()


# Auto-initialize when imported
_init_module()


# Export public API
__all__ = [
    'get_module_logger',
    'set_context',
    'get_context',
    'clear_context',
    'logging_context',
    'log_errors',
    'log_with_context',
    'ErrorHandler',
    'StructuredJSONFormatter',
    'ColoredTextFormatter',
]
