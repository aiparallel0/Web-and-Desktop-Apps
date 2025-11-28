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

# For development, you can override with SQLite
if os.getenv('USE_SQLITE', 'false').lower() == 'true':
    DATABASE_URL = 'sqlite:///./receipt_extractor.db'
    logger.warning("Using SQLite database for development. Not recommended for production!")

# Create engine
# Use NullPool for serverless/Lambda environments
poolclass = NullPool if os.getenv('SERVERLESS', 'false').lower() == 'true' else None

engine = create_engine(
    DATABASE_URL,
    poolclass=poolclass,
    pool_pre_ping=True,  # Verify connections before using
    echo=os.getenv('SQL_ECHO', 'false').lower() == 'true'  # Log SQL queries if SQL_ECHO=true
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create scoped session for thread safety
db_session = scoped_session(SessionLocal)


def init_db():
    """
    Initialize database schema

    This will create all tables if they don't exist.
    For production, use proper migrations (Alembic).
    """
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized successfully")


def drop_all():
    """
    Drop all tables

    WARNING: This will delete all data! Use only for development/testing.
    """
    logger.warning("Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
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
    db = SessionLocal()
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
    db = SessionLocal()
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
