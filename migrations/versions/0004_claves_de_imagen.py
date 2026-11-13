"""claves de imagen

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-13 21:16:23.749727

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0004'
down_revision: Union[str, None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # batch reconstruye la tabla en SQLite, que no tiene ALTER COLUMN, y hace un
    # ALTER normal en PostgreSQL.
    with op.batch_alter_table('creators') as batch_op:
        batch_op.add_column(sa.Column('image_key', sa.String(length=255), nullable=True))
    with op.batch_alter_table('works') as batch_op:
        batch_op.add_column(sa.Column('image_key', sa.String(length=255), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('works') as batch_op:
        batch_op.drop_column('image_key')
    with op.batch_alter_table('creators') as batch_op:
        batch_op.drop_column('image_key')
