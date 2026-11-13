# heroku como hosting, postgres esencial y un solo dyno

fecha: 2026-11-13
estado: aceptada

Sustituye a `0001-stack-despliegue-dominio.md` en la parte de hosting y base de
datos. Lo demás de 0001 (Python, Flask, Jinja, gunicorn, SQLite solo en local)
sigue vigente.

## decisión

- **Hosting**: Heroku, un dyno Basic (512 MB de RAM, siempre encendido).
- **Base de datos**: Heroku Postgres Essential-0 (1 GB, 20 conexiones, sin
  rollback).
- **Servidor**: gunicorn con `--workers 1 --threads 4`, `--bind 0.0.0.0:$PORT`,
  `--timeout 50`.
- **Migraciones**: proceso `release` del Procfile (`alembic upgrade head`), una
  vez por despliegue. El arranque del dyno ya no migra ni siembra en PostgreSQL.
- **Proxy**: `ProxyFix(x_for=1, x_proto=1, x_host=0, x_port=0)`, con Cloudflare
  en modo DNS only (nube gris).
- **Límite de peticiones**: almacenamiento en memoria del proceso
  (`RATELIMIT_STORAGE_URI=memory://`). Sin Redis.
- **Correo**: Resend por HTTP; si el envío inmediato falla, el aviso va a la
  tabla `email_outbox` y un hilo del propio proceso web lo reintenta.
- **Imágenes**: Cloudflare R2 (sin cambios respecto a 0002).
- **Copias de seguridad**: `pg:backups:schedule` de Heroku más un flujo diario de
  GitHub Actions que vuelca con `pg_dump`, cifra y sube a R2.

Coste: **12 $/mes** (7 $ del dyno + 5 $ de Postgres). Tope duro de 13 $/mes
gracias al crédito de GitHub Student Pack; el plan no se puede subir sin salirse
del crédito, y por eso todo está dimensionado para caber en un dyno y 20
conexiones.

## por qué

- **Heroku y no Render free**: el plan gratuito de Render duerme a los 15 minutos
  y tarda ~50 s en despertar. Con el crédito de estudiante, 12 $/mes compran un
  dyno siempre encendido y una base de datos que no caduca. Es el mismo dinero
  que costaría un plan de pago de Render, con menos piezas.
- **Un solo dyno**: 512 MB de RAM no aguantan dos procesos de gunicorn con cuatro
  hilos cada uno con holgura, y el límite en memoria de Flask-Limiter solo es
  exacto con un proceso. Con un worker el contador de intentos es el correcto:
  no hay dos procesos con dos cuentas distintas de los mismos intentos.
- **`--threads 4` y no más workers**: las peticiones son I/O (Postgres, R2,
  Resend, Stripe). Cuatro hilos cubren la espera sin duplicar el estado en
  memoria ni las conexiones a la base.
- **`--timeout 50`**: el router de Heroku corta a los 30 s de espera de la
  primera respuesta. Un gunicorn con timeout 50 deja margen para que la traza la
  escriba la aplicación y no el router; `--graceful-timeout 25` permite terminar
  la petición en curso al reiniciar.
- **Migraciones en `release`**: el proceso `release` corre una vez por
  despliegue, antes de que el dyno nuevo reciba tráfico, y con la versión de
  código nueva en el slug. Migrar en el arranque multiplica el trabajo por cada
  dyno y puede correr a la vez que una petición.
- **`ProxyFix` con un salto**: el router de Heroku añade una entrada a
  `X-Forwarded-For`. Si Cloudflare está en nube gris (solo DNS), el único proxy
  del camino es Heroku y confiar en un salto es exacto. En naranja habría dos y
  la IP del cliente se leería mal: por eso el modo recomendado es nube gris.
- **Sin Redis**: un Redis gestionado son 15 $/mes más, el doble del
  presupuesto. Con un proceso, `memory://` da el mismo resultado para lo que se
  usa aquí (frenar fuerza bruta y abuso de formularios).
- **Essential-0 y no otra cosa**: 20 conexiones son suficientes con el reparto de
  `db.py` (5 de la app, 1 de `release`, 1 del `pg_dump`, 1 de un `psql` puntual =
  8 de 20). El plan no tiene rollback, y por eso las copias son diarias y
  probadas.

## el reparto de conexiones, con números

| quién | conexiones |
|---|---|
| dyno web: `pool_size 3` + `max_overflow 2` | 5 |
| proceso `release` (`alembic upgrade head`) | 1 |
| `pg_dump` de la copia diaria | 1 |
| `heroku pg:psql` puntual | 1 |
| **total** | **8 de 20** |

`pool_pre_ping=True` y `pool_recycle=300` evitan el "server closed the connection
unexpectedly" con el que Heroku corta las conexiones ociosas. Todo se ajusta con
`DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_RECYCLE` y `DB_POOL_TIMEOUT`, pero
subirlo sin medir es la forma más rápida de tumbar la web por conexiones.

## limitaciones aceptadas

- **El contador de intentos se pierde al reiniciar el dyno.** Heroku reinicia al
  menos una vez cada 24 h. La ventana de un límite es de minutos, así que la
  exposición real es pequeña.
- **El hilo del `email_outbox` vive dentro del proceso web.** Si el dyno está
  reiniciándose, los reintentos esperan. El estado está en la tabla, no en
  memoria: al volver, el hilo retoma lo pendiente.
- **Sin rollback de base de datos.** Una migración destructiva se arregla con una
  migración nueva o restaurando la copia del día.
- **Un dyno es un punto único.** Un despliegue o un reinicio son unos segundos de
  503. Para un marketplace de cosplay es aceptable.

## alternativas descartadas

- **Render free**: dormido, arranque en frío de ~50 s y base de datos que caduca
  a los 30 días.
- **Render de pago + Neon free**: mismo coste que Heroku, dos paneles, y Neon
  pausa la base por inactividad.
- **Fly.io / Cloud Run**: piden Docker, tarjeta y no tienen tope de gasto; el
  crédito de estudiante no los cubre de forma cómoda.
- **Oracle Always Free**: mucha máquina, pero administración de VM y capacidad
  variable.
- **Redis gestionado** (`REDIS_URL` de Heroku o Upstash): 15 $/mes más para un
  contador que con un proceso en memoria ya es exacto.
- **Cloudflare en naranja**: daría caché y DDoS, pero añade un proxy delante del
  router y obliga a `x_for=2`; con el tráfico actual no compensa la complejidad.
- **Dos dynos**: el doble de coste, sale del crédito, y rompe la exactitud del
  contador en memoria.

## cuándo revisar esto

- Si el crédito de GitHub Student deja de cubrir los 12 $/mes.
- Si el tráfico necesita más de un dyno: entonces toca Redis y un dyno más.
- Si la base pasa de 1 GB o de 20 conexiones de forma sostenida.
- Si Cloudflare en naranja pasa a ser necesario por tráfico o por ataques.
