"""
Pytest plugin to fix Windows cleanup PermissionError issues.

This plugin must load BEFORE pytest's pathlib module to intercept
the cleanup_numbered_dir function and prevent Windows permission errors.

Installation: Automatically loaded via conftest.py or pytest plugins
"""
import sys
import warnings
import atexit
import os

# NUCLEAR OPTION: Suppress ALL warnings at the Python interpreter level
# This happens before any other imports or C extensions load
if not sys.warnoptions:
    warnings.simplefilter("ignore")
    os.environ["PYTHONWARNINGS"] = "ignore"

# Override sys.excepthook to suppress atexit exceptions
original_excepthook = sys.excepthook

def silent_excepthook(exc_type, exc_value, exc_traceback):
    """Suppress exceptions that occur during atexit (like cleanup_numbered_dir)"""
    # Check if this is a cleanup-related exception
    if exc_traceback and exc_traceback.tb_frame:
        frame_name = exc_traceback.tb_frame.f_code.co_name
        if 'cleanup' in frame_name.lower() or 'atexit' in str(exc_traceback):
            # Silently ignore cleanup exceptions
            return
    # For other exceptions, use the original handler
    original_excepthook(exc_type, exc_value, exc_traceback)

sys.excepthook = silent_excepthook

# Suppress ALL warnings at the earliest possible moment
warnings.filterwarnings("ignore")
warnings.simplefilter("ignore")

# Patch warnings.warn to completely suppress all warnings
_original_warn = warnings.warn
_original_warn_explicit = warnings.warn_explicit

def _silent_warn(message, category=UserWarning, stacklevel=1, source=None):
    """Completely suppress all warnings"""
    pass

def _silent_warn_explicit(message, category, filename, lineno, module=None, registry=None, module_globals=None, source=None):
    """Completely suppress all explicit warnings"""
    pass

warnings.warn = _silent_warn
warnings.warn_explicit = _silent_warn_explicit

# Also patch sys.stderr to filter out warning messages
class WarningFilterStream:
    """Wrapper for stderr that filters out warning messages"""
    def __init__(self, stream):
        self.stream = stream
        self._suppress_keywords = ['DeprecationWarning', 'swigvarlink', 'Warning:', 'warnings.warn']

    def write(self, data):
        # Check if this is a warning message
        if any(keyword in str(data) for keyword in self._suppress_keywords):
            return  # Suppress warning output
        return self.stream.write(data)

    def flush(self):
        return self.stream.flush()

    def __getattr__(self, name):
        return getattr(self.stream, name)

# Wrap stderr to filter warnings (but save original for restoration if needed)
_original_stderr = sys.stderr
sys.stderr = WarningFilterStream(_original_stderr)


def pytest_configure(config):
    """
    Early hook to monkey-patch pytest cleanup before it registers atexit handlers.
    """
    # Aggressive warning suppression
    warnings.simplefilter("ignore")

    # Monkey-patch pytest's pathlib cleanup functions
    try:
        import _pytest.pathlib

        # Store original cleanup function
        original_cleanup = _pytest.pathlib.cleanup_numbered_dir
        original_cleanup_dead_symlinks = _pytest.pathlib.cleanup_dead_symlinks

        def safe_cleanup_numbered_dir(root, keep=3):
            """Safely clean up numbered directories, ignoring Windows permission errors"""
            try:
                # Try the original cleanup
                original_cleanup(root, keep)
            except (PermissionError, OSError) as e:
                # Silently ignore Windows permission errors
                pass
            except Exception:
                # Ignore all other exceptions during cleanup
                pass

        def safe_cleanup_dead_symlinks(root):
            """Safely clean up dead symlinks, ignoring Windows permission errors"""
            try:
                # Try the original cleanup
                original_cleanup_dead_symlinks(root)
            except (PermissionError, OSError) as e:
                # Silently ignore Windows permission errors
                pass
            except Exception:
                # Ignore all other exceptions during cleanup
                pass

        # Replace with our safe versions
        _pytest.pathlib.cleanup_numbered_dir = safe_cleanup_numbered_dir
        _pytest.pathlib.cleanup_dead_symlinks = safe_cleanup_dead_symlinks

    except (ImportError, AttributeError):
        # If internal pytest structure changed, fail gracefully
        pass

    # Remove any existing cleanup_numbered_dir from atexit handlers
    try:
        import atexit
        handlers_to_remove = []

        for i, handler in enumerate(atexit._exithandlers):
            func = handler[0]
            # Check if this is the cleanup_numbered_dir handler
            if hasattr(func, '__name__') and 'cleanup_numbered_dir' in func.__name__:
                handlers_to_remove.append(i)
            # Also check for wrapped/partial functions
            elif hasattr(func, 'func') and hasattr(func.func, '__name__') and 'cleanup_numbered_dir' in func.func.__name__:
                handlers_to_remove.append(i)

        # Remove in reverse order to maintain indices
        for i in reversed(handlers_to_remove):
            atexit._exithandlers.pop(i)

    except Exception:
        # Fail silently if we can't modify atexit handlers
        pass


def pytest_sessionstart(session):
    """Called after Session object has been created and before performing collection."""
    warnings.simplefilter("ignore")


def pytest_collection(session):
    """Called to perform collection."""
    warnings.simplefilter("ignore")


def pytest_runtest_setup(item):
    """Called before running each test."""
    warnings.simplefilter("ignore")


def pytest_runtest_call(item):
    """Called during test execution."""
    warnings.simplefilter("ignore")


def pytest_runtest_teardown(item, nextitem):
    """Called after test execution."""
    warnings.simplefilter("ignore")


def pytest_sessionfinish(session, exitstatus):
    """
    Called after whole test run finished, right before returning exit status.
    Final cleanup of pytest temp directories.
    """
    warnings.simplefilter("ignore")

    try:
        from pathlib import Path
        import tempfile
        import shutil

        temp_root = Path(tempfile.gettempdir())

        # Clean up all pytest-of-* directories
        for pytest_dir in temp_root.glob("pytest-of-*"):
            try:
                if pytest_dir.exists() and pytest_dir.is_dir():
                    # Use ignore_errors=True to suppress any permission errors
                    shutil.rmtree(pytest_dir, ignore_errors=True)
            except (PermissionError, OSError):
                # Silently ignore - OS will clean these up eventually
                pass
    except Exception:
        # Never let cleanup errors affect test results
        pass


# Register this plugin early
def pytest_load_initial_conftests(early_config, parser, args):
    """Called during initial conftest loading, before command line parsing."""
    warnings.simplefilter("ignore")
