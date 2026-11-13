"""Copias en R2: nombres, subida y purga, con un cliente falso."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from scripts.copias import (
    PREFIJO,
    config_de_entorno,
    nombre_de_copia,
    purgar,
    subir,
)


class ClienteFalso:
    def __init__(self, objetos: list[dict] | None = None) -> None:
        self.objetos = objetos or []
        self.subidos: list[tuple[str, str, str]] = []
        self.borrados: list[str] = []

    def upload_file(self, ruta: str, bucket: str, clave: str) -> None:
        self.subidos.append((ruta, bucket, clave))

    def get_paginator(self, nombre: str):
        objetos = self.objetos

        class Paginador:
            def paginate(self, Bucket: str, Prefix: str):
                yield {"Contents": objetos}

        assert nombre == "list_objects_v2"
        return Paginador()

    def delete_object(self, Bucket: str, Key: str) -> None:
        self.borrados.append(Key)


def test_faltan_variables_de_r2():
    with pytest.raises(SystemExit) as error:
        config_de_entorno({})
    assert "R2_ENDPOINT_URL" in str(error.value)


def test_el_nombre_lleva_fecha_y_orden():
    momento = datetime(2026, 11, 13, 3, 0, 0, tzinfo=timezone.utc)
    assert nombre_de_copia(momento) == f"{PREFIJO}cosknot-20261113-030000.dump.enc"


def test_no_se_sube_una_copia_vacia(tmp_path):
    ruta = tmp_path / "vacia.dump.enc"
    ruta.write_bytes(b"x")
    with pytest.raises(SystemExit):
        subir(ClienteFalso(), "bucket", ruta, "copias/x.dump.enc")


def test_subir_llama_al_bucket_con_la_clave(tmp_path):
    ruta = tmp_path / "copia.dump.enc"
    ruta.write_bytes(b"x" * 2048)
    cliente = ClienteFalso()
    assert subir(cliente, "bucket", ruta, "copias/cosknot.dump.enc") == 2048
    assert cliente.subidos == [(str(ruta), "bucket", "copias/cosknot.dump.enc")]


def test_purgar_borra_solo_lo_viejo():
    ahora = datetime(2026, 11, 13, 12, 0, tzinfo=timezone.utc)
    cliente = ClienteFalso(
        [
            {"Key": "copias/vieja-1.dump.enc", "LastModified": ahora - timedelta(days=40)},
            {"Key": "copias/vieja-2.dump.enc", "LastModified": ahora - timedelta(days=31)},
            {"Key": "copias/nueva-1.dump.enc", "LastModified": ahora - timedelta(days=2)},
            {"Key": "copias/nueva-2.dump.enc", "LastModified": ahora},
        ]
    )

    borradas = purgar(cliente, "bucket", ahora=ahora)

    assert sorted(borradas) == ["copias/vieja-1.dump.enc", "copias/vieja-2.dump.enc"]
    assert cliente.borrados == borradas


def test_purgar_aguanta_fechas_sin_zona():
    ahora = datetime(2026, 11, 13, 12, 0, tzinfo=timezone.utc)
    cliente = ClienteFalso(
        [
            {
                "Key": "copias/sin-zona.dump.enc",
                "LastModified": datetime(2026, 10, 1, 3, 0, 0),
            }
        ]
    )
    assert purgar(cliente, "bucket", ahora=ahora) == ["copias/sin-zona.dump.enc"]
