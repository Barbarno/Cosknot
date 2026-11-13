"""Almacenamiento de imágenes.

Dos backends con la misma interfaz:

- `AlmacenLocal`: escribe en `static/uploads/`. Solo vale en desarrollo, porque el
  disco de Render es efímero y se borra en cada despliegue.
- `AlmacenR2`: habla con Cloudflare R2 por la API compatible con S3 (boto3).

`crear_almacen()` decide cuál toca. Si en producción faltan las claves de R2, no
rompe la aplicación: devuelve `None` y la web avisa de que las subidas están
desactivadas.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

EXTENSIONES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}

MAX_BYTES_POR_DEFECTO = 5 * 1024 * 1024


class ErrorImagen(ValueError):
    """La imagen no pasa la validación."""


def _firma_valida(datos: bytes, extension: str) -> bool:
    if extension in (".jpg", ".jpeg"):
        return datos.startswith(b"\xff\xd8\xff")
    if extension == ".png":
        return datos.startswith(b"\x89PNG\r\n\x1a\n")
    if extension == ".webp":
        return len(datos) > 12 and datos[:4] == b"RIFF" and datos[8:12] == b"WEBP"
    return False


def validar_imagen(
    nombre_original: str, content_type: str | None, datos: bytes, max_bytes: int
) -> str:
    """Valida extensión, tipo y tamaño. Devuelve la extensión normalizada."""
    extension = Path(nombre_original or "").suffix.lower()
    if extension not in EXTENSIONES:
        raise ErrorImagen("formato no admitido: usa jpg, png o webp")
    tipo = (content_type or "").split(";")[0].strip().lower()
    if tipo not in set(EXTENSIONES.values()):
        raise ErrorImagen("el tipo del archivo no es una imagen admitida")
    if EXTENSIONES[extension] != tipo:
        raise ErrorImagen("la extensión no coincide con el tipo real del archivo")
    if not datos:
        raise ErrorImagen("el archivo está vacío")
    if len(datos) > max_bytes:
        raise ErrorImagen(
            f"la imagen pasa de {max_bytes // (1024 * 1024)} MB"
        )
    if not _firma_valida(datos, extension):
        raise ErrorImagen("el contenido no es una imagen válida")
    return extension


def clave_nueva(extension: str) -> str:
    return f"obras/{uuid.uuid4().hex}{extension}"


class Almacen:
    nombre = "base"

    def guardar(self, clave: str, datos: bytes, content_type: str) -> str:
        raise NotImplementedError

    def url(self, clave: str) -> str:
        raise NotImplementedError

    def borrar(self, clave: str) -> None:
        raise NotImplementedError


class AlmacenLocal(Almacen):
    """Disco local, solo para desarrollo."""

    nombre = "local"

    def __init__(self, raiz: Path, url_base: str = "/static/uploads") -> None:
        self.raiz = raiz
        self.url_base = url_base.rstrip("/")

    def _ruta(self, clave: str) -> Path:
        destino = (self.raiz / clave).resolve()
        if self.raiz.resolve() not in destino.parents:
            raise ErrorImagen("ruta de imagen fuera del directorio permitido")
        return destino

    def guardar(self, clave: str, datos: bytes, content_type: str) -> str:
        destino = self._ruta(clave)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(datos)
        return clave

    def url(self, clave: str) -> str:
        return f"{self.url_base}/{clave}"

    def borrar(self, clave: str) -> None:
        try:
            self._ruta(clave).unlink(missing_ok=True)
        except OSError:
            pass


class AlmacenR2(Almacen):
    """Cloudflare R2 por la API compatible con S3."""

    nombre = "r2"

    def __init__(
        self,
        bucket: str,
        endpoint_url: str,
        access_key_id: str,
        secret_access_key: str,
        url_publica: str,
        cliente: Any | None = None,
    ) -> None:
        self.bucket = bucket
        self.url_publica = url_publica.rstrip("/")
        if cliente is not None:
            self.cliente = cliente
        else:
            import boto3

            self.cliente = boto3.client(
                "s3",
                endpoint_url=endpoint_url,
                region_name="auto",
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key,
            )

    def guardar(self, clave: str, datos: bytes, content_type: str) -> str:
        self.cliente.put_object(
            Bucket=self.bucket,
            Key=clave,
            Body=datos,
            ContentType=content_type,
            CacheControl="public, max-age=31536000, immutable",
        )
        return clave

    def url(self, clave: str) -> str:
        return f"{self.url_publica}/{clave}"

    def borrar(self, clave: str) -> None:
        self.cliente.delete_object(Bucket=self.bucket, Key=clave)


def origen_de(url: str) -> str:
    partes = urlparse(url)
    if not partes.scheme or not partes.netloc:
        return ""
    return f"{partes.scheme}://{partes.netloc}"


def crear_almacen(config: dict[str, Any], produccion: bool) -> tuple[Almacen | None, str]:
    """Devuelve el almacén y el motivo si está desactivado."""
    bucket = config.get("R2_BUCKET")
    endpoint = config.get("R2_ENDPOINT_URL")
    clave_id = config.get("R2_ACCESS_KEY_ID")
    secreto = config.get("R2_SECRET_ACCESS_KEY")
    url_publica = config.get("R2_PUBLIC_BASE_URL")

    modo = (config.get("IMAGE_STORAGE") or "").strip().lower()

    if modo == "r2" or (bucket and endpoint and clave_id and secreto and url_publica):
        faltan = [
            nombre
            for nombre, valor in (
                ("R2_BUCKET", bucket),
                ("R2_ENDPOINT_URL", endpoint),
                ("R2_ACCESS_KEY_ID", clave_id),
                ("R2_SECRET_ACCESS_KEY", secreto),
                ("R2_PUBLIC_BASE_URL", url_publica),
            )
            if not valor
        ]
        if faltan:
            return None, "faltan variables de R2: " + ", ".join(faltan)
        return (
            AlmacenR2(
                bucket=bucket,
                endpoint_url=endpoint,
                access_key_id=clave_id,
                secret_access_key=secreto,
                url_publica=url_publica,
            ),
            "",
        )

    if modo == "r2":
        return None, "IMAGE_STORAGE=r2 pero faltan las variables de R2"

    if produccion:
        # En Render el disco es efímero: subir ahí sería perder la foto en el
        # siguiente despliegue. Mejor desactivar la subida con un mensaje.
        return None, "las subidas están desactivadas: configura R2_* para activarlas"

    raiz = Path(config.get("UPLOAD_DIR") or "static/uploads")
    return AlmacenLocal(raiz), ""
