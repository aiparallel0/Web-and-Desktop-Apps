# Shared Utilities

Common utility functions and modules used across the Receipt Extractor application.

## Modules

### logger.py

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
