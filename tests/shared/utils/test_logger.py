"""
Test suite for logging utilities
Tests coverage for shared/utils/logger.py
"""
import pytest
import sys
import os
import logging
import json
from pathlib import Path
from unittest.mock import Mock, patch

# Add shared to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / 'shared'))

from utils.logger import (
    setup_logger,
    get_logger,
    log_with_context,
    StructuredFormatter,
    ColoredFormatter
)


class TestStructuredFormatter:
    """Test structured JSON log formatter"""

    def test_structured_formatter_creates_json(self):
        """Test that formatter creates valid JSON"""
        formatter = StructuredFormatter()

        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=10,
            msg='Test message',
            args=(),
            exc_info=None
        )

        formatted = formatter.format(record)

        # Should be valid JSON
        data = json.loads(formatted)
        assert isinstance(data, dict)

    def test_structured_formatter_includes_required_fields(self):
        """Test that formatter includes required fields"""
        formatter = StructuredFormatter()

        record = logging.LogRecord(
            name='test_logger',
            level=logging.INFO,
            pathname='test.py',
            lineno=42,
            msg='Test message',
            args=(),
            exc_info=None,
            func='test_function'
        )

        formatted = formatter.format(record)
        data = json.loads(formatted)

        assert 'timestamp' in data
        assert 'level' in data
        assert 'logger' in data
        assert 'message' in data
        assert 'module' in data
        assert 'function' in data
        assert 'line' in data

    def test_structured_formatter_log_levels(self):
        """Test formatter with different log levels"""
        formatter = StructuredFormatter()

        levels = [
            (logging.DEBUG, 'DEBUG'),
            (logging.INFO, 'INFO'),
            (logging.WARNING, 'WARNING'),
            (logging.ERROR, 'ERROR'),
            (logging.CRITICAL, 'CRITICAL')
        ]

        for level_num, level_name in levels:
            record = logging.LogRecord(
                name='test',
                level=level_num,
                pathname='test.py',
                lineno=10,
                msg='Test',
                args=(),
                exc_info=None
            )

            formatted = formatter.format(record)
            data = json.loads(formatted)

            assert data['level'] == level_name

    def test_structured_formatter_with_exception(self):
        """Test formatter includes exception information"""
        formatter = StructuredFormatter()

        try:
            raise ValueError("Test exception")
        except ValueError:
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name='test',
            level=logging.ERROR,
            pathname='test.py',
            lineno=10,
            msg='Error occurred',
            args=(),
            exc_info=exc_info
        )

        formatted = formatter.format(record)
        data = json.loads(formatted)

        assert 'exception' in data
        assert 'ValueError' in data['exception']

    def test_structured_formatter_with_extra_fields(self):
        """Test formatter with extra fields"""
        formatter = StructuredFormatter()

        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=10,
            msg='Test',
            args=(),
            exc_info=None
        )

        record.extra_fields = {'user_id': '123', 'request_id': 'abc'}

        formatted = formatter.format(record)
        data = json.loads(formatted)

        assert 'user_id' in data
        assert data['user_id'] == '123'
        assert 'request_id' in data
        assert data['request_id'] == 'abc'


class TestColoredFormatter:
    """Test colored console log formatter"""

    def test_colored_formatter_adds_colors(self):
        """Test that formatter adds color codes"""
        formatter = ColoredFormatter('%(levelname)s - %(message)s')

        levels_with_colors = [
            (logging.DEBUG, '\033[36m'),  # Cyan
            (logging.INFO, '\033[32m'),   # Green
            (logging.WARNING, '\033[33m'), # Yellow
            (logging.ERROR, '\033[31m'),  # Red
            (logging.CRITICAL, '\033[35m'), # Magenta
        ]

        for level, color_code in levels_with_colors:
            record = logging.LogRecord(
                name='test',
                level=level,
                pathname='test.py',
                lineno=10,
                msg='Test message',
                args=(),
                exc_info=None
            )

            formatted = formatter.format(record)
            assert color_code in formatted

    def test_colored_formatter_resets_color(self):
        """Test that formatter resets color at end"""
        formatter = ColoredFormatter('%(levelname)s - %(message)s')

        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=10,
            msg='Test',
            args=(),
            exc_info=None
        )

        formatted = formatter.format(record)
        # Should contain reset code
        assert '\033[0m' in formatted or 'RESET' in str(formatter.RESET)

    def test_colored_formatter_preserves_levelname(self):
        """Test that original levelname is preserved"""
        formatter = ColoredFormatter('%(levelname)s')

        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=10,
            msg='Test',
            args=(),
            exc_info=None
        )

        original_levelname = record.levelname
        formatter.format(record)

        # Levelname should be restored
        assert record.levelname == original_levelname


class TestSetupLogger:
    """Test logger setup function"""

    def test_setup_logger_creates_logger(self, tmp_path):
        """Test that setup_logger creates a logger"""
        logger = setup_logger(
            'test_logger',
            level='INFO',
            log_dir=str(tmp_path),
            console_output=False
        )

        assert logger is not None
        assert logger.name == 'test_logger'
        assert logger.level == logging.INFO

    def test_setup_logger_creates_log_file(self, tmp_path):
        """Test that setup_logger creates log file"""
        logger = setup_logger(
            'test_file_logger',
            log_dir=str(tmp_path),
            console_output=False
        )

        # Write a log message
        logger.info("Test message")

        # Check file was created
        log_file = tmp_path / 'test_file_logger.log'
        assert log_file.exists()

    def test_setup_logger_log_levels(self, tmp_path):
        """Test different log levels"""
        levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

        for level in levels:
            logger = setup_logger(
                f'test_{level.lower()}',
                level=level,
                log_dir=str(tmp_path),
                console_output=False
            )

            assert logger.level == getattr(logging, level)

    def test_setup_logger_json_format(self, tmp_path):
        """Test JSON logging format"""
        logger = setup_logger(
            'test_json',
            log_dir=str(tmp_path),
            use_json=True,
            console_output=False
        )

        logger.info("Test JSON message")

        # Read log file
        log_file = tmp_path / 'test_json.log'
        content = log_file.read_text()

        # Should be valid JSON
        log_line = content.strip().split('\n')[0]
        data = json.loads(log_line)
        assert isinstance(data, dict)

    def test_setup_logger_console_output(self, tmp_path):
        """Test console output option"""
        # With console output
        logger_with_console = setup_logger(
            'test_with_console',
            log_dir=str(tmp_path),
            console_output=True
        )

        # Without console output
        logger_without_console = setup_logger(
            'test_without_console',
            log_dir=str(tmp_path),
            console_output=False
        )

        # Both should exist
        assert logger_with_console is not None
        assert logger_without_console is not None

    def test_setup_logger_idempotent(self, tmp_path):
        """Test that calling setup_logger twice returns same logger"""
        logger1 = setup_logger(
            'test_idempotent',
            log_dir=str(tmp_path),
            console_output=False
        )

        logger2 = setup_logger(
            'test_idempotent',
            log_dir=str(tmp_path),
            console_output=False
        )

        # Should return same logger
        assert logger1 is logger2

    def test_setup_logger_creates_log_directory(self, tmp_path):
        """Test that log directory is created if it doesn't exist"""
        log_dir = tmp_path / 'logs' / 'nested'

        logger = setup_logger(
            'test_dir',
            log_dir=str(log_dir),
            console_output=False
        )

        # Directory should be created
        assert log_dir.exists()

    def test_setup_logger_rotating_file_handler(self, tmp_path):
        """Test that rotating file handler is used"""
        logger = setup_logger(
            'test_rotating',
            log_dir=str(tmp_path),
            console_output=False
        )

        # Write many log messages to trigger rotation
        for i in range(1000):
            logger.info(f"Message {i}" * 100)

        # Log file should exist
        log_file = tmp_path / 'test_rotating.log'
        assert log_file.exists()


class TestGetLogger:
    """Test get_logger function"""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger"""
        logger = get_logger('test_get')

        assert logger is not None
        assert isinstance(logger, logging.Logger)

    def test_get_logger_same_name_same_logger(self):
        """Test that same name returns same logger"""
        logger1 = get_logger('test_same')
        logger2 = get_logger('test_same')

        assert logger1 is logger2

    def test_get_logger_different_names(self):
        """Test that different names return different loggers"""
        logger1 = get_logger('test_a')
        logger2 = get_logger('test_b')

        assert logger1 is not logger2
        assert logger1.name != logger2.name


class TestLogWithContext:
    """Test contextual logging function"""

    def test_log_with_context_adds_extra_fields(self):
        """Test that log_with_context adds extra fields"""
        logger = logging.getLogger('test_context')
        logger.handlers = []  # Clear handlers

        # Add mock handler to capture log records with proper level attribute
        mock_handler = Mock()
        mock_handler.level = logging.DEBUG  # Set level to allow all log levels
        logger.addHandler(mock_handler)
        logger.setLevel(logging.INFO)

        # Log with context
        log_with_context(
            logger,
            'info',
            'Test message',
            user_id='123',
            request_id='abc'
        )

        # Handler should have been called
        assert mock_handler.handle.called

        # Get the log record
        log_record = mock_handler.handle.call_args[0][0]

        # Should have extra_fields
        assert hasattr(log_record, 'extra_fields')
        assert log_record.extra_fields['user_id'] == '123'
        assert log_record.extra_fields['request_id'] == 'abc'

    def test_log_with_context_different_levels(self):
        """Test log_with_context with different log levels"""
        logger = logging.getLogger('test_levels')
        logger.handlers = []
        mock_handler = Mock()
        mock_handler.level = logging.DEBUG  # Set level to allow all log levels
        logger.addHandler(mock_handler)
        logger.setLevel(logging.DEBUG)

        levels = ['debug', 'info', 'warning', 'error', 'critical']

        for level in levels:
            log_with_context(
                logger,
                level,
                f'Test {level}',
                test_field='value'
            )

        # Should have been called for each level
        assert mock_handler.handle.call_count == len(levels)


class TestLoggerIntegration:
    """Test logger integration scenarios"""

    def test_full_logging_workflow(self, tmp_path):
        """Test complete logging workflow"""
        # Setup logger
        logger = setup_logger(
            'integration_test',
            level='DEBUG',
            log_dir=str(tmp_path),
            use_json=True,
            console_output=False
        )

        # Log various messages
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        # Log with context
        log_with_context(
            logger,
            'info',
            'Contextual message',
            user='test_user',
            action='test_action'
        )

        # Verify log file
        log_file = tmp_path / 'integration_test.log'
        assert log_file.exists()

        content = log_file.read_text()
        lines = content.strip().split('\n')

        # Should have multiple log entries
        assert len(lines) >= 4

        # Each line should be valid JSON
        for line in lines:
            data = json.loads(line)
            assert 'timestamp' in data
            assert 'message' in data

    def test_logger_handles_unicode(self, tmp_path):
        """Test that logger handles unicode characters"""
        logger = setup_logger(
            'unicode_test',
            log_dir=str(tmp_path),
            console_output=False
        )

        unicode_messages = [
            "日本語のメッセージ",
            "Сообщение на русском",
            "Message with émojis 🎉",
            "مرحبا العالم"
        ]

        for msg in unicode_messages:
            logger.info(msg)

        # Log file should exist and contain content
        log_file = tmp_path / 'unicode_test.log'
        assert log_file.exists()

    def test_logger_exception_logging(self, tmp_path):
        """Test logging exceptions"""
        logger = setup_logger(
            'exception_test',
            log_dir=str(tmp_path),
            console_output=False
        )

        try:
            raise ValueError("Test exception")
        except ValueError:
            logger.exception("An error occurred")

        log_file = tmp_path / 'exception_test.log'
        content = log_file.read_text()

        # Should contain exception information
        assert 'ValueError' in content
        assert 'Test exception' in content
