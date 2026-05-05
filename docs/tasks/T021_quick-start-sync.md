# T021 — Sincronizar snippet `docker-compose.yaml` en README quick-start + landing

## Context

El bloque YAML del quick-start del `README.md` (líneas 83-96) y la
constante `snippet` de `site/src/components/SelfHost.astro` (líneas 2-13)
divergen del `docker-compose.yaml` de producción del repo: usan
`restart: always`, no incluyen `init: true` ni `healthcheck`. El resultado
son tres versiones distintas del mismo compose en tres documentos, lo
que confunde al usuario nuevo y envía señales contradictorias sobre qué
defaults son los recomendados.

La decisión confirmada con el usuario es sincronizar al 100% con
producción manteniendo el bind mount directo `./data:/app/data` (sin la
indirección de named volume del compose raíz, que añade ruido conceptual
para un primer arranque).

Plan de referencia: [docs/plans/docs-alignment-v5.md](../plans/docs-alignment-v5.md)

**Dependencies**: None.

## Objective

`README.md` quick-start y `site/src/components/SelfHost.astro` muestran
**el mismo** bloque YAML, alineado con el `docker-compose.yaml` de
producción (`init: true`, `restart: unless-stopped`, `healthcheck`),
pero usando bind mount directo. La build de la landing (`cd site &&
npm run build`) sigue pasando.

## Step 1 — YAML canónico

Este es el bloque de referencia que debe aparecer **literalmente** en
ambos sitios:

```yaml
services:
  ovh-dyndns-client:
    image: cibrandocampo/ovh-dyndns-client:stable
    container_name: ovh-dyndns-client
    init: true
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

## Step 2 — Reemplazar el bloque del README quick-start

En `README.md`, localizar el bloque `## Quick Start` y dentro de él el
fenced block ` ```yaml ` que empieza con `services:` (actualmente líneas
83-96, pueden haber cambiado). Reemplazar el contenido del fenced block
por el YAML del Step 1.

**No tocar** las líneas 81 ("**Create `docker-compose.yaml`:**"), 98-104
(comandos `docker compose up -d`, `Access`, `Default credentials`) ni
ninguna otra parte del README. Solo el cuerpo del fenced block YAML.

## Step 3 — Reemplazar la constante `snippet` en SelfHost.astro

En `site/src/components/SelfHost.astro`, localizar la constante
`const snippet = ...` (actualmente líneas 2-21). Es un template literal
que combina los pasos `# 1. Create docker-compose.yaml`, `# 2. Start
it`, `# 3. Open http://localhost:8000`. Sustituir el bloque YAML
embebido (entre `cat > docker-compose.yaml <<'YAML'` y `YAML`) por el
del Step 1, **manteniendo intactos** los pasos 2 y 3 y los comentarios
narrativos.

Resultado esperado de la constante (esquemático):

```ts
const snippet = `# 1. Create docker-compose.yaml
cat > docker-compose.yaml <<'YAML'
services:
  ovh-dyndns-client:
    image: cibrandocampo/ovh-dyndns-client:stable
    container_name: ovh-dyndns-client
    init: true
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
YAML

# 2. Start it
mkdir -p data
docker compose up -d

# 3. Open http://localhost:8000 (default admin/admin, change required on first login)
`
```

El resto del componente (HTML, script de copy-to-clipboard) no cambia.

## Step 4 — Verificar build de la landing

Ejecutar la build de Astro para confirmar que el cambio en
`SelfHost.astro` no rompe la compilación. Las dependencias de `site/`
ya deben estar instaladas; si no lo están, ejecutar `npm ci` primero.

```bash
cd site && npm ci 2>&1 | tail -5    # solo si node_modules no existe
cd site && npm run build 2>&1 | tail -20
```

La build debe terminar con éxito (`✓ Completed in <Xms>`) y generar
`site/dist/index.html`. Inspeccionar `site/dist/index.html` y confirmar
que contiene `restart: unless-stopped` (señal de que el snippet
embebido se ha actualizado).

## Step 5 — Verificación cruzada README ↔ landing

Comparar el bloque YAML del README con el de la landing. Deben
coincidir literalmente (mismas líneas, mismo orden, misma indentación
de 2 espacios).

## DoD — Definition of Done

1. `README.md` quick-start muestra el YAML del Step 1, con `init: true`,
   `restart: unless-stopped` y `healthcheck`.
2. `site/src/components/SelfHost.astro` tiene el mismo YAML embebido en
   la constante `snippet`, dentro de los marcadores `cat > docker-compose.yaml
   <<'YAML' ... YAML`.
3. `cd site && npm run build` finaliza sin errores y genera
   `site/dist/index.html`.
4. `site/dist/index.html` contiene la string `restart: unless-stopped`
   (confirma que el snippet llegó al output).
5. El bloque YAML del README y el de la constante de SelfHost.astro
   coinciden literalmente (mismo `diff` vacío sobre las líneas YAML
   propias).
6. Ningún otro fichero ha sido modificado.

## Evidence to produce

| # | Description | Command | File | PASS condition |
|---|-------------|---------|------|----------------|
| 1 | Bloque YAML extraído del README | `awk '/^```yaml$/,/^```$/' README.md \| head -50 2>&1` | `readme_yaml.txt` | Contiene `init: true`, `restart: unless-stopped`, `healthcheck:` |
| 2 | Constante `snippet` extraída de SelfHost.astro | `awk '/const snippet =/,/^---$/' site/src/components/SelfHost.astro 2>&1` | `selfhost_snippet.txt` | Contiene `init: true`, `restart: unless-stopped`, bloque healthcheck |
| 3 | Build de la landing | `cd site && npm run build 2>&1 \| tail -30` | `site_build.txt` | Termina con `✓ Completed`, sin errores |
| 4 | Snippet renderizado en HTML | `grep -c "restart: unless-stopped" site/dist/index.html 2>&1` | `dist_render_check.txt` | Output ≥ 1 |
| 5 | Comparación de los dos YAML (líneas YAML literales) | `diff <(awk '/^```yaml$/,/^```$/' README.md \| sed -n '/services:/,/start_period:/p') <(awk '/cat > docker-compose.yaml/,/^YAML$/' site/src/components/SelfHost.astro \| sed -n '/services:/,/start_period:/p') 2>&1` | `cross_diff.txt` | Sin diferencias (output vacío) |
| 6 | Estado git de ficheros modificados | `git status --porcelain README.md site/src/components/SelfHost.astro 2>&1` | `git_status.txt` | Solo aparecen estos dos ficheros marcados como modificados |

## Files to create/modify

| File | Action |
|------|--------|
| `README.md` | MODIFY (reemplazar el bloque YAML del quick-start) |
| `site/src/components/SelfHost.astro` | MODIFY (reemplazar el YAML dentro de la constante `snippet`) |

---

## Execution evidence

**Date**: 2026-05-05
**Modified files**:
- `README.md` — bloque YAML del quick-start sustituido por la versión sincronizada con producción (`init: true`, `restart: unless-stopped`, `healthcheck`). Eliminado el comentario inline sobre `JWT_SECRET`/`ENCRYPTION_KEY` autogen porque ya está cubierto por el callout v5 (líneas 24-38) y por `env.example`.
- `site/src/components/SelfHost.astro` — YAML embebido en la constante `snippet` reemplazado por el mismo bloque canónico, manteniendo intactos los pasos `# 1.`, `# 2.`, `# 3.` que rodean el `cat > docker-compose.yaml <<'YAML' ... YAML`.

### Verification table

| # | Deliverable | Evidence file | Result |
|---|------------|---------------|--------|
| 1 | YAML del README contiene `init: true`, `restart: unless-stopped`, `healthcheck:` | `docs/tasks/evidence/T021/readme_yaml.txt` | PASS |
| 2 | Constante `snippet` de SelfHost.astro contiene el mismo bloque | `docs/tasks/evidence/T021/selfhost_snippet.txt` | PASS |
| 3 | `cd site && npm run build` finaliza sin errores | `docs/tasks/evidence/T021/site_build.txt` | PASS — `1 page(s) built in 1.19s`, 0 errors / 0 warnings |
| 4 | `restart: unless-stopped` presente en `site/dist/index.html` | `docs/tasks/evidence/T021/dist_render_check.txt` | PASS — output `1` |
| 5 | Diff YAML entre README y SelfHost.astro vacío | `docs/tasks/evidence/T021/cross_diff.txt` | PASS — sin diferencias, exit=0 |
| 6 | Solo se han modificado los dos ficheros esperados | `docs/tasks/evidence/T021/git_status.txt` | PASS — únicamente `README.md` y `site/src/components/SelfHost.astro` |

### Design decisions

- **Comentario eliminado del bloque del README**: el README anterior incluía un comentario inline (`# JWT_SECRET and ENCRYPTION_KEY are auto-generated under ./data on first start...`). Como el plan no lo menciona y la información ya está en el callout v5 superior y en `env.example`, se elimina del YAML para mantenerlo limpio y mantener la igualdad literal con el snippet de la landing (que tampoco lo lleva). Resultado: el bloque del quick-start es exactamente el del docker-compose.yaml de producción menos la indirección de named volume.
- **Bind mount directo `./data:/app/data`**: confirmado en el plan. No se importa la indirección `volumes: ovh-dyndns-data: { driver: local, driver_opts: ... }` del `docker-compose.yaml` raíz porque añade ruido conceptual para un primer-uso sin aportar valor.
