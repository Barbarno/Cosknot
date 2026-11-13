# modelo de datos

cosknot es un marketplace de cosplay: un creador publica ropa, props, pelucas y
accesorios, y un comprador los mira, los compra o pide un encargo. De momento el modelo
solo guarda el escaparate, que son las dos tablas de abajo. Compras, encargos y pagos
todavía no tienen tabla.

Hay dos tablas, definidas en `models.py` con SQLAlchemy 2.x. No hay más tablas ni
migraciones.

El esquema se crea al arrancar con `Base.metadata.create_all(engine)` dentro de
`create_app()`. En local el motor es SQLite (`sqlite:///cosknot.db`); en producción,
PostgreSQL en Neon.

## tabla `creators`

| columna | tipo | nulo | clave o índice | qué es |
|---|---|---|---|---|
| `id` | INTEGER | no | clave primaria | identificador interno |
| `slug` | VARCHAR(120) | no | único e indexado | parte de la URL (`/creadores/<slug>`) |
| `name` | VARCHAR(120) | no | | nombre público |
| `specialty` | VARCHAR(40) | no | indexado | especialidad, texto libre |
| `location` | VARCHAR(120) | no | | ciudad y país |
| `bio` | TEXT | no | | descripción del taller |
| `contact_email` | VARCHAR(200) | no | | correo que sale en el `mailto:` |
| `accent` | INTEGER | no | | número de paleta visual, por defecto 0 |
| `verified` | BOOLEAN | no | | creador revisado por el equipo; sale la marca de verificado |
| `created_at` | DATETIME | no | | fecha de alta, la pone el servidor |

## tabla `works`

| columna | tipo | nulo | clave o índice | qué es |
|---|---|---|---|---|
| `id` | INTEGER | no | clave primaria | identificador interno |
| `slug` | VARCHAR(140) | no | único e indexado | parte de la URL (`/obras/<slug>`) |
| `creator_id` | INTEGER | no | índice, clave foránea | creador de la obra |
| `title` | VARCHAR(160) | no | | título de la pieza |
| `description` | TEXT | no | | materiales, medidas y acabado |
| `price_note` | VARCHAR(80) | sí | | precio orientativo; si es `None` sale «a consultar» |
| `status` | VARCHAR(40) | no | | disponibilidad, por defecto `disponible` |
| `created_at` | DATETIME | no | | fecha de alta, la pone el servidor |

`accent` y `status` tienen valor por defecto en el código, no en la base de datos, así
que no salen como `DEFAULT` en el `CREATE TABLE`. `created_at` sí lo pone el servidor
con `server_default=func.now()`.

## relación

Un creador tiene varias obras. `works.creator_id` apunta a `creators.id` y la relación
está declarada en los dos sentidos con `back_populates` (`Creator.works` y
`Work.creator`). `Creator.works` ordena por `Work.id`.

El borrado en cascada es solo del ORM: `Creator.works` tiene
`cascade="all, delete-orphan"`, así que si borro un creador desde una sesión de
SQLAlchemy se borran sus obras. La clave foránea no lleva `ondelete`, así que un
`DELETE` en SQL a pelo deja las obras huérfanas en SQLite y falla en PostgreSQL. Si
alguna vez hace falta borrar, se hace desde el ORM o se añade `ondelete="CASCADE"`.

## reglas que aplica el código

- `slug` es único en las dos tablas. Es lo que buscan las rutas de detalle; si no
  existe, la ruta devuelve el 404 propio.
- Longitudes máximas: `creators.slug` y `name` 120, `specialty` 40, `location` 120,
  `contact_email` 200, `works.slug` 140, `title` 160, `price_note` 80, `status` 40.
  PostgreSQL las respeta; SQLite no comprueba `VARCHAR(n)`.
- `specialty` es texto libre, sin `CHECK` ni tabla aparte. Las cuatro especialidades
  del marketplace son `ropa`, `props`, `pelucas` y `accesorios`, y son las que salen en
  el filtro de `/creadores`.
- `verified` marca si el creador ha pasado la revisión del equipo. Los del seed salen
  verificados; el valor por defecto es `False`.
- `status` también es texto libre. En el seed uso `disponible`, `encargo` y `agotado`.
- `price_note` puede ser `NULL`; la plantilla muestra «a consultar».
- No hay validación del correo: cualquier cadena de hasta 200 caracteres se acepta y
  se publica tal cual en el `mailto:`.

## búsqueda

`/buscar?q=` no usa índices dedicados ni tabla aparte. Es un `ILIKE` con el patrón
`%texto%` sobre `creators.name`, `creators.bio`, `creators.location` y
`creators.specialty`, y lo mismo sobre `works.title` y `works.description`. Luego la
plantilla pinta los dos bloques de resultados. En SQLite el `ILIKE` acaba en un `LIKE`,
que solo ignora mayúsculas en ASCII.

Con el catálogo actual, unas pocas decenas de filas, sobra: recorrer la tabla entera es
más rápido que mantener un índice de texto. Si el catálogo creciera de golpe, tocaría
mirar `pg_trgm` o el índice de texto completo de PostgreSQL.

## lo que falta para producción

- Usuarios y login: hoy no hay. Cualquiera con acceso a la base de datos puede editar
  el catálogo.
- Imágenes: las obras son solo texto, sin campo de imagen ni almacenamiento.
- Moderación: no hay revisión ni denuncias. El contacto es un `mailto:` directo, así
  que el correo del creador queda a la vista.

## migraciones

El esquema vive en Alembic. `alembic.ini` apunta a `migrations/`, y
`migrations/env.py` saca la URL de `DATABASE_URL` pasándola por
`normalize_database_url` (la misma función que usa la app, en `db.py`).
`target_metadata` es `Base.metadata`, así que `alembic revision --autogenerate`
compara los modelos contra la base real.

- **PostgreSQL (producción):** el esquema lo mueve Alembic. `create_app()` llama a
  `migraciones.aplicar_migraciones()`, que toma un advisory lock de PostgreSQL en
  una conexión aparte antes de lanzar `upgrade head`. Gunicorn arranca dos workers
  y los dos ejecutan `create_app()`; sin el lock, dos `ALTER TABLE` simultáneos se
  pisan. El que llega segundo espera, encuentra la base al día y su `upgrade` no
  hace nada.
- **SQLite (local y tests):** se sigue usando `Base.metadata.create_all(engine)`.
  Es instantáneo, idempotente y no hay despliegue que coordinar.

Cambiar una columna en `models.py` ya no basta: hace falta
`alembic revision --autogenerate -m "..."` y revisar el fichero generado antes de
subirlo. `create_all()` no compara columnas, así que en SQLite local un cambio de
tipo no se aplica solo: se borra `cosknot.db` y se recrea.

El catálogo de ejemplo no se siembra en producción. `SEED_ON_START=1` o
`flask sembrar` lo hacen a mano; en SQLite local sigue siendo automático.

