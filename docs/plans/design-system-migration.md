# Design System Migration — Adoptar paleta, tipografía e iconos de nudge

## Context

La interfaz web actual de ovh-dyndns-client (`src/static/`) usa una paleta Tailwind genérica (`#2563eb` blue + slate neutrals) y tipografía system stack, sin iconos. Es funcional pero no comparte identidad visual con el resto del ecosistema personal del usuario, en concreto con [nudge](/Users/cibran.docampo/Workspace/test/nudge), donde ya existe un sistema de diseño maduro y consistente: paleta slate-blue + indigo + amarillo brand, tipografía system stack, iconos Lucide vía sprite SVG.

El objetivo es **alinear esta UI con la de nudge** sin reestructurar el HTML ni las clases. Solo paleta, tipografía e iconos. La estructura (tablas, modales, navbar horizontal) se mantiene.

Esto baja la fricción cognitiva al saltar entre proyectos del usuario y deja la base lista para futuras evoluciones (re-skin completo, cards-style, etc.) sin recablear nada hoy.

---

## Decisions confirmed with user

| Topic | Decision |
|-------|----------|
| Alcance | **Paleta, tipografía, iconos y logo/favicon.** HTML y nombres de clase no cambian. Tablas se mantienen, modales se mantienen, navbar horizontal se mantiene. |
| Rol semántico de colores | Slate `#454961` = principal (nav, botones primarios, texto). Indigo `#4a56a1` = enlaces externos (panel/docs OVH). Amarillo `#fcd34d` = destacar la IP actual y elementos de marca. |
| Iconos | **Sprite SVG estático** en `src/static/icons.svg` + `<svg class="icon"><use href="/static/icons.svg#i-NAME"/></svg>`. Mismo patrón que nudge sin React, una sola request cacheable. |
| Logo | **Letra "D" geométrica** sobre fondo `#1a1a2e` redondeado (rx=96), glifo `#e2e8f0`, dot amarillo `#fcd34d` con halo. Mismo lenguaje gráfico que el logo de nudge, distinto símbolo. Master en `src/static/icons/source.svg`. |
| Set de assets | **PWA completo**: `source.svg`, `favicon.ico`, `apple-touch-icon-180x180.png`, `pwa-64x64.png`, `pwa-192x192.png`, `pwa-512x512.png`, `maskable-icon-512x512.png`, `manifest.json`. Sin service worker — la app no es PWA real, pero queda preparada. |
| Estrategia de PR | **Un único PR** "design system migration". |

---

## Design proposal

### 1. Tokens CSS (variables `:root`)

Reemplazar el bloque actual de `--primary-color`, `--bg-color`, etc., por la paleta de nudge **idéntica** (mismos hex, mismos nombres de variable). Se mantienen los nombres `--c-*` de nudge para que en el futuro el código sea trivialmente intercambiable.

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
  --shadow-xs: 0 1px 2px rgba(0,0,0,0.2);
  --shadow-sm: 0 2px 8px rgba(0,0,0,0.1);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.08);
  --shadow-lg: 0 20px 60px rgba(0,0,0,0.15);
  --shadow-focus: 0 0 0 2px var(--c-ring);
  --transition: 150ms ease;
}
```

Las clases existentes (`.btn-primary`, `.nav-link`, `.card`, `.table`) se reescriben para consumir las nuevas variables. **Su API pública (los nombres de clase usados desde HTML) no cambia**, así que `app.js` no necesita modificaciones.

### 2. Tipografía

System stack idéntico a nudge:

```css
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  -webkit-font-smoothing: antialiased;
}
```

Pesos: 500 / 600 / 700 (drop el actual 400/600 mixto). Tamaños comprimidos hacia el rango de nudge (0.75–1.25rem como dominante; 0.875rem inputs). Números en columnas con `font-variant-numeric: tabular-nums` (tabla de hosts y de history).

### 3. Asignación semántica de colores

| Elemento | Color | Token |
|---|---|---|
| Nav brand "OVH DynDNS Client" | slate-text | `var(--c-primary)` |
| Nav links activos | slate fondo + blanco | `--c-primary` / `--c-surface` |
| Botón "Add Host", "Save", "Login" | slate | `--c-primary` |
| Botón "Trigger Update Now" | slate | `--c-primary` |
| Botón "Delete" (modal confirm) | danger | `--c-danger` |
| Card "Current IP" | **borde izquierdo amarillo** + IP en bold | `--c-brand` (border-left: 3px) |
| `.big-text` de la IP | ink color | `--c-ink` |
| Badge / dot "IP changed" en history | amarillo brand | `--c-brand` |
| **Enlaces externos a OVH** (`<a class="external">`) | indigo | `--c-shared` |
| `Last Update` rojo si fallo | danger | `--c-danger` |
| `Last Status: success` | success | `--c-success` |
| `must_change_password` info-text | warning | `--c-warning` |
| Borde de inputs en focus | slate ring | `var(--shadow-focus)` |

Detalle del amarillo: la card de "Current IP" recibe `border-left: 3px solid var(--c-brand)` y el resto de cards (`Last Check`, `Next Check`) llevan border-left neutro `var(--c-border-inner)`. Patrón visual idéntico al `.cardBorderSuccess/Warning/Danger` de nudge.

Detalle del indigo: introducir clase `.link-external` con color `var(--c-shared)` + `text-decoration: none` + icono `external-link` adyacente. Aplicar a:
- Footer/nav: enlace nuevo "OVH DynHost panel" (ej. `https://www.ovh.com/manager/`).
- Eventualmente, en cada fila de hosts (botón secundario con icono `external-link` que abra el panel OVH del dominio). **Fuera de scope para este PR** — el token queda disponible.

### 4. Iconos Lucide vía sprite SVG

**Fichero nuevo**: `src/static/icons.svg`.

Estructura:
```xml
<svg xmlns="http://www.w3.org/2000/svg" style="display:none">
  <symbol id="i-plus" viewBox="0 0 24 24" fill="none" stroke="currentColor"
          stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M12 5v14M5 12h14"/>
  </symbol>
  <!-- ... resto de symbols ... -->
</svg>
```

Cada icono se referencia como:
```html
<svg class="icon"><use href="/static/icons.svg#i-plus"/></svg>
<svg class="icon icon-sm"><use href="/static/icons.svg#i-trash-2"/></svg>
```

Clase global `.icon` añadida al CSS (idéntica a nudge): 16px, `stroke: currentColor`, `stroke-width: 2`, `stroke-linecap/linejoin: round`, `fill: none`. Variantes `.icon-sm` (14) e `.icon-lg` (20).

**Set de iconos curado** (los estrictamente necesarios; añadir más solo cuando se usen):

| Nombre | Lucide | Uso |
|---|---|---|
| `i-activity` | activity | Nav: Status |
| `i-server` | server | Nav: Hosts |
| `i-clock` | clock | Nav: History / pending |
| `i-settings` | settings | Nav: Settings |
| `i-log-out` | log-out | Nav: Logout |
| `i-plus` | plus | Botón Add Host |
| `i-pencil` | pencil | Acción editar fila |
| `i-trash-2` | trash-2 | Acción borrar fila |
| `i-refresh-cw` | refresh-cw | Trigger Update + force update por host |
| `i-globe` | globe | Card "Current IP" |
| `i-x` | x | Cerrar modal |
| `i-chevron-left` | chevron-left | Pagination ← |
| `i-chevron-right` | chevron-right | Pagination → |
| `i-check-circle` | check-circle | Status success |
| `i-x-circle` | x-circle | Status error |
| `i-alert-triangle` | alert-triangle | Warning (must-change-password) |
| `i-external-link` | external-link | Enlaces a panel OVH (token indigo listo) |

Total: 17 iconos. Sprite estimado < 6 KB sin gzip, < 2 KB gzipped. Una sola request servida por FastAPI desde `/static/icons.svg`.

**Origen de los `<path>`**: copiar literalmente los `<path>` de los SVG oficiales de Lucide (https://lucide.dev). Cada icono Lucide es CC0/ISC, sin attribution requerida. Se copian a mano una sola vez.

### 5. Logo y favicon

**Master SVG** (`src/static/icons/source.svg`, viewBox 512×512):

- Fondo: `<rect width="512" height="512" rx="96" fill="#1a1a2e"/>`.
- Glifo "D" en `#e2e8f0`: barra vertical izquierda (rect 82×292 con `rx=6` en x=108, y=112) + bowl derecho construido con un `<path>` que arquea desde el top de la barra hasta su bottom pasando por la derecha (arco SVG `A` con curvatura suave). Para evitar overlap, la barra y el bowl pueden unirse en un único `<path>` cerrado. La equivalencia visual con la "N" de nudge se mantiene: trazo grueso, esquinas ligeramente redondeadas, peso visual similar.
- Dot amarillo: `<circle cx="394" cy="106" r="72" fill="#1a1a2e"/>` (halo de separación con el fondo) + `<circle cx="394" cy="106" r="58" fill="#FCD34D"/>` (igual que nudge).

**Derivados** (rasterizados desde el master con `pwa-asset-generator`):

| Fichero | Tamaño | Uso |
|---|---|---|
| `favicon.ico` | 32×32 + 16×16 | `<link rel="icon">` legacy |
| `apple-touch-icon-180x180.png` | 180×180 | iOS home screen |
| `pwa-64x64.png` | 64×64 | PWA small |
| `pwa-192x192.png` | 192×192 | PWA standard |
| `pwa-512x512.png` | 512×512 | PWA large / splash |
| `maskable-icon-512x512.png` | 512×512 | Adaptive icons Android (con padding interno) |
| `manifest.json` | — | Web app manifest mínimo (`name`, `short_name`, `icons[]`, `theme_color: #454961`, `background_color: #fafafa`, `display: standalone`) |

Generación: el dev container es Python/Alpine, no tiene Node. La task de generación usa un contenedor Node one-shot:
```bash
docker run --rm -v "$PWD/src/static/icons":/icons -w /icons \
  node:22-alpine sh -c "npx --yes @vite-pwa/assets-generator \
  --preset minimal source.svg"
```
El resultado se commitea (no es un build step recurrente — los assets se generan una vez y viven en el repo).

**Wiring en `index.html`** (en `<head>`):
```html
<link rel="icon" href="/static/icons/favicon.ico" sizes="any" />
<link rel="icon" type="image/svg+xml" href="/static/icons/source.svg" />
<link rel="apple-touch-icon" href="/static/icons/apple-touch-icon-180x180.png" />
<link rel="manifest" href="/static/icons/manifest.json" />
<meta name="theme-color" content="#454961" />
```

**Logo en navbar**: en `.nav-brand` prepender un `<img src="/static/icons/source.svg" class="brand-logo" alt="" />` antes del texto. Nueva regla CSS:
```css
.brand-logo { width: 24px; height: 24px; vertical-align: middle; margin-right: 0.5rem; }
.nav-brand { display: inline-flex; align-items: center; }
```

### 6. Aplicación en HTML

Cambios mínimos en `src/static/index.html`:
- En cada `<a class="nav-link">`: añadir `<svg class="icon"><use href="..."/></svg>` antes del texto.
- En botón "Add Host": idem con `i-plus`.
- En botón "Trigger Update Now": idem con `i-refresh-cw`.
- En cada fila de tabla, columna Actions: reemplazar texto "Edit"/"Delete" por botones icon (`i-pencil`, `i-trash-2`). El JS sigue identificando por clase, no cambia.
- Cerrar modal: reemplazar `&times;` por `<svg class="icon"><use href="...#i-x"/></svg>`.
- Card Current IP: añadir `<svg class="icon"><use href="...#i-globe"/></svg>` junto al título.
- Botones de pagination: prepend chevrons.
- En la card de "must change password" (info-text): prepend `i-alert-triangle`.

Las clases CSS ya existentes (`.btn-icon`, `.btn-primary`, etc.) se ajustan en CSS, no en HTML. JS no se toca salvo si añadimos un único helper opcional (ver Open design decisions abajo, ya cerrado).

### 7. Cambios en `app.js`

**Mínimos.** El JS actual solo manipula clases ya existentes y contenido textual. El único punto donde se construye HTML dinámicamente es en el render de tablas (`hosts`, `host-status`, `history`). Allí, las celdas de "Actions" pasan a generar:

```js
`<button class="btn-icon edit-btn" data-id="${id}">
   <svg class="icon"><use href="/static/icons.svg#i-pencil"/></svg>
 </button>
 <button class="btn-icon delete-btn" data-id="${id}">
   <svg class="icon"><use href="/static/icons.svg#i-trash-2"/></svg>
 </button>`
```

Sin nuevos event listeners; los selectores de delegación siguen funcionando.

---

## Scope

### What is included

- Sustitución total de variables CSS en `style.css` por las de nudge (mismos nombres, mismos valores).
- System font stack idéntico al de nudge en `body`.
- Aplicación de la paleta a todas las clases existentes (sin renombrar).
- Borde izquierdo amarillo en card "Current IP" (con token brand).
- Color indigo en clase nueva `.link-external` (sin enlaces a OVH añadidos en este PR — la clase queda disponible).
- Sprite SVG nuevo en `src/static/icons.svg` con 17 iconos curados de Lucide.
- Clases globales `.icon`, `.icon-sm`, `.icon-lg`.
- **Logo nuevo** (letra "D" sobre fondo dark con dot amarillo) como `src/static/icons/source.svg` y derivados PWA completos (favicon.ico, apple-touch-180, pwa-64/192/512, maskable-512, manifest.json).
- Logo embebido en `.nav-brand` (24×24) y wiring de `<link rel="icon">` + `<link rel="manifest">` + `<meta name="theme-color">` en `<head>`.
- Inserción de iconos en HTML: nav, botones primarios, acciones de fila, cerrar modal, paginación, card de IP, info-text de cambio de password.
- Generación de iconos en celdas de tabla dinámicas desde `app.js` (única zona de JS afectada).
- Tests E2E existentes adaptados si rompen por cambio de markup en celdas de Actions.

### What is NOT included

- **No re-estructura de HTML**: tablas siguen siendo tablas, modales no se rehacen, navbar mantiene su forma horizontal.
- **No nuevos endpoints ni nuevas pantallas**: ni "OVH panel" link funcional, ni dashboard alternativo. El token indigo queda disponible para futuro.
- **No webfonts**: mantenemos system stack.
- **No dark mode**.
- **No animaciones nuevas** más allá de la `--transition: 150ms ease` de nudge ya presente en `:root`.
- **No mobile re-layout**: el media query existente `@media (max-width: 768px)` se conserva tal cual con paleta nueva.
- **No iconos por host** ni indicadores avanzados de severidad (estilo `.cardBorderSuccess` de nudge en cada fila): fuera de scope; el HTML actual con tablas no encaja con ese patrón. Issue de seguimiento si se quiere.
- **No build step**: seguimos sin bundler. El sprite y los assets PWA se sirven estáticos. La generación de derivados PNG/ICO se ejecuta una sola vez con un contenedor Node puntual y los ficheros se commitean.
- **No service worker**: el manifest existe pero la app no es PWA real (no hay SW, no hay caché offline).

---

## Affected layers

| Layer | Impact |
|-------|--------|
| API (FastAPI) | Sin cambios. `StaticFiles` ya sirve `/static/*`, el nuevo `icons.svg` se sirve gratis. |
| Application | Sin cambios. |
| Domain | Sin cambios. |
| Infrastructure | Sin cambios. |
| Frontend (`src/static/`) | `css/style.css` reescrito (mismas clases, nuevas variables y tokens; añade `.brand-logo`). `index.html` añade iconos en puntos puntuales, links de favicon/manifest en `<head>`, `<img>` del logo en `.nav-brand`. `js/app.js` cambia generación de celdas de Actions (3-4 funciones de render). Nuevo fichero `icons.svg`. Nuevo directorio `src/static/icons/` con `source.svg`, `favicon.ico`, `apple-touch-icon-180x180.png`, `pwa-64x64.png`, `pwa-192x192.png`, `pwa-512x512.png`, `maskable-icon-512x512.png`, `manifest.json`. |
| Tests | Tests unitarios Python sin cambios. Tests E2E (Playwright en `e2e/`) pueden necesitar ajuste si seleccionan por texto "Edit"/"Delete" en celdas — comprobar y migrar a selectores robustos (`[data-action="edit"]`). |
| Docker / CI | Sin cambios. El sprite es un fichero más bajo `src/static/`, ya copiado por el `Dockerfile`. |

---

## Implementation order

1. **Variables y tipografía**: reescribir `:root` en `style.css` con la paleta y los tokens de shape de nudge. Aplicar `font-family` system stack en `body`. Sin tocar HTML. Verificación visual: la página actual ya debería verse "más slate" inmediatamente.
2. **Aplicar variables a clases existentes**: actualizar `.btn-primary`, `.nav-link`, `.card`, `.table`, `.modal`, `.form-group`, etc., para consumir las nuevas vars y ajustar espaciados/pesos según convenciones de nudge (font-weight 500/600, sizes 0.75–0.875rem dominantes). Tabular-nums en `.table`.
3. **Card de IP**: añadir `border-left: 3px solid var(--c-brand)` específicamente a la card que aloja la IP actual (clase nueva `.card-ip` o atributo data, evaluar). Resto de cards toman border-left neutro.
4. **Clase `.link-external`** y `.icon` + `.icon-sm` + `.icon-lg`: añadir bloque al final de `style.css`.
5. **Crear `src/static/icons.svg`**: sprite con los 17 symbols. Validar que `<use href="/static/icons.svg#i-X">` resuelve correctamente sirviendo desde el dev container.
6. **Insertar iconos en HTML estático**: nav, botones principales, modales, card de IP, paginación.
7. **Insertar iconos en celdas dinámicas** (`app.js`): renderizado de Actions en hosts/host-status/history. Mantener selectores existentes funcionales.
8. **E2E**: levantar Playwright y verificar; arreglar selectores frágiles (texto → atributo) si rompen.
9. **Verificación final**: lint (`ruff` no aplica al frontend, pero ESLint/HTML manual), arrancar dev container, recorrer todas las pantallas en Chrome y Safari, smoke-test con un host de prueba.

---

## Critical files

| File | Changes |
|------|---------|
| `src/static/css/style.css` | Reescritura del bloque `:root` (paleta + shape tokens). Adaptación de todas las clases existentes a las nuevas variables. Añadir `.icon`, `.icon-sm`, `.icon-lg`, `.link-external`, `.card-ip`, `.brand-logo`. Ajustar font-weight y sizes a la convención nudge. Eliminar variables obsoletas (`--primary-color`, `--bg-color`, etc.). |
| `src/static/icons.svg` | **Nuevo**. 17 `<symbol>` con paths copiados de Lucide. Display none global. |
| `src/static/icons/source.svg` | **Nuevo**. Logo master 512×512: fondo `#1a1a2e` rx=96, "D" geométrica `#e2e8f0`, dot amarillo `#fcd34d` con halo. |
| `src/static/icons/favicon.ico` | **Nuevo**. Generado desde `source.svg`. |
| `src/static/icons/apple-touch-icon-180x180.png` | **Nuevo**. |
| `src/static/icons/pwa-64x64.png` | **Nuevo**. |
| `src/static/icons/pwa-192x192.png` | **Nuevo**. |
| `src/static/icons/pwa-512x512.png` | **Nuevo**. |
| `src/static/icons/maskable-icon-512x512.png` | **Nuevo**. |
| `src/static/icons/manifest.json` | **Nuevo**. Manifest mínimo con `theme_color: #454961`, `background_color: #fafafa`, `display: standalone`. |
| `src/static/index.html` | Insertar `<svg><use/></svg>` en: nav (5 links), botones primarios (Add Host, Trigger Update, Save Settings, Login), info-text de cambio de password, card "Current IP" (i-globe), modal close (reemplaza `&times;`), botones de pagination (chevrons). Añadir clase `.card-ip` al wrapper de la card de IP. En `<head>` añadir links de favicon SVG, favicon.ico, apple-touch-icon, manifest, y `<meta name="theme-color">`. En `.nav-brand` prepender `<img class="brand-logo" src="/static/icons/source.svg" alt="">`. Bloque opcional `<a class="link-external" href="https://www.ovh.com/manager/">` en footer (decisión final en implementación). |
| `src/static/js/app.js` | Funciones de render de filas (`loadStatus`, `loadHosts`, `loadHistory`) emiten `<svg class="icon"><use/></svg>` dentro de los `<button>` de Actions en lugar de texto. |
| `e2e/tests/*.spec.js` | Sin cambios — los selectores actuales usan IDs y clases (`.btn-danger`, `#hosts-table tbody tr`), no texto. |

---

## Risks and considerations

- **`<use href="/static/icons.svg#...">` y caché**: si se cambia el sprite, el navegador puede servir versión cacheada. Mitigación: el contenedor sirve los estáticos sin cache headers fuertes; en producción detrás de proxy con TTL alto, considerar versionado del path (`icons.svg?v=1`). No crítico para v1.
- **Daltonismo**: la dependencia del amarillo brand para la card de IP no es crítica (es decoración + label textual), pero conviene validar contraste WCAG AA del slate sobre fondo gris claro (`#454961` sobre `#fafafa` da ratio ≈ 8.5:1, cumple AAA).
- **Compatibilidad de `<svg><use href="external#frag">`** con navegadores antiguos: IE11 no soporta external `<use>`, pero el proyecto target es navegadores modernos (no se documenta soporte IE), aceptable.
- **Estética coherente vs. funcionalidad**: el alcance "solo paleta y tipografía" no rehace el layout de tablas. La sensación final será **"nudge-tinted"** pero no idéntica a nudge. Si el usuario espera paridad visual completa, hace falta el re-skin medio o completo (decisión que ya rechazó). Documentar este límite en el PR description.
- **Tests E2E**: si los selectores son por texto, romperán tras quitar "Edit"/"Delete". Hay que adaptarlos en este mismo PR (no dejarlos rojos).
- **Drift con nudge en el futuro**: si nudge evoluciona sus tokens, este proyecto queda atrás. Como no compartimos un paquete CSS, aceptamos drift manual. Issue de seguimiento si se quiere extraer un paquete común.
- **Iconos copiados manualmente**: hay que respetar el origen Lucide. Licencia ISC, no requiere attribution en runtime, pero conviene una nota en `style.css` o `icons.svg` ("Icons from Lucide — https://lucide.dev — ISC").
- **Generación de assets PWA con Node**: el dev container es Python+Alpine, no tiene Node. La task de logo ejecuta `pwa-asset-generator` con un contenedor Node puntual (`docker run --rm node:22-alpine ...`). Sin impacto en CI ni en el contenedor de runtime. Los ficheros derivados se commitean como binarios en el repo.

---

## Open design decisions

Ninguna pendiente. Las cuatro decisiones de diseño abiertas se cerraron antes de redactar este documento. El plan está listo para descomponerse en tasks.
