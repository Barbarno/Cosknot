# cosknot

cosknot es un marketplace de cosplay. Los creadores publican ropa, props, pelucas y
accesorios de cualquier juego, serie o anime, y la gente les compra piezas o les pide
un encargo a medida.

Funcionamos como intermediario entre el creador y el comprador, igual que Etsy o
Airbnb, pero solo de cosplay: el creador pone el taller y el trabajo, nosotros ponemos
el escaparate, la ficha y el contacto. Las cuatro especialidades son ropa, props,
pelucas y accesorios.

Lo hemos hecho nosotros, los tres de 2º de SMR, con Flask y una base de datos:
Daniel Barrasa (CEO y CMO), Jesús Larrazabal (CTO) y Daniel Torres (CFO).

## qué hay hecho

En esta primera versión ya se puede entrar, mirar y escribirle a un creador. Comprar
dentro de la web todavía no: el cobro y la comisión llegan más adelante.

- portada con creadores destacados y obras recientes
- listado de creadores con filtro por especialidad: ropa, props, pelucas y accesorios
- ficha de cada creador con su biografía y sus obras
- ficha de cada obra con precio orientativo, estado y botón de contacto
- contacto directo por correo con el creador para comprar o pedir un encargo
- buscador en `/buscar?q=` que mira en el nombre, la bio, la ciudad y la especialidad
  del creador, y en el título y la descripción de las obras
- página de equipo en `/nosotros`, con quién hace qué y cómo funciona el marketplace
- despliegue en Render con base de datos en Neon, dominio propio y HTTPS
- página 404 propia
- `robots.txt` y `sitemap.xml` generados desde las rutas
- `healthz` para comprobar que la base de datos responde

El filtro sale de las cuatro especialidades del catálogo: ropa, props, pelucas y
accesorios. Los creadores que aparecen en la web están verificados: son los que han
pasado por el equipo antes de publicar.

El diseño sigue el patrón de los marketplaces grandes: buscador en la cabecera, barra
de categorías debajo, rejilla de tarjetas cuadradas para las piezas, listado con los
filtros en la barra lateral y ficha de obra a dos columnas. La idea es que la web se
lea como una tienda y no como una página de presentación.

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
