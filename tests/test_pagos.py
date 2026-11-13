from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import select

import pagos
from app import create_app, politica_csp
from models import Creator, Order

CONFIG_PAGOS = {
    "STRIPE_SECRET_KEY": "sk_test_falsa",
    "STRIPE_WEBHOOK_SECRET": "whsec_falsa",
    "COMMISSION_PERCENT": "10",
}


class Cuenta:
    def __init__(self, id="acct_test_1"):
        self.id = id

    def get(self, clave, defecto=None):
        return {"charges_enabled": True, "payouts_enabled": True}.get(clave, defecto)


class FakeStripe:
    """Sustituye al SDK. Nada sale a la red."""

    def __init__(self):
        self.cuentas_creadas: list[dict] = []
        self.enlaces: list[dict] = []
        self.sesiones: list[dict] = []
        self.evento = None
        self.firma_mala = False
        self.Account = self
        self.AccountLink = self
        self.checkout = self
        self.Session = self
        self.Webhook = self

    # Account
    def create(self, **kwargs):
        self.cuentas_creadas.append(kwargs)
        return Cuenta()

    def retrieve(self, cuenta_id):
        return Cuenta(cuenta_id)

    # AccountLink
    def AccountLink_create(self, **kwargs):
        return None

    # checkout.Session
    def create_session(self, **kwargs):
        return None

    # Webhook
    def construct_event(self, cuerpo, firma, secreto):
        if self.firma_mala:
            raise ValueError("firma mala")
        return self.evento


def fake_stripe_con_sesion(fake):
    """El SDK real usa AccountLink.create y checkout.Session.create; el fake imita
    esa forma con objetos anidados."""

    class AccountLink:
        @staticmethod
        def create(**kwargs):
            fake.enlaces.append(kwargs)
            return {"url": "https://connect.stripe.com/setup/acct_test_1"}

    class SessionFalsa:
        @staticmethod
        def create(**kwargs):
            fake.sesiones.append(kwargs)
            return {"id": "cs_test_1", "url": "https://checkout.stripe.com/c/cs_test_1"}

    class Checkout:
        Session = SessionFalsa

    fake.AccountLink = AccountLink
    fake.checkout = Checkout
    return fake


@pytest.fixture()
def aplicacion(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "DATABASE_URL": f"sqlite:///{(tmp_path / 'pagos.db').as_posix()}",
            "SECRET_KEY": "clave-de-pruebas",
            "UPLOAD_DIR": (tmp_path / "uploads").as_posix(),
            "EMAIL_ASYNC": False,
            **CONFIG_PAGOS,
        }
    )
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


def taller_con_obra(cliente, con_stripe=True):
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
            "titulo": "Capa bordada",
            "descripcion": "capa de lana",
            "precio_nota": "",
            "precio_euros": "120",
            "estado": "disponible",
        },
    )


def pedido_aceptado(aplicacion, con_stripe=True):
    taller = aplicacion.test_client()
    taller_con_obra(taller)
    comprador = aplicacion.test_client()
    registrar(comprador, "compra@example.com")
    comprador.post("/pedidos/nuevo/capa-bordada", data={"mensaje": "talla M"})

    with aplicacion.extensions["db_session"]() as sesion:
        pedido = sesion.scalar(select(Order).where(Order.status == "solicitado"))
        pedido_id = pedido.id
        if con_stripe:
            creador = sesion.scalar(select(Creator).where(Creator.name == "Taller Uno"))
            creador.stripe_account_id = "acct_test_1"
            creador.stripe_onboarding_ok = True
            sesion.commit()

    taller.post(f"/pedidos/{pedido_id}/estado", data={"estado": "aceptado"})
    return taller, comprador, pedido_id


def test_sin_claves_el_cobro_esta_desactivado(aplicacion):
    assert "STRIPE_SECRET_KEY" in pagos.motivo_desactivado({})
    assert "STRIPE_WEBHOOK_SECRET" in pagos.motivo_desactivado(
        {"STRIPE_SECRET_KEY": "sk_test_x"}
    )
    assert "COMMISSION_PERCENT" in pagos.motivo_desactivado(
        {"STRIPE_SECRET_KEY": "sk_test_x", "STRIPE_WEBHOOK_SECRET": "whsec_x"}
    )
    assert pagos.motivo_desactivado(CONFIG_PAGOS) == ""


def test_una_clave_live_no_vale():
    assert pagos.clave_valida({"STRIPE_SECRET_KEY": "sk_live_abc"}) is False
    assert pagos.clave_valida({"STRIPE_SECRET_KEY": "sk_test_abc"}) is True


def test_la_comision_se_calcula_y_se_redondea():
    assert pagos.calcular_comision(12000, Decimal("10")) == 1200
    assert pagos.calcular_comision(999, Decimal("15")) == 150
    assert pagos.calcular_comision(0, Decimal("10")) == 0


def test_la_sesion_de_pago_lleva_destination_charge_y_comision(monkeypatch, aplicacion):
    fake = fake_stripe_con_sesion(FakeStripe())
    monkeypatch.setattr(pagos, "_stripe", lambda: fake)
    monkeypatch.setattr(pagos, "_cliente", lambda config: fake)

    taller, comprador, pedido_id = pedido_aceptado(aplicacion)
    respuesta = comprador.post(f"/pedidos/{pedido_id}/pagar")

    assert respuesta.status_code == 303
    assert respuesta.headers["Location"].startswith("https://checkout.stripe.com/")
    assert len(fake.sesiones) == 1
    datos = fake.sesiones[0]
    assert datos["payment_intent_data"]["transfer_data"]["destination"] == "acct_test_1"
    assert datos["payment_intent_data"]["application_fee_amount"] == 1200
    assert datos["line_items"][0]["price_data"]["unit_amount"] == 12000
    assert datos["metadata"]["pedido_id"] == str(pedido_id)

    with aplicacion.extensions["db_session"]() as sesion:
        assert sesion.get(Order, pedido_id).stripe_checkout_session_id == "cs_test_1"


def test_el_comprador_no_paga_un_pedido_sin_aceptar(monkeypatch, aplicacion):
    fake = fake_stripe_con_sesion(FakeStripe())
    monkeypatch.setattr(pagos, "_stripe", lambda: fake)
    monkeypatch.setattr(pagos, "_cliente", lambda config: fake)

    taller = aplicacion.test_client()
    taller_con_obra(taller)
    comprador = aplicacion.test_client()
    registrar(comprador, "compra@example.com")
    comprador.post("/pedidos/nuevo/capa-bordada", data={"mensaje": "talla M"})
    with aplicacion.extensions["db_session"]() as sesion:
        pedido_id = sesion.scalar(select(Order.id))

    respuesta = comprador.post(
        f"/pedidos/{pedido_id}/pagar", follow_redirects=True
    )
    assert "aceptado antes de pagar" in respuesta.get_data(as_text=True)
    assert fake.sesiones == []


def test_el_webhook_marca_pagado_y_es_idempotente(monkeypatch, aplicacion):
    fake = FakeStripe()
    fake.evento = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_1",
                "payment_intent": "pi_test_1",
                "metadata": {"pedido_id": "1"},
            }
        },
    }
    monkeypatch.setattr(pagos, "_stripe", lambda: fake)

    taller, comprador, pedido_id = pedido_aceptado(aplicacion)
    fake.evento["data"]["object"]["metadata"]["pedido_id"] = str(pedido_id)

    respuesta = comprador.post(
        "/stripe/webhook",
        data=b"{}",
        headers={"Stripe-Signature": "t=1,v1=falsa"},
        content_type="application/json",
    )
    assert respuesta.status_code == 200
    assert respuesta.get_json()["resultado"].startswith("pedido")

    with aplicacion.extensions["db_session"]() as sesion:
        pedido = sesion.get(Order, pedido_id)
        assert pedido.status == "pagado"
        assert pedido.stripe_payment_intent_id == "pi_test_1"
        assert pedido.paid_at is not None

    repetido = comprador.post(
        "/stripe/webhook",
        data=b"{}",
        headers={"Stripe-Signature": "t=1,v1=falsa"},
        content_type="application/json",
    )
    assert repetido.get_json()["resultado"].startswith("repetido")


def test_el_webhook_rechaza_una_firma_mala(monkeypatch, aplicacion):
    fake = FakeStripe()
    fake.firma_mala = True
    monkeypatch.setattr(pagos, "_stripe", lambda: fake)

    respuesta = aplicacion.test_client().post(
        "/stripe/webhook",
        data=b"{}",
        headers={"Stripe-Signature": "basura"},
        content_type="application/json",
    )
    assert respuesta.status_code == 400


def test_la_csp_abre_checkout_solo_si_el_cobro_esta_configurado(aplicacion):
    assert "https://checkout.stripe.com" in politica_csp(aplicacion)

    sin_pagos = create_app(
        {
            "TESTING": True,
            "DATABASE_URL": "sqlite://",
            "SECRET_KEY": "k",
            "COMMISSION_PERCENT": "",
        }
    )
    csp = politica_csp(sin_pagos)
    assert "form-action 'self'" in csp
    assert "checkout.stripe.com" not in csp
    assert "*" not in csp


def test_sin_commision_no_se_puede_pagar(monkeypatch, aplicacion, tmp_path):
    fake = fake_stripe_con_sesion(FakeStripe())
    monkeypatch.setattr(pagos, "_stripe", lambda: fake)
    monkeypatch.setattr(pagos, "_cliente", lambda config: fake)

    aplicacion.config["COMMISSION_PERCENT"] = ""
    taller, comprador, pedido_id = pedido_aceptado(aplicacion)
    respuesta = comprador.post(f"/pedidos/{pedido_id}/pagar", follow_redirects=True)
    assert "COMMISSION_PERCENT" in respuesta.get_data(as_text=True)
    assert fake.sesiones == []
