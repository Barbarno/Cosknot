"""busqueda de texto completo

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-13 21:26:00.000000

Índices GIN sobre la expresión que usa `busqueda.py`. Son solo de PostgreSQL: en
SQLite la búsqueda va por ILIKE y no hay nada que indexar. La expresión tiene que
ser idéntica a la de la consulta (`to_tsvector('spanish', ...)` con literales) o el
planificador no usará el índice.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op


revision: str = '0006'
down_revision: Union[str, None] = '0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DOCUMENTO_CREADORES = (
    "to_tsvector('spanish', coalesce(name, '') || ' ' || coalesce(bio, '')"
    " || ' ' || coalesce(location, '') || ' ' || coalesce(specialty, ''))"
)
DOCUMENTO_OBRAS = (
    "to_tsvector('spanish', coalesce(title, '') || ' ' || coalesce(description, ''))"
)


def upgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    op.execute(
        "CREATE INDEX ix_creators_busqueda ON creators USING gin ("
        + DOCUMENTO_CREADORES
        + ")"
    )
    op.execute(
        "CREATE INDEX ix_works_busqueda ON works USING gin (" + DOCUMENTO_OBRAS + ")"
    )


def downgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    op.execute("DROP INDEX IF EXISTS ix_works_busqueda")
    op.execute("DROP INDEX IF EXISTS ix_creators_busqueda")
