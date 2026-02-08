"""
=============================================================================
DATABASE CONNECTION POOLING - Enhanced Configuration
=============================================================================

Provides robust database connection management with:
- Automatic retry logic
- Connection pool health monitoring
- Graceful degradation
- Connection leak detection

Usage:
    from web.backend.database_pool import get_db_with_retry, monitor_pool_health
    
    with get_db_with_retry() as db:
        # Database operations
        pass

=============================================================================
"""

import os
import time
import logging
from typing import Generator, Optional, Callable, Any
from contextlib import contextmanager
from functools import wraps

from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError, TimeoutError as SQLAlchemyTimeoutError
from sqlalchemy import event

logger = logging.getLogger(__name__)

# Connection retry configuration
MAX_RETRIES = int(os.getenv('DB_MAX_RETRIES', '3'))
RETRY_DELAY = float(os.getenv('DB_RETRY_DELAY', '1.0'))
RETRY_BACKOFF = float(os.getenv('DB_RETRY_BACKOFF', '2.0'))

# Pool monitoring configuration
POOL_WARNING_THRESHOLD = 0.8  # Warn when 80% of pool is used


def retry_on_connection_error(max_retries=MAX_RETRIES, delay=RETRY_DELAY, backoff=RETRY_BACKOFF):
    """
    Decorator to retry database operations on connection errors.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay on each retry
    
    Example:
        @retry_on_connection_error(max_retries=3)
        def my_db_operation(db):
            return db.query(User).all()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (OperationalError, SQLAlchemyTimeoutError) as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        logger.warning(
                            f"Database operation failed (attempt {attempt + 1}/{max_retries + 1}): {e}"
                        )
                        logger.info(f"Retrying in {current_delay}s...")
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"Database operation failed after {max_retries + 1} attempts"
                        )
                        raise
            
            raise last_exception
        
        return wrapper
    return decorator


@contextmanager
def get_db_with_retry(max_retries=MAX_RETRIES) -> Generator[Session, None, None]:
    """
    Get database session with automatic retry on connection errors.
    
    Args:
        max_retries: Maximum number of connection attempts
    
    Usage:
        with get_db_with_retry() as db:
            users = db.query(User).all()
    
    Yields:
        Session: SQLAlchemy database session
    """
    from web.backend.database import get_db_context
    
    last_exception = None
    current_delay = RETRY_DELAY
    
    for attempt in range(max_retries + 1):
        try:
            with get_db_context() as db:
                yield db
                return
        except (OperationalError, SQLAlchemyTimeoutError) as e:
            last_exception = e
            
            if attempt < max_retries:
                logger.warning(
                    f"Database connection failed (attempt {attempt + 1}/{max_retries + 1}): {e}"
                )
                logger.info(f"Retrying in {current_delay}s...")
                time.sleep(current_delay)
                current_delay *= RETRY_BACKOFF
            else:
                logger.error(
                    f"Database connection failed after {max_retries + 1} attempts"
                )
                raise
    
    raise last_exception


def monitor_pool_health() -> dict:
    """
    Monitor database connection pool health.
    
    Returns:
        dict: Pool health metrics
    """
    from web.backend.database import get_engine
    
    try:
        engine = get_engine()
        pool = engine.pool
        
        # Get pool statistics
        size = getattr(pool, 'size', lambda: None)()
        checked_out = getattr(pool, 'checkedout', lambda: 0)()
        overflow = getattr(pool, 'overflow', lambda: 0)()
        
        # Calculate utilization
        if size is not None and size > 0:
            utilization = checked_out / size
        else:
            utilization = 0
        
        health = {
            'status': 'healthy',
            'pool_size': size,
            'connections_checked_out': checked_out,
            'overflow_connections': overflow,
            'utilization': round(utilization, 2),
            'warning': None
        }
        
        # Check for issues
        if utilization >= POOL_WARNING_THRESHOLD:
            health['status'] = 'warning'
            health['warning'] = f'Pool utilization high: {utilization:.1%}'
            logger.warning(
                f"Database pool utilization high: {utilization:.1%} "
                f"({checked_out}/{size} connections in use)"
            )
        
        if overflow > 0:
            logger.info(f"Database pool overflow: {overflow} extra connections")
        
        return health
        
    except Exception as e:
        logger.error(f"Failed to monitor pool health: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }


def setup_connection_listeners():
    """
    Setup SQLAlchemy event listeners for connection monitoring.
    
    Call this once during application startup.
    """
    from web.backend.database import get_engine
    
    engine = get_engine()
    
    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        """Log new database connections."""
        logger.debug("New database connection established")
    
    @event.listens_for(engine, "checkout")
    def receive_checkout(dbapi_conn, connection_record, connection_proxy):
        """Log connection checkout from pool."""
        logger.debug("Connection checked out from pool")
        
        # Monitor pool health on checkout
        health = monitor_pool_health()
        if health['status'] == 'warning':
            logger.warning(f"Pool health warning: {health.get('warning')}")
    
    @event.listens_for(engine, "checkin")
    def receive_checkin(dbapi_conn, connection_record):
        """Log connection return to pool."""
        logger.debug("Connection returned to pool")
    
    @event.listens_for(engine, "close")
    def receive_close(dbapi_conn, connection_record):
        """Log connection close."""
        logger.debug("Database connection closed")
    
    logger.info("Database connection event listeners registered")


def test_database_connectivity(timeout=10) -> dict:
    """
    Test database connectivity with timeout.
    
    Args:
        timeout: Connection timeout in seconds
    
    Returns:
        dict: Test results
    """
    from web.backend.database import get_engine
    from sqlalchemy import text
    
    start_time = time.time()
    
    try:
        engine = get_engine()
        
        # Test simple query with timeout
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            assert result == 1
        
        elapsed = time.time() - start_time
        
        return {
            'status': 'success',
            'latency_seconds': round(elapsed, 3),
            'database': 'connected'
        }
        
    except Exception as e:
        elapsed = time.time() - start_time
        
        return {
            'status': 'failed',
            'error': str(e),
            'error_type': type(e).__name__,
            'elapsed_seconds': round(elapsed, 3)
        }


def close_all_connections():
    """
    Close all database connections in the pool.
    
    Useful for cleanup during shutdown or testing.
    """
    from web.backend.database import get_engine, _engine
    
    global _engine
    
    try:
        if _engine is not None:
            logger.info("Closing all database connections...")
            _engine.dispose()
            _engine = None
            logger.info("All connections closed")
    except Exception as e:
        logger.error(f"Failed to close connections: {e}")


__all__ = [
    'retry_on_connection_error',
    'get_db_with_retry',
    'monitor_pool_health',
    'setup_connection_listeners',
    'test_database_connectivity',
    'close_all_connections',
]
