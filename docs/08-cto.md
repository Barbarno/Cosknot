# CTO: necesidades tecnológicas

Todo lo de esta página está **elegido y presupuestado**, no instalado. Es la decisión
técnica previa a construir.

## las cinco que importan

Esto es lo que responde al enunciado. Cinco líneas:

| qué | qué vamos a usar | por qué |
|---|---|---|
| **lenguaje** | **Python 3.13** | legible, un solo lenguaje para la web y los scripts |
| **framework web** | **Flask 3.1** + **Jinja2** | microframework: cada pieza se ve y se explica en clase |
| **base de datos** | **PostgreSQL 16** (SQLite en local) | el dominio es relacional y el SQL es el mismo en los dos |
| **acceso a datos** | **SQLAlchemy 2** + **Alembic** | sin SQL a mano; cada cambio de esquema queda versionado |
| **despliegue y HTTPS** | **Heroku** con certificado automático | un comando, base gestionada y Let's Encrypt incluido |

Y así se dice en voz alta, treinta segundos:

> Usamos Python con Flask y PostgreSQL, y lo ponemos en Heroku con HTTPS automático. Los
> demás son servicios que se contratan cuando hacen falta —Stripe para cobrar, Resend
> para los correos, un almacén para las fotos—, todos con plan gratuito y ninguno pagado
> hasta que haya ventas.

El resto de la página es el anexo: qué hay detrás de cada una de esas cinco, alternativas
que descartamos y por qué. Está para quien pregunte, no para leerlo de arriba abajo.

Si la pregunta es «¿y esto para qué sirve?», la respuesta corta por tecnología y las
preguntas típicas con su contestación están en [`09-preguntas.md`](09-preguntas.md).

## anexo: el resto, por necesidad

| necesidad | solución elegida | por qué |
|---|---|---|
| servir páginas web | **Flask 3.1** sobre **Python 3.13** | microframework: cada pieza se ve y se explica en clase |
| plantillas HTML | **Jinja2** | renderizado en servidor, sin compilar frontend |
| base de datos | **PostgreSQL 16** en producción, **SQLite** en local | el dominio es relacional y el SQL es el mismo |
| acceso a datos | **SQLAlchemy 2** | sin SQL a mano y la inyección se bloquea por construcción |
| cambios de esquema | **Alembic** | cada cambio de tablas queda versionado y se puede deshacer |
| estilos | **CSS propio** (~30 KB) | sin Bootstrap ni Tailwind: control total y cero dependencias |
| comportamiento en el navegador | **JavaScript moderno sin framework** | son dos interacciones: filtro de categoría y sugerencia de descripción |
| fotos | **Cloudflare R2** con **boto3** | 10 GB gratis, S3 compatible y fuera del servidor |
| correo | **Resend** | avisos de pedido sin montar un servidor de correo |
| cobros | **Stripe Connect** | el dinero va directo al creador, con comisión de plataforma |
| suscripción | **Stripe Checkout** | plan premium del taller y destacados de pago |
| IA | **Google Gemini** | sugerir la descripción de una pieza a partir de la foto |
| errores en producción | **Sentry** | entero y con traza, sin revisar registros a mano |
| servidor de aplicación | **gunicorn**, 1 worker y 4 hilos | el plan mínimo manda en RAM y en conexiones |
| despliegue | **Heroku**, región Europa | un comando, base gestionada y HTTPS incluido |
| HTTPS | **Let's Encrypt** por ACM del hosting | certificado automático, renovación y gratis |
| DNS | **Cloudflare**, plan gratuito | DNS rápido y gratis, con el proxy en gris (solo DNS) |
| dominio | **`cosknot.me`** | gratis el primer año con el pack de estudiante |
| integración continua | **GitHub Actions** | nada se sube sin pasar las pruebas |
| pruebas | **pytest** | pruebas sin red y sin base de datos real |
| copias de seguridad | `pg_dump` diario, cifrado, a R2, purga a 30 días | la base se puede reconstruir |

## por qué estas y no otras

**Flask y no Django.** Django trae administrador, ORM y autenticación hechos. Para
aprender eso esconde justo lo que hay que explicar: cómo se hashea una contraseña, cómo
se protege un formulario, cómo se modela un pedido. Con Flask cada pieza está escrita y
se puede señalar.

**PostgreSQL y no MongoDB.** El dominio es relacional por todas partes: un usuario tiene
un taller, un taller tiene obras, una obra acaba en pedidos, un pedido tiene mensajes.
Eso son claves foráneas, no documentos sueltos.

**Sin React ni Vue.** La web se renderiza en el servidor y tiene dos interacciones. Un
framework de frontend añadiría una compilación, un `node_modules` y un segundo lenguaje,
sin nada a cambio.

**Un solo worker en gunicorn.** El límite de intentos por IP vive en memoria del
proceso: con dos workers cada uno llevaría su cuenta y el cupo real sería el doble. Y
512 MB de RAM son el recurso escaso del plan.

**Cloudflare en gris (solo DNS).** Con el proxy naranja habría dos saltos: el
certificado del hosting fallaría la validación HTTP-01 y el contador de intentos vería la
IP de Cloudflare en lugar de la del visitante.

**Heroku y no Render.** Los dos valen. Heroku cuesta 12 $/mes (7 de servidor + 5 de base)
y el pack de estudiante da 312 $ de crédito, ya confirmados en la facturación, o sea 26
meses a cero desde el primer despliegue. Render es la alternativa gratuita el día que el
crédito se acabe.

## modelo de datos previsto

```
users            id, email, password_hash, role, created_at
creators         id, slug, name, specialty, location, bio, contact_email,
                 verified, image_key, stripe_account_id, premium_hasta, user_id
works            id, slug, creator_id, title, description, price_cents, currency,
                 status, image_key, destacada_hasta, created_at
orders           id, buyer_id, work_id, status, amount_cents, application_fee_cents,
                 stripe_payment_intent_id, paid_at, created_at
order_messages   id, order_id, author_id, body, created_at
email_outbox     id, clave, destinatario, asunto, cuerpo, estado, intentos, ...
```

Dos decisiones que ya están tomadas en el diseño:

- **importes en céntimos**, enteros, nunca decimales flotantes: un céntimo perdido en un
  redondeo es una discusión con el creador.
- **fecha de fin, no un booleano**, para el plan premium: así caduca solo y no hace falta
  ningún proceso que lo apague por la noche.

## dónde se despliega

```
aplicación   Heroku, dyno Basic, región Europa
base         Heroku Postgres Essential-0, 1 GB y 20 conexiones
DNS          Cloudflare, plan Free, en gris (sin proxy)
dominio      cosknot.me, gratis el primer año por el pack de estudiante
HTTPS        certificado automático de Heroku (Let's Encrypt, validación HTTP-01)
correo       Resend, dominio verificado con DKIM, SPF y DMARC
fotos        Cloudflare R2, 10 GB gratis
```

## configuración por variables de entorno

Ninguna clave va en el repositorio. Todo lo que cambia entre local y producción es una
variable de entorno, y hay un `.env.example` con los nombres y sin los valores:

```
SECRET_KEY  DATABASE_URL  APP_ENV
STRIPE_SECRET_KEY  STRIPE_PUBLISHABLE_KEY  STRIPE_WEBHOOK_SECRET  COMMISSION_PERCENT
R2_BUCKET  R2_ENDPOINT_URL  R2_ACCESS_KEY_ID  R2_SECRET_ACCESS_KEY  R2_PUBLIC_BASE_URL
RESEND_API_KEY  EMAIL_FROM
GEMINI_API_KEY  GEMINI_MODEL
SENTRY_DSN
```

La regla de diseño es que la web **arranque sin ninguna clave**: si falta el correo, los
avisos se quedan en cola; si falta el cobro, el botón de pagar no aparece y la web
explica por qué.

## lo que estas piezas permiten construir después

| función | con qué se hace |
|---|---|
| **suscripción premium** | Stripe Checkout + una fecha de fin en el taller |
| **intereses del comprador** | una tabla de especialidades favoritas por usuario; la portada ordena primero lo que le interesa |
| **destacar una pieza** | mismo cobro, con una fecha de fin en la pieza |
| **avisos de pedido** | Resend, con una cola de reintentos en base de datos |
| **sugerencia de ficha** | Gemini a partir de la foto, solo si el usuario lo pide |

## riesgos técnicos, ya asumidos

| riesgo | consecuencia | mitigación |
|---|---|---|
| un solo servidor | si cae, la web cae | `/healthz` y aviso diario por GitHub Actions |
| contador de intentos en memoria | se reinicia al reiniciar el proceso | aceptable con un solo worker |
| 20 conexiones de PostgreSQL | el pool se queda en 3 + 2 | configuración por variable de entorno |
| 512 MB de RAM | sin margen para procesos pesados | un worker; fotos fuera del servidor |
| crédito es un importe fijo | a 12 $/mes se agota en 26 meses desde el primer despliegue | alternativa gratuita ya comparada (Render); hoy el gasto real es 0 € |
| dependencia de Stripe | sin cuenta de cobro no hay ingresos | la web funciona sin cobro; solo se apaga esa parte |
