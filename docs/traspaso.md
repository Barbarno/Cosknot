# traspaso de sesión

Documento de estado para retomar el proyecto en otra sesión o para preparar la
exposición. Todo lo que hay aquí está comprobado contra el repositorio, no contra la
memoria de una conversación.

Fecha de este documento: 14 de noviembre de 2026.

---

## 1. qué es cosknot

Marketplace de cosplay. Los creadores publican ropa, props, pelucas y accesorios de
cualquier juego, serie o anime; los compradores les compran piezas o les piden un
encargo a medida. Cosknot actúa de intermediario, como Etsy o Airbnb pero solo de
cosplay: el creador pone el taller, la web pone el escaparate, la ficha, el pedido y
el cobro con comisión.

Equipo: Daniel Barrasa (CEO y CMO), Jesús Larrazabal (CTO), Daniel Torres (CFO).
Curso: 2.º de SMR.

---

## 2. estado real del repositorio

```
repo            Barbarno/Cosknot (público)
rama            main, sincronizada con origin, árbol limpio
pruebas         162 pasan en local (~13 s), sin red
CI              GitHub Actions en verde
python          3.13 (fichero .python-version)
desplegado      no todavía
```

Lo que funciona de punta a punta en local:

| pieza | estado |
|---|---|
| portada con creadores destacados y obras recientes | hecho |
| listado de creadores con filtro por especialidad | hecho |
| ficha de creador y ficha de obra | hecho |
| buscador en `/buscar?q=` | hecho |
| registro, entrada, salida, perfil con foto | hecho |
| publicación y edición de obras (con foto) | hecho |
| pedidos con estados y mensajería por pedido | hecho |
| cobro con Stripe Connect y comisión | hecho, apagado sin claves |
| avisos por correo con Resend y cola de reintentos | hecho, apagado sin claves |
| sugerencias de descripción con Gemini | hecho, botón oculto sin clave |
| `/nosotros`, 404 propia, `robots.txt`, `sitemap.xml` | hecho |
| `/healthz` para monitorización | hecho |
| copias de seguridad diarias cifradas a R2 + purga a 30 días | hecho, sin ejecutar aún |
| despliegue en Heroku | **bloqueado por la tarjeta** |

Un dato importante para la exposición: **la app arranca sin ninguna clave**. Si falta
una variable de servicio, esa función se apaga sola con un mensaje claro en vez de
romper el arranque. Se demuestra con `python scripts/comprobar_local.py`.

---

## 3. tecnologías, con versión y motivo

### lenguajes y framework

| tecnología | versión | para qué | por qué esta |
|---|---|---|---|
| Python | 3.13 | todo el backend | es lo que estamos aprendiendo en SMR |
| Flask | 3.1.3 | servidor web y rutas | microframework: se ve cada pieza, no hay magia |
| Jinja2 | (incluido en Flask) | plantillas HTML | viene con Flask, sin capa extra |
| SQLAlchemy | 2.1.8 | base de datos desde Python | evita escribir SQL a mano y protege de inyección |
| Alembic | 1.20.1 | migraciones del esquema | cada cambio de tablas queda versionado y reversible |
| psycopg | 3.3.9 | conector de PostgreSQL | el driver moderno; el antiguo está en mantenimiento |
| SQLite | del sistema | base de datos en local | arrancar sin instalar nada |

### interfaz

| tecnología | para qué |
|---|---|
| HTML + CSS propio | 32 KB de CSS escrito a mano, sin Bootstrap ni Tailwind |
| JavaScript propio | 4 KB: menú de sugerencias y un par de interacciones |
| SVG propio | logotipo y marca, escalables y de menos de 2 KB |

No se usa ningún framework de frontend. Es una decisión consciente: para una web de
plantillas renderizadas en servidor, React o Vue solo añadirían una compilación más.

### autenticación y seguridad

| tecnología | versión | para qué |
|---|---|---|
| Flask-Login | 0.6.3 | sesiones de usuario |
| Flask-WTF | 1.3.0 | formularios con token CSRF |
| argon2-cffi | 25.1.0 | hash de contraseñas (Argon2id) |
| email-validator | 2.3.0 | validar correos en el registro |
| Flask-Limiter | 4.1.1 | límite de intentos de entrada y de alta |
| ProxyFix (de Werkzeug) | — | confiar en un solo proxy delante, el de Heroku |

Las contraseñas nunca se guardan en claro: se guarda el hash Argon2id, que es el
recomendado hoy por OWASP. El token CSRF va en todos los formularios que modifican
datos.

### servicios externos

| servicio | función | plan | coste |
|---|---|---|---|
| Heroku | ejecutar la app (dyno) + PostgreSQL | Basic + Essential-0 | 12 $/mes **cubiertos por el crédito** |
| Cloudflare | DNS del dominio, sin proxy | Free | 0 € |
| Resend | correo saliente (avisos de pedido) | Free: 3.000/mes, 100/día | 0 € |
| Cloudflare R2 | almacenar las fotos de obras y perfiles | Free: 10 GB | 0 € |
| Stripe | cobro a comprador y comisión al creador | sin cuota fija, 1,5 % + 0,25 € por cobro | 0 € si no hay ventas |
| Google Gemini | sugerir descripción de una obra | capa gratuita | 0 € |
| Sentry | errores en producción | Free | 0 € |
| GitHub Actions | pruebas y copias de seguridad | gratis en repo público | 0 € |
| Namecheap | dominio `cosknot.me` | cupón del GitHub Student Pack | 0 € el primer año |

Versiones en `requirements.txt`, todas fijadas con `==`. `pip check` sale limpio.

### por qué Heroku y no otro

Está razonado en `docs/decisions/0003-heroku-hosting.md`. Resumen: el pack de
estudiante da 13 $/mes durante 24 meses, el plan mínimo real son 12 $/mes, y Heroku
da dominio propio con HTTPS automático, base gestionada y despliegue con `git push`.
La alternativa gratuita sin tarjeta es Render free + Neon free, con arranque en frío
de ~50 s; el repo aguanta las dos porque el `Procfile` y `DATABASE_URL` son iguales.

---

## 4. suscripciones y cuentas

Todo lo que hay dado de alta, con su titular y su fecha límite.

| servicio | cuenta | plan | caduca / límite | tarjeta |
|---|---|---|---|---|
| GitHub Student Pack | cuenta de estudiante aprobada | — | mientras seas estudiante | no |
| Heroku | `danielbarrasaperezz@gmail.com` | crédito 312 $ (13 $/mes × 24) | **noviembre 2028** | **sí, obligatoria** |
| Namecheap | la del registro | `.me` gratis 1 año | **noviembre 2027** | no (cupón) |
| Cloudflare | la del registro | Free | sin caducidad | no |
| Resend | la del registro | Free | 3.000 correos/mes | no |
| Cloudflare R2 | la misma de Cloudflare | Free | 10 GB | no |
| Stripe | pendiente de crear | — | — | no hasta cobrar |
| Sentry | pendiente de crear | Free | 5.000 errores/mes | no |
| Gemini | pendiente de clave | Free | cuota diaria | no |

**El crédito de Heroku no se renueva**: son 312 $ y cuando se acaban, se acaban. A
12 $/mes dan para 26 meses, así que cubren de sobra la exposición de mayo-junio de
2027.

**Namecheap renueva solo.** Hay que apagar *Auto-Renew* en
`ap.www.namecheap.com/domains/list/` → `cosknot.me` → Manage. Es el único cargo que
puede aparecer sin que lo pidas, y cae en noviembre de 2027, después de la defensa.

---

## 5. dominio, DNS y correo

```
dominio      cosknot.me  (Namecheap, gratis el primer año)
nameservers  razvan.ns.cloudflare.com
             zainab.ns.cloudflare.com
zona         Cloudflare, plan Free, estado ACTIVE, todo en gris (sin proxy)
```

Registros que hay ahora mismo:

| tipo | nombre | valor | para qué |
|---|---|---|---|
| CNAME | `rsend` | `rsend-euw1.forge.rmta.net` | SPF del subdominio de envío |
| CNAME | `send` | `send.forge.rmta.net` | envío de Resend |
| TXT | `resend._domainkey` | `p=MIGf...QIDAQAB` | firma DKIM |
| TXT | `_dmarc` | `v=DMARC1; p=none;` | política de correo |
| A | `@` | `192.0.2.1` | **provisional**, se sustituye por el CNAME de Heroku |

`cosknot.me` está **verificado en Resend** y ya ha enviado correo real desde
`hola@cosknot.me`. Falta cambiar el `A` de relleno por el `CNAME` a
`<app>.herokuapp.com` cuando exista la app.

**Cloudflare va en gris, no en naranja.** Dos motivos técnicos, no estéticos:

1. El certificado de Heroku se valida por HTTP-01: con el proxy naranja delante,
   Cloudflare puede cachear o redirigir el fichero de validación y el certificado se
   queda en *Failing* sin decir por qué.
2. `ProxyFix` confía en un solo salto (el router de Heroku). Con naranja habría dos, y
   el limitador de intentos contaría la IP de Cloudflare en lugar de la del visitante.

---

## 6. marca y logo

Los dos ficheros están en `static/img/`, son SVG escritos a mano y pesan menos de 2 KB
entre los dos.

| fichero | qué es | dónde se usa |
|---|---|---|
| `logo.svg` | logotipo completo: marca + la palabra «Cosknot» | cabecera, pie, correos |
| `logo-mark.svg` | solo la marca cuadrada, 64×64 | favicon, avatar, redes |

Qué representa: una **C** en negro sobre un cuadrado salmón, con una **aguja e hilo**
en crema atravesándola y un hilo suelto que sale hacia la derecha. Es la idea de
coser, que es lo que hacen los creadores.

Paleta, tomada del CSS y del SVG:

| uso | color |
|---|---|
| salmón (marca) | `#fa8072` |
| salmón oscuro (enlaces, hover) | `#b8443a` |
| salmón profundo (texto sobre claro) | `#8a2f24` |
| salmón suave (fondos) | `#fde3de` |
| negro de marca | `#111111` |
| tinta de texto | `#222222` |
| crema (sobre salmón) | `#f7f1e8` |
| gris de superficie | `#f5f5f5` |

Tipografía: la del sistema (`Segoe UI`, `Arial Black`, `system-ui`). Sin fuentes
descargadas, sin peticiones a Google Fonts: cero dependencias externas y cero
parpadeo de texto.

---

## 7. cómo arrancar en local

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m flask sembrar         # crea el esquema y carga el catálogo de ejemplo
python -m flask run
```

En SQLite (local y pruebas) el esquema se crea solo con `create_all`, así que no hay
que aplicar migraciones: `flask sembrar` deja la base lista. En PostgreSQL manda
Alembic y se aplica con `alembic upgrade head`, que es lo que ejecuta el proceso
`release` en cada despliegue.

Sin ninguna variable de entorno funciona: usa SQLite y crea `cosknot.db`. Para
comprobarlo de forma automática:

```bash
python scripts/comprobar_local.py
```

Pruebas:

```bash
python -m pytest -q
```

---

## 8. estructura del repositorio

```
app.py               fábrica de la app, rutas públicas, ProxyFix, limitador
wsgi.py              punto de entrada de gunicorn
models.py            User, Creator, Work, Order, OrderMessage, EmailOutbox
db.py                motor, sesión, normalización de DATABASE_URL
auth.py              registro, entrada, salida
cuenta.py            perfil, foto, alta de Stripe Connect
pedidos.py           pedidos, estados, mensajería
pagos.py             cobro con Stripe y webhook
cobros.py            cálculo de comisión e importes
correo.py            envío con Resend, con timeout corto
outbox.py            cola de reintentos de correo (tabla email_outbox)
avisos.py            textos de los avisos
almacenamiento.py    subida de fotos a R2 (o disco en local)
sugerencias.py       descripciones con Gemini
busqueda.py          buscador
seguridad.py         hash de contraseñas, utilidades
migraciones.py       aplica Alembic con un advisory lock de PostgreSQL
seed.py              catálogo de ejemplo
formularios.py       formularios WTForms
estados_pedido.py    máquina de estados del pedido
importes.py          formato de precios en euros
admin.py             utilidades de administración
fotos.py             validación de imágenes subidas
extensiones.py       objetos compartidos (login, csrf, limiter)

migrations/          7 versiones de esquema
templates/           16 plantillas Jinja2
static/              32 KB de CSS, 4 KB de JS, logo SVG, 24 fotos
scripts/             despliegue, DNS, copias, comprobación local
docs/                documentación, decisiones y este traspaso
```

Rutas principales:

```
/                          portada
/creadores                 listado con filtro
/creadores/<slug>          ficha de creador
/obras/<slug>              ficha de obra
/obras/nueva               publicar obra
/obras/<id>/editar         editar obra
/obras/<id>/foto           subir foto
/obras/<id>/borrar         borrar obra
/obras/sugerencias         sugerencias con Gemini
/buscar?q=                 buscador
/registro, /entrar, /salir cuentas
/perfil, /perfil/foto      perfil propio
/cuenta/stripe/alta        conectar cobros
/pedidos/<id>/pagar        pagar un pedido
/stripe/webhook            confirmación de Stripe
/creadores/<id>/verificar  verificar creador (admin)
/nosotros                  página de equipo
/healthz                   salud del servicio
/robots.txt, /sitemap.xml  SEO
```

---

## 9. variables de entorno

Ninguna es obligatoria para arrancar. Todas están documentadas en
`docs/variables-entorno.md` y planteadas en `.env.example`.

| variable | activa | sin ella |
|---|---|---|
| `SECRET_KEY` | sesiones y CSRF | se genera una temporal (mal en producción) |
| `DATABASE_URL` | PostgreSQL | usa SQLite local |
| `APP_ENV=production` | modo producción | modo desarrollo |
| `R2_ENDPOINT_URL`, `R2_BUCKET`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_PUBLIC_BASE_URL` | fotos en la nube | fotos en `static/uploads` |
| `RESEND_API_KEY`, `EMAIL_FROM`, `EMAIL_REPLY_TO` | avisos por correo | los avisos se quedan en `email_outbox` |
| `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET`, `COMMISSION_PERCENT` | cobro y comisión | los pedidos no se pueden pagar |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | sugerencias | el botón no se muestra |
| `SENTRY_DSN` | errores | no se reportan |
| `PROXY_FIX_X_FOR`, `PROXY_FIX_X_PROTO` | confiar en el proxy | valores por defecto seguros |
| `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_RECYCLE`, `DB_POOL_TIMEOUT` | pool de conexiones | 3 + 2, acorde al límite de 20 de Heroku |

**El repo no contiene ninguna clave.** Las que se han usado durante la preparación se
pasaron por chat y hay que rotarlas: la de Resend en `resend.com/api-keys` y el token
de Cloudflare en `dash.cloudflare.com/profile/api-tokens`.

---

## 10. lo que falta, en orden

| # | qué | quién | desbloquea |
|---|---|---|---|
| 1 | método de pago en Heroku + aplicar la oferta de estudiante | tú | crear la app |
| 2 | `python scripts/desplegar_heroku.py --ejecutar` | yo, en un comando | app + base + variables + push |
| 3 | `CNAME @` y `www` hacia `<app>.herokuapp.com`, borrar el `A` de relleno | yo, con el token | dominio sirviendo |
| 4 | alta de Stripe (claves y webhook) | tú + yo | cobrar con comisión |
| 5 | bucket R2 y sus 5 variables | tú + yo | fotos en producción |
| 6 | `gh secret set` de los valores y `SITIO_URL` | yo | que corran las copias y el healthz |
| 7 | apagar Auto-Renew en Namecheap | tú | que no haya cargos en 2027 |
| 8 | actualizar el `README.md` | yo | dice que comprar «todavía no» y ya está hecho |

El punto 8 es un desfase real, no una errata: el `README` se escribió antes de la fase
de pedidos y cobros. Conviene corregirlo antes de enseñar el repositorio.

---

## 11. para la exposición

Tres ideas que se defienden bien y se ven en la demo:

**1. La web arranca sin claves.** Se borra el `.env`, se lanza, y funciona. Cada
servicio que falta se apaga solo: sin Stripe no se cobra, sin Resend el aviso queda en
cola, sin Gemini el botón no aparece. Eso es diseño, no suerte: son variables
opcionales con valores por defecto seguros.

**2. Un solo worker, y está razonado.** El `Procfile` no es una línea copiada; tiene
un comentario que explica por qué un worker con 4 hilos (el limitador vive en memoria y
los 512 MB del dyno son el recurso escaso) y por qué `--preload` está prohibido (el hilo
de la cola de correo se duplicaría tras el fork).

**3. Todo tiene pruebas y todo está documentado.** 162 pruebas sin red, cada función
con las suyas. Y las decisiones están escritas: por qué Heroku, por qué Cloudflare en
gris, por qué la tarjeta es obligatoria aunque el crédito cubra el gasto. Un tribunal
pregunta «¿y por qué esto?» y la respuesta está en `docs/decisions/`.

Lo que se puede enseñar en pantalla, en este orden: portada → ficha de obra →
buscador → registro → publicar obra con sugerencia de Gemini → pedido → `/healthz`.

### guion corto de la parte técnica

> Cosknot es un marketplace de cosplay hecho con Flask y PostgreSQL. El creador
> publica su obra, el comprador le escribe y le paga dentro de la web; nosotros
> cobramos una comisión por la intermediación.
>
> El stack es deliberadamente pequeño: Flask en vez de Django porque queremos ver cada
> pieza, SQLAlchemy para no escribir SQL a mano, Alembic para que cada cambio de la
> base quede versionado, y Jinja2 para renderizar en servidor. No hay React: para esta
> web sería una compilación más sin nada a cambio.
>
> La seguridad no es un añadido: contraseñas con Argon2id, CSRF en todos los
> formularios, límite de intentos por IP y un proxy de confianza declarado
> explícitamente para que el limitador cuente la IP del visitante y no la de Heroku.
>
> Todo está en servicios gratuitos o cubiertos por el pack de estudiante: Heroku con
> 312 $ de crédito, Cloudflare para el DNS, Resend para el correo, R2 para las fotos.
> El coste del proyecto hasta la entrega es cero.

---

## 12. comandos de referencia

```bash
# local
python -m flask run
python scripts/comprobar_local.py
python -m pytest -q
pip check

# base de datos
alembic upgrade head                            # aplica migraciones (PostgreSQL)
alembic revision --autogenerate -m "cambio"     # genera una nueva
python -m flask sembrar                         # catálogo de ejemplo
python -m flask migrar-fotos                    # mueve fotos al almacenamiento nuevo
python -m flask hacer-admin correo@ejemplo.com  # da rol de administrador

# despliegue
python scripts/desplegar_heroku.py              # plan, no toca nada
python scripts/desplegar_heroku.py --ejecutar   # ejecuta
python scripts/desplegar_heroku.py --sin-dominio --ejecutar

# DNS
CLOUDFLARE_API_TOKEN=... python scripts/dns_cloudflare.py cosknot.me registros.json --ejecutar

# copias de seguridad
python scripts/heroku_config.py                 # lee las variables de la app
```

---

## 13. decisiones, con su documento

| decisión | documento |
|---|---|
| stack, despliegue y dominio | `docs/decisions/0001-stack-despliegue-dominio.md` |
| modelo de marketplace, cuentas, pedidos e imágenes | `docs/decisions/0002-marketplace-cuentas-pedidos-imagenes.md` |
| Heroku como hosting, coste 12 $ y sus seis riesgos | `docs/decisions/0003-heroku-hosting.md` |

Riesgos asumidos y ya documentados en la decisión 0003: un solo dyno (si cae, la web
cae), contador de intentos en memoria (se reinicia con el dyno), 20 conexiones de
PostgreSQL como techo, 512 MB de RAM, arranque en frío tras un despliegue, y
dependencia de un proveedor con crédito temporal.
