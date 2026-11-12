# Backups y deploy

## Qué hace cada workflow

| Workflow | Disparo | Qué hace | Retención |
|---|---|---|---|
| `.github/workflows/deploy.yml` | push a `main`, `workflow_dispatch` | `POST /v1/services/<id>/deploys` en la API de Render y espera `/healthz` 200 (20 intentos, 15 s) | — |
| `.github/workflows/backup.yml` | domingo 03:00 UTC, `workflow_dispatch` | `pg_dump` formato custom y lo sube como artefacto `cosknot-db-<run_number>` | 30 días |

El servicio tiene `autoDeploy: yes` sobre el repo público, así que Render también despliega por su cuenta al detectar el commit. El workflow fuerza el deploy cuando ese polling no lo pilla y sirve de verificación: si `/healthz` no responde, el push se marca en rojo.

## Secretos del repositorio

```bash
gh secret set RENDER_API_KEY
gh secret set RENDER_SERVICE_ID
gh secret set NEON_DATABASE_URL
```

- `RENDER_API_KEY`: Render → avatar → **Account Settings** → **API Keys** → crear. Solo se muestra una vez.
- `RENDER_SERVICE_ID`: `srv-dbqte8bl550s73er4bcg` (servicio `cosknot`).
- `NEON_DATABASE_URL`: Neon Console → proyecto → **Connect** → **desactivar Connection pooling** → copiar la cadena `postgresql://...` directa. La cadena con `-pooler` no sirve para `pg_dump`.

## Restaurar

```bash
pg_restore --clean --no-owner -d "$NEON_DATABASE_URL" cosknot-db-N.dump
```

`N` es el `run_number` del workflow; el dump se descarga desde la pestaña Artifacts del run.

## Fallos frecuentes

| Síntoma | Causa | Arreglo |
|---|---|---|
| Trigger responde 401/404 | Clave de API revocada o `RENDER_SERVICE_ID` mal | Regenerar la clave y actualizar el secreto |
| Health check nunca responde | Cold start > 5 min o crash en el arranque | Revisar logs en Render; subir el margen de intentos o corregir el arranque |
| Dump de menos de 1 KB | Cadena con `-pooler` o credenciales malas | Usar la cadena directa de Neon |
| `pg_dump: server version mismatch` | Cliente del runner más viejo que el servidor Neon | Instalar `postgresql-client` de la versión del servidor en el paso de apt |
