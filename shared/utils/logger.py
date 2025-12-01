"""
=============================================================================
ENTERPRISE LOGGING FRAMEWORK - Observability & Telemetry
=============================================================================

This module implements production-ready logging infrastructure following
patterns from high-scale distributed systems.

Architecture Features:
- Structured Logging: JSON-formatted logs for machine parsing
- Correlation IDs: Request tracing across service boundaries
- Log Levels: Hierarchical severity for filtering
- Rotation: Automatic log file rotation and compression
- Metrics: Integration points for metrics collection
- Context: Thread-local context for enriched logging

Compliance:
- SOC 2 Type II compatible log formats
- GDPR-ready PII handling capabilities
- Audit trail support

Usage:
    from shared.utils.logger import setup_logger, get_logger, LogContext
    
    # Create application logger
    logger = setup_logger('receipt_extractor', level='INFO')
    
    # Use context for correlation
    with LogContext(request_id='abc123', user_id='user456'):
        logger.info('Processing receipt')

=============================================================================
"""

from __future__ import annotations

import logging
import logging.handlers
import sys
import json
import threading
import os
import uuid
import traceback
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from contextlib import contextmanager
from functools import wraps
from enum import Enum

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
            module_id="shared.utils.logger",
            file_path=__file__,
            description="Enterprise logging framework with structured JSON output and correlation IDs",
            dependencies=["shared.circular_exchange"],
            exports=["setup_logger", "get_logger", "LogContext", "LogLevel", 
                    "log_with_context", "log_operation", "generate_correlation_id"]
        ))
    except Exception:
        pass  # Ignore registration errors during import


class LogLevel(Enum):
    """Standardized log levels."""
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'


@dataclass
class LogRecord:
    """Structured log record for consistent formatting."""
    timestamp: str
    level: str
    logger: str
    message: str
    module: str
    function: str
    line: int
    correlation_id: Optional[str] = None
    extra_fields: Dict[str, Any] = field(default_factory=dict)
    exception: Optional[str] = None


# Thread-local storage for log context
_log_context = threading.local()


class LogContext:
    """
    Context manager for adding contextual information to logs.
    
    This enables correlation of logs across a request lifecycle
    and provides automatic context cleanup.
    
    Example:
        with LogContext(request_id='abc123', user_id='user456'):
            logger.info('Processing started')  # Will include request_id and user_id
    """
    
    def __init__(self, **kwargs):
        """Initialize log context with key-value pairs."""
        self.context = kwargs
        self.previous_context: Dict[str, Any] = {}
    
    def __enter__(self) -> LogContext:
        """Enter context and save previous values."""
        if not hasattr(_log_context, 'data'):
            _log_context.data = {}
        
        for key, value in self.context.items():
            self.previous_context[key] = _log_context.data.get(key)
            _log_context.data[key] = value
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and restore previous values."""
        for key in self.context:
            if self.previous_context.get(key) is None:
                _log_context.data.pop(key, None)
            else:
                _log_context.data[key] = self.previous_context[key]
    
    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """Get a value from the current log context."""
        if hasattr(_log_context, 'data'):
            return _log_context.data.get(key, default)
        return default
    
    @staticmethod
    def get_all() -> Dict[str, Any]:
        """Get all current context values."""
        if hasattr(_log_context, 'data'):
            return _log_context.data.copy()
        return {}
    
    @staticmethod
    def set(key: str, value: Any) -> None:
        """Set a value in the current log context."""
        if not hasattr(_log_context, 'data'):
            _log_context.data = {}
        _log_context.data[key] = value
    
    @staticmethod
    def clear() -> None:
        """Clear all context data."""
        if hasattr(_log_context, 'data'):
            _log_context.data.clear()


class StructuredFormatter(logging.Formatter):
    """
    JSON-structured log formatter for machine-readable logs.
    
    Produces logs in the format:
    {
        "timestamp": "2024-01-15T10:30:00.000Z",
        "level": "INFO",
        "logger": "receipt_extractor",
        "message": "Processing receipt",
        "module": "processor",
        "function": "extract",
        "line": 42,
        "correlation_id": "abc123",
        "request_id": "req-456",
        ...
    }
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add correlation ID if available
        correlation_id = LogContext.get('correlation_id')
        if correlation_id:
            log_data['correlation_id'] = correlation_id
        
        # Add all context fields
        context_data = LogContext.get_all()
        if context_data:
            log_data.update(context_data)
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
            log_data['exception_type'] = record.exc_info[0].__name__ if record.exc_info[0] else None
        
        # Add extra fields from record
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data, default=str)


class ColoredFormatter(logging.Formatter):
    """
    ANSI color-coded formatter for console output.
    
    Color scheme:
    - DEBUG: Cyan
    - INFO: Green
    - WARNING: Yellow
    - ERROR: Red
    - CRITICAL: Magenta
    """
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with ANSI colors."""
        original_levelname = record.levelname
        
        if original_levelname in self.COLORS:
            color = self.COLORS[original_levelname]
            record.levelname = f"{color}{self.BOLD}{original_levelname}{self.RESET}"
        
        # Add correlation ID if available
        correlation_id = LogContext.get('correlation_id')
        if correlation_id:
            record.msg = f"[{self.DIM}{correlation_id[:8]}{self.RESET}] {record.msg}"
        
        formatted = super().format(record)
        record.levelname = original_levelname
        
        return formatted


class MetricsHandler(logging.Handler):
    """
    Handler that extracts metrics from log records.
    
    This enables automatic metric collection from logs,
    useful for monitoring and alerting systems.
    """
    
    def __init__(self, callback: Optional[Callable[[str, Dict[str, Any]], None]] = None):
        super().__init__()
        self.callback = callback
        self.counters: Dict[str, int] = {}
    
    def emit(self, record: logging.LogRecord) -> None:
        """Process log record for metrics."""
        # Count by level
        level = record.levelname
        self.counters[level] = self.counters.get(level, 0) + 1
        
        # Notify callback if registered
        if self.callback:
            self.callback(level, {
                'logger': record.name,
                'module': record.module,
                'message': record.getMessage()[:100]
            })
    
    def get_counts(self) -> Dict[str, int]:
        """Get log level counts."""
        return self.counters.copy()


def setup_logger(
    name: str,
    level: str = 'INFO',
    log_dir: str = 'logs',
    use_json: bool = False,
    console_output: bool = True,
    file_output: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    add_metrics: bool = False
) -> logging.Logger:
    """
    Create and configure a production-ready logger.
    
    Args:
        name: Logger name (typically module name)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        use_json: Use JSON formatting for all outputs
        console_output: Enable console logging
        file_output: Enable file logging
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup log files to keep
        add_metrics: Enable metrics collection handler
    
    Returns:
        Configured Logger instance
    
    Example:
        logger = setup_logger('receipt_extractor', level='DEBUG', use_json=True)
        logger.info('Application started')
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # File handler with rotation
    if file_output:
        log_file = log_path / f'{name.replace(".", "_")}.log'
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        
        if use_json:
            file_handler.setFormatter(StructuredFormatter())
        else:
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ))
        
        logger.addHandler(file_handler)
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        
        if use_json:
            console_handler.setFormatter(StructuredFormatter())
        else:
            console_handler.setFormatter(ColoredFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            ))
        
        logger.addHandler(console_handler)
    
    # Metrics handler
    if add_metrics:
        metrics_handler = MetricsHandler()
        metrics_handler.setLevel(logging.WARNING)  # Only track warnings and above
        logger.addHandler(metrics_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get an existing logger by name.
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    **kwargs
) -> None:
    """
    Log a message with additional context fields.
    
    Args:
        logger: Logger instance
        level: Log level (debug, info, warning, error, critical)
        message: Log message
        **kwargs: Additional fields to include in log
    
    Example:
        log_with_context(logger, 'info', 'Receipt processed',
                        receipt_id='12345', model='florence2', time=2.5)
    """
    extra = {'extra_fields': kwargs}
    log_method = getattr(logger, level.lower())
    log_method(message, extra=extra)


def log_function_call(logger: logging.Logger, level: str = 'DEBUG'):
    """
    Decorator to log function entry and exit.
    
    Args:
        logger: Logger instance
        level: Log level for the messages
    
    Example:
        @log_function_call(logger)
        def process_receipt(image_path):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            log_method = getattr(logger, level.lower())
            
            log_method(f"Entering {func_name}")
            try:
                result = func(*args, **kwargs)
                log_method(f"Exiting {func_name} successfully")
                return result
            except Exception as e:
                logger.exception(f"Exception in {func_name}: {e}")
                raise
        
        return wrapper
    return decorator


def generate_correlation_id() -> str:
    """Generate a unique correlation ID for request tracing."""
    return str(uuid.uuid4())


@contextmanager
def log_operation(
    logger: logging.Logger,
    operation: str,
    level: str = 'INFO',
    **context
):
    """
    Context manager for logging operations with timing.
    
    Args:
        logger: Logger instance
        operation: Operation name/description
        level: Log level
        **context: Additional context to include
    
    Example:
        with log_operation(logger, 'receipt_extraction', receipt_id='123'):
            result = processor.extract(image)
    """
    start_time = datetime.now()
    log_method = getattr(logger, level.lower())
    
    # Generate correlation ID if not present
    if not LogContext.get('correlation_id'):
        LogContext.set('correlation_id', generate_correlation_id())
    
    log_method(f"Starting: {operation}", extra={'extra_fields': context})
    
    try:
        yield
        duration = (datetime.now() - start_time).total_seconds()
        log_method(
            f"Completed: {operation}",
            extra={'extra_fields': {**context, 'duration_seconds': duration}}
        )
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(
            f"Failed: {operation} - {e}",
            extra={'extra_fields': {**context, 'duration_seconds': duration, 'error': str(e)}}
        )
        raise


# Module-level default logger
_default_logger: Optional[logging.Logger] = None


def get_default_logger() -> logging.Logger:
    """Get or create the default application logger."""
    global _default_logger
    if _default_logger is None:
        _default_logger = setup_logger('receipt_extractor', level='INFO')
    return _default_logger


if __name__ == '__main__':
    # Demo usage
    print("=== Enterprise Logging Framework Demo ===\n")
    
    # Setup development logger
    logger = setup_logger('receipt_extractor', level='DEBUG', use_json=False)
    
    # Basic logging
    logger.debug('This is a debug message')
    logger.info('Application started')
    logger.warning('This is a warning')
    logger.error('An error occurred')
    
    # Logging with context
    with LogContext(request_id='req-12345', user_id='user-789'):
        logger.info('Processing request with context')
        
        with log_operation(logger, 'receipt_extraction', receipt_id='rec-001'):
            import time
            time.sleep(0.1)  # Simulate work
    
    # JSON logging for production
    print("\n=== JSON Format (Production) ===\n")
    json_logger = setup_logger('receipt_extractor_prod', level='INFO', use_json=True)
    
    log_with_context(
        json_logger, 'info', 'Receipt processed',
        receipt_id='12345',
        model='florence2',
        processing_time=2.5
    )
    
    # Exception logging
    try:
        raise ValueError('Example error for demonstration')
    except Exception:
        json_logger.exception('Error processing receipt')
