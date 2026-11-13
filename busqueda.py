"""Búsqueda del escaparate.

Dos caminos, mismos resultados:

- **PostgreSQL**: texto completo en español con `to_tsvector('spanish', ...)` y
  `plainto_tsquery('spanish', ...)`, apoyado en índices GIN (migración 0007). El
  stemmer hace que «capas» encuentre «capa».
- **SQLite**: `ILIKE` sobre los mismos campos. Es el motor de desarrollo y de las
  pruebas; no tiene texto completo y no hace falta.

`motor_de()` mira el dialecto de la sesión, así que la ruta no cambia.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Select, func, literal_column, or_, select

from models import Creator, Work

CAMPOS_CREADOR = ("name", "bio", "location", "specialty")
CAMPOS_OBRA = ("title", "description")

# Literales y no parámetros: el índice GIN se crea con `'spanish'` y `''` fijos, y
# PostgreSQL solo reutiliza el índice si la expresión de la consulta es idéntica.
CONFIGURACION_TEXTO = literal_column("'spanish'")
VACIO = literal_column("''")


def motor_de(sesion) -> str:
    return sesion.get_bind().dialect.name


def _documento(modelo, campos: tuple[str, ...]) -> Any:
    """Concatena los campos de texto en un solo documento."""
    partes = [func.coalesce(getattr(modelo, campo), VACIO) for campo in campos]
    documento = partes[0]
    for parte in partes[1:]:
        documento = documento + literal_column("' '") + parte
    return documento


def consulta_creadores_postgres(consulta: str) -> Select:
    documento = func.to_tsvector(CONFIGURACION_TEXTO, _documento(Creator, CAMPOS_CREADOR))
    pregunta = func.plainto_tsquery(CONFIGURACION_TEXTO, consulta)
    return (
        select(Creator)
        .where(documento.op("@@")(pregunta))
        .order_by(func.ts_rank(documento, pregunta).desc(), Creator.name)
    )


def consulta_obras_postgres(consulta: str) -> Select:
    documento = func.to_tsvector(CONFIGURACION_TEXTO, _documento(Work, CAMPOS_OBRA))
    pregunta = func.plainto_tsquery(CONFIGURACION_TEXTO, consulta)
    return (
        select(Work)
        .where(documento.op("@@")(pregunta))
        .order_by(func.ts_rank(documento, pregunta).desc(), Work.id.desc())
    )


def consulta_creadores_ilike(consulta: str) -> Select:
    patron = f"%{consulta}%"
    return (
        select(Creator)
        .where(
            or_(*[getattr(Creator, campo).ilike(patron) for campo in CAMPOS_CREADOR])
        )
        .order_by(Creator.name)
    )


def consulta_obras_ilike(consulta: str) -> Select:
    patron = f"%{consulta}%"
    return (
        select(Work)
        .where(or_(*[getattr(Work, campo).ilike(patron) for campo in CAMPOS_OBRA]))
        .order_by(Work.id.desc())
    )


def buscar_creadores(sesion, consulta: str) -> list[Creator]:
    sentencia = (
        consulta_creadores_postgres(consulta)
        if motor_de(sesion) == "postgresql"
        else consulta_creadores_ilike(consulta)
    )
    return list(sesion.scalars(sentencia).all())


def buscar_obras(sesion, consulta: str) -> list[Work]:
    sentencia = (
        consulta_obras_postgres(consulta)
        if motor_de(sesion) == "postgresql"
        else consulta_obras_ilike(consulta)
    )
    return list(sesion.scalars(sentencia).all())
