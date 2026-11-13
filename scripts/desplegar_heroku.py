"""Plan de despliegue en Heroku, en un solo sitio y comprobable.

El despliegue son doce comandos en orden y con dependencias entre ellos: el addon
antes de las config vars, las config vars antes del push, el push antes de sembrar.
Este script arma ese plan a partir del estado real (¿existe la app? ¿existe el
addon?) y lo imprime o lo ejecuta.

    python scripts/desplegar_heroku.py                 # solo enseña el plan
    python scripts/desplegar_heroku.py --ejecutar      # lo ejecuta
    python scripts/desplegar_heroku.py --app cosknot-es --ejecutar

Nada de aquí inventa valores: `SECRET_KEY` se genera con `secrets`, y las claves de
terceros (R2, Resend, Stripe, Gemini) se toman del entorno solo si están puestas. Lo
que no esté, no se configura: la función correspondiente queda desactivada y la web
lo dice, que es el comportamiento documentado.
"""

from __future__ import annotations

import argparse
import os
import secrets
import shutil
import subprocess
import sys

APP_POR_DEFECTO = "cosknot"
DOMINIO_POR_DEFECTO = "cosknot.es"
REGION = "eu"
PLAN_POSTGRES = "heroku-postgresql:essential-0"

# Config vars que siempre van. El valor de cada una está justificado en
# docs/variables-entorno.md; aquí solo se repiten los números del plan.
VARIABLES_BASE = {
    "APP_ENV": "production",
    "PROXY_FIX_X_FOR": "1",
    "PROXY_FIX_X_PROTO": "1",
    "RATELIMIT_STORAGE_URI": "memory://",
    "DB_POOL_SIZE": "3",
    "DB_MAX_OVERFLOW": "2",
    "DB_POOL_RECYCLE": "300",
    "DB_POOL_TIMEOUT": "10",
    "EMAIL_ASYNC": "1",
    "EMAIL_MAX_INTENTOS": "5",
    "GEMINI_TIMEOUT": "20",
}

# Se copian del entorno solo si existen. El orden no importa.
VARIABLES_OPCIONALES = (
    "IMAGE_STORAGE",
    "R2_ENDPOINT_URL",
    "R2_BUCKET",
    "R2_ACCESS_KEY_ID",
    "R2_SECRET_ACCESS_KEY",
    "R2_PUBLIC_BASE_URL",
    "RESEND_API_KEY",
    "EMAIL_FROM",
    "EMAIL_REPLY_TO",
    "STRIPE_SECRET_KEY",
    "STRIPE_PUBLISHABLE_KEY",
    "STRIPE_WEBHOOK_SECRET",
    "COMMISSION_PERCENT",
    "GEMINI_API_KEY",
    "GEMINI_MODEL",
    "SENTRY_DSN",
    "SENTRY_ENVIRONMENT",
    "SENTRY_TRACES_SAMPLE_RATE",
    "LOG_LEVEL",
)

# Secretos del repositorio que usan los flujos de copia y salud.
SECRETOS_GITHUB = (
    "HEROKU_APP_NAME",
    "BACKUP_PASSPHRASE",
    "R2_ENDPOINT_URL",
    "R2_BUCKET",
    "R2_ACCESS_KEY_ID",
    "R2_SECRET_ACCESS_KEY",
)


def generar_secret_key() -> str:
    """64 caracteres hex, la misma receta que sugiere `.env.example`."""
    return secrets.token_hex(32)


def variables_del_entorno(entorno: dict[str, str] | None = None) -> dict[str, str]:
    """Las opcionales presentes de verdad, sin arrastrar cadenas vacías."""
    datos = entorno if entorno is not None else os.environ
    return {
        nombre: datos[nombre].strip()
        for nombre in VARIABLES_OPCIONALES
        if (datos.get(nombre) or "").strip()
    }


def plan(
    app: str = APP_POR_DEFECTO,
    dominio: str = DOMINIO_POR_DEFECTO,
    existe_app: bool = False,
    existe_addon: bool = False,
    secret_key: str | None = None,
    opcionales: dict[str, str] | None = None,
    sembrar: bool = True,
) -> list[list[str]]:
    """Comandos en orden. Idempotente: lo que ya existe no se repite."""
    comandos: list[list[str]] = []

    if not existe_app:
        comandos.append(["heroku", "create", app, "--region", REGION])
    if not existe_addon:
        comandos.append(
            [
                "heroku",
                "addons:create",
                PLAN_POSTGRES,
                "--app",
                app,
                "--wait",
            ]
        )

    variables = dict(VARIABLES_BASE)
    variables["SECRET_KEY"] = secret_key or generar_secret_key()
    variables.update(opcionales or {})

    comandos.append(
        ["heroku", "config:set", "--app", app]
        + [f"{nombre}={valor}" for nombre, valor in variables.items()]
    )

    comandos.append(["heroku", "domains:add", dominio, "--app", app])
    if not dominio.startswith("www."):
        comandos.append(["heroku", "domains:add", f"www.{dominio}", "--app", app])
    comandos.append(["heroku", "certs:auto:enable", "--app", app])

    comandos.append(["git", "push", "heroku", "main"])
    if sembrar:
        comandos.append(["heroku", "run", "flask", "sembrar", "--app", app])

    return comandos


def plan_secretos_github(
    app: str, entorno: dict[str, str] | None = None
) -> list[list[str]]:
    """`gh secret set` solo para los valores que estén en el entorno.

    La API key de Heroku no se toca: la usa `gh` desde el entorno del flujo, y aquí
    no se copia ningún token de Heroku al repositorio.
    """
    datos = entorno if entorno is not None else os.environ
    comandos: list[list[str]] = []
    for nombre in SECRETOS_GITHUB:
        valor = (datos.get(nombre) or "").strip()
        if nombre == "HEROKU_APP_NAME":
            valor = valor or app
        if not valor:
            continue
        comandos.append(["gh", "secret", "set", nombre, "--body", valor])
    return comandos


def formatear(comandos: list[list[str]], ocultar: tuple[str, ...] = ()) -> list[str]:
    """Imprime el plan con los valores sensibles recortados."""
    lineas: list[str] = []
    for comando in comandos:
        partes: list[str] = []
        for indice, parte in enumerate(comando):
            if any(parte.startswith(f"{clave}=") for clave in ocultar):
                clave, _, valor = parte.partition("=")
                partes.append(f"{clave}={valor[:4]}...({len(valor)} caracteres)")
            elif comando[:3] == ["gh", "secret", "set"] and indice == 5:
                # gh secret set NOMBRE --body VALOR: solo se tapa el valor
                partes.append("<oculto>")
            else:
                partes.append(parte)
        lineas.append(" ".join(partes))
    return lineas


def resolver(comando: list[str]) -> list[str]:
    """Cambia el nombre del programa por su ruta real.

    En Windows `heroku` es un `.cmd` y `subprocess` no resuelve PATHEXT, así que sin
    esto el proceso no arranca aunque el comando funcione en la consola.
    """
    ruta = shutil.which(comando[0])
    if ruta is None:
        raise FileNotFoundError(comando[0])
    return [ruta, *comando[1:]]


def ejecutar(comandos: list[list[str]]) -> int:
    """Ejecuta en orden y para en el primer fallo, con el comando a la vista."""
    for comando in comandos:
        print(f"\n$ {' '.join(comando)}", flush=True)
        try:
            resultado = subprocess.run(resolver(comando), check=False)
        except FileNotFoundError:
            print(f"falta el programa {comando[0]} en el PATH", file=sys.stderr)
            return 127
        if resultado.returncode != 0:
            print(
                f"falló con código {resultado.returncode}: {' '.join(comando)}",
                file=sys.stderr,
            )
            return resultado.returncode
    return 0


def _salida(comando: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        resolver(comando), capture_output=True, text=True, check=False
    )


def existe_app(app: str) -> bool:
    if shutil.which("heroku") is None:
        raise SystemExit("falta la CLI de heroku en el PATH")
    return _salida(["heroku", "apps:info", "--app", app, "--json"]).returncode == 0


def existe_addon(app: str) -> bool:
    resultado = _salida(["heroku", "addons", "--app", app, "--all", "--json"])
    if resultado.returncode != 0:
        return False
    return PLAN_POSTGRES in resultado.stdout or "heroku-postgresql" in resultado.stdout


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="despliegue de cosknot en Heroku")
    parser.add_argument("--app", default=APP_POR_DEFECTO)
    parser.add_argument("--dominio", default=DOMINIO_POR_DEFECTO)
    parser.add_argument("--ejecutar", action="store_true", help="lanza los comandos")
    parser.add_argument(
        "--sin-sembrar", action="store_true", help="no siembra el catálogo de ejemplo"
    )
    args = parser.parse_args(argv)

    ya_existe = existe_app(args.app)
    con_addon = existe_addon(args.app) if ya_existe else False

    comandos = plan(
        app=args.app,
        dominio=args.dominio,
        existe_app=ya_existe,
        existe_addon=con_addon,
        opcionales=variables_del_entorno(),
        sembrar=not args.sin_sembrar,
    )
    secretos = plan_secretos_github(args.app)

    print(f"app: {args.app}   existe: {ya_existe}   addon: {con_addon}")
    print(f"dominio: {args.dominio}")
    print("\n--- heroku ---")
    for linea in formatear(comandos, ocultar=("SECRET_KEY",)):
        print(linea)
    print("\n--- secretos de github ---")
    for linea in formatear(secretos):
        print(linea)

    if not args.ejecutar:
        print("\n(sin --ejecutar: no se ha tocado nada)")
        return 0

    codigo = ejecutar(comandos)
    if codigo != 0:
        return codigo
    return ejecutar(secretos)


if __name__ == "__main__":
    sys.exit(main())
