"""Panel del usuario: perfil de creador y gestión de sus obras."""

from __future__ import annotations

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import select

from extensiones import limiter
from formularios import ObraForm, PerfilForm
from importes import euros_a_centimos
from models import Creator, Work
from seguridad import slug_unico, slugify
from sugerencias import SugerenciaError

bp = Blueprint("cuenta", __name__, url_prefix="/cuenta")


def _guardar_imagen(archivo, entidad) -> bool:
    """Valida y sube la foto de una obra o un taller. Devuelve si hubo cambio."""
    from flask import current_app

    from almacenamiento import ErrorImagen, clave_nueva, validar_imagen

    if archivo is None or not getattr(archivo, "filename", ""):
        return False
    almacen = current_app.extensions.get("almacen")
    if almacen is None:
        flash(
            "las subidas están desactivadas en este entorno: "
            + (current_app.extensions.get("almacen_motivo") or "falta configuración"),
            "aviso",
        )
        return False

    datos = archivo.read()
    try:
        extension = validar_imagen(
            archivo.filename,
            archivo.mimetype,
            datos,
            int(current_app.config.get("MAX_IMAGE_BYTES") or 5 * 1024 * 1024),
        )
    except ErrorImagen as error:
        flash(str(error), "error")
        return False

    anterior = entidad.image_key
    clave = clave_nueva(extension)
    almacen.guardar(clave, datos, archivo.mimetype)
    entidad.image_key = clave
    if anterior:
        almacen.borrar(anterior)
    return True


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
            price_cents=euros_a_centimos(form.precio_euros.data),
            currency="EUR",
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
    if request.method == "GET":
        form.precio_euros.data = (
            f"{obra.price_cents / 100:.2f}" if obra.price_cents else ""
        )
    if form.validate_on_submit():
        obra.title = form.titulo.data.strip()
        obra.description = form.descripcion.data.strip()
        obra.price_note = (form.precio_nota.data or "").strip() or None
        obra.price_cents = euros_a_centimos(form.precio_euros.data)
        obra.status = form.estado.data
        g.db.commit()
        flash("obra actualizada", "ok")
        return redirect(url_for("cuenta.panel"))
    return render_template("obra_form.html", form=form, obra=obra)


@bp.route("/obras/sugerencias", methods=["POST"])
@limiter.limit("10 per hour", methods=["POST"])
def sugerir_ficha():
    """Propone título, descripción y etiquetas a partir de la foto elegida.

    La petición es del usuario y va dentro de la petición HTTP, con timeout corto.
    Sin clave configurada el botón no aparece y aquí se responde 404.
    """
    sugeridor = current_app.extensions.get("sugeridor")
    if sugeridor is None or not sugeridor.activo:
        return jsonify({"error": "las sugerencias están desactivadas"}), 404

    archivo = request.files.get("foto")
    if archivo is None or not getattr(archivo, "filename", ""):
        return jsonify({"error": "elige una foto primero"}), 400

    from almacenamiento import ErrorImagen, validar_imagen

    datos = archivo.read()
    try:
        validar_imagen(
            archivo.filename,
            archivo.mimetype,
            datos,
            int(current_app.config.get("MAX_IMAGE_BYTES") or 5 * 1024 * 1024),
        )
    except ErrorImagen as error:
        return jsonify({"error": str(error)}), 400

    mime = (archivo.mimetype or "").split(";")[0].strip().lower()
    pista = (request.form.get("pista") or "").strip()

    try:
        resultado = sugeridor.sugerir(datos, mime, pista)
    except SugerenciaError as error:
        codigo = 429 if error.codigo == "cuota" else 502
        return jsonify({"error": error.mensaje, "codigo": error.codigo}), codigo

    return jsonify({"sugerencia": resultado})


@bp.route("/obras/<int:obra_id>/borrar", methods=["POST"])
def borrar_obra(obra_id: int) -> str:
    obra = _obra_propia(obra_id)
    g.db.delete(obra)
    g.db.commit()
    flash("obra borrada", "ok")
    return redirect(url_for("cuenta.panel"))


@bp.route("/perfil/foto", methods=["POST"])
def subir_foto_perfil() -> str:
    creador = _perfil_de(current_user)
    if creador is None:
        flash("crea primero el perfil del taller", "aviso")
        return redirect(url_for("cuenta.perfil"))
    if _guardar_imagen(request.files.get("foto"), creador):
        g.db.commit()
        flash("foto del taller actualizada", "ok")
    return redirect(url_for("cuenta.perfil"))


@bp.route("/obras/<int:obra_id>/foto", methods=["POST"])
def subir_foto_obra(obra_id: int) -> str:
    obra = _obra_propia(obra_id)
    if _guardar_imagen(request.files.get("foto"), obra):
        g.db.commit()
        flash("foto de la obra actualizada", "ok")
    return redirect(url_for("cuenta.editar_obra", obra_id=obra.id))
