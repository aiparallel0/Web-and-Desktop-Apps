"""
=============================================================================
ALEMBIC ENV - Migration Environment Configuration
=============================================================================

This is the Alembic environment configuration file. It sets up the
database connection and migration context.

=============================================================================
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import your models' MetaData object here
# for 'autogenerate' support
try:
    from web.backend.database import Base
    target_metadata = Base.metadata
except ImportError:
    target_metadata = None

# Get database URL from environment
def get_url():
    """Get database URL from environment or config."""
    # Check for SQLite development/testing mode (matching web/backend/database.py logic)
    if os.getenv('USE_SQLITE', 'false').lower() == 'true' or os.getenv('TESTING', 'false').lower() == 'true':
        url = os.getenv('DATABASE_URL', 'sqlite:///./receipt_extractor.db')
        if not url.startswith('sqlite'):
            url = 'sqlite:///./receipt_extractor.db'
        return url
    
    url = os.getenv('DATABASE_URL')
    if url:
        # Handle postgres:// vs postgresql:// for SQLAlchemy 2.0
        if url.startswith('postgres://'):
            url = url.replace('postgres://', 'postgresql://', 1)
        return url
    return config.get_main_option("sqlalchemy.url")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
