"""
Authentication and authorization decorators for Flask
"""
from functools import wraps
from flask import request, jsonify, g
import logging
from typing import Callable
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)

# In-memory rate limit storage (use Redis in production)
_rate_limit_storage = {}

# Import database connection at module level for better testability
_get_db_context = None


def _lazy_get_db_context():
    """Lazy import of get_db_context for better testability."""
    global _get_db_context
    if _get_db_context is None:
        from database.connection import get_db_context
        _get_db_context = get_db_context
    return _get_db_context


def get_db_context():
    """Get database context - wrapper for testing."""
    return _lazy_get_db_context()()


def require_auth(f: Callable) -> Callable:
    """
    Decorator to require valid JWT authentication

    Usage:
        @app.route('/api/protected')
        @require_auth
        def protected_route():
            user_id = g.user_id
            return jsonify({'message': 'Hello authenticated user'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from .jwt_handler import verify_access_token
        from database.models import User

        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Missing authorization header'}), 401

        # Extract token
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({'error': 'Invalid authorization header format. Use: Bearer <token>'}), 401

        token = parts[1]

        # Verify token
        payload = verify_access_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        # Get user from database
        user_id = payload.get('user_id')
        with get_db_context() as db:
            user = db.query(User).filter(User.id == user_id).first()

            if not user:
                return jsonify({'error': 'User not found'}), 401

            if not user.is_active:
                return jsonify({'error': 'User account is disabled'}), 401

            # Store user info in Flask's g object
            g.user_id = str(user.id)
            g.user_email = user.email
            g.is_admin = user.is_admin
            g.user_plan = user.plan

        return f(*args, **kwargs)

    return decorated_function


def require_admin(f: Callable) -> Callable:
    """
    Decorator to require admin privileges

    Must be used with @require_auth

    Usage:
        @app.route('/api/admin/users')
        @require_auth
        @require_admin
        def admin_route():
            return jsonify({'message': 'Hello admin'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not getattr(g, 'is_admin', False):
            return jsonify({'error': 'Admin privileges required'}), 403

        return f(*args, **kwargs)

    return decorated_function


def rate_limit(max_requests: int = 100, window_seconds: int = 3600,
               key_prefix: str = 'rate_limit') -> Callable:
    """
    Rate limiting decorator

    Args:
        max_requests: Maximum requests allowed in window
        window_seconds: Time window in seconds
        key_prefix: Prefix for rate limit keys

    Usage:
        @app.route('/api/extract')
        @require_auth
        @rate_limit(max_requests=10, window_seconds=60)
        def extract_route():
            return jsonify({'message': 'Processing...'})
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get identifier (user_id if authenticated, IP otherwise)
            identifier = getattr(g, 'user_id', None) or request.remote_addr

            if not identifier:
                return jsonify({'error': 'Unable to determine request source'}), 400

            # Create rate limit key
            key = f"{key_prefix}:{identifier}:{f.__name__}"

            # Clean up old entries
            now = datetime.utcnow()
            if key in _rate_limit_storage:
                _rate_limit_storage[key] = [
                    timestamp for timestamp in _rate_limit_storage[key]
                    if (now - timestamp).total_seconds() < window_seconds
                ]

            # Check rate limit
            request_count = len(_rate_limit_storage.get(key, []))

            if request_count >= max_requests:
                retry_after = window_seconds
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': retry_after
                }), 429

            # Record this request
            if key not in _rate_limit_storage:
                _rate_limit_storage[key] = []
            _rate_limit_storage[key].append(now)

            # Add rate limit headers
            response = f(*args, **kwargs)
            if isinstance(response, tuple):
                response_obj, status_code = response[0], response[1]
            else:
                response_obj, status_code = response, 200

            # Add headers if response is a Flask response object
            if hasattr(response_obj, 'headers'):
                response_obj.headers['X-RateLimit-Limit'] = str(max_requests)
                response_obj.headers['X-RateLimit-Remaining'] = str(max_requests - request_count - 1)
                response_obj.headers['X-RateLimit-Reset'] = str(int(now.timestamp()) + window_seconds)

            return response

        return decorated_function

    return decorator


def require_plan(required_plan: str) -> Callable:
    """
    Decorator to require specific subscription plan

    Must be used with @require_auth

    Args:
        required_plan: Minimum plan required (free, pro, business, enterprise)

    Usage:
        @app.route('/api/premium-feature')
        @require_auth
        @require_plan('pro')
        def premium_route():
            return jsonify({'message': 'Premium feature'})
    """
    plan_hierarchy = {'free': 0, 'pro': 1, 'business': 2, 'enterprise': 3}

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_plan = getattr(g, 'user_plan', 'free')

            if plan_hierarchy.get(user_plan.value, 0) < plan_hierarchy.get(required_plan, 999):
                return jsonify({
                    'error': f'This feature requires {required_plan} plan or higher',
                    'current_plan': user_plan.value,
                    'required_plan': required_plan
                }), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def check_usage_limit(f: Callable) -> Callable:
    """
    Decorator to check monthly usage limits

    Must be used with @require_auth

    Usage:
        @app.route('/api/extract')
        @require_auth
        @check_usage_limit
        def extract_route():
            return jsonify({'message': 'Processing...'})
    """
    # Usage limits per plan
    PLAN_LIMITS = {
        'free': 50,
        'pro': 1000,
        'business': 10000,
        'enterprise': 999999
    }

    @wraps(f)
    def decorated_function(*args, **kwargs):
        from database.models import User

        user_id = g.user_id
        user_plan = g.user_plan

        with get_db_context() as db:
            user = db.query(User).filter(User.id == user_id).first()

            if not user:
                return jsonify({'error': 'User not found'}), 404

            limit = PLAN_LIMITS.get(user_plan.value, PLAN_LIMITS['free'])

            if user.receipts_processed_month >= limit:
                return jsonify({
                    'error': 'Monthly usage limit exceeded',
                    'limit': limit,
                    'used': user.receipts_processed_month,
                    'plan': user_plan.value,
                    'message': 'Please upgrade your plan to process more receipts'
                }), 429

            # Increment usage counter
            user.receipts_processed_month += 1
            db.commit()

        return f(*args, **kwargs)

    return decorated_function
