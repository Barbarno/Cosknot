# despliegue en heroku

Manual de montaje, paso a paso, tal como está desplegado. La decisión y el porqué
están en `docs/decisions/0003-heroku-hosting.md`; aquí solo van los pasos y los
comandos.

| qué | valor |
|---|---|
| hosting | Heroku, un dyno **Basic** (512 MB, siempre encendido) |
| base de datos | Heroku Postgres **Essential-0** (1 GB, 20 conexiones, sin rollback) |
| Python | 3.13 (`.python-version`, y el mismo que usa el CI) |
| servidor | gunicorn `--workers 1 --threads 4 --timeout 50` (Procfile) |
| migraciones | proceso `release`: `alembic upgrade head` |
| dominio | `cosknot.es` y `www.cosknot.es` por Cloudflare en modo DNS only |
| HTTPS | certificado automático de Heroku (ACM) |
| copias | `pg:backups:schedule` + volcado diario a R2 (`docs/backups.md`) |
| coste | **12 $/mes** (7 $ dyno + 5 $ Postgres), tope 13 $ del crédito de estudiante |

Antes de empezar: `heroku --version`, `git --version` y un repositorio con la rama
`main` limpia. Los pasos 5 a 8 se pueden hacer en otro orden; el 4 solo funciona
cuando el 2 y el 3 están hechos.

## 1. crédito de estudiante

1. Entra en https://education.github.com/pack con la cuenta de GitHub y pide el
   **GitHub Student Developer Pack**.
2. Dentro del pack, activa la oferta de Heroku: son **13 $/mes durante 12 meses**, sin
   tarjeta.
3. Comprueba en https://dashboard.heroku.com/account/billing que el crédito aparece
   aplicado. Si no aparece, el despliegue se cobra a la tarjeta y el tope de 13 $ deja
   de existir.

El plan cabe en el crédito con 1 $ de margen: 7 + 5 = 12. Subir el dyno a Standard
(25 $) o el Postgres a Essential-1 (10 $ más) rompe el tope.

## 2. crear la app y la base

```bash
heroku login
heroku create cosknot --region eu
heroku buildpacks:set heroku/python -a cosknot
heroku addons:create heroku-postgresql:essential-0 -a cosknot --wait
```

- `--region eu` deja el dyno en Europa, cerca de los usuarios.
- `heroku create` añade el remoto `heroku` al repositorio.
- El addon crea la base y define `DATABASE_URL` en los config vars. La cadena lleva
  credenciales que Heroku rota: no se copia al repositorio ni a un `.env` versionado.

Comprobar:

```bash
heroku addons -a cosknot
heroku config -a cosknot
heroku pg:info -a cosknot
```

`heroku pg:info` tiene que decir `Plan: Essential-0` y `Connections: 20`.

## 3. config vars

```bash
heroku config:set -a cosknot \
  APP_ENV=production \
  SECRET_KEY="$(python -c 'import secrets;print(secrets.token_hex(32))')" \
  PROXY_FIX_X_FOR=1 \
  PROXY_FIX_X_PROTO=1 \
  RATELIMIT_STORAGE_URI=memory:// \
  DB_POOL_SIZE=3 \
  DB_MAX_OVERFLOW=2 \
  EMAIL_ASYNC=1
```

Después, las claves de cada servicio, cuando existan (pasos 6, 7 y 8):

| variable | de dónde sale |
|---|---|
| `R2_ENDPOINT_URL`, `R2_BUCKET`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_PUBLIC_BASE_URL` | paso 6 |
| `IMAGE_STORAGE=r2` | paso 6 |
| `RESEND_API_KEY`, `EMAIL_FROM`, `EMAIL_REPLY_TO` | paso 7 |
| `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET`, `COMMISSION_PERCENT` | paso 8 |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | opcional; sin ellas el botón de sugerencias no aparece |

`DATABASE_URL` no se fija a mano: la pone el addon. La lista completa está en
`docs/variables-entorno.md`.

`APP_ENV=production` no es imprescindible (Heroku define `DYNO` y la app lo detecta
sola), pero dejarlo escrito evita sorpresas si algún día se ejecuta el proceso en otro
sitio.

## 4. primer despliegue y migraciones

```bash
git push heroku main
```

El push hace tres cosas, en este orden:

1. **build**: instala `requirements.txt` con el Python de `.python-version`.
2. **release**: ejecuta `alembic upgrade head` con la versión nueva del código. Si la
   migración falla, el despliegue se para y el dyno viejo sigue sirviendo.
3. **web**: arranca gunicorn con el Procfile.

```bash
heroku logs --tail -a cosknot
heroku ps -a cosknot
```

El log del release tiene que terminar en `Running upgrade ... -> 0007`. El del web, en
`Listening at: http://0.0.0.0:$PORT`.

Sembrar el catálogo de ejemplo (solo la primera vez y solo si la base está vacía):

```bash
heroku run flask sembrar -a cosknot
```

Sin `SEED_ON_START=1` la app **no** siembra sola en producción: la base de un
marketplace real no se llena de datos de demo por arrancar.

## 5. dominio, Cloudflare y certificado

### 5.1 añadir los dominios en Heroku

```bash
heroku domains:add cosknot.es -a cosknot
heroku domains:add www.cosknot.es -a cosknot
heroku domains -a cosknot
```

`heroku domains` devuelve el destino que hay que poner en el DNS
(`<algo>.herokudns.com` para un CNAME, o la IP del router para un registro A).

### 5.2 DNS en Cloudflare: nube gris

En el panel de Cloudflare, en la zona `cosknot.es`:

| tipo | nombre | contenido | proxy |
|---|---|---|---|
| CNAME | `www` | el `<algo>.herokudns.com` que dio Heroku | **DNS only** (gris) |
| CNAME | `@` | el mismo destino | **DNS only** (gris) |

Cloudflare aplana el CNAME del dominio raíz, así que `cosknot.es` funciona sin un
registro A fijo. Si el proveedor de DNS no aplana, el raíz necesita un ALIAS/ANAME.

**Nube gris, no naranja.** Es la decisión de `docs/decisions/0003`, y no es estética:

- Con naranja hay **dos** proxies delante de la app (Cloudflare y el router de
  Heroku). `ProxyFix` está configurado con un solo salto y la IP del cliente se leería
  mal: el límite de intentos contaría la IP del proxy y un usuario podría agotar el
  cupo de todos.
- El certificado automático de Heroku (ACM) valida el dominio con **HTTP-01**, que
  consiste en servir un fichero desde el propio dominio. Si Cloudflare está en naranja
  y cachea o redirige esa ruta, la validación falla y el certificado no se emite.
  Tampoco se puede usar el modo "Full (strict)" con el certificado de Cloudflare sin
  montar antes el de Heroku.

### 5.3 activar el certificado

```bash
heroku certs:auto:enable -a cosknot
heroku certs:auto -a cosknot
```

El estado pasa de `Creating` a `Cert Issued` en unos minutos, siempre que:

1. el DNS ya resuelva al destino de Heroku (propagación de minutos a una hora);
2. Cloudflare esté en **gris** durante la emisión;
3. `http://cosknot.es/.well-known/acme-challenge/...` sea accesible sin redirección a
   HTTPS.

Si se queda en `Failing`, se mira `heroku certs:auto -a cosknot` y se comprueba el DNS
con `nslookup cosknot.es 1.1.1.1`. Cuando el certificado está emitido, se puede pasar
Cloudflare a naranja cambiando `PROXY_FIX_X_FOR=2`, pero eso ya es otra decisión y hay
que probar antes que el límite de intentos sigue contando IPs distintas.

### 5.4 comprobar

```bash
curl -sI https://cosknot.es/healthz
curl -s  https://cosknot.es/healthz
```

Tiene que dar `200` y `{"status":"ok"}`. `/healthz` ejecuta un `SELECT 1`: un 503 aquí
es problema de base de datos, no de gunicorn.

## 6. imágenes en Cloudflare R2

1. En https://dash.cloudflare.com → **R2** → **Create bucket**. Nombre `cosknot`, sin
   dominio público.
2. Dentro del bucket, **Settings → Public access**: activa el subdominio `r2.dev` o, si
   hay dominio propio, conecta `img.cosknot.es` con **Custom domain**. Ese es el valor
   de `R2_PUBLIC_BASE_URL`.
3. **Manage R2 API tokens → Create API token**, permiso **Object Read & Write** sobre
   el bucket `cosknot`.
4. Anota los cuatro valores y súbelos:

```bash
heroku config:set -a cosknot \
  IMAGE_STORAGE=r2 \
  R2_ENDPOINT_URL="https://<ACCOUNT_ID>.r2.cloudflarestorage.com" \
  R2_BUCKET=cosknot \
  R2_ACCESS_KEY_ID="<access key>" \
  R2_SECRET_ACCESS_KEY="<secret key>" \
  R2_PUBLIC_BASE_URL="https://img.cosknot.es"
```

Sin estas cinco, la app arranca igual y las subidas quedan desactivadas con un aviso en
el formulario. `R2_PUBLIC_BASE_URL` se abre en el `img-src` de la CSP, así que tiene que
ser el origen exacto, sin comodines ni barra final.

Las copias de seguridad usan un token distinto, con permiso de borrado, y su bucket
aparte (`docs/backups.md`).

## 7. correo con Resend

1. Crea la cuenta en https://resend.com y añade el dominio `cosknot.es` en **Domains**.
2. Resend da tres registros DNS. En Cloudflare, **en gris también** (los registros de
   correo no se proxian):

   | tipo | nombre | para qué |
   |---|---|---|
   | TXT | `resend._domainkey` | firma DKIM |
   | TXT | `send` (o el que indique Resend) | SPF del subdominio de envío |
   | MX | `send` | rebotes del subdominio de envío |

   El valor exacto lo da el panel: no se copia de aquí.
3. Espera a que el panel marque el dominio como **Verified** (de minutos a unas horas).
4. Crea una API key y configura:

```bash
heroku config:set -a cosknot \
  RESEND_API_KEY="re_..." \
  EMAIL_FROM="cosknot <hola@cosknot.es>" \
  EMAIL_REPLY_TO="hola@cosknot.es"
```

Sin clave, en producción el correo queda desactivado y la web lo dice. Con clave, el
aviso se intenta dentro de la petición (timeout 5 s); si falla, se guarda en
`email_outbox` y el hilo del proceso lo reintenta cada minuto, hasta 5 intentos.

## 8. pagos con Stripe en modo test

1. En https://dashboard.stripe.com/test/apikeys copia `sk_test_...` y `pk_test_...`.
2. Webhook: **Developers → Webhooks → Add endpoint**, URL
   `https://cosknot.es/stripe/webhook`, eventos `checkout.session.completed` y
   `payment_intent.payment_failed`. Copia el `whsec_...`.
3. Comisión de la plataforma, en porcentaje entero:

```bash
heroku config:set -a cosknot \
  STRIPE_SECRET_KEY="sk_test_..." \
  STRIPE_PUBLISHABLE_KEY="pk_test_..." \
  STRIPE_WEBHOOK_SECRET="whsec_..." \
  COMMISSION_PERCENT=10
```

Una clave `sk_live_` se rechaza a propósito: el cobro queda desactivado y la web lo
dice. Sin `COMMISSION_PERCENT` tampoco se cobra, porque no hay porcentaje por defecto.

Probar el webhook sin sacar la tarjeta:

```bash
stripe listen --forward-to https://cosknot.es/stripe/webhook
stripe trigger checkout.session.completed
```

## 9. secretos del repositorio

Para que funcionen las copias y el sondeo de salud (`docs/backups.md`):

```bash
gh secret set HEROKU_API_KEY
gh secret set HEROKU_APP_NAME      # cosknot
gh secret set BACKUP_PASSPHRASE
gh secret set R2_ENDPOINT_URL
gh secret set R2_BUCKET
gh secret set R2_ACCESS_KEY_ID
gh secret set R2_SECRET_ACCESS_KEY
gh variable set SITIO_URL --body https://cosknot.es
```

`HEROKU_API_KEY` está en **Account settings → API Key** y solo se muestra una vez. La
copia diaria pide `DATABASE_URL` a Heroku en tiempo de ejecución: la cadena de la base
no se guarda en GitHub.

## 10. desplegar cambios y volver atrás

```bash
git push origin main     # CI: pruebas
git push heroku main     # despliegue: build, release, dyno nuevo
```

Si el release falla, el dyno viejo sigue vivo: Heroku no cambia el tráfico hasta que el
release termina bien.

Volver a una versión anterior:

```bash
heroku releases -a cosknot
heroku rollback v42 -a cosknot
```

`heroku rollback` revierte el **código**, no la base de datos. Essential-0 no tiene
rollback de datos: si una migración rompió algo, se arregla con otra migración o se
restaura la copia del día (`docs/backups.md`).

## 11. comprobaciones después de cada despliegue

```bash
curl -s  https://cosknot.es/healthz
curl -s -o /dev/null -w "%{http_code} /\n"         https://cosknot.es/
curl -s -o /dev/null -w "%{http_code} creadores\n" https://cosknot.es/creadores
curl -s -o /dev/null -w "%{http_code} obra\n"      https://cosknot.es/obras/abrigo-de-invierno-fantasia
curl -s -o /dev/null -w "%{http_code} 404\n"       https://cosknot.es/obras/no-existe
heroku logs --tail -a cosknot
```

Esperado: `{"status":"ok"}`, `200`, `200`, `200`, `404` y ningún `500` en el log.

## 12. riesgos aceptados

Van escritos porque condicionan lo que se puede pedir a este despliegue. Ninguno es
una sorpresa: son el precio de 12 $/mes.

1. **Un solo dyno es un punto único.** Cada despliegue y cada reinicio diario de
   Heroku son unos segundos de 503. No hay balanceo ni segundo dyno: el plan no cabe
   en el crédito.
2. **512 MB de RAM y un worker.** Cuatro hilos cubren la espera de Postgres, R2,
   Resend y Stripe, pero una subida de imágenes grande o una consulta pesada compiten
   con el resto. Si el proceso pasa de memoria, Heroku lo reinicia (R14) y se pierde lo
   que hubiera en memoria.
3. **El contador de intentos vive en memoria.** `RATELIMIT_STORAGE_URI=memory://` es
   exacto con un worker, pero se pone a cero en cada reinicio del dyno. Un atacante
   paciente puede esperar al reinicio diario; no puede multiplicar los intentos mientras
   el proceso está vivo.
4. **El hilo de reintentos de correo muere con el dyno.** Los avisos pendientes no se
   pierden (están en `email_outbox`), pero no se reintentan hasta que el dyno vuelve y
   arranca el hilo. Si Heroku está caído más de lo normal, los correos salen tarde.
5. **Essential-0 no tiene rollback ni alta disponibilidad.** Un `DELETE` mal hecho o
   una migración destructiva solo se arreglan con la copia del día. La copia gestionada
   y el volcado a R2 existen por esto; una copia que nunca se ha restaurado no cuenta
   (`docs/backups.md`).
6. **El crédito de estudiante caduca.** Son 12 meses y 13 $/mes. El día que expire, el
   coste pasa a la tarjeta o hay que bajar a otro hosting. La fecha está en la cuenta de
   Heroku y conviene apuntarla antes de que llegue.

## 13. si algo se rompe

| síntoma | causa probable | dónde mirar |
|---|---|---|
| `release` falla con `relation ... does not exist` | migración que asume datos que no están | `heroku releases:info vNN --status` y `heroku logs` |
| el dyno arranca y muere en bucle | falta `SECRET_KEY` o `DATABASE_URL` | `heroku logs --tail`, la app exige las dos en producción |
| `/healthz` da 503 | base caída, conexiones agotadas o credenciales rotas | `heroku pg:info`, `heroku pg:diagnose` |
| `too many connections` | pool subido a mano o procesos sueltos | `heroku pg:info`, revisar `DB_POOL_SIZE` y `DB_MAX_OVERFLOW` |
| el certificado no se emite | Cloudflare en naranja o DNS sin propagar | `heroku certs:auto`, `nslookup` |
| las subidas están desactivadas | falta `IMAGE_STORAGE=r2` o alguna `R2_*` | `heroku config`, aviso del formulario |
| los correos no salen | Resend sin verificar o `EMAIL_FROM` distinto del dominio | logs de Heroku y panel de Resend |

Los fallos de la etapa Render + Neon quedan en `docs/troubleshooting/render-neon.md`,
marcados como históricos.
