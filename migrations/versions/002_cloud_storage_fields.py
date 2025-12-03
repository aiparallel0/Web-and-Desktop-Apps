"""Add cloud storage and HuggingFace API fields

Revision ID: 002_cloud_storage_fields
Revises: 001_initial_schema
Create Date: 2024-12-03

This migration adds fields for:
- HuggingFace API key storage (encrypted) on users table
- Cloud storage key and thumbnail URL on receipts table (if not exists)
- Index for cloud storage queries on receipts table

Note: cloud_storage_provider and cloud_storage_credentials were added in 001_initial_schema.
This migration adds the remaining cloud integration fields.

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '002_cloud_storage_fields'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def index_exists(table_name: str, index_name: str) -> bool:
    """Check if an index exists on a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    indexes = [idx['name'] for idx in inspector.get_indexes(table_name)]
    return index_name in indexes


def upgrade() -> None:
    """Add cloud storage and HuggingFace API fields."""
    
    # Add hf_api_key_encrypted to users table
    if not column_exists('users', 'hf_api_key_encrypted'):
        op.add_column(
            'users',
            sa.Column('hf_api_key_encrypted', sa.Text(), nullable=True)
        )
    
    # Verify cloud_storage_key exists on receipts (should exist from 001)
    # Add if missing for safety
    if not column_exists('receipts', 'cloud_storage_key'):
        op.add_column(
            'receipts',
            sa.Column('cloud_storage_key', sa.String(512), nullable=True)
        )
    
    # Verify thumbnail_url exists on receipts (should exist from 001)
    # Add if missing for safety
    if not column_exists('receipts', 'thumbnail_url'):
        op.add_column(
            'receipts',
            sa.Column('thumbnail_url', sa.String(512), nullable=True)
        )
    
    # Verify cloud_storage_provider exists on users (should exist from 001)
    if not column_exists('users', 'cloud_storage_provider'):
        op.add_column(
            'users',
            sa.Column('cloud_storage_provider', sa.String(20), nullable=False, server_default='none')
        )
    
    # Verify cloud_storage_credentials exists on users (should exist from 001)
    if not column_exists('users', 'cloud_storage_credentials'):
        op.add_column(
            'users',
            sa.Column('cloud_storage_credentials', sa.Text(), nullable=True)
        )
    
    # Create index for cloud storage queries if not exists
    if not index_exists('receipts', 'idx_receipt_cloud_key'):
        op.create_index(
            'idx_receipt_cloud_key',
            'receipts',
            ['cloud_storage_key'],
            unique=False
        )


def downgrade() -> None:
    """Remove cloud storage and HuggingFace API fields."""
    
    # Drop index first
    if index_exists('receipts', 'idx_receipt_cloud_key'):
        op.drop_index('idx_receipt_cloud_key', table_name='receipts')
    
    # Remove columns added in this migration
    # Note: We only drop hf_api_key_encrypted as others were from 001_initial_schema
    if column_exists('users', 'hf_api_key_encrypted'):
        op.drop_column('users', 'hf_api_key_encrypted')
