"""
Structured logging configuration for Receipt Extractor.

Provides consistent logging across all modules with:
- Structured JSON logging (optional)
- Console and file handlers
- Log rotation
- Different log levels for dev/prod
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
import sys
import json


class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    Outputs logs in JSON format for easier parsing and analysis.
    """

    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)

        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """
    Colored console formatter for better readability in development.
    """

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m'   # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"

        # Format the message
        formatted = super().format(record)

        # Reset levelname for subsequent formatters
        record.levelname = levelname

        return formatted


def setup_logger(
    name: str,
    level: str = 'INFO',
    log_dir: str = 'logs',
    use_json: bool = False,
    console_output: bool = True
) -> logging.Logger:
    """
    Set up a logger with file and console handlers.

    Args:
        name: Logger name (usually __name__)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
        use_json: Use JSON structured logging
        console_output: Enable console output

    Returns:
        Configured logger instance
    """

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Create log directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # File handler with rotation
    log_file = log_path / f'{name.replace(".", "_")}.log'
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)

    # Choose formatter based on configuration
    if use_json:
        file_formatter = StructuredFormatter()
        console_formatter = StructuredFormatter()
    else:
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )

    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    if console_output:
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with default configuration.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Convenience function for adding extra context to logs
def log_with_context(logger: logging.Logger, level: str, message: str, **kwargs):
    """
    Log a message with additional context fields.

    Args:
        logger: Logger instance
        level: Log level (info, warning, error, etc.)
        message: Log message
        **kwargs: Additional context fields
    """
    extra = {'extra_fields': kwargs}
    getattr(logger, level)(message, extra=extra)


# Example usage:
if __name__ == '__main__':
    # Development mode - colored console output
    logger = setup_logger('receipt_extractor', level='DEBUG', use_json=False)

    logger.debug('This is a debug message')
    logger.info('Application started')
    logger.warning('This is a warning')
    logger.error('An error occurred')

    # Production mode - JSON structured logging
    json_logger = setup_logger('receipt_extractor_prod', level='INFO', use_json=True)

    log_with_context(
        json_logger,
        'info',
        'Receipt processed',
        receipt_id='12345',
        model='florence2',
        processing_time=2.5
    )

    try:
        raise ValueError('Example error')
    except Exception as e:
        json_logger.exception('Error processing receipt')
