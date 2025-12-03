"""
=============================================================================
RATE LIMITING - Request Rate Limiting
=============================================================================

Provides rate limiting functionality to protect against abuse.

Supports multiple backends:
- In-memory (development)
- Redis (production)

Usage:
    from security.rate_limiting import rate_limit, create_limiter
    
    @app.route('/api/extract')
    @rate_limit(requests=10, window=60)  # 10 requests per minute
    def extract():
        ...

=============================================================================
"""

import os
import time
import logging
from functools import wraps
from typing import Dict, Callable, Optional, Tuple
from datetime import datetime
from collections import defaultdict
from flask import request, jsonify, g

logger = logging.getLogger(__name__)

# Try to import Redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class RateLimiter:
    """
    Rate limiter with support for multiple backends.
    
    Implements the sliding window algorithm for accurate rate limiting.
    """
    
    def __init__(
        self,
        backend: str = 'memory',
        redis_url: str = None
    ):
        """
        Initialize rate limiter.
        
        Args:
            backend: Backend type ('memory' or 'redis')
            redis_url: Redis connection URL (for redis backend)
        """
        self.backend = backend
        self._storage: Dict[str, list] = defaultdict(list)
        self._redis_client = None
        
        if backend == 'redis':
            if not REDIS_AVAILABLE:
                logger.warning("Redis not available, falling back to memory backend")
                self.backend = 'memory'
            else:
                redis_url = redis_url or os.getenv('REDIS_URL')
                if redis_url:
                    try:
                        self._redis_client = redis.from_url(redis_url)
                        self._redis_client.ping()
                        logger.info("Rate limiter connected to Redis")
                    except Exception as e:
                        logger.warning(f"Redis connection failed: {e}")
                        self.backend = 'memory'
        
        logger.info(f"RateLimiter initialized with {self.backend} backend")
    
    def is_allowed(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, Dict[str, int]]:
        """
        Check if a request is allowed under the rate limit.
        
        Args:
            key: Unique identifier (e.g., user_id, IP)
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        now = time.time()
        
        if self.backend == 'redis' and self._redis_client:
            return self._redis_check(key, max_requests, window_seconds, now)
        else:
            return self._memory_check(key, max_requests, window_seconds, now)
    
    def _memory_check(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
        now: float
    ) -> Tuple[bool, Dict[str, int]]:
        """Check rate limit using in-memory storage."""
        window_start = now - window_seconds
        
        # Clean old entries
        self._storage[key] = [
            ts for ts in self._storage[key]
            if ts > window_start
        ]
        
        request_count = len(self._storage[key])
        remaining = max(0, max_requests - request_count)
        reset_at = int(now + window_seconds)
        
        rate_info = {
            'limit': max_requests,
            'remaining': remaining,
            'reset': reset_at
        }
        
        if request_count >= max_requests:
            return False, rate_info
        
        # Record this request
        self._storage[key].append(now)
        rate_info['remaining'] = remaining - 1
        
        return True, rate_info
    
    def _redis_check(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
        now: float
    ) -> Tuple[bool, Dict[str, int]]:
        """Check rate limit using Redis backend."""
        pipe = self._redis_client.pipeline()
        
        window_start = now - window_seconds
        redis_key = f"rate_limit:{key}"
        
        # Remove old entries and count remaining
        pipe.zremrangebyscore(redis_key, '-inf', window_start)
        pipe.zcard(redis_key)
        pipe.zadd(redis_key, {str(now): now})
        pipe.expire(redis_key, window_seconds)
        
        results = pipe.execute()
        request_count = results[1]
        
        remaining = max(0, max_requests - request_count)
        reset_at = int(now + window_seconds)
        
        rate_info = {
            'limit': max_requests,
            'remaining': remaining,
            'reset': reset_at
        }
        
        if request_count >= max_requests:
            # Remove the request we just added
            self._redis_client.zrem(redis_key, str(now))
            return False, rate_info
        
        return True, rate_info
    
    def get_usage(self, key: str, window_seconds: int) -> int:
        """Get current usage count for a key."""
        now = time.time()
        window_start = now - window_seconds
        
        if self.backend == 'redis' and self._redis_client:
            redis_key = f"rate_limit:{key}"
            return self._redis_client.zcount(redis_key, window_start, now)
        else:
            return len([ts for ts in self._storage.get(key, []) if ts > window_start])
    
    def reset(self, key: str):
        """Reset rate limit for a key."""
        if self.backend == 'redis' and self._redis_client:
            self._redis_client.delete(f"rate_limit:{key}")
        else:
            self._storage.pop(key, None)


# =============================================================================
# GLOBAL LIMITER INSTANCE
# =============================================================================

_limiter: Optional[RateLimiter] = None


def create_limiter(backend: str = None, redis_url: str = None) -> RateLimiter:
    """
    Create and configure the global rate limiter.
    
    Args:
        backend: Backend type ('memory' or 'redis')
        redis_url: Redis connection URL
        
    Returns:
        RateLimiter instance
    """
    global _limiter
    
    backend = backend or os.getenv('RATE_LIMIT_BACKEND', 'memory')
    _limiter = RateLimiter(backend=backend, redis_url=redis_url)
    
    return _limiter


def get_limiter() -> RateLimiter:
    """Get or create the global rate limiter."""
    global _limiter
    
    if _limiter is None:
        _limiter = RateLimiter()
    
    return _limiter


# =============================================================================
# RATE LIMIT DECORATOR
# =============================================================================

def rate_limit(
    requests: int = 100,
    window: int = 60,
    key_func: Callable = None,
    error_message: str = "Rate limit exceeded"
):
    """
    Rate limiting decorator for Flask routes.
    
    Args:
        requests: Maximum requests allowed in window
        window: Time window in seconds
        key_func: Function to generate rate limit key (default: IP + user_id)
        error_message: Error message when limit exceeded
    
    Usage:
        @app.route('/api/extract')
        @rate_limit(requests=10, window=60)
        def extract():
            ...
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate rate limit key
            if key_func:
                key = key_func()
            else:
                # Default: Use IP + user_id if authenticated
                user_id = getattr(g, 'user_id', None)
                if user_id:
                    key = f"user:{user_id}"
                else:
                    key = f"ip:{request.remote_addr}"
            
            # Add endpoint to key for per-endpoint limiting
            key = f"{key}:{f.__name__}"
            
            limiter = get_limiter()
            is_allowed, rate_info = limiter.is_allowed(key, requests, window)
            
            # Add rate limit headers to response
            def add_headers(response):
                response.headers['X-RateLimit-Limit'] = str(rate_info['limit'])
                response.headers['X-RateLimit-Remaining'] = str(rate_info['remaining'])
                response.headers['X-RateLimit-Reset'] = str(rate_info['reset'])
                return response
            
            if not is_allowed:
                response = jsonify({
                    'success': False,
                    'error': error_message,
                    'retry_after': window
                })
                response.status_code = 429
                return add_headers(response)
            
            # Execute the function
            result = f(*args, **kwargs)
            
            # Add headers to successful response
            if hasattr(result, 'headers'):
                add_headers(result)
            elif isinstance(result, tuple) and len(result) >= 1:
                if hasattr(result[0], 'headers'):
                    add_headers(result[0])
            
            return result
        
        return decorated_function
    
    return decorator


# =============================================================================
# RATE LIMIT CONFIGURATIONS
# =============================================================================

# Default rate limits for different operations
RATE_LIMITS = {
    'default': {'requests': 100, 'window': 60},
    'auth': {'requests': 5, 'window': 60},         # 5 auth attempts per minute
    'extract': {'requests': 30, 'window': 60},     # 30 extractions per minute
    'batch': {'requests': 10, 'window': 60},       # 10 batch operations per minute
    'finetune': {'requests': 5, 'window': 3600},   # 5 finetune jobs per hour
    'api_key': {'requests': 1000, 'window': 3600}, # 1000 API requests per hour
}


def get_rate_limit_config(operation: str) -> Dict[str, int]:
    """Get rate limit configuration for an operation."""
    return RATE_LIMITS.get(operation, RATE_LIMITS['default'])
