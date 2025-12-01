"""
=============================================================================
CACHING MODULE - Response and Result Caching
=============================================================================

CEF Round 4: Added caching infrastructure for improved performance.

This module provides:
- LRU caching for model predictions
- Response caching with ETag support
- Database query result caching
- Cache statistics and monitoring

Integrated with Circular Exchange Framework for dynamic configuration.
=============================================================================
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

# Circular Exchange Framework Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration, PackageRegistry
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False

logger = logging.getLogger(__name__)

# Register module with Circular Exchange
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="shared.utils.cache",
            file_path=__file__,
            description="Caching infrastructure for improved performance (LRU, ETag, query caching)",
            dependencies=["shared.circular_exchange"],
            exports=["LRUCache", "cache_result", "cached_property", "ResponseCache", 
                    "get_cache_stats", "clear_all_caches"]
        ))
    except Exception:
        pass

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
        import re
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
