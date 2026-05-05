# T022 — Añadir rate limits, `/api/version` y nota 403 a `docs/API.md`

## Context

`docs/API.md` no ha seguido el ritmo de los cambios v5: no menciona los
rate limits aplicados a `/api/auth/login` (5/min) y `/api/auth/change-password`
(10/min), no documenta el endpoint público `GET /api/version` que
existe desde el commit del despliegue del site, y no menciona la
respuesta `403 Password change required` que devuelve cualquier endpoint
protegido cuando el usuario aún no ha rotado la contraseña por defecto.

Estos huecos hacen que un consumidor de la API que se base solo en
`docs/API.md` (sin leer `CONFIGURATION.md`) no entienda por qué obtiene
429 o 403 en escenarios normales.

Plan de referencia: [docs/plans/docs-alignment-v5.md](../plans/docs-alignment-v5.md)

**Dependencies**: None.

## Objective

`docs/API.md` documenta:
1. La fila `GET /api/version` en la tabla de endpoints (público, sin auth).
2. Una nota corta de rate limiting al final de la sección "Authentication"
   con enlace a `docs/CONFIGURATION.md#rate-limiting`.
3. Una mención breve de `403 Password change required` como respuesta
   posible en endpoints protegidos.

## Step 1 — Añadir fila `GET /api/version` en la tabla de endpoints

En la tabla de la sección `## Endpoints` (actualmente líneas 44-58),
insertar una fila después de `/health`:

```
| GET    | `/api/version` | Application version (no auth required) |
```

La fila debe quedar al final de la tabla, después de la fila de `/health`,
manteniendo el alineamiento de columnas con el resto.

## Step 2 — Nota de rate limiting al final de "Authentication"

Tras la subsección `### Change Password` (actualmente termina en línea
40, antes de `## Endpoints` en línea 42), añadir un nuevo subapartado:

```markdown
### Rate limiting

Authentication endpoints are rate-limited per client IP:

- `POST /api/auth/login` — 5 requests per minute
- `POST /api/auth/change-password` — 10 requests per minute

Exceeding the limit returns `429 Too Many Requests`. See
[Rate limiting](CONFIGURATION.md#rate-limiting) for the full reference,
including reverse proxy considerations.
```

No duplicar la tabla completa de CONFIGURATION.md — la nota corta más
el enlace mantienen una única fuente de verdad.

## Step 3 — Mención de `403 Password change required`

En la sección `## Authentication`, justo después de `### Login`
(actualmente línea 22, después del primer ejemplo de respuesta JSON con
`access_token`), añadir un párrafo corto:

```markdown
**Note**: when `must_change_password` is `true` in the response, every
endpoint other than `POST /api/auth/change-password` will return
`403 Password change required` until the password is rotated. This
applies to the default `admin/admin` account on first deployment.
```

El propósito es advertir al consumidor de que `must_change_password=true`
no es informativo — bloquea el resto de la API.

## Step 4 — Verificación visual

Releer `docs/API.md` completo y confirmar:

- La tabla de endpoints incluye `/api/version` como última fila.
- La sección "Authentication" tiene una subsección `### Rate limiting`
  al final (antes de `## Endpoints`).
- Después de `### Login` aparece la nota sobre `must_change_password`.
- El enlace `[Rate limiting](CONFIGURATION.md#rate-limiting)` apunta a
  un anchor que existe en `docs/CONFIGURATION.md` (la sección
  `## Rate limiting` actual línea 166).

## DoD — Definition of Done

1. `docs/API.md` contiene la fila `| GET | \`/api/version\` |` en la
   tabla de endpoints.
2. `docs/API.md` contiene una sección o subsección titulada
   `Rate limiting` con los límites 5/min y 10/min documentados.
3. `docs/API.md` contiene la string `403 Password change required` en el
   contexto de la sección Authentication.
4. El enlace `CONFIGURATION.md#rate-limiting` apunta a un anchor real
   (la sección existe en `docs/CONFIGURATION.md`).
5. Ningún endpoint que ya existía en la tabla ha sido modificado o
   eliminado.

## Evidence to produce

| # | Description | Command | File | PASS condition |
|---|-------------|---------|------|----------------|
| 1 | Fila `/api/version` presente en la tabla | `grep -E '\\\| GET .*\`/api/version\`' docs/API.md 2>&1` | `version_row.txt` | Match exactamente 1 línea |
| 2 | Sección de rate limiting | `grep -nE '^### Rate limiting\|^## Rate limiting' docs/API.md 2>&1` | `rate_limiting_section.txt` | Output no vacío, indicando línea de cabecera |
| 3 | Límites documentados | `grep -E '5 requests per minute\|10 requests per minute' docs/API.md 2>&1` | `rate_limits.txt` | Ambas strings presentes |
| 4 | Nota de 403 password change | `grep -F '403 Password change required' docs/API.md 2>&1` | `password_change_note.txt` | Match exactamente 1 línea (al menos) |
| 5 | Enlace a CONFIGURATION.md#rate-limiting válido | `grep -F '(CONFIGURATION.md#rate-limiting)' docs/API.md 2>&1 && grep -E '^## Rate limiting' docs/CONFIGURATION.md 2>&1` | `link_anchor_check.txt` | Ambos greps con match (link + anchor existen) |
| 6 | Endpoints existentes intactos | `grep -cE '^\\\| (GET\|POST\|PUT\|DELETE) ' docs/API.md 2>&1` | `endpoint_count.txt` | Output = 14 (13 previos + 1 nuevo `/api/version`) |
| 7 | Estado git | `git status --porcelain docs/API.md 2>&1` | `git_status.txt` | Solo `docs/API.md` modificado |

## Files to create/modify

| File | Action |
|------|--------|
| `docs/API.md` | MODIFY (3 inserciones puntuales: fila tabla, subsección rate limiting, nota 403) |

---

## Execution evidence

**Date**: 2026-05-05
**Modified files**:
- `docs/API.md` — cuatro inserciones puntuales:
  1. Línea 3: actualizada para listar `/api/version` junto a `/api/auth/login` y `/health` como endpoints sin auth (coherencia con la nueva fila de la tabla).
  2. Tras el JSON response de `### Login`: nota de 4 líneas advirtiendo que `must_change_password=true` provoca `403 Password change required` en cualquier endpoint distinto de `change-password`.
  3. Tras `### Change Password`: nueva subsección `### Rate limiting` con los límites 5/min y 10/min, respuesta `429 Too Many Requests`, y enlace a `CONFIGURATION.md#rate-limiting`.
  4. Final de la tabla `## Endpoints`: nueva fila `| GET | \`/api/version\` | Application version (no auth required) |` justo después de `/health`.

### Verification table

| # | Deliverable | Evidence file | Result |
|---|------------|---------------|--------|
| 1 | Fila `/api/version` presente | `docs/tasks/evidence/T022/version_row.txt` | PASS — 1 match exacto |
| 2 | Sección `### Rate limiting` | `docs/tasks/evidence/T022/rate_limiting_section.txt` | PASS — encontrada en línea 47 |
| 3 | Límites 5/min y 10/min documentados | `docs/tasks/evidence/T022/rate_limits.txt` | PASS — ambas strings presentes |
| 4 | Nota `403 Password change required` | `docs/tasks/evidence/T022/password_change_note.txt` | PASS — 1 match |
| 5 | Enlace y anchor a CONFIGURATION.md | `docs/tasks/evidence/T022/link_anchor_check.txt` | PASS — link presente en API.md, sección `## Rate limiting` existe en CONFIGURATION.md |
| 6 | Total endpoints = 14 (13 + 1) | `docs/tasks/evidence/T022/endpoint_count.txt` | PASS — output `14` |
| 7 | Solo `docs/API.md` modificado | `docs/tasks/evidence/T022/git_status.txt` | PASS — únicamente `M docs/API.md` |

### Design decisions

- **Línea 3 actualizada (no estaba en el task original)**: la frase de cabecera enumeraba los endpoints sin autenticación (`/api/auth/login` y `/health`). Añadir `/api/version` a la tabla sin actualizar esa frase dejaría la documentación incoherente. La actualización es trivial (`/api/auth/login`, `/health` and `/api/version`) y consistente con la intención del task.
- **Posición de la nota 403**: entre el JSON response del Login y `### Using the Token`, no como subsección con su propio header. La nota está semánticamente ligada a la respuesta del login (es la consecuencia de `must_change_password: true`), por lo que vivir como "**Note**:" inline tras el ejemplo es más natural que abrir una subsección nueva.
- **Rate limiting como subsección hermana de Login/Change Password**: alternativa descartada — añadir el contenido al final del documento lejos de las secciones que limita. Mantenerlo dentro de `## Authentication` agrupa la información en un único lugar conceptual.
- **Sin duplicar la tabla completa de CONFIGURATION.md**: solo se enumeran los dos límites con un enlace al documento canónico. Una sola fuente de verdad.
