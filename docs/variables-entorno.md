# variables de entorno

Todo lo que la app lee del entorno. El archivo `.env.example` tiene la plantilla; en
local se copia a `.env` y Flask lo carga con `python-dotenv`. Ningún secreto vive en el
repositorio.

Arrancar en local con solo SQLite no necesita ninguna de las variables marcadas como
«producción»: sin claves externas la app levanta, sirve el catálogo de ejemplo y las
funciones que dependen de terceros quedan desactivadas con un aviso.

## base y sesión

| variable | fase | qué hace | obligatoria |
|---|---|---|---|
| `DATABASE_URL` | 1 | cadena de conexión. Vacía = `sqlite:///cosknot.db` en local. En Render es la cadena *pooled* de Neon. | en producción |
| `SECRET_KEY` | 1 | firma las cookies de sesión y los tokens CSRF. | en producción |
| `SEED_ON_START` | 1 | `1` siembra el catálogo de ejemplo al arrancar. En SQLite se siembra solo; en PostgreSQL hay que pedirlo o usar `flask sembrar`. | no |
| `FLASK_ENV` | 1 | entorno de Flask para desarrollo. | no |

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
| `RESEND_API_KEY` | 5 | clave de Resend. Sin ella el correo se imprime en consola en desarrollo y queda desactivado en producción. | para enviar |
| `EMAIL_FROM` | 5 | remitente verificado en Resend. | para enviar |
| `EMAIL_REPLY_TO` | 5 | `reply-to` de los avisos. | no |
| `EMAIL_ASYNC` | 5 | `0` envía dentro de la petición (depuración). Por defecto `1`: en un hilo aparte. | no |

## pagos

| variable | fase | qué hace | obligatoria |
|---|---|---|---|
| `STRIPE_SECRET_KEY` | 6 | clave de Stripe en modo test (`sk_test_...`). Una `sk_live_` se rechaza. | para cobrar |
| `STRIPE_PUBLISHABLE_KEY` | 6 | clave publicable; se documenta por si algún día se incrusta Checkout. | no |
| `STRIPE_WEBHOOK_SECRET` | 6 | secreto del endpoint `/stripe/webhook`; sin él no se acepta ningún evento. | para cobrar |
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
| `RENDER` | 1 | la define Render en todos sus servicios. Activa las comprobaciones de producción: exige `SECRET_KEY` y `DATABASE_URL`, marca la cookie `Secure` y desactiva el seed automático. |

## comprobación rápida

```powershell
# sin ninguna clave, en local
python -c "import app; a=app.app; print(a.test_client().get('/healthz').get_json())"
# {'status': 'ok'}
```

Con eso: base SQLite creada, catálogo sembrado, imágenes en `static/uploads`, correo por
consola y cobro desactivado con su motivo.
