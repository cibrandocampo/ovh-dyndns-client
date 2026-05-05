# T020 — Sincronizar `env.example` con `docs/CONFIGURATION.md`

## Context

Tras la security hardening de v5.0.0, `docs/CONFIGURATION.md` se actualizó
para documentar el nuevo modelo de configuración (auto-generación de
`JWT_SECRET` y `ENCRYPTION_KEY`, defaults para `ADMIN_USERNAME`/`ADMIN_PASSWORD`).
Pero `env.example` quedó atrás: todavía muestra `JWT_SECRET=your-secure-random-secret-key`
con un comentario engañoso ("recommended to change in production") y omite
todas las variables nuevas. Es el primer fichero que copia un self-hoster,
por lo que da una imagen incorrecta del modelo v5.

Plan de referencia: [docs/plans/docs-alignment-v5.md](../plans/docs-alignment-v5.md)

**Dependencies**: None.

## Objective

`env.example` queda como espejo verbatim del bloque `## Example .env File`
de `docs/CONFIGURATION.md` (líneas 125-147). Una sola fuente canónica para
el ejemplo `.env`, copiada exactamente a `env.example`.

## Step 1 — Leer el bloque canónico de CONFIGURATION.md

Localizar y leer la sección `## Example .env File` de `docs/CONFIGURATION.md`
(actualmente líneas 125-147). Es el contenido exacto que debe quedar en
`env.example`. Incluye:

- Comentarios de sección (`# Project`, `# API`, `# Data persistence`, `# Security`, `# Admin user`, `# Logging`).
- Variables con defaults documentados.
- Variables opcionales marcadas como comentarios (`# JWT_SECRET=`, `# ENCRYPTION_KEY=`, `# ADMIN_PASSWORD=`).

## Step 2 — Reescribir `env.example`

Reemplazar el contenido completo de `env.example` con el bloque copiado
desde `docs/CONFIGURATION.md`. Mantener:

- Línea de cabecera tipo `# OVH DynDNS Client - Environment Variables`
  y `# Copy this file to .env and adjust values as needed` (o equivalente
  acorde con CONFIGURATION.md).
- Estructura por secciones idéntica a CONFIGURATION.md.
- Sin defaults inline para `JWT_SECRET` y `ENCRYPTION_KEY` (deben aparecer
  comentados, vacíos, indicando que se autogeneran si no se establecen).
- `ADMIN_USERNAME=admin` sin comentar (es un default seguro).
- `# ADMIN_PASSWORD=` comentado con explicación de que el default es
  `admin` y se fuerza cambio en primer login.

Resultado esperado (esquemático — la versión final viene del plan, sección
"Design proposal"):

```ini
# OVH DynDNS Client - Environment Variables
# Copy this file to .env and adjust values as needed

# Project
PROJECT_NAME=ovh-dyndns-client
DOCKER_OVH_VERSION=stable

# API
API_PORT=8000

# Data persistence (SQLite + secrets — protect this directory!)
DATA_PATH=./data

# Security — both auto-generated under data/ if not set.
# Set explicit values only if you need them fixed across deployments.
# JWT_SECRET=
# ENCRYPTION_KEY=

# Admin user — change immediately after first login!
ADMIN_USERNAME=admin
# ADMIN_PASSWORD=  # default 'admin', change required on first login

# Logging
LOGGER_LEVEL=INFO
```

## Step 3 — Verificación cruzada

Comparar línea a línea `env.example` con la sección `## Example .env File`
de `docs/CONFIGURATION.md`. Salvo la cabecera `# OVH DynDNS Client - ...`,
deben coincidir literalmente. Cualquier variable que aparezca en la **tabla
de variables** de CONFIGURATION.md (líneas 5-19) y NO esté en el ejemplo
queda fuera por decisión consciente — documentado en el plan.

Variables fuera de alcance por decisión (no añadir a env.example):

- `LOGGER_NAME` — raramente customizado.
- `JWT_EXPIRATION_HOURS` — tuning, no setup mínimo.
- `DATA_DIR`, `DATABASE_PATH` — rutas internas del contenedor.

## DoD — Definition of Done

1. `env.example` contiene exactamente las secciones `# Project`, `# API`,
   `# Data persistence`, `# Security`, `# Admin user`, `# Logging`, en
   ese orden.
2. `JWT_SECRET` y `ENCRYPTION_KEY` aparecen como líneas comentadas
   (`# JWT_SECRET=` y `# ENCRYPTION_KEY=`), no con valores placeholder.
3. `ADMIN_USERNAME=admin` sin comentar; `# ADMIN_PASSWORD=` comentado
   con nota inline.
4. `LOGGER_NAME`, `JWT_EXPIRATION_HOURS`, `DATA_DIR`, `DATABASE_PATH`
   NO aparecen en `env.example` (decisión documentada en el plan).
5. `diff <(grep -E "^[A-Z_]+=" env.example | cut -d= -f1) <(grep -E "^[A-Z_]+=" <(awk '/```ini/,/```$/' docs/CONFIGURATION.md) | cut -d= -f1)`
   no muestra diferencias en variables no comentadas.

## Evidence to produce

| # | Description | Command | File | PASS condition |
|---|-------------|---------|------|----------------|
| 1 | Contenido final de `env.example` | `cat env.example 2>&1` | `env_example.txt` | Coincide con la estructura del Step 2 |
| 2 | Diff de variables activas vs CONFIGURATION.md | `diff <(grep -E '^[A-Z_]+=' env.example \| cut -d= -f1 \| sort) <(awk '/^\`\`\`ini/,/^\`\`\`$/' docs/CONFIGURATION.md \| grep -E '^[A-Z_]+=' \| cut -d= -f1 \| sort) 2>&1` | `vars_diff.txt` | Sin diferencias (output vacío) |
| 3 | Lista de variables comentadas (opcionales) en `env.example` | `grep -E '^# [A-Z_]+=' env.example 2>&1` | `commented_vars.txt` | Incluye `JWT_SECRET`, `ENCRYPTION_KEY`, `ADMIN_PASSWORD` |
| 4 | Validación de no-introducción de variables fuera de alcance | `grep -E '^(LOGGER_NAME\|JWT_EXPIRATION_HOURS\|DATA_DIR\|DATABASE_PATH)=' env.example 2>&1; echo "exit=$?"` | `out_of_scope_check.txt` | exit=1 (grep no encuentra) |

## Files to create/modify

| File | Action |
|------|--------|
| `env.example` | MODIFY (reescritura completa) |

---

## Execution evidence

**Date**: 2026-05-05
**Modified files**:
- `env.example` — reescritura completa como espejo del bloque `## Example .env File` de `docs/CONFIGURATION.md`. Conserva las dos líneas de cabecera del fichero original (`# OVH DynDNS Client - Environment Variables` / `# Copy this file to .env and adjust values as needed`); el resto del contenido coincide literalmente con CONFIGURATION.md.

### Verification table

| # | Deliverable | Evidence file | Result |
|---|------------|---------------|--------|
| 1 | Contenido final de `env.example` | `docs/tasks/evidence/T020/env_example.txt` | PASS — secciones `# Project`, `# API`, `# Data persistence`, `# Security`, `# Admin user`, `# Logging` en orden |
| 2 | Diff variables activas vs CONFIGURATION.md | `docs/tasks/evidence/T020/vars_diff.txt` | PASS — diff vacío, exit=0 |
| 3 | Variables comentadas (opcionales) | `docs/tasks/evidence/T020/commented_vars.txt` | PASS — `JWT_SECRET`, `ENCRYPTION_KEY`, `ADMIN_PASSWORD` presentes |
| 4 | Variables fuera de alcance ausentes | `docs/tasks/evidence/T020/out_of_scope_check.txt` | PASS — exit=1 (grep no encuentra `LOGGER_NAME`, `JWT_EXPIRATION_HOURS`, `DATA_DIR`, `DATABASE_PATH`) |

### Design decisions

- **Cabecera del fichero**: se conservaron las dos líneas comentario de cabecera del `env.example` original (`# OVH DynDNS Client - Environment Variables` / `# Copy this file to .env and adjust values as needed`). El task lo permite explícitamente ("o equivalente acorde con CONFIGURATION.md") y aporta contexto que el bloque ini de CONFIGURATION.md no incluye porque allí la sección madre ya da contexto.
- **Variables fuera de alcance** (`LOGGER_NAME`, `JWT_EXPIRATION_HOURS`, `DATA_DIR`, `DATABASE_PATH`): no se añaden al ejemplo, conforme a la decisión documentada en el plan (`docs/plans/docs-alignment-v5.md`, sección "Design proposal §1").
- **Sin cambios de código ni tests**: tarea puramente documental; no se ejecutan suites — el plan deja explícito que `env.example` no afecta runtime.
