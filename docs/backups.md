# copias de seguridad

Hay dos copias y ninguna depende de la otra: la que gestiona Heroku y un volcado
diario propio que se queda fuera de Heroku.

| copia | cuándo | herramienta | dónde | cuánto se guarda |
|---|---|---|---|---|
| gestionada | a diario, 03:00 UTC | `pg:backups:schedule` de Heroku | almacenamiento de Heroku Postgres | según el plan |
| propia | a diario, por cron del flujo de trabajo | `pg_dump` y `openssl` | Cloudflare R2 | 30 días |

Heroku Postgres Essential-0 no tiene rollback, así que la copia diaria no es un
extra: es el plan B cuando una migración rompe algo.

## copia gestionada de Heroku

```bash
heroku pg:backups:schedule DATABASE_URL --at '03:00 UTC'
heroku pg:backups
```

`heroku pg:backups:schedule` deja la programación en el add-on, no en el
repositorio. `heroku pg:backups` lista las copias con su identificador y su estado;
`heroku pg:backups:download` baja una concreta.

## copia propia en GitHub Actions

`backup.yml` hace, en este orden:

1. obtiene `DATABASE_URL` en tiempo de ejecución desde Heroku con
   `heroku config:get DATABASE_URL`, así que la cadena de la base no está guardada
   en los secretos del repositorio;
2. vuelca con `pg_dump --format=custom --no-owner --no-privileges`;
3. cifra con `openssl enc -aes-256-cbc -pbkdf2 -salt -pass env:BACKUP_PASSPHRASE`;
4. sube el fichero a Cloudflare R2 con boto3 y `region_name="auto"`;
5. borra del bucket las copias con más de 30 días.

Ya no se usan artefactos de GitHub. El repositorio es público y cualquiera con
cuenta puede descargar un artefacto; el bucket de R2 es privado y el dump va
cifrado igualmente.

```bash
# lo mismo que hace el flujo, a mano
pg_dump --format=custom --no-owner --no-privileges -f cosknot.dump "$DATABASE_URL"
openssl enc -aes-256-cbc -pbkdf2 -salt -in cosknot.dump -out cosknot.dump.enc \
  -pass env:BACKUP_PASSPHRASE
rm -f cosknot.dump
```

## secretos del repositorio

```bash
gh secret set HEROKU_API_KEY
gh secret set BACKUP_PASSPHRASE
gh secret set R2_ENDPOINT_URL
gh secret set R2_BUCKET
gh secret set R2_ACCESS_KEY_ID
gh secret set R2_SECRET_ACCESS_KEY
```

- `HEROKU_API_KEY`: cuenta de Heroku → **Account settings** → **API Key**. Solo se
  muestra una vez.
- `BACKUP_PASSPHRASE`: la contraseña con la que se cifra el dump. Sin ella las
  copias son inservibles, así que vive en dos sitios: el secreto del repositorio y
  un gestor de contraseñas.
- `R2_ENDPOINT_URL`, `R2_BUCKET`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`: los
  mismos valores que usa la app para las imágenes, con un token que pueda escribir
  y borrar en el bucket de copias.

## versión del cliente `pg_dump`

El cliente tiene que ser de versión mayor o igual que el servidor. El flujo compara
las dos versiones antes de volcar —`pg_dump --version` frente al `server_version`
que devuelve la base— y falla con un mensaje claro si no se cumple, en lugar de
dejar un dump a medias o un error de protocolo a mitad de la subida.

Si Heroku sube la versión del servidor, se sube también la imagen del flujo antes
de la siguiente copia programada.

## restaurar una copia

```bash
openssl enc -d -aes-256-cbc -pbkdf2 \
  -in copia.dump.enc -out copia.dump \
  -pass env:BACKUP_PASSPHRASE
pg_restore --clean --no-owner --no-privileges -d "$DATABASE_URL" copia.dump
```

`--clean` borra los objetos antes de recrearlos, así que la restauración deja la
base exactamente como estaba en la copia. Sobre la base de producción se lanza con
la web parada: `heroku ps:scale web=0`, restaurar, `heroku ps:scale web=1`.

La cabecera de un dump sin cifrar son los bytes `PGDMP`; si el fichero empieza por
`Salted__` es que sigue cifrado.

## prueba de restauración

Una copia que nunca se ha restaurado no es una copia. La prueba se hace una vez al
mes:

1. crear una base local vacía:

   ```bash
   createdb cosknot_prueba
   ```

2. descargar la última copia de R2 y descifrarla con el comando de arriba, sin
   tocar `DATABASE_URL`;
3. restaurar en la base local:

   ```bash
   pg_restore --clean --no-owner --no-privileges \
     -d "postgresql://localhost/cosknot_prueba" copia.dump
   ```

4. contar filas en la copia restaurada:

   ```bash
   psql -d cosknot_prueba -c "select count(*) from works;"
   psql -d cosknot_prueba -c "select count(*) from users;"
   ```

5. contar lo mismo en producción y comparar:

   ```bash
   heroku pg:psql DATABASE_URL -c "select count(*) from works;"
   heroku pg:psql DATABASE_URL -c "select count(*) from users;"
   ```

Si los conteos de `works` y `users` coinciden con producción, la copia sirve. Si la
restauración falla o los números no cuadran, la copia del día no vale y el flujo de
`backup.yml` es lo primero que hay que mirar.

## fallos que ya me han pasado

| síntoma | causa | arreglo |
|---|---|---|
| la copia ocupa menos de 1 KB | credenciales malas o base vacía | comprobar `heroku config:get DATABASE_URL` y repetir el volcado |
| `pg_dump: server version mismatch` | cliente más viejo que el servidor | subir la versión de `postgresql-client` en el flujo |
| `pg_restore: error: could not execute query` al principio | `--clean` sobre una base con conexiones abiertas | cerrar las conexiones o restaurar en una base recién creada |
| el flujo falla al subir a R2 | bucket o token mal, o `region_name` distinto de `auto` | revisar los cuatro secretos de R2 |
| `heroku pg:psql` pide confirmación | falta `-a` con el nombre de la app | añadir `-a <app>` o ejecutar dentro del repositorio enlazado |
