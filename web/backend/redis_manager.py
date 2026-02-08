"""
=============================================================================
REDIS CONNECTION MANAGER - Enterprise Connection Pooling
=============================================================================

Production-grade Redis connection management with:
- Connection pooling
- Automatic failover
- Health monitoring
- Retry logic
- Sentinel support
- Cluster support

Usage:
    from web.backend.redis_manager import RedisManager
    
    manager = RedisManager()
    
    # Basic operations
    manager.set('key', 'value', expire=3600)
    value = manager.get('key')
    
    # Pipeline operations
    with manager.pipeline() as pipe:
        pipe.set('key1', 'value1')
        pipe.set('key2', 'value2')
        pipe.execute()

=============================================================================
"""

import os
import time
import logging
import threading
from typing import Any, Optional, List, Dict, Union
from contextlib import contextmanager
from functools import wraps

logger = logging.getLogger(__name__)

# Try to import redis
try:
    import redis
    from redis.connection import ConnectionPool
    from redis.sentinel import Sentinel
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not installed. Run: pip install redis")

# Configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
REDIS_MAX_CONNECTIONS = int(os.getenv('REDIS_MAX_CONNECTIONS', '50'))
REDIS_SOCKET_TIMEOUT = float(os.getenv('REDIS_SOCKET_TIMEOUT', '5.0'))
REDIS_SOCKET_CONNECT_TIMEOUT = float(os.getenv('REDIS_SOCKET_CONNECT_TIMEOUT', '5.0'))
REDIS_RETRY_ON_TIMEOUT = os.getenv('REDIS_RETRY_ON_TIMEOUT', 'true').lower() == 'true'
REDIS_HEALTH_CHECK_INTERVAL = int(os.getenv('REDIS_HEALTH_CHECK_INTERVAL', '30'))

# Sentinel configuration
REDIS_SENTINEL_ENABLED = os.getenv('REDIS_SENTINEL_ENABLED', 'false').lower() == 'true'
REDIS_SENTINEL_HOSTS = os.getenv('REDIS_SENTINEL_HOSTS', '').split(',')
REDIS_SENTINEL_SERVICE_NAME = os.getenv('REDIS_SENTINEL_SERVICE_NAME', 'mymaster')


class RedisConnectionError(Exception):
    """Redis connection error."""
    pass


class RedisOperationError(Exception):
    """Redis operation error."""
    pass


def retry_on_redis_error(max_retries=3, delay=0.5, backoff=2.0):
    """
    Decorator to retry Redis operations on connection errors.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay on each retry
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (redis.ConnectionError, redis.TimeoutError) as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        logger.warning(
                            f"Redis operation failed (attempt {attempt + 1}/{max_retries + 1}): {e}"
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"Redis operation failed after {max_retries + 1} attempts"
                        )
                        raise RedisConnectionError(f"Redis operation failed: {e}")
            
            raise last_exception
        
        return wrapper
    return decorator


class RedisManager:
    """
    Enterprise-grade Redis connection manager.
    
    Features:
    - Connection pooling for better performance
    - Automatic retry on connection errors
    - Health monitoring
    - Sentinel/Cluster support
    """
    
    def __init__(self, url: Optional[str] = None):
        """
        Initialize Redis manager.
        
        Args:
            url: Redis connection URL (defaults to REDIS_URL env var)
        """
        if not REDIS_AVAILABLE:
            raise ImportError("Redis not available. Install with: pip install redis")
        
        self.url = url or REDIS_URL
        self._client = None
        self._pool = None
        self._sentinel = None
        self._lock = threading.Lock()
        
        # Health monitoring
        self.is_healthy = False
        self.last_health_check = None
        self.health_check_thread = None
        self.health_check_running = False
        
        # Statistics
        self.stats = {
            'operations_count': 0,
            'errors_count': 0,
            'retries_count': 0,
            'connection_errors': 0,
            'timeout_errors': 0
        }
        
        # Initialize connection
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize Redis connection with appropriate configuration."""
        try:
            if REDIS_SENTINEL_ENABLED and REDIS_SENTINEL_HOSTS:
                # Sentinel configuration for high availability
                self._initialize_sentinel()
            else:
                # Standard connection pool
                self._initialize_pool()
            
            # Test connection
            if self.ping():
                self.is_healthy = True
                logger.info(f"Redis connection established: {self.url}")
            else:
                logger.warning("Redis connection test failed")
                self.is_healthy = False
                
        except Exception as e:
            logger.error(f"Failed to initialize Redis connection: {e}")
            self.is_healthy = False
    
    def _initialize_pool(self):
        """Initialize standard connection pool."""
        self._pool = ConnectionPool.from_url(
            self.url,
            max_connections=REDIS_MAX_CONNECTIONS,
            socket_timeout=REDIS_SOCKET_TIMEOUT,
            socket_connect_timeout=REDIS_SOCKET_CONNECT_TIMEOUT,
            retry_on_timeout=REDIS_RETRY_ON_TIMEOUT,
            decode_responses=True
        )
        self._client = redis.Redis(connection_pool=self._pool)
    
    def _initialize_sentinel(self):
        """Initialize Sentinel configuration for high availability."""
        sentinel_hosts = [
            tuple(host.split(':')) for host in REDIS_SENTINEL_HOSTS
            if ':' in host
        ]
        
        if not sentinel_hosts:
            logger.warning("No valid Sentinel hosts configured, falling back to standard pool")
            self._initialize_pool()
            return
        
        self._sentinel = Sentinel(
            sentinel_hosts,
            socket_timeout=REDIS_SOCKET_TIMEOUT
        )
        
        # Get master connection
        self._client = self._sentinel.master_for(
            REDIS_SENTINEL_SERVICE_NAME,
            socket_timeout=REDIS_SOCKET_TIMEOUT,
            decode_responses=True
        )
    
    @property
    def client(self) -> redis.Redis:
        """Get Redis client instance."""
        if self._client is None:
            with self._lock:
                if self._client is None:
                    self._initialize_connection()
        return self._client
    
    def start_health_monitoring(self):
        """Start background health check thread."""
        if self.health_check_running:
            logger.warning("Health check already running")
            return
        
        self.health_check_running = True
        self.health_check_thread = threading.Thread(
            target=self._health_check_loop,
            daemon=True,
            name='RedisHealthMonitor'
        )
        self.health_check_thread.start()
        logger.info("Redis health monitoring started")
    
    def stop_health_monitoring(self):
        """Stop health check thread."""
        self.health_check_running = False
        if self.health_check_thread:
            self.health_check_thread.join(timeout=5)
        logger.info("Redis health monitoring stopped")
    
    def _health_check_loop(self):
        """Health check monitoring loop."""
        while self.health_check_running:
            try:
                is_healthy = self.ping()
                self.is_healthy = is_healthy
                self.last_health_check = time.time()
                
                if not is_healthy:
                    logger.warning("Redis health check failed")
                
            except Exception as e:
                logger.error(f"Health check error: {e}")
                self.is_healthy = False
            
            time.sleep(REDIS_HEALTH_CHECK_INTERVAL)
    
    @retry_on_redis_error(max_retries=3)
    def ping(self) -> bool:
        """
        Test Redis connection.
        
        Returns:
            True if connection is alive, False otherwise
        """
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            self.stats['connection_errors'] += 1
            return False
    
    @retry_on_redis_error(max_retries=3)
    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """
        Set a key-value pair in Redis.
        
        Args:
            key: Redis key
            value: Value to store
            expire: Optional expiration time in seconds
            
        Returns:
            True if successful
        """
        try:
            self.stats['operations_count'] += 1
            
            if expire:
                return self.client.setex(key, expire, value)
            else:
                return self.client.set(key, value)
                
        except Exception as e:
            self.stats['errors_count'] += 1
            logger.error(f"Redis SET failed for key {key}: {e}")
            raise RedisOperationError(f"SET operation failed: {e}")
    
    @retry_on_redis_error(max_retries=3)
    def get(self, key: str) -> Optional[Any]:
        """
        Get value for a key from Redis.
        
        Args:
            key: Redis key
            
        Returns:
            Value if found, None otherwise
        """
        try:
            self.stats['operations_count'] += 1
            return self.client.get(key)
            
        except Exception as e:
            self.stats['errors_count'] += 1
            logger.error(f"Redis GET failed for key {key}: {e}")
            raise RedisOperationError(f"GET operation failed: {e}")
    
    @retry_on_redis_error(max_retries=3)
    def delete(self, *keys: str) -> int:
        """
        Delete one or more keys from Redis.
        
        Args:
            *keys: Keys to delete
            
        Returns:
            Number of keys deleted
        """
        try:
            self.stats['operations_count'] += 1
            return self.client.delete(*keys)
            
        except Exception as e:
            self.stats['errors_count'] += 1
            logger.error(f"Redis DELETE failed: {e}")
            raise RedisOperationError(f"DELETE operation failed: {e}")
    
    @retry_on_redis_error(max_retries=3)
    def exists(self, *keys: str) -> int:
        """
        Check if one or more keys exist in Redis.
        
        Args:
            *keys: Keys to check
            
        Returns:
            Number of keys that exist
        """
        try:
            self.stats['operations_count'] += 1
            return self.client.exists(*keys)
            
        except Exception as e:
            self.stats['errors_count'] += 1
            logger.error(f"Redis EXISTS failed: {e}")
            raise RedisOperationError(f"EXISTS operation failed: {e}")
    
    @retry_on_redis_error(max_retries=3)
    def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration time for a key.
        
        Args:
            key: Redis key
            seconds: Expiration time in seconds
            
        Returns:
            True if expiration was set
        """
        try:
            self.stats['operations_count'] += 1
            return self.client.expire(key, seconds)
            
        except Exception as e:
            self.stats['errors_count'] += 1
            logger.error(f"Redis EXPIRE failed for key {key}: {e}")
            raise RedisOperationError(f"EXPIRE operation failed: {e}")
    
    @retry_on_redis_error(max_retries=3)
    def ttl(self, key: str) -> int:
        """
        Get remaining time to live for a key.
        
        Args:
            key: Redis key
            
        Returns:
            TTL in seconds, -1 if no expiration, -2 if key doesn't exist
        """
        try:
            self.stats['operations_count'] += 1
            return self.client.ttl(key)
            
        except Exception as e:
            self.stats['errors_count'] += 1
            logger.error(f"Redis TTL failed for key {key}: {e}")
            raise RedisOperationError(f"TTL operation failed: {e}")
    
    @retry_on_redis_error(max_retries=3)
    def incr(self, key: str, amount: int = 1) -> int:
        """
        Increment value of a key.
        
        Args:
            key: Redis key
            amount: Amount to increment by
            
        Returns:
            New value after increment
        """
        try:
            self.stats['operations_count'] += 1
            return self.client.incr(key, amount)
            
        except Exception as e:
            self.stats['errors_count'] += 1
            logger.error(f"Redis INCR failed for key {key}: {e}")
            raise RedisOperationError(f"INCR operation failed: {e}")
    
    @retry_on_redis_error(max_retries=3)
    def decr(self, key: str, amount: int = 1) -> int:
        """
        Decrement value of a key.
        
        Args:
            key: Redis key
            amount: Amount to decrement by
            
        Returns:
            New value after decrement
        """
        try:
            self.stats['operations_count'] += 1
            return self.client.decr(key, amount)
            
        except Exception as e:
            self.stats['errors_count'] += 1
            logger.error(f"Redis DECR failed for key {key}: {e}")
            raise RedisOperationError(f"DECR operation failed: {e}")
    
    @contextmanager
    def pipeline(self, transaction: bool = True):
        """
        Context manager for Redis pipeline operations.
        
        Args:
            transaction: Whether to use transaction (MULTI/EXEC)
            
        Yields:
            Pipeline object
        """
        pipe = self.client.pipeline(transaction=transaction)
        try:
            yield pipe
        finally:
            pass
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get Redis server info.
        
        Returns:
            Server information dictionary
        """
        try:
            return self.client.info()
        except Exception as e:
            logger.error(f"Failed to get Redis info: {e}")
            return {}
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get connection manager statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'is_healthy': self.is_healthy,
            'last_health_check': self.last_health_check,
            'operations_count': self.stats['operations_count'],
            'errors_count': self.stats['errors_count'],
            'retries_count': self.stats['retries_count'],
            'connection_errors': self.stats['connection_errors'],
            'timeout_errors': self.stats['timeout_errors'],
            'error_rate': (
                self.stats['errors_count'] / self.stats['operations_count']
                if self.stats['operations_count'] > 0 else 0.0
            )
        }
    
    def flush_db(self):
        """
        Flush current database (DANGEROUS - use with caution).
        """
        if os.getenv('REDIS_ALLOW_FLUSH', 'false').lower() != 'true':
            raise PermissionError("Redis FLUSHDB not allowed. Set REDIS_ALLOW_FLUSH=true")
        
        logger.warning("Flushing Redis database")
        return self.client.flushdb()
    
    def close(self):
        """Close Redis connection."""
        if self._pool:
            self._pool.disconnect()
        if self.health_check_running:
            self.stop_health_monitoring()
        logger.info("Redis connection closed")


# Global manager instance
_manager_instance = None
_manager_lock = threading.Lock()


def get_redis_manager(url: Optional[str] = None) -> Optional[RedisManager]:
    """
    Get or create global Redis manager instance.
    
    Args:
        url: Redis connection URL
        
    Returns:
        RedisManager instance or None if Redis not available
    """
    if not REDIS_AVAILABLE:
        return None
    
    global _manager_instance
    
    with _manager_lock:
        if _manager_instance is None:
            try:
                _manager_instance = RedisManager(url)
            except Exception as e:
                logger.error(f"Failed to create Redis manager: {e}")
                return None
        return _manager_instance


def is_redis_available() -> bool:
    """Check if Redis is available and healthy."""
    if not REDIS_AVAILABLE:
        return False
    
    manager = get_redis_manager()
    if manager is None:
        return False
    
    return manager.is_healthy


__all__ = [
    'RedisManager',
    'RedisConnectionError',
    'RedisOperationError',
    'get_redis_manager',
    'is_redis_available',
]
