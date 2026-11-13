from __future__ import annotations

import pytest
from sqlalchemy import select

from app import create_app
from correo import CorreoConsola, CorreoDesactivado, CorreoResend, crear_correo
from models import Order


class CorreoFalso(CorreoConsola):
    """Guarda lo que se habría enviado. Nada sale a la red."""

    nombre = "falso"

    def __init__(self):
        self.enviados: list[tuple[str, str, str]] = []

    def enviar(self, para: str, asunto: str, texto: str) -> bool:
        self.enviados.append((para, asunto, texto))
        return True


@pytest.fixture()
def aplicacion(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "DATABASE_URL": f"sqlite:///{(tmp_path / 'correo.db').as_posix()}",
            "SECRET_KEY": "clave-de-pruebas",
            "UPLOAD_DIR": (tmp_path / "uploads").as_posix(),
            "EMAIL_ASYNC": False,
        }
    )
    app.extensions["correo"] = CorreoFalso()
    return app


def registrar(cliente, email, rol="comprador"):
    return cliente.post(
        "/registro",
        data={
            "email": email,
            "password": "contrasena-larga",
            "confirmar": "contrasena-larga",
            "rol": rol,
        },
        follow_redirects=True,
    )


def taller_con_obra(cliente):
    registrar(cliente, "taller@example.com", rol="creador")
    cliente.post(
        "/cuenta/perfil",
        data={
            "nombre": "Taller Uno",
            "especialidad": "ropa",
            "ubicacion": "Madrid, España",
            "bio": "coso desde 2015.",
            "contacto": "contacto@taller.example",
        },
    )
    cliente.post(
        "/cuenta/obras/nueva",
        data={
            "titulo": "Capa bordada",
            "descripcion": "capa de lana",
            "precio_nota": "",
            "precio_euros": "120",
            "estado": "disponible",
        },
    )


def test_sin_clave_el_correo_queda_desactivado():
    correo = crear_correo({})
    assert isinstance(correo, CorreoDesactivado)
    assert "RESEND_API_KEY" in correo.motivo
    assert correo.activo is False

    correo = crear_correo({"RESEND_API_KEY": "re_test"})
    assert isinstance(correo, CorreoDesactivado)
    assert "EMAIL_FROM" in correo.motivo

    correo = crear_correo({"RESEND_API_KEY": "re_test", "EMAIL_FROM": "hola@cosknot.example"})
    assert isinstance(correo, CorreoResend)
    assert correo.remitente == "hola@cosknot.example"


def test_un_fallo_de_resend_no_lanza_excepcion():
    def rompe(para, asunto, texto):
        raise RuntimeError("la api no contesta")

    correo = CorreoResend("re_test", "hola@cosknot.example", enviar_fn=rompe)
    assert correo.enviar("a@example.com", "asunto", "texto") is False


def test_resend_manda_lo_que_le_piden():
    visto = {}

    def captura(para, asunto, texto):
        visto["para"] = para
        visto["asunto"] = asunto
        visto["texto"] = texto

    correo = CorreoResend("re_test", "hola@cosknot.example", enviar_fn=captura)
    assert correo.enviar("a@example.com", "hola", "cuerpo") is True
    assert visto == {"para": "a@example.com", "asunto": "hola", "texto": "cuerpo"}


def test_un_encargo_avisa_al_taller(aplicacion):
    taller = aplicacion.test_client()
    taller_con_obra(taller)

    comprador = aplicacion.test_client()
    registrar(comprador, "compra@example.com")
    comprador.post("/pedidos/nuevo/capa-bordada", data={"mensaje": "talla M"})

    correo = aplicacion.extensions["correo"]
    assert len(correo.enviados) == 1
    para, asunto, texto = correo.enviados[0]
    assert para == "taller@example.com"
    assert "nuevo encargo" in asunto
    assert "compra@example.com" in texto
    assert "/pedidos/" in texto


def test_el_cambio_de_estado_avisa_a_la_otra_parte(aplicacion):
    taller = aplicacion.test_client()
    taller_con_obra(taller)
    comprador = aplicacion.test_client()
    registrar(comprador, "compra@example.com")
    comprador.post("/pedidos/nuevo/capa-bordada", data={"mensaje": "talla M"})

    with aplicacion.extensions["db_session"]() as sesion:
        pedido_id = sesion.scalar(
            select(Order.id).where(Order.status == "solicitado")
        )

    correo = aplicacion.extensions["correo"]
    correo.enviados.clear()

    taller.post(f"/pedidos/{pedido_id}/estado", data={"estado": "aceptado"})
    assert len(correo.enviados) == 1
    para, asunto, texto = correo.enviados[0]
    assert para == "compra@example.com"
    assert "solicitado -> aceptado" in asunto
    assert "taller@example.com" in texto


def test_un_mensaje_avisa_a_la_otra_parte(aplicacion):
    taller = aplicacion.test_client()
    taller_con_obra(taller)
    comprador = aplicacion.test_client()
    registrar(comprador, "compra@example.com")
    comprador.post("/pedidos/nuevo/capa-bordada", data={"mensaje": "talla M"})

    with aplicacion.extensions["db_session"]() as sesion:
        pedido_id = sesion.scalar(select(Order.id))

    correo = aplicacion.extensions["correo"]
    correo.enviados.clear()

    taller.post(f"/pedidos/{pedido_id}/mensajes", data={"cuerpo": "te paso medidas"})
    para, asunto, texto = correo.enviados[0]
    assert para == "compra@example.com"
    assert "mensaje nuevo" in asunto
    assert "te paso medidas" in texto


def test_sin_correo_configurado_el_pedido_se_crea_igual(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "DATABASE_URL": f"sqlite:///{(tmp_path / 'sin.db').as_posix()}",
            "SECRET_KEY": "clave",
            "UPLOAD_DIR": (tmp_path / "uploads").as_posix(),
            "EMAIL_ASYNC": False,
        }
    )
    taller = app.test_client()
    taller_con_obra(taller)
    comprador = app.test_client()
    registrar(comprador, "compra@example.com")
    respuesta = comprador.post(
        "/pedidos/nuevo/capa-bordada", data={"mensaje": "hola"}, follow_redirects=True
    )
    assert "encargo enviado al taller" in respuesta.get_data(as_text=True)


def test_la_ficha_del_taller_ya_no_publica_su_correo(aplicacion):
    taller = aplicacion.test_client()
    taller_con_obra(taller)
    cuerpo = aplicacion.test_client().get("/creadores/taller-uno").get_data(as_text=True)
    assert "contacto@taller.example" not in cuerpo
    assert "mailto:contacto@taller.example" not in cuerpo
