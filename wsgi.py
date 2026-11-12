"""Punto de entrada para gunicorn en Render: `gunicorn wsgi:app`."""

from app import app

application = app
