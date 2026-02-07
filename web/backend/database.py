"""
Database module - Models and connection management

Integrated with Circular Exchange Framework for dynamic configuration.
Telemetry: Tracks database operations for query performance monitoring.
"""

import os
from typing import Optional, Generator, Any, Dict, Iterator, Callable, Tuple
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
import logging
import time

# Telemetry integration
try:
    from shared.utils.telemetry import get_tracer, set_span_attributes
    TELEMETRY_AVAILABLE = True
except ImportError:
    TELEMETRY_AVAILABLE = False

"""
Database connection and session management
"""

logger = logging.getLogger(__name__)

# Database URL from environment variable
DATABASE_URL = os.getenv('DATABASE_URL')

# For development/testing, you can override with SQLite
if os.getenv('USE_SQLITE', 'false').lower() == 'true' or os.getenv('TESTING', 'false').lower() == 'true':
    # Use /tmp for SQLite in production/containers (writable)
    default_sqlite = 'sqlite:////tmp/receipt_extractor.db' if not os.getenv('TESTING') else 'sqlite:///./receipt_extractor.db'
    DATABASE_URL = os.getenv('DATABASE_URL', default_sqlite)
    
    if DATABASE_URL and not DATABASE_URL.startswith('sqlite'):
        DATABASE_URL = default_sqlite
    
    logger.warning("Using SQLite database. Not recommended for production!")
elif not DATABASE_URL:
    # No DATABASE_URL set - use default PostgreSQL URL
    DATABASE_URL = 'postgresql://receipt_user:receipt_pass@localhost:5432/receipt_extractor'
    logger.warning("No DATABASE_URL set, using default: localhost PostgreSQL")

# Create engine lazily to support testing
_engine = None

# Connection pool configuration (CEF-suggested based on pool exhaustion errors)
# These settings help prevent "connection pool exhausted" errors
POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '5'))  # Maximum connections in pool
POOL_MAX_OVERFLOW = int(os.getenv('DB_POOL_MAX_OVERFLOW', '10'))  # Extra connections when pool is full
POOL_TIMEOUT = int(os.getenv('DB_POOL_TIMEOUT', '30'))  # Seconds to wait for connection
POOL_RECYCLE = int(os.getenv('DB_POOL_RECYCLE', '1800'))  # Recycle connections every 30 minutes

def get_engine() -> Engine:
    """
    Get or create the database engine.
    
    Configured with connection pool management to prevent pool exhaustion.
    Added based on CEF analysis detecting recurring "connection pool exhausted" errors.
    
    Returns:
        Engine: SQLAlchemy database engine instance
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
    def __getattr__(self, name: str) -> Any:
        return getattr(get_engine(), name)

engine = EngineProxy()

# Create session factory lazily
_SessionLocal = None

def get_session_factory() -> sessionmaker:
    """
    Get or create the session factory.
    
    Returns:
        sessionmaker: SQLAlchemy session factory
    """
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal

# Module-level SessionLocal that creates session factory on first access
class SessionLocalProxy:
    """Proxy class that lazily creates the session factory."""
    def __call__(self) -> Any:
        return get_session_factory()()
    
    def __getattr__(self, name: str) -> Any:
        return getattr(get_session_factory(), name)

SessionLocal = SessionLocalProxy()

# Create scoped session for thread safety
db_session = scoped_session(lambda: get_session_factory()())

def init_db() -> None:
    """
    Initialize database schema

    This will create all tables if they don't exist.
    For production, use proper migrations (Alembic).
    """
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=get_engine())
    logger.info("Database schema initialized successfully")

def drop_all() -> None:
    """
    Drop all tables

    WARNING: This will delete all data! Use only for development/testing.
    """
    logger.warning("Dropping all database tables...")
    Base.metadata.drop_all(bind=get_engine())
    logger.warning("All tables dropped")

def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting database session with telemetry tracking.

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
            
    Yields:
        Session: SQLAlchemy database session
    """
    if TELEMETRY_AVAILABLE:
        tracer = get_tracer()
        with tracer.start_as_current_span("database.get_session") as span:
            set_span_attributes(span, {
                "operation.type": "create_session",
                "database.type": "postgresql" if not DATABASE_URL.startswith('sqlite') else "sqlite"
            })
            
            db = get_session_factory()()
            try:
                yield db
            finally:
                db.close()
                set_span_attributes(span, {
                    "operation.success": True
                })
    else:
        # Fallback without telemetry
        db = get_session_factory()()
        try:
            yield db
        finally:
            db.close()

@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database session with telemetry tracking.

    Usage:
        with get_db_context() as db:
            user = db.query(User).filter(User.email == email).first()
            # ... do work ...
            
    Yields:
        Session: SQLAlchemy database session
    """
    if TELEMETRY_AVAILABLE:
        tracer = get_tracer()
        with tracer.start_as_current_span("database.context_session") as span:
            start_time = time.time()
            set_span_attributes(span, {
                "operation.type": "context_session",
                "database.type": "postgresql" if not DATABASE_URL.startswith('sqlite') else "sqlite"
            })
            
            db = get_session_factory()()
            try:
                yield db
                db.commit()
                set_span_attributes(span, {
                    "operation.success": True,
                    "session.duration": time.time() - start_time,
                    "session.committed": True
                })
            except Exception as e:
                db.rollback()
                span.record_exception(e)
                set_span_attributes(span, {
                    "operation.success": False,
                    "session.rolled_back": True,
                    "error.type": type(e).__name__
                })
                raise
            finally:
                db.close()
    else:
        # Fallback without telemetry
        db = get_session_factory()()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

def cleanup_expired_tokens() -> int:
    """
    Clean up expired refresh tokens with telemetry tracking.

    Should be run periodically (e.g., daily cron job)
    
    Returns:
        int: Number of expired tokens deleted
    """
    from datetime import datetime, timezone
    from .models import RefreshToken

    if TELEMETRY_AVAILABLE:
        tracer = get_tracer()
        with tracer.start_as_current_span("database.cleanup_expired_tokens") as span:
            start_time = time.time()
            set_span_attributes(span, {
                "operation.type": "cleanup",
                "cleanup.target": "expired_refresh_tokens"
            })
            
            try:
                with get_db_context() as db:
                    expired_count = db.query(RefreshToken).filter(
                        RefreshToken.expires_at < datetime.now(timezone.utc)
                    ).delete()

                    set_span_attributes(span, {
                        "operation.success": True,
                        "cleanup.deleted_count": expired_count,
                        "cleanup.duration": time.time() - start_time
                    })
                    
                    logger.info(f"Cleaned up {expired_count} expired refresh tokens")
                    return expired_count
            except Exception as e:
                span.record_exception(e)
                set_span_attributes(span, {
                    "operation.success": False,
                    "error.type": type(e).__name__
                })
                raise
    else:
        # Fallback without telemetry
        with get_db_context() as db:
            expired_count = db.query(RefreshToken).filter(
                RefreshToken.expires_at < datetime.now(timezone.utc)
            ).delete()

            logger.info(f"Cleaned up {expired_count} expired refresh tokens")
            return expired_count

def reset_monthly_usage() -> int:
    """
    Reset monthly usage counters with telemetry tracking.

    Should be run on the 1st of each month
    
    Returns:
        int: Number of users whose usage was reset
    """
    from .models import User

    if TELEMETRY_AVAILABLE:
        tracer = get_tracer()
        with tracer.start_as_current_span("database.reset_monthly_usage") as span:
            start_time = time.time()
            set_span_attributes(span, {
                "operation.type": "reset_usage",
                "reset.target": "monthly_usage_counters"
            })
            
            try:
                with get_db_context() as db:
                    user_count = db.query(User).update({
                        User.receipts_processed_month: 0
                    })

                    set_span_attributes(span, {
                        "operation.success": True,
                        "reset.user_count": user_count,
                        "reset.duration": time.time() - start_time
                    })
                    
                    logger.info(f"Reset monthly usage for {user_count} users")
                    return user_count
            except Exception as e:
                span.record_exception(e)
                set_span_attributes(span, {
                    "operation.success": False,
                    "error.type": type(e).__name__
                })
                raise
    else:
        # Fallback without telemetry
        with get_db_context() as db:
            user_count = db.query(User).update({
                User.receipts_processed_month: 0
            })

            logger.info(f"Reset monthly usage for {user_count} users")
            return user_count


def validate_database_config():
    """
    Validate database configuration on startup and provide helpful error messages.
    """
    logger.info("="*70)
    logger.info("DATABASE CONFIGURATION CHECK")
    logger.info("="*70)
    
    # Check if Railway environment
    is_railway = os.getenv('RAILWAY_ENVIRONMENT') is not None
    
    if DATABASE_URL.startswith('sqlite'):
        logger.info(f"Using SQLite: {DATABASE_URL}")
        
        # Check if path is writable
        if DATABASE_URL != 'sqlite:///:memory:':
            # Extract file path from sqlite:///path
            db_path = DATABASE_URL.replace('sqlite:///', '')
            db_dir = os.path.dirname(db_path) or '.'
            
            if not os.access(db_dir, os.W_OK):
                logger.error(f"❌ SQLite directory not writable: {db_dir}")
                logger.error("   Solution: Use DATABASE_URL=sqlite:////tmp/receipt_extractor.db")
                if is_railway:
                    logger.error("   Or add PostgreSQL database in Railway dashboard")
                raise RuntimeError(f"Cannot write to SQLite directory: {db_dir}")
        
        logger.warning("⚠️  SQLite is ephemeral in containers - data lost on restart!")
        if is_railway:
            logger.warning("   Recommendation: Add PostgreSQL in Railway for persistence")
    
    elif DATABASE_URL.startswith('postgresql'):
        if 'localhost' in DATABASE_URL:
            logger.error("="*70)
            logger.error("❌ DATABASE CONFIGURATION ERROR")
            logger.error("="*70)
            logger.error("Database URL points to localhost, but no database is available!")
            logger.error("")
            logger.error("SOLUTIONS:")
            if is_railway:
                logger.error("  1. Add PostgreSQL database in Railway:")
                logger.error("     - Click '+ New' → Database → PostgreSQL")
                logger.error("     - Railway will auto-set DATABASE_URL")
                logger.error("")
                logger.error("  2. OR use SQLite temporarily:")
                logger.error("     - Set: USE_SQLITE=true")
                logger.error("     - Set: DATABASE_URL=sqlite:////tmp/receipt_extractor.db")
            else:
                logger.error("  - Set DATABASE_URL to your PostgreSQL connection string")
                logger.error("  - Or set USE_SQLITE=true for development")
            logger.error("="*70)
            raise RuntimeError("Database not configured properly")
        else:
            logger.info(f"Using PostgreSQL: {DATABASE_URL.split('@')[-1]}")
    
    else:
        logger.warning(f"Unknown database type: {DATABASE_URL}")
    
    logger.info("="*70)


def check_database_health() -> Dict[str, Any]:
    """
    Check database connection health and return status metrics.
    
    Returns:
        Dict with status, connection pool info, and query latency
    """
    import time
    from typing import Dict, Any
    
    try:
        engine = get_engine()
        
        # Test query with timing
        start_time = time.time()
        with engine.connect() as conn:
            conn.execute(sa.text("SELECT 1"))
        query_latency = time.time() - start_time
        
        # Get pool stats
        pool = engine.pool
        pool_info = {
            'size': getattr(pool, 'size', lambda: 'N/A')(),
            'checked_out': getattr(pool, 'checkedout', lambda: 'N/A')(),
            'overflow': getattr(pool, 'overflow', lambda: 'N/A')(),
        }
        
        return {
            'status': 'healthy',
            'query_latency_seconds': round(query_latency, 3),
            'pool': pool_info,
            'database_url': DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else 'sqlite'
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}", exc_info=True)
        return {
            'status': 'unhealthy',
            'error': str(e),
            'error_type': type(e).__name__
        }


"""
Database models for Receipt Extractor SaaS Platform
Implements Priority 1: MVP Backend Infrastructure
"""
from datetime import datetime, timezone
from typing import Optional
import uuid as uuid_module
from sqlalchemy import (
    Column, String, DateTime, Boolean, Integer, Float,
    ForeignKey, Text, JSON, Enum as SQLEnum, Index
)
from sqlalchemy.orm import declarative_base, relationship
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

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import UUID
            return dialect.type_descriptor(UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        if value is not None:
            if dialect.name == 'postgresql':
                return value
            else:
                if isinstance(value, uuid_module.UUID):
                    return str(value)
                return value
        return value

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is not None:
            if not isinstance(value, uuid_module.UUID):
                return uuid_module.UUID(value)
        return value

class JSONBCompatible(TypeDecorator):
    """A JSON type that works with both PostgreSQL (JSONB) and SQLite (JSON)."""
    impl = JSON
    cache_ok = True
    
    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import JSONB
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())
    
    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        if value is not None:
            if dialect.name == 'sqlite':
                return json.dumps(value) if not isinstance(value, str) else value
        return value
    
    def process_result_value(self, value: Any, dialect: Any) -> Any:
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

    # Trial Management
    trial_start_date = Column(DateTime, nullable=True)
    trial_end_date = Column(DateTime, nullable=True)
    trial_activated = Column(Boolean, default=False)

    # Referral System
    referral_code = Column(String(20), unique=True, nullable=True, index=True)
    referred_by = Column(GUID(), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    referral_count = Column(Integer, default=0)
    referral_reward_months = Column(Integer, default=0)

    # Onboarding
    onboarding_completed = Column(Boolean, default=False)
    onboarding_step = Column(Integer, default=0)

    # Usage Tracking
    receipts_processed_month = Column(Integer, default=0)
    storage_used_bytes = Column(Integer, default=0)

    # Cloud Storage Integration (Phase 1.2 - ROADMAP.md)
    cloud_storage_provider = Column(SQLEnum(CloudStorageProvider), default=CloudStorageProvider.NONE, nullable=False)
    cloud_storage_credentials = Column(Text, nullable=True)  # Encrypted JSON credentials

    # HuggingFace API Integration (Phase 3.1 - ROADMAP.md)
    hf_api_key_encrypted = Column(Text, nullable=True)  # Encrypted HuggingFace API key

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
        Index('idx_user_referral_code', 'referral_code'),
        Index('idx_user_trial_end', 'trial_end_date'),
    )

    def __repr__(self) -> str:
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

    def __repr__(self) -> str:
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

    def __repr__(self) -> str:
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

    def __repr__(self) -> str:
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

    def __repr__(self) -> str:
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

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action='{self.action}', user_id={self.user_id})>"

class Referral(Base):
    """Referral tracking for referral program"""
    __tablename__ = "referrals"

    # Primary Key
    id = Column(GUID(), primary_key=True, default=uuid_module.uuid4)

    # Referrer (user who sent the referral)
    referrer_id = Column(GUID(), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # Referred user (user who was referred)
    referred_user_id = Column(GUID(), ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True)

    # Referral Details
    referral_code = Column(String(20), nullable=False, index=True)
    email = Column(String(255), nullable=True)  # Email of referred user (before signup)
    
    # Status
    status = Column(String(50), default='pending')  # pending, signed_up, rewarded
    
    # Reward Tracking
    reward_granted = Column(Boolean, default=False)
    reward_granted_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)  # When referred user signed up

    # Indexes
    __table_args__ = (
        Index('idx_referral_referrer_id', 'referrer_id'),
        Index('idx_referral_referred_user_id', 'referred_user_id'),
        Index('idx_referral_code', 'referral_code'),
        Index('idx_referral_status', 'status'),
    )

    def __repr__(self) -> str:
        return f"<Referral(id={self.id}, referrer_id={self.referrer_id}, status='{self.status}')>"

class EmailSequenceType(str, enum.Enum):
    """Email sequence types"""
    WELCOME = "welcome"
    TRIAL_CONVERSION = "trial_conversion"
    ONBOARDING = "onboarding"
    RE_ENGAGEMENT = "re_engagement"

class EmailSequence(Base):
    """Track email sequence memberships for marketing automation"""
    __tablename__ = "email_sequences"
    
    # Primary Key
    id = Column(GUID(), primary_key=True, default=uuid_module.uuid4)
    
    # Foreign Key
    user_id = Column(GUID(), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Sequence Details
    sequence_name = Column(SQLEnum(EmailSequenceType), nullable=False, index=True)
    current_step = Column(Integer, default=0, nullable=False)  # Current step in sequence (0-indexed)
    
    # Status
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    paused = Column(Boolean, default=False)
    unsubscribed = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_email_sequence_user_id', 'user_id'),
        Index('idx_email_sequence_name', 'sequence_name'),
        Index('idx_email_sequence_started', 'started_at'),
    )
    
    def __repr__(self) -> str:
        seq_name = self.sequence_name.value if hasattr(self.sequence_name, 'value') else self.sequence_name
        return f"<EmailSequence(id={self.id}, user_id={self.user_id}, sequence='{seq_name}', step={self.current_step})>"

class EmailLog(Base):
    """Log all sent emails for tracking and compliance"""
    __tablename__ = "email_logs"
    
    # Primary Key
    id = Column(GUID(), primary_key=True, default=uuid_module.uuid4)
    
    # Foreign Key (nullable for emails to non-users)
    user_id = Column(GUID(), ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    
    # Email Details
    email_address = Column(String(255), nullable=False, index=True)
    email_type = Column(String(100), nullable=False, index=True)  # welcome, trial_reminder, etc.
    subject = Column(String(500), nullable=False)
    template_version = Column(String(50), nullable=True)
    
    # Tracking
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    opened_at = Column(DateTime, nullable=True)
    clicked_at = Column(DateTime, nullable=True)
    bounced_at = Column(DateTime, nullable=True)
    
    # External Service
    external_id = Column(String(255), nullable=True)  # SendGrid/Mailgun message ID
    external_status = Column(String(50), nullable=True)  # delivered, bounced, etc.
    
    # Additional Data (renamed from metadata to avoid SQLAlchemy reserved name)
    additional_data = Column(JSONBCompatible, nullable=True)  # Additional tracking data
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_email_log_user_id', 'user_id'),
        Index('idx_email_log_email_address', 'email_address'),
        Index('idx_email_log_type', 'email_type'),
        Index('idx_email_log_sent_at', 'sent_at'),
    )
    
    def __repr__(self) -> str:
        return f"<EmailLog(id={self.id}, email='{self.email_address}', type='{self.email_type}')>"

class AnalyticsEvent(Base):
    """Track user events for analytics and funnel analysis"""
    __tablename__ = "analytics_events"
    
    # Primary Key
    id = Column(GUID(), primary_key=True, default=uuid_module.uuid4)
    
    # User (nullable for anonymous events)
    user_id = Column(GUID(), ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    session_id = Column(String(255), nullable=True, index=True)
    
    # Event Details
    event_name = Column(String(255), nullable=False, index=True)
    event_properties = Column(JSONBCompatible, nullable=True)  # Flexible event data
    
    # UTM Tracking
    utm_source = Column(String(255), nullable=True, index=True)
    utm_medium = Column(String(255), nullable=True)
    utm_campaign = Column(String(255), nullable=True)
    utm_term = Column(String(255), nullable=True)
    utm_content = Column(String(255), nullable=True)
    
    # Request Metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)
    referrer = Column(String(512), nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_analytics_event_user_id', 'user_id'),
        Index('idx_analytics_event_session_id', 'session_id'),
        Index('idx_analytics_event_name', 'event_name'),
        Index('idx_analytics_event_created_at', 'created_at'),
        Index('idx_analytics_event_utm_source', 'utm_source'),
    )
    
    def __repr__(self) -> str:
        return f"<AnalyticsEvent(id={self.id}, event='{self.event_name}', user_id={self.user_id})>"

class FunnelType(str, enum.Enum):
    """Conversion funnel types"""
    SIGNUP = "signup"
    ACTIVATION = "activation"
    CONVERSION = "conversion"
    RETENTION = "retention"

class ConversionFunnel(Base):
    """Track user progression through conversion funnels"""
    __tablename__ = "conversion_funnels"
    
    # Primary Key
    id = Column(GUID(), primary_key=True, default=uuid_module.uuid4)
    
    # Foreign Key
    user_id = Column(GUID(), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Funnel Details
    funnel_type = Column(SQLEnum(FunnelType), nullable=False, index=True)
    step_name = Column(String(255), nullable=False, index=True)
    
    # Completion
    completed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Additional Data (renamed from metadata to avoid SQLAlchemy reserved name)
    additional_data = Column(JSONBCompatible, nullable=True)  # Additional step data
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_conversion_funnel_user_id', 'user_id'),
        Index('idx_conversion_funnel_type', 'funnel_type'),
        Index('idx_conversion_funnel_step', 'step_name'),
        Index('idx_conversion_funnel_completed', 'completed_at'),
    )
    
    def __repr__(self) -> str:
        funnel_value = self.funnel_type.value if hasattr(self.funnel_type, 'value') else self.funnel_type
        return f"<ConversionFunnel(id={self.id}, user_id={self.user_id}, funnel='{funnel_value}', step='{self.step_name}')>"

# Module exports
__all__ = [
    'Base',
    'User',
    'Receipt',
    'Subscription',
    'APIKey',
    'RefreshToken',
    'AuditLog',
    'Referral',
    'EmailSequence',
    'EmailLog',
    'AnalyticsEvent',
    'ConversionFunnel',
    'SubscriptionPlan',
    'SubscriptionStatus',
    'CloudStorageProvider',
    'EmailSequenceType',
    'FunnelType',
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

def _get_db_context() -> Callable:
    """
    Lazy import of database context.
    
    Returns:
        Callable: Database context function
    """
    global _db_context
    if _db_context is None:
        from database.connection import get_db_context
        _db_context = get_db_context
    return _db_context

def _get_models() -> Tuple[Any, Any]:
    """
    Lazy import of database models.
    
    Returns:
        Tuple[Any, Any]: Receipt and User model classes
    """
    global _Receipt, _User
    if _Receipt is None:
        from database.models import Receipt, User
        _Receipt = Receipt
        _User = User
    return _Receipt, _User

def require_auth_simple(f: Callable) -> Callable:
    """
    Simple auth check decorator for receipts routes.
    
    Args:
        f: Function to decorate
        
    Returns:
        Callable: Decorated function with authentication check
    """
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Tuple[Any, int]:
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
def list_receipts() -> Tuple[Any, int]:
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
        Tuple[Any, int]: JSON response with list of receipts and HTTP status code
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
def get_receipt(receipt_id: str) -> Tuple[Any, int]:
    """
    Get a specific receipt by ID.
    
    Args:
        receipt_id: Receipt ID to retrieve
    
    Returns:
        Tuple[Any, int]: JSON response with receipt details and HTTP status code
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
def delete_receipt(receipt_id: str) -> Tuple[Any, int]:
    """
    Delete a receipt.
    
    Args:
        receipt_id: Receipt ID to delete
    
    Returns:
        Tuple[Any, int]: JSON response with deletion result and HTTP status code
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
def update_receipt(receipt_id: str) -> Tuple[Any, int]:
    """
    Update receipt data (e.g., correct extracted information).
    
    Args:
        receipt_id: Receipt ID to update
    
    Request body:
        {
            "store_name": "Updated Store Name",
            "total_amount": 25.99,
            "transaction_date": "2024-01-15",
            "extracted_data": { ... }
        }
    
    Returns:
        Tuple[Any, int]: JSON response with update result and HTTP status code
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

            receipt.updated_at = datetime.now(timezone.utc)
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
def get_receipt_stats() -> Tuple[Any, int]:
    """
    Get receipt statistics for the current user.
    
    Query parameters:
        period: Time period (month, year, all)
    
    Returns:
        Tuple[Any, int]: JSON response with statistics and HTTP status code
    """
    try:
        from sqlalchemy import func
        Receipt, _ = _get_models()
        
        period = request.args.get('period', 'month')
        
        with _get_db_context()() as db:
            query = db.query(Receipt).filter(Receipt.user_id == g.user_id)

            # Apply time filter
            now = datetime.now(timezone.utc)
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

def register_receipts_routes(app: Any) -> None:
    """
    Register receipts blueprint with the Flask app.
    
    Args:
        app: Flask application instance
    """
    app.register_blueprint(receipts_bp)
    logger.info("Receipts routes registered")
