"""
Database package initialization
"""
from .models import (
    Base,
    User,
    Receipt,
    Subscription,
    APIKey,
    RefreshToken,
    AuditLog,
    SubscriptionPlan,
    SubscriptionStatus
)
from .connection import get_db, init_db, engine

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
    'get_db',
    'init_db',
    'engine'
]
"""
Database connection and session management
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
import logging

from .models import Base

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


def get_engine():
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        # Use NullPool for serverless/Lambda environments
        poolclass = NullPool if os.getenv('SERVERLESS', 'false').lower() == 'true' else None
        
        engine_kwargs = {
            'pool_pre_ping': True,  # Verify connections before using
            'echo': os.getenv('SQL_ECHO', 'false').lower() == 'true'  # Log SQL queries if SQL_ECHO=true
        }
        
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
