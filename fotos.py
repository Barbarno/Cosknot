"""Fotos del escaparate.

Las fotos viejas viven en `static/img` y se eligen por slug. Cuando una obra o un
taller tiene `image_key`, la foto sale del almacén configurado (disco local en
desarrollo, R2 en producción).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from flask import current_app

# Fotos de piezas y talleres sacadas de Wikimedia Commons (licencias libres).
# La lista es explícita porque cada foto se eligió a mano para que pegue con la
# pieza: un casco no puede llevar la foto de un vestido.
FOTO_OBRA = {
    "abrigo-de-invierno-fantasia": "obra-abrigo-de-invierno-fantasia.jpg",
    "vestido-de-gala-anime": "obra-vestido-de-gala-anime.jpg",
    "espada-de-caballero-de-fantasia": "obra-espada-de-caballero-de-fantasia.jpg",
    "pistola-de-ciencia-ficcion": "cat-props-2.jpg",
    "peluca-estilizada-personaje": "obra-peluca-estilizada-personaje.jpg",
    "extensiones-de-color-a-medida": "obra-extensiones-de-color-a-medida.jpg",
    "casco-de-soldado-espacial": "obra-casco-de-soldado-espacial.jpg",
    "hombreras-de-cuero-sintetico": "obra-hombreras-de-cuero-sintetico.jpg",
    "capa-con-capucha-bordada": "obra-capa-con-capucha-bordada.jpg",
    "armadura-textil-acolchada": "pieza-01.jpg",
    "arnes-de-cuero-con-remaches": "pieza-10.jpg",
    "funda-de-daga-de-fantasia": "pieza-09.jpg",
    "guantes-de-armadura-fantasia": "obra-guantes-de-armadura-fantasia.jpg",
    "garras-de-criatura": "pieza-07.jpg",
    "mascara-de-criatura-del-bosque": "pieza-04.jpg",
}

FOTO_TALLER = {
    "marisol-vega": "taller-marisol-vega.jpg",
    "tomas-iriarte": "pieza-11.jpg",
    "lucia-ferrer": "taller-lucia-ferrer.jpg",
    "iker-zabaleta": "pieza-01.jpg",
    "valentina-ortiz": "taller-valentina-ortiz.jpg",
    "diego-salazar": "pieza-10.jpg",
    "sofia-bianchi": "pieza-04.jpg",
}

DIRECTORIO_IMAGENES = Path(__file__).parent / "static" / "img"
FOTOS = sorted(p.name for p in DIRECTORIO_IMAGENES.glob("*.jpg"))


def foto_de(slug: str) -> str:
    """Foto de `static/img` para un slug, con reparto estable por hash."""
    nombre = FOTO_OBRA.get(slug) or FOTO_TALLER.get(slug)
    if nombre is None and FOTOS:
        indice = int(hashlib.md5(slug.encode("utf-8")).hexdigest(), 16) % len(FOTOS)
        nombre = FOTOS[indice]
    return f"/static/img/{nombre}" if nombre else ""


def foto(entidad) -> str:
    """URL de la foto de una obra o un taller. Acepta también un slug suelto."""
    if isinstance(entidad, str):
        return foto_de(entidad)
    clave = getattr(entidad, "image_key", None)
    almacen = current_app.extensions.get("almacen")
    if clave and almacen is not None:
        return almacen.url(clave)
    return foto_de(getattr(entidad, "slug", ""))


def nombre_actual(slug: str) -> str:
    """Fichero de `static/img` que corresponde a un slug, para el script de migración."""
    return FOTO_OBRA.get(slug) or FOTO_TALLER.get(slug) or ""
