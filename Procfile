# Despliegue en Heroku. Ver docs/deployment.md.
#
# `release` corre una sola vez por despliegue, antes de que el dyno nuevo reciba
# tráfico. Si `alembic upgrade head` falla, Heroku aborta el despliegue y la
# versión anterior sigue sirviendo: no hay ventana con el esquema a medias.
release: alembic upgrade head

# Un solo worker con 4 hilos, a propósito:
#   - el límite de intentos vive en memoria del proceso, así que con 2 workers
#     cada uno llevaría su propia cuenta y el cupo real sería el doble;
#   - 1 worker son ~2 procesos menos en 512 MB de RAM, que es el techo del dyno
#     Basic y el recurso más escaso del plan.
# `--timeout 50` mata al worker colgado; el router de Heroku corta antes la espera
# de la primera respuesta (30 s), así que este timeout es la red de seguridad del
# proceso, no la del cliente. `--max-requests` recicla el proceso para que una
# fuga de memoria no tumbe el dyno a mitad de semana. `--preload` está prohibido:
# el hilo de la bandeja de correo arrancaría en el master antes del fork y se
# duplicaría.
web: gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 50 --graceful-timeout 25 --keep-alive 5 --max-requests 1000 --max-requests-jitter 100 --access-logfile - --error-logfile -
