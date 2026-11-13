"""Lectura de config vars de Heroku por API (copia de seguridad)."""

from __future__ import annotations

import io
import json
import urllib.error

import pytest

from scripts.heroku_config import con_sslmodo, main, pedir_config


class RespuestaFalsa(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
        return False


def abridor(datos: dict) -> object:
    def abrir(peticion, timeout=None):
        assert "api.heroku.com/apps/cosknot/config-vars" in peticion.full_url
        assert peticion.headers["Authorization"] == "Bearer clave"
        return RespuestaFalsa(json.dumps(datos).encode("utf-8"))

    return abrir


def test_lee_las_config_vars(monkeypatch):
    monkeypatch.setenv("HEROKU_API_KEY", "clave")
    config = pedir_config(
        "cosknot", "clave", abrir=abridor({"DATABASE_URL": "postgres://u:p@h/db"})
    )
    assert config["DATABASE_URL"] == "postgres://u:p@h/db"


def test_sin_app_o_sin_clave_falla_claro():
    with pytest.raises(SystemExit) as error:
        pedir_config("", "clave")
    assert "app" in str(error.value)
    with pytest.raises(SystemExit) as error:
        pedir_config("cosknot", "  ")
    assert "HEROKU_API_KEY" in str(error.value)


def test_un_404_del_api_se_explica():
    def abrir(peticion, timeout=None):
        raise urllib.error.HTTPError(
            peticion.full_url, 404, "Not Found", {}, io.BytesIO(b'{"id":"not_found"}')
        )

    with pytest.raises(SystemExit) as error:
        pedir_config("no-existe", "clave", abrir=abrir)
    assert "404" in str(error.value)


def test_sslmode_se_anade_una_sola_vez():
    assert con_sslmodo("postgres://u:p@h/db") == "postgres://u:p@h/db?sslmode=require"
    assert (
        con_sslmodo("postgres://u:p@h/db?application_name=x")
        == "postgres://u:p@h/db?application_name=x&sslmode=require"
    )
    ya = "postgres://u:p@h/db?sslmode=require"
    assert con_sslmodo(ya) == ya


def test_sin_url_no_se_inventa_nada():
    with pytest.raises(SystemExit):
        con_sslmodo("")


def test_main_imprime_el_valor_y_no_los_nombres(monkeypatch, capsys):
    monkeypatch.setenv("HEROKU_API_KEY", "clave")
    monkeypatch.setattr("scripts.heroku_config.pedir_config", lambda app, key: {
        "DATABASE_URL": "postgres://u:p@h/db",
        "SECRET_KEY": "no se imprime",
    })
    assert main(["cosknot", "database_url"]) == 0
    salida = capsys.readouterr().out.strip()
    assert salida == "postgres://u:p@h/db?sslmode=require"
    assert "no se imprime" not in salida


def test_main_lista_nombres_con_todas(monkeypatch, capsys):
    monkeypatch.setattr(
        "scripts.heroku_config.pedir_config",
        lambda app, key: {"SECRET_KEY": "x", "DATABASE_URL": "y"},
    )
    assert main(["cosknot", "--todas"]) == 0
    assert capsys.readouterr().out.split() == ["DATABASE_URL", "SECRET_KEY"]
