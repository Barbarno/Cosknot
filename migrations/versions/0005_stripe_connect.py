"""stripe connect

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-13 21:21:44.627234

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0005'
down_revision: Union[str, None] = '0004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('creators') as batch_op:
        batch_op.add_column(sa.Column('stripe_account_id', sa.String(length=255), nullable=True))
        # false() se traduce a `0` en SQLite y a `false` en PostgreSQL.
        batch_op.add_column(
            sa.Column(
                'stripe_onboarding_ok',
                sa.Boolean(),
                server_default=sa.false(),
                nullable=False,
            )
        )
        batch_op.create_unique_constraint(
            'uq_creators_stripe_account_id', ['stripe_account_id']
        )

    with op.batch_alter_table('orders') as batch_op:
        batch_op.add_column(
            sa.Column('stripe_payment_intent_id', sa.String(length=255), nullable=True)
        )
        batch_op.add_column(
            sa.Column('stripe_checkout_session_id', sa.String(length=255), nullable=True)
        )
        batch_op.add_column(sa.Column('paid_at', sa.DateTime(), nullable=True))
        batch_op.create_unique_constraint(
            'uq_orders_stripe_payment_intent', ['stripe_payment_intent_id']
        )
        batch_op.create_unique_constraint(
            'uq_orders_stripe_checkout_session', ['stripe_checkout_session_id']
        )


def downgrade() -> None:
    with op.batch_alter_table('orders') as batch_op:
        batch_op.drop_constraint('uq_orders_stripe_checkout_session', type_='unique')
        batch_op.drop_constraint('uq_orders_stripe_payment_intent', type_='unique')
        batch_op.drop_column('paid_at')
        batch_op.drop_column('stripe_checkout_session_id')
        batch_op.drop_column('stripe_payment_intent_id')

    with op.batch_alter_table('creators') as batch_op:
        batch_op.drop_constraint('uq_creators_stripe_account_id', type_='unique')
        batch_op.drop_column('stripe_onboarding_ok')
        batch_op.drop_column('stripe_account_id')
