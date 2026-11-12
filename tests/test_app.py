from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app import build_engine, create_app, normalize_database_url
from models import Creator, Work
from seed import SEED_CREATORS


@pytest.fixture()
def aplicacion(tmp_path):
    ruta_db = tmp_path / "test.db"
    app = create_app(
        {
            "TESTING": True,
            "DATABASE_URL": f"sqlite:///{ruta_db.as_posix()}",
            "SECRET_KEY": "clave-de-pruebas",
        }
    )
    return app


@pytest.fixture()
def cliente(aplicacion):
    return aplicacion.test_client()


def test_normaliza_la_url_de_la_base_de_datos():
    assert normalize_database_url(None) == "sqlite:///cosknot.db"
    assert normalize_database_url("") == "sqlite:///cosknot.db"
    assert normalize_database_url("sqlite:///x.db") == "sqlite:///x.db"
    assert (
        normalize_database_url("postgres://u:p@host/db")
        == "postgresql+psycopg://u:p@host/db"
    )
    assert (
        normalize_database_url("postgresql://u:p@host/db")
        == "postgresql+psycopg://u:p@host/db"
    )
    assert (
        normalize_database_url("postgresql+psycopg://u:p@host/db")
        == "postgresql+psycopg://u:p@host/db"
    )


def test_el_motor_cambia_segun_la_base_de_datos():
    motor_sqlite = build_engine("sqlite:///x.db")
    assert motor_sqlite.dialect.name == "sqlite"
    assert motor_sqlite.pool._pre_ping is False
    assert "sslmode" not in (motor_sqlite.dialect.create_connect_args(motor_sqlite.url)[1] or {})

    motor_postgres = build_engine("postgresql+psycopg://u:p@localhost/db")
    assert motor_postgres.dialect.name == "postgresql"
    assert motor_postgres.pool._pre_ping is True


def test_la_portada_carga(cliente):
    respuesta = cliente.get("/")
    assert respuesta.status_code == 200
    cuerpo = respuesta.get_data(as_text=True)
    assert "descubrir creadores" in cuerpo
    assert "cómo funciona" in cuerpo
    assert "/creadores" in cuerpo


def test_el_listado_muestra_los_creadores_del_seed(cliente):
    respuesta = cliente.get("/creadores")
    assert respuesta.status_code == 200
    cuerpo = respuesta.get_data(as_text=True)
    assert cuerpo.count('class="card creator-card"') == len(SEED_CREATORS)
    for especialidad in ("ropa", "props", "accesorios"):
        assert f'data-filter="{especialidad}"' in cuerpo
    assert 'data-specialty="ropa"' in cuerpo


def test_la_ficha_del_creador_muestra_bio_y_obras(cliente, aplicacion):
    slug = SEED_CREATORS[0]["slug"]
    respuesta = cliente.get(f"/creadores/{slug}")
    assert respuesta.status_code == 200
    cuerpo = respuesta.get_data(as_text=True)
    assert SEED_CREATORS[0]["name"] in cuerpo
    assert SEED_CREATORS[0]["bio"][:60] in cuerpo
    for obra in SEED_CREATORS[0]["works"]:
        assert obra["title"] in cuerpo
        assert f"/obras/{obra['slug']}" in cuerpo


def test_la_obra_muestra_precio_estado_y_correo(cliente):
    creador = SEED_CREATORS[0]
    obra = creador["works"][1]
    respuesta = cliente.get(f"/obras/{obra['slug']}")
    assert respuesta.status_code == 200
    cuerpo = respuesta.get_data(as_text=True)
    assert obra["title"] in cuerpo
    assert obra["description"] in cuerpo
    assert obra["price_note"] in cuerpo
    assert obra["status"] in cuerpo
    assert f"mailto:{creador['contact_email']}" in cuerpo
    assert f"/creadores/{creador['slug']}" in cuerpo


def test_obra_sin_precio_muestra_a_consultar(cliente):
    creador = next(c for c in SEED_CREATORS if any(o["price_note"] is None for o in c["works"]))
    obra = next(o for o in creador["works"] if o["price_note"] is None)
    respuesta = cliente.get(f"/obras/{obra['slug']}")
    cuerpo = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 200
    assert "a consultar" in cuerpo


def test_healthz_responde_ok(cliente):
    respuesta = cliente.get("/healthz")
    assert respuesta.status_code == 200
    assert respuesta.get_json() == {"status": "ok"}


def test_rutas_inexistentes_dan_404_propio(cliente):
    for ruta in ("/no-existe", "/creadores/no-existe", "/obras/no-existe"):
        respuesta = cliente.get(ruta)
        assert respuesta.status_code == 404
        cuerpo = respuesta.get_data(as_text=True)
        assert "esta página no existe" in cuerpo
        assert "/creadores" in cuerpo


def test_el_seed_no_duplica_datos(aplicacion):
    fabrica = aplicacion.extensions["db_session"]
    with fabrica() as sesion:
        assert sesion.scalar(select(func.count()).select_from(Creator)) == len(SEED_CREATORS)
        obras_por_creador = sesion.execute(
            select(Work.creator_id, func.count()).group_by(Work.creator_id)
        ).all()
    assert all(2 <= total <= 3 for _, total in obras_por_creador)

    # Arrancar la aplicación otra vez no debe volver a sembrar el catálogo.
    create_app(
        {
            "TESTING": True,
            "DATABASE_URL": aplicacion.config["DATABASE_URL"],
            "SECRET_KEY": "clave-de-pruebas",
        }
    )

    with fabrica() as sesion:
        assert sesion.scalar(select(func.count()).select_from(Creator)) == len(SEED_CREATORS)


def test_robots_txt(cliente):
    respuesta = cliente.get("/robots.txt")
    assert respuesta.status_code == 200
    cuerpo = respuesta.get_data(as_text=True)
    assert "User-agent: *" in cuerpo
    assert "Sitemap: http" in cuerpo


def test_el_sitemap_incluye_creadores_y_obras(cliente):
    respuesta = cliente.get("/sitemap.xml")
    assert respuesta.status_code == 200
    assert respuesta.mimetype == "application/xml"
    cuerpo = respuesta.get_data(as_text=True)
    assert "<urlset" in cuerpo
    assert "/creadores/" in cuerpo
    assert "/obras/" in cuerpo
