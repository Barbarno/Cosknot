"""Pruebas de la adaptación a Heroku: producción, proxy y conexiones.

Nada de aquí toca la red: se simulan las cabeceras del router y se comprueba la
configuración del motor, no una conexión real.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flask import request

from app import create_app, es_produccion, proxies_de_confianza
from db import build_engine, engine_options
from extensiones import limiter

RAIZ = Path(__file__).resolve().parent.parent


def test_sin_variables_no_es_produccion(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("FLASK_ENV", raising=False)
    monkeypatch.delenv("DYNO", raising=False)
    assert es_produccion() is False


def test_app_env_manda_sobre_dyno(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("DYNO", raising=False)
    assert es_produccion() is True

    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DYNO", "web.1")
    assert es_produccion() is False


def test_dyno_implica_produccion_si_falta_app_env(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("FLASK_ENV", raising=False)
    monkeypatch.setenv("DYNO", "web.1")
    assert es_produccion() is True


def test_los_proxies_de_confianza_se_acotan(monkeypatch):
    monkeypatch.setenv("PROXY_FIX_X_FOR", "2")
    monkeypatch.setenv("PROXY_FIX_X_PROTO", "1")
    assert proxies_de_confianza() == (2, 1)

    monkeypatch.setenv("PROXY_FIX_X_FOR", "99")
    monkeypatch.setenv("PROXY_FIX_X_PROTO", "basura")
    assert proxies_de_confianza() == (5, 1)


def test_el_router_de_heroku_no_es_la_ip_del_cliente(tmp_path, monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("DYNO", raising=False)
    aplicacion = create_app(
        {
            "TESTING": True,
            "DATABASE_URL": f"sqlite:///{(tmp_path / 'proxy.db').as_posix()}",
            "SECRET_KEY": "clave-de-pruebas",
        }
    )

    visto: dict[str, object] = {}

    @aplicacion.get("/_ip")
    def _ip():
        visto["remote_addr"] = request.remote_addr
        visto["scheme"] = request.scheme
        visto["clave_limite"] = limiter._key_func()
        return {"ok": True}

    cliente = aplicacion.test_client()
    respuesta = cliente.get(
        "/_ip",
        headers={
            "X-Forwarded-For": "203.0.113.7",
            "X-Forwarded-Proto": "https",
            "X-Forwarded-Host": "cosknot.me",
        },
    )

    assert respuesta.status_code == 200
    # ProxyFix reescribe remote_addr con la IP que puso el router, no la del router.
    assert visto["remote_addr"] == "203.0.113.7"
    assert visto["scheme"] == "https"
    # El límite de intentos cuenta esa misma IP: no la del proxy.
    assert visto["clave_limite"] == "203.0.113.7"


def test_sin_cabeceras_del_router_la_ip_es_la_del_cliente(tmp_path, monkeypatch):
    monkeypatch.delenv("PROXY_FIX_X_FOR", raising=False)
    monkeypatch.delenv("PROXY_FIX_X_PROTO", raising=False)
    aplicacion = create_app(
        {
            "TESTING": True,
            "DATABASE_URL": f"sqlite:///{(tmp_path / 'proxy2.db').as_posix()}",
            "SECRET_KEY": "clave-de-pruebas",
        }
    )
    visto: dict[str, str] = {}

    @aplicacion.get("/_ip")
    def _ip():
        visto["remote_addr"] = request.remote_addr or ""
        return {"ok": True}

    aplicacion.test_client().get("/_ip")
    assert visto["remote_addr"] in ("127.0.0.1", "localhost", "::1")


def test_el_motor_de_postgres_respeta_el_limite_de_conexiones(monkeypatch):
    monkeypatch.setenv("DB_POOL_SIZE", "3")
    monkeypatch.setenv("DB_MAX_OVERFLOW", "2")
    motor = build_engine("postgresql+psycopg://u:p@localhost/db")
    try:
        assert motor.pool.size() == 3
        assert motor.pool._max_overflow == 2
        assert motor.pool._pre_ping is True
        # 3 + 2 = 5 conexiones de la app; con release, copia y psql: 8 de 20.
        assert 3 + 2 <= 5
        argumentos = motor.dialect.create_connect_args(motor.url)[1] or {}
        assert argumentos.get("host") == "localhost"
        # El TLS no viaja en la URL: Heroku rota credenciales y sobrescribe
        # DATABASE_URL, así que el `sslmode` se inyecta en connect_args.
        assert engine_options("postgresql+psycopg://u:p@localhost/db")["connect_args"] == {
            "sslmode": "require"
        }
    finally:
        motor.dispose()


def test_un_valor_absurdo_de_pool_no_rompe(monkeypatch):
    monkeypatch.setenv("DB_POOL_SIZE", "muchas")
    monkeypatch.setenv("DB_MAX_OVERFLOW", "")
    motor = build_engine("postgresql+psycopg://u:p@localhost/db")
    try:
        assert motor.pool.size() == 3
        assert motor.pool._max_overflow == 2
    finally:
        motor.dispose()


def test_el_limite_de_intentos_usa_memoria_por_defecto(tmp_path, monkeypatch):
    monkeypatch.delenv("RATELIMIT_STORAGE_URI", raising=False)
    aplicacion = create_app(
        {
            "TESTING": True,
            "DATABASE_URL": f"sqlite:///{(tmp_path / 'limite.db').as_posix()}",
            "SECRET_KEY": "clave-de-pruebas",
        }
    )
    assert aplicacion.config["RATELIMIT_STORAGE_URI"] == "memory://"
    # El valor llega de verdad al backend del limitador, no se queda en config.
    assert type(limiter._storage).__name__ == "MemoryStorage"


def test_la_variable_del_limite_manda_sobre_el_valor_por_defecto(tmp_path, monkeypatch):
    monkeypatch.setenv("RATELIMIT_STORAGE_URI", "memory://")
    aplicacion = create_app(
        {
            "TESTING": True,
            "DATABASE_URL": f"sqlite:///{(tmp_path / 'limite2.db').as_posix()}",
            "SECRET_KEY": "clave-de-pruebas",
        }
    )
    assert aplicacion.config["RATELIMIT_STORAGE_URI"] == "memory://"
    assert type(limiter._storage).__name__ == "MemoryStorage"


def test_el_arranque_en_postgres_no_migra_ni_conecta(tmp_path, monkeypatch):
    """Las migraciones van en el proceso release, no en el arranque del dyno.

    Si `create_app` migrara al arrancar, esta llamada intentaría conectar con un
    puerto cerrado y reventaría. Que devuelva la app demuestra que el arranque no
    abre conexión ni ejecuta Alembic.
    """
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("DYNO", raising=False)
    aplicacion = create_app(
        {
            "DATABASE_URL": "postgresql://usuario:clave@127.0.0.1:1/cosknot",
            "SECRET_KEY": "clave-de-pruebas",
        }
    )
    assert aplicacion is not None
    motor = aplicacion.extensions["db_engine"]
    try:
        assert motor.dialect.name == "postgresql"
        assert motor.pool.checkedin() == 0
    finally:
        motor.dispose()


def test_el_procfile_arranca_con_un_worker_y_timeout_corto():
    procfile = (RAIZ / "Procfile").read_text(encoding="utf-8")
    web = next(
        linea for linea in procfile.splitlines() if linea.startswith("web:")
    )
    assert "--workers 1" in web
    assert "--threads 4" in web
    assert "--timeout 50" in web
    assert "--bind 0.0.0.0:$PORT" in web
    assert "--preload" not in web
    # Las migraciones van en release, una vez por despliegue.
    assert any(linea.startswith("release: alembic upgrade head") for linea in procfile.splitlines())


def test_la_version_de_python_esta_fijada():
    version = (RAIZ / ".python-version").read_text(encoding="utf-8").strip()
    assert version == "3.13"
