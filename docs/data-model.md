# modelo de datos

cosknot es un marketplace de cosplay: un creador publica ropa, props, pelucas y
accesorios, y un comprador los mira, los compra o pide un encargo. El modelo guarda el
escaparate, las cuentas y los pedidos con su conversación. Los pagos con tarjeta
llegan en la fase 6 y no añaden tablas propias: el `payment_intent` de Stripe se
guarda en el pedido.

Hay cinco tablas, definidas en `models.py` con SQLAlchemy 2.x: `users`, `creators`,
`works`, `orders` y `order_messages`.

## tabla `users`

| columna | tipo | nulo | clave o índice | qué es |
|---|---|---|---|---|
| `id` | INTEGER | no | clave primaria | identificador interno |
| `email` | VARCHAR(200) | no | único e indexado | correo con el que se entra; se guarda en minúsculas |
| `password_hash` | VARCHAR(255) | no | | hash argon2id; nunca la contraseña |
| `role` | VARCHAR(20) | no | indexado | `comprador`, `creador` o `admin` |
| `created_at` | DATETIME | no | | fecha de alta, la pone el servidor |

Los roles no son una tabla: `models.ROLES` los enumera y el código comprueba el
valor. `admin` puede además publicar obras y verificar talleres. El registro público
solo permite `comprador` y `creador`; un admin se crea con
`flask hacer-admin <correo>`.

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
| `image_key` | VARCHAR(255) | sí | | clave de la foto en el almacén; `NULL` usa la foto de `static/img` |
| `stripe_account_id` | VARCHAR(255) | sí | único | cuenta conectada express de Stripe; `NULL` si el taller no cobra |
| `stripe_onboarding_ok` | BOOLEAN | no | | `true` cuando Stripe ya permite cobrar y transferir a esa cuenta |
| `user_id` | INTEGER | sí | índice único, clave foránea | cuenta que gestiona el taller; `NULL` en los perfiles del seed |
| `created_at` | DATETIME | no | | fecha de alta, la pone el servidor |

## tabla `works`

| columna | tipo | nulo | clave o índice | qué es |
|---|---|---|---|---|
| `id` | INTEGER | no | clave primaria | identificador interno |
| `slug` | VARCHAR(140) | no | único e indexado | parte de la URL (`/obras/<slug>`) |
| `creator_id` | INTEGER | no | índice, clave foránea | creador de la obra |
| `title` | VARCHAR(160) | no | | título de la pieza |
| `description` | TEXT | no | | materiales, medidas y acabado |
| `price_note` | VARCHAR(80) | sí | | precio orientativo en texto libre; si es `None` sale «a consultar» |
| `price_cents` | INTEGER | sí | | precio real en céntimos, el que se cobra; `NULL` si el taller no lo ha fijado |
| `currency` | VARCHAR(3) | no | | moneda ISO-4217, por defecto `EUR` |
| `status` | VARCHAR(40) | no | | disponibilidad, por defecto `disponible` |
| `image_key` | VARCHAR(255) | sí | | clave de la foto en el almacén; `NULL` usa la foto de `static/img` |
| `created_at` | DATETIME | no | | fecha de alta, la pone el servidor |

`accent` y `status` tienen valor por defecto en el código, no en la base de datos, así
que no salen como `DEFAULT` en el `CREATE TABLE`. `created_at` sí lo pone el servidor
con `server_default=func.now()`.

## tabla `orders`

| columna | tipo | nulo | clave o índice | qué es |
|---|---|---|---|---|
| `id` | INTEGER | no | clave primaria | identificador interno |
| `buyer_id` | INTEGER | no | índice, clave foránea a `users.id` | quién encarga |
| `work_id` | INTEGER | no | índice, clave foránea a `works.id` | qué obra |
| `status` | VARCHAR(20) | no | indexado | estado del pedido, por defecto `solicitado` |
| `amount_cents` | INTEGER | no | | importe acordado en céntimos; copia de `works.price_cents` al crear el pedido |
| `application_fee_cents` | INTEGER | no | | comisión de cosknot en céntimos; la calcula el cobro |
| `stripe_payment_intent_id` | VARCHAR(255) | sí | único | `payment_intent` de Stripe; se rellena en el webhook |
| `stripe_checkout_session_id` | VARCHAR(255) | sí | único | sesión de Checkout creada al pagar |
| `paid_at` | DATETIME | sí | | fecha en la que el webhook confirmó el pago |
| `created_at` | DATETIME | no | | fecha del encargo |

## tabla `order_messages`

| columna | tipo | nulo | clave o índice | qué es |
|---|---|---|---|---|
| `id` | INTEGER | no | clave primaria | identificador interno |
| `order_id` | INTEGER | no | índice, clave foránea a `orders.id` | pedido al que pertenece |
| `author_id` | INTEGER | no | índice, clave foránea a `users.id` | quién escribe |
| `body` | TEXT | no | | texto del mensaje |
| `created_at` | DATETIME | no | | fecha del mensaje |

## estados de un pedido

La máquina de estados vive en `estados_pedido.py`, no en las plantillas.

| desde | puede pasar a | quién |
|---|---|---|
| `solicitado` | `aceptado` | creador |
| `solicitado` | `cancelado` | comprador o creador |
| `aceptado` | `pagado` | creador (en la fase 6 lo pone el webhook de Stripe) |
| `aceptado` | `cancelado` | comprador o creador |
| `pagado` | `enviado` | creador |
| `pagado` | `cancelado` | comprador o creador |
| `enviado` | `completado` | comprador |
| `completado` | — | terminal |
| `cancelado` | — | terminal |

`cambiar_estado(pedido, destino, usuario)` comprueba tres cosas antes de tocar nada:
que el destino exista, que la transición esté en la tabla y que el rol del usuario
pueda provocarla. Un `admin` puede todas. Cualquier otra cosa lanza
`TransicionInvalida` y la ruta devuelve el pedido sin cambios con un aviso.


## relación

Un creador tiene varias obras. `works.creator_id` apunta a `creators.id` y la relación
está declarada en los dos sentidos con `back_populates` (`Creator.works` y
`Work.creator`). `Creator.works` ordena por `Work.id`.

Un usuario puede tener como mucho un taller: `creators.user_id` es único y puede ser
`NULL`. Los perfiles que crea el seed no tienen cuenta detrás; los que se crean desde
`/cuenta/perfil` sí. El borrado en cascada es solo del ORM, así que borrar un
`User` desde SQL no borra su `Creator`: primero se pone `user_id` a `NULL` o se
borra el taller desde la sesión.

## roles

- `comprador`: puede navegar y (a partir de la fase 3) hacer pedidos.
- `creador`: además tiene taller y puede crear, editar y borrar sus obras.
- `admin`: todo lo del creador más `/admin/creadores`, donde marca talleres como
  verificados.

Las rutas de `/cuenta` exigen sesión con `@login_required`; las de `/admin` además
comprueban `current_user.is_admin` y devuelven 403 si no lo es. Un creador solo
puede tocar obras cuyo `creator.user_id` sea el suyo; el resto da 403.

El borrado en cascada es solo del ORM: `Creator.works` tiene
`cascade="all, delete-orphan"`, así que si borro un creador desde una sesión de
SQLAlchemy se borran sus obras. La clave foránea no lleva `ondelete`, así que un
`DELETE` en SQL a pelo deja las obras huérfanas en SQLite y falla en PostgreSQL. Si
alguna vez hace falta borrar, se hace desde el ORM o se añade `ondelete="CASCADE"`.

## reglas que aplica el código

- `slug` es único en `creators` y `works`. Es lo que buscan las rutas de detalle; si no
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
- El correo de registro y el de contacto del taller se validan con el validador
  `Email` de WTForms; la contraseña exige 8 caracteres como mínimo y se guarda como
  hash argon2id. `users.email` se normaliza a minúsculas antes de guardar.

## búsqueda

`/buscar?q=` tiene dos caminos en `busqueda.py`, elegidos por el dialecto de la sesión:

- **PostgreSQL**: texto completo en español. `to_tsvector('spanish', ...)` sobre
  `creators.name`, `creators.bio`, `creators.location` y `creators.specialty` (y sobre
  `works.title` y `works.description`), contra `plainto_tsquery('spanish', ...)`, con
  `ts_rank` para ordenar. Los índices GIN de la migración `0006` cubren exactamente esa
  expresión, con literales, para que el planificador los use.
- **SQLite**: `ILIKE` con el patrón `%texto%` sobre los mismos campos. Es el motor de
  desarrollo y de las pruebas, y solo ignora mayúsculas en ASCII.

La ruta no cambia: pide los resultados a `buscar_creadores()` y `buscar_obras()`. El
stemmer español hace que «capas» encuentre «capa»; en SQLite eso no pasa y hay que
escribir la palabra tal cual.


## imágenes

`creators.image_key` y `works.image_key` guardan la clave del objeto en el almacén.
Si es `NULL`, `fotos.foto()` cae en la foto de `static/img` que toca por slug, así que
el seed y las fichas antiguas siguen funcionando sin tocar nada.

- **Desarrollo**: `AlmacenLocal` escribe en `UPLOAD_DIR` (por defecto
  `static/uploads`) y sirve por `/static/uploads/<clave>`.
- **Producción**: `AlmacenR2` sube a Cloudflare R2 por la API compatible con S3 y
  devuelve la URL de `R2_PUBLIC_BASE_URL`. Sin las cinco variables de R2 las subidas
  se desactivan con un aviso y la ficha sigue con la foto antigua.
- **Validación**: extensión (`.jpg`, `.jpeg`, `.png`, `.webp`), content-type, firma
  del archivo y tamaño máximo (`MAX_IMAGE_BYTES`, 5 MB por defecto). El tope global
  de la petición es `MAX_CONTENT_LENGTH`.
- **CSP**: `img-src` solo se abre al origen de `R2_PUBLIC_BASE_URL`, sin comodines.
- **Migración de las fotos viejas**: `flask migrar-fotos` sube los ficheros de
  `static/img` al almacén y rellena `image_key` en cada taller y obra. No toca el
  seed: si un slug no tiene foto asignada, se queda con la de reserva.

## lo que falta para producción

- Moderación: no hay revisión ni denuncias de obras o mensajes.

## migraciones

El esquema vive en Alembic. `alembic.ini` apunta a `migrations/`, y
`migrations/env.py` saca la URL de `DATABASE_URL` pasándola por
`normalize_database_url` (la misma función que usa la app, en `db.py`).
`target_metadata` es `Base.metadata`, así que `alembic revision --autogenerate`
compara los modelos contra la base real.

- **PostgreSQL (producción):** el esquema lo aplica el proceso `release` del
  Procfile con `alembic upgrade head`, una vez por despliegue y antes de que el
  dyno nuevo reciba tráfico. Si la migración falla, Heroku aborta el despliegue y
  la versión anterior sigue sirviendo: no hay ventana con el esquema a medias. El
  arranque del dyno no migra ni siembra; `create_app()` solo llama a `create_all()`
  cuando la base es SQLite.
- **SQLite (local y tests):** `Base.metadata.create_all(engine)` crea el esquema
  desde los modelos. Es instantáneo, idempotente y no hay despliegue que coordinar.

Cambiar una columna en `models.py` ya no basta: hace falta
`alembic revision --autogenerate -m "..."` y revisar el fichero generado antes de
subirlo. `create_all()` no compara columnas, así que en SQLite local un cambio de
tipo no se aplica solo: se borra `cosknot.db` y se recrea.

El catálogo de ejemplo no se siembra en producción. `SEED_ON_START=1` o
`flask sembrar` lo hacen a mano; en SQLite local sigue siendo automático.

