# problemas con Render y Neon

> **Aviso histórico.** Este documento describe el despliegue antiguo en Render con
> Neon y se conserva como referencia. El despliegue actual es Heroku con Heroku
> Postgres; ver `docs/decisions/0003-heroku-hosting.md`. Nada de lo que hay debajo
> aplica a la producción de hoy.

Formato: síntoma, causa y arreglo. Los pasos de despliegue están en
`docs/deployment.md` y las copias de seguridad en `docs/backups.md`.

## la primera visita tarda unos 50 segundos

**Síntoma**: tras un rato sin tráfico, la primera petición tarda muchísimo y luego
carga. El flujo de despliegue puede salir en rojo en el paso que sondea `/healthz`.
**Causa**: el plan free de Render duerme el servicio a los 15 minutos. La primera
petición paga el arranque de gunicorn, la carga de Flask y SQLAlchemy, el `create_all`
con el seed y la reconexión a Neon, que también se despierta.
**Arreglo**: no es una caída. El flujo de despliegue da 5 minutos de margen. Si tarda más, hay que
mirar los logs, porque entonces el problema es otro.

## `/healthz` devuelve 503

**Síntoma**: `curl` da 503 y el cuerpo es `{"status":"error"}`. Render puede marcar el
despliegue como fallido aunque gunicorn esté escuchando.
**Causa**: `/healthz` no es un ping, hace un `SELECT 1`. El proceso está vivo y lo que
falla es la base de datos: Neon caído o suspendido, `DATABASE_URL` mal escrita, o la
conexión se abre pero la consulta se rechaza. Si en vez de 503 sale 502, el problema
sí es el proceso.
**Arreglo**: mirar el estado del proyecto en Neon y probar la misma cadena desde local
con `scripts/check_db.py`. Si ahí conecta y en Render no, comparar la variable del panel
carácter a carácter (un espacio o un salto de línea al final la rompen).

## el health check va bien pero la portada da 500

**Síntoma**: `/healthz` responde 200 y `/` o una ficha devuelve 500.
**Causa**: el health check solo prueba `SELECT 1`. La portada hace tres consultas y
renderiza la plantilla, así que un 500 suele ser de plantilla o de esquema: un
`url_for` a una ruta renombrada, una variable que no llega, o una columna nueva en
`models.py` que no existe en la tabla. `create_all()` no altera tablas que ya existen.
**Arreglo**: mirar la traza en los logs. Si es plantilla, reproducirlo en local contra
la misma base. Si es esquema, añadir la columna a mano o recrear la tabla.

## `connection refused` o `too many connections`

**Síntoma**: el despliegue arranca, la primera petición da 500 y el log muestra un fallo
contra un host `ep-xxxx.<region>.aws.neon.tech` sin `-pooler`, o un `too many
connections` al levantar los workers.
**Causa**: la cadena directa no pasa por el pooler y se come el límite de conexiones
del plan free. Con `--workers 2 --threads 4` cada worker abre su propio pool.
**Arreglo**: usar la cadena pooled, la que lleva `-pooler`, sin parámetros. Si sigue
agotándose, bajar a `--workers 1 --threads 8` antes de tocar el pool.

## errores raros de prepared statements

**Síntoma**: consultas que fallan y funcionan alternando, sobre todo en la primera
petición de cada worker o después de que Neon despierte.
**Causa**: el pooler de Neon en modo transacción no guarda estado de sesión. psycopg3
cachea prepared statements por conexión y el servidor que atiende cambia.
**Arreglo**: ya está aplicado en `build_engine()` con `prepare_threshold: None`, que
desactiva la caché.

## el push no despliega nada

**Síntoma**: el commit está en `main` pero Render sigue sirviendo el anterior, o en
Actions no aparece ninguna ejecución.
**Causa**: el autodespliegue está apagado, mira otra rama, o el push no llegó a `main`.
**Arreglo**: revisar **Settings → Build & Deploy** en Render (Auto-Deploy en yes,
trigger `commit`, branch `main`). En GitHub, mirar si el flujo de trabajo está activo y si
existen los secretos `RENDER_API_KEY` y `RENDER_SERVICE_ID`; si faltan, el paso del
trigger se salta y solo queda el sondeo de salud.

## los datos vuelven al catálogo de ejemplo

**Síntoma**: después de un despliegue, la web vuelve a tener 7 creadores y 15 obras.
**Causa**: el disco de Render es efímero. Si falta `DATABASE_URL`, la app cae a SQLite
en `cosknot.db`, responde 200 y pierde todo en el siguiente despliegue sin dar ningún
error.
**Arreglo**: tener `DATABASE_URL` siempre definida en Render y usar SQLite solo en
local. Si aparece el fallback, definir la variable, redesplegar y comprobar los conteos
con `check_db.py`.

## la cuota de Neon se agota

**Síntoma**: a mitad de mes todo falla al conectar y el proyecto aparece con el compute
suspendido. La copia del domingo también falla.
**Causa**: el plan free son 100 horas de cómputo al mes. Con el mínimo son unas 400
horas despiertas de las 730 de un mes, así que cualquier cosa que toque la base con
frecuencia la mantiene encendida.
**Arreglo**: quitar lo que despierte la base sin necesidad y dejar que Neon se suspenda
solo a los 5 minutos. Nada de keep-alive ni de uptime checks contra la base.

## el dominio sigue `unverified`

**Síntoma**: `cosknot.duckdns.org` aparece sin verificar, **Verify** no cambia nada y la
web no carga por ese dominio.
**Causa**: el registro A no apunta a `216.24.57.1`, o DuckDNS conserva una IP vieja.
**Arreglo**: comprobar con `nslookup cosknot.duckdns.org 1.1.1.1`. Si no sale
`216.24.57.1`, corregirlo en DuckDNS o por API, esperar un minuto y volver a verificar.

## no se emite el certificado HTTPS

**Síntoma**: el dominio ya está verificado pero el navegador da error de certificado.
**Causa**: el certificado es el segundo paso y no empieza hasta que la verificación
termina. La emisión tarda unos minutos. Si pasan horas, el dominio dejó de estar
verificado.
**Arreglo**: confirmar que sigue `verified` y esperar. Se comprueba con
`curl -sI https://cosknot.duckdns.org/healthz`.

## 502 justo después del despliegue

**Síntoma**: el despliegue sale como live pero todo devuelve 502, `/healthz` incluido.
**Causa**: el proceso no está escuchando: un import roto, gunicorn apuntando a un objeto
que no existe, o escuchando en otro puerto.
**Arreglo**: leer los logs. Comprobar que el start command lleva
`--bind 0.0.0.0:$PORT` y que apunta a `wsgi:app`.
