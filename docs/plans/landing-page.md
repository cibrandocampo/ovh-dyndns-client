# Landing page (`site/`)

## Context

GitHub Pages está habilitado en Settings → Pages → Source: GitHub Actions, y dos PRs anteriores (PR #11 y PR #12) introdujeron sendos enlaces al website desde el README. Pero la URL `https://cibrandocampo.github.io/ovh-dyndns-client/` devuelve **404** porque el repo no contiene aún la carpeta `site/` ni el workflow de deploy: la landing simplemente no existe.

Esta es la tercera pieza del split que agreed cuando empezamos el ciclo seed/screenshots. Al cerrarla, los enlaces ya activos del README cobrarán sentido y la URL servirá una landing real.

Mirroriza el patrón de nudge (`site/` con Astro + Tailwind, deploy a Pages vía workflow nativo de GitHub) adaptado al alcance de ovh-dyndns: una sola página estática con cinco secciones, **sin las áreas que no aplican aquí** (offline-first, notificaciones push, sharing).

## Decisions confirmed with user

| Topic | Decision |
|-------|----------|
| Stack | Astro + Tailwind, build estático para GitHub Pages. Imita 1:1 la estructura de `nudge/site/`. |
| Build runtime | Nativo con `npm` (no Docker). El resto del proyecto vive en Docker; la landing no — es coherente con el aislamiento que tiene nudge. |
| Hosting | GitHub Pages (`https://cibrandocampo.github.io/ovh-dyndns-client/`). Workflow nuevo dispara en `push: main`. |
| Screenshots source-of-truth | `docs/dashboard-*.png` (los cuatro PNGs ya seedeados por la pipeline T013–T015). El prebuild hook de Astro mirroriza esos PNGs a `site/public/screenshots/` antes de cada build. |
| Tema visual | **Dark**, igual que nudge. Background gradient slate/indigo oscuro, texto claro. Sin auto-switch a light. |
| Número de secciones | **5 lean**: Hero / How it works / Feature grid / Self-host snippet / Footer. Sin Pitch separado, sin Screenshots carousel, sin FAQ, sin Privacy section. |
| Install snippet | Bloque `<pre>` con botón **Copy** (mismo patrón de nudge: `<script is:inline>` con `navigator.clipboard.writeText`). |
| Stack badges | Visibles en el Hero, mismo patrón que nudge (Python, FastAPI, SQLite, Docker). Ayudan al visitante técnico a calibrar en 2 segundos. |
| Ámbito del PR | Solo el `site/` + workflow + Makefile targets + `.gitignore`. **Sin tocar el README** (el callout vive en una PR aparte ya pusheada). |

## Design proposal

### Estructura de directorios

```
site/
├── package.json                 # deps + scripts (dev, build, preview, astro)
├── astro.config.mjs             # site, base, output: 'static', integrations
├── tailwind.config.mjs          # palette + content globs
├── tsconfig.json                # de plantilla Astro
├── .gitignore                   # node_modules, dist, public/screenshots
├── public/
│   ├── favicon.ico              # copia de src/static/icons/favicon.ico
│   ├── icons/                   # los pwa-*.png para OG image / iOS install
│   └── screenshots/             # generado por prebuild — gitignored
├── scripts/
│   └── copy-screenshots.mjs     # prebuild hook
└── src/
    ├── env.d.ts
    ├── styles/global.css
    ├── layouts/Base.astro       # html shell + meta tags + body gradient
    ├── components/
    │   ├── Hero.astro
    │   ├── HowItWorks.astro
    │   ├── FeatureCard.astro
    │   ├── SelfHost.astro
    │   └── Footer.astro
    └── pages/
        └── index.astro
```

### Tailwind config

Replicate la estrategia de nudge: paleta custom anclada en los tokens del app, más `brand` para el yellow.

```js
// site/tailwind.config.mjs
export default {
  content: ['./src/**/*.{astro,html,js,jsx,ts,tsx,md,mdx}'],
  darkMode: 'media',
  theme: {
    extend: {
      colors: {
        brand: '#FCD34D',
        // Slate-blue ramp anchored on `--c-primary` from the app (#454961).
        // Used for primary CTAs, links and the dark gradient background.
        ovh: {
          50:  '#f1f2f5',
          100: '#dde0e8',
          300: '#8d93a9',
          500: '#454961',
          600: '#3a3d52',
          700: '#2d3041',
          800: '#23252f',
          900: '#181a22',
          950: '#0e0f15',
        },
      },
      fontFamily: {
        sans: ['system-ui', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', '"Helvetica Neue"', 'Arial', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      },
    },
  },
}
```

Body class en Base.astro: `bg-gradient-to-br from-ovh-950 via-slate-950 to-ovh-900 text-slate-100 antialiased`.

### Astro config

```js
// site/astro.config.mjs
import { defineConfig } from 'astro/config'
import tailwind from '@astrojs/tailwind'

export default defineConfig({
  site: 'https://cibrandocampo.github.io',
  base: '/ovh-dyndns-client',
  output: 'static',
  trailingSlash: 'ignore',
  integrations: [tailwind()],
})
```

`base: '/ovh-dyndns-client'` es crítico — debe coincidir con el path bajo el dominio de Pages. Sin él, los assets se sirven con paths rotos.

### Las cinco secciones de `index.astro`

1. **Hero** — Logo "D" + título "OVH DynDNS Client" + tagline ("Your IP changes. Your domains shouldn't.") + 4 stack badges (Python 3.14, FastAPI, SQLite, Docker multi-arch) + CTA primario ("Install"; ancla a `#self-host`) + screenshot grande del dashboard (`screenshots/dashboard-status.png`).
2. **How it works** — Tres pasos numerados:
   - **Add a host** — hostname + OVH DynHost credentials. Con un mini mock del modal "Add Host".
   - **The agent watches your IP** — texto + screenshot pequeño del status card "Current IP".
   - **DNS gets updated** — texto + dot amarillo o highlight visual.
3. **Feature grid** — 6 cards con icono Lucide + título + 1-2 frases:
   - Web UI
   - REST API + JWT
   - Encrypted credentials at rest
   - Rate-limited auth endpoints
   - Idempotent boot-time migration
   - Docker multi-arch (`amd64`, `arm64`, `arm/v7`)
4. **Self-host snippet** — Bloque `<pre>` con `docker compose up -d` + botón Copy + link al README "Self-hosting and technical details".
5. **Footer** — Copyright, link MIT licence, link al GitHub repo.

### Prebuild hook `copy-screenshots.mjs`

Adaptación del de nudge: en lugar de leer `docs/screenshots/<dir>/<file>.png` recursivo, lee `docs/dashboard-*.png` (los 4 PNGs planos) y los mirroriza a `site/public/screenshots/`. Mismo patrón de `sync` (copia + elimina archivos stale en destino).

```js
// site/scripts/copy-screenshots.mjs (sketch)
const SRC = join(__dirname, '..', '..', 'docs')
const DEST = join(__dirname, '..', 'public', 'screenshots')

// Solo los ficheros que matchean dashboard-*.png — no recursivo.
const files = readdirSync(SRC).filter(f => f.startsWith('dashboard-') && f.endsWith('.png'))
// Copy + remove stale
```

### Workflow `site-deploy.yml`

Clon directo del de nudge, ajustando los paths.

```yaml
# .github/workflows/site-deploy.yml
name: Deploy landing to GitHub Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: site
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v5
        with:
          node-version: '22'
          cache: npm
          cache-dependency-path: site/package-lock.json
      - run: npm ci
      - run: npm run build
      - uses: actions/upload-pages-artifact@v5
        with:
          path: site/dist
  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v5
```

### Makefile (raíz)

Añadir dos targets al Makefile que ya existe:

```makefile
.PHONY: help screenshots site-dev site-build

site-dev:   ## Run the Astro landing dev server on http://localhost:4321/ovh-dyndns-client/
	cd site && npm run dev

site-build: ## Build the Astro landing site into site/dist/
	cd site && npm run build
```

### `.gitignore`

Añadir entradas:
```
site/node_modules
site/dist
site/public/screenshots
```

(El último porque los screenshots se mirrorizan ahí en cada build; ya viven como source-of-truth en `docs/`.)

## Scope

### What is included

- `site/` con Astro + Tailwind, layout, 4 componentes, 1 página, prebuild hook, configs, package.json, tsconfig.
- `.github/workflows/site-deploy.yml` (nuevo).
- Makefile root: targets `site-dev` y `site-build`.
- `.gitignore`: tres entradas para no commitear node_modules / dist / screenshots mirrorizadas.
- `site/public/favicon.ico` y un par de PNGs PWA copiados desde `src/static/icons/` para OG image y favicon de la landing.
- `site/package-lock.json` committed (CI lo necesita para `npm ci`).

### What is NOT included

- Cambios en el README (callout ya está en branch separada `docs/readme-website-callout`).
- Mobile-only responsive adjustments más allá de lo que Tailwind da por default.
- I18n (la landing va solo en inglés, igual que nudge).
- FAQ section, Pitch section, Privacy section, Screenshots carousel — se descartaron por scope.
- Web Analytics o Telemetría (cero tracking; valor del producto self-hosted).
- Test E2E sobre la landing (no hay tests del site en nudge tampoco; verificación visual sobre la URL pública).
- Re-captura de screenshots desde la landing (esa pipeline vive aparte en T013–T015).
- Branding redesign (reusamos el logo "D" existente).

## Affected layers

| Layer | Impact |
|-------|--------|
| API (FastAPI) | None. |
| Application (services/ports) | None. |
| Domain (models) | None. |
| Infrastructure | None. |
| Tests | No unit/integration tests para la landing — verification es ojo + URL pública post-deploy. |
| Docker | Sin cambios. La landing builds nativa con `npm`, no en el dev container. |
| CI | Nuevo workflow `site-deploy.yml`. Workflows existentes (`build-on-changes.yml`, `update-python.yml`) intactos. |
| Documentation | El plan + 2-3 task files. Sin cambios al README en este PR. |

## Implementation order

1. **Scaffold del Astro project**: `npm create astro` o creación manual de `site/package.json`, `astro.config.mjs`, `tsconfig.json`. Verificar que `npm install && npm run dev` arranca un dev server.
2. **Tailwind setup**: instalar `@astrojs/tailwind`, crear `tailwind.config.mjs` con la paleta `ovh` + `brand`, `src/styles/global.css` con `@tailwind` directivas.
3. **`Base.astro` layout**: html shell + meta tags (incluyendo og:title, og:image, twitter:card) + body gradient + `<slot />`.
4. **`Hero.astro`**: componente con logo + título + tagline + badges + CTA + dashboard screenshot.
5. **`HowItWorks.astro`**: tres pasos numerados con texto + mini-visuals.
6. **`FeatureCard.astro`**: componente reusable (icon Lucide inline + título + body).
7. **`SelfHost.astro`**: bloque pre con código + botón Copy + script inline.
8. **`Footer.astro`**: una línea con copyright + MIT + GitHub link.
9. **`index.astro`**: orchestrate las cinco secciones.
10. **`scripts/copy-screenshots.mjs`**: prebuild hook adaptado.
11. **`Makefile`**: targets `site-dev`, `site-build`.
12. **`.github/workflows/site-deploy.yml`**: workflow de Pages.
13. **`.gitignore`**: entradas nuevas.
14. **`site/public/favicon.ico` + PNGs**: copiar desde `src/static/icons/`.
15. **Build local end-to-end**: `make site-build` → `site/dist` poblado, abrir `index.html` y validar visualmente.
16. **Push** + verificar que el workflow hace deploy + URL responde 200 con la landing.

## Critical files

| File | Action |
|------|--------|
| `site/package.json` | CREATE |
| `site/astro.config.mjs` | CREATE |
| `site/tailwind.config.mjs` | CREATE |
| `site/tsconfig.json` | CREATE |
| `site/src/env.d.ts` | CREATE |
| `site/src/styles/global.css` | CREATE |
| `site/src/layouts/Base.astro` | CREATE |
| `site/src/components/Hero.astro` | CREATE |
| `site/src/components/HowItWorks.astro` | CREATE |
| `site/src/components/FeatureCard.astro` | CREATE |
| `site/src/components/SelfHost.astro` | CREATE |
| `site/src/components/Footer.astro` | CREATE |
| `site/src/pages/index.astro` | CREATE |
| `site/scripts/copy-screenshots.mjs` | CREATE |
| `site/public/favicon.ico` | CREATE (copy) |
| `site/public/icons/*` | CREATE (copy from src/static/icons) |
| `site/package-lock.json` | CREATE (genera `npm install`) |
| `.github/workflows/site-deploy.yml` | CREATE |
| `Makefile` | MODIFY (`site-dev`, `site-build` targets) |
| `.gitignore` | MODIFY (3 entries) |

## Risks and considerations

- **`base: '/ovh-dyndns-client'` debe ser exacto.** Si lo cambias o la URL del repo cambia, todos los assets internos (imágenes, hojas de estilo) se sirven con paths rotos. Probar con `astro preview` localmente — `astro preview` simula el deploy con base path.
- **El primer deploy a Pages** puede tardar 1-2 minutos en propagarse. Si justo después del merge la URL devuelve 404, esperar antes de declarar el deploy roto.
- **Workflow runs en cada push a main**. La build es <1 min — barato. Sin path filter porque mantener la landing en sync con el resto del código vale la pena.
- **`site/package-lock.json`** debe commitearse (CI usa `npm ci`, que requiere lockfile). Generar con `npm install` en el dev local.
- **Nodo 22** en CI — Astro v4 funciona con Node 18+, pero alineamos a la versión que usa nudge para evitar drift.
- **Screenshots stale**: el hook copy-screenshots NO regenera los PNGs, solo los copia. Si el dashboard cambia, hay que correr `make screenshots` (T015) y commitear los nuevos `docs/dashboard-*.png` antes de mergear; el deploy de la landing los recogerá.
- **Sin tests automatizados de la landing**. Bugfixes son operator-driven via `make site-dev` + ojo. Aceptable para un site marketing pequeño; si crece, añadir Playwright sobre la URL pública.
- **`site/node_modules` puede crecer**: ~150-200 MB con Astro + Tailwind. Está en `.gitignore`, no impacta al repo.
- **`darkMode: 'media'`** en Tailwind — respeta `prefers-color-scheme`. Pero como diseñamos solo dark, los selectores `dark:` no aplican y todo se ve dark consistentemente. Aceptable por ahora.
- **CORS / mixed content**: la landing es totalmente estática, no llama al backend del app. Cero riesgo.
- **Política de seguridad / CSP**: no añadimos `Content-Security-Policy` headers — GitHub Pages no permite headers custom de todas formas. El JS del botón Copy es inline (`is:inline`) y no depende de cdn externos.

## Open design decisions

Ninguna pendiente. Las cuatro decisiones abiertas se cerraron antes de redactar el documento. Plan listo para descomponer en tasks.
