"""
=============================================================================
SECURITY HEADERS - HTTP Security Headers Middleware
=============================================================================

Adds security headers to all HTTP responses.

Headers added:
- Content-Security-Policy
- X-Content-Type-Options
- X-Frame-Options
- X-XSS-Protection
- Strict-Transport-Security (in production)
- Referrer-Policy

=============================================================================
"""

import os
import logging
from typing import Dict
from flask import Flask, Response

logger = logging.getLogger(__name__)


# =============================================================================
# SECURITY HEADERS CONFIGURATION
# =============================================================================

# Default Content Security Policy
DEFAULT_CSP = {
    "default-src": "'self'",
    "script-src": "'self' 'unsafe-inline'",  # Required for inline scripts in index.html
    "style-src": "'self' 'unsafe-inline'",   # Required for inline styles
    "img-src": "'self' data: blob:",
    "font-src": "'self'",
    "connect-src": "'self' https://huggingface.co https://api.stripe.com",
    "frame-ancestors": "'none'",
    "form-action": "'self'",
    "base-uri": "'self'"
}

# Production-specific CSP additions
PRODUCTION_CSP_ADDITIONS = {
    "upgrade-insecure-requests": ""
}


def build_csp_header(csp_config: Dict[str, str]) -> str:
    """Build CSP header string from configuration."""
    parts = []
    for directive, value in csp_config.items():
        if value:
            parts.append(f"{directive} {value}")
        else:
            parts.append(directive)
    return "; ".join(parts)


# =============================================================================
# SECURITY HEADERS FUNCTION
# =============================================================================

def add_security_headers(response: Response) -> Response:
    """
    Add security headers to a Flask response.
    
    Args:
        response: Flask response object
        
    Returns:
        Response with security headers added
    """
    is_production = os.getenv('FLASK_ENV') == 'production'
    
    # Content Security Policy
    csp = DEFAULT_CSP.copy()
    if is_production:
        csp.update(PRODUCTION_CSP_ADDITIONS)
    response.headers['Content-Security-Policy'] = build_csp_header(csp)
    
    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'DENY'
    
    # XSS protection (legacy, but still useful)
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Referrer policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Permissions policy (formerly Feature-Policy)
    response.headers['Permissions-Policy'] = (
        "camera=(), microphone=(), geolocation=(), payment=(self)"
    )
    
    # HSTS for production (only over HTTPS)
    if is_production:
        response.headers['Strict-Transport-Security'] = (
            'max-age=31536000; includeSubDomains; preload'
        )
    
    # Cache control for sensitive endpoints
    if 'api/auth' in response.headers.get('X-Request-Path', ''):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
    
    return response


# =============================================================================
# MIDDLEWARE CLASS
# =============================================================================

class SecurityHeadersMiddleware:
    """
    WSGI middleware to add security headers to all responses.
    
    Usage:
        app.wsgi_app = SecurityHeadersMiddleware(app.wsgi_app)
    """
    
    def __init__(self, app):
        """
        Initialize middleware.
        
        Args:
            app: WSGI application
        """
        self.app = app
        logger.info("SecurityHeadersMiddleware initialized")
    
    def __call__(self, environ, start_response):
        """Process request and add security headers to response."""
        
        def custom_start_response(status, response_headers, exc_info=None):
            # Add security headers
            security_headers = self._get_security_headers()
            
            # Convert to list if needed
            if not isinstance(response_headers, list):
                response_headers = list(response_headers)
            
            # Add our headers
            response_headers.extend(security_headers)
            
            return start_response(status, response_headers, exc_info)
        
        return self.app(environ, custom_start_response)
    
    def _get_security_headers(self):
        """Get security headers as list of tuples."""
        is_production = os.getenv('FLASK_ENV') == 'production'
        
        csp = DEFAULT_CSP.copy()
        if is_production:
            csp.update(PRODUCTION_CSP_ADDITIONS)
        
        headers = [
            ('Content-Security-Policy', build_csp_header(csp)),
            ('X-Content-Type-Options', 'nosniff'),
            ('X-Frame-Options', 'DENY'),
            ('X-XSS-Protection', '1; mode=block'),
            ('Referrer-Policy', 'strict-origin-when-cross-origin'),
            ('Permissions-Policy', 'camera=(), microphone=(), geolocation=()'),
        ]
        
        if is_production:
            headers.append((
                'Strict-Transport-Security',
                'max-age=31536000; includeSubDomains'
            ))
        
        return headers


# =============================================================================
# FLASK INTEGRATION
# =============================================================================

def init_security_headers(app: Flask):
    """
    Initialize security headers for a Flask application.
    
    Args:
        app: Flask application instance
    
    Usage:
        from security.headers import init_security_headers
        init_security_headers(app)
    """
    @app.after_request
    def add_headers(response):
        # Store request path for cache control decisions
        from flask import request
        response.headers['X-Request-Path'] = request.path
        
        return add_security_headers(response)
    
    logger.info("Security headers enabled for Flask app")


def configure_cors_headers(
    response: Response,
    allowed_origins: list = None,
    allow_credentials: bool = True
) -> Response:
    """
    Configure CORS headers for a response.
    
    Args:
        response: Flask response
        allowed_origins: List of allowed origins
        allow_credentials: Whether to allow credentials
        
    Returns:
        Response with CORS headers
    """
    from flask import request
    
    origin = request.headers.get('Origin', '')
    
    if allowed_origins is None:
        allowed_origins = os.getenv('CORS_ORIGINS', '*').split(',')
    
    if '*' in allowed_origins or origin in allowed_origins:
        response.headers['Access-Control-Allow-Origin'] = origin or '*'
    
    if allow_credentials:
        response.headers['Access-Control-Allow-Credentials'] = 'true'
    
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = (
        'Content-Type, Authorization, X-Requested-With'
    )
    response.headers['Access-Control-Max-Age'] = '86400'  # 24 hours
    
    return response
