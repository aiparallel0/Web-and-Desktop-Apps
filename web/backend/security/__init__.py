"""
=============================================================================
SECURITY MODULE - Security Hardening Components
=============================================================================

Provides security features for the application:
- Rate limiting
- Input validation
- Security headers
- Request validation

=============================================================================
"""

from .rate_limiting import RateLimiter, rate_limit, create_limiter
from .validation_schemas import (
    validate_request,
    ValidationError,
    sanitize_input,
    validate_email,
    validate_model_id
)
from .headers import add_security_headers, SecurityHeadersMiddleware

__all__ = [
    # Rate limiting
    'RateLimiter',
    'rate_limit',
    'create_limiter',
    # Validation
    'validate_request',
    'ValidationError',
    'sanitize_input',
    'validate_email',
    'validate_model_id',
    # Headers
    'add_security_headers',
    'SecurityHeadersMiddleware',
]
