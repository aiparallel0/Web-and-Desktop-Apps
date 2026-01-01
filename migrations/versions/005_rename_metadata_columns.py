"""Rename metadata columns to avoid SQLAlchemy reserved name

Revision ID: 005
Revises: 004
Create Date: 2026-01-01

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    """Rename metadata columns to additional_data to avoid SQLAlchemy reserved name conflict."""
    
    # Rename metadata column in email_logs table to additional_data
    with op.batch_alter_table('email_logs', schema=None) as batch_op:
        batch_op.alter_column('metadata',
                              new_column_name='additional_data',
                              existing_type=sa.JSON(),
                              existing_nullable=True)
    
    # Rename metadata column in conversion_funnels table to additional_data
    with op.batch_alter_table('conversion_funnels', schema=None) as batch_op:
        batch_op.alter_column('metadata',
                              new_column_name='additional_data',
                              existing_type=sa.JSON(),
                              existing_nullable=True)


def downgrade():
    """Revert column names back to metadata."""
    
    # Rename additional_data back to metadata in email_logs table
    with op.batch_alter_table('email_logs', schema=None) as batch_op:
        batch_op.alter_column('additional_data',
                              new_column_name='metadata',
                              existing_type=sa.JSON(),
                              existing_nullable=True)
    
    # Rename additional_data back to metadata in conversion_funnels table
    with op.batch_alter_table('conversion_funnels', schema=None) as batch_op:
        batch_op.alter_column('additional_data',
                              new_column_name='metadata',
                              existing_type=sa.JSON(),
                              existing_nullable=True)
