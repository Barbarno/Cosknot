# modelo de datos

dos tablas, definidas en `models.py` sobre sqlalchemy 2.x. no hay más tablas y no hay ficheros de migración.

el esquema se crea al arrancar con `Base.metadata.create_all(engine)` dentro de `create_app()`. en local el motor es sqlite (`sqlite:///cosknot.db`); en producción, postgres en neon.

## tabla `creators`

| columna | tipo sql | nulo | índice / único | qué representa |
|---|---|---|---|---|
| `id` | `INTEGER` | no | clave primaria, autoincremental | identificador interno del creador |
| `slug` | `VARCHAR(120)` | no | único e indexado | identificador legible para la url (`/creadores/<slug>`) |
| `name` | `VARCHAR(120)` | no | — | nombre público del creador |
| `specialty` | `VARCHAR(40)` | no | indexado | especialidad principal, texto libre |
| `location` | `VARCHAR(120)` | no | — | ciudad y país en texto libre |
| `bio` | `TEXT` | no | — | descripción larga del taller o del trabajo |
| `contact_email` | `VARCHAR(200)` | no | — | correo que se publica en un `mailto:` en la ficha de obra |
| `accent` | `INTEGER` | no | — | índice de paleta visual usado por las plantillas, por defecto `0` |
| `created_at` | `DATETIME` | no | — | fecha de alta, valor por defecto del servidor (`now()`) |

## tabla `works`

| columna | tipo sql | nulo | índice / único | qué representa |
|---|---|---|---|---|
| `id` | `INTEGER` | no | clave primaria, autoincremental | identificador interno de la obra |
| `slug` | `VARCHAR(140)` | no | único e indexado | identificador legible para la url (`/obras/<slug>`) |
| `creator_id` | `INTEGER` | no | índice, clave foránea a `creators.id` | creador al que pertenece la obra |
| `title` | `VARCHAR(160)` | no | — | título de la pieza |
| `description` | `TEXT` | no | — | descripción de materiales, medidas y acabado |
| `price_note` | `VARCHAR(80)` | sí | — | nota de precio en texto libre; `None` se muestra como «a consultar» |
| `status` | `VARCHAR(40)` | no | — | disponibilidad, por defecto `disponible` en python |
| `created_at` | `DATETIME` | no | — | fecha de alta, valor por defecto del servidor (`now()`) |

`accent` y `status` tienen valor por defecto a nivel de aplicación, no de base de datos: no aparecen en el `CREATE TABLE` como `DEFAULT`. `created_at` sí es `server_default=func.now()`.

## relación

un creador tiene N obras. `works.creator_id` apunta a `creators.id` y la relación está declarada en los dos sentidos con `back_populates` (`Creator.works` y `Work.creator`).

borrado: la cascada es solo de ORM. `Creator.works` declara `cascade="all, delete-orphan"`, así que al borrar un `Creator` a través de una `Session` sqlalchemy borra también sus obras. la clave foránea no lleva `ondelete`, por lo que a nivel de base de datos no hay cascada: un `DELETE FROM creators WHERE ...` ejecutado en sql crudo deja las obras huérfanas en sqlite (que no valida claves foráneas por defecto) y falla en postgres por la restricción. cualquier borrado debe hacerse por el ORM o añadir `ondelete="CASCADE"` a la foránea.

`Creator.works` ordena por `Work.id`.

## reglas que impone el código

- `slug` único en las dos tablas. es la clave de búsqueda de las rutas de detalle; si no existe, la ruta devuelve el 404 propio.
- longitudes máximas por columna: `creators.slug` y `creators.name` 120, `specialty` 40, `location` 120, `contact_email` 200, `works.slug` 140, `works.title` 160, `price_note` 80, `status` 40. postgres las aplica; sqlite no valida `VARCHAR(n)` y acepta texto más largo.
- `specialty` es texto libre, sin `CHECK` ni tabla de referencia. `seed.py` usa tres valores: `ropa`, `props`, `accesorios`, exportados como `SPECIALTIES` e inyectados en las plantillas como filtros. un valor fuera de esa tupla se guarda, pero no aparece en el filtro de `/creadores`.
- `status` es texto libre. `seed.py` usa `disponible`, `encargo` y `agotado`.
- `price_note` admite `NULL`; la plantilla de obra muestra «a consultar» en ese caso.
- no hay validación de formato en `contact_email`: cualquier cadena de hasta 200 caracteres se acepta y se publica tal cual en un `mailto:`.

## qué falta para producción

- autenticación y tabla de usuarios: hoy no existe ninguna. cualquiera con acceso a la base de datos edita el catálogo, y no hay sesiones ni roles.
- imágenes en almacenamiento de objetos: las obras se describen en texto, sin campo de imagen ni proveedor de ficheros.
- moderación: no hay estado de revisión, ni denuncia, ni cola de aprobación. el contacto es un `mailto:` directo, así que el correo del creador queda expuesto sin filtro.

## migraciones

hoy no hay alembic ni ninguna otra herramienta de migración: el esquema se crea con `Base.metadata.create_all(engine)`, que solo crea tablas que faltan. no compara columnas existentes. cambiar un tipo, una longitud, un `nullable` o un nombre de columna en `models.py` no altera una tabla ya creada: el cambio se ignora en bases existentes y el código empieza a escribir contra un esquema que no coincide. lo mismo con un índice nuevo. hasta que se añada alembic, cualquier cambio de esquema exige recrear la tabla o aplicarlo a mano en sql.
