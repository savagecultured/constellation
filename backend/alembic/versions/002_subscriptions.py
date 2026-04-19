"""Create subscriptions table

Revision ID: 002_subscriptions
Revises: 001_initial_users
Create Date: 2024-01-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_subscriptions'
down_revision: Union[str, None] = '001_initial_users'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    tier_enum = sa.Enum('FREE', 'BASIC', 'PREMIUM', 'FAMILY', name='subscriptiontier', create_type=False)
    status_enum = sa.Enum('ACTIVE', 'CANCELLED', 'EXPIRED', 'PAST_DUE', 'TRIALING', name='subscriptionstatus', create_type=False)
    
    # Create subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('tier', tier_enum, nullable=False, server_default='FREE'),
        sa.Column('status', status_enum, nullable=False, server_default='TRIALING'),
        sa.Column('external_subscription_id', sa.String(length=255), nullable=True),
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancel_at_period_end', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_in_trial_period', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('external_subscription_id')
    )
    
    # Create indexes
    op.create_index('ix_subscriptions_id', 'subscriptions', ['id'])
    op.create_index('ix_subscriptions_user_id', 'subscriptions', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_subscriptions_user_id', table_name='subscriptions')
    op.drop_index('ix_subscriptions_id', table_name='subscriptions')
    op.drop_table('subscriptions')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS subscriptionstatus')
    op.execute('DROP TYPE IF EXISTS subscriptiontier')