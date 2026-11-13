"""Buzón de avisos: encolado, reintento y arranque único del hilo.

Nada de aquí sale a la red: los envíos van por un correo falso que cuenta lo que
le piden y falla cuando se le dice.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from app import create_app
from correo import Correo
from models import EmailOutbox
from outbox import (
    clave_de,
    encolar,
    iniciar_hilo,
    pendientes,
    procesar,
)


class CorreoQueFalla(Correo):
    nombre = "falla"
    activo = True

    def __init__(self) -> None:
        self.intentos: list[str] = []

    def enviar(self, para: str, asunto: str, texto: str) -> bool:
        self.intentos.append(para)
        return False


class CorreoQueFunciona(Correo):
    nombre = "funciona"
    activo = True

    def __init__(self) -> None:
        self.enviados: list[str] = []

    def enviar(self, para: str, asunto: str, texto: str) -> bool:
        self.enviados.append(para)
        return True


@pytest.fixture()
def aplicacion(tmp_path):
    return create_app(
        {
            "TESTING": True,
            "DATABASE_URL": f"sqlite:///{(tmp_path / 'outbox.db').as_posix()}",
            "SECRET_KEY": "clave-de-pruebas",
            "UPLOAD_DIR": (tmp_path / "uploads").as_posix(),
            "EMAIL_ASYNC": True,
        }
    )


def test_la_clave_es_estable_e_igual_para_el_mismo_aviso():
    una = clave_de("a@example.com", "asunto", "cuerpo")
    otra = clave_de("a@example.com", "asunto", "cuerpo")
    distinta = clave_de("a@example.com", "asunto", "otro cuerpo")
    assert una == otra
    assert una != distinta
    assert len(una) == 64


def test_encolar_dos_veces_el_mismo_aviso_no_duplica(aplicacion):
    with aplicacion.extensions["db_session"]() as sesion:
        primero = encolar(sesion, "a@example.com", "hola", "cuerpo")
        segundo = encolar(sesion, "a@example.com", "hola", "cuerpo")
        sesion.commit()
        assert primero.id == segundo.id
        total = len(sesion.scalars(select(EmailOutbox)).all())
        assert total == 1


def test_un_aviso_sin_destinatario_no_se_encola(aplicacion):
    with aplicacion.extensions["db_session"]() as sesion:
        with pytest.raises(ValueError):
            encolar(sesion, "", "hola", "cuerpo")


def test_procesar_marca_enviado(aplicacion):
    correo = CorreoQueFunciona()
    with aplicacion.extensions["db_session"]() as sesion:
        encolar(sesion, "a@example.com", "hola", "cuerpo")
        sesion.commit()
        resultado = procesar(sesion, correo)
        assert resultado == {"enviados": 1, "reintentar": 0, "fallidos": 0}

        aviso = sesion.scalar(select(EmailOutbox))
        assert aviso.estado == "enviado"
        assert aviso.enviado_at is not None
        assert aviso.intentos == 0
        assert correo.enviados == ["a@example.com"]


def test_un_fallo_aplaza_el_siguiente_intento(aplicacion):
    correo = CorreoQueFalla()
    ahora = datetime(2026, 11, 13, 12, 0, 0)
    with aplicacion.extensions["db_session"]() as sesion:
        encolar(sesion, "a@example.com", "hola", "cuerpo", ahora=ahora)
        sesion.commit()

        resultado = procesar(sesion, correo, ahora=ahora)
        assert resultado == {"enviados": 0, "reintentar": 1, "fallidos": 0}

        aviso = sesion.scalar(select(EmailOutbox))
        assert aviso.estado == "pendiente"
        assert aviso.intentos == 1
        # primer reintento: 2 minutos después
        assert aviso.proximo_intento == ahora + timedelta(minutes=2)

        # antes de tiempo no se toca
        assert pendientes(sesion, ahora + timedelta(seconds=30)) == []
        assert len(pendientes(sesion, ahora + timedelta(minutes=3))) == 1


def test_tras_los_intentos_maximos_queda_fallido(aplicacion):
    correo = CorreoQueFalla()
    ahora = datetime(2026, 11, 13, 12, 0, 0)
    with aplicacion.extensions["db_session"]() as sesion:
        aviso = encolar(sesion, "a@example.com", "hola", "cuerpo", ahora=ahora)
        sesion.commit()

        momento = ahora
        for _ in range(3):
            procesar(sesion, correo, ahora=momento, max_intentos=3)
            momento = momento + timedelta(hours=2)

        sesion.refresh(aviso)
        assert aviso.estado == "fallido"
        assert aviso.intentos == 3
        assert len(correo.intentos) == 3


def test_sin_correo_activo_no_se_toca_nada(aplicacion):
    with aplicacion.extensions["db_session"]() as sesion:
        encolar(sesion, "a@example.com", "hola", "cuerpo")
        sesion.commit()

        class Apagado(Correo):
            activo = False
            nombre = "apagado"

            def enviar(self, para, asunto, texto):
                raise AssertionError("no debería intentarse")

        assert procesar(sesion, Apagado()) == {
            "enviados": 0,
            "reintentar": 0,
            "fallidos": 0,
        }
        assert sesion.scalar(select(EmailOutbox)).estado == "pendiente"


def test_un_pedido_con_correo_roto_deja_el_aviso_en_el_buzon(tmp_path):
    aplicacion = create_app(
        {
            "TESTING": True,
            "DATABASE_URL": f"sqlite:///{(tmp_path / 'pedido.db').as_posix()}",
            "SECRET_KEY": "clave-de-pruebas",
            "UPLOAD_DIR": (tmp_path / "uploads").as_posix(),
            "EMAIL_ASYNC": True,
        }
    )
    aplicacion.extensions["correo"] = CorreoQueFalla()

    taller = aplicacion.test_client()
    taller.post(
        "/registro",
        data={
            "email": "taller@example.com",
            "password": "contrasena-larga",
            "confirmar": "contrasena-larga",
            "rol": "creador",
        },
    )
    taller.post(
        "/cuenta/perfil",
        data={
            "nombre": "Taller Uno",
            "especialidad": "ropa",
            "ubicacion": "Madrid, España",
            "bio": "coso desde 2015.",
            "contacto": "contacto@taller.example",
        },
    )
    taller.post(
        "/cuenta/obras/nueva",
        data={
            "titulo": "Capa bordada",
            "descripcion": "capa de lana",
            "precio_nota": "",
            "precio_euros": "120",
            "estado": "disponible",
        },
    )

    comprador = aplicacion.test_client()
    comprador.post(
        "/registro",
        data={
            "email": "compra@example.com",
            "password": "contrasena-larga",
            "confirmar": "contrasena-larga",
            "rol": "comprador",
        },
    )
    respuesta = comprador.post(
        "/pedidos/nuevo/capa-bordada", data={"mensaje": "talla M"}, follow_redirects=True
    )
    assert respuesta.status_code == 200

    with aplicacion.extensions["db_session"]() as sesion:
        aviso = sesion.scalar(select(EmailOutbox))
        assert aviso is not None
        assert aviso.destinatario == "taller@example.com"
        assert "nuevo encargo" in aviso.asunto
        assert aviso.estado == "pendiente"


def test_el_hilo_solo_arranca_una_vez(aplicacion):
    assert iniciar_hilo(aplicacion, intervalo=3600) is True
    assert iniciar_hilo(aplicacion, intervalo=3600) is False
