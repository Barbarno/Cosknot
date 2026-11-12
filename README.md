# cosknot

cosknot es una aplicación web en una fase inicial para personas que crean y disfrutan del cosplay y de trabajos hechos a mano relacionados con videojuegos, series, anime y otros mundos de ficción.

## dirección actual

cosknot no pretende ser una copia de un marketplace general. En esta primera versión, la idea es ayudar a descubrir creadores, conocer mejor su trabajo y ponerse en contacto con ellos.

## desplegado

- producción: https://cosknot.onrender.com, con health check en `/healthz`.
- plataforma: render en plan free, región frankfurt, con base de datos neon (postgres) en la misma región.
- el servicio se duerme tras 15 min sin tráfico: la primera petición siguiente tarda alrededor de 50 s por el cold start, no es una caída.

## estructura del proyecto

- `app.py`: fábrica de la aplicación flask, rutas públicas y health check.
- `models.py`: modelos sqlalchemy de creadores y obras.
- `seed.py`: datos de ejemplo y especialidades usadas en las plantillas.
- `wsgi.py`: punto de entrada que consume gunicorn en producción.
- `templates/`: plantillas jinja (base, index, creadores, creador, obra y 404).
- `static/`: css y javascript del sitio.
- `tests/`: pruebas con pytest.
- `scripts/`: utilidades de línea de comandos, como la comprobación de la base de datos.
- `docs/cosknot-roadmap.md`: dirección del producto y aspectos técnicos.
- `docs/cosknot-kanban.md`: tablero de trabajo con las tareas pendientes, en proceso, terminadas y aprobadas.
- `docs/context.md`: contexto del proyecto e información del equipo.
- `docs/context/cosknot-css-guide.md`: guía visual y de estilos CSS inicial.
- `docs/decisions/`: decisiones de arquitectura y flujo de trabajo.
- `docs/research/`: investigación con fuentes.
- `docs/deployment.md`: pasos de despliegue en render y neon.
- `docs/troubleshooting/`: problemas, síntomas y soluciones.
- `domains/cosknot.json`: registro de dominio para is-a.dev.
- `render.yaml`: blueprint del servicio en render.
- `requirements.txt`: dependencias de python.

## tecnologías de la primera versión

- python
- flask
- jinja
- html y css
- javascript vanilla
- sqlite para el prototipo local
- pytest
- git y github

antes de añadir funciones nuevas, revisa `docs/cosknot-roadmap.md` y mantén la primera versión centrada en lo esencial: descubrir creadores y permitir el contacto.
