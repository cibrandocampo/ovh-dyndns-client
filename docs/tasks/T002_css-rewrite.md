# T002 — Reescribir style.css con paleta nudge, tipografía y clases helper

## Context

El `style.css` actual usa una paleta Tailwind genérica (`#2563eb` blue + slate neutrals) que no coincide con ningún token de nudge. Esta task reescribe el bloque `:root`, adapta todas las clases existentes a las nuevas variables, y añade las clases helper que el resto de tasks consumirán: `.icon` (T001/T004), `.brand-logo` (T003), `.link-external` y `.card-ip` (futuro).

El alcance es **solo CSS**: las clases públicas no se renombran, así que `index.html` y `app.js` siguen funcionando sin cambios mientras esta task está en vuelo.

Plan: [docs/plans/design-system-migration.md](../plans/design-system-migration.md), secciones 1-3 y 7.

**Dependencies**: None. Independiente de T001.

## Objective

Sustituir la paleta y tipografía actuales de `src/static/css/style.css` por las equivalentes de nudge (mismos hex, mismos nombres `--c-*`), adaptar las clases existentes a las nuevas variables, y añadir las clases helper necesarias.

## Step 1 — Reescribir el bloque `:root`

Reemplazar **todo el bloque `:root`** actual por la paleta de nudge idéntica + tokens de shape:

```css
:root {
  /* Brand */
  --c-brand: #fcd34d;
  --c-brand-text: #78350f;

  /* Neutral / primary slate */
  --c-primary: #454961;
  --c-primary-hover: #5a5f7d;
  --c-bg: #fafafa;
  --c-surface: #ffffff;
  --c-ink: #0a0a0a;
  --c-text: #454961;
  --c-text-2: #6c7188;
  --c-text-3: #a1a1aa;
  --c-muted: #d4d4d8;
  --c-border: #e4e4e7;
  --c-border-inner: #f4f4f5;
  --c-ring: rgba(69, 73, 97, 0.18);

  /* Status */
  --c-success: #22c55e;
  --c-warning: #ca8a04;
  --c-danger: #ef4444;

  /* Accent (indigo) — enlaces externos a OVH */
  --c-shared: #4a56a1;
  --c-shared-light: #c5c9e3;

  /* Delete */
  --c-delete: #fca5a5;
  --c-delete-hover: #f87171;

  /* Shape */
  --radius-sm: 4px;
  --radius: 6px;
  --radius-lg: 8px;
  --radius-xl: 10px;
  --radius-xxl: 12px;
  --shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.2);
  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.1);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.08);
  --shadow-lg: 0 20px 60px rgba(0, 0, 0, 0.15);
  --shadow-focus: 0 0 0 2px var(--c-ring);
  --transition: 150ms ease;
}
```

Eliminar variables obsoletas (`--primary-color`, `--primary-hover`, `--danger-color`, `--danger-hover`, `--success-color`, `--warning-color`, `--bg-color`, `--card-bg`, `--text-color`, `--text-muted`, `--border-color`, `--shadow`, `--shadow-lg`).

## Step 2 — Aplicar `body` y reset

```css
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background-color: var(--c-bg);
  color: var(--c-text);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}
```

## Step 3 — Adaptar todas las clases existentes a las nuevas variables

Recorrer las clases del fichero actual y sustituir referencias a las variables viejas por las nuevas. Mapping:

| Variable vieja | Variable nueva |
|---|---|
| `--primary-color` | `var(--c-primary)` |
| `--primary-hover` | `var(--c-primary-hover)` |
| `--danger-color` | `var(--c-danger)` |
| `--danger-hover` | `var(--c-delete-hover)` |
| `--success-color` | `var(--c-success)` |
| `--warning-color` | `var(--c-warning)` |
| `--bg-color` | `var(--c-bg)` |
| `--card-bg` | `var(--c-surface)` |
| `--text-color` | `var(--c-text)` |
| `--text-muted` | `var(--c-text-3)` (en navbar y small text) o `var(--c-text-2)` (en card titles) — usar criterio según jerarquía |
| `--border-color` | `var(--c-border)` |
| `--shadow` | `var(--shadow-sm)` |
| `--shadow-lg` | `var(--shadow-lg)` |

Además, ajustar pesos y tamaños hacia la convención de nudge:

- `font-weight: 600` en lugar de 500 para títulos secundarios y nav-brand.
- Botones primarios: padding `0.6rem 1.2rem`, `border-radius: var(--radius-lg)`, `font-size: 0.875rem`, `font-weight: 500`.
- `.card` con `border-radius: var(--radius-lg)`, sombra `var(--shadow-sm)`, padding `1.5rem`.
- `.table` con `font-size: 0.875rem`, `font-variant-numeric: tabular-nums` (números alineados en columnas).
- `.table th` con `font-weight: 600`, `letter-spacing: 0.08em`, `font-size: 0.7rem`, `text-transform: uppercase`, color `var(--c-ink)`.
- `.nav-brand` con `font-weight: 700`, `font-size: 1rem`, color `var(--c-primary)`.
- `.btn` con `border-radius: var(--radius)`, `transition: all var(--transition)`.
- `.modal-content` con `border-radius: var(--radius-xxl)`, `box-shadow: var(--shadow-lg)`.
- Inputs con `border-radius: var(--radius)`, focus con `box-shadow: var(--shadow-focus)`.

`.message.success`, `.message.error`, `.message.info`: ajustar fondos a `rgba(34,197,94,0.08)` / `rgba(239,68,68,0.08)` / `rgba(74,86,161,0.08)` con borde `1px solid` del color correspondiente, en línea con la estética de nudge (transparencia suave en vez de pasteles sólidos).

`.status-success`, `.status-error`, `.status-pending`: mantener clases, recalibrar a `var(--c-success/danger/warning)`.

`.btn-icon`: pasar a 32×32 con `background: var(--c-border-inner)`, hover `var(--c-border)`, color `var(--c-text-3)`.

## Step 4 — Añadir clases helper nuevas

Al final del fichero, añadir:

```css
/* ── Icon base (consumido por <use href="/static/icons.svg#i-X">) ── */
.icon {
  width: 16px;
  height: 16px;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
  fill: none;
  flex-shrink: 0;
  display: inline-block;
  vertical-align: middle;
}
.icon-sm { width: 14px; height: 14px; }
.icon-lg { width: 20px; height: 20px; }

/* ── Brand logo en navbar (T003) ── */
.brand-logo {
  width: 24px;
  height: 24px;
  vertical-align: middle;
  margin-right: 0.5rem;
}
.nav-brand {
  display: inline-flex;
  align-items: center;
}

/* ── Card destacada de IP actual ── */
.card-ip {
  border-left: 3px solid var(--c-brand);
}

/* ── Enlace externo (token indigo, listo para futuros enlaces a OVH) ── */
.link-external {
  color: var(--c-shared);
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
}
.link-external:hover {
  text-decoration: underline;
}
```

## Step 5 — Verificar que no quedan referencias a variables viejas

Después de la reescritura, no debe quedar ningún `var(--primary-color)`, `var(--bg-color)`, etc. en el fichero.

## DoD — Definition of Done

1. El bloque `:root` contiene exactamente los tokens de nudge listados (sin variables obsoletas).
2. `body` usa el font stack system de nudge.
3. Todas las referencias a las variables viejas (`--primary-color`, `--bg-color`, etc.) se han migrado a sus equivalentes `--c-*`.
4. Las clases helper `.icon`, `.icon-sm`, `.icon-lg`, `.brand-logo`, `.nav-brand` (extendida), `.card-ip`, `.link-external` están añadidas al final del fichero.
5. El media query `@media (max-width: 768px)` del final se conserva intacto.
6. La página renderiza sin errores en navegador (verificación manual en T005, no en esta task).

## Evidence to produce

| # | Description | Command | File | PASS condition |
|---|-------------|---------|------|----------------|
| 1 | Sin variables viejas | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev sh -c "grep -E 'var\\(--(primary-color\|bg-color\|card-bg\|text-color\|text-muted\|border-color\|danger-color\|success-color\|warning-color\|primary-hover\|danger-hover)\\)' static/css/style.css \|\| echo CLEAN"` | `legacy_vars.txt` | imprime `CLEAN` |
| 2 | Tokens nudge presentes | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev sh -c "grep -cE '\\-\\-c-(brand\|primary\|bg\|surface\|ink\|text\|text-2\|text-3\|muted\|border\|border-inner\|ring\|success\|warning\|danger\|shared\|shared-light\|delete\|delete-hover\|brand-text)' static/css/style.css"` | `nudge_tokens.txt` | número >= 21 (los 21 tokens listados, al menos una declaración cada uno) |
| 3 | Clases helper añadidas | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev sh -c "grep -cE '^\\.(icon\|icon-sm\|icon-lg\|brand-logo\|card-ip\|link-external) ' static/css/style.css"` | `helper_classes.txt` | número >= 6 |
| 4 | Font stack system | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev sh -c "grep -A1 'body {' static/css/style.css \| grep -E 'apple-system'"` | `font_stack.txt` | match no vacío |

## Files to create/modify

| File | Action |
|------|--------|
| `src/static/css/style.css` | MODIFY (reescritura mayor) |

## Execution evidence

**Date**: 2026-05-03
**Modified files**:
- `src/static/css/style.css` — REWRITTEN. New `:root` block with the nudge palette (21 `--c-*` tokens + shape/shadow tokens). System font stack on `body`. All existing classes (`.btn`, `.card`, `.table`, `.modal-content`, `.nav-link`, `.form-group`, etc.) migrated to consume the new variables and adopt nudge typographic conventions (font-weight 500/600/700, sizes 0.7–1.25rem, tabular-nums on numeric tables). Helper classes appended: `.icon`, `.icon-sm`, `.icon-lg`, `.brand-logo`, `.card-ip`, `.link-external`. `.nav-brand` extended with `display: inline-flex; align-items: center;` to host the future logo. Mobile media query preserved verbatim. Status messages (`.message.success/error/info`) recalibrated to soft transparent backgrounds (rgba 0.08) with thin colored borders, matching nudge's visual register. `.btn-icon` reshaped to 32×32 with `--c-border-inner` background.

### Verification table

| # | Deliverable | Evidence file | Result |
|---|------------|---------------|--------|
| 1 | No legacy variables (`--primary-color`, `--bg-color`, etc.) | `docs/tasks/evidence/T002/legacy_vars.txt` | PASS — output: `CLEAN` |
| 2 | Nudge tokens (`--c-*`) present | `docs/tasks/evidence/T002/nudge_tokens.txt` | PASS — output: `86` (≥ 21 required) |
| 3 | Helper classes appended (`.icon`, `.icon-sm`, `.icon-lg`, `.brand-logo`, `.card-ip`, `.link-external`) | `docs/tasks/evidence/T002/helper_classes.txt` | PASS — output: `6` |
| 4 | Body uses system font stack | `docs/tasks/evidence/T002/font_stack.txt` | PASS — match on `-apple-system, BlinkMacSystemFont, ...` |
| 5 | `@media (max-width: 768px)` preserved | `docs/tasks/evidence/T002/media_query.txt` | PASS — match present |
| 6 | Braces balanced (CSS structurally well-formed) | `docs/tasks/evidence/T002/braces_balance.txt` | PASS — `open=71 close=71`, `BALANCED` |
| 7 | Backend tests still green (regression guard) | `docs/tasks/evidence/T002/backend_tests.txt` | PASS — `179 passed` |
| 8 | Lint clean (regression guard) | `docs/tasks/evidence/T002/ruff_check.txt` | PASS — `All checks passed!` |

### Design decisions

- **Variable mapping for `--text-muted`**: applied `--c-text-3` (lighter neutral) for tertiary copy (form `<small>`, `#page-info`, `.close-modal`) and `--c-text-2` for `.card h3` titles inside status cards (where slightly more contrast is wanted). Matches nudge's hierarchy (`text` > `text-2` > `text-3`).
- **`.section h3`** added explicitly. The original CSS only styled `.section h2`, leaving the inline `<h3>Host Status</h3>` in `index.html` (status section) un-themed. New rule gives it uppercase + letter-spacing per nudge convention.
- **`.btn-primary` and `.btn-danger` border-color** set to match background. Nudge's primary buttons in `shared.module.css` use the same trick (`border: 1px solid transparent` then `border-color: var(--c-primary)` on `.btnPrimary`). Keeps box-sizing consistent with `.btn-secondary`-style buttons (which carry a visible border).
- **`.message.info`** mapped to indigo (`--c-shared`) instead of slate-primary. Reason: keeps "informational" visually distinct from "primary action" — nudge uses indigo-shared for its informational/share family, which is the nearest semantic match here.
- **`.btn-icon` background** set to `--c-border-inner` (instead of transparent). Matches nudge's `.btnIcon` and gives the button an obvious tap target on cards/modals where it sits next to text.
- **`-webkit-font-smoothing: antialiased`** kept under `body` (matches nudge). No need for an explicit Firefox equivalent — modern Firefox renders well by default.
