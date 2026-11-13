"""Comprobación de arranque en local con SQLite y sin ninguna clave.

Falla si la app no levanta, si /healthz no responde ok o si algún servicio externo
queda activo sin clave. Se ejecuta a mano; no forma parte de pytest.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

VARIABLES = (
    "DATABASE_URL",
    "SECRET_KEY",
    "APP_ENV",
    "DYNO",
    "RESEND_API_KEY",
    "EMAIL_FROM",
    "IMAGE_STORAGE",
    "R2_ENDPOINT_URL",
    "R2_BUCKET",
    "R2_ACCESS_KEY_ID",
    "R2_SECRET_ACCESS_KEY",
    "R2_PUBLIC_BASE_URL",
    "STRIPE_SECRET_KEY",
    "STRIPE_PUBLISHABLE_KEY",
    "STRIPE_WEBHOOK_SECRET",
    "COMMISSION_PERCENT",
    "GEMINI_API_KEY",
    "GEMINI_MODEL",
    "SENTRY_DSN",
    "RATELIMIT_STORAGE_URI",
    "EMAIL_ASYNC",
    "EMAIL_MAX_INTENTOS",
    "PROXY_FIX_X_FOR",
    "PROXY_FIX_X_PROTO",
    "DB_POOL_SIZE",
    "DB_MAX_OVERFLOW",
    "SEED_ON_START",
)

for nombre in VARIABLES:
    os.environ.pop(nombre, None)

temporal = Path(tempfile.mkdtemp())
os.environ["DATABASE_URL"] = f"sqlite:///{(temporal / 'local.db').as_posix()}"
os.environ["UPLOAD_DIR"] = (temporal / "uploads").as_posix()

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app as modulo  # noqa: E402

aplicacion = modulo.app
cliente = aplicacion.test_client()

salud = cliente.get("/healthz")
print("healthz:", salud.status_code, salud.get_json())
print("portada:", cliente.get("/").status_code)
print("buscador:", cliente.get("/buscar?q=capa").status_code)

correo = aplicacion.extensions["correo"]
almacen = aplicacion.extensions.get("almacen")
sugeridor = aplicacion.extensions["sugeridor"]
print("correo:", correo.nombre, "activo:", correo.activo)
print("almacen:", "activo" if almacen else "desactivado")
print("sugerencias:", sugeridor.nombre, "activo:", sugeridor.activo)
print("cobro desactivado por:", modulo.motivo_desactivado(aplicacion.config))
print("produccion:", modulo.es_produccion())
print("limite:", aplicacion.config["RATELIMIT_STORAGE_URI"])

with aplicacion.extensions["db_session"]() as sesion:
    from sqlalchemy import func, select

    from models import Creator, Work

    print(
        "catalogo:",
        "creadores", sesion.scalar(select(func.count()).select_from(Creator)),
        "obras", sesion.scalar(select(func.count()).select_from(Work)),
    )

assert salud.status_code == 200, "healthz no responde 200"
assert correo.activo is True, "sin RESEND_API_KEY debería usar la consola en local"
assert sugeridor.activo is False, "sin GEMINI_API_KEY no debe haber sugerencias"
assert almacen is not None, "en local debería haber almacén de disco"
assert modulo.es_produccion() is False, "sin APP_ENV ni DYNO no es producción"
print("OK: arranca en local con SQLite y sin claves")
sys.exit(0)
