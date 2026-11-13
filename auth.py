"""Registro, entrada y salida de cuentas."""

from __future__ import annotations

from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from sqlalchemy import select

from extensiones import limiter
from formularios import EntrarForm, RegistroForm
from models import User
from seguridad import hash_password, necesita_rehash, normalizar_email, verificar_password

bp = Blueprint("auth", __name__)


def _destino_seguro(destino: str | None) -> str:
    """Solo se acepta un destino interno: nada de redirigir fuera del dominio."""
    if destino and destino.startswith("/") and not destino.startswith("//"):
        return destino
    return url_for("cuenta.panel")


@bp.route("/registro", methods=["GET", "POST"])
@limiter.limit("10 per hour", methods=["POST"])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for("cuenta.panel"))
    form = RegistroForm()
    if form.validate_on_submit():
        email = normalizar_email(form.email.data)
        if g.db.scalar(select(User).where(User.email == email)) is not None:
            flash("ya hay una cuenta con ese correo", "error")
            return render_template("registro.html", form=form), 400
        rol = form.rol.data if form.rol.data in ("comprador", "creador") else "comprador"
        usuario = User(
            email=email,
            password_hash=hash_password(form.password.data),
            role=rol,
        )
        g.db.add(usuario)
        g.db.commit()
        login_user(usuario)
        flash("cuenta creada", "ok")
        return redirect(url_for("cuenta.panel"))
    return render_template("registro.html", form=form)


@bp.route("/entrar", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def entrar():
    if current_user.is_authenticated:
        return redirect(url_for("cuenta.panel"))
    form = EntrarForm()
    if form.validate_on_submit():
        email = normalizar_email(form.email.data)
        usuario = g.db.scalar(select(User).where(User.email == email))
        # Se verifica siempre, exista o no la cuenta, para no filtrar por tiempo
        # de respuesta qué correos están registrados.
        if usuario is None or not verificar_password(
            usuario.password_hash, form.password.data
        ):
            flash("correo o contraseña incorrectos", "error")
            return render_template("entrar.html", form=form), 401
        if necesita_rehash(usuario.password_hash):
            usuario.password_hash = hash_password(form.password.data)
            g.db.commit()
        login_user(usuario)
        return redirect(_destino_seguro(request.args.get("next")))
    return render_template("entrar.html", form=form)


@bp.route("/salir", methods=["POST"])
def salir():
    logout_user()
    flash("sesión cerrada", "ok")
    return redirect(url_for("index"))
