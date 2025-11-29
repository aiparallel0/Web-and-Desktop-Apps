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
