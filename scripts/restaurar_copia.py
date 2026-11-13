"""Restaura una copia de R2 en una base de datos.

Sirve para la prueba mensual de restauración y para una emergencia. Nunca toca
producción por su cuenta: el destino es lo que se pase en `--destino`, y si no se
pasa, se usa `DATABASE_URL` del entorno con un aviso por pantalla.

    R2_...=... BACKUP_PASSPHRASE=... \
        python scripts/restaurar_copia.py --listar
    R2_...=... BACKUP_PASSPHRASE=... \
        python scripts/restaurar_copia.py copias/cosknot-20261113-030000.dump.enc \
            --destino "postgresql://localhost/cosknot_prueba"

El descifrado y el `pg_restore` se hacen con las herramientas del sistema, igual
que en `docs/backups.md`: si `openssl` o `pg_restore` no están en el PATH, el
script falla diciéndolo.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from copias import PREFIJO, cliente_r2, config_de_entorno  # noqa: E402


def _exigir(programa: str) -> str:
    ruta = shutil.which(programa)
    if not ruta:
        raise SystemExit(f"falta {programa} en el PATH")
    return ruta


def listar(cliente, bucket: str, prefijo: str = PREFIJO) -> list[tuple[str, int]]:
    """Copias disponibles, de la más nueva a la más vieja."""
    objetos: list[tuple[str, int]] = []
    paginador = cliente.get_paginator("list_objects_v2")
    for pagina in paginador.paginate(Bucket=bucket, Prefix=prefijo):
        for objeto in pagina.get("Contents", []):
            objetos.append((objeto["Key"], int(objeto.get("Size") or 0)))
    objetos.sort(key=lambda par: par[0], reverse=True)
    return objetos


def restaurar(
    cliente,
    bucket: str,
    clave: str,
    destino: str,
    passphrase: str,
    directorio: Path | None = None,
) -> None:
    """Baja, descifra y restaura. Falla en el primer paso que no cuadre."""
    if not passphrase:
        raise SystemExit("falta BACKUP_PASSPHRASE")
    openssl = _exigir("openssl")
    pg_restore = _exigir("pg_restore")

    with tempfile.TemporaryDirectory(dir=directorio) as temporal:
        cifrado = Path(temporal) / "copia.dump.enc"
        plano = Path(temporal) / "copia.dump"
        print(f"bajando {clave}")
        cliente.download_file(bucket, clave, str(cifrado))

        print("descifrando")
        subprocess.run(
            [
                openssl,
                "enc",
                "-d",
                "-aes-256-cbc",
                "-pbkdf2",
                "-in",
                str(cifrado),
                "-out",
                str(plano),
                "-pass",
                "env:BACKUP_PASSPHRASE",
            ],
            check=True,
            env={**os.environ, "BACKUP_PASSPHRASE": passphrase},
        )

        if plano.open("rb").read(5) != b"PGDMP":
            raise SystemExit("el fichero descifrado no es un dump de PostgreSQL")

        print(f"restaurando en {destino.split('@')[-1]}")
        subprocess.run(
            [
                pg_restore,
                "--clean",
                "--no-owner",
                "--no-privileges",
                "--if-exists",
                "-d",
                destino,
                str(plano),
            ],
            check=True,
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="restaura una copia de cosknot")
    parser.add_argument("clave", nargs="?", help="ruta de la copia dentro del bucket")
    parser.add_argument("--listar", action="store_true", help="muestra las copias")
    parser.add_argument("--destino", default=os.environ.get("DATABASE_URL") or "")
    args = parser.parse_args(argv)

    config = config_de_entorno()
    cliente = cliente_r2(config)

    if args.listar or not args.clave:
        for clave, tamano in listar(cliente, config["bucket"]):
            print(f"{clave}  {tamano} bytes")
        if not args.clave:
            return 0

    if not args.destino:
        raise SystemExit("falta --destino o DATABASE_URL")

    passphrase = (os.environ.get("BACKUP_PASSPHRASE") or "").strip()
    restaurar(cliente, config["bucket"], args.clave, args.destino, passphrase)
    print("restauración terminada")
    return 0


if __name__ == "__main__":
    sys.exit(main())
