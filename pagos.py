"""Pagos con Stripe Connect.

Modelo: cuentas conectadas **express**, cobro con **destination charges** y
`application_fee_amount` como comisión de cosknot. El comprador paga con Stripe
Checkout alojado (redirección), así que no se incrusta `stripe.js` y la CSP no
necesita `script-src` ni `frame-src` de Stripe.

Reglas:

- Siempre modo test: las claves salen de `STRIPE_SECRET_KEY` y tienen que empezar
  por `sk_test_`. Una clave `sk_live_` no se acepta.
- `COMMISSION_PERCENT` no tiene valor por defecto. Si falta, el cobro no se activa
  y la web lo dice.
- El webhook verifica la firma antes de mirar el cuerpo y es idempotente: si el
  pedido ya está pagado con el mismo payment intent, no hace nada.
"""

from __future__ import annotations

import logging
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

registro = logging.getLogger(__name__)


class ErrorPago(ValueError):
    """No se puede iniciar o procesar un cobro."""


def clave_valida(config: dict[str, Any]) -> bool:
    clave = (config.get("STRIPE_SECRET_KEY") or "").strip()
    return clave.startswith("sk_test_")


def comision_porcentaje(config: dict[str, Any]) -> Decimal | None:
    """Lee COMMISSION_PERCENT. Devuelve None si falta o no es un número válido."""
    crudo = (config.get("COMMISSION_PERCENT") or "").strip()
    if not crudo:
        return None
    try:
        valor = Decimal(crudo.replace(",", "."))
    except InvalidOperation:
        return None
    if valor < 0 or valor >= 100:
        return None
    return valor


def calcular_comision(amount_cents: int, porcentaje: Decimal) -> int:
    """Comisión en céntimos, redondeada al céntimo más cercano."""
    if amount_cents <= 0:
        return 0
    bruto = (Decimal(amount_cents) * porcentaje / Decimal(100)).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    )
    return int(bruto)


def motivo_desactivado(config: dict[str, Any]) -> str:
    """Cadena vacía si el cobro está listo; si no, el motivo para la interfaz."""
    if not clave_valida(config):
        return "el cobro está desactivado: falta STRIPE_SECRET_KEY de pruebas"
    if not (config.get("STRIPE_WEBHOOK_SECRET") or "").strip():
        return "el cobro está desactivado: falta STRIPE_WEBHOOK_SECRET"
    if comision_porcentaje(config) is None:
        return "el cobro está desactivado: falta COMMISSION_PERCENT"
    return ""


def _stripe():
    import stripe

    return stripe


def _cliente(config: dict[str, Any]) -> Any:
    if not clave_valida(config):
        raise ErrorPago("falta STRIPE_SECRET_KEY de pruebas")
    return _stripe()


def crear_cuenta_express(config: dict[str, Any], email: str) -> str:
    """Crea la cuenta conectada express del taller y devuelve su id."""
    stripe = _cliente(config)
    cuenta = stripe.Account.create(
        type="express",
        email=email,
        capabilities={"card_payments": {"requested": True}, "transfers": {"requested": True}},
        settings={"payouts": {"schedule": {"interval": "manual"}}},
    )
    return cuenta["id"]


def enlace_de_alta(
    config: dict[str, Any], cuenta_id: str, retorno: str, refresco: str
) -> str:
    """Enlace al alta de Stripe (KYC, datos bancarios)."""
    stripe = _cliente(config)
    enlace = stripe.AccountLink.create(
        account=cuenta_id,
        refresh_url=refresco,
        return_url=retorno,
        type="account_onboarding",
    )
    return enlace["url"]


def cuenta_lista(config: dict[str, Any], cuenta_id: str) -> bool:
    """True si Stripe ya permite cobrar y transferir a esa cuenta."""
    stripe = _cliente(config)
    cuenta = stripe.Account.retrieve(cuenta_id)
    return bool(cuenta.get("charges_enabled")) and bool(cuenta.get("payouts_enabled"))


def crear_sesion_checkout(
    config: dict[str, Any],
    pedido,
    cuenta_destino: str,
    exito: str,
    cancelado: str,
) -> Any:
    """Sesión de Stripe Checkout alojado con destination charge."""
    porcentaje = comision_porcentaje(config)
    if porcentaje is None:
        raise ErrorPago("falta COMMISSION_PERCENT")
    if pedido.amount_cents <= 0:
        raise ErrorPago("el pedido no tiene importe que cobrar")

    stripe = _cliente(config)
    comision = calcular_comision(pedido.amount_cents, porcentaje)
    return stripe.checkout.Session.create(
        mode="payment",
        line_items=[
            {
                "quantity": 1,
                "price_data": {
                    "currency": (pedido.work.currency or "eur").lower(),
                    "unit_amount": pedido.amount_cents,
                    "product_data": {"name": pedido.work.title},
                },
            }
        ],
        payment_intent_data={
            "application_fee_amount": comision,
            "transfer_data": {"destination": cuenta_destino},
            "metadata": {"pedido_id": str(pedido.id)},
        },
        metadata={"pedido_id": str(pedido.id)},
        success_url=exito,
        cancel_url=cancelado,
    )


def verificar_evento(config: dict[str, Any], cuerpo: bytes, firma: str) -> dict[str, Any]:
    """Valida la firma del webhook. Lanza ErrorPago si no cuadra."""
    secreto = (config.get("STRIPE_WEBHOOK_SECRET") or "").strip()
    if not secreto:
        raise ErrorPago("falta STRIPE_WEBHOOK_SECRET")
    stripe = _stripe()
    try:
        return stripe.Webhook.construct_event(cuerpo, firma, secreto)
    except Exception as error:  # noqa: BLE001 - firma mala o cuerpo manipulado
        raise ErrorPago(f"firma del webhook no válida: {error}") from error


def aplicar_evento(sesion_db, evento: dict[str, Any]) -> str:
    """Aplica un evento ya verificado. Devuelve qué ha hecho, para el log.

    Idempotente: repetir el mismo evento no cambia nada.
    """
    from datetime import datetime, timezone

    from models import Order

    tipo = evento.get("type", "")
    if tipo not in (
        "checkout.session.completed",
        "checkout.session.async_payment_succeeded",
    ):
        return f"ignorado: {tipo}"

    datos = (evento.get("data") or {}).get("object") or {}
    pedido_id = None
    metadatos = datos.get("metadata") or {}
    if metadatos.get("pedido_id"):
        pedido_id = int(metadatos["pedido_id"])
    if pedido_id is None:
        return "ignorado: sin pedido_id"

    pedido = sesion_db.get(Order, pedido_id)
    if pedido is None:
        return f"ignorado: pedido {pedido_id} no existe"

    pago = datos.get("payment_intent")
    if not pago:
        return f"ignorado: pedido {pedido_id} sin payment_intent"

    if pedido.stripe_payment_intent_id == pago and pedido.status == "pagado":
        return f"repetido: pedido {pedido_id} ya estaba pagado"

    pedido.stripe_payment_intent_id = pago
    pedido.stripe_checkout_session_id = datos.get("id") or pedido.stripe_checkout_session_id
    pedido.status = "pagado"
    pedido.paid_at = datetime.now(timezone.utc).replace(tzinfo=None)
    sesion_db.commit()
    registro.info("pedido %s pagado con %s", pedido_id, pago)
    return f"pedido {pedido_id} marcado como pagado"
