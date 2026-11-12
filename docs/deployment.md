# despliegue de cosknot: estado real

lo que hay desplegado hoy, cómo se llegó ahí y cómo se repite. los pasos son los que se ejecutaron de verdad, no el plan inicial.

## 1. estado actual

| qué | valor |
|---|---|
| URL de producción | `https://cosknot.onrender.com` |
| plataforma | Render, web service `cosknot`, id `srv-dbqte8bl550s73er4bcg`, plan free, región Frankfurt |
| runtime | Python 3.13.17 |
| base de datos | Neon, proyecto `cosknot`, Postgres 18, AWS `eu-central-1` (Frankfurt), base `cosknot`, usuario `cosknot_owner` |
| datos | `creators` 10 filas, `works` 24; la app siembra sola al arrancar si `creators` está vacía |
| dominio | `cosknot.onrender.com` activo; `cosknot.is-a.dev` añadido como custom domain (id `cdm-dbqtj9mi0phs738hnum0`) en estado `unverified` |
| TLS | Render emite y renueva el certificado Let's Encrypt del subdominio. `cosknot.is-a.dev` no tiene TLS hasta que el CNAME resuelva |
| coste | 0 €/mes (Render free + Neon free, sin tarjeta) |
| cold start | Render duerme el servicio a los 15 min sin tráfico; la primera petición después tarda ~50 s |
| health check | `/healthz` (configurado en Render como health check path) |

el servicio se creó desde **Public Git Repository** apuntando a `https://github.com/Barbarno/Cosknot`, rama `main`. Render tiene `autoDeploy: yes` con `autoDeployTrigger: commit`: redespliega al detectar el commit nuevo en `main`.

consecuencia: `render.yaml` **no** es la fuente de verdad del servicio. Existe en el repo como referencia, pero el servicio no se creó desde un Blueprint, así que editarlo no cambia nada en Render.

## 2. reproducir el despliegue desde cero

### 2.1 base de datos en Neon

1. https://console.neon.tech → crear proyecto.
2. nombre `cosknot`, región **AWS eu-central-1 (Frankfurt)**, Postgres 18.
3. base de datos `cosknot`, usuario/rol `cosknot_owner`.
4. panel **Connect** → copiar la cadena **pooled** (la que lleva `-pooler` en el host). Debe quedar **sin query params**:

   ```
   postgresql://cosknot_owner:PASSWORD@ep-xxxx-pooler.eu-central-1.aws.neon.tech/cosknot
   ```

   no añadas `?sslmode=require`: la app mete `sslmode=require` ella misma en `build_engine()` (`app.py`), junto con `pool_pre_ping=True`.

5. no pegues la cadena en el repo, en un `.md` ni en un issue. Va directa al panel de Render.

### 2.2 servicio en Render

1. https://dashboard.render.com → **New** → **Web Service**.
2. pestaña **Public Git Repository** → `https://github.com/Barbarno/Cosknot`.
3. rellenar:
   - **Name**: `cosknot`
   - **Region**: Frankfurt (EU Central)
   - **Branch**: `main`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 60`
   - **Health Check Path**: `/healthz`
   - **Instance Type**: Free
   - **Auto-Deploy**: Yes, trigger `commit`
4. crear el servicio.

### 2.3 variables de entorno

en **Environment** del servicio:

| variable | valor |
|---|---|
| `DATABASE_URL` | cadena pooled de Neon del paso 2.1, sin query params |
| `SECRET_KEY` | generada, 64 caracteres (`python -c "import secrets;print(secrets.token_hex(32))"`) |
| `PYTHON_VERSION` | `3.13.17` |

`FLASK_ENV` no hace falta: `app.py` usa `production` por defecto. `PYTHONUNBUFFERED` tampoco es necesario para el deploy.

### 2.4 primer arranque

al crear el servicio, Render hace el build (`pip install -r requirements.txt`: flask, gunicorn, sqlalchemy, psycopg[binary], python-dotenv, pytest) y arranca gunicorn. En el arranque, `create_app()` ejecuta `Base.metadata.create_all(engine)` y luego `seed_database()`, que inserta el catálogo de `seed.py` solo si `creators` está vacía. No hay paso de migraciones ni script manual: la primera vez que arranca contra una base vacía, la deja con 10 creadores y 24 obras.

### 2.5 secretos del repositorio

los tres secretos (`RENDER_API_KEY`, `RENDER_SERVICE_ID`, `NEON_DATABASE_URL`) y cómo se generan están en `docs/backups.md`. `RENDER_SERVICE_ID` es `srv-dbqte8bl550s73er4bcg`.

### 2.6 dominio (después del merge)

ver sección 5. El bloque `domains:` de `render.yaml` sigue comentado a propósito: si el blueprint se aplicara con el CNAME sin resolver, la verificación del dominio falla el deploy.

## 3. desplegar cambios

### 3.1 por push a `main`

```bash
git push origin main
```

pasan dos cosas en paralelo:

1. **Render** detecta el commit nuevo (`autoDeploy: yes`, trigger `commit`) y arranca build + deploy por su cuenta.
2. **`.github/workflows/deploy.yml`** se dispara con el push: hace `POST /v1/services/<id>/deploys` contra la API de Render para forzar el deploy si el polling no lo pilla, y después sondea `https://cosknot.onrender.com/healthz` hasta 20 veces cada 15 s. Si no responde 200 en 5 min, el workflow se marca en rojo. Si faltan `RENDER_API_KEY` o `RENDER_SERVICE_ID`, el paso del trigger se salta con `exit 0` y solo queda la comprobación de salud.

el workflow también se puede lanzar a mano desde **Actions → deploy → Run workflow**.

### 3.2 forzar un deploy a mano por API

```bash
curl --fail --silent --show-error \
  -X POST \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}' \
  https://api.render.com/v1/services/srv-dbqte8bl550s73er4bcg/deploys
```

responde con el objeto del deploy (`id`, `status`, `commit`). el mismo endpoint es el que usa el workflow.

### 3.3 cuánto tarda

el build es corto (seis paquetes, `psycopg[binary]` viene en wheel), pero no hay duración medida en el repo: el margen que da el workflow es de **5 minutos** (20 intentos × 15 s), y con eso sobra. Si el servicio estaba dormido, el primer `/healthz` suma el cold start de ~50 s. El progreso se sigue en **Render → Logs** del deploy, o en la pestaña **Deploys** del servicio.

## 4. verificar

1. health check:

   ```bash
   curl -s https://cosknot.onrender.com/healthz
   ```

   debe devolver exactamente `{"status":"ok"}`. Ojo: `/healthz` **sí** toca la base de datos, ejecuta `SELECT 1`; si la conexión falla devuelve `{"status":"error"}` con 503. Un 503 aquí es problema de `DATABASE_URL`, no del proceso.

2. rutas públicas, todas deben dar 200 con contenido real:

   ```bash
   curl -s -o /dev/null -w "%{http_code} /\n"        https://cosknot.onrender.com/
   curl -s -o /dev/null -w "%{http_code} /creadores\n" https://cosknot.onrender.com/creadores
   curl -s -o /dev/null -w "%{http_code} detalle\n"  https://cosknot.onrender.com/creadores/marisol-vega
   curl -s -o /dev/null -w "%{http_code} obra\n"     https://cosknot.onrender.com/obras/abrigo-de-invierno-fantasia
   ```

   la home muestra 3 creadores destacados, 3 obras y el contador de creadores. Si sale vacía con 200, la base está vacía o el seed no corrió. Un slug inexistente debe dar 404 con la plantilla `404.html`, no un error 500.

3. base de datos desde local, con la cadena pooled en el entorno:

   ```bash
   DATABASE_URL="postgresql://cosknot_owner:PASSWORD@ep-xxxx-pooler.eu-central-1.aws.neon.tech/cosknot" \
     python scripts/check_db.py
   ```

   imprime la lista de tablas y el conteo de `creators` y `works`. Esperado: `['creators', 'works']`, `creators 10`, `works 24`. El script exige `DATABASE_URL` (si falta, `KeyError`), convierte el esquema a `postgresql+psycopg://` y conecta con `sslmode=require`.

4. si Render marca el deploy como fallido en el health check pero el log dice `Listening at: http://0.0.0.0:10000`, el problema es el `SELECT 1` contra Neon, no gunicorn.

## 5. cerrar el dominio cuando mergeen el PR

estado: el custom domain `cosknot.is-a.dev` ya está añadido en Render (id `cdm-dbqtj9mi0phs738hnum0`) y figura como `unverified`. El PR `is-a.dev/register#61033` está abierto. Mientras no se mergee, no hay registro DNS que resolver y la verificación no puede pasar.

1. **fork del registro**: fork de `https://github.com/is-a-dev/register` en la cuenta `Barbarno`. El fichero va en `domains/cosknot.json` del fork, y su contenido es el de `domains/cosknot.json` de este repo:

   ```json
   {
     "owner": { "username": "Barbarno", "email": "EMAIL_DEL_OWNER" },
     "records": { "CNAME": "cosknot.onrender.com" }
   }
   ```

   el `username` es el de GitHub, no el nombre del proyecto. El `CNAME` va sin `https://` y sin barra final. El email es el de la cuenta con la que se firmó en is-a.dev.

2. **esperar el merge** del PR `#61033`. Lo revisa una persona; hasta que entra en `main` del registro, el DNS no existe.

3. **confirmar el DNS**:

   ```bash
   nslookup cosknot.is-a.dev
   ```

   debe devolver un CNAME hacia `cosknot.onrender.com`. Si el resolver local cachea el fallo anterior, probar con `nslookup cosknot.is-a.dev 1.1.1.1`.

4. **verificar el dominio en Render**, cuando el DNS ya resuelve. Por panel: servicio → **Settings** → **Custom Domains** → `cosknot.is-a.dev` → **Verify**. Por API:

   ```bash
   curl --fail --silent --show-error \
     -X POST \
     -H "Authorization: Bearer $RENDER_API_KEY" \
     https://api.render.com/v1/services/srv-dbqte8bl550s73er4bcg/custom-domains/cdm-dbqtj9mi0phs738hnum0/verify
   ```

   el estado pasa de `unverified` a verificado cuando Render ve el CNAME.

5. **TLS**: lo emite Render solo, con Let's Encrypt, en cuanto la verificación pasa. No hay certificado que subir ni renovar a mano. Puede tardar de minutos a unas horas; hasta entonces el navegador da error de certificado aunque el DNS ya esté bien. Se comprueba con:

   ```bash
   curl -sI https://cosknot.is-a.dev/healthz
   ```

   `200` y certificado válido. Mientras el dominio no esté cerrado, `https://cosknot.onrender.com` sigue siendo la URL de producción y la que usan el workflow y los chequeos.

6. opcional: cuando el dominio verifique, descomentar el bloque `domains:` de `render.yaml` para que el repo lo refleje. No es necesario para que funcione; el dominio ya está añadido en el panel.

## 6. si algo se rompe

- **síntoma → causa → arreglo** de los fallos de esta combinación: `docs/troubleshooting/render-neon.md`. Cubre base vacía tras deploy, `could not connect to server`, prepared statements con el pooler, cold start, cuota de Neon, banda de Render, TLS del dominio y 502 tras el deploy.
- **backups, restauración y secretos**: `docs/backups.md`. Los dumps los genera `.github/workflows/backup.yml` los domingos a las 03:00 UTC (formato custom, artefacto `cosknot-db-<run_number>`, 30 días de retención).

### rollback

si un deploy deja el servicio roto:

1. Render → servicio `cosknot` → **Deploys**.
2. localizar el último deploy sano (el anterior al que rompió).
3. menú **⋯** de esa fila → **Rollback to this deploy**.

Render redespliega ese commit. Los dos últimos deploys siempre están ahí, así que el rollback no depende de nada local. Después del rollback, comprobar `/healthz` y la home, y arreglar el commit en `main` con un revert en vez de dejar el servicio apuntando a un commit viejo: el siguiente push a `main` (o el autoDeploy de Render) vuelve a desplegar la cabeza de rama y deshace el rollback.

si el problema es de datos y no de código, el rollback no sirve: restaurar el dump desde `docs/backups.md`.
