"""Extensiones de Flask compartidas por los blueprints."""

from __future__ import annotations

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_wtf import CSRFProtect

csrf = CSRFProtect()

# El almacenamiento se decide en `create_app` con la config RATELIMIT_STORAGE_URI
# (por defecto memory://). En Heroku no hay Redis: el contador vive en la memoria
# del único proceso web, es exacto mientras haya un worker y se pierde cuando el
# dyno se reinicia o cambia de máquina. Está anotado en docs/decisions/0003.
limiter = Limiter(key_func=get_remote_address)


login_manager = LoginManager()
login_manager.login_view = "auth.entrar"
login_manager.login_message = "entra con tu cuenta para continuar"
login_manager.login_message_category = "aviso"
