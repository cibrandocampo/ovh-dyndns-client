# T003 — Diseñar logo "D", generar set de assets PWA y wirear `<head>`

## Context

El proyecto no tiene logo ni favicon. Esta task crea un logo **letra "D" geométrica** sobre fondo `#1a1a2e` con dot amarillo `#fcd34d`, calcando el lenguaje gráfico del logo de nudge (que usa "N"). Genera el set completo de derivados PWA (favicon, apple-touch, pwa-64/192/512, maskable, manifest) desde un único `source.svg` y conecta los `<link>` correspondientes en `<head>`.

Plan: [docs/plans/design-system-migration.md](../plans/design-system-migration.md), sección 5.

**Dependencies**: None. Independiente de T001 y T002 (no toca CSS ni el sprite Lucide).

## Objective

Producir el directorio `src/static/icons/` con `source.svg`, sus derivados PNG/ICO y un `manifest.json` mínimo. Cablear los `<link>` en `index.html`. Insertar el logo (24×24) en `.nav-brand`.

## Step 1 — Crear el directorio y el master SVG

Crear `src/static/icons/source.svg` con viewBox 512×512:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <!-- Background: dark rounded square (mismo que nudge) -->
  <rect width="512" height="512" rx="96" fill="#1a1a2e"/>

  <!-- Letter D: vertical bar (left) + bowl (right) constructed as a single closed path
       so background y bowl no se solapen.
       Geometría análoga a la N de nudge: trazo grueso, esquinas con rx=6. -->
  <path d="
    M 108 112
    H 240
    A 156 146 0 0 1 240 404
    H 108
    Z
    M 190 184
    H 240
    A 80 70 0 0 1 240 332
    H 190
    Z
  " fill="#e2e8f0" fill-rule="evenodd"/>

  <!-- Notification dot: dark halo + yellow circle (idéntico a nudge) -->
  <circle cx="394" cy="106" r="72" fill="#1a1a2e"/>
  <circle cx="394" cy="106" r="58" fill="#FCD34D"/>
</svg>
```

Notas de implementación:
- El `fill-rule="evenodd"` permite que el sub-path interno funcione como cutout del bowl.
- Los radios (156×146 outer, 80×70 inner) y el ancho del trazo (190-108=82) replican proporcionalmente el peso visual de la N de nudge — ajustar a ojo si la D queda demasiado fina o demasiado densa.
- Validar visualmente abriendo el `.svg` en navegador antes de generar derivados.

## Step 2 — Generar los derivados con `pwa-asset-generator`

El dev container es Python+Alpine y no trae Node. Usar un contenedor Node puntual:

```bash
docker run --rm \
  -v "$(pwd)/src/static/icons":/icons \
  -w /icons \
  node:22-alpine sh -c \
  "npx --yes @vite-pwa/assets-generator@latest --preset minimal source.svg"
```

El preset `minimal` de `@vite-pwa/assets-generator` produce:
- `favicon.ico`
- `apple-touch-icon-180x180.png`
- `pwa-64x64.png`
- `pwa-192x192.png`
- `pwa-512x512.png`
- `maskable-icon-512x512.png`

Si el preset no genera exactamente esa lista, ajustar opciones según la documentación de `@vite-pwa/assets-generator` (`--preset minimal` cubre los más comunes; ver https://vite-pwa-org.netlify.app/assets-generator/).

Verificar que los seis ficheros existen tras la ejecución y que su tamaño es razonable (<50KB cada PNG).

## Step 3 — Crear `manifest.json`

`src/static/icons/manifest.json`:

```json
{
  "name": "OVH DynDNS Client",
  "short_name": "OVH DynDNS",
  "description": "Self-hosted client for OVH DynHost. Updates DNS records when your IP changes.",
  "start_url": "/",
  "display": "standalone",
  "theme_color": "#454961",
  "background_color": "#fafafa",
  "icons": [
    { "src": "/static/icons/pwa-64x64.png", "sizes": "64x64", "type": "image/png" },
    { "src": "/static/icons/pwa-192x192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/static/icons/pwa-512x512.png", "sizes": "512x512", "type": "image/png" },
    { "src": "/static/icons/maskable-icon-512x512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ]
}
```

## Step 4 — Conectar los `<link>` en `index.html`

En el `<head>` de `src/static/index.html`, después del `<title>` y antes del `<link rel="stylesheet">`, añadir:

```html
<link rel="icon" href="/static/icons/favicon.ico" sizes="any" />
<link rel="icon" type="image/svg+xml" href="/static/icons/source.svg" />
<link rel="apple-touch-icon" href="/static/icons/apple-touch-icon-180x180.png" />
<link rel="manifest" href="/static/icons/manifest.json" />
<meta name="theme-color" content="#454961" />
```

## Step 5 — Insertar el logo en `.nav-brand`

En el div `<div class="nav-brand">OVH DynDNS Client</div>` (dentro del `<nav class="navbar">`), prepender el `<img>`:

```html
<div class="nav-brand">
  <img src="/static/icons/source.svg" alt="" class="brand-logo" />
  OVH DynDNS Client
</div>
```

`alt=""` porque es decorativo — el texto adyacente ya nombra la app.

NOTA: la clase `.brand-logo` se define en T002 (`style.css`). Si T002 aún no se ha ejecutado al correr esta task, el logo se mostrará a tamaño nativo del SVG (proporcional, no roto). Para `/dev-3-run`, ejecutar T002 antes de T003 si se quiere previsualizar correctamente, pero no es bloqueante.

## DoD — Definition of Done

1. Existe `src/static/icons/source.svg` con la D geométrica + dot amarillo.
2. Existen los 6 derivados PNG/ICO en `src/static/icons/`.
3. Existe `src/static/icons/manifest.json` válido como JSON.
4. El `<head>` de `index.html` tiene los 4 `<link>` (favicon ico, favicon svg, apple-touch, manifest) y el `<meta name="theme-color">`.
5. `.nav-brand` contiene un `<img class="brand-logo">` que apunta a `source.svg`.
6. Los nuevos ficheros se commitean (no en `.gitignore`).

## Evidence to produce

| # | Description | Command | File | PASS condition |
|---|-------------|---------|------|----------------|
| 1 | source.svg presente y SVG válido | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -c "import xml.etree.ElementTree as ET; r=ET.parse('static/icons/source.svg').getroot(); print('valid' if 'svg' in r.tag else 'invalid')"` | `source_svg_valid.txt` | imprime `valid` |
| 2 | Derivados generados | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev sh -c "ls static/icons/"` | `icons_dir.txt` | lista al menos: `apple-touch-icon-180x180.png`, `favicon.ico`, `manifest.json`, `maskable-icon-512x512.png`, `pwa-192x192.png`, `pwa-512x512.png`, `pwa-64x64.png`, `source.svg` |
| 3 | manifest.json válido | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -c "import json; m=json.load(open('static/icons/manifest.json')); assert m['theme_color']=='#454961'; assert len(m['icons'])>=4; print('ok')"` | `manifest_valid.txt` | imprime `ok` |
| 4 | Links en `<head>` | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev sh -c "grep -E '(rel=\"icon\"\|rel=\"apple-touch\"\|rel=\"manifest\"\|theme-color)' static/index.html \| wc -l"` | `head_links.txt` | número >= 5 |
| 5 | Logo embebido en navbar | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev sh -c "grep 'brand-logo' static/index.html"` | `nav_logo.txt` | match con `<img.*brand-logo.*source.svg>` |
| 6 | Servir el favicon vía API | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev sh -c "curl -sf -o /dev/null -w '%{http_code}' http://localhost:8000/static/icons/favicon.ico"` | `favicon_serve.txt` | imprime `200` (requiere app levantada — verificación blanda; si la app no está levantada en este momento, marcar como diferido a T005) |

## Files to create/modify

| File | Action |
|------|--------|
| `src/static/icons/source.svg` | CREATE |
| `src/static/icons/favicon.ico` | CREATE (generado) |
| `src/static/icons/apple-touch-icon-180x180.png` | CREATE (generado) |
| `src/static/icons/pwa-64x64.png` | CREATE (generado) |
| `src/static/icons/pwa-192x192.png` | CREATE (generado) |
| `src/static/icons/pwa-512x512.png` | CREATE (generado) |
| `src/static/icons/maskable-icon-512x512.png` | CREATE (generado) |
| `src/static/icons/manifest.json` | CREATE |
| `src/static/index.html` | MODIFY (añade `<link>` en `<head>` y `<img>` en `.nav-brand`) |

## Execution evidence

**Date**: 2026-05-03
**Modified files**:
- `src/static/icons/source.svg` — CREATED. Master logo SVG (viewBox 512×512). Dark rounded square `#1a1a2e` (rx=96) + geometric "D" in `#e2e8f0` built as a single `<path>` with `fill-rule="evenodd"` (outer bowl + inner cutout). Yellow notification dot `#FCD34D` (r=58) with dark halo (r=72). Mirrors nudge's logo grammar with the letter swapped.
- `src/static/icons/favicon.ico`, `apple-touch-icon-180x180.png`, `pwa-64x64.png`, `pwa-192x192.png`, `pwa-512x512.png`, `maskable-icon-512x512.png` — CREATED. Generated from `source.svg` with `@vite-pwa/assets-generator@latest --preset minimal` running in a one-shot `node:22-alpine` container. All under 4KB.
- `src/static/icons/manifest.json` — CREATED. Web app manifest with `name`, `short_name`, `start_url`, `display: standalone`, `theme_color: #454961`, `background_color: #fafafa`, and the four PWA icons (64/192/512 + maskable). Absolute paths `/static/icons/...` so it works regardless of where the page is requested from.
- `src/static/index.html` — MODIFIED. Five `<link>` / `<meta>` entries added in `<head>` between `<title>` and the stylesheet (favicon ico + svg, apple-touch-icon, manifest, theme-color). `.nav-brand` extended with an inline 24×24 `<img class="brand-logo">` pointing to `source.svg`.

### Verification table

| # | Deliverable | Evidence file | Result |
|---|------------|---------------|--------|
| 1 | source.svg parses as valid SVG | `docs/tasks/evidence/T003/source_svg_valid.txt` | PASS — `valid` |
| 2 | All 8 assets present in `static/icons/` | `docs/tasks/evidence/T003/icons_dir.txt` | PASS — apple-touch + favicon.ico + manifest + maskable + 3 pwa sizes + source.svg |
| 3 | manifest.json valid + theme_color + 4 icons | `docs/tasks/evidence/T003/manifest_valid.txt` | PASS — `ok` |
| 4 | 5 head links/meta entries | `docs/tasks/evidence/T003/head_links.txt` | PASS — `5` |
| 5 | Logo embedded in `.nav-brand` | `docs/tasks/evidence/T003/nav_logo.txt` | PASS — `<img src="/static/icons/source.svg" alt="" class="brand-logo" />` |
| 6 | Favicon served by FastAPI (200) | `docs/tasks/evidence/T003/favicon_serve.txt` | PASS — `200` |
| 7 | source.svg, manifest.json, apple-touch, pwa-192 served (200) | `docs/tasks/evidence/T003/static_assets_serve.txt` | PASS — all 4 return `200` |
| 8 | Backend tests still green (regression guard) | `docs/tasks/evidence/T003/backend_tests.txt` | PASS — `179 passed` |

### Design decisions

- **Generator chosen**: `@vite-pwa/assets-generator@latest --preset minimal`. This is the package nudge uses (`pwa-assets-generator` is the deprecated alias). The `minimal` preset emits exactly the six derivatives the task expects (favicon.ico, apple-touch-icon-180x180.png, pwa-64/192/512, maskable-icon-512x512). Run via one-shot `node:22-alpine` since the dev container is Python+Alpine.
- **Path syntax in source.svg**: collapsed the multi-line `<path d="...">` from the task spec into a single line. Browsers and the SVG parser handle both equally; single line keeps the file marginally smaller and avoids whitespace quirks if any tool re-parses it.
- **`alt=""`** on the `<img>`: deliberate — the logo is decorative, the adjacent text "OVH DynDNS Client" already names the app for screen readers (avoids redundant announcement).
- **Absolute icon paths in manifest** (`/static/icons/...`) instead of relative. Reason: the manifest is fetched with the page URL as base; relative paths can break if the page is served from a non-root path or behind a path-rewriting reverse proxy. Absolute paths under `/static/` align with how FastAPI mounts `StaticFiles`.
- **Health-check loop in Python** (not `curl`) to verify the running app: the dev container ships with `wget` (busybox) but not `curl`. Used `urllib.request` for portability.
- **App stopped after evidence #6**: the dev compose defines `command: tail -f /dev/null`, so `python main.py` was launched in detached mode purely to verify static serving, then killed. Container left in its original keep-alive state.
