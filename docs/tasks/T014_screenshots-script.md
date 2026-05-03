# T014 — Playwright screenshot capture (`e2e/screenshots.mjs`)

## Context

Consumer side of the screenshots pipeline. With the seed in place
(T013), Playwright can drive a real browser through the dashboard and
produce the four canonical PNGs the README references. The script
mirrors what `e2e/tests/*.spec.js` already does, but with a single
purpose: capture, not assert.

Plan: [docs/plans/seed-and-screenshots-pipeline.md](../plans/seed-and-screenshots-pipeline.md).

**Dependencies**: T013 (the seed populates realistic data; screenshots
against an empty DB look broken).

## Objective

Ship `e2e/screenshots.mjs`, a Playwright ESM script that, when run
inside the existing `ovh-dyndns-e2e` Docker image with the dev API
reachable on `host` network, captures four screens at viewport
1280×800 and writes them to a mounted output directory:

- `dashboard-status.png`
- `dashboard-hosts.png`
- `dashboard-history.png`
- `dashboard-settings.png`

## Step 1 — Write `e2e/screenshots.mjs`

Create the file. Outline (faithful but exact wording can vary):

```javascript
#!/usr/bin/env node
import { chromium } from '@playwright/test'
import { mkdir } from 'fs/promises'
import { join } from 'path'

const BASE_URL = process.env.BASE_URL ?? 'http://localhost:8000'
const USERNAME = process.env.E2E_USERNAME ?? 'admin'
const PASSWORD = process.env.E2E_PASSWORD ?? 'admin'
const OUT = process.env.SCREENSHOTS_DIR ?? '/screenshots'

async function login(page) { /* ... */ }
async function shoot(page, name) { /* ... */ }

const browser = await chromium.launch()
const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } })
const page = await ctx.newPage()
await mkdir(OUT, { recursive: true })

await login(page)
// status (default landing after login)
await page.locator('#status-section').waitFor({ state: 'visible' })
await shoot(page, 'dashboard-status')
// hosts
await page.locator('.nav-link[data-section="hosts"]').click()
await page.locator('#hosts-section').waitFor({ state: 'visible' })
await shoot(page, 'dashboard-hosts')
// history
await page.locator('.nav-link[data-section="history"]').click()
await page.locator('#history-section').waitFor({ state: 'visible' })
await shoot(page, 'dashboard-history')
// settings
await page.locator('.nav-link[data-section="settings"]').click()
await page.locator('#settings-section').waitFor({ state: 'visible' })
await shoot(page, 'dashboard-settings')

await browser.close()
```

`login()` mirrors the helper at `e2e/tests/helpers.js` but **does NOT**
need to handle the `must_change_password` redirect, because the seed
sets the admin's flag to `False`. If the redirect ever happens (manual
DB tinkering), throw a clear error rather than silently continue.

`shoot()` calls `page.waitForLoadState('networkidle')` and a small
debounce (`page.waitForTimeout(300)`) before the screenshot to let
fonts settle. Captures `fullPage: false` (viewport only — the seeded
data fits comfortably; full-page would add empty whitespace below).

## Step 2 — Header docstring

The file's leading comment block must explain:

- What it captures and where it writes (use the same wording as the
  plan: four scenes, viewport 1280×800).
- Required env vars (`BASE_URL`, `E2E_USERNAME`, `E2E_PASSWORD`,
  `SCREENSHOTS_DIR`) with defaults.
- Run command for manual invocation:
  ```
  docker run --rm --network host \
    -v "$(pwd)/e2e/screenshots.mjs":/e2e/screenshots.mjs \
    -v "$(pwd)/docs":/screenshots \
    ovh-dyndns-e2e node /e2e/screenshots.mjs
  ```
- Note that the seeded admin (`admin`/`admin` with
  `must_change_password=False`) is the expected state.

## Step 3 — Smoke verification

The full smoke (dev container up → seed --reset → boot app → run
screenshots) is the responsibility of T015's Makefile. For T014,
verify by running the pieces manually:

1. Confirm `ovh-dyndns-e2e` image exists; build if not (`docker build
   -f e2e/Dockerfile -t ovh-dyndns-e2e ./e2e`).
2. Confirm the dev container is up and the seed has run (T013).
3. Boot the app (`docker compose ... exec -d ... python /app/main.py`)
   and wait for `/health`.
4. Mount-and-run the screenshots script. Confirm the four PNGs land in
   `docs/dashboard-*.png`, are non-empty, and visually match the seeded
   data (5 hosts in Hosts, current IP `1.2.3.4` in Status, populated
   History with the dropdown, version footer in Settings).
5. Stop the app.

## DoD — Definition of Done

1. `e2e/screenshots.mjs` exists and is valid Node ESM.
2. Manual run produces the four PNGs in the mounted output directory.
3. Each PNG is non-empty (> 5 KB) and viewport-sized (1280×800
   approximately, allowing for image-format overhead).
4. The four PNGs render the seeded data (visual review — included
   under Evidence file `screenshots-review.md` as a short note).
5. Script does not modify any data on the dev container (read-only
   navigation; no clicking on Add Host / Force Update / etc.).

## Evidence to produce

| # | Description | Command | File | PASS condition |
|---|-------------|---------|------|----------------|
| 1 | Script exists and parses | `node --check e2e/screenshots.mjs && echo OK` | `script_parse.txt` | `OK` |
| 2 | E2E image present | `docker images --format '{{.Repository}}:{{.Tag}}' \| grep ovh-dyndns-e2e` | `e2e_image.txt` | match no vacío |
| 3 | App health pre-capture | `curl -sf http://localhost:8000/health` | `health.txt` | `{"status":"healthy"}` |
| 4 | Capture run | `docker run --rm --network host -v "$(pwd)/e2e/screenshots.mjs":/e2e/screenshots.mjs -v "$(pwd)/docs":/screenshots ovh-dyndns-e2e node /e2e/screenshots.mjs 2>&1` | `capture_log.txt` | exit 0, four `captured` lines |
| 5 | Four PNGs created with non-zero size | `ls -la docs/dashboard-status.png docs/dashboard-hosts.png docs/dashboard-history.png docs/dashboard-settings.png` | `pngs_size.txt` | each file ≥ 5000 bytes |
| 6 | Visual review note | manual; written by hand into the file | `screenshots-review.md` | three lines: status shows IP `1.2.3.4` and 5 hosts; hosts table shows the 5 example.com entries; settings footer shows the version string (not blank). |
| 7 | Lint not regressed | `docker compose -f dev/docker-compose.yaml exec --workdir /app ovh-dyndns-dev ruff check .` | `ruff_check.txt` | `All checks passed!` |

## Files to create/modify

| File | Action |
|------|--------|
| `e2e/screenshots.mjs` | CREATE |
| `src/main.py` | MODIFY (`DISABLE_SCHEDULER=1` env-var guard around the scheduler thread — required to keep the seed state stable during capture) |
| `docs/dashboard-status.png` | OVERWRITE (output of the run) |
| `docs/dashboard-hosts.png` | OVERWRITE |
| `docs/dashboard-history.png` | CREATE (new scene; replaces nothing) |
| `docs/dashboard-settings.png` | OVERWRITE |

## Execution evidence

**Date**: 2026-05-03
**Modified files**:
- `e2e/screenshots.mjs` — CREATED. ESM Playwright script. Logs in via the seeded `admin/admin` (the seed sets `must_change_password=False` so it lands on the dashboard directly), navigates the four sections, captures viewport-only PNGs at 1280x800. `networkidle` + 300ms debounce before each shot to let fonts and async fetches settle. Read-only navigation — no Add Host / Force Update / Delete clicks.
- `src/main.py` — MODIFIED. Wrapped the scheduler thread launch in an `os.getenv("DISABLE_SCHEDULER") == "1"` guard. When set, the scheduler is skipped and the API is served by uvicorn alone. Required for screenshots: without it the scheduler runs `controller.handler()` immediately on app start, refreshes the IP from ipify (clobbering the seed's `1.2.3.4`), and tries to update every host via OVH with the seed's fake credentials — turning every host into a `Failed / HTTP 401` entry seconds before capture. Side benefit: easier API debugging without scheduler log noise.
- `docs/dashboard-*.png` — four PNGs regenerated against the seeded state.

### Verification table

| # | Deliverable | Evidence file | Result |
|---|------------|---------------|--------|
| 1 | Script parses as Node ESM | `docs/tasks/evidence/T014/script_parse.txt` | PASS — `OK` |
| 2 | E2E Docker image present | `docs/tasks/evidence/T014/e2e_image.txt` | PASS — `ovh-dyndns-e2e:latest` |
| 3 | App health pre-capture | `docs/tasks/evidence/T014/health.txt` | PASS — `{"status":"healthy"}` |
| 4 | Capture run | `docs/tasks/evidence/T014/capture_log.txt` | PASS — four `captured` lines + `done` |
| 5 | Four PNGs created with non-zero size | `docs/tasks/evidence/T014/pngs_size.txt` | PASS — 28 KB / 49 KB / 65 KB / 88 KB (all ≥ 5 KB) |
| 6 | Visual review note | `docs/tasks/evidence/T014/screenshots-review.md` | PASS — manual notes match the seeded state |
| 7 | Lint not regressed | `docs/tasks/evidence/T014/ruff_check.txt` | PASS — `All checks passed!` |
| 8 | Backend tests still green (regression for main.py guard) | inline | PASS — `234 passed in 32.54s` |

### Design decisions

- **`DISABLE_SCHEDULER` env var added to `src/main.py`.** Out of the original T014 scope, but required to make the screenshots actually reflect the seed. Without it, the scheduler runs `controller.handler()` on the first tick (immediately at boot, no delay), which queries ipify for the real public IP, calls `set_ip()` (overwriting `1.2.3.4`), then fans out to OVH for every host with the fake-credentials seed and writes `last_status=False` / `last_error="HTTP 401: Unauthorized"` for all five — clobbering the carefully-seeded mix of healthy/failed/pending. The first capture I ran demonstrated this: every host turned red within seconds. The env-var guard is small (4 lines), backwards-compatible (default behaviour unchanged), and useful beyond screenshots (debug an API without scheduler noise).
- **`fullPage: false`** for screenshots. The seeded data fits comfortably in 1280x800; full-page would add a long whitespace tail below the cards (status section content stops at ~750px tall).
- **Visual change-password guard.** The login helper does `Promise.race` between `#dashboard` and `#change-password-page` and throws if the latter wins. Rather than silently capture the wrong screen, fail loud — a clear remediation message that points to re-seeding.
- **Read-only navigation.** The script never clicks destructive controls. Running it does not modify the dev DB. Re-running is idempotent except for the timestamp drift on relative-time fields ("5 minutes ago" → "6 minutes ago" if the next run happens later).
- **Seed-then-boot ordering matters.** If you boot the app first (with scheduler enabled) and then seed, the seed's `set_ip(1.2.3.4)` will be overwritten by the scheduler's next tick. The Makefile in T015 will enforce: seed → boot-with-DISABLE_SCHEDULER=1 → wait → capture → stop.
