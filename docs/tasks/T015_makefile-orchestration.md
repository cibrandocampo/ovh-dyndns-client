# T015 — Orchestration: `Makefile` + `wait-for-health.sh` + regenerated PNGs

## Context

Final piece of the screenshots pipeline. With the seed (T013) and the
capture script (T014) in place, this task wires them under a single
operator command (`make screenshots`) and produces the canonical set of
PNGs that the README links.

The new project-root `Makefile` mirrors nudge's pattern (root-level for
cross-cutting orchestration, while `dev/Makefile` keeps the per-folder
shortcuts). A small shell helper (`scripts/wait-for-health.sh`) breaks
the polling logic out of the Makefile, where shell loops are awkward.

Plan: [docs/plans/seed-and-screenshots-pipeline.md](../plans/seed-and-screenshots-pipeline.md).

**Dependencies**: T013 (seed), T014 (screenshots script).

## Objective

After this task lands, an operator can run `make screenshots` from the
project root and end up with refreshed `docs/dashboard-*.png` ready to
review and commit. The Makefile orchestrates: dev container up, seed
reset, app boot, health wait, capture, app stop.

## Step 1 — Write `scripts/wait-for-health.sh`

Create the file with shebang `#!/usr/bin/env sh` and `chmod +x`:

```sh
#!/usr/bin/env sh
# Block until http://localhost:8000/health responds 200, or fail after $1 seconds (default 30).
TIMEOUT="${1:-30}"
i=0
until curl -sf http://localhost:8000/health > /dev/null 2>&1; do
    i=$((i + 1))
    if [ "$i" -ge "$TIMEOUT" ]; then
        echo "timeout waiting for http://localhost:8000/health" >&2
        exit 1
    fi
    sleep 1
done
echo "ready"
```

POSIX `sh`, runs on the host (macOS or Linux). `curl` is available on
both by default; the dev container's port 8000 is published to the host
via the existing compose mapping.

## Step 2 — Write the project-root `Makefile`

Create `Makefile` (project root, NOT under `dev/`):

```makefile
.PHONY: help screenshots

help:
	@echo "Available top-level targets:"
	@echo "  screenshots  Regenerate docs/dashboard-*.png from the seeded dev container"

screenshots:
	@echo "==> Bringing dev container up..."
	docker compose -f dev/docker-compose.yaml up -d
	@echo "==> Resetting and seeding fixtures..."
	docker compose -f dev/docker-compose.yaml exec --workdir /app -T ovh-dyndns-dev python /scripts/seed.py --reset
	@echo "==> Booting app..."
	docker compose -f dev/docker-compose.yaml exec --workdir /app -d ovh-dyndns-dev python /app/main.py
	@scripts/wait-for-health.sh
	@echo "==> Capturing PNGs..."
	docker run --rm --network host \
		-v $(CURDIR)/e2e/screenshots.mjs:/e2e/screenshots.mjs \
		-v $(CURDIR)/docs:/screenshots \
		ovh-dyndns-e2e node /e2e/screenshots.mjs
	@echo "==> Stopping app (container stays up)..."
	-docker compose -f dev/docker-compose.yaml exec -T ovh-dyndns-dev sh -c "pkill -f 'python /app/main.py' 2>/dev/null"
	@echo "==> Done. Review docs/dashboard-*.png and commit manually."
```

Notes:

- `-` prefix on `pkill` so a non-zero exit (no matching process) does
  not abort the make recipe.
- `$(CURDIR)` is the Make built-in for the directory `make` was invoked
  from — guarantees the right host path even when run via `make -C`.
- `-T` on `exec` disables TTY allocation (required for non-interactive
  execution from a Makefile).
- The recipe assumes `ovh-dyndns-e2e` Docker image is built. If
  missing, the run fails. Document this in `make help` output as a
  prerequisite, OR add a guarded prereq target. Prefer the simpler
  fail-fast for now; a future commit can refine.

## Step 3 — End-to-end run

Once Makefile and helper are in place:

```bash
chmod +x scripts/wait-for-health.sh
make screenshots
```

Expected sequence in the terminal:

```
==> Bringing dev container up...
[ ... compose output ... ]
==> Resetting and seeding fixtures...
Seeded: 1 admin, 5 hosts, ~17 history events, IP=1.2.3.4
==> Booting app...
==> wait-for-health
ready
==> Capturing PNGs...
captured /screenshots/dashboard-status.png
captured /screenshots/dashboard-hosts.png
captured /screenshots/dashboard-history.png
captured /screenshots/dashboard-settings.png
==> Stopping app (container stays up)...
==> Done. Review docs/dashboard-*.png and commit manually.
```

After this, `git status` shows the four PNGs as modified/untracked.
The operator inspects them visually (open in Preview / browser) and
commits manually as part of this task.

## Step 4 — Documentation note in `dev/README.md`

Add a one-line entry under the existing dev README's command index
pointing at `make screenshots` and noting that PNGs land in `docs/`,
must be reviewed before committing.

## DoD — Definition of Done

1. `Makefile` at project root with `screenshots` and `help` targets
   declared `.PHONY`.
2. `scripts/wait-for-health.sh` exists, executable, and exits 0 within
   `$TIMEOUT` seconds when the API is up.
3. `make help` prints the available targets without error.
4. `make screenshots` runs end-to-end without manual intervention and
   produces the four PNGs in `docs/`.
5. The four PNGs are non-empty (> 5 KB), 1280×800 viewport, and
   render the seeded data (visual review).
6. `make screenshots` is idempotent: running twice produces equivalent
   PNGs (modulo timestamps in "X minutes ago" wording, which differ).
7. `dev/README.md` mentions the new target.

## Evidence to produce

| # | Description | Command | File | PASS condition |
|---|-------------|---------|------|----------------|
| 1 | Makefile parses | `make -n screenshots > /dev/null && echo OK` | `make_parse.txt` | `OK` |
| 2 | Help target works | `make help` | `make_help.txt` | output mentions `screenshots` |
| 3 | wait helper executable | `test -x scripts/wait-for-health.sh && echo OK` | `wait_exec.txt` | `OK` |
| 4 | wait helper smoke | run app first, then `scripts/wait-for-health.sh 5` | `wait_smoke.txt` | `ready` within 5s |
| 5 | End-to-end run | `make screenshots 2>&1` | `make_run.txt` | exit 0, "Done" line visible, four `captured` lines |
| 6 | Four PNGs refreshed | `ls -la docs/dashboard-*.png` | `pngs_after.txt` | four files, each ≥ 5000 bytes, mtime within last 5 minutes |
| 7 | Visual review note | manual | `screenshots-review.md` | one line per PNG describing what is visible (e.g. "status shows IP 1.2.3.4 and 5 hosts incl. nas.example.com in red Failed state") |
| 8 | dev README updated | `grep -E 'make screenshots' dev/README.md` | `dev_readme.txt` | match no vacío |

## Files to create/modify

| File | Action |
|------|--------|
| `Makefile` | CREATE (project root) |
| `scripts/wait-for-health.sh` | CREATE (chmod +x) |
| `dev/README.md` | MODIFY (one-liner reference to `make screenshots`) |
| `docs/dashboard-status.png` | OVERWRITE (output) |
| `docs/dashboard-hosts.png` | OVERWRITE (output) |
| `docs/dashboard-history.png` | OVERWRITE / CREATE (output) |
| `docs/dashboard-settings.png` | OVERWRITE (output) |

## Execution evidence

**Date**: 2026-05-03
**Modified files**:
- `Makefile` — CREATED at project root. Single `screenshots` target plus `help` and `.PHONY`. Sequence: bring dev container up → `seed.py --reset` → boot app with `DISABLE_SCHEDULER=1` → `wait-for-health.sh` → `docker run` Playwright capture mounting the script and `docs/` → stop the app. Per-folder shortcuts stay in `dev/Makefile`. Hyphens vs underscores in compose service name handled per project memory.
- `scripts/wait-for-health.sh` — CREATED, mode `0755`. POSIX `sh`, polls `http://localhost:8000/health` with `curl -sf` once per second. Default timeout 30s; first arg overrides. Exits non-zero with a clear stderr message on timeout.
- `dev/README.md` — added a "Project-root targets" subsection pointing operators to the new `make screenshots`. Notes that `dev/data` is wiped via `--reset` and that the operator must review the PNGs and commit manually.
- `docs/dashboard-*.png` — four PNGs refreshed by `make screenshots` end-to-end at the seeded state.

### Verification table

| # | Deliverable | Evidence file | Result |
|---|------------|---------------|--------|
| 1 | Makefile parses (`make -n screenshots`) | `docs/tasks/evidence/T015/make_parse.txt` | PASS — `OK` |
| 2 | `make help` works | `docs/tasks/evidence/T015/make_help.txt` | PASS — output mentions `screenshots` |
| 3 | wait helper executable | `docs/tasks/evidence/T015/wait_exec.txt` | PASS — `OK` |
| 4 | wait helper smoke against running app | `docs/tasks/evidence/T015/wait_smoke.txt` | PASS — `ready` within 10s |
| 5 | End-to-end `make screenshots` run | `docs/tasks/evidence/T015/make_run.txt` | PASS — exit 0, "Done" line, four `captured` lines, no errors |
| 6 | Four PNGs refreshed | `docs/tasks/evidence/T015/pngs_after.txt` | PASS — 28-91 KB each, mtime within run window |
| 7 | Visual review note | `docs/tasks/evidence/T015/screenshots-review.md` | PASS — content matches the seed |
| 8 | dev README mentions the target | `docs/tasks/evidence/T015/dev_readme.txt` | PASS — `make screenshots` line found |

### Design decisions

- **`DISABLE_SCHEDULER=1` propagated through the Makefile**, not just used ad-hoc. The env var was introduced in T014 to keep the seed stable; the Makefile makes the use of it the canonical path. Without it, the scheduler clobbers the seed within seconds and the resulting PNGs are useless.
- **Project-root `Makefile` lives separately from `dev/Makefile`.** Per the plan, this is mirroring nudge's layout: cross-cutting orchestration at root, per-folder shortcuts in `dev/`. `make help` at root explicitly tells operators where the dev shortcuts are. No existing target was moved.
- **wait helper runs on the host, not inside the container.** Two reasons: (1) the host has `curl` available on macOS and Linux; (2) keeps the polling logic out of the Makefile, where shell loops are awkward. The dev container's port 8000 is already published to the host so the URL `http://localhost:8000/health` reaches uvicorn through the existing port mapping.
- **`-T` flag on `docker compose exec`** disables TTY allocation, required for non-interactive execution from a Makefile recipe — without it, GNU Make sees garbled output in some terminals.
- **`-` prefix on the `pkill` line** prevents Make from aborting the recipe when no `python /app/main.py` process is running. Idempotent shutdown.
- **Visual diff workflow**: `make screenshots` deliberately stops short of staging or committing. The operator reviews the PNGs (the four are the only files that should change in `git status`) and commits them manually, alongside any other intentional changes. The plan called this out explicitly; the recipe's final line spells it out.
