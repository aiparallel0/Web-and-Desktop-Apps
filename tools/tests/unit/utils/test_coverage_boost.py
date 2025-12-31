"""
Focused Tests for Utility Functions

This file tests functional behavior of utilities and helpers:
- shared.utils.decorators - Utility decorators  
- web.backend.config - Configuration utilities

NOTE: Removed trivial import-only tests. Import failures will show up
      naturally when running functional tests.
"""
import pytest
import os
from pathlib import Path
from unittest.mock import patch


class TestWebBackendConfig:
    """Test the web backend configuration module."""

    def test_get_bool_function(self):
        """Test the _get_bool helper function."""
        import importlib.util
        
        test_dir = Path(__file__).parent.parent.parent
        config_path = test_dir / "web" / "backend" / "config.py"
        spec = importlib.util.spec_from_file_location("config", str(config_path))
        
        if spec and spec.loader:
            import sys
            config_module = importlib.util.module_from_spec(spec)
            sys.modules['web.backend.config'] = config_module
            spec.loader.exec_module(config_module)

            _get_bool = config_module._get_bool

            # Test various boolean conversions
            assert _get_bool('true') is True
            assert _get_bool('True') is True
            assert _get_bool('1') is True
            assert _get_bool('yes') is True
            assert _get_bool('false') is False
            assert _get_bool('0') is False
            assert _get_bool(True) is True
            assert _get_bool(False) is False
            assert _get_bool(None, default=True) is True

    def test_get_int_function(self):
        """Test the _get_int helper function."""
        import importlib.util
        
        test_dir = Path(__file__).parent.parent.parent
        config_path = test_dir / "web" / "backend" / "config.py"
        spec = importlib.util.spec_from_file_location("config", str(config_path))
        
        if spec and spec.loader:
            import sys
            config_module = importlib.util.module_from_spec(spec)
            sys.modules['web.backend.config'] = config_module
            spec.loader.exec_module(config_module)

            _get_int = config_module._get_int

            assert _get_int('123') == 123
            assert _get_int('0') == 0
            assert _get_int(None, default=10) == 10
            assert _get_int('invalid', default=5) == 5


class TestUtilsDecorators:
    """Test the shared.utils.decorators module."""

    def test_retry_on_failure_decorator(self):
        """Test retry_on_failure decorator."""
        from shared.utils.decorators import retry_on_failure

        call_count = 0

        @retry_on_failure(max_attempts=3, delay=0.01)
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"

        result = failing_function()
        assert result == "success"
        assert call_count == 2

    def test_log_execution_time_decorator(self):
        """Test log_execution_time decorator."""
        from shared.utils.decorators import log_execution_time

        @log_execution_time
        def timed_func():
            return "result"

        result = timed_func()
        assert result == "result"

    def test_deprecated_decorator(self):
        """Test deprecated decorator."""
        import warnings
        from shared.utils.decorators import deprecated

        @deprecated(reason="Test deprecation", alternative="new_func")
        def old_func():
            return "old"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = old_func()
            assert result == "old"
            assert len(w) >= 1

    def test_handle_errors_decorator(self):
        """Test handle_errors decorator."""
        from shared.utils.decorators import handle_errors

        @handle_errors(default_return="default")
        def error_func():
            raise Exception("Test error")

        result = error_func()
        assert result == "default"

    def test_handle_errors_no_error(self):
        """Test handle_errors decorator when no error occurs."""
        from shared.utils.decorators import handle_errors

        @handle_errors(default_return="default")
        def success_func():
            return "actual"

        result = success_func()
        assert result == "actual"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
