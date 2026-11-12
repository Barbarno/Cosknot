# despliegue

Aquí apunto cómo está desplegado cosknot hoy y cómo se repite, con los pasos que usé
de verdad y no con el plan inicial.

## cómo está ahora

| qué | valor |
|---|---|
| URL de producción | `https://cosknot.duckdns.org` |
| plataforma | Render, servicio web `cosknot` (`srv-dbqte8bl550s73er4bcg`), plan free, Frankfurt |
| Python | 3.13.17 |
| base de datos | Neon, PostgreSQL 18, Frankfurt, base `cosknot`, usuario `cosknot_owner` |
| datos | 10 creadores y 24 obras; la app siembra sola si `creators` está vacía |
| dominio | `cosknot.duckdns.org`, con un registro **A** a `216.24.57.1` |
| HTTPS | lo emite y renueva Render con Let's Encrypt |
| coste | 0 € al mes, sin tarjeta |
| arranque en frío | Render duerme a los 15 min sin tráfico; la primera visita tarda unos 50 s |
| health check | `/healthz` |

El servicio se creó desde **Public Git Repository** apuntando a
`https://github.com/Barbarno/Cosknot`, rama `main`, con el autodespliegue activado.

Por eso `render.yaml` no manda: existe como referencia, pero el servicio no se creó
desde un blueprint y editarlo no cambia nada en Render.

## montarlo desde cero

### 1. base de datos en Neon

1. Entra en https://console.neon.tech y crea un proyecto.
2. Nombre `cosknot`, región **AWS eu-central-1 (Frankfurt)**, PostgreSQL 18.
3. Base de datos `cosknot`, usuario `cosknot_owner`.
4. En **Connect**, copia la cadena **pooled** (la que lleva `-pooler` en el host). Sin
   parámetros al final:

   ```
   postgresql://cosknot_owner:PASSWORD@ep-xxxx-pooler.eu-central-1.aws.neon.tech/cosknot
   ```

   No hace falta añadir `?sslmode=require`: la app ya lo pone en `build_engine()`,
   junto con `pool_pre_ping=True`.

5. La cadena no se pega en el repositorio ni en un issue. Va directa al panel de Render.

### 2. servicio en Render

1. En https://dashboard.render.com, **New** → **Web Service**.
2. Pestaña **Public Git Repository**, URL del repositorio.
3. Rellena:
   - **Name**: `cosknot`
   - **Region**: Frankfurt (EU Central)
   - **Branch**: `main`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 60`
   - **Health Check Path**: `/healthz`
   - **Instance Type**: Free
   - **Auto-Deploy**: Yes, trigger `commit`
4. Crea el servicio.

### 3. variables de entorno

En **Environment**:

| variable | valor |
|---|---|
| `DATABASE_URL` | la cadena pooled de Neon, sin parámetros |
| `SECRET_KEY` | una generada con `python -c "import secrets;print(secrets.token_hex(32))"` |
| `PYTHON_VERSION` | `3.13.17` |

`FLASK_ENV` no hace falta: la app usa `production` por defecto.

### 4. primer arranque

Render instala las dependencias y arranca gunicorn. Al arrancar, `create_app()` ejecuta
`Base.metadata.create_all(engine)` y después `seed_database()`, que mete el catálogo de
`seed.py` solo si `creators` está vacía. No hay paso de migraciones: la primera vez
contra una base vacía la deja con 10 creadores y 24 obras.

### 5. secretos del repositorio

Los tres (`RENDER_API_KEY`, `RENDER_SERVICE_ID`, `NEON_DATABASE_URL`) están explicados
en `docs/backups.md`.

### 6. dominio

El dominio está añadido y verificado desde el panel de Render. En `render.yaml` el
bloque `domains:` está comentado a propósito: el blueprint no es la fuente de verdad y,
si se aplicara con el registro sin resolver, el despliegue fallaría.

## desplegar cambios

Lo normal es hacer push a `main`:

```bash
git push origin main
```

Pasan dos cosas a la vez:

1. Render ve el commit y despliega por su cuenta.
2. `deploy.yml` se dispara con el push, busca el despliegue de ese commit en la API de
   Render y espera a que quede en `live`. Después comprueba `/healthz` para confirmar
   que la web responde.

Si algo falla, el flujo sale en rojo.

También se puede lanzar a mano desde **Actions → despliegue → Run workflow**.

Si quieres forzarlo solo con `curl`:

```bash
curl --fail --silent --show-error \
  -X POST \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}' \
  https://api.render.com/v1/services/srv-dbqte8bl550s73er4bcg/deploys
```

El build es corto. El progreso se sigue en **Render → Logs** o en la pestaña
**Deploys**.

## comprobar que ha ido bien

1. Health check:

   ```bash
   curl -s https://cosknot.onrender.com/healthz
   ```

   Tiene que devolver `{"status":"ok"}`. Ojo, `/healthz` sí toca la base de datos con
   un `SELECT 1`; si falla devuelve `{"status":"error"}` y 503. Un 503 aquí es problema
   de `DATABASE_URL`, no del proceso.

2. Rutas públicas:

   ```bash
   curl -s -o /dev/null -w "%{http_code} /\n"        https://cosknot.onrender.com/
   curl -s -o /dev/null -w "%{http_code} /creadores\n" https://cosknot.onrender.com/creadores
   curl -s -o /dev/null -w "%{http_code} detalle\n"  https://cosknot.onrender.com/creadores/marisol-vega
   curl -s -o /dev/null -w "%{http_code} obra\n"     https://cosknot.onrender.com/obras/abrigo-de-invierno-fantasia
   ```

   La portada tiene que mostrar 3 creadores, 3 obras y el contador. Un slug que no
   existe tiene que dar 404 con la plantilla propia, no un 500.

3. Base de datos desde local:

   ```bash
   DATABASE_URL="postgresql://cosknot_owner:PASSWORD@ep-xxxx-pooler.eu-central-1.aws.neon.tech/cosknot" \
     python scripts/check_db.py
   ```

   Tiene que imprimir las tablas y los conteos: `creators 10`, `works 24`.

4. Si Render marca el despliegue como fallido por el health check pero en el log pone
   `Listening at: http://0.0.0.0:10000`, el problema es el `SELECT 1` contra Neon, no
   gunicorn.

## el dominio `cosknot.duckdns.org`

Es un subdominio gratuito de DuckDNS. En Render figura como dominio verificado y el
certificado lo emite Render solo. `https://cosknot.onrender.com` sigue funcionando y es
la URL que usan los workflows.

No hay CNAME: DuckDNS solo deja un registro **A**, y Render clasifica
`cosknot.duckdns.org` como apex porque `duckdns.org` está en la Public Suffix List. Un
apex se resuelve con un A a `216.24.57.1`, que es la entrada de Render.

Para mantenerlo:

1. Si cambia la IP de Render, se actualiza en https://www.duckdns.org → dominio
   `cosknot` → campo `current ip` → `216.24.57.1`. También por API:

   ```bash
   curl "https://www.duckdns.org/update?domains=cosknot&token=$DUCKDNS_TOKEN&ip=216.24.57.1"
   ```

   Responde `OK`. El token no va en el repositorio.

2. Comprobar el registro A:

   ```bash
   nslookup cosknot.duckdns.org 1.1.1.1
   ```

   Tiene que salir `216.24.57.1`. Pregunto a Cloudflare porque el resolver local puede
   tener el valor viejo en caché.

3. Si el dominio sale `unverified`, se le da a **Verify** en **Settings → Custom
   Domains**, o por API:

   ```bash
   curl --fail --silent --show-error \
     -X POST \
     -H "Authorization: Bearer $RENDER_API_KEY" \
     https://api.render.com/v1/services/srv-dbqte8bl550s73er4bcg/custom-domains/cdm-dbqtuo6tlv9c739hqo4g/verify
   ```

4. El HTTPS se emite solo cuando la verificación pasa. Hasta entonces el navegador da
   error de certificado aunque el DNS esté bien. Se comprueba con:

   ```bash
   curl -sI https://cosknot.duckdns.org/healthz
   ```

5. `sitemap.xml` y `robots.txt` no hay que tocarlos: se generan con
   `request.url_root`, así que usan el dominio por el que entra la visita.

`cosknot.is-a.dev` queda como reserva. Su PR sigue abierto, pero is-a.dev es solo para
proyectos de software y prohíbe el uso comercial, así que lo normal es que lo rechacen.
El fichero está en `domains/cosknot.json`.

## si algo se rompe

- Los fallos típicos de Render con Neon están en
  `docs/troubleshooting/render-neon.md`.
- Las copias de seguridad y los secretos, en `docs/backups.md`.

### volver atrás un despliegue

Si un despliegue deja la web rota:

1. Render → servicio `cosknot` → **Deploys**.
2. Busca el último despliegue que funcionaba.
3. Menú **⋯** de esa fila → **Rollback to this deploy**.

Render vuelve a desplegar ese commit. Los dos últimos siempre están ahí. Después del
rollback conviene arreglar el commit en `main` con un revert, porque el siguiente push
volvería a desplegar la cabeza de rama.

Si el problema es de datos y no de código, el rollback no sirve: hay que restaurar el
dump como explico en `docs/backups.md`.
