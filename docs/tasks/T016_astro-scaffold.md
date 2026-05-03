# T016 — Astro + Tailwind scaffold + Base layout + public assets + `.gitignore`

## Context

Foundation of the landing page. Sets up the Astro project tree
(`site/`), the Tailwind palette anchored on the app's slate-blue
tokens, the body gradient that all pages will inherit, the public
assets the layout's `<link rel="icon">` and `<meta property="og:image">`
need, and the `.gitignore` entries the rest of the series will rely on.
At the end of this task `npm run dev` boots an Astro dev server and
serves a blank page with the dark gradient background — visually empty
but architecturally complete.

Plan: [docs/plans/landing-page.md](../plans/landing-page.md).

**Dependencies**: None.

## Objective

Create the `site/` directory tree with all configuration files, the
shared `Base.astro` layout, copied PWA / favicon assets under
`site/public/`, and the three `.gitignore` entries the build pipeline
needs. The Astro dev server must boot without errors.

## Step 1 — `site/package.json`

Mirror nudge's structure with our naming. Scripts wire `copy-screenshots.mjs`
in T018 — leave the `dev` and `build` lines empty for that hook for now,
just `astro dev` / `astro check && astro build`. T018 prepends the hook.

```json
{
  "name": "ovh-dyndns-site",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "astro dev",
    "build": "astro check && astro build",
    "preview": "astro preview",
    "astro": "astro"
  },
  "dependencies": {
    "@astrojs/check": "^0.9.4",
    "@astrojs/tailwind": "^5.1.4",
    "astro": "^4.16.18",
    "tailwindcss": "^3.4.17",
    "typescript": "^5.7.2"
  }
}
```

## Step 2 — `site/astro.config.mjs`

```javascript
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

`base: '/ovh-dyndns-client'` is critical — must match the GitHub Pages
URL path under the user account.

## Step 3 — `site/tailwind.config.mjs`

Custom palette: `brand` (yellow) + `ovh` ramp (slate-blue, anchored on
`#454961` — the app's `--c-primary`).

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,ts,tsx,md,mdx}'],
  darkMode: 'media',
  theme: {
    extend: {
      colors: {
        brand: '#FCD34D',
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

## Step 4 — `site/tsconfig.json`

Standard Astro template:

```json
{
  "extends": "astro/tsconfigs/strict",
  "include": ["src/**/*", ".astro/types.d.ts"],
  "exclude": ["dist"]
}
```

## Step 5 — `site/src/env.d.ts`

```typescript
/// <reference types="astro/client" />
```

## Step 6 — `site/src/styles/global.css`

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

## Step 7 — `site/src/layouts/Base.astro`

Layout shell with meta tags, OG image references, and the dark gradient
body.

```astro
---
import '../styles/global.css'

export interface Props {
  title?: string
  description?: string
}

const {
  title = 'OVH DynDNS Client — Self-hosted DynDNS for OVH domains',
  description = 'Point your OVH domains to a dynamic IP and forget about it. One Docker container, encrypted credentials, no external dependencies.',
} = Astro.props

const canonical = new URL(Astro.url.pathname, Astro.site ?? 'https://cibrandocampo.github.io').toString()
---
<!doctype html>
<html lang="en" class="scroll-smooth">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="color-scheme" content="dark" />
    <title>{title}</title>
    <meta name="description" content={description} />
    <link rel="icon" href={`${import.meta.env.BASE_URL}/favicon.ico`} />
    <link rel="canonical" href={canonical} />
    <meta property="og:title" content={title} />
    <meta property="og:description" content={description} />
    <meta property="og:type" content="website" />
    <meta property="og:url" content={canonical} />
    <meta property="og:image" content={`${import.meta.env.BASE_URL}/icons/pwa-512x512.png`} />
    <meta name="twitter:card" content="summary" />
    <meta name="twitter:title" content={title} />
    <meta name="twitter:description" content={description} />
  </head>
  <body class="min-h-screen bg-gradient-to-br from-ovh-950 via-slate-950 to-ovh-900 text-slate-100 antialiased">
    <slot />
  </body>
</html>
```

## Step 8 — Public assets

Copy from `src/static/icons/`:

- `src/static/icons/favicon.ico` → `site/public/favicon.ico`
- `src/static/icons/pwa-192x192.png` → `site/public/icons/pwa-192x192.png`
- `src/static/icons/pwa-512x512.png` → `site/public/icons/pwa-512x512.png`
- `src/static/icons/apple-touch-icon-180x180.png` → `site/public/icons/apple-touch-icon-180x180.png`

(Use plain `cp`. The site references `pwa-512x512.png` for OG image.)

## Step 9 — `.gitignore` entries

Append to the project root `.gitignore`:

```
# Astro landing site
site/node_modules
site/dist
site/public/screenshots
```

## Step 10 — Smoke test

```bash
cd site
npm install
npm run dev &
DEV_PID=$!
sleep 5
curl -sf -o /dev/null -w "%{http_code}\n" http://localhost:4321/ovh-dyndns-client/
kill $DEV_PID 2>/dev/null
```

Expected: HTTP 200. Page is blank but renders the dark gradient
background.

## DoD — Definition of Done

1. `site/` directory exists with the expected file tree.
2. `site/package.json`, `astro.config.mjs`, `tailwind.config.mjs`,
   `tsconfig.json`, `src/env.d.ts`, `src/styles/global.css` present and
   valid.
3. `site/src/layouts/Base.astro` exists and parses (no Astro errors at
   build time).
4. `site/public/favicon.ico` and three PNG icons present.
5. `.gitignore` has the three site-related entries.
6. `cd site && npm install` completes without errors.
7. `npm run dev` boots and serves HTTP 200 on
   `http://localhost:4321/ovh-dyndns-client/`.
8. The served HTML references the correct `<title>`, `<link rel="icon">`,
   and OG image paths.

## Evidence to produce

| # | Description | Command | File | PASS condition |
|---|-------------|---------|------|----------------|
| 1 | `site/` tree present | `find site -maxdepth 3 -type f \| sort` | `tree.txt` | lists at minimum: package.json, astro.config.mjs, tailwind.config.mjs, tsconfig.json, src/env.d.ts, src/styles/global.css, src/layouts/Base.astro, public/favicon.ico, public/icons/pwa-512x512.png |
| 2 | Public assets in place | `ls -la site/public/ site/public/icons/ \| head -10` | `public_assets.txt` | favicon.ico + at least 3 PNGs visible |
| 3 | `.gitignore` entries | `grep -E '^site/' .gitignore` | `gitignore.txt` | three lines: `site/node_modules`, `site/dist`, `site/public/screenshots` |
| 4 | npm install | `cd site && npm install 2>&1 \| tail -5` | `npm_install.txt` | exit 0, "added N packages" line visible |
| 5 | Astro check passes | `cd site && npx astro check 2>&1 \| tail -10` | `astro_check.txt` | exit 0, "0 errors" or equivalent |
| 6 | Dev server returns 200 | `cd site && (npm run dev &) && sleep 6 && curl -sf -o /dev/null -w '%{http_code}' http://localhost:4321/ovh-dyndns-client/ ; pkill -f 'astro dev' \|\| true` | `dev_server.txt` | `200` |
| 7 | HTML contains expected meta tags | `cd site && (npm run dev &) && sleep 6 && curl -s http://localhost:4321/ovh-dyndns-client/ \| grep -E '<title>\|og:image' ; pkill -f 'astro dev' \|\| true` | `meta_tags.txt` | `<title>` line present, `og:image` line references `pwa-512x512.png` |

## Files to create/modify

| File | Action |
|------|--------|
| `site/package.json` | CREATE |
| `site/astro.config.mjs` | CREATE |
| `site/tailwind.config.mjs` | CREATE |
| `site/tsconfig.json` | CREATE |
| `site/src/env.d.ts` | CREATE |
| `site/src/styles/global.css` | CREATE |
| `site/src/layouts/Base.astro` | CREATE |
| `site/public/favicon.ico` | CREATE (copy from `src/static/icons/favicon.ico`) |
| `site/public/icons/pwa-192x192.png` | CREATE (copy) |
| `site/public/icons/pwa-512x512.png` | CREATE (copy) |
| `site/public/icons/apple-touch-icon-180x180.png` | CREATE (copy) |
| `site/package-lock.json` | CREATE (generated by `npm install`) |
| `.gitignore` | MODIFY (append 3 entries) |

## Execution evidence

**Date**: 2026-05-04
**Modified files**:
- `site/package.json` — Astro+Tailwind dependency manifest
- `site/astro.config.mjs` — `base: '/ovh-dyndns-client'`, static output, Tailwind integration
- `site/tailwind.config.mjs` — `ovh` ramp anchored on `#454961` + `brand` yellow
- `site/tsconfig.json` — strict Astro template
- `site/src/env.d.ts` — Astro client types (auto-extended by `astro check` to also reference `.astro/types.d.ts`)
- `site/src/styles/global.css` — Tailwind base/components/utilities directives
- `site/src/layouts/Base.astro` — shared layout with title, meta, OG tags, dark gradient body
- `site/src/pages/index.astro` — placeholder routing page so the dev server returns 200 (T017 will replace the body)
- `site/public/favicon.ico`, `site/public/icons/{pwa-192x192,pwa-512x512,apple-touch-icon-180x180}.png` — copied from `src/static/icons/`
- `site/package-lock.json` — generated by `npm install`
- `.gitignore` — removed dead `/site` mkdocs vestige (would have ignored the entire new site/) and appended `site/node_modules`, `site/dist`, `site/public/screenshots`

### Verification table

| # | Deliverable | Evidence file | Result |
|---|-------------|---------------|--------|
| 1 | `site/` tree present | `docs/tasks/evidence/T016/tree.txt` | PASS — package.json, astro.config.mjs, tailwind.config.mjs, tsconfig.json, src/env.d.ts, src/styles/global.css, src/layouts/Base.astro, public/favicon.ico, public/icons/pwa-512x512.png all listed |
| 2 | Public assets in place | `docs/tasks/evidence/T016/public_assets.txt` | PASS — favicon.ico + 3 PNGs |
| 3 | `.gitignore` entries | `docs/tasks/evidence/T016/gitignore.txt` | PASS — `site/node_modules`, `site/dist`, `site/public/screenshots` |
| 4 | npm install | `docs/tasks/evidence/T016/npm_install.txt` | PASS — `added 449 packages` |
| 5 | Astro check | `docs/tasks/evidence/T016/astro_check.txt` | PASS — `0 errors`, `0 warnings`, `0 hints` |
| 6 | Dev server returns 200 | `docs/tasks/evidence/T016/dev_server.txt` | PASS — `200` on `http://localhost:4321/ovh-dyndns-client/` |
| 7 | HTML contains expected meta tags | `docs/tasks/evidence/T016/meta_tags.txt` | PASS — `<title>OVH DynDNS Client — Self-hosted DynDNS for OVH domains</title>` and `og:image` resolves to `/ovh-dyndns-client/icons/pwa-512x512.png` |

### Design decisions

- **`/site` mkdocs entry removed from `.gitignore`** — the leading `/site` (line 129 of the previous version) was a vestigial mkdocs-output path. With `base: '/ovh-dyndns-client'` Astro emits `dist/`, never `site/`, but a top-level `/site` rule would silently swallow the entire new project tree. Real mkdocs builds are still ignored via `docs/_build/` higher up.
- **`site/src/pages/index.astro` added in this task** — the task spec smoke-tests for HTTP 200, but `Base.astro` is a layout, not a page. Astro returns 404 without a page in `src/pages/`. A one-line placeholder (`<Base />`) routes the URL while leaving the body empty for T017 to fill in.
- **Node version mismatch is fine for local dev** — local Node is 20.19.4; CI workflow (T019) pins 22. Astro 4.16 supports both (≥18.17.1 / ≥20.3.0 / ≥22), so a single lockfile works for both environments.
