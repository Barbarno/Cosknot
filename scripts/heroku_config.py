"""Lee `DATABASE_URL` de una app de Heroku por su API.

Se usa en `backup.yml` para no guardar la cadena de la base en GitHub: el flujo pide
la config var en tiempo de ejecución y Heroku puede rotar las credenciales sin que
nada del repositorio se entere.

No hace falta la CLI de Heroku: es un `GET` a la API de la plataforma con la clave
de cuenta (`HEROKU_API_KEY`). Así el runner solo necesita Python y `curl` no entra
en juego.

    HEROKU_API_KEY=... python scripts/heroku_config.py cosknot database_url
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.heroku.com"
CABECERAS = {
    "Accept": "application/vnd.heroku+json; version=3",
    "Content-Type": "application/json",
}


def pedir_config(app: str, api_key: str, abrir=None) -> dict[str, str]:
    """Devuelve todas las config vars de la app. Falla con el motivo del API."""
    if not app.strip():
        raise SystemExit("falta el nombre de la app")
    if not api_key.strip():
        raise SystemExit("falta HEROKU_API_KEY")

    abrir = abrir or urllib.request.urlopen
    peticion = urllib.request.Request(
        f"{API}/apps/{app.strip()}/config-vars",
        headers={**CABECERAS, "Authorization": f"Bearer {api_key.strip()}"},
    )
    try:
        with abrir(peticion, timeout=30) as respuesta:
            datos = json.loads(respuesta.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        cuerpo = error.read().decode("utf-8", "replace")[:300]
        raise SystemExit(f"Heroku respondió {error.code} para {app}: {cuerpo}") from error
    except urllib.error.URLError as error:
        raise SystemExit(f"no se pudo hablar con la API de Heroku: {error.reason}") from error

    if not isinstance(datos, dict):
        raise SystemExit("la API no devolvió un objeto de config vars")
    return datos


def con_sslmodo(url: str) -> str:
    """Añade `sslmode=require` si no viene: el addon lo exige y psycopg no lo pone."""
    if not url:
        raise SystemExit("Heroku no devolvió DATABASE_URL")
    if "sslmode=" in url:
        return url
    return url + ("&sslmode=require" if "?" in url else "?sslmode=require")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="config vars de Heroku por API")
    parser.add_argument("app", nargs="?", default=os.environ.get("HEROKU_APP_NAME") or "")
    parser.add_argument(
        "variable", nargs="?", default="database_url", help="en minúsculas o mayúsculas"
    )
    parser.add_argument(
        "--todas", action="store_true", help="imprime los nombres, no los valores"
    )
    args = parser.parse_args(argv)

    config = pedir_config(args.app, os.environ.get("HEROKU_API_KEY") or "")

    if args.todas:
        for nombre in sorted(config):
            print(nombre)
        return 0

    clave = args.variable.strip()
    valor = config.get(clave) or config.get(clave.upper()) or config.get(clave.lower())
    if valor is None:
        raise SystemExit(f"{args.app} no tiene la config var {clave}")
    print(valor if clave.lower() != "database_url" else con_sslmodo(valor))
    return 0


if __name__ == "__main__":
    sys.exit(main())
