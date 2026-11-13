from __future__ import annotations

import logging

import sentry_sdk

from app import configurar_registro, configurar_sentry, create_app


def test_el_nivel_de_log_sale_de_la_variable(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    configurar_registro()
    assert logging.getLogger().level == logging.DEBUG

    monkeypatch.setenv("LOG_LEVEL", "warning")
    configurar_registro()
    assert logging.getLogger().level == logging.WARNING

    monkeypatch.setenv("LOG_LEVEL", "no-es-un-nivel")
    configurar_registro()
    assert logging.getLogger().level == logging.INFO

    monkeypatch.delenv("LOG_LEVEL", raising=False)
    configurar_registro()
    assert logging.getLogger().level == logging.INFO


def test_sin_dsn_sentry_no_se_inicializa(monkeypatch, tmp_path):
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    app = create_app(
        {
            "TESTING": True,
            "DATABASE_URL": f"sqlite:///{(tmp_path / 'a.db').as_posix()}",
            "SECRET_KEY": "clave",
            "UPLOAD_DIR": (tmp_path / "uploads").as_posix(),
        }
    )
    assert configurar_sentry(app) is False
    assert "sentry_iniciado" not in app.extensions


def test_en_tests_sentry_no_se_inicializa_aunque_haya_dsn(monkeypatch, tmp_path):
    monkeypatch.setenv("SENTRY_DSN", "https://clave@sentry.example/1")
    app = create_app(
        {
            "TESTING": True,
            "DATABASE_URL": f"sqlite:///{(tmp_path / 'b.db').as_posix()}",
            "SECRET_KEY": "clave",
            "UPLOAD_DIR": (tmp_path / "uploads").as_posix(),
        }
    )
    assert configurar_sentry(app) is False


def test_con_dsn_se_inicializa_una_vez(monkeypatch, tmp_path):
    monkeypatch.setenv("SENTRY_DSN", "https://clave@sentry.example/1")
    monkeypatch.setenv("SENTRY_ENVIRONMENT", "staging")
    monkeypatch.setenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")

    llamadas = []
    monkeypatch.setattr(sentry_sdk, "init", lambda **kw: llamadas.append(kw))

    app = create_app(
        {
            "DATABASE_URL": f"sqlite:///{(tmp_path / 'c.db').as_posix()}",
            "SECRET_KEY": "clave",
            "UPLOAD_DIR": (tmp_path / "uploads").as_posix(),
        }
    )
    assert len(llamadas) == 1
    assert llamadas[0]["dsn"] == "https://clave@sentry.example/1"
    assert llamadas[0]["environment"] == "staging"
    assert llamadas[0]["traces_sample_rate"] == 0.1
    assert llamadas[0]["send_default_pii"] is False
    assert app.extensions["sentry_iniciado"] is True

    # segunda llamada: ya estaba inicializado, no se repite
    assert configurar_sentry(app) is True
    assert len(llamadas) == 1


def test_una_tasa_mal_escrita_cae_en_cero(monkeypatch, tmp_path):
    monkeypatch.setenv("SENTRY_DSN", "https://clave@sentry.example/1")
    monkeypatch.setenv("SENTRY_TRACES_SAMPLE_RATE", "mucho")
    llamadas = []
    monkeypatch.setattr(sentry_sdk, "init", lambda **kw: llamadas.append(kw))

    create_app(
        {
            "DATABASE_URL": f"sqlite:///{(tmp_path / 'd.db').as_posix()}",
            "SECRET_KEY": "clave",
            "UPLOAD_DIR": (tmp_path / "uploads").as_posix(),
        }
    )
    assert llamadas[0]["traces_sample_rate"] == 0.0


def test_healthz_sigue_igual(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "DATABASE_URL": f"sqlite:///{(tmp_path / 'e.db').as_posix()}",
            "SECRET_KEY": "clave",
            "UPLOAD_DIR": (tmp_path / "uploads").as_posix(),
        }
    )
    respuesta = app.test_client().get("/healthz")
    assert respuesta.status_code == 200
    assert respuesta.get_json()["status"] == "ok"
