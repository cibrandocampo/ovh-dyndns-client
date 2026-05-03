# T019 — `site-deploy.yml` workflow + verify Pages URL responds 200

## Context

Last piece. With T016–T018 producing a buildable `site/dist/`, the
remaining work is to wire CI so every push to `main` rebuilds and
deploys the landing to GitHub Pages. The user has already enabled
**Settings → Pages → Source: GitHub Actions**, so the runner has the
permissions it needs.

After this task lands and the workflow runs once, the URL
`https://cibrandocampo.github.io/ovh-dyndns-client/` switches from
**HTTP 404** to **HTTP 200** with the rendered landing.

Plan: [docs/plans/landing-page.md](../plans/landing-page.md), section
"Workflow `site-deploy.yml`".

**Dependencies**: T018 (the local build must succeed end-to-end before
trusting CI to do the same).

## Objective

Ship `.github/workflows/site-deploy.yml` mirroring nudge's pattern
(checkout → setup-node → npm ci → npm run build → upload-pages-artifact
→ deploy-pages). After the PR merges, verify the workflow runs to
completion and the public URL serves the landing.

## Step 1 — Write `.github/workflows/site-deploy.yml`

Direct adaptation of nudge's workflow with our path:

```yaml
name: Deploy landing to GitHub Pages

on:
  # Redeploy on every merge to main. No path filter on purpose: build
  # takes <1 min and keeping the site in lock-step with the deployed
  # code is worth the CI minutes.
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

Notes:
- **`actions/checkout@v4`** is the version pinned by the rest of this
  repo's workflows. Nudge uses v6; we stay aligned with the in-repo
  convention.
- **`cache-dependency-path: site/package-lock.json`** keys the npm cache
  to the lockfile, not the repo root.
- **`concurrency: group: pages`** prevents two concurrent deploys
  fighting for the Pages artifact.

## Step 2 — Push the branch and open a PR

The workflow needs to land on `main` to take effect. The merge of this
PR triggers the first `push: main` event.

## Step 3 — Verify the run

After merge, a `Deploy landing to GitHub Pages` workflow run appears
under Actions. Two jobs: `build` then `deploy`. Both should turn green.

```bash
# from local workstation, after merge:
gh run list --workflow=site-deploy.yml --limit 1
# Wait until the latest run is in completed/success state.
```

## Step 4 — Verify the URL

```bash
curl -sf -o /dev/null -w "HTTP %{http_code}\n" https://cibrandocampo.github.io/ovh-dyndns-client/
```

Expected: `HTTP 200` (was 404 before this PR).

Then open the URL in a browser and eyeball:
- Hero with logo, title, badges, CTA, dashboard screenshot.
- How it works with three numbered cards.
- Six feature cards in a grid.
- Self-host snippet with working Copy button (click it, paste somewhere
  to confirm the clipboard got the text).
- Footer with three links (GitHub, Docker Hub, MIT).

## DoD — Definition of Done

1. `.github/workflows/site-deploy.yml` exists at the path shown.
2. The workflow YAML parses (validates via GitHub's lint when pushed;
   no syntax errors visible in the Actions tab).
3. After merge, the workflow run completes successfully (both `build`
   and `deploy` jobs green).
4. `https://cibrandocampo.github.io/ovh-dyndns-client/` responds with
   **HTTP 200** and the served HTML contains the literal string
   "OVH DynDNS Client".
5. The Copy button on the live site works (manual click test).
6. Visual review: all five sections render as expected on the public
   URL.

## Evidence to produce

| # | Description | Command | File | PASS condition |
|---|-------------|---------|------|----------------|
| 1 | Workflow file present | `ls -la .github/workflows/site-deploy.yml` | `workflow_present.txt` | non-zero size |
| 2 | YAML parses (offline validation) | `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/site-deploy.yml'))" && echo OK` | `yaml_parse.txt` | `OK` |
| 3 | Workflow run succeeds (post-merge) | `gh run list --workflow=site-deploy.yml --limit 1 --json status,conclusion` | `run_status.txt` | status `completed`, conclusion `success` |
| 4 | Public URL responds 200 | `curl -sf -o /dev/null -w 'HTTP %{http_code}\n' https://cibrandocampo.github.io/ovh-dyndns-client/` | `url_status.txt` | `HTTP 200` |
| 5 | Live HTML contains expected content | `curl -s https://cibrandocampo.github.io/ovh-dyndns-client/ \| grep -c 'OVH DynDNS Client'` | `live_html.txt` | number ≥ 1 |
| 6 | Live HTML references the screenshots | `curl -s https://cibrandocampo.github.io/ovh-dyndns-client/ \| grep -c 'dashboard-status.png'` | `live_screenshots.txt` | number ≥ 1 |
| 7 | Visual + Copy button manual test | manual | `manual-review.md` | one line confirming the five sections render and Copy works |

NOTE: Evidences 3-7 require the PR to be merged first. The execution
order is: implement workflow → push branch → open PR → review locally
→ merge → run evidences 3-7. The agent doing this task may need to
pause and resume after merge.

## Files to create/modify

| File | Action |
|------|--------|
| `.github/workflows/site-deploy.yml` | CREATE |

## Execution evidence

**Date**: 2026-05-04
**Modified files**:
- `.github/workflows/site-deploy.yml` — Pages deploy workflow: build job runs `npm ci && npm run build` from `site/` and uploads `site/dist/` as a Pages artifact; deploy job consumes that artifact via `actions/deploy-pages@v5`. `concurrency: pages` serializes deploys.

### Verification table

| # | Deliverable | Evidence file | Result |
|---|-------------|---------------|--------|
| 1 | Workflow file present | `docs/tasks/evidence/T019/workflow_present.txt` | PASS — 1042 bytes at the expected path |
| 2 | YAML parses (offline validation) | `docs/tasks/evidence/T019/yaml_parse.txt` | PASS — `OK` (also confirmed structurally: 2 jobs `build`+`deploy`, deploy `needs: build`, permissions and concurrency block intact) |
| 3 | Workflow run succeeds (post-merge) | `docs/tasks/evidence/T019/run_status.txt` | **PENDING-MERGE** — first `push: main` event after the PR merges triggers the run; verify with `gh run list --workflow=site-deploy.yml --limit 1 --json status,conclusion`. |
| 4 | Public URL responds 200 | `docs/tasks/evidence/T019/url_status.txt` | **PENDING-MERGE** — `https://cibrandocampo.github.io/ovh-dyndns-client/` returns 404 until the first deploy completes; recapture after green run with `curl -sf -o /dev/null -w 'HTTP %{http_code}\n' https://cibrandocampo.github.io/ovh-dyndns-client/`. |
| 5 | Live HTML contains expected content | `docs/tasks/evidence/T019/live_html.txt` | **PENDING-MERGE** — `curl -s … \| grep -c 'OVH DynDNS Client'` once the URL resolves. |
| 6 | Live HTML references the screenshots | `docs/tasks/evidence/T019/live_screenshots.txt` | **PENDING-MERGE** — `curl -s … \| grep -c 'dashboard-status.png'`. |
| 7 | Visual + Copy button manual test | `docs/tasks/evidence/T019/manual-review.md` | **PENDING-MERGE** — open the URL, click Copy, paste, confirm the five sections render. |

### Design decisions

- **`actions/checkout@v4`** is the version pinned by the rest of this repo's workflows (`build-on-changes.yml`, `update-python.yml`). Stayed aligned even though nudge uses `@v6`.
- **`cache-dependency-path: site/package-lock.json`** so the npm cache is keyed on the site's lockfile, not the (non-existent) repo-root one.
- **`concurrency: group: pages` with `cancel-in-progress: false`** — Pages deploys are serialized by GitHub regardless, but pinning the group keeps queued runs explicit and prevents two pushes from racing. Not cancelling in progress because the upload→deploy pair should complete atomically once started.
- **`node-version: '22'`** matches the latest LTS Astro recommends. Local dev runs on Node 20.19.4 (Astro 4.16 supports both ≥18.17.1 / ≥20.3.0 / ≥22), so the lockfile is portable across both environments.
- **No `path` filter on `push`** — every merge to `main` redeploys, even if the change is unrelated to `site/`. Build cost is sub-1-min; the value of "deployed site == latest main" outweighs the wasted CI minutes.

### Post-merge follow-up

Items 3–7 are unblockable until this PR lands on `main`. After merge:

```bash
# 3 — wait for the workflow run
gh run list --workflow=site-deploy.yml --limit 1 --json status,conclusion \
  | tee docs/tasks/evidence/T019/run_status.txt
# 4 — URL responds 200
curl -sf -o /dev/null -w 'HTTP %{http_code}\n' https://cibrandocampo.github.io/ovh-dyndns-client/ \
  | tee docs/tasks/evidence/T019/url_status.txt
# 5 — live HTML mentions the product
curl -s https://cibrandocampo.github.io/ovh-dyndns-client/ | grep -c 'OVH DynDNS Client' \
  | tee docs/tasks/evidence/T019/live_html.txt
# 6 — live HTML references the screenshots
curl -s https://cibrandocampo.github.io/ovh-dyndns-client/ | grep -c 'dashboard-status.png' \
  | tee docs/tasks/evidence/T019/live_screenshots.txt
# 7 — manual: open the URL, click Copy, paste somewhere, eyeball the five sections.
```
