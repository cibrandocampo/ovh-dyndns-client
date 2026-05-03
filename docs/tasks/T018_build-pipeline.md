# T018 — Prebuild `copy-screenshots.mjs` + Makefile (`site-dev` / `site-build`)

## Context

The Hero component references `screenshots/dashboard-status.png` but
that file lives under `docs/dashboard-status.png` — outside `site/`.
Astro can only serve files from `site/public/`, so we mirror the four
flat `docs/dashboard-*.png` PNGs into `site/public/screenshots/` as a
prebuild hook. Same approach as nudge, simpler (we have four files at a
fixed name pattern, not a recursive subtree).

Also adds two top-level Makefile targets so the operator commands stay
short: `make site-dev` for local hacking, `make site-build` for a
local production-equivalent build.

Plan: [docs/plans/landing-page.md](../plans/landing-page.md), section
"Prebuild hook" + "Makefile (raíz)".

**Dependencies**: T017 (the build needs the components/page to exist
or the Astro build emits a useful site).

## Objective

Wire `site/scripts/copy-screenshots.mjs` so it runs before every
`astro dev` / `astro build`, copying the four `docs/dashboard-*.png`
into `site/public/screenshots/`. Add `site-dev` and `site-build` targets
to the project-root `Makefile` so the build pipeline is one command
each.

## Step 1 — Write `site/scripts/copy-screenshots.mjs`

Adaptation of nudge's hook for our flat layout. Source: `docs/dashboard-*.png`
(no subdirs). Destination: `site/public/screenshots/<file>.png`.

```javascript
#!/usr/bin/env node
/*
 * Prebuild hook: mirror ../docs/dashboard-*.png into ./public/screenshots/
 * so the Astro landing references them via /<base>/screenshots/<file>.
 * Sync mode: stale files in destination are removed.
 */
import { mkdirSync, readdirSync, copyFileSync, rmSync, statSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const SRC = join(__dirname, '..', '..', 'docs')
const DEST = join(__dirname, '..', 'public', 'screenshots')

function listDashboardPngs(dir) {
  const result = new Set()
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (entry.isFile() && entry.name.startsWith('dashboard-') && entry.name.endsWith('.png')) {
      result.add(entry.name)
    }
  }
  return result
}

mkdirSync(DEST, { recursive: true })

const srcFiles = listDashboardPngs(SRC)
let destFiles = new Set()
try {
  destFiles = listDashboardPngs(DEST)
} catch {
  // dest empty, fine
}

let copied = 0
for (const name of srcFiles) {
  copyFileSync(join(SRC, name), join(DEST, name))
  copied += 1
}

let removed = 0
for (const name of destFiles) {
  if (srcFiles.has(name)) continue
  rmSync(join(DEST, name), { force: true })
  removed += 1
}

const suffix = removed > 0 ? ` (removed ${removed} stale)` : ''
console.log(`copy-screenshots: mirrored ${copied} PNG(s) from docs → site/public/screenshots${suffix}`)
```

## Step 2 — Wire the hook into `site/package.json`

Modify `dev` and `build` scripts to run the hook first. The result is
identical to nudge's package.json:

```json
{
  "scripts": {
    "dev": "node scripts/copy-screenshots.mjs && astro dev",
    "build": "node scripts/copy-screenshots.mjs && astro check && astro build",
    "preview": "astro preview",
    "astro": "astro"
  }
}
```

(Only `dev` and `build` get the prefix. `preview` runs against `dist/`
which already has the assets baked in.)

## Step 3 — Add Makefile targets

Append to the project-root `Makefile` (created in T015 with the
`screenshots` target). Two new `.PHONY` targets:

```makefile
.PHONY: help screenshots site-dev site-build

# ... existing screenshots target ...

site-dev:
	@echo "==> Starting Astro dev server on http://localhost:4321/ovh-dyndns-client/"
	cd site && npm run dev

site-build:
	@echo "==> Building Astro landing into site/dist/"
	cd site && npm run build
	@echo "==> Done. site/dist/ is ready for preview or deploy."
```

Update the `help` target output to mention the two new targets:

```makefile
help:
	@echo "Available top-level targets:"
	@echo "  screenshots  Regenerate docs/dashboard-*.png from the seeded dev container"
	@echo "  site-dev     Run the Astro landing dev server (http://localhost:4321/ovh-dyndns-client/)"
	@echo "  site-build   Build the Astro landing into site/dist/"
	@echo ""
	@echo "Per-folder developer shortcuts live in dev/Makefile (build, up, test, lint, ...)."
```

## Step 4 — End-to-end smoke

```bash
make site-build
# Expected: copy-screenshots prints "mirrored 4 PNG(s)", then astro check + build
ls -la site/public/screenshots/   # the four dashboard PNGs
ls -la site/dist/index.html       # built HTML
```

Open `site/dist/index.html` in a browser. The Hero's
`dashboard-status.png` should now load (no 404).

## DoD — Definition of Done

1. `site/scripts/copy-screenshots.mjs` exists and runs without errors
   when invoked directly with `node`.
2. `site/package.json` `dev` and `build` scripts run the hook before
   Astro.
3. `make site-build` runs end-to-end, exits 0, and produces:
   - `site/public/screenshots/dashboard-status.png` (and the other 3)
   - `site/dist/index.html`
4. `make site-dev` boots the dev server (verify it responds 200, then
   stop it).
5. `make help` mentions the two new targets.

## Evidence to produce

| # | Description | Command | File | PASS condition |
|---|-------------|---------|------|----------------|
| 1 | Hook script parses | `node --check site/scripts/copy-screenshots.mjs && echo OK` | `script_parse.txt` | `OK` |
| 2 | Standalone run mirrors 4 PNGs | `node site/scripts/copy-screenshots.mjs` | `hook_run.txt` | output `mirrored 4 PNG(s)` |
| 3 | `site/public/screenshots/` populated | `ls site/public/screenshots/ \| sort` | `mirrored.txt` | exactly: `dashboard-history.png`, `dashboard-hosts.png`, `dashboard-settings.png`, `dashboard-status.png` |
| 4 | Stale removal works | `touch site/public/screenshots/stale.png && node site/scripts/copy-screenshots.mjs && ls site/public/screenshots/ \| grep -c stale` | `stale_removed.txt` | `0` (stale.png gone) |
| 5 | `make site-build` end-to-end | `make site-build 2>&1 \| tail -15` | `make_build.txt` | exit 0, "Done" line, no errors |
| 6 | `dist/index.html` has the dashboard image reference | `grep -c 'dashboard-status.png' site/dist/index.html` | `dist_image_ref.txt` | number ≥ 1 |
| 7 | `make site-dev` boots and serves 200 | `(make site-dev &) && sleep 6 && curl -sf -o /dev/null -w '%{http_code}' http://localhost:4321/ovh-dyndns-client/ ; pkill -f 'astro dev' \|\| true` | `make_dev.txt` | `200` |
| 8 | `make help` lists new targets | `make help` | `make_help.txt` | output mentions `site-dev` and `site-build` |

## Files to create/modify

| File | Action |
|------|--------|
| `site/scripts/copy-screenshots.mjs` | CREATE |
| `site/package.json` | MODIFY (chain hook in `dev` and `build` scripts) |
| `Makefile` | MODIFY (add `site-dev` and `site-build` targets, update `help`) |

## Execution evidence

**Date**: 2026-05-04
**Modified files**:
- `site/scripts/copy-screenshots.mjs` — prebuild hook mirroring `docs/dashboard-*.png` → `site/public/screenshots/` with stale sweep
- `site/package.json` — chained `node scripts/copy-screenshots.mjs` before `astro dev` and `astro check && astro build`
- `Makefile` — added `site-dev` and `site-build` targets; expanded `help` to list both alongside the existing `screenshots` target

### Verification table

| # | Deliverable | Evidence file | Result |
|---|-------------|---------------|--------|
| 1 | Hook script parses | `docs/tasks/evidence/T018/script_parse.txt` | PASS — `OK` |
| 2 | Standalone run mirrors 4 PNGs | `docs/tasks/evidence/T018/hook_run.txt` | PASS — `mirrored 4 PNG(s) from docs → site/public/screenshots` |
| 3 | `site/public/screenshots/` populated | `docs/tasks/evidence/T018/mirrored.txt` | PASS — `dashboard-history.png`, `dashboard-hosts.png`, `dashboard-settings.png`, `dashboard-status.png` |
| 4 | Stale removal works | `docs/tasks/evidence/T018/stale_removed.txt` | PASS — hook reported `(removed 1 stale)`, `grep -c stale` = `0` |
| 5 | `make site-build` end-to-end | `docs/tasks/evidence/T018/make_build.txt` | PASS — `1 page(s) built in 591ms`, `Complete!`, `==> Done.` |
| 6 | `dist/index.html` references the dashboard image | `docs/tasks/evidence/T018/dist_image_ref.txt` | PASS — `1` |
| 7 | `make site-dev` boots and serves 200 | `docs/tasks/evidence/T018/make_dev.txt` | PASS — `200` |
| 8 | `make help` lists new targets | `docs/tasks/evidence/T018/make_help.txt` | PASS — both `site-dev` and `site-build` visible |

### Design decisions

- **Generic dest sweep instead of `dashboard-*.png`-only filter** — the task spec contradicted itself: the example code only swept stale `dashboard-*.png` files, but evidence #4 expects a non-prefixed `stale.png` to be removed. Since `site/public/screenshots/` is fully owned by this hook and is gitignored, sweeping anything no longer in source is the honest implementation of the "Sync mode" promise in the file header. Added a small `listAllFiles` helper for the dest scan; the SRC scan keeps the `dashboard-*.png` filter so we never accidentally pick up unrelated PNGs from `docs/`.
- **No `chmod +x` on the script** — invoked via `node scripts/copy-screenshots.mjs`, never via `./scripts/copy-screenshots.mjs`. The shebang is documentation, not an entry point.
- **`make site-build` builds via `npm run build`, not `astro build` directly** — keeps the prebuild hook chain in one place (`package.json`). If the hook ever needs adjusting, only one entry point changes.
