"""
Test that utils package can be imported without heavy dependencies.
"""
import pytest
import sys


def test_utils_helpers_import_without_numpy():
    """Test that utils helpers can be imported even without numpy."""
    # Remove numpy from sys.modules if it exists
    numpy_in_modules = 'numpy' in sys.modules
    if numpy_in_modules:
        # We can't actually test this if numpy is already imported
        pytest.skip("numpy already imported - cannot test without it")
    
    try:
        from shared.utils.helpers import ErrorCategory, create_error_response
        assert ErrorCategory is not None
        assert create_error_response is not None
    except ImportError as e:
        if 'numpy' in str(e):
            pytest.fail(f"Utils helpers should not require numpy at import time: {e}")
        raise


def test_utils_package_exports():
    """Test that utils package exports expected symbols."""
    from shared.utils import (
        ErrorCategory, ErrorCode, ReceiptExtractorError,
        get_module_logger, LRUCache
    )
    
    assert ErrorCategory is not None
    assert ErrorCode is not None
    assert ReceiptExtractorError is not None
    assert get_module_logger is not None
    assert LRUCache is not None


def test_image_functions_available_but_may_fail():
    """Test that image functions are available but give helpful errors."""
    from shared.utils import load_and_validate_image
    
    # Function should be importable
    assert load_and_validate_image is not None
    
    # If numpy is not available, should give helpful error
    try:
        # Try to use it (will fail for missing file or numpy)
        load_and_validate_image('nonexistent.jpg')
    except ImportError as e:
        # Should have helpful message
        assert 'numpy' in str(e).lower() or 'pillow' in str(e).lower()
    except FileNotFoundError:
        # OK - means numpy was available
        pass
    except Exception:
        # Other exceptions are OK - we're just testing import behavior
        pass


def test_critical_ci_imports():
    """Test the imports that CI validates."""
    import sys
    sys.path.insert(0, '.')
    
    from shared.circular_exchange import PROJECT_CONFIG
    assert PROJECT_CONFIG is not None
    
    from shared.models.schemas import DetectionResult
    assert DetectionResult is not None
    
    from shared.utils.helpers import ErrorCategory
    assert ErrorCategory is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
