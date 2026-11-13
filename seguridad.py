"""Hash de contraseñas y utilidades de slug."""

from __future__ import annotations

import re
import unicodedata

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from sqlalchemy import select
from sqlalchemy.orm import Session

_hasher = PasswordHasher()

LONGITUD_MINIMA = 8
LONGITUD_MAXIMA = 128


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verificar_password(hash_guardado: str, password: str) -> bool:
    try:
        return _hasher.verify(hash_guardado, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def necesita_rehash(hash_guardado: str) -> bool:
    try:
        return _hasher.check_needs_rehash(hash_guardado)
    except InvalidHashError:
        return True


def normalizar_email(email: str | None) -> str:
    return (email or "").strip().lower()


def slugify(texto: str) -> str:
    normalizado = unicodedata.normalize("NFKD", texto)
    ascii_plano = normalizado.encode("ascii", "ignore").decode("ascii")
    limpio = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_plano).strip("-").lower()
    return limpio or "sin-nombre"


def slug_unico(sesion: Session, modelo, base: str) -> str:
    """Devuelve un slug libre para `modelo`, añadiendo -2, -3... si hace falta."""
    candidato = base[:110]
    existentes = set(
        sesion.scalars(select(modelo.slug).where(modelo.slug.like(f"{candidato}%"))).all()
    )
    if candidato not in existentes:
        return candidato
    sufijo = 2
    while f"{candidato}-{sufijo}" in existentes:
        sufijo += 1
    return f"{candidato}-{sufijo}"
