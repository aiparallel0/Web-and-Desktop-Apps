"""Initial migration - create all tables

Revision ID: 001_initial
Revises: 
Create Date: 2024-12-03

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial database schema."""
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('email_verified', sa.Boolean(), default=False),
        sa.Column('email_verification_token', sa.String(255), nullable=True),
        sa.Column('password_reset_token', sa.String(255), nullable=True),
        sa.Column('password_reset_expires', sa.DateTime(), nullable=True),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('company', sa.String(255), nullable=True),
        sa.Column('plan', sa.String(20), default='free', nullable=False),
        sa.Column('stripe_customer_id', sa.String(255), nullable=True, unique=True),
        sa.Column('receipts_processed_month', sa.Integer(), default=0),
        sa.Column('storage_used_bytes', sa.Integer(), default=0),
        sa.Column('cloud_storage_provider', sa.String(20), default='none', nullable=False),
        sa.Column('cloud_storage_credentials', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_admin', sa.Boolean(), default=False),
    )
    
    # Create indexes for users
    op.create_index('idx_user_email', 'users', ['email'])
    op.create_index('idx_user_plan', 'users', ['plan'])
    op.create_index('idx_user_created_at', 'users', ['created_at'])
    
    # Create receipts table
    op.create_table(
        'receipts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('image_url', sa.String(512), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('cloud_storage_key', sa.String(512), nullable=True),
        sa.Column('thumbnail_url', sa.String(512), nullable=True),
        sa.Column('extracted_data', sa.JSON(), nullable=True),
        sa.Column('store_name', sa.String(255), nullable=True),
        sa.Column('total_amount', sa.Float(), nullable=True),
        sa.Column('transaction_date', sa.DateTime(), nullable=True),
        sa.Column('model_used', sa.String(100), nullable=False),
        sa.Column('processing_time_seconds', sa.Float(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('status', sa.String(50), default='processing'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create indexes for receipts
    op.create_index('idx_receipt_user_id', 'receipts', ['user_id'])
    op.create_index('idx_receipt_created_at', 'receipts', ['created_at'])
    op.create_index('idx_receipt_store_name', 'receipts', ['store_name'])
    op.create_index('idx_receipt_transaction_date', 'receipts', ['transaction_date'])
    op.create_index('idx_receipt_status', 'receipts', ['status'])
    op.create_index('idx_receipt_cloud_key', 'receipts', ['cloud_storage_key'])
    
    # Create subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('stripe_subscription_id', sa.String(255), unique=True, nullable=False),
        sa.Column('stripe_price_id', sa.String(255), nullable=True),
        sa.Column('plan', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('current_period_start', sa.DateTime(), nullable=True),
        sa.Column('current_period_end', sa.DateTime(), nullable=True),
        sa.Column('cancel_at_period_end', sa.Boolean(), default=False),
        sa.Column('canceled_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    op.create_index('idx_subscription_user_id', 'subscriptions', ['user_id'])
    
    # Create API keys table
    op.create_table(
        'api_keys',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('key_hash', sa.String(255), unique=True, nullable=False),
        sa.Column('key_prefix', sa.String(20), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('usage_count', sa.Integer(), default=0),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    op.create_index('idx_api_key_user_id', 'api_keys', ['user_id'])
    op.create_index('idx_api_key_hash', 'api_keys', ['key_hash'])
    
    # Create refresh tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_hash', sa.String(255), unique=True, nullable=False),
        sa.Column('device_info', sa.String(255), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('revoked', sa.Boolean(), default=False),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    op.create_index('idx_refresh_token_user_id', 'refresh_tokens', ['user_id'])
    op.create_index('idx_refresh_token_expires_at', 'refresh_tokens', ['expires_at'])
    op.create_index('idx_refresh_token_revoked', 'refresh_tokens', ['revoked'])
    
    # Create audit logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(100), nullable=True),
        sa.Column('resource_id', sa.String(36), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(512), nullable=True),
        sa.Column('audit_extra_data', sa.JSON(), nullable=True),
        sa.Column('success', sa.Boolean(), default=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    op.create_index('idx_audit_log_user_id', 'audit_logs', ['user_id'])
    op.create_index('idx_audit_log_action', 'audit_logs', ['action'])
    op.create_index('idx_audit_log_created_at', 'audit_logs', ['created_at'])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('audit_logs')
    op.drop_table('refresh_tokens')
    op.drop_table('api_keys')
    op.drop_table('subscriptions')
    op.drop_table('receipts')
    op.drop_table('users')
