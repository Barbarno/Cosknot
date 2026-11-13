"""Aplicación de las migraciones de Alembic al arrancar.

En PostgreSQL el esquema lo mueve Alembic. Gunicorn levanta varios workers y
cada uno ejecuta `create_app()`, así que todos intentarían migrar a la vez y
Alembic no serializa ese trabajo: dos `ALTER TABLE` simultáneos se pisan.

La solución más simple que funciona es un advisory lock de PostgreSQL tomado
en una conexión aparte que se mantiene abierta mientras corre `upgrade`. El
lock es de sesión, no de transacción, así que basta con soltarlo al final.
Los workers que llegan tarde esperan, encuentran la base ya migrada y su
`upgrade` es un no-op.
"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text

from db import build_engine

RAIZ = Path(__file__).resolve().parent

# Identificador arbitrario y estable del lock: "cosk" en hexadecimal.
CLAVE_BLOQUEO = 0x636F736B


def config_alembic(url: str) -> Config:
    cfg = Config(str(RAIZ / "alembic.ini"))
    cfg.set_main_option("script_location", str(RAIZ / "migrations"))
    # `%` es el carácter de interpolación de ConfigParser: hay que escaparlo o
    # una contraseña con `%` rompe el arranque.
    cfg.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    return cfg


def aplicar_migraciones(url: str) -> None:
    cfg = config_alembic(url)
    engine = build_engine(url)
    conexion = None
    if engine.dialect.name == "postgresql":
        conexion = engine.connect()
        conexion.execute(text("SELECT pg_advisory_lock(:clave)"), {"clave": CLAVE_BLOQUEO})
    try:
        command.upgrade(cfg, "head")
    finally:
        if conexion is not None:
            conexion.execute(
                text("SELECT pg_advisory_unlock(:clave)"), {"clave": CLAVE_BLOQUEO}
            )
            conexion.commit()
            conexion.close()
        engine.dispose()
