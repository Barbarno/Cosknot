from __future__ import annotations

import pytest
from sqlalchemy import create_engine, inspect

from migraciones import aplicar_migraciones, config_alembic
from models import Base


def test_las_migraciones_crean_el_mismo_esquema_que_los_modelos(tmp_path):
    url = f"sqlite:///{(tmp_path / 'migrada.db').as_posix()}"
    aplicar_migraciones(url)

    motor = create_engine(url)
    inspector = inspect(motor)
    tablas = {t for t in inspector.get_table_names() if t != "alembic_version"}

    assert tablas == set(Base.metadata.tables)

    for nombre, tabla in Base.metadata.tables.items():
        columnas_migradas = {c["name"] for c in inspector.get_columns(nombre)}
        assert columnas_migradas == {c.name for c in tabla.columns}

    indices_migrados = {i["name"] for i in inspector.get_indexes("works")}
    assert "ix_works_slug" in indices_migrados
    motor.dispose()


def test_aplicar_migraciones_dos_veces_no_rompe(tmp_path):
    url = f"sqlite:///{(tmp_path / 'repetida.db').as_posix()}"
    aplicar_migraciones(url)
    aplicar_migraciones(url)

    motor = create_engine(url)
    assert "creators" in inspect(motor).get_table_names()
    motor.dispose()


def test_el_config_de_alembic_acepta_contrasenas_con_porcentajes():
    cfg = config_alembic("postgresql+psycopg://u:p%40ss@host/db")
    # `set_main_option` escapa el `%` para ConfigParser; al leerlo vuelve a salir tal cual.
    assert cfg.get_main_option("sqlalchemy.url") == "postgresql+psycopg://u:p%40ss@host/db"


@pytest.mark.parametrize(
    "url, variable, esperado",
    [
        ("sqlite:///cosknot.db", None, True),
        ("sqlite:///cosknot.db", "0", True),
        ("postgresql+psycopg://u:p@host/db", None, False),
        ("postgresql+psycopg://u:p@host/db", "1", True),
    ],
)
def test_la_siembra_automatica_solo_vale_en_sqlite(url, variable, esperado):
    from app import debe_sembrar

    assert debe_sembrar(url, variable) is esperado
