# troubleshooting: render + neon

formato: síntoma → causa → arreglo.

## 1. la base de datos vuelve vacía después de cada deploy

**síntoma**: los usuarios/obras creados desaparecen tras un redeploy o tras reiniciar el servicio; el fichero `.db` no está.
**causa**: sqlite sobre el filesystem de render, que es efímero. cada deploy monta un contenedor nuevo y el fichero se va con el anterior.
**arreglo**: mover todo a neon. `DATABASE_URL` como variable de entorno y el engine de sqlalchemy apuntando ahí. sqlite solo en local.

## 2. `could not connect to server` / `connection refused` tras poner la cadena

**síntoma**: el deploy arranca pero el primer request da 500 y el log muestra fallo de conexión al host `ep-xxxx.<region>.aws.neon.tech`.
**causa**: cadena directa (sin `-pooler`) o `sslmode` ausente. en el plan free el número de conexiones directas es bajo y gunicorn abre varias por worker.
**arreglo**: copiar de neon la cadena **pooled** (`...-pooler...`) y terminar en `?sslmode=require`. en sqlalchemy, `create_engine(url, pool_pre_ping=True)`.

## 3. `prepared statement "s0" already exists` o `bind message supplies N parameters`

**síntoma**: errores intermitentes al consultar, sobre todo tras el primer request de cada worker.
**causa**: el pooler de neon (pgbouncer, transaction mode) no soporta prepared statements a nivel de sesión; psycopg los cachea por conexión y el server las reasigna.
**arreglo**: en la cadena pooled añadir `?sslmode=require&prepare_threshold=0`, o en el engine `connect_args={"prepare_threshold": 0}`. si se usa sqlalchemy con `psycopg`, ese ajuste desactiva la caché.

## 4. el primer acceso del día tarda un minuto y parece caído

**síntoma**: el navegador gira ~60 s y luego carga; los monitores externos marcan el sitio como down a intervalos.
**causa**: render free duerme el servicio a los 15 min sin tráfico; el arranque de gunicorn más el import de flask y la reconexión a neon suman ese minuto. neon además despierta el compute en el primer `SELECT` (~1 s).
**arreglo**: no es una caída, es cold start. aceptarlo en el mvp, o pasar a plan de pago / cloud run. no poner keep-alive contra neon para evitarlo (ver entrada 5).

## 5. neon suspende el compute a mitad de mes

**síntoma**: a partir de la segunda quincena, todo request devuelve error de conexión; en el panel de neon el proyecto figura suspendido por cuota.
**causa**: el plan free son 100 cu-horas por proyecto y mes. a 0,25 cu (mínimo) son ~400 h de compute despierto; un mes tiene ~730 h. cualquier ping periódico mantiene el compute encendido y agota la cuota.
**arreglo**: quitar crons, uptime checks y keep-alive contra la db. dejar que neon haga scale-to-zero a los 5 min. al llegar el día 1 del mes siguiente se reactiva solo. si el uso es real y constante, pasar a plan de pago.

## 6. render suspende el servicio por banda o por tráfico saliente

**síntoma**: el servicio pasa a estado suspendido sin un deploy fallido; el panel muestra aviso de límite de banda o de "service-initiated traffic".
**causa**: el plan free son 5 gb de banda al mes y hay reportes de suspensión cuando la app genera mucho tráfico saliente (llamadas a la db, cron, webhooks). es anécdota de foro, no una regla publicada, pero el límite de banda sí es oficial.
**arreglo**: revisar **Metrics** del servicio. recortar peticiones salientes (una conexión reutilizada, sin polling), servir estáticos con cache, y esperar al día 1 si es banda agotada. contactar soporte si la suspensión es por tráfico saliente.

## 7. HTTPS no se emite en `cosknot.is-a.dev`

**síntoma**: el dominio responde por http o el navegador da `ERR_CERT_COMMON_NAME_INVALID`; render deja el dominio en "pending verification".
**causa**: render emite el certificado con let's encrypt solo cuando el CNAME ya resuelve públicamente hacia `cosknot.onrender.com`. si se añade el dominio antes del merge del PR en is-a.dev, la verificación nunca termina.
**arreglo**: confirmar con `nslookup cosknot.is-a.dev` que devuelve el CNAME, esperar la propagación (minutos a horas), y volver a pulsar **Verify** en render. si el CNAME apunta a otro sitio, el certificado no se emite hasta corregirlo.

## 8. `502 Bad Gateway` justo después del deploy

**síntoma**: el deploy dice "live" pero toda petición devuelve 502; `/healthz` también.
**causa**: el proceso muere al arrancar — import error en `wsgi.py`, `DATABASE_URL` ausente, o gunicorn escuchando en un puerto distinto del `$PORT`.
**arreglo**: leer **Logs** del servicio, no el health check. los tres fallos habituales: `startCommand` sin `--bind 0.0.0.0:$PORT`, `app.py` sin `app` a nivel de módulo, y variable de entorno no definida en el panel.
