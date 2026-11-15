# CTO: necesidades tecnológicas

Todo lo de esta página está **elegido y presupuestado**, no instalado. Es la decisión
técnica previa a construir.

## las cinco que importan

Esto es lo que responde al enunciado. Cinco líneas:

| qué | qué vamos a usar | por qué |
|---|---|---|
| **lenguaje** | **Python 3.13** | legible, un solo lenguaje para la web y los scripts |
| **framework web** | **Flask 3.1** + **Jinja2** | microframework: cada pieza se ve y se explica en clase |
| **base de datos** | **PostgreSQL 16** en **Neon** (SQLite en local) | el dominio es relacional y el SQL es el mismo en los dos |
| **acceso a datos** | **SQLAlchemy 2** + **Alembic** | sin SQL a mano; cada cambio de esquema queda versionado |
| **despliegue y HTTPS** | **Google Cloud Run** + **Neon** | arranca y se apaga solo, escala de 0 a N instancias, certificado incluido y 0 € hasta muy por encima de 100 clientes |

Y así se dice en voz alta, treinta segundos:

> Usamos Python con Flask y PostgreSQL, y lo ponemos en Google Cloud Run con la base en
> Neon. Cloud Run arranca instancias cuando hay visitas y las apaga cuando no, así que el
> coste con cero usuarios es cero y con cien clientes sigue siendo cero: no hay un servidor
> que administrar ni un techo de memoria que subir. Los demás son servicios que se
> contratan cuando hacen falta —Stripe para cobrar, Resend para los correos, Cloudflare
> para el dominio y las fotos—, todos con plan gratuito y ninguno pagado hasta que haya
> ventas.

El resto de la página es el anexo: qué hay detrás de cada una de esas cinco, alternativas
que descartamos y por qué. Está para quien pregunte, no para leerlo de arriba abajo.

Si la pregunta es «¿y esto para qué sirve?», la respuesta corta por tecnología y las
preguntas típicas con su contestación están en [`09-preguntas.md`](09-preguntas.md).

## anexo: el resto, por necesidad

| necesidad | solución elegida | por qué |
|---|---|---|
| servir páginas web | **Flask 3.1** sobre **Python 3.13** | microframework: cada pieza se ve y se explica en clase |
| plantillas HTML | **Jinja2** | renderizado en servidor, sin compilar frontend |
| base de datos | **PostgreSQL 16** en producción (Neon), **SQLite** en local | el dominio es relacional y el SQL es el mismo |
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
| servidor de aplicación | **gunicorn**, 2 workers y 4 hilos por instancia | cada instancia atiende varias peticiones y Cloud Run levanta más si hace falta |
| despliegue | **Google Cloud Run**, región `europe-west1` (Bélgica) | despliega desde el código, escala solo y no hay máquina que administrar |
| base de datos gestionada | **Neon**, PostgreSQL 16 con *pooler* | copias, parches y conexiones incluidos; el plan gratuito da 0,5 GB |
| HTTPS | certificado automático de Cloud Run | lo emite y lo renueva la plataforma; no se toca ningún fichero |
| trabajos periódicos | **Cloud Run Jobs** + **Cloud Scheduler** | la cola de correos se vacía cada minuto sin un proceso permanente |
| migraciones | un **Cloud Run Job** con `alembic upgrade head` | se aplican antes de estrenar la versión nueva |
| DNS | **Cloudflare**, plan gratuito | DNS rápido y gratis; el proxy se puede dejar en gris (solo DNS) |
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

**Gemini y no OpenAI ni Claude.** Las tres sirven para lo mismo: escribir la descripción
de una pieza a partir de su foto. Se elige Gemini por tres razones concretas. Tiene capa
gratuita sin tarjeta, con un límite diario muy por encima de lo que generaría un catálogo
de este tamaño. Acepta la imagen en la misma llamada, así que la foto no viaja antes a
ningún sitio. Y el cliente de Python son cuatro líneas, sin SDK propio que mantener.

La función es **opcional por diseño**: si `GEMINI_API_KEY` no está, el formulario de una
pieza funciona igual y simplemente no aparece el botón de sugerir. Ninguna otra parte del
sitio depende de la IA, así que una caída del proveedor no rompe nada.

**El contador de intentos vive en la base de datos, no en memoria.** Con Cloud Run hay
varias instancias a la vez y cada una empezaría su propia cuenta: el cupo real por IP se
multiplicaría por el número de instancias. Por eso el límite es una tabla
(`intentos`: clave, contador, expira) con un incremento atómico, y vale igual con una
instancia que con veinte. Es la decisión que hace posible escalar sin abrir un agujero
en el inicio de sesión.

**Cloudflare en gris (solo DNS).** Con el proxy naranja el contador de intentos vería la
IP de Cloudflare en lugar de la del visitante, y filtrar por IP dejaría de significar nada.
En gris, la IP que llega es la real.

**Cloud Run y no Heroku.** Heroku cobra 12 $/mes (7 de servidor + 5 de base) y el plan
básico da 512 MB, una sola instancia que se reinicia a diario y 20 conexiones a la base.
Dimensionado para 100 clientes eso se queda corto justo donde importa —procesos y
memoria— y arreglarlo cuesta entre 26 y 60 $/mes. Cloud Run da hasta 4 GB por instancia,
levanta instancias solo cuando hay visitas y el tramo gratuito (2 millones de peticiones y
180.000 vCPU-segundo al mes) no se roza ni con 100 talleres. El crédito de 312 $ del pack
de estudiante sigue intacto, como red de seguridad.

**Cloud Run y no Render.** Render es más rápido de montar, pero su plan gratuito duerme el
servicio a los 15 minutos sin visitas y su PostgreSQL gratuito caduca a los 30 días. Para
que esté siempre en pie hay que pagar, y entonces se paga por algo peor que Cloud Run.

**Cloud Run y no Oracle Cloud.** Oracle *Always Free* da más máquina: 24 GB de RAM, 200 GB
de disco y sin fecha de caducidad. Se descartó por tres motivos, y el tercero es el que
decide. Uno: Cloud Run ya cubre el requisito de 100 clientes sin administrar nada, así que
ese hardware extra no compra nada que necesitemos. Dos: administrar el sistema
operativo, el certificado y las copias cuesta más horas que el dinero que ahorra. Tres: la
instancia ARM gratuita no siempre está disponible (*out of host capacity* en muchas
regiones), y la alternativa AMD de 1 GB tiene menos procesador que una instancia de Cloud
Run. Lo que sí se queda de esa comparación es la lección: **el trabajo está dimensionado
para 100 clientes, no para un portátil**.

**Sin Docker.** Cloud Run construye la imagen él solo a partir de `requirements.txt` y un
comando de arranque (`GOOGLE_ENTRYPOINT`): detecta el lenguaje, instala y arranca. Un
`Dockerfile` sería una capa más que mantener y explicar sin resolver nada que no esté ya
resuelto. Si algún día hace falta control total de la imagen, se añade en una tarde y la
plataforma lo acepta tal cual.

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

## dimensionado para 100 clientes

El trabajo no se entrega con un servidor de juguete: está escrito para que, si mañana hay
100 talleres, no haya que cambiarlo. Esto es lo que eso significa en números y en piezas.

| qué | con 100 talleres | qué lo absorbe |
|---|---|---|
| piezas en catálogo | ~1.000 filas | una tabla pequeña, ni se nota |
| fotos | ~3 GB (2 por pieza, 1,5 MB) | R2: 10 GB gratis, fuera del servidor |
| base de datos | menos de 50 MB | Neon: 0,5 GB gratis |
| visitas en hora punta | 3–5 peticiones por segundo | un puñado de instancias de Cloud Run |
| correos | decenas al mes | Resend: 3.000/mes gratis |
| procesos | varias instancias web + una tarea programada | Cloud Run (0 a N) + Cloud Run Job |

```
Cloudflare          cosknot.me · DNS · fotos en R2
   │
Cloud Run           0 a N instancias de Flask · hasta 4 GB · 0 € en este volumen
   │
Neon Postgres       base gestionada · pooler · copias incluidas
   │
Cloud Run Job       vaciar la cola de correos, cada minuto (Cloud Scheduler)
   │
Stripe · Resend · Gemini   los servicios de siempre, sin cambios
```

Cinco piezas y cada una tiene su porqué. Lo que hace que aguante no es la máquina: es que
**no hay un número fijo de instancias**. Con una instancia y 512 MB el techo llega el día
que dos clientes suben fotos a la vez; aquí el techo lo pone la factura, y la factura
empieza a subir muy por encima de lo que este proyecto va a generar.

Lo honesto que hay que saber decir: **el coste con cero usuarios es cero y con cien
clientes sigue siendo cero**, porque lo que se paga es el tiempo de ejecución, no el
servidor.

## dónde se despliega

```
aplicación   Google Cloud Run, región europe-west1, 1 GB por instancia
arranque     gunicorn 2 workers × 4 hilos, escuchando en $PORT
base         Neon PostgreSQL 16 con pooler, 0,5 GB y copias incluidas
migraciones  Cloud Run Job con alembic upgrade head, antes de estrenar versión
cola         Cloud Run Job + Cloud Scheduler, cada minuto
DNS          Cloudflare, plan Free, proxy en gris (solo DNS)
dominio      cosknot.me, gratis el primer año por el pack de estudiante
HTTPS        certificado automático de Cloud Run, renovado por la plataforma
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

Además de esas, Cloud Run usa cuatro ajustes que no son secretos y van en el despliegue:

```
PORT                  lo pone la plataforma; la web solo tiene que escuchar en él
GOOGLE_PYTHON_VERSION 3.13
GOOGLE_ENTRYPOINT     gunicorn app:app --bind :$PORT --workers 2 --threads 4
APP_BASE_URL          https://cosknot.me, para los enlaces de los correos
```

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
| arranque en frío | la primera visita tras un rato sin tráfico tarda 1–3 s | se acepta; se quita dejando una instancia mínima encendida, que cuesta unos euros |
| dependencia de Google | si el tramo gratuito cambia, hay que pagar o mudarse | el código no cambia: el mismo despliegue se va a Heroku, con los 312 $ de crédito como red |
| dos proveedores en vez de uno | Cloud Run y Neon hay que mirarlos por separado | Neon habla PostgreSQL estándar: lo único que cambia es `DATABASE_URL` |
| contador de intentos en base de datos | una escritura por intento de acceso | tabla de tres columnas con índice por caducidad; es el precio de poder escalar |
| copias de Neon | el plan gratuito guarda poco historial | `pg_dump` diario y cifrado a R2, purga a 30 días |
| dependencia de Stripe | sin cuenta de cobro no hay ingresos | la web funciona sin cobro; solo se apaga esa parte |
