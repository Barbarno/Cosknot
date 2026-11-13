"""buzon de avisos pendientes

Revision ID: 0007
Revises: 0006
Create Date: 2026-11-13 23:10:00.000000

Tabla `email_outbox`: el aviso que falla en la petición se guarda aquí y el hilo
del proceso web lo reintenta cada minuto. `clave` es única para que un doble clic
o un reintento del navegador no encolen el mismo aviso dos veces.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = '0007'
down_revision: Union[str, None] = '0006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "email_outbox",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("clave", sa.String(length=64), nullable=False),
        sa.Column("destinatario", sa.String(length=200), nullable=False),
        sa.Column("asunto", sa.String(length=200), nullable=False),
        sa.Column("cuerpo", sa.Text(), nullable=False),
        sa.Column(
            "estado", sa.String(length=20), server_default="pendiente", nullable=False
        ),
        sa.Column("intentos", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "proximo_intento", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("ultimo_error", sa.Text(), nullable=True),
        sa.Column("enviado_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clave", name="uq_email_outbox_clave"),
    )
    op.create_index("ix_email_outbox_clave", "email_outbox", ["clave"])
    op.create_index(
        "ix_email_outbox_destinatario", "email_outbox", ["destinatario"]
    )
    op.create_index("ix_email_outbox_estado", "email_outbox", ["estado"])
    op.create_index(
        "ix_email_outbox_proximo_intento", "email_outbox", ["proximo_intento"]
    )


def downgrade() -> None:
    op.drop_index("ix_email_outbox_proximo_intento", table_name="email_outbox")
    op.drop_index("ix_email_outbox_estado", table_name="email_outbox")
    op.drop_index("ix_email_outbox_destinatario", table_name="email_outbox")
    op.drop_index("ix_email_outbox_clave", table_name="email_outbox")
    op.drop_table("email_outbox")
