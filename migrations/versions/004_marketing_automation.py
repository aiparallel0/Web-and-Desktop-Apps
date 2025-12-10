"""Add marketing automation tables

Revision ID: 004
Revises: 003
Create Date: 2024-12-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    """Add marketing automation tables for email sequences, logs, analytics, and conversion funnels."""
    
    # Create email_sequences table
    op.create_table(
        'email_sequences',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('sequence_name', sa.String(50), nullable=False),  # welcome, trial_conversion, onboarding, re_engagement
        sa.Column('current_step', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('paused', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('unsubscribed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )
    
    # Create indexes for email_sequences
    op.create_index('idx_email_sequence_user_id', 'email_sequences', ['user_id'])
    op.create_index('idx_email_sequence_name', 'email_sequences', ['sequence_name'])
    op.create_index('idx_email_sequence_started', 'email_sequences', ['started_at'])
    
    # Create foreign key for user_id
    op.create_foreign_key(
        'fk_email_sequence_user',
        'email_sequences', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # Create email_logs table
    op.create_table(
        'email_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=True),
        sa.Column('email_address', sa.String(255), nullable=False),
        sa.Column('email_type', sa.String(100), nullable=False),
        sa.Column('subject', sa.String(500), nullable=False),
        sa.Column('template_version', sa.String(50), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('opened_at', sa.DateTime(), nullable=True),
        sa.Column('clicked_at', sa.DateTime(), nullable=True),
        sa.Column('bounced_at', sa.DateTime(), nullable=True),
        sa.Column('external_id', sa.String(255), nullable=True),
        sa.Column('external_status', sa.String(50), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )
    
    # Create indexes for email_logs
    op.create_index('idx_email_log_user_id', 'email_logs', ['user_id'])
    op.create_index('idx_email_log_email_address', 'email_logs', ['email_address'])
    op.create_index('idx_email_log_type', 'email_logs', ['email_type'])
    op.create_index('idx_email_log_sent_at', 'email_logs', ['sent_at'])
    
    # Create foreign key for user_id (nullable)
    op.create_foreign_key(
        'fk_email_log_user',
        'email_logs', 'users',
        ['user_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Create analytics_events table
    op.create_table(
        'analytics_events',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=True),
        sa.Column('session_id', sa.String(255), nullable=True),
        sa.Column('event_name', sa.String(255), nullable=False),
        sa.Column('event_properties', sa.JSON(), nullable=True),
        sa.Column('utm_source', sa.String(255), nullable=True),
        sa.Column('utm_medium', sa.String(255), nullable=True),
        sa.Column('utm_campaign', sa.String(255), nullable=True),
        sa.Column('utm_term', sa.String(255), nullable=True),
        sa.Column('utm_content', sa.String(255), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(512), nullable=True),
        sa.Column('referrer', sa.String(512), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )
    
    # Create indexes for analytics_events
    op.create_index('idx_analytics_event_user_id', 'analytics_events', ['user_id'])
    op.create_index('idx_analytics_event_session_id', 'analytics_events', ['session_id'])
    op.create_index('idx_analytics_event_name', 'analytics_events', ['event_name'])
    op.create_index('idx_analytics_event_created_at', 'analytics_events', ['created_at'])
    op.create_index('idx_analytics_event_utm_source', 'analytics_events', ['utm_source'])
    
    # Create foreign key for user_id (nullable)
    op.create_foreign_key(
        'fk_analytics_event_user',
        'analytics_events', 'users',
        ['user_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Create conversion_funnels table
    op.create_table(
        'conversion_funnels',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('funnel_type', sa.String(50), nullable=False),  # signup, activation, conversion, retention
        sa.Column('step_name', sa.String(255), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )
    
    # Create indexes for conversion_funnels
    op.create_index('idx_conversion_funnel_user_id', 'conversion_funnels', ['user_id'])
    op.create_index('idx_conversion_funnel_type', 'conversion_funnels', ['funnel_type'])
    op.create_index('idx_conversion_funnel_step', 'conversion_funnels', ['step_name'])
    op.create_index('idx_conversion_funnel_completed', 'conversion_funnels', ['completed_at'])
    
    # Create foreign key for user_id
    op.create_foreign_key(
        'fk_conversion_funnel_user',
        'conversion_funnels', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade():
    """Remove marketing automation tables."""
    
    # Drop conversion_funnels table
    op.drop_constraint('fk_conversion_funnel_user', 'conversion_funnels', type_='foreignkey')
    op.drop_index('idx_conversion_funnel_completed', 'conversion_funnels')
    op.drop_index('idx_conversion_funnel_step', 'conversion_funnels')
    op.drop_index('idx_conversion_funnel_type', 'conversion_funnels')
    op.drop_index('idx_conversion_funnel_user_id', 'conversion_funnels')
    op.drop_table('conversion_funnels')
    
    # Drop analytics_events table
    op.drop_constraint('fk_analytics_event_user', 'analytics_events', type_='foreignkey')
    op.drop_index('idx_analytics_event_utm_source', 'analytics_events')
    op.drop_index('idx_analytics_event_created_at', 'analytics_events')
    op.drop_index('idx_analytics_event_name', 'analytics_events')
    op.drop_index('idx_analytics_event_session_id', 'analytics_events')
    op.drop_index('idx_analytics_event_user_id', 'analytics_events')
    op.drop_table('analytics_events')
    
    # Drop email_logs table
    op.drop_constraint('fk_email_log_user', 'email_logs', type_='foreignkey')
    op.drop_index('idx_email_log_sent_at', 'email_logs')
    op.drop_index('idx_email_log_type', 'email_logs')
    op.drop_index('idx_email_log_email_address', 'email_logs')
    op.drop_index('idx_email_log_user_id', 'email_logs')
    op.drop_table('email_logs')
    
    # Drop email_sequences table
    op.drop_constraint('fk_email_sequence_user', 'email_sequences', type_='foreignkey')
    op.drop_index('idx_email_sequence_started', 'email_sequences')
    op.drop_index('idx_email_sequence_name', 'email_sequences')
    op.drop_index('idx_email_sequence_user_id', 'email_sequences')
    op.drop_table('email_sequences')
