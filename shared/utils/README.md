# Shared Utilities

Common utility functions and modules used across the Receipt Extractor application.

## Modules

### centralized_logging.py (Recommended)

**Centralized logging and error handling system** that follows industry best practices
used by companies like Amazon and Meta. New files automatically get logging configured
when they import from this module - no manual setup required.

#### Quick Start

```python
from shared.utils import get_module_logger, log_errors

# Get a logger - automatically uses the module name
logger = get_module_logger()

# Automatic error handling with decorator
@log_errors
def my_function():
    logger.info("Processing...")
    # Function code here

# Or with options
@log_errors(reraise=False, message="Processing failed")
def safe_function():
    # Exceptions are logged but not re-raised
    pass
```

#### Features

- **Automatic Logger Injection**: `get_module_logger()` automatically detects the calling module's name
- **Thread-Local Context**: Add request ID, user ID, etc. that appears in all logs
- **Structured JSON Logging**: Machine-parseable logs for log aggregation systems (ELK, Splunk, CloudWatch)
- **Colored Console Output**: Readable logs during development
- **Error Handling Decorators**: `@log_errors` for automatic exception logging
- **Context Manager**: `ErrorHandler` for handling errors in code blocks
- **Environment Configuration**: Configure via environment variables

#### Usage Examples

```python
from shared.utils import (
    get_module_logger,
    log_errors,
    logging_context,
    set_context,
    ErrorHandler
)

logger = get_module_logger()

# Add context that appears in all logs from this thread
set_context(request_id='abc123', user_id='user456')
logger.info("Processing request")  # Includes request_id and user_id

# Temporary context with context manager
with logging_context(operation='receipt_extraction'):
    logger.info("Starting extraction")  # Includes operation field
logger.info("After extraction")  # Does NOT include operation field

# Error handling with decorator
@log_errors
def process_receipt(image_path):
    logger.info(f"Processing {image_path}")
    # ... processing code ...
    return result

# Error handling with context manager
with ErrorHandler(logger, "Receipt processing", reraise=False):
    # If exception occurs, it's logged with context
    risky_operation()
```

#### Environment Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `LOG_FORMAT` | `json` | Format type ('json' or 'text') |
| `LOG_DIR` | `logs` | Directory for log files |
| `LOG_TO_CONSOLE` | `true` | Whether to log to console |
| `LOG_TO_FILE` | `true` | Whether to log to file |
| `LOG_MAX_BYTES` | `10485760` | Max log file size (10MB) |
| `LOG_BACKUP_COUNT` | `5` | Number of backup log files |
| `LOG_APP_NAME` | `receipt_extractor` | Root logger name (allows reuse in other projects) |

### logger.py (Legacy)

Structured logging configuration with support for:

- **Structured JSON logging** - For production environments
- **Colored console output** - For development
- **Log rotation** - Automatic log file rotation (10MB per file, 5 backups)
- **Multiple handlers** - Console and file output
- **Context logging** - Add custom fields to log entries

#### Usage

```python
from shared.utils.logger import setup_logger

# Development mode (colored console)
logger = setup_logger('my_module', level='DEBUG')
logger.info('Application started')

# Production mode (JSON structured)
logger = setup_logger('my_module', level='INFO', use_json=True)
logger.info('Processing receipt')

# Add context to logs
from shared.utils.logger import log_with_context

log_with_context(
    logger,
    'info',
    'Receipt processed successfully',
    receipt_id='12345',
    model='florence2',
    processing_time=2.5
)
```

#### Configuration Options

```python
setup_logger(
    name='module_name',         # Logger name (use __name__)
    level='INFO',               # DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_dir='logs',             # Directory for log files
    use_json=False,             # Enable JSON structured logging
    console_output=True         # Enable console output
)
```

#### Log Levels

- **DEBUG** - Detailed debugging information
- **INFO** - General informational messages
- **WARNING** - Warning messages (non-critical issues)
- **ERROR** - Error messages (failed operations)
- **CRITICAL** - Critical errors (system failures)

#### Log Files

Logs are stored in the `logs/` directory:

```
logs/
├── receipt_extractor.log
├── receipt_extractor.log.1  # Rotated backup
├── receipt_extractor.log.2
└── ...
```

### Future Utilities

Additional utilities to be added:

- `validators.py` - Input validation functions
- `file_helpers.py` - File handling utilities
- `image_helpers.py` - Image processing helpers
- `format_converters.py` - Data format conversion utilities

## Development Guidelines

### Adding New Files

New files automatically get centralized logging when they import from shared:

```python
# In any new Python file:
from shared.utils import get_module_logger, log_errors

logger = get_module_logger()  # Logger is automatically configured

@log_errors  # Exceptions are automatically logged
def my_new_function():
    logger.info("This just works!")
```

No manual logger setup, no configuration needed - it's automatic!

### Adding New Utilities

1. Create a new module in `shared/utils/`
2. Add docstrings and type hints
3. Write unit tests in `tests/shared/`
4. Update this README with usage examples

### Testing Utilities

```bash
# Run utility tests
pytest tests/shared/test_utils.py
```

## Error Handling Best Practices

### Use the Centralized Error Handling (Recommended)

```python
from shared.utils import get_module_logger, log_errors, ErrorHandler

logger = get_module_logger()

# Option 1: Decorator for entire functions
@log_errors
def extract_receipt(image_path):
    # All exceptions are automatically logged with context
    return process_image(image_path)

# Option 2: Context manager for code blocks
def complex_operation():
    with ErrorHandler(logger, "Loading model", reraise=False):
        model = load_model()  # If this fails, error is logged
    
    with ErrorHandler(logger, "Processing image"):
        result = process_image()  # If this fails, error is logged and re-raised
    
    return result

# Option 3: Custom error handling with logging
@log_errors(reraise=False, message="Receipt extraction failed")
def safe_extract(image_path):
    return extract(image_path)  # Returns None if exception occurs
```

### Use Structured Exceptions

```python
class ReceiptExtractionError(Exception):
    """Base exception for receipt extraction."""
    pass

class ModelLoadError(ReceiptExtractionError):
    """Failed to load AI model."""
    pass

class InvalidImageError(ReceiptExtractionError):
    """Invalid or corrupted image."""
    pass
```

### Log Exceptions with Context

```python
try:
    result = extract_receipt(image)
except Exception as e:
    logger.exception(
        'Receipt extraction failed',
        extra={
            'extra_fields': {
                'image_path': image_path,
                'model': model_id,
                'error_type': type(e).__name__
            }
        }
    )
    raise
```

### Graceful Error Recovery

```python
def process_with_retry(func, max_attempts=3):
    """Retry function with exponential backoff."""
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            wait_time = 2 ** attempt
            logger.warning(f'Attempt {attempt + 1} failed, retrying in {wait_time}s')
            time.sleep(wait_time)
```

## Performance Monitoring

### Timing Decorator

```python
import time
from functools import wraps

def timed_operation(logger):
    """Decorator to log operation execution time."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                log_with_context(
                    logger,
                    'info',
                    f'{func.__name__} completed',
                    duration=f'{duration:.2f}s'
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                log_with_context(
                    logger,
                    'error',
                    f'{func.__name__} failed',
                    duration=f'{duration:.2f}s',
                    error=str(e)
                )
                raise
        return wrapper
    return decorator

# Usage
@timed_operation(logger)
def extract_receipt(image_path):
    # Processing logic
    pass
```

## Resources

- [Python Logging Documentation](https://docs.python.org/3/library/logging.html)
- [Structured Logging Best Practices](https://www.structlog.org/en/stable/)
- [JSON Logging Format](https://github.com/madzak/python-json-logger)
