"""Administración: marcar creadores como verificados."""

from __future__ import annotations

from flask import Blueprint, abort, flash, g, redirect, render_template, url_for
from flask_login import current_user, login_required
from sqlalchemy import select

from models import Creator

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.before_request
@login_required
def exigir_admin() -> None:
    if not current_user.is_admin:
        abort(403)


@bp.route("/creadores")
def creadores() -> str:
    filas = g.db.scalars(select(Creator).order_by(Creator.name)).all()
    return render_template("admin_creadores.html", creadores=filas)


@bp.route("/creadores/<int:creador_id>/verificar", methods=["POST"])
def verificar(creador_id: int) -> str:
    creador = g.db.get(Creator, creador_id)
    if creador is None:
        abort(404)
    creador.verified = not creador.verified
    g.db.commit()
    flash(
        f"{creador.name}: {'verificado' if creador.verified else 'sin verificar'}",
        "ok",
    )
    return redirect(url_for("admin.creadores"))
