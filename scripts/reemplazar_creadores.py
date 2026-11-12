"""Borra el catálogo actual y lo vuelve a sembrar desde `seed.py`.

Sirve para actualizar los creadores de una base de datos que ya tiene datos,
por ejemplo la de Neon. Sin argumentos usa `DATABASE_URL`; si no está definida,
falla.

    DATABASE_URL="postgresql://usuario:clave@host/base" python scripts/reemplazar_creadores.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, delete, func, select
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models import Base, Creator, Work  # noqa: E402
from seed import seed_database  # noqa: E402


def url_de_entorno() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("falta DATABASE_URL en el entorno")
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://") :]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


def main() -> None:
    url = url_de_entorno()
    opciones = {}
    if url.startswith("postgresql"):
        # Neon va por el pooler en modo transacción: sin caché de prepared statements.
        opciones = {
            "connect_args": {"sslmode": "require", "prepare_threshold": None},
            "pool_pre_ping": True,
        }

    engine = create_engine(url, **opciones)
    Base.metadata.create_all(engine)
    sesion = sessionmaker(bind=engine, expire_on_commit=False)

    with sesion() as s:
        s.execute(delete(Work))
        s.execute(delete(Creator))
        s.commit()
        seed_database(s)
        creadores = s.scalar(select(func.count()).select_from(Creator))
        obras = s.scalar(select(func.count()).select_from(Work))
        print(f"creadores: {creadores}, obras: {obras}")


if __name__ == "__main__":
    main()
