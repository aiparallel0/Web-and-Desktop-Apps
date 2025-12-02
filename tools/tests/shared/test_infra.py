"""
Tests for the shared image processing utilities module.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
from PIL import Image
import tempfile
import os


class TestLoadAndValidateImage:
    """Tests for load_and_validate_image function."""

    def test_load_valid_rgb_image(self, tmp_path):
        from shared.utils.image_processing import load_and_validate_image
        
        # Create a test image
        img = Image.new('RGB', (100, 100), color='red')
        image_path = tmp_path / "test.png"
        img.save(str(image_path))
        
        result = load_and_validate_image(str(image_path))
        assert isinstance(result, Image.Image)
        assert result.mode == 'RGB'

    def test_load_grayscale_image(self, tmp_path):
        from shared.utils.image_processing import load_and_validate_image
        
        img = Image.new('L', (100, 100), color=128)
        image_path = tmp_path / "test_gray.png"
        img.save(str(image_path))
        
        result = load_and_validate_image(str(image_path))
        assert isinstance(result, Image.Image)
        assert result.mode == 'L'

    def test_load_rgba_converts_to_rgb(self, tmp_path):
        from shared.utils.image_processing import load_and_validate_image
        
        img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
        image_path = tmp_path / "test_rgba.png"
        img.save(str(image_path))
        
        result = load_and_validate_image(str(image_path))
        assert isinstance(result, Image.Image)
        assert result.mode == 'RGB'

    def test_file_not_found_raises_error(self):
        from shared.utils.image_processing import load_and_validate_image
        
        with pytest.raises(FileNotFoundError):
            load_and_validate_image("/nonexistent/path/image.png")

    def test_empty_file_raises_error(self, tmp_path):
        from shared.utils.image_processing import load_and_validate_image
        
        empty_file = tmp_path / "empty.png"
        empty_file.touch()
        
        with pytest.raises(ValueError):
            load_and_validate_image(str(empty_file))


class TestEnhanceImage:
    """Tests for enhance_image function."""

    def test_enhance_with_defaults(self):
        from shared.utils.image_processing import enhance_image
        
        img = Image.new('RGB', (100, 100), color='gray')
        result = enhance_image(img)
        
        assert isinstance(result, Image.Image)
        assert result.size == img.size

    def test_enhance_brightness_only(self):
        from shared.utils.image_processing import enhance_image
        
        img = Image.new('RGB', (100, 100), color='gray')
        result = enhance_image(img, enhance_brightness=True, enhance_contrast=False, sharpen=False)
        
        assert isinstance(result, Image.Image)

    def test_enhance_contrast_only(self):
        from shared.utils.image_processing import enhance_image
        
        img = Image.new('RGB', (100, 100), color='gray')
        result = enhance_image(img, enhance_brightness=False, enhance_contrast=True, sharpen=False)
        
        assert isinstance(result, Image.Image)

    def test_enhance_sharpen_only(self):
        from shared.utils.image_processing import enhance_image
        
        img = Image.new('RGB', (100, 100), color='gray')
        result = enhance_image(img, enhance_brightness=False, enhance_contrast=False, sharpen=True)
        
        assert isinstance(result, Image.Image)

    def test_enhance_no_enhancement(self):
        from shared.utils.image_processing import enhance_image
        
        img = Image.new('RGB', (100, 100), color='red')
        result = enhance_image(img, enhance_brightness=False, enhance_contrast=False, sharpen=False)
        
        assert isinstance(result, Image.Image)


class TestAssessImageQuality:
    """Tests for assess_image_quality function."""

    @patch('shared.utils.image_processing._estimate_blur')
    @patch('shared.utils.image_processing._estimate_noise')
    def test_assess_bright_image(self, mock_noise, mock_blur):
        from shared.utils.image_processing import assess_image_quality
        
        mock_blur.return_value = 150.0
        mock_noise.return_value = 10.0
        
        img = Image.new('RGB', (100, 100), color='white')
        result = assess_image_quality(img)
        
        assert 'brightness' in result
        assert 'contrast' in result
        assert 'is_bright_enough' in result
        assert result['brightness'] > 200  # White image should be bright

    @patch('shared.utils.image_processing._estimate_blur')
    @patch('shared.utils.image_processing._estimate_noise')
    def test_assess_dark_image(self, mock_noise, mock_blur):
        from shared.utils.image_processing import assess_image_quality
        
        mock_blur.return_value = 150.0
        mock_noise.return_value = 10.0
        
        img = Image.new('RGB', (100, 100), color='black')
        result = assess_image_quality(img)
        
        assert result['brightness'] < 10  # Black image should be dark
        assert result['is_bright_enough'] == False

    @patch('shared.utils.image_processing._estimate_blur')
    @patch('shared.utils.image_processing._estimate_noise')
    def test_quality_overall_good(self, mock_noise, mock_blur):
        from shared.utils.image_processing import assess_image_quality
        
        mock_blur.return_value = 150.0
        mock_noise.return_value = 10.0
        
        # Create an image with good brightness and varied content for contrast
        img = Image.new('RGB', (100, 100))
        pixels = img.load()
        for i in range(100):
            for j in range(100):
                gray = 150 + (i % 50)  # Creates variation
                pixels[i, j] = (gray, gray, gray)
        
        result = assess_image_quality(img)
        assert 'overall_quality' in result


class TestPreprocessForOcr:
    """Tests for preprocess_for_ocr function."""

    @patch('cv2.Laplacian')
    @patch('cv2.cvtColor')
    @patch('cv2.adaptiveThreshold')
    @patch('cv2.fastNlMeansDenoising')
    def test_non_aggressive_mode(self, mock_denoise, mock_thresh, mock_cvt, mock_lap):
        from shared.utils.image_processing import preprocess_for_ocr
        
        img = Image.new('RGB', (100, 100), color='white')
        mock_cvt.return_value = np.ones((100, 100), dtype=np.uint8) * 255
        mock_thresh.return_value = np.ones((100, 100), dtype=np.uint8) * 255
        mock_denoise.return_value = np.ones((100, 100), dtype=np.uint8) * 255
        
        result = preprocess_for_ocr(img, aggressive=False)
        assert isinstance(result, Image.Image)


class TestBrightnessThreshold:
    """Tests for brightness threshold constant."""

    def test_brightness_threshold_defined(self):
        from shared.utils.image_processing import BRIGHTNESS_THRESHOLD
        assert BRIGHTNESS_THRESHOLD == 100


class TestContrastThreshold:
    """Tests for contrast threshold constant."""

    def test_contrast_threshold_defined(self):
        from shared.utils.image_processing import CONTRAST_THRESHOLD
        assert CONTRAST_THRESHOLD == 40
"""
Test suite for centralized logging system
Tests for shared/utils/centralized_logging.py
"""
import pytest
import sys
import os
import json
import logging
import threading
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add shared to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'shared'))

from shared.utils.centralized_logging import (
    get_module_logger,
    set_context,
    get_context,
    clear_context,
    logging_context,
    log_errors,
    log_with_context,
    ErrorHandler,
    StructuredJSONFormatter,
    ColoredTextFormatter,
    CentralizedLoggingManager,
)


class TestGetModuleLogger:
    """Test get_module_logger function"""

    def test_get_module_logger_returns_logger(self):
        """Test that get_module_logger returns a logger instance"""
        logger = get_module_logger()
        assert logger is not None
        assert isinstance(logger, logging.Logger)

    def test_get_module_logger_with_name(self):
        """Test get_module_logger with explicit name"""
        logger = get_module_logger('test.custom.name')
        assert logger is not None
        assert 'test.custom.name' in logger.name

    def test_get_module_logger_same_name_same_instance(self):
        """Test that same name returns same logger instance"""
        logger1 = get_module_logger('test.same')
        logger2 = get_module_logger('test.same')
        # Should be the same logger (cached)
        assert logger1.name == logger2.name

    def test_get_module_logger_different_names(self):
        """Test that different names return different loggers"""
        logger1 = get_module_logger('test.logger1')
        logger2 = get_module_logger('test.logger2')
        assert logger1.name != logger2.name


class TestContextManagement:
    """Test context management functions"""

    def test_set_and_get_context(self):
        """Test setting and getting context"""
        clear_context()  # Start fresh
        set_context(request_id='123', user_id='456')
        context = get_context()
        assert context['request_id'] == '123'
        assert context['user_id'] == '456'
        clear_context()

    def test_clear_context(self):
        """Test clearing context"""
        set_context(request_id='123')
        clear_context()
        context = get_context()
        assert context == {} or 'request_id' not in context

    def test_context_is_thread_local(self):
        """Test that context is thread-local"""
        clear_context()
        results = {}

        def thread_func(thread_id):
            set_context(thread_id=thread_id)
            import time
            time.sleep(0.01)  # Small delay to ensure interleaving
            results[thread_id] = get_context().get('thread_id')

        threads = []
        for i in range(3):
            t = threading.Thread(target=thread_func, args=(f'thread_{i}',))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Each thread should have its own context
        for i in range(3):
            assert results[f'thread_{i}'] == f'thread_{i}'

        clear_context()

    def test_logging_context_manager(self):
        """Test logging_context context manager"""
        clear_context()
        
        with logging_context(request_id='abc123'):
            context = get_context()
            assert context['request_id'] == 'abc123'
        
        # Context should be cleared after exiting
        context = get_context()
        assert 'request_id' not in context or context.get('request_id') != 'abc123'

    def test_nested_logging_context(self):
        """Test nested logging context managers"""
        clear_context()
        
        with logging_context(outer='1'):
            assert get_context()['outer'] == '1'
            
            with logging_context(inner='2'):
                context = get_context()
                assert context['inner'] == '2'
            
            # Inner context should be removed
            context = get_context()
            assert context.get('outer') == '1'


class TestLogErrors:
    """Test log_errors decorator"""

    def test_log_errors_logs_exception(self, tmp_path):
        """Test that log_errors logs exceptions"""
        logger = get_module_logger('test.log_errors')
        mock_handler = Mock()
        mock_handler.level = logging.DEBUG
        logger.addHandler(mock_handler)
        logger.setLevel(logging.DEBUG)

        @log_errors(logger=logger)
        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            failing_function()

        # Handler should have been called
        assert mock_handler.handle.called

    def test_log_errors_reraise_false(self):
        """Test log_errors with reraise=False"""
        logger = get_module_logger('test.no_reraise')
        
        @log_errors(logger=logger, reraise=False)
        def failing_function():
            raise ValueError("Test error")

        # Should not raise
        result = failing_function()
        assert result is None

    def test_log_errors_reraise_true(self):
        """Test log_errors with reraise=True (default)"""
        logger = get_module_logger('test.reraise')
        
        @log_errors(logger=logger, reraise=True)
        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            failing_function()

    def test_log_errors_preserves_return_value(self):
        """Test that log_errors preserves return value on success"""
        @log_errors
        def successful_function():
            return 42

        result = successful_function()
        assert result == 42

    def test_log_errors_without_parentheses(self):
        """Test log_errors used without parentheses"""
        @log_errors
        def my_function():
            return "success"

        result = my_function()
        assert result == "success"

    def test_log_errors_with_custom_message(self):
        """Test log_errors with custom message"""
        logger = get_module_logger('test.custom_msg')
        mock_handler = Mock()
        mock_handler.level = logging.DEBUG
        logger.addHandler(mock_handler)
        logger.setLevel(logging.DEBUG)

        @log_errors(logger=logger, message="Custom error message")
        def failing_function():
            raise ValueError("Test")

        with pytest.raises(ValueError):
            failing_function()

        # Check that custom message was used
        if mock_handler.handle.called:
            record = mock_handler.handle.call_args[0][0]
            assert "Custom error message" in record.getMessage()


class TestErrorHandler:
    """Test ErrorHandler context manager"""

    def test_error_handler_logs_exception(self):
        """Test that ErrorHandler logs exceptions"""
        logger = get_module_logger('test.error_handler')
        mock_handler = Mock()
        mock_handler.level = logging.DEBUG
        logger.addHandler(mock_handler)
        logger.setLevel(logging.DEBUG)

        with pytest.raises(ValueError):
            with ErrorHandler(logger, "Test operation"):
                raise ValueError("Test error")

        assert mock_handler.handle.called

    def test_error_handler_reraise_false(self):
        """Test ErrorHandler with reraise=False"""
        logger = get_module_logger('test.handler_no_reraise')
        
        with ErrorHandler(logger, "Test operation", reraise=False) as handler:
            raise ValueError("Test error")

        # Should have captured the error
        assert handler.error is not None
        assert isinstance(handler.error, ValueError)

    def test_error_handler_no_exception(self):
        """Test ErrorHandler when no exception occurs"""
        logger = get_module_logger('test.handler_success')
        
        with ErrorHandler(logger, "Test operation") as handler:
            result = 42

        assert handler.error is None


class TestStructuredJSONFormatter:
    """Test StructuredJSONFormatter"""

    def test_formatter_creates_valid_json(self):
        """Test that formatter creates valid JSON"""
        formatter = StructuredJSONFormatter()
        
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
        data = json.loads(formatted)
        
        assert isinstance(data, dict)
        assert 'timestamp' in data
        assert 'level' in data
        assert 'message' in data

    def test_formatter_includes_required_fields(self):
        """Test that formatter includes all required fields"""
        formatter = StructuredJSONFormatter()
        
        record = logging.LogRecord(
            name='test.logger',
            level=logging.ERROR,
            pathname='test.py',
            lineno=42,
            msg='Error message',
            args=(),
            exc_info=None,
            func='test_function'
        )
        
        formatted = formatter.format(record)
        data = json.loads(formatted)
        
        assert data['level'] == 'ERROR'
        assert data['logger'] == 'test.logger'
        assert data['message'] == 'Error message'
        assert data['line'] == 42

    def test_formatter_with_exception(self):
        """Test formatter includes exception info"""
        formatter = StructuredJSONFormatter()
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            exc_info = sys.exc_info()
        
        record = logging.LogRecord(
            name='test',
            level=logging.ERROR,
            pathname='test.py',
            lineno=10,
            msg='Error',
            args=(),
            exc_info=exc_info
        )
        
        formatted = formatter.format(record)
        data = json.loads(formatted)
        
        assert 'exception' in data
        assert 'ValueError' in data['exception']

    def test_formatter_with_extra_fields(self):
        """Test formatter with extra fields"""
        formatter = StructuredJSONFormatter()
        
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
        
        assert data['user_id'] == '123'
        assert data['request_id'] == 'abc'


class TestColoredTextFormatter:
    """Test ColoredTextFormatter"""

    def test_formatter_adds_colors(self):
        """Test that formatter adds ANSI color codes"""
        formatter = ColoredTextFormatter('%(levelname)s - %(message)s')
        
        record = logging.LogRecord(
            name='test',
            level=logging.ERROR,
            pathname='test.py',
            lineno=10,
            msg='Error message',
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        
        # Should contain ANSI color code for red
        assert '\033[31m' in formatted

    def test_formatter_resets_levelname(self):
        """Test that formatter resets levelname after formatting"""
        formatter = ColoredTextFormatter('%(levelname)s')
        
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


class TestLogWithContext:
    """Test log_with_context function"""

    def test_log_with_context_adds_extra_fields(self):
        """Test that log_with_context adds extra fields"""
        logger = logging.getLogger('test.context_log')
        logger.handlers = []
        
        mock_handler = Mock()
        mock_handler.level = logging.DEBUG
        logger.addHandler(mock_handler)
        logger.setLevel(logging.INFO)
        
        log_with_context(
            logger,
            'info',
            'Test message',
            user_id='123',
            action='test'
        )
        
        assert mock_handler.handle.called
        record = mock_handler.handle.call_args[0][0]
        assert hasattr(record, 'extra_fields')
        assert record.extra_fields['user_id'] == '123'

    def test_log_with_context_different_levels(self):
        """Test log_with_context with different log levels"""
        logger = logging.getLogger('test.levels')
        logger.handlers = []
        mock_handler = Mock()
        mock_handler.level = logging.DEBUG
        logger.addHandler(mock_handler)
        logger.setLevel(logging.DEBUG)
        
        levels = ['debug', 'info', 'warning', 'error', 'critical']
        
        for level in levels:
            log_with_context(logger, level, f'Test {level}', key='value')
        
        assert mock_handler.handle.call_count == len(levels)


class TestCentralizedLoggingManager:
    """Test CentralizedLoggingManager singleton"""

    def test_manager_is_singleton(self):
        """Test that manager is a singleton"""
        manager1 = CentralizedLoggingManager()
        manager2 = CentralizedLoggingManager()
        assert manager1 is manager2

    def test_manager_creates_logger(self):
        """Test that manager creates loggers"""
        manager = CentralizedLoggingManager()
        logger = manager.get_logger('test.singleton')
        assert logger is not None
        assert isinstance(logger, logging.Logger)

    def test_manager_caches_loggers(self):
        """Test that manager caches loggers"""
        manager = CentralizedLoggingManager()
        logger1 = manager.get_logger('test.cache')
        logger2 = manager.get_logger('test.cache')
        assert logger1 is logger2


class TestIntegration:
    """Integration tests for the full logging workflow"""

    def test_full_logging_workflow(self, tmp_path):
        """Test complete logging workflow"""
        # Override log directory for testing
        import shared.utils.centralized_logging as cl
        original_config = cl._CONFIG.copy()
        cl._CONFIG['log_dir'] = str(tmp_path)
        cl._CONFIG['file_output'] = True
        cl._CONFIG['console_output'] = False
        cl._CONFIG['format'] = 'json'
        
        # Force reconfigure
        manager = CentralizedLoggingManager()
        manager._configured = False
        manager.configure(force=True)
        
        try:
            logger = get_module_logger('test.integration')
            
            # Log various messages
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            
            # Log with context
            with logging_context(request_id='test123'):
                logger.info("Contextual message")
            
            # Force flush - use configurable app name
            app_name = cl._CONFIG['app_name']
            for handler in logging.getLogger(app_name).handlers:
                handler.flush()
            
            # Verify log file was created
            log_file = tmp_path / 'application.log'
            assert log_file.exists()
            
        finally:
            # Restore original config
            cl._CONFIG.update(original_config)
            manager._configured = False

    def test_decorator_with_context(self):
        """Test log_errors decorator with logging context"""
        clear_context()
        
        @log_errors(reraise=False)
        def function_with_error():
            raise ValueError("Test error")
        
        with logging_context(request_id='ctx123'):
            result = function_with_error()
        
        assert result is None

    def test_error_handler_with_context(self):
        """Test ErrorHandler with logging context"""
        clear_context()
        logger = get_module_logger('test.handler_ctx')
        
        with logging_context(user_id='user123'):
            with ErrorHandler(logger, "Test op", reraise=False):
                raise ValueError("Test")


class TestEnvironmentConfiguration:
    """Test environment variable configuration"""

    def test_default_configuration(self):
        """Test default configuration values"""
        import shared.utils.centralized_logging as cl
        
        # These are the defaults if env vars are not set
        assert cl._CONFIG['level'] in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        assert cl._CONFIG['format'] in ['json', 'text']

    def test_log_level_setting(self):
        """Test that log level can be set via environment"""
        # This tests the configuration structure
        import shared.utils.centralized_logging as cl
        
        # The level should be a valid log level
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        assert cl._CONFIG['level'] in valid_levels

    def test_app_name_is_configurable(self):
        """Test that app name can be configured via LOG_APP_NAME"""
        import shared.utils.centralized_logging as cl
        
        # Default app name should be set
        assert 'app_name' in cl._CONFIG
        assert cl._CONFIG['app_name'] == 'receipt_extractor'  # Default value
        
        # App name is used in logger creation
        manager = CentralizedLoggingManager()
        logger = manager.get_logger('test.module')
        assert cl._CONFIG['app_name'] in logger.name
