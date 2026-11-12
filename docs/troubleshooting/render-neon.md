# troubleshooting: render + neon

formato: síntoma → causa → arreglo.

combinación real: render web service `cosknot` (`srv-dbqte8bl550s73er4bcg`, free, Frankfurt, Python 3.13.17) + neon free en Frankfurt. los pasos de despliegue están en `docs/deployment.md`; backups, restauración y secretos, en `docs/backups.md`.

## 1. cold start: la primera petición tarda ~50 s

**síntoma**: el primer acceso tras un rato sin tráfico tarda decenas de segundos y luego carga; el run de `deploy` en github puede marcar rojo en el paso que sondea `/healthz`. no hay error en los logs, solo el arranque.
**causa**: render free duerme el servicio a los 15 min sin tráfico. la primera petición paga el arranque de gunicorn, el import de flask y sqlalchemy, `create_all()` + seed contra la base, y la reconexión a neon (el compute de neon también despierta en el primer `SELECT 1`). en este proyecto está medido en ~50 s.
**arreglo**: no es una caída. `.github/workflows/deploy.yml` sondea `/healthz` 20 veces cada 15 s, o sea 5 min de margen; si el servicio tarda más que eso, el problema no es el cold start: mirar **Logs** del deploy. si el cold start molesta a los usuarios, plan de pago o cloud run (`docs/decisions/0001-stack-despliegue-dominio.md`). no poner un keep-alive contra la base para evitarlo: la mantiene despierta y gasta la cuota de neon (entrada 8).

## 2. `/healthz` devuelve 503

**síntoma**: `curl -s -o /dev/null -w "%{http_code}" https://cosknot.onrender.com/healthz` da 503 y el cuerpo es `{"status":"error"}`; render puede marcar el deploy como fallido en el health check aunque gunicorn esté escuchando.
**causa**: `/healthz` no es un ping. abre sesión y ejecuta `SELECT 1`; el 503 sale del `except` de la ruta en `app.py`. el proceso está vivo; lo que falla es postgres. tres orígenes: neon caído o con el compute suspendido, `DATABASE_URL` mal (host, usuario, contraseña, nombre de base), o conexión que abre pero con el `SELECT` rechazado. si en lugar de 503 sale 502, el problema sí es el proceso (entrada 11).
**arreglo**: mirar el estado del proyecto en la consola de neon y, en paralelo, probar la misma cadena desde local:

```bash
DATABASE_URL="postgresql://cosknot_owner:PASSWORD@ep-xxxx-pooler.eu-central-1.aws.neon.tech/cosknot" \
  python scripts/check_db.py
```

si `check_db.py` conecta y render no, comparar la variable del panel carácter a carácter (espacio final, salto de línea, contraseña rotada). no añadir query params a la cadena: `build_engine()` ya pasa `sslmode=require` en `connect_args`, y la cadena de render va sin `?`. el deploy no se reintenta solo: hay que relanzarlo cuando la base responda (`docs/deployment.md` §3.2).

## 3. health check en verde pero la home responde 500

**síntoma**: `/healthz` da 200 `{"status":"ok"}` y `/` (o solo `/creadores`, o un detalle) devuelve 500.
**causa**: el health check solo prueba `SELECT 1`. la home hace tres consultas (`Creator`, `Work`, `count(*)`) y renderiza `index.html`. con la base viva, un 500 es plantilla o esquema: una variable o filtro que la plantilla espera y no llega, un `url_for` a un endpoint renombrado, o una columna nueva en `models.py` que no existe en la tabla. `Base.metadata.create_all()` crea tablas que faltan, **no** altera las que ya existen, así que un cambio de modelo no se aplica solo.
**arreglo**: **Logs** del servicio, la traza dice cuál de los dos es. si es plantilla, reproducir en local contra la misma base. si es esquema, añadir la columna a mano en neon (o recrear la tabla); el proyecto no tiene migraciones, todo el esquema lo pone `create_all()` al arrancar (`docs/deployment.md` §2.4).

## 4. `connection refused` o `too many connections` contra neon

**síntoma**: el deploy arranca, el primer request da 500 y el log muestra fallo de conexión a un host `ep-xxxx.<region>.aws.neon.tech` (sin `-pooler`), o el arranque falla con `too many connections` cuando gunicorn levanta los workers.
**causa**: la cadena directa abre conexiones que no pasan por el pooler, contra el límite de conexiones directas del plan free. el start command va con `--workers 2 --threads 4` y cada worker mantiene su propio pool, así que el número de conexiones se multiplica.
**arreglo**: usar la cadena **pooled**, la que lleva `-pooler` en el host; es la que está en `DATABASE_URL` en render y la que documenta `docs/deployment.md` §2.1. sin query params. si aun así se agota, bajar workers (`--workers 1 --threads 8`) antes que tocar el pool. `pool_pre_ping=True` ya está en `build_engine()` y evita revivir conexiones muertas tras el scale-to-zero.

## 5. errores intermitentes de prepared statements con la cadena pooled

**síntoma**: consultas que fallan y funcionan alternando, sobre todo en el primer request de cada worker o después de que neon despierte; la base responde y `/healthz` suele seguir en verde porque el `SELECT 1` cae en otra conexión del pool.
**causa**: el pooler de neon en transaction mode no mantiene estado de sesión. psycopg3 cachea prepared statements por conexión (`prepare_threshold`, por defecto a los 5 usos) y el servidor que atiende la transacción cambia, así que una sentencia preparada en una conexión no existe en la siguiente.
**arreglo**: desactivar la caché. ya está aplicado en `build_engine()`:

```python
options["connect_args"] = {"sslmode": "require", "prepare_threshold": None}
```

`None` desactiva los prepared statements del todo, que es lo que necesita el transaction mode. no cambia nada del resto del engine.

## 6. el push no dispara ningún deploy

**síntoma**: el commit está en `main` en github y render sigue sirviendo el anterior; o en **Actions** no aparece ningún run de `deploy`.
**causa**: el servicio no tiene auto-deploy activo, o mira otra rama, o el push no llegó a `main`. no hay deploy hook en este proyecto: el deploy normal lo dispara `autoDeploy: yes` con `autoDeployTrigger: commit` sobre el repositorio público (render consulta el repo y redespliega al ver el commit, sin github app), y `.github/workflows/deploy.yml` lo fuerza por API como red de seguridad.
**arreglo**: render → servicio `cosknot` → **Settings → Build & Deploy**: `Auto-Deploy` en yes, trigger `commit`, branch `main`. mirar **Events** y **Deploys** del servicio para ver si render vio el commit. en github, Actions → `deploy`: si no hay run, el push no entró en `main` o el workflow está desactivado; si hay run y falló el trigger, revisar `RENDER_API_KEY` y `RENDER_SERVICE_ID` (si faltan, el paso sale con `exit 0` y solo queda el sondeo de salud). forzar a mano, desde el panel o con el `curl` de `docs/deployment.md` §3.2, o con **Actions → deploy → Run workflow**.

## 7. los datos desaparecen tras un deploy

**síntoma**: después de un redeploy o un reinicio, la home vuelve al catálogo del seed y `creators`/`works` vuelven a 10/24; en los logs aparece que la app creó `cosknot.db`.
**causa**: el filesystem de render es efímero. cada deploy y cada reinicio monta un contenedor nuevo y el disco anterior se va con él, así que sqlite pierde todo. el detalle que lo hace silencioso: `normalize_database_url()` cae a `sqlite:///cosknot.db` cuando `DATABASE_URL` no está definida, de modo que un servicio sin la variable arranca en sqlite, responde `/healthz` 200 y borra los datos en el siguiente deploy, sin un solo error.
**arreglo**: `DATABASE_URL` definida siempre en render (`docs/deployment.md` §2.3); sqlite solo en local. si aparece el fallback, definir la variable, redesplegar y comprobar el conteo real con `python scripts/check_db.py`. el seed se repite solo cuando `creators` está vacía. nada de lo que suba un usuario se guarda en disco: en free no hay volumen persistente, así que ficheros e imágenes van a un bucket externo o no van.

## 8. la cuota de neon se agota y el compute queda suspendido

**síntoma**: a mitad de ciclo, todo request falla al conectar y el proyecto figura con el compute suspendido por cuota; el run del domingo de `.github/workflows/backup.yml` también falla, en el paso de `pg_dump`.
**causa**: el plan free son 100 cu-horas por proyecto y mes. con el mínimo de compute (0,25 cu) son ~400 h despiertas contra las ~730 h de un mes, así que cualquier cosa que toque la base con frecuencia mantiene el compute encendido y agota la cuota. aquí tocan la base: `/healthz` en cada sondeo del CI, el seed del arranque y el `pg_dump` semanal.
**arreglo**: quitar lo que despierte la base sin necesidad y dejar que el scale-to-zero de neon (5 min) haga su trabajo; no hay keep-alive ni uptime check contra la base. el compute se reactiva al empezar el ciclo siguiente. mientras dure la suspensión no hay backup posible: ese hueco del histórico se pierde y hay que anotarlo (`docs/backups.md`). si el uso es diario y real, toca plan de pago.

## 9. el dominio `cosknot.duckdns.org` sigue `unverified` en render

**síntoma**: el custom domain `cosknot.duckdns.org` (id `cdm-dbqtuo6tlv9c739hqo4g`) figura en `unverified`, pulsar **Verify** no cambia el estado y `https://cosknot.duckdns.org` no carga.
**causa**: el registro **A** de DuckDNS no apunta a `216.24.57.1`, o DuckDNS conserva una IP vieja de un `update ip` anterior. render clasifica `cosknot.duckdns.org` como `domainType: apex` porque `duckdns.org` está en la Public Suffix List, así que espera un A; un CNAME no es posible en DuckDNS y tampoco serviría para un apex. si el A es correcto y el estado no cambia, el resolver que usa render aún tiene el valor anterior en caché (TTL corto, 60 s).
**arreglo**: comprobar a quién apunta el nombre, saltándose la caché local:

```bash
nslookup cosknot.duckdns.org 1.1.1.1
```

si no devuelve `216.24.57.1`, corregirlo en https://www.duckdns.org → dominio `cosknot` → campo `current ip` → `216.24.57.1` → `update ip`, o por API:

```bash
curl "https://www.duckdns.org/update?domains=cosknot&token=$DUCKDNS_TOKEN&ip=216.24.57.1"
```

esperar un minuto y volver a verificar: **Settings → Custom Domains → Verify**, o el `POST .../custom-domains/cdm-dbqtuo6tlv9c739hqo4g/verify` de `docs/deployment.md` §5. el estado pasa a verificado cuando render ve el A correcto.

## 10. TLS no se emite en `cosknot.duckdns.org`

**síntoma**: el dominio ya figura `verified` y `https://cosknot.duckdns.org` da error de certificado (nombre que no coincide, o ninguno emitido); `curl -sI https://cosknot.duckdns.org/healthz` no completa.
**causa**: el certificado es el segundo paso y no empieza hasta que el primero termina. render pide el Let's Encrypt del dominio cuando la verificación pasa, y la emisión tarda unos minutos. si pasan horas sin certificado, el dominio dejó de estar verificado: el A cambió, DuckDNS devolvió otra IP, o el custom domain se volvió a añadir. no hay certificado que subir ni renovar a mano.
**arreglo**: confirmar que el dominio sigue `verified` en **Settings → Custom Domains** (o relanzar el `verify` de `docs/deployment.md` §5) y esperar la emisión. comprobar con:

```bash
curl -sI https://cosknot.duckdns.org/healthz
```

200 y certificado válido. mientras tanto `https://cosknot.onrender.com` sigue sirviendo la app y es la URL que usan el workflow y los chequeos.

nota: `cosknot.is-a.dev` queda solo como reserva; su PR sigue abierto y hoy no se usa.

## 11. `502 Bad Gateway` justo después del deploy

**síntoma**: el deploy figura como live pero toda petición devuelve 502, `/healthz` incluido.
**causa**: el proceso no está escuchando. import error al arrancar, gunicorn apuntando a un objeto que no existe, o gunicorn escuchando en un puerto distinto de `$PORT`.
**arreglo**: leer **Logs**, no el health check. tres comprobaciones: `startCommand` con `--bind 0.0.0.0:$PORT`; gunicorn contra `wsgi:app` (`wsgi.py` expone `app`, que `app.py` crea a nivel de módulo); y ninguna variable obligatoria ausente en el panel. si `/healthz` devolviera 503 en vez de 502, no es esto (entrada 2).

## 12. el servicio aparece suspendido sin un deploy fallido

**síntoma**: el servicio pasa a suspendido sin build ni deploy rojo; el aviso del panel habla de banda o de "service-initiated traffic".
**causa**: el plan free son 5 GB de banda al mes, y ese límite sí es oficial. la suspensión por tráfico saliente es anécdota de foro, no una regla publicada; no hay confirmación. no consta que haya pasado en este proyecto.
**arreglo**: revisar **Metrics** del servicio para ver el consumo real. si es banda agotada, esperar al ciclo siguiente y recortar lo que genere tráfico saliente: conexiones reutilizadas, nada de polling, estáticos con cache. si el aviso es por tráfico saliente y no hay consumo que lo explique, abrir ticket con soporte.
