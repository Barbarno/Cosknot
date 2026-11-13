"""Textos de los avisos por correo de un pedido.

Cada función devuelve `(destinatario, asunto, texto)` y no envía nada: el envío lo
hace `correo.enviar()`. Así el texto se puede probar sin tocar la red y la ruta
decide si el aviso va en un hilo o no.
"""

from __future__ import annotations

from flask import url_for

from importes import formato_importe
from models import Order, OrderMessage


def _correo_del_taller(pedido: Order) -> str:
    creador = pedido.work.creator
    if creador is None:
        return ""
    if creador.user is not None and creador.user.email:
        return creador.user.email
    return creador.contact_email or ""


def _enlace(pedido: Order) -> str:
    return url_for("pedidos.detalle", pedido_id=pedido.id, _external=True)


def _resumen(pedido: Order) -> str:
    obra = pedido.work
    taller = obra.creator.name if obra.creator else "el taller"
    return (
        f"obra: {obra.title}\n"
        f"taller: {taller}\n"
        f"estado: {pedido.status}\n"
        f"importe: {formato_importe(pedido.amount_cents, obra.currency)}\n"
        f"pedido: {_enlace(pedido)}\n"
    )


def nuevo_pedido(pedido: Order) -> tuple[str, str, str]:
    para = _correo_del_taller(pedido)
    asunto = f"nuevo encargo: {pedido.work.title}"
    texto = (
        f"tienes un encargo nuevo de {pedido.buyer.email}.\n\n"
        + _resumen(pedido)
        + "\nentra en la web para aceptarlo o preguntar lo que falte."
    )
    return para, asunto, texto


def cambio_de_estado(
    pedido: Order, anterior: str, autor_email: str
) -> tuple[str, str, str]:
    # Se avisa a la otra parte: si el cambio lo hizo el comprador, se entera el
    # taller, y al revés.
    if autor_email == pedido.buyer.email:
        para = _correo_del_taller(pedido)
    else:
        para = pedido.buyer.email
    asunto = f"pedido #{pedido.id}: {anterior} -> {pedido.status}"
    texto = (
        f"{autor_email} ha dejado el pedido en «{pedido.status}».\n\n"
        + _resumen(pedido)
        + "\nentra en la web para seguir con el encargo."
    )
    return para, asunto, texto


def mensaje_nuevo(
    pedido: Order, mensaje: OrderMessage, autor_email: str
) -> tuple[str, str, str]:
    if autor_email == pedido.buyer.email:
        para = _correo_del_taller(pedido)
    else:
        para = pedido.buyer.email
    asunto = f"pedido #{pedido.id}: mensaje nuevo"
    texto = (
        f"{autor_email} ha escrito en el pedido de «{pedido.work.title}»:\n\n"
        f"{mensaje.body}\n\n"
        f"responde en {_enlace(pedido)}"
    )
    return para, asunto, texto
