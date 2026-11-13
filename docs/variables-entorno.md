# variables de entorno

Todo lo que la app lee del entorno. El archivo `.env.example` tiene la plantilla; en
local se copia a `.env` y Flask lo carga con `python-dotenv`. En Heroku no se sube: se
configuran con `heroku config:set`. Ningún secreto vive en el repositorio.

Ninguna de las variables marcadas como «en producción» es necesaria para arrancar en
local con SQLite y sin claves: la app levanta, sirve el catálogo de ejemplo y las
funciones que dependen de terceros quedan desactivadas con un aviso.

## base y sesión

| variable | fase | qué hace | obligatoria |
|---|---|---|---|
| `DATABASE_URL` | 1 | cadena de conexión. Vacía = `sqlite:///cosknot.db` en local. En Heroku la pone el addon de Postgres. Acepta `postgres://` y `postgresql://`; se normaliza a `postgresql+psycopg://`. | en producción |
| `SECRET_KEY` | 1 | firma las cookies de sesión y los tokens CSRF. | en producción |
| `APP_ENV` | 1 | entorno de la app. En Heroku vale `production`. Si falta, se considera producción cuando existe `DYNO`. | en producción |
| `SEED_ON_START` | 1 | `1` siembra el catálogo de ejemplo al arrancar. En SQLite se siembra solo; en PostgreSQL hay que pedirlo o usar `flask sembrar`. | no |

## proxy

| variable | fase | qué hace | obligatoria |
|---|---|---|---|
| `PROXY_FIX_X_FOR` | 1 | saltos de proxy en los que confiar para `X-Forwarded-For`. El router de Heroku añade uno; con Cloudflare en modo DNS only (nube gris) `1` es exacto. Se acota entre 0 y 5. | no |
| `PROXY_FIX_X_PROTO` | 1 | saltos de proxy en los que confiar para `X-Forwarded-Proto`. Mismo criterio: `1` con el router de Heroku y Cloudflare en DNS only. Se acota entre 0 y 5. | no |

## pool de conexiones

Techo de conexiones de la app: `DB_POOL_SIZE + DB_MAX_OVERFLOW = 5`. A eso se suman una
conexión del proceso `release` (que corre `alembic upgrade head`), una de `pg_dump` y una
de `psql`: 8 de las 20 del plan Essential-0.

| variable | fase | qué hace | obligatoria |
|---|---|---|---|
| `DB_POOL_SIZE` | 1 | conexiones permanentes del pool. Por defecto `3`. | no |
| `DB_MAX_OVERFLOW` | 1 | conexiones extra por encima del pool. Por defecto `2`. | no |
| `DB_POOL_RECYCLE` | 1 | segundos antes de reciclar una conexión. Por defecto `300`. | no |
| `DB_POOL_TIMEOUT` | 1 | segundos de espera para obtener una conexión del pool. Por defecto `10`. | no |

## límite de peticiones

| variable | fase | qué hace | obligatoria |
|---|---|---|---|
| `RATELIMIT_STORAGE_URI` | 2 | backend del contador de límites. Por defecto `memory://`: contador en memoria del proceso, exacto con un solo worker (el del `Procfile`) y se pierde al reiniciar el dyno. | no |

## imágenes

| variable | fase | qué hace | obligatoria |
|---|---|---|---|
| `IMAGE_STORAGE` | 4 | `local` (disco, solo desarrollo) o `r2`. Vacío = local en desarrollo y subidas desactivadas en producción. | no |
| `UPLOAD_DIR` | 4 | carpeta del backend local. Por defecto `static/uploads`. | no |
| `R2_ENDPOINT_URL` | 4 | `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`. | con R2 |
| `R2_BUCKET` | 4 | nombre del bucket. | con R2 |
| `R2_ACCESS_KEY_ID` | 4 | credencial de R2. | con R2 |
| `R2_SECRET_ACCESS_KEY` | 4 | secreto de R2. | con R2 |
| `R2_PUBLIC_BASE_URL` | 4 | dominio público del bucket. Se abre en `img-src` de la CSP, sin comodines. | con R2 |

## correo

| variable | fase | qué hace | obligatoria |
|---|---|---|---|
| `RESEND_API_KEY` | 3 | clave de Resend (HTTP; Heroku bloquea SMTP). Sin ella el correo se imprime en consola en desarrollo y queda desactivado en producción. | para enviar |
| `EMAIL_FROM` | 3 | remitente verificado en Resend, por ejemplo `cosknot <hola@tudominio.com>`. | para enviar |
| `EMAIL_REPLY_TO` | 3 | `reply-to` de los avisos. | no |
| `EMAIL_ASYNC` | 3 | `1` (por defecto) = intentar en la petición y, si falla, dejar el aviso en la tabla `email_outbox` para el hilo de reintentos. `0` = solo en la petición, sin outbox. | no |
| `EMAIL_MAX_INTENTOS` | 3 | reintentos máximos por aviso antes de dejarlo como `fallido`. Por defecto `5`. | no |

## sugerencias con IA

| variable | fase | qué hace | obligatoria |
|---|---|---|---|
| `GEMINI_API_KEY` | 4 | clave de Gemini. Sin ella el botón de sugerencias no aparece. | no |
| `GEMINI_MODEL` | 4 | modelo a usar. Obligatorio si hay clave: no hay valor por defecto en el código. Ejemplo: `gemini-2.5-flash`. | con clave |
| `GEMINI_TIMEOUT` | 4 | tiempo máximo de espera de la sugerencia, en segundos. Por defecto `20`. | no |

## pagos

| variable | fase | qué hace | obligatoria |
|---|---|---|---|
| `STRIPE_SECRET_KEY` | 6 | clave de Stripe en modo test (`sk_test_...`). Una `sk_live_` se rechaza a propósito. | para cobrar |
| `STRIPE_PUBLISHABLE_KEY` | 6 | clave publicable; se documenta por si algún día se incrusta Checkout. | no |
| `STRIPE_WEBHOOK_SECRET` | 6 | secreto del endpoint `/stripe/webhook` (`whsec_...`); sin él no se acepta ningún evento. | para cobrar |
| `COMMISSION_PERCENT` | 6 | comisión de cosknot en porcentaje. Sin valor por defecto: si falta, el cobro no se activa. | para cobrar |

## errores y registro

| variable | fase | qué hace | obligatoria |
|---|---|---|---|
| `LOG_LEVEL` | 8 | `DEBUG`, `INFO`, `WARNING` o `ERROR`. Por defecto `INFO`. | no |
| `SENTRY_DSN` | 8 | DSN de Sentry. Sin él Sentry no se inicializa. | no |
| `SENTRY_ENVIRONMENT` | 8 | etiqueta de entorno en Sentry. Por defecto `production`. | no |
| `SENTRY_TRACES_SAMPLE_RATE` | 8 | muestreo de trazas de 0 a 1. Por defecto `0` (solo errores). | no |

## variables que pone la plataforma

| variable | fase | qué hace |
|---|---|---|
| `DYNO` | 1 | la define Heroku en todos los dynos. Sirve para detectar producción cuando falta `APP_ENV`: exige `SECRET_KEY` y `DATABASE_URL`, marca la cookie `Secure` y desactiva el seed automático. |
| `DATABASE_URL` | 1 | la pone el addon de Postgres y rota credenciales; no se fija a mano. |
| `PORT` | 1 | puerto que asigna Heroku. El `Procfile` lo usa con `--bind 0.0.0.0:$PORT`. |

## comprobación rápida

```bash
# sin ninguna clave, en local
python -c "import app; a=app.app; print(a.test_client().get('/healthz').get_json())"
# {'status': 'ok'}
```

Con eso: base SQLite creada, catálogo sembrado, imágenes en `static/uploads`, correo por
consola y cobro desactivado con su motivo.
