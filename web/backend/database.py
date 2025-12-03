"""
Database module - Models and connection management

Integrated with Circular Exchange Framework for dynamic configuration.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
import logging

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
            module_id="web.backend.database",
            file_path=__file__,
            description="Database models and connection management for SQLAlchemy",
            dependencies=["shared.circular_exchange"],
            exports=["Base", "User", "Receipt", "Subscription", "APIKey", 
                    "RefreshToken", "AuditLog", "get_db", "init_db", "CloudStorageProvider"]
        ))
    except Exception:
        pass  # Ignore registration errors during import

"""
Database connection and session management
"""

logger = logging.getLogger(__name__)

# Database URL from environment variable
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://receipt_user:receipt_pass@localhost:5432/receipt_extractor'
)

# For development/testing, you can override with SQLite
if os.getenv('USE_SQLITE', 'false').lower() == 'true' or os.getenv('TESTING', 'false').lower() == 'true':
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./receipt_extractor.db')
    if not DATABASE_URL.startswith('sqlite'):
        DATABASE_URL = 'sqlite:///./receipt_extractor.db'
    logger.warning("Using SQLite database for development/testing. Not recommended for production!")

# Create engine lazily to support testing
_engine = None

# Connection pool configuration (CEF-suggested based on pool exhaustion errors)
# These settings help prevent "connection pool exhausted" errors
POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '5'))  # Maximum connections in pool
POOL_MAX_OVERFLOW = int(os.getenv('DB_POOL_MAX_OVERFLOW', '10'))  # Extra connections when pool is full
POOL_TIMEOUT = int(os.getenv('DB_POOL_TIMEOUT', '30'))  # Seconds to wait for connection
POOL_RECYCLE = int(os.getenv('DB_POOL_RECYCLE', '1800'))  # Recycle connections every 30 minutes


def get_engine():
    """
    Get or create the database engine.
    
    Configured with connection pool management to prevent pool exhaustion.
    Added based on CEF analysis detecting recurring "connection pool exhausted" errors.
    """
    global _engine
    if _engine is None:
        # Use NullPool for serverless/Lambda environments
        poolclass = NullPool if os.getenv('SERVERLESS', 'false').lower() == 'true' else None
        
        engine_kwargs = {
            'pool_pre_ping': True,  # Verify connections before using
            'echo': os.getenv('SQL_ECHO', 'false').lower() == 'true'  # Log SQL queries if SQL_ECHO=true
        }
        
        # Add pool configuration for PostgreSQL (not for SQLite or serverless)
        if not DATABASE_URL.startswith('sqlite') and poolclass is None:
            engine_kwargs.update({
                'pool_size': POOL_SIZE,
                'max_overflow': POOL_MAX_OVERFLOW,
                'pool_timeout': POOL_TIMEOUT,
                'pool_recycle': POOL_RECYCLE,
            })
            logger.info(
                "Database pool configured: size=%d, max_overflow=%d, timeout=%ds, recycle=%ds",
                POOL_SIZE, POOL_MAX_OVERFLOW, POOL_TIMEOUT, POOL_RECYCLE
            )
        
        # Only add poolclass for non-SQLite databases
        if poolclass and not DATABASE_URL.startswith('sqlite'):
            engine_kwargs['poolclass'] = poolclass
        
        _engine = create_engine(DATABASE_URL, **engine_kwargs)
    return _engine


# Lazy property for backwards compatibility
class EngineProxy:
    """Proxy object for lazy engine initialization."""
    def __getattr__(self, name):
        return getattr(get_engine(), name)


engine = EngineProxy()

# Create session factory lazily
_SessionLocal = None


def get_session_factory():
    """Get or create the session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


# Module-level SessionLocal that creates session factory on first access
class SessionLocalProxy:
    """Proxy class that lazily creates the session factory."""
    def __call__(self):
        return get_session_factory()()
    
    def __getattr__(self, name):
        return getattr(get_session_factory(), name)


SessionLocal = SessionLocalProxy()


# Create scoped session for thread safety
db_session = scoped_session(lambda: get_session_factory()())


def init_db():
    """
    Initialize database schema

    This will create all tables if they don't exist.
    For production, use proper migrations (Alembic).
    """
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=get_engine())
    logger.info("Database schema initialized successfully")


def drop_all():
    """
    Drop all tables

    WARNING: This will delete all data! Use only for development/testing.
    """
    logger.warning("Dropping all database tables...")
    Base.metadata.drop_all(bind=get_engine())
    logger.warning("All tables dropped")


def get_db():
    """
    Dependency for getting database session

    Usage in Flask:
        @app.route('/api/endpoint')
        def endpoint():
            with get_db() as db:
                users = db.query(User).all()
                return jsonify(users)

    Usage in FastAPI:
        @app.get('/api/endpoint')
        def endpoint(db: Session = Depends(get_db)):
            users = db.query(User).all()
            return users
    """
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context manager for database session

    Usage:
        with get_db_context() as db:
            user = db.query(User).filter(User.email == email).first()
            # ... do work ...
    """
    db = get_session_factory()()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def cleanup_expired_tokens():
    """
    Clean up expired refresh tokens

    Should be run periodically (e.g., daily cron job)
    """
    from datetime import datetime
    from .models import RefreshToken

    with get_db_context() as db:
        expired_count = db.query(RefreshToken).filter(
            RefreshToken.expires_at < datetime.utcnow()
        ).delete()

        logger.info(f"Cleaned up {expired_count} expired refresh tokens")
        return expired_count


def reset_monthly_usage():
    """
    Reset monthly usage counters

    Should be run on the 1st of each month
    """
    from .models import User

    with get_db_context() as db:
        user_count = db.query(User).update({
            User.receipts_processed_month: 0
        })

        logger.info(f"Reset monthly usage for {user_count} users")
        return user_count
"""
Database models for Receipt Extractor SaaS Platform
Implements Priority 1: MVP Backend Infrastructure
"""
from datetime import datetime
from typing import Optional
import uuid as uuid_module
from sqlalchemy import (
    Column, String, DateTime, Boolean, Integer, Float,
    ForeignKey, Text, JSON, Enum as SQLEnum, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator, CHAR
import enum
import json

Base = declarative_base()


class GUID(TypeDecorator):
    """Platform-independent GUID type.
    
    Uses PostgreSQL's UUID type or CHAR(36) for other databases (like SQLite).
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import UUID
            return dialect.type_descriptor(UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is not None:
            if dialect.name == 'postgresql':
                return value
            else:
                if isinstance(value, uuid_module.UUID):
                    return str(value)
                return value
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            if not isinstance(value, uuid_module.UUID):
                return uuid_module.UUID(value)
        return value


class JSONBCompatible(TypeDecorator):
    """A JSON type that works with both PostgreSQL (JSONB) and SQLite (JSON)."""
    impl = JSON
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import JSONB
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            if dialect.name == 'sqlite':
                return json.dumps(value) if not isinstance(value, str) else value
        return value
    
    def process_result_value(self, value, dialect):
        if value is not None:
            if dialect.name == 'sqlite' and isinstance(value, str):
                return json.loads(value)
        return value


class SubscriptionPlan(str, enum.Enum):
    """Subscription plan tiers"""
    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, enum.Enum):
    """Subscription status"""
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"


class CloudStorageProvider(str, enum.Enum):
    """Cloud storage provider options for user data storage"""
    NONE = "none"
    S3 = "s3"
    GDRIVE = "gdrive"
    DROPBOX = "dropbox"


class User(Base):
    """User model with authentication and subscription info"""
    __tablename__ = "users"

    # Primary Key
    id = Column(GUID(), primary_key=True, default=uuid_module.uuid4)

    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String(255), nullable=True)

    # Password Reset
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)

    # Profile
    full_name = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)

    # Subscription
    plan = Column(SQLEnum(SubscriptionPlan), default=SubscriptionPlan.FREE, nullable=False)
    stripe_customer_id = Column(String(255), nullable=True, unique=True)

    # Usage Tracking
    receipts_processed_month = Column(Integer, default=0)
    storage_used_bytes = Column(Integer, default=0)

    # Cloud Storage Integration (Phase 1.2 - ROADMAP.md)
    cloud_storage_provider = Column(SQLEnum(CloudStorageProvider), default=CloudStorageProvider.NONE, nullable=False)
    cloud_storage_credentials = Column(Text, nullable=True)  # Encrypted JSON credentials

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    # Relationships
    receipts = relationship("Receipt", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_user_email', 'email'),
        Index('idx_user_plan', 'plan'),
        Index('idx_user_created_at', 'created_at'),
    )

    def __repr__(self):
        plan_value = self.plan.value if hasattr(self.plan, 'value') else self.plan
        return f"<User(id={self.id}, email='{self.email}', plan='{plan_value}')>"


class Receipt(Base):
    """Receipt extraction records"""
    __tablename__ = "receipts"

    # Primary Key
    id = Column(GUID(), primary_key=True, default=uuid_module.uuid4)

    # Foreign Key
    user_id = Column(GUID(), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # File Information
    filename = Column(String(255), nullable=False)
    image_url = Column(String(512), nullable=True)  # S3/storage URL
    file_size_bytes = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)

    # Cloud Storage Integration (Phase 1.2 - ROADMAP.md)
    cloud_storage_key = Column(String(512), nullable=True)  # S3 key or cloud file ID
    thumbnail_url = Column(String(512), nullable=True)  # Quick preview URL

    # Extraction Results
    extracted_data = Column(JSONBCompatible, nullable=True)  # Full receipt data as JSON
    store_name = Column(String(255), nullable=True, index=True)  # For searching
    total_amount = Column(Float, nullable=True)  # For analytics
    transaction_date = Column(DateTime, nullable=True, index=True)  # For filtering

    # Processing Metadata
    model_used = Column(String(100), nullable=False)
    processing_time_seconds = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)

    # Status
    status = Column(String(50), default='processing')  # processing, completed, failed
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="receipts")

    # Indexes
    __table_args__ = (
        Index('idx_receipt_user_id', 'user_id'),
        Index('idx_receipt_created_at', 'created_at'),
        Index('idx_receipt_store_name', 'store_name'),
        Index('idx_receipt_transaction_date', 'transaction_date'),
        Index('idx_receipt_status', 'status'),
        Index('idx_receipt_cloud_key', 'cloud_storage_key'),  # For cloud storage queries
    )

    def __repr__(self):
        return f"<Receipt(id={self.id}, user_id={self.user_id}, store='{self.store_name}')>"


class Subscription(Base):
    """Stripe subscription records"""
    __tablename__ = "subscriptions"

    # Primary Key
    id = Column(GUID(), primary_key=True, default=uuid_module.uuid4)

    # Foreign Key
    user_id = Column(GUID(), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # Stripe Information
    stripe_subscription_id = Column(String(255), unique=True, nullable=False)
    stripe_price_id = Column(String(255), nullable=True)

    # Subscription Details
    plan = Column(SQLEnum(SubscriptionPlan), nullable=False)
    status = Column(SQLEnum(SubscriptionStatus), nullable=False)

    # Billing
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    canceled_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="subscriptions")

    def __repr__(self):
        plan_value = self.plan.value if hasattr(self.plan, 'value') else self.plan
        status_value = self.status.value if hasattr(self.status, 'value') else self.status
        return f"<Subscription(id={self.id}, user_id={self.user_id}, plan='{plan_value}', status='{status_value}')>"


class APIKey(Base):
    """API keys for programmatic access"""
    __tablename__ = "api_keys"

    # Primary Key
    id = Column(GUID(), primary_key=True, default=uuid_module.uuid4)

    # Foreign Key
    user_id = Column(GUID(), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # API Key
    key_hash = Column(String(255), unique=True, nullable=False, index=True)  # Hashed key
    key_prefix = Column(String(20), nullable=False)  # First few chars for display
    name = Column(String(255), nullable=True)  # User-friendly name

    # Usage
    last_used_at = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0)

    # Status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="api_keys")

    def __repr__(self):
        return f"<APIKey(id={self.id}, prefix='{self.key_prefix}', user_id={self.user_id})>"


class RefreshToken(Base):
    """JWT refresh tokens for authentication"""
    __tablename__ = "refresh_tokens"

    # Primary Key
    id = Column(GUID(), primary_key=True, default=uuid_module.uuid4)

    # Foreign Key
    user_id = Column(GUID(), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # Token
    token_hash = Column(String(255), unique=True, nullable=False, index=True)

    # Metadata
    device_info = Column(String(255), nullable=True)  # User agent, device type
    ip_address = Column(String(45), nullable=True)  # IPv6 support

    # Expiry
    expires_at = Column(DateTime, nullable=False, index=True)

    # Status
    revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="refresh_tokens")

    # Indexes
    __table_args__ = (
        Index('idx_refresh_token_user_id', 'user_id'),
        Index('idx_refresh_token_expires_at', 'expires_at'),
        Index('idx_refresh_token_revoked', 'revoked'),
    )

    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, revoked={self.revoked})>"


class AuditLog(Base):
    """Audit log for security and compliance"""
    __tablename__ = "audit_logs"

    # Primary Key
    id = Column(GUID(), primary_key=True, default=uuid_module.uuid4)

    # User (nullable for anonymous actions)
    user_id = Column(GUID(), ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)

    # Action Details
    action = Column(String(100), nullable=False, index=True)  # login, logout, create_receipt, etc.
    resource_type = Column(String(100), nullable=True)  # receipt, user, subscription
    resource_id = Column(GUID(), nullable=True)

    # Request Metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)

    # Additional Data
    audit_extra_data = Column(JSONBCompatible, nullable=True)  # Flexible additional info (renamed from 'extra_data')

    # Result
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Indexes
    __table_args__ = (
        Index('idx_audit_log_user_id', 'user_id'),
        Index('idx_audit_log_action', 'action'),
        Index('idx_audit_log_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', user_id={self.user_id})>"


# Module exports
__all__ = [
    'Base',
    'User',
    'Receipt',
    'Subscription',
    'APIKey',
    'RefreshToken',
    'AuditLog',
    'SubscriptionPlan',
    'SubscriptionStatus',
    'CloudStorageProvider',
    'get_db',
    'init_db',
    'engine',
]


"""
Receipts API routes for managing user receipts.

Provides CRUD operations for receipts with user authentication and authorization.
"""
import logging
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, g

logger = logging.getLogger(__name__)

# Create Blueprint
receipts_bp = Blueprint('receipts', __name__, url_prefix='/api/receipts')

# Lazy imports
_db_context = None
_Receipt = None
_User = None


def _get_db_context():
    """Lazy import of database context."""
    global _db_context
    if _db_context is None:
        from database.connection import get_db_context
        _db_context = get_db_context
    return _db_context


def _get_models():
    """Lazy import of database models."""
    global _Receipt, _User
    if _Receipt is None:
        from database.models import Receipt, User
        _Receipt = Receipt
        _User = User
    return _Receipt, _User


def require_auth_simple(f):
    """Simple auth check decorator for receipts routes."""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from auth.jwt_handler import verify_access_token
        
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
        
        g.user_id = payload.get('user_id')
        g.is_admin = payload.get('is_admin', False)
        
        return f(*args, **kwargs)
    
    return decorated_function


@receipts_bp.route('', methods=['GET'])
@require_auth_simple
def list_receipts():
    """
    List receipts for the current user.
    
    Query parameters:
        page: Page number (default: 1)
        per_page: Items per page (default: 20, max: 100)
        store_name: Filter by store name
        status: Filter by status (processing, completed, failed)
        start_date: Filter by date range start (ISO format)
        end_date: Filter by date range end (ISO format)
        sort_by: Sort field (created_at, transaction_date, total_amount)
        sort_order: Sort order (asc, desc)
    
    Returns:
        200: List of receipts with pagination info
    """
    try:
        Receipt, User = _get_models()
        
        # Parse query parameters
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(100, max(1, int(request.args.get('per_page', 20))))
        store_name = request.args.get('store_name', '').strip()
        status = request.args.get('status', '').strip()
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        with _get_db_context()() as db:
            query = db.query(Receipt).filter(Receipt.user_id == g.user_id)
            
            # Apply filters
            if store_name:
                query = query.filter(Receipt.store_name.ilike(f'%{store_name}%'))
            
            if status:
                query = query.filter(Receipt.status == status)
            
            if start_date:
                try:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    query = query.filter(Receipt.transaction_date >= start_dt)
                except ValueError:
                    pass
            
            if end_date:
                try:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    query = query.filter(Receipt.transaction_date <= end_dt)
                except ValueError:
                    pass
            
            # Apply sorting - validate against allowed fields
            ALLOWED_SORT_FIELDS = {'created_at', 'transaction_date', 'total_amount', 'store_name'}
            if sort_by not in ALLOWED_SORT_FIELDS:
                sort_by = 'created_at'
            sort_column = getattr(Receipt, sort_by, Receipt.created_at)
            if sort_order == 'asc':
                query = query.order_by(sort_column.asc())
            else:
                query = query.order_by(sort_column.desc())
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            receipts = query.offset((page - 1) * per_page).limit(per_page).all()
            
            return jsonify({
                'success': True,
                'receipts': [
                    {
                        'id': str(r.id),
                        'filename': r.filename,
                        'store_name': r.store_name,
                        'total_amount': r.total_amount,
                        'transaction_date': r.transaction_date.isoformat() if r.transaction_date else None,
                        'model_used': r.model_used,
                        'confidence_score': r.confidence_score,
                        'status': r.status,
                        'created_at': r.created_at.isoformat() if r.created_at else None
                    }
                    for r in receipts
                ],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            })
            
    except Exception as e:
        logger.error(f"List receipts error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Failed to list receipts'}), 500


@receipts_bp.route('/<receipt_id>', methods=['GET'])
@require_auth_simple
def get_receipt(receipt_id):
    """
    Get a specific receipt by ID.
    
    Returns:
        200: Receipt details with extracted data
        404: Receipt not found
    """
    try:
        Receipt, _ = _get_models()
        
        with _get_db_context()() as db:
            receipt = db.query(Receipt).filter(
                Receipt.id == receipt_id,
                Receipt.user_id == g.user_id
            ).first()
            
            if not receipt:
                return jsonify({'success': False, 'error': 'Receipt not found'}), 404
            
            return jsonify({
                'success': True,
                'receipt': {
                    'id': str(receipt.id),
                    'filename': receipt.filename,
                    'image_url': receipt.image_url,
                    'file_size_bytes': receipt.file_size_bytes,
                    'mime_type': receipt.mime_type,
                    'store_name': receipt.store_name,
                    'total_amount': receipt.total_amount,
                    'transaction_date': receipt.transaction_date.isoformat() if receipt.transaction_date else None,
                    'extracted_data': receipt.extracted_data,
                    'model_used': receipt.model_used,
                    'processing_time_seconds': receipt.processing_time_seconds,
                    'confidence_score': receipt.confidence_score,
                    'status': receipt.status,
                    'error_message': receipt.error_message,
                    'created_at': receipt.created_at.isoformat() if receipt.created_at else None,
                    'updated_at': receipt.updated_at.isoformat() if receipt.updated_at else None
                }
            })
            
    except Exception as e:
        logger.error(f"Get receipt error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Failed to get receipt'}), 500


@receipts_bp.route('/<receipt_id>', methods=['DELETE'])
@require_auth_simple
def delete_receipt(receipt_id):
    """
    Delete a receipt.
    
    Returns:
        200: Receipt deleted successfully
        404: Receipt not found
    """
    try:
        Receipt, _ = _get_models()
        
        with _get_db_context()() as db:
            receipt = db.query(Receipt).filter(
                Receipt.id == receipt_id,
                Receipt.user_id == g.user_id
            ).first()
            
            if not receipt:
                return jsonify({'success': False, 'error': 'Receipt not found'}), 404
            
            db.delete(receipt)
            db.commit()
            
            logger.info(f"Receipt deleted: {receipt_id}")
            
            return jsonify({
                'success': True,
                'message': 'Receipt deleted successfully'
            })
            
    except Exception as e:
        logger.error(f"Delete receipt error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Failed to delete receipt'}), 500


@receipts_bp.route('/<receipt_id>', methods=['PATCH'])
@require_auth_simple
def update_receipt(receipt_id):
    """
    Update receipt data (e.g., correct extracted information).
    
    Request body:
        {
            "store_name": "Updated Store Name",
            "total_amount": 25.99,
            "transaction_date": "2024-01-15",
            "extracted_data": { ... }
        }
    
    Returns:
        200: Receipt updated successfully
        404: Receipt not found
    """
    try:
        Receipt, _ = _get_models()
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Request body is required'}), 400
        
        with _get_db_context()() as db:
            receipt = db.query(Receipt).filter(
                Receipt.id == receipt_id,
                Receipt.user_id == g.user_id
            ).first()
            
            if not receipt:
                return jsonify({'success': False, 'error': 'Receipt not found'}), 404
            
            # Update allowed fields
            if 'store_name' in data:
                receipt.store_name = data['store_name']
            
            if 'total_amount' in data:
                try:
                    receipt.total_amount = float(data['total_amount'])
                except (ValueError, TypeError):
                    pass
            
            if 'transaction_date' in data:
                try:
                    receipt.transaction_date = datetime.fromisoformat(
                        data['transaction_date'].replace('Z', '+00:00')
                    )
                except ValueError:
                    pass
            
            if 'extracted_data' in data and isinstance(data['extracted_data'], dict):
                receipt.extracted_data = data['extracted_data']
            
            receipt.updated_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Receipt updated: {receipt_id}")
            
            return jsonify({
                'success': True,
                'message': 'Receipt updated successfully',
                'receipt': {
                    'id': str(receipt.id),
                    'store_name': receipt.store_name,
                    'total_amount': receipt.total_amount,
                    'transaction_date': receipt.transaction_date.isoformat() if receipt.transaction_date else None
                }
            })
            
    except Exception as e:
        logger.error(f"Update receipt error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Failed to update receipt'}), 500


@receipts_bp.route('/stats', methods=['GET'])
@require_auth_simple
def get_receipt_stats():
    """
    Get receipt statistics for the current user.
    
    Query parameters:
        period: Time period (month, year, all)
    
    Returns:
        200: Receipt statistics
    """
    try:
        from sqlalchemy import func
        Receipt, _ = _get_models()
        
        period = request.args.get('period', 'month')
        
        with _get_db_context()() as db:
            query = db.query(Receipt).filter(Receipt.user_id == g.user_id)
            
            # Apply time filter
            now = datetime.utcnow()
            if period == 'month':
                start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(Receipt.created_at >= start_date)
            elif period == 'year':
                start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(Receipt.created_at >= start_date)
            
            # Get counts
            total_count = query.count()
            completed_count = query.filter(Receipt.status == 'completed').count()
            failed_count = query.filter(Receipt.status == 'failed').count()
            
            # Get totals
            total_amount_result = db.query(func.sum(Receipt.total_amount)).filter(
                Receipt.user_id == g.user_id,
                Receipt.status == 'completed'
            )
            if period == 'month':
                total_amount_result = total_amount_result.filter(Receipt.created_at >= start_date)
            elif period == 'year':
                total_amount_result = total_amount_result.filter(Receipt.created_at >= start_date)
            
            total_amount = total_amount_result.scalar() or 0
            
            # Get top stores
            top_stores = db.query(
                Receipt.store_name,
                func.count(Receipt.id).label('count')
            ).filter(
                Receipt.user_id == g.user_id,
                Receipt.store_name.isnot(None)
            ).group_by(Receipt.store_name).order_by(
                func.count(Receipt.id).desc()
            ).limit(5).all()
            
            return jsonify({
                'success': True,
                'stats': {
                    'period': period,
                    'total_receipts': total_count,
                    'completed': completed_count,
                    'failed': failed_count,
                    'total_amount': float(total_amount),
                    'top_stores': [
                        {'store_name': s[0], 'count': s[1]} 
                        for s in top_stores if s[0]
                    ]
                }
            })
            
    except Exception as e:
        logger.error(f"Get stats error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Failed to get statistics'}), 500


def register_receipts_routes(app):
    """Register receipts blueprint with the Flask app."""
    app.register_blueprint(receipts_bp)
    logger.info("Receipts routes registered")
