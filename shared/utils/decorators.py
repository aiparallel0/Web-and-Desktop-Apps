"""
Utility Decorators Module

Provides reusable decorators to reduce boilerplate code across the Receipt Extractor
application. Created as part of code optimization initiative to eliminate repetitive
patterns found in 28+ files.

Key Features:
- @circular_exchange_module: Automatic Circular Exchange Framework registration
- @retry_on_failure: Automatic retry logic with exponential backoff
- @log_execution_time: Performance monitoring
- @deprecated: Deprecation warnings for legacy code
- @handle_errors: Graceful error handling with default return values
"""
import functools
import time
import logging
import warnings
from typing import Callable, Optional, List, Any

# Circular Exchange Framework Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    try:
        from ..circular_exchange import PROJECT_CONFIG, ModuleRegistration
        CIRCULAR_EXCHANGE_AVAILABLE = True
    except ImportError:
        CIRCULAR_EXCHANGE_AVAILABLE = False
        PROJECT_CONFIG = None
        ModuleRegistration = None

logger = logging.getLogger(__name__)

# Register this module itself with Circular Exchange
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="shared.utils.decorators",
            file_path=__file__,
            description="Utility decorators for reducing boilerplate and adding cross-cutting concerns",
            dependencies=[],
            exports=["circular_exchange_module", "retry_on_failure", "log_execution_time", "deprecated", "handle_errors"]
        ))
    except Exception:
        pass  # Ignore registration errors

def circular_exchange_module(
    module_id: str,
    description: str,
    dependencies: Optional[List[str]] = None,
    exports: Optional[List[str]] = None,
    file_path: Optional[str] = None
):
    """
    Decorator to automatically register a module with the Circular Exchange Framework.

    This decorator eliminates the 15+ line boilerplate required for manual registration
    by handling the try/except/import logic automatically.

    Args:
        module_id: Unique identifier for the module (e.g., "shared.models.my_module")
        description: Human-readable description of what the module does
        dependencies: List of module IDs this module depends on
        exports: List of classes/functions this module exports
        file_path: Path to the module file (auto-detected if not provided)

    Returns:
        Decorator function that registers the module and returns the original function/class

    Example:
        >>> @circular_exchange_module(
        ...     module_id="shared.services.my_service",
        ...     description="Provides cool service functionality",
        ...     dependencies=["shared.utils.helpers"],
        ...     exports=["MyService", "process_data"]
        ... )
        ... def my_function():
        ...     return "Hello World"

    Replaces this boilerplate (15 lines):
        ```python
        try:
            from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
            CIRCULAR_EXCHANGE_AVAILABLE = True
        except ImportError:
            CIRCULAR_EXCHANGE_AVAILABLE = False

        if CIRCULAR_EXCHANGE_AVAILABLE:
            try:
                PROJECT_CONFIG.register_module(ModuleRegistration(
                    module_id="...",
                    file_path=__file__,
                    description="...",
                    dependencies=["..."],
                    exports=["..."]
                ))
            except Exception:
                pass
        ```
    """
    def decorator(obj: Any) -> Any:
        """Inner decorator that performs the actual registration."""
        if CIRCULAR_EXCHANGE_AVAILABLE:
            try:
                # Auto-detect file path if not provided
                detected_file_path = file_path
                if detected_file_path is None:
                    import inspect
                    if inspect.isfunction(obj) or inspect.isclass(obj):
                        detected_file_path = inspect.getfile(obj)
                    else:
                        detected_file_path = __file__

                PROJECT_CONFIG.register_module(ModuleRegistration(
                    module_id=module_id,
                    file_path=detected_file_path,
                    description=description,
                    dependencies=dependencies or [],
                    exports=exports or []
                ))
                logger.debug(f"Registered module '{module_id}' with Circular Exchange Framework")
            except Exception as e:
                logger.debug(f"Could not register module '{module_id}': {e}")
                pass  # Ignore registration errors

        return obj

    return decorator

def retry_on_failure(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator to automatically retry a function on failure with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff_factor: Multiplier for delay after each failure (exponential backoff)
        exceptions: Tuple of exception types to catch and retry

    Returns:
        Decorator function

    Example:
        >>> @retry_on_failure(max_attempts=3, delay=2.0)
        ... def unstable_api_call():
        ...     return requests.get("https://api.example.com/data")
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: {e}"
                        )

            # If all attempts failed, raise the last exception
            raise last_exception

        return wrapper
    return decorator

def log_execution_time(func: Callable) -> Callable:
    """
    Decorator to log the execution time of a function.

    Useful for performance monitoring and identifying bottlenecks.

    Args:
        func: Function to wrap

    Returns:
        Wrapped function that logs execution time

    Example:
        >>> @log_execution_time
        ... def expensive_computation():
        ...     time.sleep(2)
        ...     return "Done"
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.info(f"{func.__name__} completed in {elapsed:.4f} seconds")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"{func.__name__} failed after {elapsed:.4f} seconds: {e}")
            raise

    return wrapper

def deprecated(reason: str = "", alternative: Optional[str] = None):
    """
    Decorator to mark functions/classes as deprecated.

    Emits a DeprecationWarning when the decorated function is called.

    Args:
        reason: Explanation of why the function is deprecated
        alternative: Suggested replacement function/method

    Returns:
        Decorator function

    Example:
        >>> @deprecated(reason="Use new_function instead", alternative="new_function")
        ... def old_function():
        ...     return "Legacy behavior"
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            message = f"{func.__name__} is deprecated"
            if reason:
                message += f": {reason}"
            if alternative:
                message += f". Use {alternative} instead"

            warnings.warn(message, category=DeprecationWarning, stacklevel=2)
            logger.warning(message)

            return func(*args, **kwargs)

        return wrapper
    return decorator

def handle_errors(default_return: Any = None, log_traceback: bool = True):
    """
    Decorator to handle errors gracefully with optional default return value.

    Catches all exceptions, logs them, and returns a default value instead of raising.
    Useful for non-critical operations where failures should not crash the application.

    Args:
        default_return: Value to return if an exception occurs
        log_traceback: Whether to log full traceback (default: True)

    Returns:
        Decorator function

    Example:
        >>> @handle_errors(default_return={})
        ... def extract_receipt(image):
        ...     # May fail, but won't crash
        ...     return process_with_ocr(image)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_traceback:
                    logger.exception(f"Error in {func.__name__}: {e}")
                else:
                    logger.error(f"Error in {func.__name__}: {e}")
                return default_return

        return wrapper
    return decorator

__all__ = [
    'circular_exchange_module',
    'retry_on_failure',
    'log_execution_time',
    'deprecated',
    'handle_errors'
]
