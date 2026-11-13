"""Formularios de la web. Todos pasan por CSRF de Flask-WTF."""

from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import (
    PasswordField,
    RadioField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.fields.choices import SelectChoice
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional

from estados_pedido import ESTADOS as ESTADOS_PEDIDO
from seed import SPECIALTIES

ESTADOS_OBRA = ("disponible", "encargo", "agotado")


class RegistroForm(FlaskForm):
    email = StringField(
        "correo", validators=[DataRequired(), Email(), Length(max=200)]
    )
    password = PasswordField(
        "contraseña",
        validators=[DataRequired(), Length(min=8, max=128)],
    )
    confirmar = PasswordField(
        "repite la contraseña",
        validators=[
            DataRequired(),
            EqualTo("password", message="las contraseñas no coinciden"),
        ],
    )
    rol = RadioField(
        "quiero",
        choices=[SelectChoice("comprador", "comprar"), SelectChoice("creador", "vender")],
        default="comprador",
    )
    enviar = SubmitField("crear cuenta")


class EntrarForm(FlaskForm):
    email = StringField("correo", validators=[DataRequired(), Email(), Length(max=200)])
    password = PasswordField("contraseña", validators=[DataRequired(), Length(max=128)])
    enviar = SubmitField("entrar")


class PerfilForm(FlaskForm):
    nombre = StringField("nombre del taller", validators=[DataRequired(), Length(max=120)])
    especialidad = SelectField(
        "especialidad",
        choices=[SelectChoice(s, s) for s in SPECIALTIES],
        validators=[DataRequired()],
    )
    ubicacion = StringField("ciudad y país", validators=[DataRequired(), Length(max=120)])
    bio = TextAreaField("bio", validators=[DataRequired(), Length(max=4000)])
    contacto = StringField(
        "correo de contacto", validators=[DataRequired(), Email(), Length(max=200)]
    )
    enviar = SubmitField("guardar perfil")


class ObraForm(FlaskForm):
    titulo = StringField("título", validators=[DataRequired(), Length(max=160)])
    descripcion = TextAreaField(
        "descripción", validators=[DataRequired(), Length(max=8000)]
    )
    precio_nota = StringField(
        "precio orientativo (texto libre)", validators=[Optional(), Length(max=80)]
    )
    precio_euros = StringField(
        "precio en euros (para poder cobrar con tarjeta)",
        validators=[Optional(), Length(max=12)],
    )
    estado = SelectField(
        "estado",
        choices=[SelectChoice(e, e) for e in ESTADOS_OBRA],
        validators=[DataRequired()],
    )
    enviar = SubmitField("guardar obra")


class PedidoForm(FlaskForm):
    mensaje = TextAreaField(
        "cuéntale qué necesitas",
        validators=[DataRequired(), Length(max=4000)],
    )
    enviar = SubmitField("hacer el encargo")


class MensajeForm(FlaskForm):
    cuerpo = TextAreaField("mensaje", validators=[DataRequired(), Length(max=4000)])
    enviar = SubmitField("enviar")


class EstadoForm(FlaskForm):
    estado = SelectField(
        "nuevo estado", choices=[SelectChoice(e, e) for e in ESTADOS_PEDIDO]
    )
    enviar = SubmitField("cambiar")
