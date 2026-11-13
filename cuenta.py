"""Panel del usuario: perfil de creador y gestión de sus obras."""

from __future__ import annotations

from flask import Blueprint, abort, flash, g, redirect, render_template, url_for
from flask_login import current_user, login_required
from sqlalchemy import select

from formularios import ObraForm, PerfilForm
from models import Creator, Work
from seguridad import slug_unico, slugify

bp = Blueprint("cuenta", __name__, url_prefix="/cuenta")


@bp.before_request
@login_required
def exigir_sesion() -> None:
    """Todo el panel exige cuenta."""


def _perfil_de(usuario) -> Creator | None:
    return g.db.scalar(select(Creator).where(Creator.user_id == usuario.id))


def _obra_propia(obra_id: int) -> Work:
    obra = g.db.get(Work, obra_id)
    if obra is None:
        abort(404)
    if obra.creator is None or obra.creator.user_id != current_user.id:
        abort(403)
    return obra


@bp.route("/")
def panel() -> str:
    perfil = _perfil_de(current_user)
    obras = list(perfil.works) if perfil else []
    return render_template("cuenta.html", perfil=perfil, obras=obras)


@bp.route("/perfil", methods=["GET", "POST"])
def perfil() -> str:
    if not current_user.is_creator:
        flash("tu cuenta es de comprador; no puedes publicar obras", "aviso")
        return redirect(url_for("cuenta.panel"))

    creador = _perfil_de(current_user)
    form = PerfilForm(obj=creador)
    if form.validate_on_submit():
        if creador is None:
            creador = Creator(
                slug=slug_unico(g.db, Creator, slugify(form.nombre.data)),
                user_id=current_user.id,
                accent=0,
                verified=False,
            )
            g.db.add(creador)
        creador.name = form.nombre.data.strip()
        creador.specialty = form.especialidad.data
        creador.location = form.ubicacion.data.strip()
        creador.bio = form.bio.data.strip()
        creador.contact_email = form.contacto.data.strip()
        g.db.commit()
        flash("perfil guardado", "ok")
        return redirect(url_for("cuenta.panel"))
    return render_template("perfil.html", form=form, creador=creador)


@bp.route("/obras/nueva", methods=["GET", "POST"])
def nueva_obra() -> str:
    creador = _perfil_de(current_user)
    if creador is None:
        flash("crea primero el perfil del taller", "aviso")
        return redirect(url_for("cuenta.perfil"))

    form = ObraForm()
    if form.validate_on_submit():
        obra = Work(
            slug=slug_unico(g.db, Work, slugify(form.titulo.data)),
            creator_id=creador.id,
            title=form.titulo.data.strip(),
            description=form.descripcion.data.strip(),
            price_note=(form.precio_nota.data or "").strip() or None,
            status=form.estado.data,
        )
        g.db.add(obra)
        g.db.commit()
        flash("obra publicada", "ok")
        return redirect(url_for("cuenta.panel"))
    return render_template("obra_form.html", form=form, obra=None)


@bp.route("/obras/<int:obra_id>/editar", methods=["GET", "POST"])
def editar_obra(obra_id: int) -> str:
    obra = _obra_propia(obra_id)
    form = ObraForm(obj=obra)
    if form.validate_on_submit():
        obra.title = form.titulo.data.strip()
        obra.description = form.descripcion.data.strip()
        obra.price_note = (form.precio_nota.data or "").strip() or None
        obra.status = form.estado.data
        g.db.commit()
        flash("obra actualizada", "ok")
        return redirect(url_for("cuenta.panel"))
    return render_template("obra_form.html", form=form, obra=obra)


@bp.route("/obras/<int:obra_id>/borrar", methods=["POST"])
def borrar_obra(obra_id: int) -> str:
    obra = _obra_propia(obra_id)
    g.db.delete(obra)
    g.db.commit()
    flash("obra borrada", "ok")
    return redirect(url_for("cuenta.panel"))
