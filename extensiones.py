"""Extensiones de Flask compartidas por los blueprints."""

from __future__ import annotations

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_wtf import CSRFProtect

csrf = CSRFProtect()

# Almacenamiento en memoria a propósito: con dos workers de gunicorn el límite
# es por proceso, así que el cupo real es el doble. Está anotado en
# docs/decisions/0002-decisiones-marketplace.md; para un límite exacto haría
# falta un backend compartido (Redis) y el plan free de Render no lo incluye.
limiter = Limiter(key_func=get_remote_address, storage_uri="memory://")

login_manager = LoginManager()
login_manager.login_view = "auth.entrar"
login_manager.login_message = "entra con tu cuenta para continuar"
login_manager.login_message_category = "aviso"
