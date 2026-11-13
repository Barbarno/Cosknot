"""Motor y URL de la base de datos.

Vive aparte de `app.py` para que `migrations/env.py` pueda importar la
normalización de la URL sin ejecutar `create_app()` (que arranca motor y siembra
el catálogo).
"""

from __future__ import annotations

import os
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

DEFAULT_DATABASE_URL = "sqlite:///cosknot.db"

# Heroku Postgres Essential-0 da 20 conexiones y el plan no se puede subir sin
# salirse de los 13 $ del crédito. El reparto, con un solo dyno web de 4 hilos:
#
#   1 worker × (pool_size 3 + max_overflow 2) = 5 conexiones de la app
#   1 conexión del proceso `release` mientras corre `alembic upgrade head`
#   1 conexión del `pg_dump` de la copia diaria de GitHub Actions
#   1 conexión de un `heroku pg:psql` puntual
#   ---------------------------------------------------------------
#   8 como techo cómodo, 12 de margen sobre el límite de 20.
#
# Todo se puede ajustar por variable de entorno sin tocar código, pero subirlo
# sin medir es la forma más rápida de tumbar la web con "too many connections".
DEFAULT_POOL_SIZE = 3
DEFAULT_MAX_OVERFLOW = 2
DEFAULT_POOL_RECYCLE = 300
DEFAULT_POOL_TIMEOUT = 10


def normalize_database_url(url: str | None) -> str:
    if not url:
        return DEFAULT_DATABASE_URL
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


def _entero(variable: str, defecto: int) -> int:
    """Lee un entero de entorno; si falta o no es un número, usa el defecto."""
    valor = (os.environ.get(variable) or "").strip()
    if not valor:
        return defecto
    try:
        return int(valor)
    except ValueError:
        return defecto


def engine_options(url: str) -> dict[str, Any]:
    """Opciones de `create_engine` según el motor. Separado para poder probarlas."""
    options: dict[str, Any] = {}
    if url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
        if ":memory:" in url or url.endswith(":memory:"):
            from sqlalchemy.pool import StaticPool

            options["poolclass"] = StaticPool
    else:
        # Heroku Postgres solo acepta TLS. El `sslmode` va en el connect_args y no
        # en la URL porque Heroku sobrescribe DATABASE_URL y las credenciales se
        # rotan: el proceso siempre lee la variable del dyno, nunca una copia.
        options["connect_args"] = {"sslmode": "require"}
        options["pool_pre_ping"] = True
        # Heroku corta las conexiones ociosas; reciclarlas antes evita el
        # "server closed the connection unexpectedly" en el primer clic del día.
        options["pool_recycle"] = _entero("DB_POOL_RECYCLE", DEFAULT_POOL_RECYCLE)
        options["pool_size"] = _entero("DB_POOL_SIZE", DEFAULT_POOL_SIZE)
        options["max_overflow"] = _entero("DB_MAX_OVERFLOW", DEFAULT_MAX_OVERFLOW)
        options["pool_timeout"] = _entero("DB_POOL_TIMEOUT", DEFAULT_POOL_TIMEOUT)
    return options


def build_engine(url: str) -> Engine:
    return create_engine(url, **engine_options(url))
