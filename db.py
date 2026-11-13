"""Motor y URL de la base de datos.

Vive aparte de `app.py` para que `migrations/env.py` pueda importar la
normalización de la URL sin ejecutar `create_app()` (que arranca motor, aplica
esquema y siembra el catálogo).
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

DEFAULT_DATABASE_URL = "sqlite:///cosknot.db"


def normalize_database_url(url: str | None) -> str:
    if not url:
        return DEFAULT_DATABASE_URL
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


def build_engine(url: str) -> Engine:
    options: dict[str, Any] = {}
    if url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
        if ":memory:" in url or url.endswith(":memory:"):
            from sqlalchemy.pool import StaticPool

            options["poolclass"] = StaticPool
    else:
        options["pool_pre_ping"] = True
        # Neon va por pgbouncer en modo transacción: no guarda estado entre
        # transacciones, así que los prepared statements que cachea psycopg3
        # fallan. Desactivando la caché no hay problema.
        options["connect_args"] = {"sslmode": "require", "prepare_threshold": None}
    return create_engine(url, **options)
