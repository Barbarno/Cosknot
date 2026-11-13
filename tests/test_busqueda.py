from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.dialects import postgresql

import busqueda
from app import create_app
from models import Creator, Work


@pytest.fixture()
def aplicacion(tmp_path):
    return create_app(
        {
            "TESTING": True,
            "DATABASE_URL": f"sqlite:///{(tmp_path / 'busqueda.db').as_posix()}",
            "SECRET_KEY": "clave-de-pruebas",
            "UPLOAD_DIR": (tmp_path / "uploads").as_posix(),
        }
    )


@pytest.fixture()
def cliente(aplicacion):
    return aplicacion.test_client()


def test_en_sqlite_se_usa_ilike(aplicacion):
    with aplicacion.extensions["db_session"]() as sesion:
        assert busqueda.motor_de(sesion) == "sqlite"
        creadores = busqueda.buscar_creadores(sesion, "pelucas")
        assert creadores
        assert all(
            "peluca" in c.specialty.lower() or "peluca" in c.bio.lower()
            for c in creadores
        )


def test_el_buscador_encuentra_por_titulo_de_obra(cliente):
    cuerpo = cliente.get("/buscar?q=capa").get_data(as_text=True)
    assert "resultados para" in cuerpo
    assert "capa" in cuerpo.lower()


def test_el_buscador_encuentra_por_ubicacion(cliente, aplicacion):
    with aplicacion.extensions["db_session"]() as sesion:
        creador = sesion.scalar(select(Creator).order_by(Creator.id))
        ciudad = creador.location.split(",")[0].strip()

    cuerpo = cliente.get(f"/buscar?q={ciudad}").get_data(as_text=True)
    assert creador.name in cuerpo


def test_sin_resultados_avisa_igual_que_antes(cliente):
    respuesta = cliente.get("/buscar?q=zzzznoexiste")
    assert respuesta.status_code == 200
    assert "nada con ese nombre" in respuesta.get_data(as_text=True)


def test_la_consulta_de_postgres_usa_tsvector_y_tsquery():
    sql_creadores = str(
        busqueda.consulta_creadores_postgres("capa").compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )
    assert "to_tsvector('spanish'" in sql_creadores
    assert "plainto_tsquery('spanish'" in sql_creadores
    assert "@@" in sql_creadores
    assert "ts_rank" in sql_creadores
    assert "ILIKE" not in sql_creadores.upper()

    sql_obras = str(
        busqueda.consulta_obras_postgres("capa").compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )
    assert "to_tsvector('spanish'" in sql_obras
    assert "works.title" in sql_obras


def test_la_consulta_de_sqlite_usa_ilike():
    from sqlalchemy.dialects import sqlite

    sql = str(
        busqueda.consulta_creadores_ilike("capa").compile(
            dialect=sqlite.dialect(), compile_kwargs={"literal_binds": True}
        )
    )
    assert "LIKE" in sql.upper()
    assert "to_tsvector" not in sql


def test_los_mismos_campos_en_los_dos_motores():
    assert busqueda.CAMPOS_CREADOR == ("name", "bio", "location", "specialty")
    assert busqueda.CAMPOS_OBRA == ("title", "description")

    for modelo, campos in (
        (Creator, busqueda.CAMPOS_CREADOR),
        (Work, busqueda.CAMPOS_OBRA),
    ):
        for campo in campos:
            assert hasattr(modelo, campo)
