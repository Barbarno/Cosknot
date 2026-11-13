# marketplace: migraciones, cuentas, pedidos e imágenes

fecha: 2026-11-13
estado: aceptada

## decisión

Convertir el escaparate en un marketplace de verdad, en fases, sin cambiar de stack ni
de hosting.

- **Esquema**: Alembic directamente, sin `flask-migrate`. En PostgreSQL el esquema se
  migra al arrancar con un advisory lock de PostgreSQL para que los dos workers de
  gunicorn no migren a la vez. En SQLite (local y tests) se sigue usando
  `Base.metadata.create_all`, que es instantáneo y no necesita coordinación.
- **Cuentas**: tabla `users` con hash argon2id, roles `comprador` / `creador` /
  `admin`, Flask-Login para la sesión, CSRF de Flask-WTF en todos los POST y
  Flask-Limiter en el login. Cookie de sesión `HttpOnly`, `SameSite=Lax` y `Secure`
  solo cuando corre en Render (en local la web va por http y el navegador no enviaría
  una cookie `Secure`).
- **Pedidos**: tablas `orders` y `order_messages`. El estado del pedido lo decide una
  máquina de estados en `estados_pedido.py`, con tabla de transiciones y permisos por
  rol; las plantillas solo pintan los botones que esa función devuelve.
- **Precio**: `works.price_cents` (entero, céntimos) para poder cobrar, manteniendo
  `works.price_note` como texto libre para el escaparate.
- **Imágenes**: interfaz de almacenamiento con dos backends, `AlmacenLocal`
  (`static/uploads`, solo desarrollo) y `AlmacenR2` (Cloudflare R2 por la API
  compatible con S3 de boto3). En producción, si faltan las variables de R2, las
  subidas se desactivan con un mensaje y la app arranca igual.
- **CSP**: se mantiene cerrada y `img-src` solo se abre, sin comodines, al origen que
  diga `R2_PUBLIC_BASE_URL`.
- **Correo**: Resend por HTTP, nunca SMTP (Render free bloquea 25, 465 y 587). Backend
  de consola en desarrollo y en tests. El envío va en un hilo aparte con timeout de 5 s
  y un fallo de correo no tumba el pedido. Los avisos son nuevo encargo, cambio de
  estado y mensaje nuevo, siempre a la otra parte.
- **Pagos**: Stripe Connect con cuentas conectadas express, cobro con destination
  charges y `application_fee_amount` como comisión. Stripe Checkout alojado
  (redirección), así que no se incrusta `stripe.js`. Solo claves `sk_test_`.
  `COMMISSION_PERCENT` no tiene valor por defecto: sin él el cobro no se activa. El
  webhook verifica la firma y es idempotente.

## responsabilidad en los pagos

En esta configuración la plataforma es la responsable de los reembolsos, las disputas
y los saldos negativos de las cuentas conectadas. Es lo que describe la documentación
de Stripe para destination charges: el cargo se crea en la cuenta de la plataforma y
después se transfiere la parte del taller, así que la disputa la atiende la plataforma
y un saldo negativo en la cuenta conectada lo cubre la plataforma. Por eso el alta es
express (Stripe hace el KYC) y el cobro solo se activa con claves de pruebas.

## registro y errores

`LOG_LEVEL` fija el nivel del logger raíz (por defecto `INFO`). Sentry solo se
inicializa si existe `SENTRY_DSN` y la app no está en pruebas; el muestreo de trazas
sale de `SENTRY_TRACES_SAMPLE_RATE` y por defecto es 0, así que solo se envían errores.
`send_default_pii=False`. `/healthz` no cambia: sigue devolviendo `{"status": "ok"}` o
503 si la base no contesta.

## csp y la redirección a checkout

`form-action 'self'` puede bloquear la redirección posterior a un POST si el navegador
aplica esa directiva a los redirects. La opción más estrecha es añadir el origen exacto
`https://checkout.stripe.com` a `form-action`, y solo cuando el cobro está configurado.
No se añaden `script-src` ni `frame-src` de Stripe porque Checkout va alojado: no hay
JavaScript de Stripe en ninguna página propia.

## por qué

- **Alembic directo**: el proyecto usa SQLAlchemy a pelo, con la sesión en `g.db` y sin
  Flask-SQLAlchemy. `flask-migrate` obliga a instalar Flask-SQLAlchemy solo para
  envolver Alembic, y aquí no hace falta.
- **Advisory lock**: Render arranca dos workers y los dos ejecutan `create_app()`. Sin
  lock, los dos intentan migrar a la vez y uno revienta por DDL concurrente. Con el
  lock, uno migra y el otro espera y sigue.
- **argon2id**: es el algoritmo que recomienda OWASP para contraseñas y `argon2-cffi`
  ya trae los parámetros razonables. Se rehashea al entrar si los parámetros cambian.
- **Máquina de estados en Python**: la regla de negocio («quién puede dejar el pedido
  en qué estado») tiene que estar en un solo sitio y ser comprobable con tests. Si
  vive en la plantilla, el primer POST a mano se la salta.
- **`price_cents` además de `price_note`**: Stripe cobra en la unidad mínima de la
  moneda. Guardar céntimos evita hacer aritmética con cadenas como «desde 180 €».
- **R2 y no disco en Render**: el plan free de Render no tiene discos persistentes, así
  que subir fotos al disco del contenedor es perderlas en el siguiente despliegue.
  R2 tiene capa gratuita y habla S3, así que boto3 sirve sin SDK propio.
- **Subidas desactivadas sin claves**: la regla del proyecto es que falte una clave
  externa no tumbe la app. La ficha sigue enseñando la foto antigua de `static/img`.

## alternativas

- **`flask-migrate`**: descartado, arrastra Flask-SQLAlchemy.
- **`create_all` también en producción**: descartado, no permite cambiar columnas sin
  perder datos y ya nos pilló una vez con el esquema desincronizado.
- **Sesiones en Redis**: descartado, no hay Redis en el plan free y la cookie firmada
  de Flask basta para este tamaño.
- **JWT en el navegador**: descartado, más superficie de ataque (XSS se lleva el token)
  y no hace falta para una web renderizada en servidor.
- **Disco de Render**: descartado, es efímero.
- **Cloudinary o imgix**: válidos, pero R2 es más barato a este tamaño y no mete un
  tercero en el camino de las imágenes.
- **Guardar las fotos como BLOB en PostgreSQL**: descartado, engorda la base y las
  copias de seguridad.
- **`img-src *`**: descartado, abre la CSP a cualquier origen.

## cuándo revisar

- Si el catálogo pasa de unos miles de imágenes, mirar transformaciones en el borde
  (R2 + Worker o un CDN delante) para no servir el JPEG original.
- Si aparece más de un servidor con escritura, el límite del login en memoria de
  Flask-Limiter deja de valer; entonces toca un backend compartido.
- Si los pedidos crecen, mover la conversación a su propia tabla con adjuntos y
  notificaciones, y valorar WebSockets para el chat.
- Si el lock de Alembic da guerra en el arranque, sacar la migración a un job previo al
  despliegue.
