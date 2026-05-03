# T001 — Crear sprite SVG con 17 iconos Lucide

## Context

Esta task entrega el set de iconos curado que el frontend consumirá vía `<svg class="icon"><use href="/static/icons.svg#i-NAME"/></svg>`. Es el patrón calcado de nudge (un único sprite, fragment-only refs, stroke con `currentColor`) adaptado al stack vanilla de este proyecto.

Plan: [docs/plans/design-system-migration.md](../plans/design-system-migration.md), sección 4.

**Dependencies**: None.

## Objective

Crear `src/static/icons.svg` con 17 `<symbol>` Lucide listos para ser referenciados por `<use>`. El fichero queda servido de forma estática por FastAPI (`StaticFiles`) sin tocar Python.

## Step 1 — Crear el fichero del sprite

Crear `src/static/icons.svg` con la siguiente envoltura:

```xml
<svg xmlns="http://www.w3.org/2000/svg" style="display:none" aria-hidden="true">
  <!-- Icons from Lucide — https://lucide.dev — ISC license -->
  <!-- One <symbol> per icon, viewBox 0 0 24 24, stroke=currentColor.
       Stroke-width / linecap / linejoin / fill se gestionan vía la clase
       global `.icon` definida en style.css. -->

  <!-- ... <symbol> blocks aquí ... -->
</svg>
```

## Step 2 — Añadir los 17 symbols

Cada `<symbol>` debe tener `id="i-<name>"` y `viewBox="0 0 24 24"`. Copiar los `<path>` / `<line>` / `<circle>` / `<polyline>` exactamente desde los SVG oficiales de Lucide (https://lucide.dev/icons/<name>). NO incluir el `<svg>` exterior dentro del symbol — solo los hijos.

| `id` | Nombre Lucide |
|---|---|
| `i-activity` | activity |
| `i-server` | server |
| `i-clock` | clock |
| `i-settings` | settings |
| `i-log-out` | log-out |
| `i-plus` | plus |
| `i-pencil` | pencil |
| `i-trash-2` | trash-2 |
| `i-refresh-cw` | refresh-cw |
| `i-globe` | globe |
| `i-x` | x |
| `i-chevron-left` | chevron-left |
| `i-chevron-right` | chevron-right |
| `i-check-circle` | check-circle |
| `i-x-circle` | x-circle |
| `i-alert-triangle` | alert-triangle |
| `i-external-link` | external-link |

Ejemplo de cómo queda un symbol (`i-plus`):

```xml
<symbol id="i-plus" viewBox="0 0 24 24">
  <path d="M5 12h14"/>
  <path d="M12 5v14"/>
</symbol>
```

NO añadir `stroke`, `stroke-width`, `fill`, etc. en cada `<path>` — esos atributos los gestiona la clase `.icon` desde CSS (T002), y el `<use>` los hereda.

## Step 3 — Verificación de integridad

Los símbolos deben renderizar sin distorsión a 14/16/20px. Verificar visualmente en navegador (a posteriori en T005), pero ya en esta task validar:

- El fichero parsea como XML válido.
- Los 17 IDs están presentes y son únicos.
- No hay paths con `fill="..."` ni `stroke="..."` hardcoded — todos heredan.

## DoD — Definition of Done

1. El fichero `src/static/icons.svg` existe.
2. Contiene exactamente 17 `<symbol>` con los IDs listados arriba.
3. Cada symbol tiene `viewBox="0 0 24 24"`.
4. Los paths se han copiado de Lucide (compararlos manualmente con la web oficial al menos en 3 iconos al azar).
5. El fichero parsea como XML válido (`xmllint --noout` o equivalente).
6. No hay atributos `stroke`/`fill` hardcoded en los hijos de los `<symbol>`.

## Evidence to produce

| # | Description | Command | File | PASS condition |
|---|-------------|---------|------|----------------|
| 1 | XML válido | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -c "import xml.etree.ElementTree as ET; ET.parse('static/icons.svg'); print('valid')"` | `xml_valid.txt` | imprime `valid` |
| 2 | Conteo de symbols | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev sh -c "grep -c '<symbol id=' static/icons.svg"` | `symbol_count.txt` | imprime `17` |
| 3 | IDs presentes | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev sh -c "grep -oE 'id=\"i-[a-z-]+\"' static/icons.svg \| sort"` | `symbol_ids.txt` | lista los 17 IDs esperados, sin duplicados |
| 4 | Sin stroke/fill hardcoded en hijos | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev sh -c "grep -E '(stroke=\|fill=)' static/icons.svg \| grep -v 'display:none' \|\| echo NO_HARDCODED"` | `no_hardcoded.txt` | imprime `NO_HARDCODED` |

## Files to create/modify

| File | Action |
|------|--------|
| `src/static/icons.svg` | CREATE |

## Execution evidence

**Date**: 2026-05-03
**Modified files**:
- `src/static/icons.svg` — CREATED. SVG sprite with 17 Lucide `<symbol>` elements (activity, server, clock, settings, log-out, plus, pencil, trash-2, refresh-cw, globe, x, chevron-left, chevron-right, check-circle, x-circle, alert-triangle, external-link). All symbols use `viewBox="0 0 24 24"`, no hardcoded stroke/fill — styling inherited from `.icon` class via `<use>`.

### Verification table

| # | Deliverable | Evidence file | Result |
|---|------------|---------------|--------|
| 1 | XML válido | `docs/tasks/evidence/T001/xml_valid.txt` | PASS — output: `valid` |
| 2 | 17 symbols | `docs/tasks/evidence/T001/symbol_count.txt` | PASS — output: `17` |
| 3 | 17 IDs únicos y correctos | `docs/tasks/evidence/T001/symbol_ids.txt` | PASS — los 17 IDs esperados, ordenados alfabéticamente, sin duplicados |
| 4 | Sin stroke/fill hardcoded | `docs/tasks/evidence/T001/no_hardcoded.txt` | PASS — output: `NO_HARDCODED` |
| 5 | viewBox uniforme `0 0 24 24` | `docs/tasks/evidence/T001/viewbox.txt` | PASS — output: `17` (un viewBox por symbol) |

### Design decisions

- **`docker compose exec` con service name (`ovh-dyndns-dev`) en lugar del container name (`ovh_dyndns_dev`)**. CLAUDE.md prescribe el container name (con underscores), pero la versión instalada de Docker Compose v2 acepta solo el service name. Las evidencias usan el service name. Posible mejora futura: alinear CLAUDE.md o renombrar el service para que coincidan.
- **Working directory `/app`**. El contenedor arranca con `WORKDIR /` por configuración de imagen, así que las rutas relativas no resuelven a la raíz del código. Las evidencias usan `--workdir /app`. Cualquier comando subsiguiente sobre estáticos debe usar la misma flag o rutas absolutas.
- **Paths copiados literalmente de Lucide v0.575+** (versión usada por nudge). Cada `<symbol>` contiene únicamente los hijos del SVG fuente (sin `<svg>` exterior, sin `stroke`/`fill` inline) — el styling viene 100% del CSS via `currentColor` y la clase `.icon`.
- **`fill-rule` no necesario** en estos 17 iconos. Lucide usa paths simples de stroke; no hay overlap ni cutouts complejos.
