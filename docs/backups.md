# Backups y deploy

## Qué hace cada workflow

| Workflow | Disparo | Qué hace | Retención |
|---|---|---|---|
| `.github/workflows/deploy.yml` | push a `main`, `workflow_dispatch` | POST al deploy hook de Render y espera `/healthz` 200 (20 intentos, 15 s) | — |
| `.github/workflows/backup.yml` | domingo 03:00 UTC, `workflow_dispatch` | `pg_dump` formato custom y lo sube como artefacto `cosknot-db-<run_number>` | 30 días |

El repo se creó en Render desde "Public Git Repository": no hay auto-deploy por push. El único camino a producción es el deploy hook.

## Secretos del repositorio

```bash
gh secret set RENDER_DEPLOY_HOOK
gh secret set NEON_DATABASE_URL
```

- `RENDER_DEPLOY_HOOK`: Render → servicio `cosknot` → **Settings** → **Deploy Hook** → copiar la URL completa (`https://api.render.com/deploy/...`).
- `NEON_DATABASE_URL`: Neon Console → proyecto → **Connect** → **desactivar Connection pooling** → copiar la cadena `postgresql://...` directa. La cadena con `-pooler` no sirve para `pg_dump`.

## Restaurar

```bash
pg_restore --clean --no-owner -d "$NEON_DATABASE_URL" cosknot-db-N.dump
```

`N` es el `run_number` del workflow; el dump se descarga desde la pestaña Artifacts del run.

## Fallos frecuentes

| Síntoma | Causa | Arreglo |
|---|---|---|
| Hook responde 404 | Servicio borrado o hook regenerado | Recrear el servicio o copiar el hook nuevo al secreto |
| Health check nunca responde | Cold start > 5 min o crash en el arranque | Revisar logs en Render; subir el margen de intentos o corregir el arranque |
| Dump de menos de 1 KB | Cadena con `-pooler` o credenciales malas | Usar la cadena directa de Neon |
| `pg_dump: server version mismatch` | Cliente del runner más viejo que el servidor Neon | Instalar `postgresql-client` de la versión del servidor en el paso de apt |
