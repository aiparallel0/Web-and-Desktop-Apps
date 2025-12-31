"""
=============================================================================
BASE HANDLER UTILITIES - Common Patterns for Storage and Training Handlers
=============================================================================

Provides common utilities for handler classes including:
- Environment variable loading with defaults
- Configuration validation helpers
- Common initialization patterns
- Retry logic with exponential backoff
- OAuth flow helpers

Usage:
    from shared.utils.base_handler import load_env_config, RetryMixin
    
    class MyHandler(RetryMixin):
        def __init__(self):
            self.config = load_env_config({
                'api_key': 'MY_API_KEY',
                'secret': 'MY_SECRET'
            })
=============================================================================
"""

import os
import time
import logging
from typing import Dict, Any, Optional, Callable, TypeVar, List
from functools import wraps
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""
    pass

def load_env_config(
    env_map: Dict[str, str],
    defaults: Dict[str, Any] = None,
    required: List[str] = None
) -> Dict[str, Any]:
    """
    Load configuration from environment variables.
    
    Args:
        env_map: Mapping of config keys to environment variable names
                 e.g., {'api_key': 'AWS_ACCESS_KEY_ID'}
        defaults: Default values for optional configs
        required: List of required config keys
        
    Returns:
        Dictionary of configuration values
        
    Raises:
        ConfigurationError: If required config is missing
    """
    config = {}
    defaults = defaults or {}
    required = required or []
    
    for key, env_var in env_map.items():
        value = os.getenv(env_var)
        if value is None:
            if key in defaults:
                config[key] = defaults[key]
            elif key in required:
                raise ConfigurationError(
                    f"Required configuration '{key}' not found. "
                    f"Set environment variable '{env_var}'"
                )
        else:
            config[key] = value
    
    return config

def validate_required_fields(
    obj: Any,
    required_fields: List[str],
    obj_name: str = "object"
) -> None:
    """
    Validate that required fields are present and not None.
    
    Args:
        obj: Object to validate (dict or object with attributes)
        required_fields: List of required field names
        obj_name: Name of object for error messages
        
    Raises:
        ConfigurationError: If any required field is missing or None
    """
    missing = []
    
    for field in required_fields:
        if isinstance(obj, dict):
            if field not in obj or obj[field] is None:
                missing.append(field)
        else:
            if not hasattr(obj, field) or getattr(obj, field) is None:
                missing.append(field)
    
    if missing:
        raise ConfigurationError(
            f"{obj_name} missing required fields: {', '.join(missing)}"
        )

@dataclass
class ExponentialBackoff:
    """Configuration for exponential backoff retry logic."""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number."""
        import random
        
        delay = min(
            self.base_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        
        if self.jitter:
            delay = delay * (0.5 + random.random() * 0.5)
        
        return delay

T = TypeVar('T')

class RetryMixin:
    """
    Mixin class providing retry functionality with exponential backoff.
    
    Usage:
        class MyHandler(RetryMixin):
            def __init__(self):
                self.backoff = ExponentialBackoff(max_retries=3)
            
            def fetch_data(self):
                return self.retry_with_backoff(self._fetch_data_impl)
    """
    
    def retry_with_backoff(
        self,
        func: Callable[..., T],
        *args,
        backoff: Optional[ExponentialBackoff] = None,
        retry_exceptions: tuple = (Exception,),
        **kwargs
    ) -> T:
        """
        Execute function with exponential backoff retry.
        
        Args:
            func: Function to execute
            *args: Function arguments
            backoff: Backoff configuration (uses default if None)
            retry_exceptions: Tuple of exceptions to retry on
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries fail
        """
        if backoff is None:
            backoff = ExponentialBackoff()
        
        last_exception = None
        
        for attempt in range(backoff.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except retry_exceptions as e:
                last_exception = e
                
                if attempt < backoff.max_retries:
                    delay = backoff.calculate_delay(attempt)
                    logger.warning(
                        f"Attempt {attempt + 1}/{backoff.max_retries + 1} failed: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"All {backoff.max_retries + 1} attempts failed. "
                        f"Last error: {e}"
                    )
        
        raise last_exception

def retry_on_exception(
    max_retries: int = 3,
    base_delay: float = 1.0,
    retry_exceptions: tuple = (Exception,)
):
    """
    Decorator to add retry logic to a function.
    
    Args:
        max_retries: Maximum number of retries
        base_delay: Base delay in seconds
        retry_exceptions: Tuple of exceptions to retry on
        
    Usage:
        @retry_on_exception(max_retries=3, base_delay=1.0)
        def fetch_data():
            # ... might fail temporarily
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            backoff = ExponentialBackoff(
                max_retries=max_retries,
                base_delay=base_delay
            )
            
            retry_mixin = RetryMixin()
            return retry_mixin.retry_with_backoff(
                func,
                *args,
                backoff=backoff,
                retry_exceptions=retry_exceptions,
                **kwargs
            )
        
        return wrapper
    
    return decorator

class OAuthFlowHelper:
    """
    Helper for common OAuth flow patterns.
    
    Provides utilities for:
    - Generating authorization URLs
    - Handling callback codes
    - Managing token refresh
    """
    
    @staticmethod
    def build_auth_url(
        auth_uri: str,
        client_id: str,
        redirect_uri: str,
        scopes: List[str],
        state: Optional[str] = None,
        extra_params: Dict[str, str] = None
    ) -> str:
        """
        Build OAuth authorization URL.
        
        Args:
            auth_uri: OAuth provider's authorization endpoint
            client_id: OAuth client ID
            redirect_uri: Redirect URI after authorization
            scopes: List of requested scopes
            state: Optional state parameter for CSRF protection
            extra_params: Additional query parameters
            
        Returns:
            Complete authorization URL
        """
        from urllib.parse import urlencode
        
        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(scopes)
        }
        
        if state:
            params['state'] = state
        
        if extra_params:
            params.update(extra_params)
        
        return f"{auth_uri}?{urlencode(params)}"
    
    @staticmethod
    def validate_state(
        received_state: Optional[str],
        expected_state: Optional[str]
    ) -> bool:
        """
        Validate OAuth state parameter for CSRF protection.
        
        Args:
            received_state: State received from OAuth callback
            expected_state: Expected state value
            
        Returns:
            True if states match (or both None)
        """
        if expected_state is None:
            return True
        
        return received_state == expected_state

def log_handler_event(
    handler_name: str,
    event: str,
    details: Dict[str, Any] = None,
    level: str = "info"
):
    """
    Log handler events in a standardized format.
    
    Args:
        handler_name: Name of the handler (e.g., "S3Storage", "HFTrainer")
        event: Event description (e.g., "initialized", "upload_complete")
        details: Additional event details
        level: Log level (debug, info, warning, error)
    """
    log_func = getattr(logger, level.lower(), logger.info)
    message = f"[{handler_name}] {event}"
    
    if details:
        message += f" | {details}"
    
    log_func(message)
