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
                RefreshToken.revoked == False,
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
        
        User, _ = _get_models()
        
        with _get_db_context()() as db:
            user = db.query(User).filter(User.id == payload['user_id']).first()
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
        
        User, _ = _get_models()
        
        with _get_db_context()() as db:
            user = db.query(User).filter(User.id == payload['user_id']).first()
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
