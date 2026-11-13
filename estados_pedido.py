"""Máquina de estados de un pedido.

Las transiciones viven aquí y no en las plantillas: la plantilla solo pregunta
qué botones pintar con `transiciones_disponibles()`; el cambio real pasa por
`cambiar_estado()`, que vuelve a comprobarlo todo.
"""

from __future__ import annotations

ESTADOS = (
    "solicitado",
    "aceptado",
    "pagado",
    "enviado",
    "completado",
    "cancelado",
)

# A dónde puede ir cada estado.
TRANSICIONES: dict[str, frozenset[str]] = {
    "solicitado": frozenset({"aceptado", "cancelado"}),
    "aceptado": frozenset({"pagado", "cancelado"}),
    "pagado": frozenset({"enviado", "cancelado"}),
    "enviado": frozenset({"completado"}),
    "completado": frozenset(),
    "cancelado": frozenset(),
}

# Qué rol puede provocar cada transición. `admin` puede todas.
ACCIONES: dict[str, frozenset[str]] = {
    "aceptado": frozenset({"creador"}),
    "pagado": frozenset({"creador", "sistema"}),
    "enviado": frozenset({"creador"}),
    "completado": frozenset({"comprador"}),
    "cancelado": frozenset({"comprador", "creador"}),
}


class TransicionInvalida(ValueError):
    """El estado pedido no está permitido para este pedido y este usuario."""


def rol_en_pedido(pedido, usuario) -> str | None:
    """Devuelve `comprador`, `creador`, `admin` o `None` si no participa."""
    if usuario is None or not getattr(usuario, "is_authenticated", False):
        return None
    if getattr(usuario, "role", None) == "admin":
        return "admin"
    if pedido.buyer_id == usuario.id:
        return "comprador"
    creador = pedido.work.creator if pedido.work is not None else None
    if creador is not None and creador.user_id == usuario.id:
        return "creador"
    return None


def transiciones_disponibles(pedido, usuario) -> list[str]:
    rol = rol_en_pedido(pedido, usuario)
    if rol is None:
        return []
    disponibles = []
    for destino in sorted(TRANSICIONES.get(pedido.status, frozenset())):
        if rol == "admin" or rol in ACCIONES.get(destino, frozenset()):
            disponibles.append(destino)
    return disponibles


def cambiar_estado(pedido, nuevo_estado: str, usuario) -> None:
    if nuevo_estado not in ESTADOS:
        raise TransicionInvalida(f"estado desconocido: {nuevo_estado}")
    if nuevo_estado not in TRANSICIONES.get(pedido.status, frozenset()):
        raise TransicionInvalida(
            f"no se puede pasar de {pedido.status} a {nuevo_estado}"
        )
    rol = rol_en_pedido(pedido, usuario)
    if rol is None:
        raise TransicionInvalida("no participas en este pedido")
    if rol != "admin" and rol not in ACCIONES.get(nuevo_estado, frozenset()):
        raise TransicionInvalida(f"el rol {rol} no puede dejar el pedido en {nuevo_estado}")
    pedido.status = nuevo_estado
