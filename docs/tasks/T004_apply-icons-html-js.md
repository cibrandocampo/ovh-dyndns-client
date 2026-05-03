# T004 — Insertar iconos Lucide en `index.html` y `app.js`

## Context

Con el sprite ya construido (T001) y el CSS ya con la clase `.icon` y la nueva paleta (T002), esta task aplica los iconos en los puntos del UI definidos por el plan: nav, botones primarios, modales, paginación, card de IP, info-text de cambio de password y celdas dinámicas de tablas.

Plan: [docs/plans/design-system-migration.md](../plans/design-system-migration.md), secciones 6 y 7.

**Dependencies**: T001 (sprite existe en `/static/icons.svg`), T002 (clase `.icon` definida).

## Objective

Que cada punto del UI listado en el plan tenga su icono Lucide correspondiente, sin tocar la lógica de la app. La estructura HTML y los selectores existentes se mantienen.

## Step 1 — Iconos en el navbar

En `src/static/index.html`, dentro de `<div class="nav-links">`, prepender un `<svg>` a cada link:

| Link | Icono |
|---|---|
| `data-section="status"` | `i-activity` |
| `data-section="hosts"` | `i-server` |
| `data-section="history"` | `i-clock` |
| `data-section="settings"` | `i-settings` |
| `id="logout-link"` | `i-log-out` |

Patrón:

```html
<a href="#" data-section="status" class="nav-link active">
  <svg class="icon icon-sm"><use href="/static/icons.svg#i-activity"/></svg>
  Status
</a>
```

Mantener `class="nav-link active"` y demás atributos.

## Step 2 — Iconos en botones primarios y card de IP

| Elemento | Icono | Notas |
|---|---|---|
| `#trigger-update` (botón "Trigger Update Now") | `i-refresh-cw` | Prepender |
| `#add-host-btn` (botón "Add Host") | `i-plus` | Prepender |
| Card "Current IP" `<div class="card">` | `i-globe` | Prepender al `<h3>Current IP</h3>` con `class="icon icon-sm"`. Añadir además `class="card card-ip"` al div para activar el border-left amarillo (T002). |
| `<p class="info-text">` de change-password page | `i-alert-triangle` | Prepender con `class="icon icon-sm"` |
| Modal close (`.close-modal`) | `i-x` | Reemplazar el contenido `&times;` por `<svg class="icon"><use href="/static/icons.svg#i-x"/></svg>` |

Ejemplo card-ip:

```html
<div class="card card-ip">
  <h3><svg class="icon icon-sm"><use href="/static/icons.svg#i-globe"/></svg> Current IP</h3>
  <p id="current-ip" class="big-text">-</p>
</div>
```

## Step 3 — Iconos en pagination

En la sección history, sustituir texto por iconos + texto en los botones de paginación:

```html
<button id="prev-page" class="btn" disabled>
  <svg class="icon icon-sm"><use href="/static/icons.svg#i-chevron-left"/></svg>
  Previous
</button>
<span id="page-info">Page 1</span>
<button id="next-page" class="btn">
  Next
  <svg class="icon icon-sm"><use href="/static/icons.svg#i-chevron-right"/></svg>
</button>
```

## Step 4 — Iconos en celdas dinámicas de tabla (`app.js`)

Modificar tres funciones de render. El patrón general: en los botones de Actions, sustituir el texto por un `<svg>`. Mantener la clase de cada botón (`btn-danger`, etc.) intacta porque los E2E y los listeners dependen de ellas.

### `loadStatus()` — botón "Force Update" (línea ~226)

Antes:
```js
<button class="btn btn-small btn-primary" onclick="forceUpdateHost('${escapeHtml(host.hostname)}')">Force Update</button>
```

Después:
```js
<button class="btn btn-small btn-primary" onclick="forceUpdateHost('${escapeHtml(host.hostname)}')" aria-label="Force update">
  <svg class="icon icon-sm"><use href="/static/icons.svg#i-refresh-cw"/></svg>
</button>
```

Además, en la columna `Status`: reemplazar las strings literales `Success`/`Failed`/`Pending` por icono + texto:

```js
<td class="${host.last_status === true ? 'status-success' : host.last_status === false ? 'status-error' : 'status-pending'}">
  <svg class="icon icon-sm"><use href="/static/icons.svg#${host.last_status === true ? 'i-check-circle' : host.last_status === false ? 'i-x-circle' : 'i-clock'}"/></svg>
  ${host.last_status === true ? 'Success' : host.last_status === false ? 'Failed' : 'Pending'}
</td>
```

Ajustar también la función `forceUpdateHost(hostname)` (línea ~235): ya no debe sustituir `btn.textContent = 'Updating...'` (rompería el icono). Cambiar el feedback "loading" a:

```js
btn.disabled = true;
btn.dataset.loading = 'true';  // marca para CSS opcional o lectura por test
// ... mantener el restablecimiento en finally
btn.dataset.loading = 'false';
btn.disabled = false;
```

Eliminar el manejo de `originalText` y `btn.textContent`.

### `loadHosts()` — botones "Edit" y "Delete" (línea ~291)

Antes:
```js
<button class="btn btn-small" onclick="editHost(${host.id})">Edit</button>
<button class="btn btn-small btn-danger" onclick="confirmDeleteHost(${host.id}, '${escapeHtml(host.hostname)}')">Delete</button>
```

Después:
```js
<button class="btn btn-small" onclick="editHost(${host.id})" aria-label="Edit host">
  <svg class="icon icon-sm"><use href="/static/icons.svg#i-pencil"/></svg>
</button>
<button class="btn btn-small btn-danger" onclick="confirmDeleteHost(${host.id}, '${escapeHtml(host.hostname)}')" aria-label="Delete host">
  <svg class="icon icon-sm"><use href="/static/icons.svg#i-trash-2"/></svg>
</button>
```

Mantener `btn-danger` y la clase `btn` para que los selectores E2E (`#hosts-table tbody tr` + `.btn-danger`) sigan funcionando.

### `loadHistory()` — sin cambios obligatorios

Las celdas de history son texto puro y no tienen botones de acción. Si se quiere, dejar tal cual.

### Manejador de `#trigger-update` (línea ~260)

Igual que `forceUpdateHost`: NO sustituir `btn.textContent` con string en disabled state. El botón mantiene icono + texto siempre. Cambiar el patrón a:

```js
btn.disabled = true;
btn.dataset.loading = 'true';
// ... operación ...
btn.disabled = false;
btn.dataset.loading = 'false';
```

Eliminar `btn.textContent = 'Updating...'` y la restauración a `'Trigger Update Now'`.

## Step 5 — Verificar que `app.js` no rompe el contrato visible

- Las clases que usan los E2E (`btn-danger`, IDs como `#hosts-table tbody tr`) siguen presentes en el HTML generado.
- Los `onclick="..."` siguen apuntando a las mismas funciones.
- No se introducen nuevos event listeners.

## DoD — Definition of Done

1. Los 5 nav-links tienen su `<svg>` correspondiente con el icono listado.
2. `#trigger-update` y `#add-host-btn` tienen icono prepended.
3. Card "Current IP" lleva `class="card card-ip"` y un `<svg>` con `i-globe` en el `<h3>`.
4. La info-text de change-password lleva `<svg>` con `i-alert-triangle`.
5. Cada `.close-modal` muestra `<svg>` con `i-x` en lugar de `&times;`.
6. Botones de paginación llevan chevrons.
7. `loadStatus()` renderiza la columna Status con icono + texto y el botón de Force Update con `i-refresh-cw`.
8. `loadHosts()` renderiza los botones Edit/Delete como icon-only con `aria-label`.
9. `forceUpdateHost()` y el handler de `#trigger-update` ya no sustituyen `textContent` con strings — usan `dataset.loading` o equivalente para el estado disabled.
10. Los selectores existentes para tests (`#hosts-table tbody tr` + `.btn-danger`, `#confirm-delete`, `#delete-modal`, `#host-modal`) siguen funcionando: el HTML generado los incluye intactos.

## Evidence to produce

| # | Description | Command | File | PASS condition |
|---|-------------|---------|------|----------------|
| 1 | Iconos en nav (5 links) | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev sh -c "grep -cE 'href=\"/static/icons.svg#i-(activity\|server\|clock\|settings\|log-out)\"' static/index.html"` | `nav_icons.txt` | número >= 5 |
| 2 | `card-ip` aplicado | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev sh -c "grep 'class=\"card card-ip\"' static/index.html"` | `card_ip.txt` | match no vacío |
| 3 | Modal close usa `i-x` | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev sh -c "grep -A1 'close-modal' static/index.html \| grep 'i-x'"` | `modal_close.txt` | match no vacío |
| 4 | Iconos en `app.js` (tablas dinámicas) | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev sh -c "grep -cE '/static/icons.svg#i-(refresh-cw\|pencil\|trash-2\|check-circle\|x-circle\|clock)' static/js/app.js"` | `js_icons.txt` | número >= 6 |
| 5 | E2E selectors intactos en JS render | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev sh -c "grep -cE 'class=\"btn btn-small btn-danger\"' static/js/app.js"` | `e2e_selectors.txt` | número >= 1 |
| 6 | textContent loading patch | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev sh -c "grep -E 'Updating\\.\\.\\.' static/js/app.js \|\| echo CLEAN"` | `loading_patch.txt` | imprime `CLEAN` |

## Files to create/modify

| File | Action |
|------|--------|
| `src/static/index.html` | MODIFY |
| `src/static/js/app.js` | MODIFY |

## Execution evidence

**Date**: 2026-05-03
**Modified files**:
- `src/static/index.html` — MODIFIED. Five nav links extended with their `i-activity` / `i-server` / `i-clock` / `i-settings` / `i-log-out` icons. `#trigger-update` button now leads with `i-refresh-cw`; `#add-host-btn` with `i-plus`. Card "Current IP" gained `class="card card-ip"` (yellow border-left from T002) and an `i-globe` glyph in its `<h3>`. Change-password info-text gained `i-alert-triangle`. `.close-modal` shows an `i-x` icon instead of `&times;`. Pagination buttons gained `i-chevron-left` / `i-chevron-right`.
- `src/static/js/app.js` — MODIFIED. `loadStatus()` Status column renders an icon (`i-check-circle` / `i-x-circle` / `i-clock` chosen by ternary on `host.last_status`) before the textual state. Force Update button reduced to icon-only with `aria-label="Force update"`. `loadHosts()` Edit/Delete buttons reduced to icon-only with `i-pencil` / `i-trash-2` and `aria-label`s; classes `btn`, `btn-small`, `btn-danger` preserved verbatim so E2E selectors (`#hosts-table tbody tr` + `.btn-danger`) keep working. `forceUpdateHost()` and the `#trigger-update` click handler no longer mutate `textContent` to "Updating..." — they toggle `dataset.loading` and `disabled` instead, so the icon survives the loading state. `event.target.closest('button')` ensures we land on the button regardless of whether the user clicked the SVG, the `<use>`, or the button frame.

### Verification table

| # | Deliverable | Evidence file | Result |
|---|------------|---------------|--------|
| 1 | Nav has 5 Lucide refs | `docs/tasks/evidence/T004/nav_icons.txt` | PASS — `5` |
| 2 | `card-ip` applied | `docs/tasks/evidence/T004/card_ip.txt` | PASS — `<div class="card card-ip">` |
| 3 | Modal close uses `i-x` | `docs/tasks/evidence/T004/modal_close.txt` | PASS — `<svg class="icon"><use href="/static/icons.svg#i-x"/></svg>` |
| 4 | JS literal URL refs (refresh-cw / pencil / trash-2 plus the ternary status icons) | `docs/tasks/evidence/T004/js_icons.txt` | LITERAL `3` (only direct refs match — see note); intent verified by #4b |
| 4b | All 6 icon names referenced in `app.js` (unique) | `docs/tasks/evidence/T004/js_icons_unique.txt` | PASS — `i-check-circle, i-clock, i-pencil, i-refresh-cw, i-trash-2, i-x-circle` |
| 5 | `class="btn btn-small btn-danger"` preserved (E2E selector) | `docs/tasks/evidence/T004/e2e_selectors.txt` | PASS — `1` |
| 6 | No `Updating...` `textContent` mutation left | `docs/tasks/evidence/T004/loading_patch.txt` | PASS — `CLEAN` |
| 7 | HTML action icons (refresh-cw, plus, globe, alert-triangle, chevrons) | `docs/tasks/evidence/T004/html_action_icons.txt` | PASS — `6` |
| 8 | Backend tests still green (regression guard) | `docs/tasks/evidence/T004/backend_tests.txt` | PASS — `179 passed` |
| 9 | Ruff clean (regression guard) | `docs/tasks/evidence/T004/ruff_check.txt` | PASS — `All checks passed!` |

### Design decisions

- **`event.target.closest('button')`** in `forceUpdateHost`. The button now contains an `<svg>` and a `<use>` element; depending on where the user clicks, `event.target` may be the SVG/use/path child rather than the button itself. `closest('button')` always returns the button. The previous code (`event.target` directly) silently broke as soon as we put any child element inside the button.
- **`dataset.loading`** instead of disabled-only. The SVG icon stays visible during async operations, and CSS or future tests can read `[data-loading="true"]` for visual feedback (spinner overlay, opacity, etc.) without code changes here. Avoids the textContent reassignment trap that would have wiped the icon.
- **Ternary inside the `#${...}` URL fragment** for the Status column icon. Three rendering branches (success/failed/pending) collapsed to one template literal. Trade-off: makes the literal-URL grep evidence (#4) under-count — only the 3 direct icon refs hit, the other 3 are computed at runtime. Recorded a complementary evidence (#4b) that proves all 6 icon names are referenced.
- **`aria-label`** added to every icon-only button (`Edit host`, `Delete host`, `Force update`). Without text, screen readers would announce the button by its accessible name, which falls back to the SVG content otherwise.
- **`alt=""`** semantics carried over to the modal close: used `aria-label="Close"` on the `<span>` since `<span>` has no `alt`, but the icon itself remains presentational (`aria-hidden` is implicit for `<use>` references inside an unlabeled SVG without role).
- **History pagination icons** chose chevron + label format (`◀ Previous` / `Next ▶`) over icon-only. Reason: pagination buttons are wide already and the textual "Previous"/"Next" gives keyboard users a faster scan target; the chevron just reinforces direction.
