"""
=============================================================================
TELEMETRY UTILITIES - OpenTelemetry Helper Functions
=============================================================================

Provides helper functions and decorators for adding OpenTelemetry tracing
to functions and methods across the codebase.

Usage:
    from shared.utils.telemetry import trace_function, get_tracer
    
    @trace_function("process_receipt", attributes={"operation.type": "ocr_processing"})
    def process_receipt(image_path: str, model_id: str):
        ...

=============================================================================
"""

import logging
import functools
from typing import Callable, Dict, Any, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Circular Exchange Framework Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False

# Register module with Circular Exchange
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="shared.utils.telemetry",
            file_path=__file__,
            description="OpenTelemetry helper functions and decorators for tracing",
            dependencies=["shared.circular_exchange"],
            exports=["trace_function", "get_tracer", "record_exception", "set_span_attributes"]
        ))
    except Exception:
        pass  # Ignore registration errors

# Try to import OpenTelemetry
try:
    from web.backend.telemetry.otel_config import get_tracer as _get_tracer, OTEL_AVAILABLE
except ImportError:
    OTEL_AVAILABLE = False
    _get_tracer = None


def get_tracer(name: str = None):
    """
    Get OpenTelemetry tracer.
    
    Args:
        name: Tracer name (defaults to service name)
        
    Returns:
        Tracer instance or no-op tracer if not available
    """
    if OTEL_AVAILABLE and _get_tracer:
        return _get_tracer(name)
    
    # Return no-op tracer
    class NoOpTracer:
        def start_as_current_span(self, name, **kwargs):
            @contextmanager
            def no_op_span():
                class NoOpSpan:
                    def set_attribute(self, key, value):
                        pass
                    def add_event(self, name, attributes=None):
                        pass
                    def set_status(self, status, description=None):
                        pass
                    def record_exception(self, exception, attributes=None):
                        pass
                yield NoOpSpan()
            return no_op_span()
    
    return NoOpTracer()


def trace_function(
    span_name: str = None,
    attributes: Dict[str, Any] = None,
    record_exception: bool = True,
    set_error_status: bool = True
):
    """
    Decorator to add OpenTelemetry tracing to a function.
    
    Args:
        span_name: Name of the span (defaults to function name)
        attributes: Static attributes to add to the span
        record_exception: Whether to record exceptions in the span
        set_error_status: Whether to set span status to ERROR on exceptions
    
    Example:
        @trace_function("process_receipt", attributes={"operation.type": "ocr"})
        def process_receipt(image_path: str):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            name = span_name or f"{func.__module__}.{func.__name__}"
            
            with tracer.start_as_current_span(name) as span:
                # Set static attributes
                if attributes:
                    for key, value in attributes.items():
                        try:
                            span.set_attribute(key, value)
                        except Exception as e:
                            logger.debug(f"Failed to set attribute {key}: {e}")
                
                # Set function metadata
                try:
                    span.set_attribute("code.function", func.__name__)
                    span.set_attribute("code.namespace", func.__module__)
                except Exception:
                    pass
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    if record_exception:
                        try:
                            span.record_exception(e)
                        except Exception:
                            pass
                    
                    if set_error_status:
                        try:
                            # Import Status and StatusCode
                            if OTEL_AVAILABLE:
                                from opentelemetry.trace import Status, StatusCode
                                span.set_status(Status(StatusCode.ERROR, str(e)))
                        except Exception:
                            pass
                    
                    raise
        
        return wrapper
    return decorator


def set_span_attributes(span, attributes: Dict[str, Any]) -> None:
    """
    Safely set multiple attributes on a span.
    
    Args:
        span: OpenTelemetry span
        attributes: Dictionary of attributes to set
    """
    if not attributes:
        return
    
    for key, value in attributes.items():
        try:
            # Convert value to string if it's not a primitive type
            if value is not None and not isinstance(value, (str, int, float, bool)):
                value = str(value)
            span.set_attribute(key, value)
        except Exception as e:
            logger.debug(f"Failed to set attribute {key}: {e}")


def sanitize_attributes(attributes: Dict[str, Any], sensitive_keys: list = None) -> Dict[str, Any]:
    """
    Sanitize attributes to remove sensitive information.
    
    Args:
        attributes: Dictionary of attributes
        sensitive_keys: List of keys to sanitize (defaults to common sensitive keys)
        
    Returns:
        Sanitized dictionary
    """
    if sensitive_keys is None:
        sensitive_keys = [
            'password', 'token', 'secret', 'api_key', 'access_key',
            'authorization', 'credit_card', 'ssn', 'email'
        ]
    
    sanitized = {}
    for key, value in attributes.items():
        # Check if key contains sensitive keywords
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            sanitized[key] = "***REDACTED***"
        else:
            sanitized[key] = value
    
    return sanitized


__all__ = [
    'get_tracer',
    'trace_function',
    'set_span_attributes',
    'sanitize_attributes'
]
