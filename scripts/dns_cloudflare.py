"""Crea registros DNS en Cloudflare desde una lista, de forma idempotente.

Se usa para el correo de Resend y para el `CNAME` de Heroku: los valores se pasan en
un fichero JSON y el script comprueba qué existe ya antes de crear nada.

    python scripts/dns_cloudflare.py cosknot.me registros.json            # plan
    python scripts/dns_cloudflare.py cosknot.me registros.json --ejecutar

Formato del fichero (una lista de objetos):

    [
      {"type": "TXT",   "name": "resend._domainkey", "content": "p=MIGf..."},
      {"type": "CNAME", "name": "rsend",             "content": "rsend-eu..."},
      {"type": "CNAME", "name": "@",                 "content": "app.herokuapp.com"}
    ]

`name` va sin el dominio; `@` es el raíz. Todos se crean en **DNS only** (sin proxy):
los de correo no pueden ir proxied, y el del raíz tampoco mientras el certificado de
Heroku se valida por HTTP-01. Ver `docs/deployment.md` para el porqué.

El token de Cloudflare se lee de `CLOUDFLARE_API_TOKEN` y necesita dos permisos:
`Zone: Read` (para sacar el id de la zona) y `DNS: Edit` (para crearlos).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any

API = "https://api.cloudflare.com/client/v4"
TIPOS = {"A", "AAAA", "CNAME", "TXT", "MX", "NS"}


class ErrorCloudflare(Exception):
    """Fallo con el motivo que devuelve la API, no un mensaje genérico."""


def _peticion(
    metodo: str, ruta: str, token: str, abrir=None, cuerpo: dict | None = None
) -> dict[str, Any]:
    if not token.strip():
        raise ErrorCloudflare("falta CLOUDFLARE_API_TOKEN")
    datos = json.dumps(cuerpo).encode("utf-8") if cuerpo is not None else None
    peticion = urllib.request.Request(
        f"{API}{ruta}",
        method=metodo,
        data=datos,
        headers={
            "Authorization": f"Bearer {token.strip()}",
            "Content-Type": "application/json",
        },
    )
    abrir = abrir or urllib.request.urlopen
    try:
        with abrir(peticion, timeout=30) as respuesta:
            cargado = json.loads(respuesta.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        crudo = error.read().decode("utf-8", "replace")
        try:
            detalle = json.loads(crudo).get("errors") or crudo[:200]
        except json.JSONDecodeError:
            detalle = crudo[:200]
        raise ErrorCloudflare(f"{metodo} {ruta} → {error.code}: {detalle}") from error
    except urllib.error.URLError as error:
        raise ErrorCloudflare(f"sin red: {error.reason}") from error

    if not cargado.get("success", False):
        raise ErrorCloudflare(str(cargado.get("errors") or "respuesta sin success"))
    return cargado


def zona_id(nombre: str, token: str, abrir=None) -> str:
    """Identificador interno de la zona. Falla claro si el token no la ve."""
    respuesta = _peticion("GET", f"/zones?name={nombre}", token, abrir=abrir)
    zonas = respuesta.get("result") or []
    if not zonas:
        raise ErrorCloudflare(
            f"el token no ve la zona {nombre}: revisa que incluya Zone:Read"
        )
    return zonas[0]["id"]


def registros_existentes(ident: str, token: str, abrir=None) -> list[dict[str, Any]]:
    respuesta = _peticion(
        "GET", f"/zones/{ident}/dns_records?per_page=100", token, abrir=abrir
    )
    return list(respuesta.get("result") or [])


def normalizar(nombre: str, dominio: str) -> str:
    """`@` y el nombre suelto se guardan como FQDN, que es lo que compara Cloudflare."""
    limpio = nombre.strip().rstrip(".")
    if limpio in ("", "@"):
        return dominio
    if limpio.endswith(dominio):
        return limpio
    return f"{limpio}.{dominio}"


def leer_fichero(ruta: str) -> list[dict[str, Any]]:
    with open(ruta, encoding="utf-8") as manejador:
        datos = json.load(manejador)
    if not isinstance(datos, list):
        raise ErrorCloudflare("el fichero tiene que ser una lista de registros")
    registros: list[dict[str, Any]] = []
    for posicion, bruto in enumerate(datos, start=1):
        if not isinstance(bruto, dict):
            raise ErrorCloudflare(f"el registro {posicion} no es un objeto")
        tipo = str(bruto.get("type", "")).strip().upper()
        if tipo not in TIPOS:
            raise ErrorCloudflare(f"el registro {posicion} tiene un tipo no soportado: {tipo}")
        nombre = str(bruto.get("name", "")).strip()
        contenido = str(bruto.get("content", "")).strip()
        if not contenido:
            raise ErrorCloudflare(f"el registro {posicion} no tiene content")
        registros.append(
            {
                "type": tipo,
                "name": nombre,
                "content": contenido,
                "ttl": int(bruto.get("ttl") or 1),
                # Nunca proxied: los de correo no pueden, y el del raíz rompe el ACM.
                "proxied": False,
            }
        )
    return registros


def plan(
    deseados: list[dict[str, Any]],
    existentes: list[dict[str, Any]],
    dominio: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Separa lo que hay que crear de lo que ya está igual."""
    crear: list[dict[str, Any]] = []
    omitir: list[dict[str, Any]] = []
    for registro in deseados:
        fqdn = normalizar(registro["name"], dominio)
        igual = next(
            (
                previo
                for previo in existentes
                if previo.get("type") == registro["type"]
                and previo.get("name", "").rstrip(".") == fqdn
                and str(previo.get("content", "")).strip() == registro["content"]
            ),
            None,
        )
        if igual is not None:
            omitir.append(registro)
        else:
            crear.append({**registro, "name": fqdn})
    return crear, omitir


def crear(ident: str, token: str, registro: dict[str, Any], abrir=None) -> str:
    respuesta = _peticion(
        "POST", f"/zones/{ident}/dns_records", token, abrir=abrir, cuerpo=registro
    )
    return str((respuesta.get("result") or {}).get("id", ""))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="registros DNS de cosknot en Cloudflare")
    parser.add_argument("dominio")
    parser.add_argument("fichero", help="JSON con la lista de registros")
    parser.add_argument("--ejecutar", action="store_true", help="crea de verdad")
    args = parser.parse_args(argv)

    token = os.environ.get("CLOUDFLARE_API_TOKEN") or ""
    try:
        deseados = leer_fichero(args.fichero)
        ident = zona_id(args.dominio, token)
        existentes = registros_existentes(ident, token)
        crear_ahora, omitir = plan(deseados, existentes, args.dominio)
    except ErrorCloudflare as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print(f"zona {args.dominio} ({ident})")
    print(f"ya estaban: {len(omitir)}")
    print(f"por crear:  {len(crear_ahora)}")
    for registro in crear_ahora:
        print(f"  {registro['type']:6} {registro['name']:40} {registro['content'][:50]}")

    if not args.ejecutar:
        print("\n(sin --ejecutar: no se ha creado nada)")
        return 0

    for registro in crear_ahora:
        try:
            nuevo = crear(ident, token, registro)
        except ErrorCloudflare as error:
            print(f"error creando {registro['name']}: {error}", file=sys.stderr)
            return 1
        print(f"creado {registro['type']} {registro['name']} → {nuevo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
