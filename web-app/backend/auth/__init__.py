"""
Authentication and authorization module

Provides complete authentication infrastructure including:
- Password hashing with bcrypt
- JWT token creation and verification
- Route decorators for authentication and authorization
- API routes for user registration, login, and session management
"""
from .password import hash_password, verify_password, is_password_strong
from .jwt_handler import (
    create_access_token,
    create_refresh_token,
    verify_access_token,
    verify_refresh_token,
    revoke_refresh_token
)
from .decorators import require_auth, require_admin, rate_limit, require_plan, check_usage_limit
from .routes import auth_bp, register_auth_routes

__all__ = [
    # Password utilities
    'hash_password',
    'verify_password',
    'is_password_strong',
    # JWT utilities
    'create_access_token',
    'create_refresh_token',
    'verify_access_token',
    'verify_refresh_token',
    'revoke_refresh_token',
    # Decorators
    'require_auth',
    'require_admin',
    'rate_limit',
    'require_plan',
    'check_usage_limit',
    # Routes
    'auth_bp',
    'register_auth_routes'
]
