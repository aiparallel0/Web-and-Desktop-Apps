"""
=============================================================================
BILLING MIDDLEWARE - Usage Enforcement
=============================================================================

Provides decorators and middleware for enforcing subscription limits.

Usage:
    from billing.middleware import require_subscription, check_usage_limits
    
    @app.route('/api/premium-feature')
    @require_auth
    @require_subscription('pro')
    def premium_route():
        return jsonify({'message': 'Premium feature'})

=============================================================================
"""

from functools import wraps
from flask import g, jsonify, request
import logging
from typing import Callable

from .plans import SUBSCRIPTION_PLANS, PLAN_HIERARCHY, get_plan_features

logger = logging.getLogger(__name__)


class UsageLimitExceeded(Exception):
    """Exception raised when usage limit is exceeded."""
    
    def __init__(self, message: str, limit_type: str, limit: int, used: int):
        self.message = message
        self.limit_type = limit_type
        self.limit = limit
        self.used = used
        super().__init__(self.message)


def require_subscription(min_plan: str = 'pro') -> Callable:
    """
    Decorator to require minimum subscription plan.
    
    Args:
        min_plan: Minimum required plan (free, pro, business, enterprise)
    
    Usage:
        @require_subscription('pro')
        def premium_endpoint():
            ...
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get user's plan from g object (set by require_auth)
            user_plan = getattr(g, 'user_plan', 'free')
            
            # Handle enum values
            if hasattr(user_plan, 'value'):
                user_plan = user_plan.value
            
            # Check plan hierarchy
            user_level = PLAN_HIERARCHY.get(user_plan, 0)
            required_level = PLAN_HIERARCHY.get(min_plan, 1)
            
            if user_level < required_level:
                return jsonify({
                    'success': False,
                    'error': f'This feature requires {min_plan} plan or higher',
                    'current_plan': user_plan,
                    'required_plan': min_plan,
                    'upgrade_url': '/pricing'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


def check_usage_limits(f: Callable) -> Callable:
    """
    Decorator to check if user has exceeded monthly limits.
    
    Must be used after @require_auth.
    
    Usage:
        @require_auth
        @check_usage_limits
        def extract_endpoint():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Lazy import to avoid circular imports
        from database import get_db_context, User
        
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        with get_db_context() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return jsonify({'success': False, 'error': 'User not found'}), 404
            
            # Get plan features
            plan_name = user.plan.value if hasattr(user.plan, 'value') else str(user.plan)
            features = get_plan_features(plan_name)
            
            # Check receipts limit
            receipts_limit = features.get('receipts_per_month', 10)
            if receipts_limit != 'unlimited':
                if user.receipts_processed_month >= receipts_limit:
                    return jsonify({
                        'success': False,
                        'error': 'Monthly receipt limit exceeded',
                        'limit_type': 'receipts',
                        'limit': receipts_limit,
                        'used': user.receipts_processed_month,
                        'plan': plan_name,
                        'upgrade_url': '/pricing',
                        'message': 'Please upgrade your plan to process more receipts'
                    }), 429
            
            # Check storage limit
            storage_limit_bytes = features.get('storage_gb', 0.1) * 1024 * 1024 * 1024
            if user.storage_used_bytes >= storage_limit_bytes:
                return jsonify({
                    'success': False,
                    'error': 'Storage limit exceeded',
                    'limit_type': 'storage',
                    'limit_gb': features.get('storage_gb', 0.1),
                    'used_gb': round(user.storage_used_bytes / (1024 ** 3), 2),
                    'plan': plan_name,
                    'upgrade_url': '/pricing',
                    'message': 'Please upgrade your plan or delete old receipts'
                }), 429
            
            # Increment usage counter
            user.receipts_processed_month += 1
            db.commit()
        
        return f(*args, **kwargs)
    
    return decorated_function


def check_feature_access(feature: str) -> Callable:
    """
    Decorator to check if user has access to a specific feature.
    
    Args:
        feature: Feature name to check (e.g., 'cloud_training', 'api_access')
    
    Usage:
        @require_auth
        @check_feature_access('cloud_training')
        def cloud_training_endpoint():
            ...
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get user's plan from g object
            user_plan = getattr(g, 'user_plan', 'free')
            
            # Handle enum values
            if hasattr(user_plan, 'value'):
                user_plan = user_plan.value
            
            # Get plan features
            features = get_plan_features(user_plan)
            
            # Check if feature is available
            if not features.get(feature, False):
                return jsonify({
                    'success': False,
                    'error': f'Feature "{feature}" is not available on your plan',
                    'current_plan': user_plan,
                    'upgrade_url': '/pricing',
                    'message': 'Please upgrade to access this feature'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


def check_file_size_limit(f: Callable) -> Callable:
    """
    Decorator to check file size against plan limits.
    
    Must be used on endpoints that receive file uploads.
    
    Usage:
        @require_auth
        @check_file_size_limit
        def upload_endpoint():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get user's plan from g object
        user_plan = getattr(g, 'user_plan', 'free')
        
        # Handle enum values
        if hasattr(user_plan, 'value'):
            user_plan = user_plan.value
        
        # Get plan features
        features = get_plan_features(user_plan)
        max_size_mb = features.get('max_file_size_mb', 5)
        max_size_bytes = max_size_mb * 1024 * 1024
        
        # Check content length
        content_length = request.content_length
        if content_length and content_length > max_size_bytes:
            return jsonify({
                'success': False,
                'error': f'File size exceeds plan limit of {max_size_mb}MB',
                'max_size_mb': max_size_mb,
                'file_size_mb': round(content_length / (1024 * 1024), 2),
                'current_plan': user_plan,
                'upgrade_url': '/pricing'
            }), 413
        
        return f(*args, **kwargs)
    
    return decorated_function


def increment_storage_usage(bytes_used: int) -> bool:
    """
    Increment user's storage usage.
    
    Args:
        bytes_used: Number of bytes to add
        
    Returns:
        True if successful, False if limit exceeded
    """
    from database import get_db_context, User
    
    user_id = getattr(g, 'user_id', None)
    if not user_id:
        return False
    
    with get_db_context() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        # Get plan limits
        plan_name = user.plan.value if hasattr(user.plan, 'value') else str(user.plan)
        features = get_plan_features(plan_name)
        storage_limit_bytes = features.get('storage_gb', 0.1) * 1024 * 1024 * 1024
        
        # Check if adding would exceed limit
        if user.storage_used_bytes + bytes_used > storage_limit_bytes:
            return False
        
        # Increment storage usage
        user.storage_used_bytes += bytes_used
        db.commit()
    
    return True


def decrement_storage_usage(bytes_freed: int) -> bool:
    """
    Decrement user's storage usage.
    
    Args:
        bytes_freed: Number of bytes freed
        
    Returns:
        True if successful
    """
    from database import get_db_context, User
    
    user_id = getattr(g, 'user_id', None)
    if not user_id:
        return False
    
    with get_db_context() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        # Decrement (ensure non-negative)
        user.storage_used_bytes = max(0, user.storage_used_bytes - bytes_freed)
        db.commit()
    
    return True
