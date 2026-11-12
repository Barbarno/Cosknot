# cosknot

cosknot es una aplicación web en una fase inicial para personas que crean y disfrutan del cosplay y de trabajos hechos a mano relacionados con videojuegos, series, anime y otros mundos de ficción.

## dirección actual

cosknot no pretende ser una copia de un marketplace general. En esta primera versión, la idea es ayudar a descubrir creadores, conocer mejor su trabajo y ponerse en contacto con ellos.

## desplegado

- producción: https://cosknot.duckdns.org, con health check en `/healthz`.
- dominio: subdominio gratuito de DuckDNS, apunta a render con un registro **A** a `216.24.57.1` (el ingress de render); DuckDNS no admite CNAME en este caso porque el nombre es apex para la PSL.
- servicio: https://cosknot.onrender.com sigue activo como URL del servicio, y es la que usan los workflows de CI para sondear `/healthz`.
- plataforma: render en plan free, región frankfurt, con base de datos neon (postgres) en la misma región.
- el servicio se duerme tras 15 min sin tráfico: la primera petición siguiente tarda alrededor de 50 s por el cold start, no es una caída.

## ejecutar en local

requisitos: python 3.13 y powershell en windows. los comandos se ejecutan desde la raíz del repositorio.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m flask --app app run --debug
```

el servidor queda en http://127.0.0.1:5000.

pruebas:

```powershell
.venv\Scripts\python -m pytest -q
```

sin `DATABASE_URL` en el entorno se usa sqlite en `cosknot.db` (creado en la raíz del repositorio). la primera ejecución crea las tablas con `Base.metadata.create_all` y siembra el catálogo de ejemplo; las siguientes no duplican datos porque la siembra solo actúa si la tabla `creators` está vacía. para apuntar a neon, copia `.env.example` a `.env` y rellena `DATABASE_URL`; el comando `flask run` carga ese fichero.

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
- `docs/backups.md`: copias de seguridad y restauración de la base de datos.
- `docs/data-model.md`: modelo de datos inicial (tablas, columnas, reglas y carencias).
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
