# despliegue de cosknot en render + neon

orden de ejecución: de arriba abajo, sin saltos. el paso 6 se puede dejar para después del primer deploy.

## 0. requisitos

- cuenta de github con el repo subido y rama `main`.
- python 3.13.17 en local si vas a probar antes de desplegar (no es obligatorio para render).
- cuenta de render (registro con github, sin tarjeta).
- cuenta de neon (registro con github, sin tarjeta).

## 1. crear el proyecto en neon

1. entra en https://console.neon.tech y crea un proyecto.
2. región: la más cercana a frankfurt (render `frankfurt` y neon `aws-eu-central-1` quedan en el mismo continente; evita `us-east`).
3. base de datos y usuario: deja los valores por defecto (`neondb`, rol `neondb_owner`) o define uno propio.
4. abre el panel **Connect** y copia la cadena **pooled**. es la que lleva `-pooler` en el host:

```
postgresql://USUARIO:PASSWORD@ep-xxxx-pooler.eu-central-1.aws.neon.tech/neondb?sslmode=require
```

5. guarda esa cadena. no la pegues en el repo, ni en un `.md`, ni en un issue: va directa al panel de render.

si copias la cadena con `-pooler` mal, la app arranca pero cada request abre una conexión directa y neon empieza a rechazar conexiones al llegar al límite del plan free.

## 2. crear el web service en render

1. https://dashboard.render.com → **New** → **Blueprint** si vas a usar `render.yaml`, o **New** → **Web Service** si lo configuras a mano.
2. conecta github y elige el repo de cosknot.
3. si eliges Blueprint, render lee `render.yaml` del repo y crea el servicio con build, start, health check y plan ya puestos. si lo haces a mano, rellena:
   - runtime: **Python 3**
   - build command: `pip install -r requirements.txt`
   - start command: `gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 60`
   - health check path: `/healthz`
   - plan: **Free**
   - región: **Frankfurt** (EU Central)
4. rama: `main`. auto deploy: activado.

## 3. variables de entorno en render

en **Environment** del servicio:

| variable | valor |
|---|---|
| `DATABASE_URL` | la cadena de neon del paso 1, con `-pooler` |
| `SECRET_KEY` | generada por render o `python -c "import secrets;print(secrets.token_hex(32))"` |
| `PYTHON_VERSION` | `3.13.17` |
| `FLASK_ENV` | `production` |

`DATABASE_URL` va con `sync: false` en `render.yaml`: render no la versiona y la pide al crear el servicio. si el servicio ya existe, se pega a mano en el panel.

## 4. primer deploy

1. pulsa **Create Web Service** / **Deploy**. el primer build tarda 2-5 min (instala `psycopg` y compila lo que falte).
2. mira los logs hasta que aparezca `Listening at: http://0.0.0.0:10000` y las migraciones/creación de tablas hayan corrido.
3. si el deploy falla en build, el log dice el paquete exacto. si falla en runtime, casi siempre es `DATABASE_URL` ausente o sin `sslmode=require`.

## 5. verificar

1. `https://cosknot.onrender.com/healthz` debe devolver `200` con un cuerpo corto (`ok` o similar). si devuelve 502/503 el proceso no arrancó.
2. `https://cosknot.onrender.com/` debe renderizar la home con datos reales de la db (no una lista vacía por error silencioso).
3. en neon, panel **Monitoring**, debe verse la conexión entrando en el momento del request.
4. primera petición tras 15 min de inactividad tarda ~1 min: es el cold start, no una caída.

la ruta `/healthz` la implementa `app.py` y devuelve 200 sin tocar la base de datos. si no existe, render marca el health check como fallido y no promociona el deploy.

## 6. dominio `cosknot.is-a.dev` (is-a.dev)

1. haz fork de https://github.com/is-a-dev/register → botón **Fork**. el fork queda en `https://github.com/TU_USUARIO/register`.
2. en tu fork, crea el fichero `domains/cosknot.json` con el contenido de `domains/cosknot.json` de este repo:
   ```json
   {
     "owner": { "username": "Barbarno", "email": "RELLENA_TU_EMAIL" },
     "records": { "CNAME": "cosknot.onrender.com" }
   }
   ```
   el `email` lo pone el dueño de la cuenta (el mismo con el que se firmó el fork en is-a.dev); `username` es el usuario de github, no el nombre del proyecto.
3. abre el PR contra `is-a.dev/register`, rama `main`, título `feat: add cosknot`. el PR lo revisa un humano; mediana de merge ~1 día, casos de hasta una semana.
4. si el bot de validación se queja, revisa que el json esté en `domains/` y que el `CNAME` no lleve `https://` ni barra final.

## 7. tras el merge: custom domain en render

1. comprueba que el DNS ya resuelve: `nslookup cosknot.is-a.dev` debe devolver el CNAME hacia `cosknot.onrender.com`.
2. en render, servicio → **Settings** → **Custom Domains** → **Add Custom Domain** → `cosknot.is-a.dev`.
3. render verifica el registro y emite el certificado let's encrypt. puede tardar de minutos a unas horas; hasta que el DNS propague no hay HTTPS y el navegador da error de certificado.
4. si usas el blueprint, descomenta el bloque `domains:` de `render.yaml` y redespliega en vez de hacerlo a mano.
5. verifica: `https://cosknot.is-a.dev/healthz` → 200 y candado válido.

## 8. fallos típicos

| síntoma | causa | arreglo |
|---|---|---|
| los datos desaparecen en cada deploy | sqlite en el filesystem efímero de render | `DATABASE_URL` a neon; nunca sqlite en producción |
| el primer acceso tras un rato tarda ~1 min | render duerme a los 15 min de inactividad en free | aceptarlo, o pasar a plan de pago / cloud run |
| neon suspende el compute a mitad de mes | keep-alive o ping periódico gastando las 100 cu-horas | quitar cualquier cron/ping contra la db; dejar scale-to-zero |
| `too many connections` en los logs | cadena sin `-pooler` | copiar la cadena pooled de neon |
| cambios en el repo no aparecen | auto deploy desactivado o rama distinta | revisar rama y **Auto-Deploy** en settings |
| el dominio nuevo da error de certificado | DNS aún sin propagar | esperar; render no emite TLS contra un CNAME inexistente |
| 502 tras el deploy | el proceso no arranca (import error, variable ausente) | leer los logs del deploy, no el health check |

## 9. copia de seguridad semanal

neon free da 6 h de historial, no un backup eterno. una vez por semana, desde tu máquina:

```bash
pg_dump "postgresql://USUARIO:PASSWORD@ep-xxxx-pooler.eu-central-1.aws.neon.tech/neondb?sslmode=require" \
  -Fc -f cosknot-$(date +%Y%m%d).dump
```

el `.dump` va fuera del repo (el `.gitignore` ya excluye `*.dump`). restaurar:

```bash
pg_restore -d "CADENA_DE_DESTINO" --clean --if-exists cosknot-20260101.dump
```

`pg_dump` va contra la cadena pooled sin problema; usa `--no-sync` solo si sabes lo que haces.

## 10. reglas que no se rompen

- `.env` nunca en el repo. el `.gitignore` lo excluye y `render.yaml` no lo versiona.
- la `DATABASE_URL` solo existe en el panel de render y en tu `.env` local.
- nada de sqlite en render.
- nada de keep-alive contra neon.
