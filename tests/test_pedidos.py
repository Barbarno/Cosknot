from __future__ import annotations

import pytest
from sqlalchemy import select

from app import create_app
from estados_pedido import TransicionInvalida, cambiar_estado, transiciones_disponibles
from importes import euros_a_centimos, formato_importe
from models import Creator, Order, OrderMessage, User, Work


@pytest.fixture()
def aplicacion(tmp_path):
    return create_app(
        {
            "TESTING": True,
            "DATABASE_URL": f"sqlite:///{(tmp_path / 'pedidos.db').as_posix()}",
            "SECRET_KEY": "clave-de-pruebas",
        }
    )


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


def taller_con_obra(cliente, precio="180,00", titulo="Capa bordada"):
    registrar(cliente, "taller@example.com", rol="creador")
    cliente.post(
        "/cuenta/perfil",
        data={
            "nombre": "Taller Uno",
            "especialidad": "ropa",
            "ubicacion": "Madrid, España",
            "bio": "coso desde 2015.",
            "contacto": "taller@example.com",
        },
    )
    cliente.post(
        "/cuenta/obras/nueva",
        data={
            "titulo": titulo,
            "descripcion": "capa de lana con bordado",
            "precio_nota": "desde 180 €",
            "precio_euros": precio,
            "estado": "disponible",
        },
    )


def test_los_importes_se_convierten_y_se_pintan():
    assert euros_a_centimos("180,00") == 18000
    assert euros_a_centimos("180.5 €") == 18050
    assert euros_a_centimos("") is None
    assert euros_a_centimos("no es un numero") is None
    assert euros_a_centimos("-4") is None
    assert formato_importe(18000, "EUR") == "180.00 €"
    assert formato_importe(None) == "a consultar"


def test_sin_sesion_la_ficha_invita_a_entrar(aplicacion):
    taller = aplicacion.test_client()
    taller_con_obra(taller)

    visitante = aplicacion.test_client()
    respuesta = visitante.get("/obras/capa-bordada")
    cuerpo = respuesta.get_data(as_text=True)
    assert "entrar para encargar" in cuerpo
    assert "hacer el encargo" not in cuerpo


def test_un_comprador_hace_un_encargo(aplicacion):
    taller = aplicacion.test_client()
    taller_con_obra(taller)

    comprador = aplicacion.test_client()
    registrar(comprador, "compra@example.com")
    respuesta = comprador.post(
        "/pedidos/nuevo/capa-bordada",
        data={"mensaje": "la quiero en talla M para octubre"},
        follow_redirects=True,
    )
    assert respuesta.status_code == 200
    assert "encargo enviado al taller" in respuesta.get_data(as_text=True)

    with aplicacion.extensions["db_session"]() as sesion:
        pedido = sesion.scalar(select(Order))
        assert pedido.status == "solicitado"
        assert pedido.amount_cents == 18000
        assert pedido.application_fee_cents == 0
        assert len(pedido.messages) == 1
        assert pedido.messages[0].body == "la quiero en talla M para octubre"


def test_el_creador_no_se_encarga_su_propia_obra(aplicacion):
    taller = aplicacion.test_client()
    taller_con_obra(taller)
    respuesta = taller.post(
        "/pedidos/nuevo/capa-bordada",
        data={"mensaje": "yo mismo"},
        follow_redirects=True,
    )
    assert "no puedes encargarte tu propia obra" in respuesta.get_data(as_text=True)


def test_las_transiciones_las_valida_el_servidor(aplicacion):
    taller = aplicacion.test_client()
    taller_con_obra(taller)
    comprador = aplicacion.test_client()
    registrar(comprador, "compra@example.com")
    comprador.post("/pedidos/nuevo/capa-bordada", data={"mensaje": "hola"})

    with aplicacion.extensions["db_session"]() as sesion:
        pedido_id = sesion.scalar(select(Order.id))

    # el comprador no puede aceptar su propio pedido
    respuesta = comprador.post(
        f"/pedidos/{pedido_id}/estado", data={"estado": "aceptado"}, follow_redirects=True
    )
    assert "no puede dejar el pedido en aceptado" in respuesta.get_data(as_text=True)

    with aplicacion.extensions["db_session"]() as sesion:
        assert sesion.get(Order, pedido_id).status == "solicitado"

    respuesta = taller.post(
        f"/pedidos/{pedido_id}/estado", data={"estado": "aceptado"}, follow_redirects=True
    )
    assert "el pedido pasa a aceptado" in respuesta.get_data(as_text=True)

    # salto inválido: de aceptado no se pasa directo a enviado
    respuesta = taller.post(
        f"/pedidos/{pedido_id}/estado", data={"estado": "enviado"}, follow_redirects=True
    )
    assert "no se puede pasar de aceptado a enviado" in respuesta.get_data(as_text=True)


def test_el_ciclo_completo_de_un_pedido(aplicacion):
    taller = aplicacion.test_client()
    taller_con_obra(taller)
    comprador = aplicacion.test_client()
    registrar(comprador, "compra@example.com")
    comprador.post("/pedidos/nuevo/capa-bordada", data={"mensaje": "hola"})

    with aplicacion.extensions["db_session"]() as sesion:
        pedido_id = sesion.scalar(select(Order.id))

    for cliente, destino in (
        (taller, "aceptado"),
        (taller, "pagado"),
        (taller, "enviado"),
        (comprador, "completado"),
    ):
        cliente.post(f"/pedidos/{pedido_id}/estado", data={"estado": destino})

    with aplicacion.extensions["db_session"]() as sesion:
        pedido = sesion.get(Order, pedido_id)
        assert pedido.status == "completado"
        assert transiciones_disponibles(pedido, None) == []


def test_los_mensajes_llegan_a_las_dos_partes_y_nadie_mas(aplicacion):
    taller = aplicacion.test_client()
    taller_con_obra(taller)
    comprador = aplicacion.test_client()
    registrar(comprador, "compra@example.com")
    comprador.post("/pedidos/nuevo/capa-bordada", data={"mensaje": "hola"})

    with aplicacion.extensions["db_session"]() as sesion:
        pedido_id = sesion.scalar(select(Order.id))

    respuesta = taller.post(
        f"/pedidos/{pedido_id}/mensajes",
        data={"cuerpo": "te paso medidas mañana"},
        follow_redirects=True,
    )
    assert "te paso medidas mañana" in respuesta.get_data(as_text=True)
    assert "hola" in respuesta.get_data(as_text=True)

    intruso = aplicacion.test_client()
    registrar(intruso, "intruso@example.com")
    assert intruso.get(f"/pedidos/{pedido_id}").status_code == 403
    assert intruso.post(f"/pedidos/{pedido_id}/mensajes", data={"cuerpo": "x"}).status_code == 403


def test_la_maquina_de_estados_es_unitaria(aplicacion):
    taller = aplicacion.test_client()
    taller_con_obra(taller)
    comprador = aplicacion.test_client()
    registrar(comprador, "compra@example.com")
    comprador.post("/pedidos/nuevo/capa-bordada", data={"mensaje": "hola"})

    with aplicacion.extensions["db_session"]() as sesion:
        pedido = sesion.scalar(select(Order))
        creador_user = sesion.scalar(select(User).where(User.email == "taller@example.com"))
        comprador_user = sesion.scalar(select(User).where(User.email == "compra@example.com"))

        assert transiciones_disponibles(pedido, creador_user) == ["aceptado", "cancelado"]
        assert transiciones_disponibles(pedido, comprador_user) == ["cancelado"]

        with pytest.raises(TransicionInvalida):
            cambiar_estado(pedido, "enviado", creador_user)
        with pytest.raises(TransicionInvalida):
            cambiar_estado(pedido, "aceptado", comprador_user)

        cambiar_estado(pedido, "aceptado", creador_user)
        assert pedido.status == "aceptado"


def test_el_listado_separa_compras_y_ventas(aplicacion):
    taller = aplicacion.test_client()
    taller_con_obra(taller)
    comprador = aplicacion.test_client()
    registrar(comprador, "compra@example.com")
    comprador.post("/pedidos/nuevo/capa-bordada", data={"mensaje": "hola"})

    cuerpo_comprador = comprador.get("/pedidos/").get_data(as_text=True)
    assert "como comprador" in cuerpo_comprador
    assert "Capa bordada" in cuerpo_comprador
    assert "como creador" not in cuerpo_comprador

    cuerpo_taller = taller.get("/pedidos/").get_data(as_text=True)
    assert "como creador" in cuerpo_taller
    assert "compra@example.com" in cuerpo_taller


def test_el_precio_numerico_sale_en_la_ficha(aplicacion):
    taller = aplicacion.test_client()
    taller_con_obra(taller, precio="180,00")
    cuerpo = taller.get("/obras/capa-bordada").get_data(as_text=True)
    assert "180.00 €" in cuerpo

    with aplicacion.extensions["db_session"]() as sesion:
        obra = sesion.scalar(select(Work).where(Work.slug == "capa-bordada"))
        assert obra.price_cents == 18000
        assert obra.currency == "EUR"
        assert obra.price_note == "desde 180 €"
