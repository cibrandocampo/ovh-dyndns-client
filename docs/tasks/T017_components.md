# T017 — Components (Hero, HowItWorks, FeatureCard, SelfHost, Footer) + `index.astro`

## Context

Visual content of the landing. With the foundation from T016 in place
(Astro scaffold, Tailwind palette, Base layout), this task fills it with
five sections per the plan: Hero, How it works, Feature grid, Self-host
snippet, Footer. `index.astro` orchestrates them.

Plan: [docs/plans/landing-page.md](../plans/landing-page.md), section
"Las cinco secciones de `index.astro`".

**Dependencies**: T016 (Base layout + Tailwind palette must exist).

## Objective

Five Astro components and one orchestrator page that, when built,
produce a cohesive landing covering the product pitch, the three-step
how-it-works, the six feature cards, the install snippet with a working
Copy button, and a minimal footer.

## Step 1 — `Hero.astro`

Centered block: logo ("D" master SVG) → title → tagline → 4 stack
badges → primary CTA (anchor to `#self-host`) → dashboard hero
screenshot.

Sketch:

```astro
---
const badges = [
  { label: 'Python 3.14', color: '#3776AB' },
  { label: 'FastAPI', color: '#009688' },
  { label: 'SQLite', color: '#003B57' },
  { label: 'Docker multi-arch', color: '#2496ED' },
]
---
<section class="mx-auto max-w-5xl px-6 py-16 sm:py-24 text-center">
  <img src={`${import.meta.env.BASE_URL}/icons/pwa-512x512.png`} class="mx-auto h-20 w-20" alt="OVH DynDNS Client logo" />
  <h1 class="mt-6 text-4xl sm:text-5xl font-bold tracking-tight">OVH DynDNS Client</h1>
  <p class="mt-4 text-xl text-slate-300">
    <em>Your IP changes. Your domains shouldn't.</em>
  </p>
  <p class="mt-3 text-base text-slate-400 max-w-2xl mx-auto">
    Point your OVH domains to a dynamic IP and forget about it — one container, no external dependencies, your server, your rules.
  </p>
  <div class="mt-6 flex flex-wrap justify-center gap-2">
    {badges.map((b) => (
      <span class="inline-flex items-center rounded-full bg-ovh-800 border border-ovh-700 px-3 py-1 text-xs font-medium text-slate-200">{b.label}</span>
    ))}
  </div>
  <div class="mt-8">
    <a href="#self-host" class="inline-flex items-center rounded-md bg-brand text-ovh-900 px-5 py-2.5 text-sm font-semibold hover:bg-yellow-300 transition">
      Install in 5 minutes →
    </a>
  </div>
  <div class="mt-12">
    <img src={`${import.meta.env.BASE_URL}/screenshots/dashboard-status.png`} class="mx-auto rounded-lg border border-slate-800 shadow-2xl shadow-ovh-900/40 max-w-full" alt="OVH DynDNS Client dashboard — status page with current IP and host status" />
  </div>
</section>
```

## Step 2 — `HowItWorks.astro`

Three-step explainer. Numbered cards in a grid.

Steps content:
1. **Add a host** — Hostname + OVH DynHost username/password. Stored encrypted at rest with Fernet.
2. **The agent watches your IP** — Polls a public IP service on a configurable interval, persists to SQLite, retries failed hosts on the next cycle.
3. **DNS gets updated** — When the IP changes, OVH receives a DynHost update for every host in parallel. Failures surface in the dashboard with the upstream error.

Sketch:

```astro
<section id="how-it-works" class="mx-auto max-w-6xl px-6 py-16 sm:py-24 border-t border-slate-800">
  <div class="text-center mb-12">
    <h2 class="text-3xl sm:text-4xl font-semibold tracking-tight">How it works</h2>
    <p class="mt-4 text-slate-400 max-w-2xl mx-auto">Three beats from setup to set-and-forget.</p>
  </div>
  <div class="grid gap-8 md:grid-cols-3">
    {/* three numbered cards */}
  </div>
</section>
```

## Step 3 — `FeatureCard.astro`

Reusable card: Lucide-style inline SVG icon + title + 1-2 sentence body.
Mirror nudge's component.

```astro
---
export interface Props { icon: string; title: string; body: string }
const { icon, title, body } = Astro.props
---
<div class="rounded-lg border border-slate-800 bg-slate-900/50 p-6 hover:bg-slate-900/70 transition">
  <div class="text-brand mb-3">
    {/* render Lucide icon path based on `icon` prop */}
  </div>
  <h3 class="text-lg font-semibold">{title}</h3>
  <p class="mt-2 text-sm text-slate-400 leading-relaxed">{body}</p>
</div>
```

The icon prop names match symbols already in `src/static/icons.svg`
(globe, server, shield, refresh-cw, lock, package). Inline a tiny SVG
per icon, or a switch on the prop string. Pick the cheaper path.

## Step 4 — `index.astro` feature grid section

Six cards rendered via `FeatureCard`:

```javascript
const features = [
  { icon: 'globe',     title: 'Web UI',                     body: 'Manage hosts, view status and history from a browser. No CLI required.' },
  { icon: 'server',    title: 'REST API + JWT auth',        body: 'Full-featured API protected by JWT bearer tokens. Use it from your own scripts.' },
  { icon: 'lock',      title: 'Encrypted credentials',      body: 'OVH host passwords are encrypted at rest with Fernet. The data volume is the only thing you back up.' },
  { icon: 'shield',    title: 'Rate-limited auth',          body: '5 logins/min and 10 password-changes/min per IP. Brute-force attempts return 429.' },
  { icon: 'refresh-cw', title: 'Idempotent migration',      body: 'Boot-time auto-migration encrypts legacy plaintext passwords on first start. Zero-touch upgrade from 4.x.' },
  { icon: 'package',   title: 'Docker multi-arch',          body: 'Pre-built images for amd64, arm64 and arm/v7. Runs on a Synology, a Pi, or a cheap VPS.' },
]
```

Render in a `grid gap-6 md:grid-cols-2 lg:grid-cols-3` layout inside a
section with the same border/spacing pattern as nudge.

## Step 5 — `SelfHost.astro`

Bloque copy-pasteable + botón Copy. Reusa el patrón inline-script de
nudge (vanilla JS, no framework).

```astro
<section id="self-host" class="mx-auto max-w-4xl px-6 py-16 sm:py-24 border-t border-slate-800">
  <div class="text-center mb-10">
    <h2 class="text-3xl sm:text-4xl font-semibold tracking-tight">Self-host in 5 minutes</h2>
    <p class="mt-4 text-slate-400 max-w-2xl mx-auto">
      One <code class="rounded bg-slate-800 px-1.5 py-0.5 text-sm text-slate-200">docker-compose.yaml</code>, one <code class="rounded bg-slate-800 px-1.5 py-0.5 text-sm text-slate-200">docker compose up</code>. Full reference in the README.
    </p>
  </div>
  <div class="relative rounded-xl border border-slate-800 bg-slate-950/80 p-6 shadow-xl shadow-ovh-900/20">
    <button
      id="copy-install-snippet"
      type="button"
      class="absolute top-4 right-4 rounded-md border border-slate-700 bg-slate-800/80 px-3 py-1 text-xs font-medium text-slate-300 hover:bg-slate-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand"
    >Copy</button>
    <pre class="overflow-x-auto text-sm leading-relaxed text-slate-200"><code id="install-snippet"># 1. Create docker-compose.yaml
cat > docker-compose.yaml <<'YAML'
services:
  ovh-dyndns-client:
    image: cibrandocampo/ovh-dyndns-client:stable
    container_name: ovh-dyndns-client
    restart: always
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
YAML

# 2. Start it
mkdir -p data
docker compose up -d

# 3. Open http://localhost:8000 (default admin/admin, change required on first login)
</code></pre>
  </div>
  <p class="mt-6 text-center text-sm text-slate-400">
    Full configuration reference:
    <a class="text-brand hover:underline" href="https://github.com/cibrandocampo/ovh-dyndns-client/blob/main/docs/CONFIGURATION.md">docs/CONFIGURATION.md</a>
  </p>
  <script is:inline>
    (function () {
      var btn = document.getElementById('copy-install-snippet')
      var pre = document.getElementById('install-snippet')
      if (!btn || !pre) return
      btn.addEventListener('click', function () {
        var text = pre.textContent || ''
        if (!navigator.clipboard) return
        navigator.clipboard.writeText(text).then(function () {
          var previous = btn.textContent
          btn.textContent = 'Copied ✓'
          setTimeout(function () { btn.textContent = previous || 'Copy' }, 2000)
        })
      })
    })()
  </script>
</section>
```

## Step 6 — `Footer.astro`

```astro
<footer class="border-t border-slate-800 py-10 text-center text-sm text-slate-500">
  <p>
    <a class="hover:text-slate-300 underline-offset-4 hover:underline" href="https://github.com/cibrandocampo/ovh-dyndns-client">GitHub</a>
    <span class="mx-2 text-slate-700">·</span>
    <a class="hover:text-slate-300 underline-offset-4 hover:underline" href="https://hub.docker.com/r/cibrandocampo/ovh-dyndns-client">Docker Hub</a>
    <span class="mx-2 text-slate-700">·</span>
    <a class="hover:text-slate-300 underline-offset-4 hover:underline" href="https://github.com/cibrandocampo/ovh-dyndns-client/blob/main/LICENSE">MIT licence</a>
  </p>
  <p class="mt-3 text-xs text-slate-600">© Cibrán Docampo Piñeiro</p>
</footer>
```

## Step 7 — `index.astro`

Orchestrate the five sections inside `<Base>`:

```astro
---
import Base from '../layouts/Base.astro'
import Hero from '../components/Hero.astro'
import HowItWorks from '../components/HowItWorks.astro'
import FeatureCard from '../components/FeatureCard.astro'
import SelfHost from '../components/SelfHost.astro'
import Footer from '../components/Footer.astro'

const features = [ /* the six items from Step 4 */ ]
---
<Base>
  <Hero />
  <HowItWorks />

  <section id="features" class="mx-auto max-w-6xl px-6 py-16 sm:py-24 border-t border-slate-800">
    <div class="text-center mb-12">
      <h2 class="text-3xl sm:text-4xl font-semibold tracking-tight">Built right, runs anywhere</h2>
      <p class="mt-4 text-slate-400 max-w-2xl mx-auto">No managed SaaS. No vendor lock-in. Your Docker, your DNS.</p>
    </div>
    <div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      {features.map((f) => <FeatureCard icon={f.icon} title={f.title} body={f.body} />)}
    </div>
  </section>

  <SelfHost />
  <Footer />
</Base>
```

## Step 8 — Build and visual verification

```bash
cd site
npm run build
# dist/index.html should now exist with all five sections
ls -la dist/index.html
grep -c "self-host\|How it works\|Built right" dist/index.html
```

Open `site/dist/index.html` in a browser to eyeball the result. Key
visual checks:
- Dark gradient background top-to-bottom
- Hero centered, badges and CTA visible
- Three numbered cards in How it works
- Six feature cards in a 3-column grid
- Self-host snippet renders with the Copy button
- Footer pinned at bottom

The `dashboard-status.png` reference in the Hero will 404 until T018
wires the prebuild hook — that's expected. Build still succeeds; only
the image is missing.

## DoD — Definition of Done

1. Five components exist under `site/src/components/` and parse without Astro errors.
2. `site/src/pages/index.astro` orchestrates them.
3. `npm run build` exits 0.
4. `site/dist/index.html` exists, is non-empty, and contains the literal strings
   "How it works", "Self-host in 5 minutes", "Built right".
5. The Copy button's inline script is present in the built HTML.
6. Visual review (manual): all five sections render in the expected dark theme.

## Evidence to produce

| # | Description | Command | File | PASS condition |
|---|-------------|---------|------|----------------|
| 1 | Component files present | `ls site/src/components/` | `components.txt` | Hero.astro, HowItWorks.astro, FeatureCard.astro, SelfHost.astro, Footer.astro |
| 2 | `astro check` passes | `cd site && npx astro check 2>&1 \| tail -10` | `astro_check.txt` | exit 0, "0 errors" |
| 3 | Build succeeds | `cd site && npm run build 2>&1 \| tail -10` | `build.txt` | exit 0, dist generated |
| 4 | dist/index.html non-empty | `wc -c site/dist/index.html` | `dist_size.txt` | size ≥ 5000 bytes |
| 5 | Sections rendered | `grep -cE 'How it works\|Self-host\|Built right' site/dist/index.html` | `sections.txt` | number ≥ 3 |
| 6 | Copy button JS present | `grep -c 'copy-install-snippet' site/dist/index.html` | `copy_button.txt` | number ≥ 2 (button + script) |
| 7 | Visual review note | manual | `visual-review.md` | one line per section confirming what is visible |

## Files to create/modify

| File | Action |
|------|--------|
| `site/src/components/Hero.astro` | CREATE |
| `site/src/components/HowItWorks.astro` | CREATE |
| `site/src/components/FeatureCard.astro` | CREATE |
| `site/src/components/SelfHost.astro` | CREATE |
| `site/src/components/Footer.astro` | CREATE |
| `site/src/pages/index.astro` | CREATE |

## Execution evidence

**Date**: 2026-05-04
**Modified files**:
- `site/src/components/Hero.astro` — logo, title, tagline, badges, CTA, hero screenshot
- `site/src/components/HowItWorks.astro` — three numbered cards (Add host → Watch IP → Update DNS)
- `site/src/components/FeatureCard.astro` — reusable card with inline Lucide SVG; supports `globe|server|shield|refresh-cw|lock|package`
- `site/src/components/SelfHost.astro` — copy-pasteable docker compose snippet + Copy button + inline JS handler
- `site/src/components/Footer.astro` — three links + copyright (year computed at build time)
- `site/src/pages/index.astro` — replaced T016 placeholder with full orchestration of 5 sections

### Verification table

| # | Deliverable | Evidence file | Result |
|---|-------------|---------------|--------|
| 1 | Component files present | `docs/tasks/evidence/T017/components.txt` | PASS — `Hero.astro`, `HowItWorks.astro`, `FeatureCard.astro`, `SelfHost.astro`, `Footer.astro` |
| 2 | `astro check` passes | `docs/tasks/evidence/T017/astro_check.txt` | PASS — 9 files, 0 errors / 0 warnings / 0 hints |
| 3 | Build succeeds | `docs/tasks/evidence/T017/build.txt` | PASS — `1 page(s) built in 548ms`, `Complete!` |
| 4 | dist/index.html non-empty | `docs/tasks/evidence/T017/dist_size.txt` | PASS — 12 712 bytes |
| 5 | Sections rendered | `docs/tasks/evidence/T017/sections.txt` | PASS — `How it works: 1`, `Self-host: 4`, `Built right: 1` (each ≥ 1) |
| 6 | Copy button JS present | `docs/tasks/evidence/T017/copy_button.txt` | PASS — 2 occurrences (button id + script `getElementById`) |
| 7 | Visual review | `docs/tasks/evidence/T017/visual-review.md` | PASS — five sections + dark gradient confirmed by reading built HTML |

### Design decisions

- **Inline SVGs in `FeatureCard.astro` instead of referencing the `src/static/icons.svg` sprite** — the sprite is served by the FastAPI app at `/static/icons.svg`, not by the static landing site. Of the six icons the feature grid needs (`globe`, `server`, `shield`, `refresh-cw`, `lock`, `package`), only three exist in the sprite anyway (`shield`, `lock`, `package` are absent), so importing the sprite would not have saved work. Inlining keeps the landing self-contained — no extra HTTP request and no coupling to the app's asset pipeline.
- **`<ol>` for the How it works list** — semantically a numbered list, even though the visual numbers are rendered as styled `<div>` badges instead of CSS list-counters. `list-none p-0` strips the default ordered-list rendering so the styled badges read as the numbering.
- **`grep -oF | wc -l` instead of `grep -c`** for the section evidence — Astro builds emit minified HTML where multiple text matches can fall on a single line; `grep -c` returns matching lines and undercounts. The DoD condition is "each marker present", so per-pattern counting is the honest verification.
- **Copyright year computed at build time** (`new Date().getFullYear()`) instead of hardcoded — the build runs on every push to main, so the year stays current without anyone touching the template.
