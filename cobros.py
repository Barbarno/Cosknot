"""Rutas de cobro: alta en Stripe del taller, pago del pedido y webhook."""

from __future__ import annotations

from flask import (
    Blueprint,
    current_app,
    flash,
    g,
    jsonify,
    redirect,
    request,
    url_for,
)
from flask_login import current_user, login_required

import pagos
from estados_pedido import rol_en_pedido
from extensiones import csrf
from models import Creator, Order
from sqlalchemy import select

bp = Blueprint("cobros", __name__)


@bp.route("/cuenta/stripe/alta", methods=["POST"])
@login_required
def alta_stripe() -> str:
    motivo = pagos.motivo_desactivado(current_app.config)
    if motivo:
        flash(motivo, "aviso")
        return redirect(url_for("cuenta.panel"))

    creador = g.db.scalar(select(Creator).where(Creator.user_id == current_user.id))
    if creador is None:
        flash("crea primero el perfil del taller", "aviso")
        return redirect(url_for("cuenta.perfil"))

    try:
        if not creador.stripe_account_id:
            creador.stripe_account_id = pagos.crear_cuenta_express(
                current_app.config, current_user.email
            )
            g.db.commit()
        enlace = pagos.enlace_de_alta(
            current_app.config,
            creador.stripe_account_id,
            url_for("cobros.retorno_stripe", _external=True),
            url_for("cobros.retorno_stripe", _external=True),
        )
    except pagos.ErrorPago as error:
        flash(str(error), "error")
        return redirect(url_for("cuenta.panel"))
    except Exception as error:  # noqa: BLE001 - Stripe caído no rompe el panel
        current_app.logger.warning("alta de stripe falló: %s", error)
        flash("Stripe no ha contestado; inténtalo en un rato", "error")
        return redirect(url_for("cuenta.panel"))

    return redirect(enlace, code=303)


@bp.route("/cuenta/stripe/retorno")
@login_required
def retorno_stripe() -> str:
    creador = g.db.scalar(select(Creator).where(Creator.user_id == current_user.id))
    if creador is None or not creador.stripe_account_id:
        flash("no hay cuenta de cobro que revisar", "aviso")
        return redirect(url_for("cuenta.panel"))

    try:
        lista = pagos.cuenta_lista(current_app.config, creador.stripe_account_id)
    except Exception as error:  # noqa: BLE001
        current_app.logger.warning("consulta de cuenta stripe falló: %s", error)
        flash("no se ha podido comprobar la cuenta de cobro", "error")
        return redirect(url_for("cuenta.panel"))

    creador.stripe_onboarding_ok = lista
    g.db.commit()
    if lista:
        flash("cuenta de cobro lista: ya puedes recibir pagos", "ok")
    else:
        flash("Stripe aún no ha validado los datos; vuelve a entrar en un rato", "aviso")
    return redirect(url_for("cuenta.panel"))


@bp.route("/pedidos/<int:pedido_id>/pagar", methods=["POST"])
@login_required
def pagar(pedido_id: int) -> str:
    pedido = g.db.get(Order, pedido_id)
    if pedido is None:
        flash("ese pedido no existe", "error")
        return redirect(url_for("pedidos.lista"))
    if rol_en_pedido(pedido, current_user) != "comprador":
        flash("solo el comprador paga este pedido", "error")
        return redirect(url_for("pedidos.detalle", pedido_id=pedido.id))
    if pedido.status != "aceptado":
        flash("el pedido tiene que estar aceptado antes de pagar", "aviso")
        return redirect(url_for("pedidos.detalle", pedido_id=pedido.id))

    motivo = pagos.motivo_desactivado(current_app.config)
    if motivo:
        flash(motivo, "aviso")
        return redirect(url_for("pedidos.detalle", pedido_id=pedido.id))

    creador = pedido.work.creator
    if creador is None or not creador.stripe_account_id or not creador.stripe_onboarding_ok:
        flash("el taller todavía no tiene la cuenta de cobro lista", "aviso")
        return redirect(url_for("pedidos.detalle", pedido_id=pedido.id))

    try:
        sesion = pagos.crear_sesion_checkout(
            current_app.config,
            pedido,
            creador.stripe_account_id,
            url_for("cobros.vuelta_pago", pedido_id=pedido.id, _external=True),
            url_for("pedidos.detalle", pedido_id=pedido.id, _external=True),
        )
    except pagos.ErrorPago as error:
        flash(str(error), "error")
        return redirect(url_for("pedidos.detalle", pedido_id=pedido.id))
    except Exception as error:  # noqa: BLE001
        current_app.logger.warning("checkout de stripe falló: %s", error)
        flash("Stripe no ha contestado; inténtalo en un rato", "error")
        return redirect(url_for("pedidos.detalle", pedido_id=pedido.id))

    pedido.stripe_checkout_session_id = sesion["id"]
    g.db.commit()
    # 303: el navegador cambia a GET y va a checkout.stripe.com. Por eso
    # form-action lleva ese origen exacto y no un comodín.
    return redirect(sesion["url"], code=303)


@bp.route("/pedidos/<int:pedido_id>/pago/vuelta")
@login_required
def vuelta_pago(pedido_id: int) -> str:
    pedido = g.db.get(Order, pedido_id)
    if pedido is None:
        return redirect(url_for("pedidos.lista"))
    if pedido.status == "pagado":
        flash("pago recibido", "ok")
    else:
        flash("el pago se está confirmando; el pedido se actualiza solo", "aviso")
    return redirect(url_for("pedidos.detalle", pedido_id=pedido.id))


@bp.route("/stripe/webhook", methods=["POST"])
@csrf.exempt
def webhook():
    cuerpo = request.get_data()
    firma = request.headers.get("Stripe-Signature", "")
    try:
        evento = pagos.verificar_evento(current_app.config, cuerpo, firma)
    except pagos.ErrorPago as error:
        current_app.logger.warning("webhook rechazado: %s", error)
        return jsonify({"error": "firma no válida"}), 400

    resultado = pagos.aplicar_evento(g.db, evento)
    current_app.logger.info("webhook: %s", resultado)
    return jsonify({"recibido": True, "resultado": resultado}), 200
