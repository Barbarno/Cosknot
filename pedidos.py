"""Pedidos y mensajes entre comprador y creador."""

from __future__ import annotations

from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, url_for
from flask_login import current_user, login_required
from sqlalchemy import select

import avisos
from correo import enviar
from estados_pedido import TransicionInvalida, cambiar_estado, rol_en_pedido, transiciones_disponibles
from formularios import EstadoForm, MensajeForm, PedidoForm
from models import Creator, Order, OrderMessage, Work

bp = Blueprint("pedidos", __name__, url_prefix="/pedidos")


def _avisar(para: str, asunto: str, texto: str) -> None:
    """Un aviso que falla no puede tumbar el pedido: `enviar` ya se traga el error."""
    correo = current_app.extensions.get("correo")
    if correo is None or not para:
        return
    enviar(
        correo,
        para,
        asunto,
        texto,
        sincrono=not bool(current_app.config.get("EMAIL_ASYNC")),
    )



@bp.before_request
@login_required
def exigir_sesion() -> None:
    """Nadie sin cuenta ve pedidos."""


def _pedido_accesible(pedido_id: int) -> Order:
    pedido = g.db.get(Order, pedido_id)
    if pedido is None:
        abort(404)
    if rol_en_pedido(pedido, current_user) is None:
        abort(403)
    return pedido


@bp.route("/")
def lista() -> str:
    compras = list(
        g.db.scalars(
            select(Order)
            .where(Order.buyer_id == current_user.id)
            .order_by(Order.id.desc())
        ).all()
    )
    ventas = list(
        g.db.scalars(
            select(Order)
            .join(Work, Order.work_id == Work.id)
            .join(Creator, Work.creator_id == Creator.id)
            .where(Creator.user_id == current_user.id)
            .order_by(Order.id.desc())
        ).all()
    )
    return render_template("pedidos.html", compras=compras, ventas=ventas)


@bp.route("/nuevo/<slug>", methods=["POST"])
def nuevo(slug: str) -> str:
    obra = g.db.scalar(select(Work).where(Work.slug == slug))
    if obra is None:
        abort(404)
    if obra.creator.user_id == current_user.id:
        flash("no puedes encargarte tu propia obra", "aviso")
        return redirect(url_for("work_detail", slug=obra.slug))

    form = PedidoForm()
    if not form.validate_on_submit():
        flash("escribe qué necesitas para hacer el encargo", "error")
        return redirect(url_for("work_detail", slug=obra.slug))

    pedido = Order(
        buyer_id=current_user.id,
        work_id=obra.id,
        status="solicitado",
        amount_cents=obra.price_cents or 0,
        application_fee_cents=0,
    )
    g.db.add(pedido)
    g.db.flush()
    g.db.add(
        OrderMessage(
            order_id=pedido.id,
            author_id=current_user.id,
            body=form.mensaje.data.strip(),
        )
    )
    g.db.commit()
    _avisar(*avisos.nuevo_pedido(pedido))
    flash("encargo enviado al taller", "ok")
    return redirect(url_for("pedidos.detalle", pedido_id=pedido.id))


@bp.route("/<int:pedido_id>")
def detalle(pedido_id: int) -> str:
    pedido = _pedido_accesible(pedido_id)
    return render_template(
        "pedido.html",
        pedido=pedido,
        mensaje_form=MensajeForm(),
        estado_form=EstadoForm(),
        transiciones=transiciones_disponibles(pedido, current_user),
        rol=rol_en_pedido(pedido, current_user),
    )


@bp.route("/<int:pedido_id>/estado", methods=["POST"])
def estado(pedido_id: int) -> str:
    pedido = _pedido_accesible(pedido_id)
    form = EstadoForm()
    if not form.validate_on_submit():
        flash("estado no válido", "error")
        return redirect(url_for("pedidos.detalle", pedido_id=pedido.id))
    anterior = pedido.status
    try:
        cambiar_estado(pedido, form.estado.data, current_user)
    except TransicionInvalida as error:
        flash(str(error), "error")
        return redirect(url_for("pedidos.detalle", pedido_id=pedido.id))
    g.db.commit()
    _avisar(*avisos.cambio_de_estado(pedido, anterior, current_user.email))
    flash(f"el pedido pasa a {pedido.status}", "ok")
    return redirect(url_for("pedidos.detalle", pedido_id=pedido.id))


@bp.route("/<int:pedido_id>/mensajes", methods=["POST"])
def mensaje(pedido_id: int) -> str:
    pedido = _pedido_accesible(pedido_id)
    form = MensajeForm()
    if not form.validate_on_submit():
        flash("el mensaje está vacío", "error")
        return redirect(url_for("pedidos.detalle", pedido_id=pedido.id))
    nuevo_mensaje = OrderMessage(
        order_id=pedido.id,
        author_id=current_user.id,
        body=form.cuerpo.data.strip(),
    )
    g.db.add(nuevo_mensaje)
    g.db.commit()
    _avisar(*avisos.mensaje_nuevo(pedido, nuevo_mensaje, current_user.email))
    return redirect(url_for("pedidos.detalle", pedido_id=pedido.id))
