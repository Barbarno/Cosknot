# copias de seguridad y despliegue

## qué hace cada flujo de trabajo

| flujo | cuándo | qué hace | cuánto se guarda |
|---|---|---|---|
| `.github/workflows/deploy.yml` | push a `main` o a mano | busca el despliegue de ese commit en la API de Render y espera a que quede en `live` | nada |
| `.github/workflows/backup.yml` | domingos a las 03:00 UTC o a mano | hace un `pg_dump` en formato custom, lo cifra y sube `cosknot-db-<run_number>.dump.enc` como artefacto | 30 días |

El servicio tiene el autodespliegue activado en Render, así que normalmente Render
despliega solo cuando ve el commit. El flujo de despliegue lo fuerza cuando el sondeo
de Render no lo pilla y, de paso, avisa si `/healthz` no responde.

## secretos del repositorio

```bash
gh secret set RENDER_API_KEY
gh secret set RENDER_SERVICE_ID
gh secret set NEON_DATABASE_URL
gh secret set BACKUP_PASSPHRASE
```

- `RENDER_API_KEY`: en Render, avatar → **Account Settings** → **API Keys**. Solo se
  muestra una vez.
- `RENDER_SERVICE_ID`: `srv-dbqte8bl550s73er4bcg`, el servicio `cosknot`.
- `NEON_DATABASE_URL`: en la consola de Neon, **Connect**, desactiva el connection
  pooling y copia la cadena `postgresql://...` directa. La que lleva `-pooler` no
  sirve para `pg_dump`.
- `BACKUP_PASSPHRASE`: la contraseña con la que se cifra el dump. Sin ella los
  artefactos son inservibles, así que vive en dos sitios: el secreto del repositorio
  y un gestor de contraseñas. El repositorio es público y los artefactos los puede
  descargar cualquier cuenta de GitHub, por eso el dump no se sube en claro.

## restaurar una copia

El artefacto se descarga desde la pestaña Artifacts de la ejecución y se descifra antes
de restaurar:

```bash
openssl enc -d -aes-256-cbc -pbkdf2 \
  -in cosknot-db-N.dump.enc -out cosknot-db-N.dump \
  -pass env:BACKUP_PASSPHRASE
pg_restore --clean --no-owner -d "$NEON_DATABASE_URL" cosknot-db-N.dump
```

`N` es el número de ejecución del flujo de trabajo. La cabecera de un dump sin cifrar
son los bytes `PGDMP`; si el fichero empieza por `Salted__` es que sigue cifrado.

## fallos que ya me han pasado

| síntoma | causa | arreglo |
|---|---|---|
| el trigger devuelve 401 o 404 | clave revocada o `RENDER_SERVICE_ID` mal | regenerar la clave y actualizar el secreto |
| el health check no responde nunca | arranque lento o crash | mirar los logs de Render y corregir el arranque |
| el dump ocupa menos de 1 KB | cadena con `-pooler` o credenciales malas | usar la cadena directa de Neon |
| `pg_dump: server version mismatch` | cliente más viejo que el servidor | instalar el `postgresql-client` de la versión del servidor |
