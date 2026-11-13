"""Copias de seguridad en Cloudflare R2.

Dos operaciones y ninguna dependencia de Heroku:

- `subir <fichero>`: deja la copia en `copias/cosknot-AAAAMMDD-HHMMSS.dump.enc`.
- `purgar`: borra del bucket las copias con más de 30 días.

La copia llega ya cifrada desde el flujo de trabajo; aquí no se toca el contenido.
Se usa boto3 con `region_name="auto"`, que es lo que espera R2 para la firma.

    R2_ENDPOINT_URL=... R2_BUCKET=... R2_ACCESS_KEY_ID=... R2_SECRET_ACCESS_KEY=... \
        python scripts/copias.py subir copia.dump.enc
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

PREFIJO = "copias/"
DIAS_RETENCION = 30


def config_de_entorno(entorno: dict[str, str] | None = None) -> dict[str, str]:
    """Lee las cuatro variables de R2 y falla nombrando la que falta."""
    datos = entorno if entorno is not None else os.environ
    faltan = [
        nombre
        for nombre in (
            "R2_ENDPOINT_URL",
            "R2_BUCKET",
            "R2_ACCESS_KEY_ID",
            "R2_SECRET_ACCESS_KEY",
        )
        if not (datos.get(nombre) or "").strip()
    ]
    if faltan:
        raise SystemExit("faltan variables de R2: " + ", ".join(faltan))
    return {
        "endpoint_url": datos["R2_ENDPOINT_URL"].strip().rstrip("/"),
        "bucket": datos["R2_BUCKET"].strip(),
        "access_key": datos["R2_ACCESS_KEY_ID"].strip(),
        "secret_key": datos["R2_SECRET_ACCESS_KEY"].strip(),
    }


def cliente_r2(config: dict[str, str], cliente: Any | None = None) -> Any:
    """Cliente de S3 apuntando a R2. `region_name="auto"` es obligatorio."""
    if cliente is not None:
        return cliente
    import boto3

    return boto3.client(
        "s3",
        endpoint_url=config["endpoint_url"],
        region_name="auto",
        aws_access_key_id=config["access_key"],
        aws_secret_access_key=config["secret_key"],
    )


def nombre_de_copia(momento: datetime | None = None) -> str:
    """Ruta dentro del bucket. Se ordena sola por fecha en el nombre."""
    instante = momento or datetime.now(timezone.utc)
    return f"{PREFIJO}cosknot-{instante.strftime('%Y%m%d-%H%M%S')}.dump.enc"


def subir(cliente: Any, bucket: str, ruta: Path, clave: str) -> int:
    """Sube la copia y devuelve el tamaño en bytes."""
    if not ruta.is_file():
        raise SystemExit(f"no existe el fichero {ruta}")
    tamano = ruta.stat().st_size
    if tamano < 1024:
        raise SystemExit(f"la copia ocupa {tamano} bytes: algo falló antes de subirla")
    cliente.upload_file(str(ruta), bucket, clave)
    return tamano


def purgar(
    cliente: Any,
    bucket: str,
    prefijo: str = PREFIJO,
    dias: int = DIAS_RETENCION,
    ahora: datetime | None = None,
) -> list[str]:
    """Borra las copias más viejas que `dias`. Devuelve las claves borradas."""
    limite = (ahora or datetime.now(timezone.utc)) - timedelta(days=dias)
    borradas: list[str] = []
    paginador = cliente.get_paginator("list_objects_v2")
    for pagina in paginador.paginate(Bucket=bucket, Prefix=prefijo):
        for objeto in pagina.get("Contents", []):
            fecha = objeto.get("LastModified")
            if fecha is None:
                continue
            if fecha.tzinfo is None:
                fecha = fecha.replace(tzinfo=timezone.utc)
            if fecha < limite:
                cliente.delete_object(Bucket=bucket, Key=objeto["Key"])
                borradas.append(objeto["Key"])
    return borradas


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="copias de cosknot en R2")
    sub = parser.add_subparsers(dest="orden", required=True)

    subir_parser = sub.add_parser("subir", help="sube una copia ya cifrada")
    subir_parser.add_argument("fichero", type=Path)

    purgar_parser = sub.add_parser("purgar", help="borra copias de más de N días")
    purgar_parser.add_argument("--dias", type=int, default=DIAS_RETENCION)

    args = parser.parse_args(argv)
    config = config_de_entorno()
    cliente = cliente_r2(config)

    if args.orden == "subir":
        clave = nombre_de_copia()
        tamano = subir(cliente, config["bucket"], args.fichero, clave)
        print(f"subida {clave} ({tamano} bytes)")
        return 0

    borradas = purgar(cliente, config["bucket"], dias=args.dias)
    print(f"borradas {len(borradas)} copias de más de {args.dias} días")
    for clave in borradas:
        print(f"  {clave}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
