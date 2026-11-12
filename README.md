# cosknot

cosknot es una web para encontrar gente que hace cosplay (ropa, props y accesorios) y
poder escribirle directamente, sin intermediarios. Es el proyecto del módulo de 2º de
SMR, hecho con Flask y una base de datos.

La idea no es copiar un marketplace enorme. De momento la web sirve para tres cosas:
descubrir creadores, ver su trabajo y contactar con ellos por correo.

## qué hay hecho

- portada con creadores destacados y obras recientes
- listado de creadores con filtro por especialidad
- ficha de cada creador con su biografía y sus obras
- ficha de cada obra con precio orientativo, estado y botón de contacto
- página 404 propia
- `robots.txt` y `sitemap.xml` generados desde las rutas
- `healthz` para comprobar que la base de datos responde

## arrancarlo en local

Necesitas Python 3.13 y PowerShell en Windows. Los comandos se lanzan desde la raíz
del repositorio.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m flask --app app run --debug
```

Luego abres http://127.0.0.1:5000.

Si no hay `DATABASE_URL` en el entorno, la app usa SQLite en `cosknot.db`, que se crea
sola la primera vez. También se rellena el catálogo de ejemplo, pero solo si la tabla
`creators` está vacía, así que reiniciar no duplica nada.

Para usar Neon en vez de SQLite, copia `.env.example` a `.env`, rellena `DATABASE_URL`
y arranca igual.

## pruebas

```powershell
.venv\Scripts\python -m pytest -q
```

Son pruebas con el cliente de Flask y una base de datos temporal, así que no tocan
`cosknot.db`.

## estructura

- `app.py`: crea la app, las rutas públicas y el health check.
- `models.py`: los dos modelos de SQLAlchemy, creadores y obras.
- `seed.py`: catálogo de ejemplo y lista de especialidades.
- `wsgi.py`: lo que usa gunicorn en producción.
- `templates/`: plantillas de Jinja.
- `static/`: CSS y el JavaScript del filtro.
- `tests/`: pruebas con pytest.
- `scripts/check_db.py`: comprueba que la base de datos de producción responde.
- `docs/`: apuntes del proyecto (contexto, despliegue, modelo de datos...).

## despliegue

Está desplegado en Render con una base de datos gratuita de Neon:

- producción: https://cosknot.duckdns.org (health check en `/healthz`)
- servicio: https://cosknot.onrender.com

El plan free duerme el servicio a los 15 minutos sin tráfico. La primera visita
después tarda unos 50 segundos, no es que esté caído.

Los pasos completos están en `docs/deployment.md`.

## tecnologías

Python, Flask, Jinja, SQLAlchemy, SQLite en local y PostgreSQL (Neon) en producción,
gunicorn, pytest, GitHub Actions y Render.
