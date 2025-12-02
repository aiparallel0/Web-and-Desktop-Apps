"""
Authentication and authorization module

Provides complete authentication infrastructure including:
- Password hashing with bcrypt
- JWT token creation and verification
- Route decorators for authentication and authorization
- API routes for user registration, login, and session management

Integrated with Circular Exchange Framework for dynamic configuration.
"""

# Circular Exchange Framework Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False

# Register module with Circular Exchange
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="web-app.backend.auth",
            file_path=__file__,
            description="Authentication and authorization with JWT tokens and password hashing",
            dependencies=["shared.circular_exchange"],
            exports=["hash_password", "verify_password", "create_access_token", 
                    "verify_access_token", "require_auth", "require_admin", "auth_bp"]
        ))
    except Exception:
        pass  # Ignore registration errors during import

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
"""
Password hashing and verification using bcrypt
"""
import bcrypt
import logging

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt

    Args:
        password: Plain text password

    Returns:
        Hashed password as string
    """
    if not password:
        raise ValueError("Password cannot be empty")

    # Generate salt and hash password
    salt = bcrypt.gensalt(rounds=12)  # 12 rounds is secure and performant
    password_bytes = password.encode('utf-8')
    hashed = bcrypt.hashpw(password_bytes, salt)

    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against its hash

    Args:
        password: Plain text password to verify
        password_hash: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    if not password or not password_hash:
        return False

    try:
        password_bytes = password.encode('utf-8')
        hash_bytes = password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def is_password_strong(password: str) -> tuple[bool, list[str]]:
    """
    Check if password meets strength requirements

    Requirements:
    - At least 8 characters
    - Contains uppercase letter
    - Contains lowercase letter
    - Contains number
    - Contains special character

    Args:
        password: Password to check

    Returns:
        Tuple of (is_strong, list_of_issues)
    """
    issues = []

    if len(password) < 8:
        issues.append("Password must be at least 8 characters long")

    if not any(c.isupper() for c in password):
        issues.append("Password must contain at least one uppercase letter")

    if not any(c.islower() for c in password):
        issues.append("Password must contain at least one lowercase letter")

    if not any(c.isdigit() for c in password):
        issues.append("Password must contain at least one number")

    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        issues.append("Password must contain at least one special character")

    return (len(issues) == 0, issues)
"""
JWT token creation and verification
"""
import os
import jwt
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging
import secrets

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'change-this-secret-in-production-use-env-var')
JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # Short-lived access tokens
REFRESH_TOKEN_EXPIRE_DAYS = 30  # Long-lived refresh tokens

if JWT_SECRET == 'change-this-secret-in-production-use-env-var':
    logger.warning(
        "Using default JWT_SECRET! "
        "Set JWT_SECRET environment variable in production!"
    )


def create_access_token(user_id: str, email: str, is_admin: bool = False) -> str:
    """
    Create a short-lived JWT access token

    Args:
        user_id: User's UUID
        email: User's email
        is_admin: Whether user is admin

    Returns:
        Encoded JWT token
    """
    now = datetime.utcnow()
    expires = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        'user_id': str(user_id),
        'email': email,
        'is_admin': is_admin,
        'iat': now,  # Issued at
        'exp': expires,  # Expires at
        'type': 'access'
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def create_refresh_token() -> tuple[str, str]:
    """
    Create a long-lived refresh token

    Returns:
        Tuple of (token, token_hash) where:
        - token: The actual token to return to client
        - token_hash: Hash to store in database
    """
    # Generate cryptographically secure random token
    token = secrets.token_urlsafe(32)

    # Hash the token for storage
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    return token, token_hash


def verify_access_token(token: str) -> Optional[Dict]:
    """
    Verify and decode an access token

    Args:
        token: JWT token to verify

    Returns:
        Decoded payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        # Verify it's an access token
        if payload.get('type') != 'access':
            logger.warning("Token is not an access token")
            return None

        return payload

    except jwt.ExpiredSignatureError:
        logger.debug("Access token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid access token: {e}")
        return None


def verify_refresh_token(token: str, stored_hash: str) -> bool:
    """
    Verify a refresh token against its stored hash

    Args:
        token: The refresh token from client
        stored_hash: The hash stored in database

    Returns:
        True if token is valid, False otherwise
    """
    try:
        # Hash the provided token
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Compare with stored hash (constant-time comparison)
        return secrets.compare_digest(token_hash, stored_hash)

    except Exception as e:
        logger.error(f"Error verifying refresh token: {e}")
        return False


def revoke_refresh_token(db, token: str) -> bool:
    """
    Revoke a refresh token

    Args:
        db: Database session
        token: The refresh token to revoke

    Returns:
        True if token was revoked, False if not found
    """
    from database.models import RefreshToken

    try:
        # Hash the token to find it in database
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Find and revoke the token
        refresh_token = db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash
        ).first()

        if refresh_token:
            refresh_token.revoked = True
            refresh_token.revoked_at = datetime.utcnow()
            db.commit()
            logger.info(f"Revoked refresh token for user {refresh_token.user_id}")
            return True

        return False

    except Exception as e:
        logger.error(f"Error revoking refresh token: {e}")
        db.rollback()
        return False


def decode_token_without_verification(token: str) -> Optional[Dict]:
    """
    Decode a token without verifying signature
    Useful for debugging or extracting user_id from expired tokens

    Args:
        token: JWT token to decode

    Returns:
        Decoded payload (unverified)
    """
    try:
        return jwt.decode(token, options={"verify_signature": False})
    except Exception as e:
        logger.error(f"Error decoding token: {e}")
        return None
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
"""
Authentication API routes for user registration, login, and session management.

These routes integrate the auth module with the database and provide a complete
authentication system for the Receipt Extractor application.
"""
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, g
from functools import wraps

logger = logging.getLogger(__name__)

# Create Blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Lazy imports to avoid circular dependencies
_db_context = None
_User = None
_RefreshToken = None


def _get_db_context():
    """Lazy import of database context."""
    global _db_context
    if _db_context is None:
        from database.connection import get_db_context
        _db_context = get_db_context
    return _db_context


def _get_models():
    """Lazy import of database models."""
    global _User, _RefreshToken
    if _User is None:
        from database.models import User, RefreshToken
        _User = User
        _RefreshToken = RefreshToken
    return _User, _RefreshToken


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user account.
    
    Request body:
        {
            "email": "user@example.com",
            "password": "SecurePass123!",
            "full_name": "John Doe" (optional),
            "company": "Acme Inc" (optional)
        }
    
    Returns:
        201: User created successfully
        400: Validation error
        409: Email already exists
    """
    try:
        from .password import hash_password, is_password_strong
        from .jwt_handler import create_access_token, create_refresh_token
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Request body is required'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        full_name = data.get('full_name', '').strip()
        company = data.get('company', '').strip()
        
        # Validate email
        if not email:
            return jsonify({'success': False, 'error': 'Email is required'}), 400
        
        if '@' not in email or '.' not in email:
            return jsonify({'success': False, 'error': 'Invalid email format'}), 400
        
        # Validate password strength
        is_strong, issues = is_password_strong(password)
        if not is_strong:
            return jsonify({
                'success': False,
                'error': 'Password does not meet requirements',
                'issues': issues
            }), 400
        
        User, RefreshToken = _get_models()
        
        with _get_db_context()() as db:
            # Check if email already exists
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                return jsonify({'success': False, 'error': 'Email already registered'}), 409
            
            # Create new user
            import uuid
            user = User(
                id=uuid.uuid4(),
                email=email,
                password_hash=hash_password(password),
                full_name=full_name or None,
                company=company or None,
                is_active=True,
                email_verified=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(user)
            db.flush()  # Get the user ID
            
            # Create tokens
            access_token = create_access_token(str(user.id), user.email, user.is_admin)
            refresh_token, token_hash = create_refresh_token()
            
            # Store refresh token
            refresh_token_record = RefreshToken(
                id=uuid.uuid4(),
                user_id=user.id,
                token_hash=token_hash,
                expires_at=datetime.utcnow() + timedelta(days=30),
                device_info=request.headers.get('User-Agent', '')[:255],
                ip_address=request.remote_addr
            )
            db.add(refresh_token_record)
            db.commit()
            
            logger.info(f"New user registered: {email}")
            
            return jsonify({
                'success': True,
                'message': 'Registration successful',
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'full_name': user.full_name,
                    'plan': user.plan.value if hasattr(user.plan, 'value') else str(user.plan)
                },
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': 'Bearer',
                'expires_in': 900  # 15 minutes
            }), 201
            
    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Registration failed'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate user and return tokens.
    
    Request body:
        {
            "email": "user@example.com",
            "password": "SecurePass123!"
        }
    
    Returns:
        200: Login successful with tokens
        401: Invalid credentials
    """
    try:
        from .password import verify_password
        from .jwt_handler import create_access_token, create_refresh_token
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Request body is required'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'success': False, 'error': 'Email and password are required'}), 400
        
        User, RefreshToken = _get_models()
        
        with _get_db_context()() as db:
            # Find user
            user = db.query(User).filter(User.email == email).first()
            
            if not user or not verify_password(password, user.password_hash):
                logger.warning(f"Failed login attempt for: {email}")
                return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
            
            if not user.is_active:
                return jsonify({'success': False, 'error': 'Account is disabled'}), 401
            
            # Update last login
            user.last_login_at = datetime.utcnow()
            
            # Create tokens
            access_token = create_access_token(str(user.id), user.email, user.is_admin)
            refresh_token, token_hash = create_refresh_token()
            
            # Store refresh token
            import uuid
            refresh_token_record = RefreshToken(
                id=uuid.uuid4(),
                user_id=user.id,
                token_hash=token_hash,
                expires_at=datetime.utcnow() + timedelta(days=30),
                device_info=request.headers.get('User-Agent', '')[:255],
                ip_address=request.remote_addr
            )
            db.add(refresh_token_record)
            db.commit()
            
            logger.info(f"User logged in: {email}")
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'full_name': user.full_name,
                    'plan': user.plan.value if hasattr(user.plan, 'value') else str(user.plan),
                    'is_admin': user.is_admin
                },
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': 'Bearer',
                'expires_in': 900  # 15 minutes
            })
            
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Login failed'}), 500


@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """
    Get a new access token using a refresh token.
    
    Request body:
        {
            "refresh_token": "your_refresh_token"
        }
    
    Returns:
        200: New access token
        401: Invalid or expired refresh token
    """
    try:
        from .jwt_handler import create_access_token, verify_refresh_token
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Request body is required'}), 400
        
        token = data.get('refresh_token', '')
        if not token:
            return jsonify({'success': False, 'error': 'Refresh token is required'}), 400
        
        User, RefreshToken = _get_models()
        
        import hashlib
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        with _get_db_context()() as db:
            # Find refresh token
            refresh_record = db.query(RefreshToken).filter(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked.is_(False),
                RefreshToken.expires_at > datetime.utcnow()
            ).first()
            
            if not refresh_record:
                return jsonify({'success': False, 'error': 'Invalid or expired refresh token'}), 401
            
            # Get user
            user = db.query(User).filter(User.id == refresh_record.user_id).first()
            if not user or not user.is_active:
                return jsonify({'success': False, 'error': 'User not found or disabled'}), 401
            
            # Create new access token
            access_token = create_access_token(str(user.id), user.email, user.is_admin)
            
            return jsonify({
                'success': True,
                'access_token': access_token,
                'token_type': 'Bearer',
                'expires_in': 900  # 15 minutes
            })
            
    except Exception as e:
        logger.error(f"Token refresh error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Token refresh failed'}), 500


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Logout user and revoke refresh token.
    
    Request body:
        {
            "refresh_token": "your_refresh_token"
        }
    
    Returns:
        200: Logout successful
    """
    try:
        from .jwt_handler import revoke_refresh_token
        
        data = request.get_json()
        token = data.get('refresh_token', '') if data else ''
        
        if token:
            with _get_db_context()() as db:
                revoke_refresh_token(db, token)
        
        return jsonify({
            'success': True,
            'message': 'Logout successful'
        })
        
    except Exception as e:
        logger.error(f"Logout error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Logout failed'}), 500


@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """
    Get current authenticated user's profile.
    
    Headers:
        Authorization: Bearer <access_token>
    
    Returns:
        200: User profile
        401: Not authenticated
    """
    try:
        from .jwt_handler import verify_access_token
        from .decorators import require_auth
        
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'success': False, 'error': 'Missing authorization header'}), 401
        
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({'success': False, 'error': 'Invalid authorization header format'}), 401
        
        token = parts[1]
        payload = verify_access_token(token)
        if not payload:
            return jsonify({'success': False, 'error': 'Invalid or expired token'}), 401
        
        user_id = payload.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Invalid token payload'}), 401
        
        User, _ = _get_models()
        
        with _get_db_context()() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return jsonify({'success': False, 'error': 'User not found'}), 404
            
            return jsonify({
                'success': True,
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'full_name': user.full_name,
                    'company': user.company,
                    'plan': user.plan.value if hasattr(user.plan, 'value') else str(user.plan),
                    'is_admin': user.is_admin,
                    'email_verified': user.email_verified,
                    'receipts_processed_month': user.receipts_processed_month,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'last_login_at': user.last_login_at.isoformat() if user.last_login_at else None
                }
            })
            
    except Exception as e:
        logger.error(f"Get user error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Failed to get user profile'}), 500


@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    """
    Change the current user's password.
    
    Headers:
        Authorization: Bearer <access_token>
    
    Request body:
        {
            "current_password": "OldPass123!",
            "new_password": "NewPass456!"
        }
    
    Returns:
        200: Password changed successfully
        400: Validation error
        401: Invalid current password
    """
    try:
        from .jwt_handler import verify_access_token
        from .password import verify_password, hash_password, is_password_strong
        
        # Verify authentication
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'success': False, 'error': 'Missing authorization header'}), 401
        
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({'success': False, 'error': 'Invalid authorization header format'}), 401
        
        token = parts[1]
        payload = verify_access_token(token)
        if not payload:
            return jsonify({'success': False, 'error': 'Invalid or expired token'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Request body is required'}), 400
        
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        
        if not current_password or not new_password:
            return jsonify({'success': False, 'error': 'Both current and new password are required'}), 400
        
        # Validate new password strength
        is_strong, issues = is_password_strong(new_password)
        if not is_strong:
            return jsonify({
                'success': False,
                'error': 'New password does not meet requirements',
                'issues': issues
            }), 400
        
        user_id = payload.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Invalid token payload'}), 401
        
        User, _ = _get_models()
        
        with _get_db_context()() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return jsonify({'success': False, 'error': 'User not found'}), 404
            
            # Verify current password
            if not verify_password(current_password, user.password_hash):
                return jsonify({'success': False, 'error': 'Current password is incorrect'}), 401
            
            # Update password
            user.password_hash = hash_password(new_password)
            user.updated_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Password changed for user: {user.email}")
            
            return jsonify({
                'success': True,
                'message': 'Password changed successfully'
            })
            
    except Exception as e:
        logger.error(f"Change password error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Failed to change password'}), 500


def register_auth_routes(app):
    """Register auth blueprint with the Flask app."""
    app.register_blueprint(auth_bp)
    logger.info("Auth routes registered")
"""
Validation package for input validation using Pydantic
"""
from .schemas import (
    UserRegisterSchema,
    UserLoginSchema,
    RefreshTokenSchema,
    PasswordResetRequestSchema,
    PasswordResetSchema,
    ReceiptUploadSchema,
    ReceiptUpdateSchema,
    APIKeyCreateSchema,
    FileUploadValidation,
    PaginationParams,
    DateRangeFilter,
    ReceiptSearchSchema
)

__all__ = [
    'UserRegisterSchema',
    'UserLoginSchema',
    'RefreshTokenSchema',
    'PasswordResetRequestSchema',
    'PasswordResetSchema',
    'ReceiptUploadSchema',
    'ReceiptUpdateSchema',
    'APIKeyCreateSchema',
    'FileUploadValidation',
    'PaginationParams',
    'DateRangeFilter',
    'ReceiptSearchSchema'
]
"""
Pydantic validation schemas for API input validation
Implements Priority 1: Security Hardening - Input Validation
"""
from pydantic import BaseModel, EmailStr, Field, validator, constr
from typing import Optional, List
from datetime import datetime
import re


class UserRegisterSchema(BaseModel):
    """Schema for user registration"""
    email: EmailStr = Field(..., description="User's email address")
    password: constr(min_length=8, max_length=128) = Field(..., description="User's password")
    full_name: Optional[str] = Field(None, max_length=255, description="User's full name")
    company: Optional[str] = Field(None, max_length=255, description="Company name")

    @validator('password')
    def password_strength(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')

        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')

        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')

        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')

        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in v):
            raise ValueError('Password must contain at least one special character')

        return v

    @validator('email')
    def email_not_disposable(cls, v):
        """Block common disposable email domains"""
        disposable_domains = [
            'tempmail.com', 'guerrillamail.com', '10minutemail.com',
            'mailinator.com', 'throwaway.email'
        ]

        domain = v.split('@')[1].lower()
        if domain in disposable_domains:
            raise ValueError('Disposable email addresses are not allowed')

        return v.lower()


class UserLoginSchema(BaseModel):
    """Schema for user login"""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=1, max_length=128, description="User's password")


class RefreshTokenSchema(BaseModel):
    """Schema for refresh token request"""
    refresh_token: str = Field(..., description="Refresh token")


class PasswordResetRequestSchema(BaseModel):
    """Schema for password reset request"""
    email: EmailStr = Field(..., description="User's email address")


class PasswordResetSchema(BaseModel):
    """Schema for password reset"""
    token: str = Field(..., description="Password reset token")
    new_password: constr(min_length=8, max_length=128) = Field(..., description="New password")

    @validator('new_password')
    def password_strength(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')

        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')

        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')

        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')

        return v


class ReceiptUploadSchema(BaseModel):
    """Schema for receipt upload"""
    model_id: Optional[str] = Field(None, max_length=100, description="Model to use for extraction")

    @validator('model_id')
    def validate_model_id(cls, v):
        """Validate model ID format"""
        if v is None:
            return v

        # Allow alphanumeric, underscores, hyphens
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Invalid model ID format')

        return v


class ReceiptUpdateSchema(BaseModel):
    """Schema for receipt update"""
    extracted_data: Optional[dict] = Field(None, description="Updated extraction data")
    status: Optional[str] = Field(None, description="Receipt status")

    @validator('status')
    def validate_status(cls, v):
        """Validate status values"""
        if v is None:
            return v

        valid_statuses = ['processing', 'completed', 'failed']
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')

        return v


class APIKeyCreateSchema(BaseModel):
    """Schema for creating API key"""
    name: str = Field(..., min_length=1, max_length=255, description="API key name")

    @validator('name')
    def validate_name(cls, v):
        """Validate API key name"""
        # Remove extra whitespace
        v = ' '.join(v.split())

        if len(v) < 1:
            raise ValueError('Name cannot be empty')

        return v


class FileUploadValidation:
    """Validation for file uploads"""

    # Allowed image MIME types
    ALLOWED_MIME_TYPES = {
        'image/jpeg',
        'image/jpg',
        'image/png',
        'image/bmp',
        'image/tiff',
        'image/tif'
    }

    # Maximum file size (10 MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024

    @classmethod
    def validate_image(cls, file_size: int, mime_type: str) -> tuple[bool, Optional[str]]:
        """
        Validate uploaded image file

        Args:
            file_size: Size of file in bytes
            mime_type: MIME type of file

        Returns:
            Tuple of (is_valid, error_message)
        """
        if file_size > cls.MAX_FILE_SIZE:
            return False, f'File size exceeds maximum of {cls.MAX_FILE_SIZE // (1024*1024)}MB'

        if mime_type not in cls.ALLOWED_MIME_TYPES:
            return False, f'Invalid file type. Allowed types: {", ".join(cls.ALLOWED_MIME_TYPES)}'

        return True, None


class PaginationParams(BaseModel):
    """Schema for pagination parameters"""
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate offset from page number"""
        return (self.page - 1) * self.per_page


class DateRangeFilter(BaseModel):
    """Schema for date range filtering"""
    start_date: Optional[datetime] = Field(None, description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")

    @validator('end_date')
    def end_after_start(cls, v, values):
        """Validate end date is after start date"""
        if v and values.get('start_date') and v < values['start_date']:
            raise ValueError('End date must be after start date')

        return v


class ReceiptSearchSchema(BaseModel):
    """Schema for receipt search"""
    query: Optional[str] = Field(None, max_length=255, description="Search query")
    store_name: Optional[str] = Field(None, max_length=255, description="Filter by store name")
    min_amount: Optional[float] = Field(None, ge=0, description="Minimum total amount")
    max_amount: Optional[float] = Field(None, ge=0, description="Maximum total amount")
    start_date: Optional[datetime] = Field(None, description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")

    @validator('max_amount')
    def max_after_min(cls, v, values):
        """Validate max amount is greater than min amount"""
        if v and values.get('min_amount') and v < values['min_amount']:
            raise ValueError('Maximum amount must be greater than minimum amount')

        return v
