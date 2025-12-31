"""
Utility helpers for the Receipt Extractor application.

This module provides:
- Circuit Breaker pattern for fault tolerance
- LRU caching utilities
- Response caching

Error handling has been moved to shared.utils.errors module.
For backward compatibility, error classes are re-exported from here.

Integrated with Circular Exchange Framework for dynamic configuration.
"""
import logging
import re
import time
import traceback
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

# Import and re-export error handling from consolidated module
from shared.utils.errors import (
    ErrorCategory,
    ErrorCode,
    ReceiptExtractorError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ProcessingError,
    RateLimitError,
    ExternalServiceError,
    ErrorResponse,
    create_error_response as _create_error_response,
    ERROR_METADATA
)

logger = logging.getLogger(__name__)

# Re-export error handling for backward compatibility
__all__ = [
    # Error handling (from shared.utils.errors)
    'ErrorCategory', 'ErrorCode', 'ReceiptExtractorError',
    'ValidationError', 'AuthenticationError', 'AuthorizationError',
    'NotFoundError', 'ProcessingError', 'RateLimitError',
    'ExternalServiceError', 'ErrorResponse', 'ERROR_METADATA',
    'create_error_response', 'create_simple_error_response',
    'handle_exception', 'register_error_handlers',
    # Circuit Breaker
    'CircuitBreakerState', 'CircuitBreakerConfig', 'CircuitBreaker',
    'get_circuit_breaker', 'get_all_circuit_breaker_states',
    # Caching
    'CacheEntry', 'LRUCache', 'get_cache', 'get_cache_stats',
    'clear_all_caches', 'cache_result', 'cached_property',
]

# Error response utilities (wrapping consolidated errors module)
def create_error_response(
    error: ReceiptExtractorError
) -> tuple:
    """Create a Flask-compatible error response tuple."""
    error.log_error()
    return error.to_dict(), error.http_status

def create_simple_error_response(
    message: str,
    status_code: int = 500,
    error_type: str = "error"
) -> tuple:
    """Create a simple error response without custom exception."""
    response = {
        'success': False,
        'error': {
            'type': error_type,
            'message': message,
            'timestamp': time.time()
        }
    }
    return response, status_code

def handle_exception(e: Exception) -> tuple:
    """Handle any exception and return appropriate response."""
    if isinstance(e, ReceiptExtractorError):
        return create_error_response(e)
    
    # Log unexpected errors with traceback
    logger.error(f"Unexpected error: {str(e)}", exc_info=True)
    
    # Return generic error for security (don't expose internal details)
    return create_simple_error_response(
        message="An unexpected error occurred",
        status_code=500,
        error_type="internal_error"
    )

# Flask error handlers
def register_error_handlers(app):
    """Register error handlers with a Flask application."""
    from flask import jsonify
    
    @app.errorhandler(ReceiptExtractorError)
    def handle_receipt_extractor_error(error):
        response, status_code = create_error_response(error)
        return jsonify(response), status_code
    
    @app.errorhandler(413)
    def handle_request_entity_too_large(error):
        return jsonify({
            'success': False,
            'error': {
                'code': ErrorCode.FILE_TOO_LARGE.value,
                'type': ErrorCategory.VALIDATION.value,
                'message': 'File size exceeds maximum limit',
                'timestamp': time.time()
            }
        }), 413
    
    @app.errorhandler(429)
    def handle_rate_limit(error):
        return jsonify({
            'success': False,
            'error': {
                'code': ErrorCode.RATE_LIMIT_EXCEEDED.value,
                'type': ErrorCategory.RATE_LIMIT.value,
                'message': 'Too many requests',
                'timestamp': time.time()
            }
        }), 429
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({
            'success': False,
            'error': {
                'code': ErrorCode.INTERNAL_ERROR.value,
                'type': ErrorCategory.INTERNAL.value,
                'message': 'Internal server error',
                'timestamp': time.time()
            }
        }), 500
    
    logger.info("Error handlers registered")

# =============================================================================
# CIRCUIT BREAKER PATTERN - Added based on CEF Round 5 analysis
# =============================================================================

class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Failing, reject requests
    HALF_OPEN = "half_open" # Testing if service recovered

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5          # Failures before opening
    success_threshold: int = 3          # Successes to close from half-open
    timeout_seconds: float = 30.0       # Time before attempting half-open
    half_open_max_calls: int = 3        # Max calls in half-open state

class CircuitBreaker:
    """
    Circuit breaker implementation for external service calls.
    
    CEF Round 5: Added to improve reliability by preventing cascading failures
    when external services become unavailable.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service failing, requests rejected immediately  
    - HALF_OPEN: Testing recovery, limited requests allowed
    
    Usage:
        breaker = CircuitBreaker("ocr_service")
        
        @breaker
        def call_ocr_service():
            # External call
            pass
    """
    
    def __init__(self, service_name: str, config: Optional[CircuitBreakerConfig] = None):
        self.service_name = service_name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.half_open_calls = 0
    
    def _should_allow_request(self) -> bool:
        """Check if request should be allowed."""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        
        if self.state == CircuitBreakerState.OPEN:
            # Check if timeout has passed
            if self.last_failure_time:
                elapsed = time.time() - self.last_failure_time
                if elapsed >= self.config.timeout_seconds:
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.half_open_calls = 0
                    self.success_count = 0
                    logger.info(f"Circuit breaker for {self.service_name} entering HALF_OPEN state")
                    return True
            return False
        
        # HALF_OPEN: Allow limited requests
        if self.half_open_calls < self.config.half_open_max_calls:
            return True
        return False
    
    def record_success(self):
        """Record a successful call."""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            self.half_open_calls += 1
            
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                logger.info(f"Circuit breaker for {self.service_name} CLOSED (service recovered)")
        else:
            # Reset failure count on success in closed state
            self.failure_count = 0
    
    def record_failure(self):
        """Record a failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            # Any failure in half-open goes back to open
            self.state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit breaker for {self.service_name} OPEN (failure in half-open)")
        elif self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit breaker for {self.service_name} OPEN (threshold reached)")
    
    def __call__(self, func):
        """Decorator to wrap function with circuit breaker."""
        from functools import wraps
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not self._should_allow_request():
                raise ExternalServiceError(
                    f"Service {self.service_name} is temporarily unavailable (circuit breaker open)",
                    service_name=self.service_name
                )
            
            try:
                result = func(*args, **kwargs)
                self.record_success()
                return result
            except Exception as e:
                self.record_failure()
                raise
        
        return wrapper
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state."""
        return {
            'service': self.service_name,
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'last_failure': self.last_failure_time
        }

# Global circuit breaker registry for service monitoring
_circuit_breakers: Dict[str, CircuitBreaker] = {}

def get_circuit_breaker(service_name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    """Get or create a circuit breaker for a service."""
    if service_name not in _circuit_breakers:
        _circuit_breakers[service_name] = CircuitBreaker(service_name, config)
    return _circuit_breakers[service_name]

def get_all_circuit_breaker_states() -> Dict[str, Dict[str, Any]]:
    """Get states of all circuit breakers (for health monitoring)."""
    return {name: breaker.get_state() for name, breaker in _circuit_breakers.items()}

# =============================================================================
# CACHING MODULE - Response and Result Caching
# =============================================================================

"""
CEF Round 4: Added caching infrastructure for improved performance.

This module provides:
- LRU caching for model predictions
- Response caching with ETag support
- Database query result caching
- Cache statistics and monitoring

Integrated with Circular Exchange Framework for dynamic configuration.
"""

import os
import time
import hashlib
import threading
import logging
from typing import Dict, Optional, Any, Callable, TypeVar
from dataclasses import dataclass, field
from functools import wraps
from collections import OrderedDict

logger = logging.getLogger(__name__)

# Type variable for generic caching
T = TypeVar('T')

# =============================================================================
# LRU CACHE IMPLEMENTATION
# =============================================================================

@dataclass
class CacheEntry:
    """Entry in the cache with metadata."""
    value: Any
    created_at: float
    accessed_at: float
    hit_count: int = 0
    size_bytes: int = 0

class LRUCache:
    """
    Thread-safe LRU (Least Recently Used) cache implementation.
    
    CEF Round 4: Core caching component for model predictions and 
    frequently accessed data.
    
    Features:
    - Thread-safe operations
    - TTL (time-to-live) support
    - Size-based eviction
    - Statistics tracking
    
    Usage:
        cache = LRUCache(max_size=100, ttl_seconds=300)
        cache.set("key", value)
        result = cache.get("key")
    """
    
    def __init__(
        self,
        max_size: int = 100,
        ttl_seconds: Optional[float] = None,
        name: str = "default"
    ):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.name = name
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache."""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            entry = self._cache[key]
            
            # Check TTL
            if self.ttl_seconds and (time.time() - entry.created_at) > self.ttl_seconds:
                del self._cache[key]
                self._misses += 1
                return None
            
            # Update access time and move to end (most recently used)
            entry.accessed_at = time.time()
            entry.hit_count += 1
            self._cache.move_to_end(key)
            self._hits += 1
            
            return entry.value
    
    def set(self, key: str, value: Any, size_bytes: int = 0) -> None:
        """Set a value in the cache."""
        with self._lock:
            # Remove if already exists
            if key in self._cache:
                del self._cache[key]
            
            # Evict if at capacity
            while len(self._cache) >= self.max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                logger.debug(f"Cache {self.name}: evicted {oldest_key}")
            
            # Add new entry
            now = time.time()
            self._cache[key] = CacheEntry(
                value=value,
                created_at=now,
                accessed_at=now,
                size_bytes=size_bytes
            )
    
    def delete(self, key: str) -> bool:
        """Delete a key from the cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all entries from the cache."""
        with self._lock:
            self._cache.clear()
            logger.info(f"Cache {self.name}: cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0
            
            return {
                'name': self.name,
                'size': len(self._cache),
                'max_size': self.max_size,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': hit_rate,
                'ttl_seconds': self.ttl_seconds
            }
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists in cache (without updating access time)."""
        return key in self._cache

# Global cache registry
_caches: Dict[str, LRUCache] = {}

def get_cache(name: str, max_size: int = 100, ttl_seconds: Optional[float] = None) -> LRUCache:
    """Get or create a named cache."""
    if name not in _caches:
        _caches[name] = LRUCache(max_size=max_size, ttl_seconds=ttl_seconds, name=name)
    return _caches[name]

def get_cache_stats() -> Dict[str, Dict[str, Any]]:
    """Get statistics for all caches."""
    return {name: cache.get_stats() for name, cache in _caches.items()}

def clear_all_caches() -> None:
    """Clear all caches."""
    for cache in _caches.values():
        cache.clear()
    logger.info("All caches cleared")

# =============================================================================
# CACHING DECORATORS
# =============================================================================

def cache_result(
    cache_name: str = "default",
    max_size: int = 100,
    ttl_seconds: Optional[float] = None,
    key_func: Optional[Callable[..., str]] = None
):
    """
    Decorator to cache function results.
    
    CEF Round 4: Easy-to-use decorator for adding caching to any function.
    
    Usage:
        @cache_result(cache_name="model_predictions", ttl_seconds=300)
        def predict(image_path: str) -> dict:
            # Expensive computation
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cache = get_cache(cache_name, max_size, ttl_seconds)
        
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default: hash of function name + args
                key_parts = [func.__name__] + [str(a) for a in args]
                key_parts += [f"{k}={v}" for k, v in sorted(kwargs.items())]
                cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
            
            # Check cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_value
            
            # Compute and cache
            result = func(*args, **kwargs)
            cache.set(cache_key, result)
            logger.debug(f"Cached result for {func.__name__}")
            
            return result
        
        # Expose cache for testing/debugging
        wrapper.cache = cache
        return wrapper
    
    return decorator

class cached_property:
    """
    Decorator for cached class properties.
    
    Similar to functools.cached_property but with TTL support.
    
    Usage:
        class Model:
            @cached_property(ttl_seconds=300)
            def expensive_data(self):
                return compute_expensive()
    """
    
    def __init__(self, func: Callable = None, ttl_seconds: Optional[float] = None):
        self.func = func
        self.ttl_seconds = ttl_seconds
        self.attr_name = None
        self.lock = threading.RLock()
    
    def __set_name__(self, owner, name):
        self.attr_name = f"_cached_{name}"
        self.time_attr = f"_cached_{name}_time"
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        
        with self.lock:
            # Check if cached value exists and is valid
            cached_value = getattr(obj, self.attr_name, None)
            cached_time = getattr(obj, self.time_attr, None)
            
            if cached_value is not None and cached_time is not None:
                if self.ttl_seconds is None or (time.time() - cached_time) < self.ttl_seconds:
                    return cached_value
            
            # Compute and cache
            value = self.func(obj)
            setattr(obj, self.attr_name, value)
            setattr(obj, self.time_attr, time.time())
            
            return value
    
    def __call__(self, func):
        self.func = func
        return self

# =============================================================================
# RESPONSE CACHING FOR API
# =============================================================================

@dataclass
class ResponseCacheEntry:
    """Cache entry for HTTP responses."""
    data: Any
    etag: str
    created_at: float
    content_type: str = "application/json"

class ResponseCache:
    """
    HTTP response cache with ETag support.
    
    CEF Round 4: Enables efficient response caching with conditional requests.
    
    Features:
    - ETag generation and validation
    - Cache-Control header support
    - Conditional GET support (If-None-Match)
    
    Usage:
        response_cache = ResponseCache(ttl_seconds=300)
        
        # In Flask route:
        @app.route('/api/data')
        def get_data():
            cache_key = f"data:{request.args}"
            
            # Check cache with ETag
            cached, etag = response_cache.get_with_etag(cache_key)
            if cached and request.headers.get('If-None-Match') == etag:
                return '', 304  # Not Modified
            
            if cached:
                return jsonify(cached), 200, {'ETag': etag}
            
            # Generate new data
            data = expensive_operation()
            etag = response_cache.set(cache_key, data)
            return jsonify(data), 200, {'ETag': etag}
    """
    
    def __init__(self, ttl_seconds: float = 300.0, max_size: int = 1000):
        self._cache: Dict[str, ResponseCacheEntry] = {}
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self._lock = threading.RLock()
    
    def _generate_etag(self, data: Any) -> str:
        """Generate ETag for data."""
        import json
        data_str = json.dumps(data, sort_keys=True, default=str)
        return f'"{hashlib.md5(data_str.encode()).hexdigest()}"'
    
    def get_with_etag(self, key: str) -> tuple:
        """Get cached value with its ETag."""
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                return None, None
            
            # Check TTL
            if (time.time() - entry.created_at) > self.ttl_seconds:
                del self._cache[key]
                return None, None
            
            return entry.data, entry.etag
    
    def set(self, key: str, data: Any, content_type: str = "application/json") -> str:
        """Cache data and return ETag."""
        with self._lock:
            # Evict if at capacity
            while len(self._cache) >= self.max_size:
                oldest_key = min(self._cache.keys(), 
                               key=lambda k: self._cache[k].created_at)
                del self._cache[oldest_key]
            
            etag = self._generate_etag(data)
            self._cache[key] = ResponseCacheEntry(
                data=data,
                etag=etag,
                created_at=time.time(),
                content_type=content_type
            )
            
            return etag
    
    def invalidate(self, key: str) -> bool:
        """Invalidate a cache entry."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all entries matching pattern."""
        with self._lock:
            regex = re.compile(pattern)
            keys_to_delete = [k for k in self._cache.keys() if regex.match(k)]
            for key in keys_to_delete:
                del self._cache[key]
            return len(keys_to_delete)
    
    def clear(self) -> None:
        """Clear all entries."""
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'ttl_seconds': self.ttl_seconds
            }

# Global response cache instance
_response_cache: Optional[ResponseCache] = None

def get_response_cache(ttl_seconds: float = 300.0) -> ResponseCache:
    """Get the global response cache instance."""
    global _response_cache
    if _response_cache is None:
        _response_cache = ResponseCache(ttl_seconds=ttl_seconds)
    return _response_cache
