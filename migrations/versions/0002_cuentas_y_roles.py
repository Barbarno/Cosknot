"""cuentas y roles

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-13 21:08:29.272741

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=200), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)

    # batch_alter_table reconstruye la tabla en SQLite (que no admite ADD COLUMN
    # con clave foránea) y hace un ALTER normal en PostgreSQL.
    with op.batch_alter_table('creators') as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_creators_user_id_users', 'users', ['user_id'], ['id']
        )
    op.create_index(op.f('ix_creators_user_id'), 'creators', ['user_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_creators_user_id'), table_name='creators')
    with op.batch_alter_table('creators') as batch_op:
        batch_op.drop_constraint('fk_creators_user_id_users', type_='foreignkey')
        batch_op.drop_column('user_id')
    op.drop_index(op.f('ix_users_role'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
