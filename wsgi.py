"""Arranque del proceso web: gunicorn importa `wsgi:app`.

El hilo de reintento de avisos se arranca solo en producción y solo aquí, no en
`create_app`: en las pruebas no debe correr nada en segundo plano, y en local el
correo va por consola. `iniciar_hilo` es idempotente, así que un import repetido
no crea un segundo hilo.
"""

from app import app, es_produccion
from outbox import iniciar_hilo

if es_produccion():
    iniciar_hilo(app)

application = app
