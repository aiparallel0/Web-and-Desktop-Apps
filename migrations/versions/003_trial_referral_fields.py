"""Add trial management and referral fields

Revision ID: 003
Revises: 002
Create Date: 2024-12-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    """Add trial management and referral system fields to users table."""
    
    # Add trial management fields
    op.add_column('users', sa.Column('trial_start_date', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('trial_end_date', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('trial_activated', sa.Boolean(), nullable=False, server_default='false'))
    
    # Add referral system fields
    op.add_column('users', sa.Column('referral_code', sa.String(20), nullable=True))
    op.add_column('users', sa.Column('referred_by', sa.String(36), nullable=True))
    op.add_column('users', sa.Column('referral_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('referral_reward_months', sa.Integer(), nullable=False, server_default='0'))
    
    # Add onboarding fields
    op.add_column('users', sa.Column('onboarding_completed', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('onboarding_step', sa.Integer(), nullable=False, server_default='0'))
    
    # Create indexes for better query performance
    op.create_index('idx_user_referral_code', 'users', ['referral_code'], unique=True)
    op.create_index('idx_user_trial_end', 'users', ['trial_end_date'])
    
    # Add foreign key for referred_by
    # Note: Using string type for UUID compatibility with SQLite
    # In production PostgreSQL, this would be a proper UUID FK
    
    # Create referrals table
    op.create_table(
        'referrals',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('referrer_id', sa.String(36), nullable=False),
        sa.Column('referred_user_id', sa.String(36), nullable=True),
        sa.Column('referral_code', sa.String(20), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('reward_granted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('reward_granted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True)
    )
    
    # Create indexes for referrals table
    op.create_index('idx_referral_referrer_id', 'referrals', ['referrer_id'])
    op.create_index('idx_referral_referred_user_id', 'referrals', ['referred_user_id'])
    op.create_index('idx_referral_code', 'referrals', ['referral_code'])
    op.create_index('idx_referral_status', 'referrals', ['status'])


def downgrade():
    """Remove trial management and referral system fields."""
    
    # Drop referrals table indexes
    op.drop_index('idx_referral_status', 'referrals')
    op.drop_index('idx_referral_code', 'referrals')
    op.drop_index('idx_referral_referred_user_id', 'referrals')
    op.drop_index('idx_referral_referrer_id', 'referrals')
    
    # Drop referrals table
    op.drop_table('referrals')
    
    # Drop indexes from users table
    op.drop_index('idx_user_trial_end', 'users')
    op.drop_index('idx_user_referral_code', 'users')
    
    # Remove onboarding fields
    op.drop_column('users', 'onboarding_step')
    op.drop_column('users', 'onboarding_completed')
    
    # Remove referral fields
    op.drop_column('users', 'referral_reward_months')
    op.drop_column('users', 'referral_count')
    op.drop_column('users', 'referred_by')
    op.drop_column('users', 'referral_code')
    
    # Remove trial fields
    op.drop_column('users', 'trial_activated')
    op.drop_column('users', 'trial_end_date')
    op.drop_column('users', 'trial_start_date')
