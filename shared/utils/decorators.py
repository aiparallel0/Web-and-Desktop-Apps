"""
Utility decorators for the Receipt Extractor application

This module provides decorators to reduce boilerplate code, particularly
for Circular Exchange Framework integration.
"""
import functools
import logging
from typing import List, Optional, Callable, Union, Type

logger = logging.getLogger(__name__)


def circular_exchange_module(
    module_id: str,
    description: str,
    dependencies: Optional[List[str]] = None,
    exports: Optional[List[str]] = None
):
    """
    Decorator to automatically register a module with the Circular Exchange Framework.

    This eliminates the boilerplate try/except/if CIRCULAR_EXCHANGE_AVAILABLE pattern
    that was repeated across 28+ files.

    Args:
        module_id: Unique identifier for the module (e.g., "shared.models.ocr")
        description: Brief description of module functionality
        dependencies: List of module dependencies
        exports: List of exported classes/functions

    Usage:
        @circular_exchange_module(
            module_id="shared.models.ocr",
            description="OCR processing utilities",
            dependencies=["shared.utils.image"],
            exports=["OCRProcessor", "normalize_price"]
        )
        class OCRProcessor:
            pass

        Or on module level:

        @circular_exchange_module(
            module_id="shared.utils.helpers",
            description="Helper utilities"
        )
        def register_module():
            pass
        register_module.__file__ = __file__
    """
    def decorator(func_or_class: Union[Callable, Type]):
        try:
            from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration

            # Get the file path from the decorated object's module
            import inspect
            file_path = inspect.getfile(func_or_class)

            try:
                PROJECT_CONFIG.register_module(ModuleRegistration(
                    module_id=module_id,
                    file_path=file_path,
                    description=description,
                    dependencies=dependencies or [],
                    exports=exports or []
                ))
                logger.debug(f"Registered module {module_id} with Circular Exchange")
            except Exception as e:
                logger.debug(f"Failed to register {module_id} with Circular Exchange: {e}")

        except ImportError:
            logger.debug("Circular Exchange Framework not available")

        return func_or_class

    return decorator


def retry_on_failure(max_retries: int = 3, delay: float = 1.0,
                    exceptions: tuple = (Exception,)):
    """
    Decorator to retry a function on failure.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
        exceptions: Tuple of exceptions to catch

    Usage:
        @retry_on_failure(max_retries=3, delay=2.0)
        def unreliable_api_call():
            # May fail occasionally
            pass
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time

            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}"
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"{func.__name__} failed after {max_retries + 1} attempts"
                        )

            raise last_exception

        return wrapper

    return decorator


def log_execution_time(func: Callable):
    """
    Decorator to log the execution time of a function.

    Usage:
        @log_execution_time
        def slow_function():
            time.sleep(5)
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        import time
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.2f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.2f}s: {e}")
            raise

    return wrapper


def deprecated(alternative: Optional[str] = None):
    """
    Decorator to mark a function as deprecated.

    Args:
        alternative: Suggested alternative function/method

    Usage:
        @deprecated(alternative="new_function")
        def old_function():
            pass
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            msg = f"{func.__name__} is deprecated"
            if alternative:
                msg += f". Use {alternative} instead"
            logger.warning(msg)
            return func(*args, **kwargs)

        return wrapper

    return decorator
