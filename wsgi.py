"""punto de entrada para gunicorn en render: `gunicorn wsgi:app`."""

from app import app

application = app
