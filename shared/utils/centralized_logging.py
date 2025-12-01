"""
Centralized Logging and Error Handling System

Supports industry-standard log formats:
- Syslog (RFC 5424) - Standard system logging protocol
- Common Log Format (CLF) - Apache/NCSA standard  
- Cisco IOS Format - Network device standard
- JSON - Structured logging for log aggregation
- Text - Human-readable colored console output

Environment Variables:
    LOG_LEVEL: DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FORMAT: syslog, clf, cisco, json, text
    LOG_DIR: Directory for log files (default: 'logs')
    LOG_TO_CONSOLE: 'true'/'false'
    LOG_TO_FILE: 'true'/'false'
    LOG_APP_NAME: Root logger name (default: 'receipt_extractor')
    LOG_MAX_BYTES: Max file size (default: 10MB)
    LOG_BACKUP_COUNT: Backup files to keep (default: 5)

Usage:
    from shared.utils.centralized_logging import get_module_logger
    logger = get_module_logger()
    logger.info("Processing...")
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

# Circular Exchange Framework Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration, PackageRegistry
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False

# Register module with Circular Exchange (deferred to avoid circular import)
def _register_logging_module():
    if CIRCULAR_EXCHANGE_AVAILABLE:
        try:
            PROJECT_CONFIG.register_module(ModuleRegistration(
                module_id="shared.utils.centralized_logging",
                file_path=__file__,
                description="Centralized logging with automatic logger injection and structured JSON output",
                dependencies=["shared.circular_exchange"],
                exports=["get_module_logger", "log_errors", "set_request_context", "LoggingConfig"]
            ))
        except Exception:
            pass  # Ignore registration errors during import

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
    'app_name': os.getenv('LOG_APP_NAME', 'receipt_extractor'),  # Configurable root logger name
}

# Initialize Circular Exchange logging config
_logging_registry = PackageRegistry() if CIRCULAR_EXCHANGE_AVAILABLE else None

def _init_logging_config():
    """Initialize logging configuration with Circular Exchange."""
    if _logging_registry is None:
        return
    try:
        _logging_registry.create_package(
            name='logging.level',
            initial_value=_CONFIG['level'],
            source_module='shared.utils.centralized_logging'
        )
        _logging_registry.create_package(
            name='logging.format',
            initial_value=_CONFIG['format'],
            source_module='shared.utils.centralized_logging'
        )
    except Exception:
        pass  # Ignore errors during init

_init_logging_config()
_register_logging_module()

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


class DataCollectorHandler(logging.Handler):
    """
    Logging handler that sends log entries to the DataCollector for analysis.
    
    This handler captures log entries and forwards them to the centralized
    data collection system for:
    - Pattern analysis
    - Error tracking
    - Continuous improvement insights
    - Model fine-tuning data
    """
    
    def __init__(self):
        super().__init__()
        self._data_collector = None
        self._initialized = False
    
    def _lazy_init(self):
        """Lazy initialization to avoid circular imports."""
        if self._initialized:
            return
        try:
            from shared.circular_exchange.data_collector import DATA_COLLECTOR, LogEntry
            self._data_collector = DATA_COLLECTOR
            self._log_entry_class = LogEntry
            self._initialized = True
        except ImportError:
            self._initialized = True  # Mark as initialized to avoid repeated attempts
    
    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record to the data collector."""
        self._lazy_init()
        
        if self._data_collector is None:
            return
        
        try:
            # Get context
            context = get_context()
            
            # Create LogEntry
            entry = self._log_entry_class(
                log_id=str(uuid.uuid4()),
                level=record.levelname,
                message=record.getMessage(),
                module=record.module,
                function=record.funcName,
                line_number=record.lineno,
                correlation_id=context.get('correlation_id'),
                user_id=context.get('user_id'),
                request_id=context.get('request_id'),
                exception_info=self.formatException(record.exc_info) if record.exc_info else None,
                extra_data=context.copy()
            )
            
            # Record to data collector
            self._data_collector.record_log_entry(entry)
            
        except Exception:
            # Never let data collection errors affect the application
            pass


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
            
            # Get or create root logger for our app (configurable via LOG_APP_NAME env var)
            app_name = _CONFIG['app_name']
            root_logger = logging.getLogger(app_name)
            root_logger.setLevel(getattr(logging, _CONFIG['level']))
            
            # Clear existing handlers
            root_logger.handlers.clear()
            
            # Create formatters based on LOG_FORMAT env var
            # Supports: json, syslog, clf, cisco, text
            log_format = _CONFIG['format'].lower()
            
            if log_format == 'syslog':
                from shared.utils.standard_logging import SyslogFormatter
                file_formatter = SyslogFormatter(app_name=app_name)
                console_formatter = SyslogFormatter(app_name=app_name)
            elif log_format == 'clf':
                from shared.utils.standard_logging import CLFFormatter
                file_formatter = CLFFormatter()
                console_formatter = CLFFormatter()
            elif log_format == 'cisco':
                from shared.utils.standard_logging import CiscoFormatter
                file_formatter = CiscoFormatter(facility=app_name[:3].upper())
                console_formatter = CiscoFormatter(facility=app_name[:3].upper())
            elif log_format == 'json':
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
            
            # Add data collector handler for continuous improvement
            if os.getenv('ENABLE_DATA_COLLECTION', 'true').lower() == 'true':
                try:
                    data_collector_handler = DataCollectorHandler()
                    data_collector_handler.setLevel(logging.INFO)  # Collect INFO and above
                    root_logger.addHandler(data_collector_handler)
                except Exception as e:
                    pass  # Silently skip if data collector is not available
            
            self._configured = True
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get or create a logger with the given name."""
        self.configure()
        
        if name in self._loggers:
            return self._loggers[name]
        
        # Create logger as child of our root logger (uses configurable app name)
        app_name = _CONFIG['app_name']
        if not name.startswith(app_name):
            full_name = f'{app_name}.{name}'
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


# Additional utilities from logger.py (consolidated)
def generate_correlation_id() -> str:
    """Generate a unique correlation ID for request tracing."""
    return str(uuid.uuid4())


def log_function_call(logger: Optional[logging.Logger] = None, level: str = 'DEBUG'):
    """
    Decorator to log function entry and exit.
    
    Args:
        logger: Logger instance. If None, uses module's logger.
        level: Log level for the messages
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            _logger = logger or get_module_logger(func.__module__)
            func_name = func.__name__
            log_method = getattr(_logger, level.lower())
            log_method(f"Entering {func_name}")
            try:
                result = func(*args, **kwargs)
                log_method(f"Exiting {func_name} successfully")
                return result
            except Exception as e:
                _logger.exception(f"Exception in {func_name}: {e}")
                raise
        return wrapper
    return decorator


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
    """
    from datetime import datetime
    start_time = datetime.now()
    log_method = getattr(logger, level.lower())
    correlation_id = get_context().get('correlation_id')
    if not correlation_id:
        set_context(correlation_id=generate_correlation_id())
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


class LogContext:
    """
    Context manager for adding contextual information to logs.
    Backward compatibility wrapper for logging_context.
    
    Example:
        with LogContext(request_id='abc123', user_id='user456'):
            logger.info('Processing request')
    """
    def __init__(self, **kwargs):
        self.context = kwargs
        self._previous_context = None
    
    def __enter__(self):
        self._previous_context = getattr(_context, 'data', {}).copy()
        set_context(**self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        _context.data = self._previous_context if self._previous_context else {}
        return False
    
    @staticmethod
    def get(key, default=None):
        """Get a value from the current log context."""
        return get_context().get(key, default)
    
    @staticmethod
    def get_all():
        """Get all current context values."""
        return get_context()
    
    @staticmethod
    def set(key, value):
        """Set a value in the current log context."""
        set_context(**{key: value})
    
    @staticmethod
    def clear():
        """Clear all context data."""
        clear_context()


def setup_logger(
    name: str,
    level: str = 'INFO',
    log_dir: str = 'logs',
    use_json: bool = False,
    console_output: bool = True,
    file_output: bool = True,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> logging.Logger:
    """
    Create and configure a production-ready logger.
    Wrapper for compatibility with logger.py API.
    """
    import logging.handlers
    from pathlib import Path
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    if logger.handlers:
        return logger
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    if file_output:
        log_file = log_path / f'{name.replace(".", "_")}.log'
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8'
        )
        if use_json:
            file_handler.setFormatter(StructuredJSONFormatter())
        else:
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ))
        logger.addHandler(file_handler)
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        if use_json:
            console_handler.setFormatter(StructuredJSONFormatter())
        else:
            console_handler.setFormatter(ColoredTextFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            ))
        logger.addHandler(console_handler)
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get an existing logger by name. Alias for compatibility."""
    return logging.getLogger(name)


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
    # Added from logger.py consolidation
    'generate_correlation_id',
    'log_function_call',
    'log_operation',
    'LogContext',
    'setup_logger',
    'get_logger',
]
