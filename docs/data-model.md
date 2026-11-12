# modelo de datos

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
- `specialty` es texto libre, sin `CHECK` ni tabla aparte. En `seed.py` hay tres
  valores (`ropa`, `props`, `accesorios`) que salen en el filtro de `/creadores`.
- `status` también es texto libre. En el seed uso `disponible`, `encargo` y `agotado`.
- `price_note` puede ser `NULL`; la plantilla muestra «a consultar».
- No hay validación del correo: cualquier cadena de hasta 200 caracteres se acepta y
  se publica tal cual en el `mailto:`.

## lo que falta para producción

- Usuarios y login: hoy no hay. Cualquiera con acceso a la base de datos puede editar
  el catálogo.
- Imágenes: las obras son solo texto, sin campo de imagen ni almacenamiento.
- Moderación: no hay revisión ni denuncias. El contacto es un `mailto:` directo, así
  que el correo del creador queda a la vista.

## migraciones

No hay Alembic ni nada parecido. `create_all()` solo crea las tablas que faltan y no
compara columnas, así que cambiar un tipo, una longitud o un `nullable` en `models.py`
no cambia una tabla que ya existe. Mientras no haya migraciones, cualquier cambio de
esquema hay que hacerlo a mano en la base de datos o recreando la tabla.
