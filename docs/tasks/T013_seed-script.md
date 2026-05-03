# T013 — Seed `scripts/seed.py` + dev compose mount + tests

## Context

Producer-side of the screenshots pipeline. Without realistic fixtures the
dashboard renders empty — useless for README captures and demo. The seed
populates a curated set: 5 hosts (mix of healthy / failed / pending), 1
admin already past the must-change flag, a public IP `1.2.3.4`, default
settings, and ~25 history rows enough to fill 2 pages of the paginated
view.

Plan: [docs/plans/seed-and-screenshots-pipeline.md](../plans/seed-and-screenshots-pipeline.md).

**Dependencies**: None.

## Objective

Ship a Python script under `scripts/seed.py` that, when invoked as
`python /scripts/seed.py [--reset]` inside the dev container, populates
the database with the fixture set defined in the plan. Refuses to
overwrite existing data unless `--reset`. Backed by unit tests that
exercise the happy path, the refusal, and the reset round-trip.

## Step 1 — Mount `scripts/` in the dev container

Edit `dev/docker-compose.yaml` to add a read-only bind mount of the
project-root `scripts/` folder. The dev compose `volumes:` block
currently mounts `../src/:/app` and `./data:/app/data`; add a third
entry mounting the project's `scripts/` folder at `/scripts:ro`:

```yaml
    volumes:
      - ../src/:/app
      - ./data:/app/data
      - ../scripts:/scripts:ro
```

Bind mounts only attach when the container is created. After saving,
`docker compose -f dev/docker-compose.yaml down && up -d` so the new
mount takes effect (no rebuild needed — the image is unchanged).

## Step 2 — Write `scripts/seed.py`

Create `scripts/seed.py` with the following structure (this is a sketch —
implement faithfully but the verbatim layout can vary):

```python
#!/usr/bin/env python3
"""Seed the dev database with realistic fixtures for screenshots/demo."""
import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# `src/` is mounted at /app in the dev container; make it importable.
sys.path.insert(0, str(Path("/app")))

from api.auth import hash_password  # noqa: E402
from infrastructure.database import SqliteRepository, init_db  # noqa: E402
from infrastructure.database.database import get_db_session  # noqa: E402
from infrastructure.database.models import History, Host, Settings, State, User  # noqa: E402
```

**Constants** at the top:

- `ADMIN_USERNAME = "admin"`
- `ADMIN_PASSWORD = "admin"`
- `PUBLIC_IP = "1.2.3.4"`
- `HOSTS = [...]` — five tuples per the plan: `home.example.com` (success
  +5min), `vpn.example.com` (success +10min), `files.example.com`
  (success +1h), `nas.example.com` (failure with auth error, +30min),
  `media.example.com` (pending, no last_update). Ages relative to "now".

**Functions**:

- `seed(reset: bool = False) -> None` — entry. Calls `init_db()`, checks
  emptiness via `_has_data()`, exits non-zero with a clear message if
  data exists and `reset=False`, otherwise wipes and seeds.
- `_has_data() -> bool` — returns True if any of `Host`, `History`,
  `State`, `User` has rows.
- `_wipe() -> None` — `db.query(<Model>).delete()` for History, Host,
  State, Settings, User in this order. The session's commit happens at
  context exit. Does NOT touch `data/.jwt_secret` or
  `data/.encryption_key`.
- Inline seeding logic: admin with `must_change_password=False`,
  `repo.init_default_settings()`, `repo.set_ip(PUBLIC_IP)`,
  `repo.create_host(...)` per `HOSTS`, `repo.update_host_status(...)`
  for the four with non-`None` status, then a manual `db.add(History(...))`
  loop for ~17 synthetic past events that together with the rows already
  written by `set_ip`/`create_host`/`update_host_status` exceed 25 (so
  the paginated view shows two pages at limit=20).

**Manual `last_update` overrides**: `update_host_status` sets
`last_update = now()`. To make the table read "5 minutes ago",
"1 hour ago", etc., override the row's `last_update` directly with
`now - timedelta(minutes=age)` after the status update.

**CLI block** at the bottom:

```python
def main() -> None:
    parser = argparse.ArgumentParser(description="...")
    parser.add_argument("--reset", action="store_true", help="...")
    seed(reset=parser.parse_args().reset)


if __name__ == "__main__":
    main()
```

**Refusal message** when data exists and `--reset` not set must be
printed to `stderr` and exit with `sys.exit(1)`. Suggested wording:

```
Refusing to seed: database already contains data. Re-run with --reset to wipe
and re-seed, or remove data/dyndns.db first.
```

## Step 3 — Write `src/test/test_seed.py`

Create the test file. Pattern: `unittest.TestCase` (matches the rest of
the suite). At the top, insert `scripts/` into `sys.path` so `seed` is
importable from the test:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
```

(`parents[2]` from `src/test/test_seed.py` resolves to the project root.)

`setUpClass` sets a tmp DB and a generated `ENCRYPTION_KEY` env var (the
seed creates hosts which run through `encrypt_password`). `setUp` calls
`init_db()` and wipes every table, so each test starts clean.

Six required cases:

1. `test_seed_creates_expected_rows`: `seed(reset=False)` against a
   clean DB, then count rows: `users == 1`, `hosts == 5`, `state == 1`,
   `settings == 1`, `history >= 25`.
2. `test_admin_must_change_password_is_false`: post-seed, the admin row
   has `must_change_password is False`.
3. `test_includes_failed_host`: at least one `Host` with
   `last_status is False` and a non-null `last_error`.
4. `test_includes_pending_host`: at least one `Host` with
   `last_status is None`.
5. `test_refuses_to_overwrite_without_reset`: seed once, then call
   again without `reset` — assert `SystemExit` is raised.
6. `test_reset_wipes_and_reseeds`: seed once, capture counts, call with
   `reset=True`, counts match (still 5 hosts, no leftovers, no doubles).

## Step 4 — Smoke run inside the dev container

After the script and tests are in place:

```bash
# Make the new compose mount visible.
docker compose -f dev/docker-compose.yaml down
docker compose -f dev/docker-compose.yaml up -d

# Run the seed.
docker compose -f dev/docker-compose.yaml exec --workdir /app \
    -e ENCRYPTION_KEY="$(docker compose -f dev/docker-compose.yaml exec --workdir /app -T ovh-dyndns-dev python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')" \
    ovh-dyndns-dev python /scripts/seed.py --reset

# Quick sanity query against the freshly-seeded DB.
docker compose -f dev/docker-compose.yaml exec --workdir /app ovh-dyndns-dev \
    python -c "from infrastructure.database.database import get_db_session, init_db; from infrastructure.database.models import Host, History, User, State; init_db(); s=get_db_session().__enter__(); print('hosts', s.query(Host).count(), 'history', s.query(History).count(), 'users', s.query(User).count(), 'state', s.query(State).count())"
```

(Real run is part of the evidence; commands above just illustrate.)

## DoD — Definition of Done

1. `scripts/seed.py` exists, is valid Python, executable.
2. `dev/docker-compose.yaml` has the `../scripts:/scripts:ro` mount.
3. `src/test/test_seed.py` exists with the six required cases.
4. Test suite passes (`docker compose -f dev/docker-compose.yaml exec --workdir /app ovh-dyndns-dev python -m pytest test/test_seed.py -v`).
5. Full suite passes with coverage gate ≥ 90%.
6. `ruff check` and `ruff format --check` pass.
7. End-to-end smoke: running the seed against a fresh DB inserts the
   expected row counts, observable via direct SQLAlchemy query.
8. Running the seed twice without `--reset` exits non-zero on the
   second call.

## Evidence to produce

| # | Description | Command | File | PASS condition |
|---|-------------|---------|------|----------------|
| 1 | Seed script exists | `docker compose -f dev/docker-compose.yaml exec --workdir /app ovh-dyndns-dev test -f /scripts/seed.py && echo OK` | `seed_file.txt` | imprime `OK` |
| 2 | Mount declared in compose | `grep -E '/scripts:ro' dev/docker-compose.yaml` | `compose_mount.txt` | match no vacío |
| 3 | Mount visible inside container | `docker compose -f dev/docker-compose.yaml exec --workdir /app ovh-dyndns-dev sh -c "ls -ld /scripts"` | `mount_visible.txt` | dir listed (read-only is acceptable) |
| 4 | test_seed passes | `docker compose -f dev/docker-compose.yaml exec --workdir /app ovh-dyndns-dev python -m pytest test/test_seed.py -v 2>&1` | `test_seed.txt` | exit 0, ≥ 6 tests pass |
| 5 | Full suite + coverage | `docker compose -f dev/docker-compose.yaml exec --workdir /app ovh-dyndns-dev python -m pytest test/ -q --cov=. --cov-fail-under=90 2>&1` | `tests_full.txt` | exit 0, coverage ≥ 90% |
| 6 | Lint clean | `docker compose -f dev/docker-compose.yaml exec --workdir /app ovh-dyndns-dev ruff check .` | `ruff_check.txt` | `All checks passed!` |
| 7 | Format clean | `docker compose -f dev/docker-compose.yaml exec --workdir /app ovh-dyndns-dev ruff format --check .` | `ruff_format.txt` | exit 0 |
| 8 | Live seed run row counts | `docker compose -f dev/docker-compose.yaml exec --workdir /app -T ovh-dyndns-dev python /scripts/seed.py --reset && docker compose -f dev/docker-compose.yaml exec --workdir /app ovh-dyndns-dev python -c "from infrastructure.database.database import get_db_session, init_db; from infrastructure.database.models import Host, History, User; init_db(); s=get_db_session().__enter__(); print('hosts', s.query(Host).count(), 'history', s.query(History).count(), 'users', s.query(User).count())"` | `live_seed.txt` | output shows `hosts 5`, `history >= 25`, `users 1` |
| 9 | Refuses second seed without --reset | `docker compose -f dev/docker-compose.yaml exec --workdir /app -T ovh-dyndns-dev python /scripts/seed.py 2>&1; echo "exit=$?"` | `seed_refusal.txt` | message `Refusing to seed`, `exit=1` |

## Files to create/modify

| File | Action |
|------|--------|
| `scripts/seed.py` | CREATE |
| `dev/docker-compose.yaml` | MODIFY (add mount) |
| `src/test/test_seed.py` | CREATE |

## Execution evidence

**Date**: 2026-05-03
**Modified files**:
- `scripts/seed.py` — CREATED. Public API: `seed(reset=False)`. CLI entry via `main()` exposes `--reset`. Constants: 1 admin (`admin/admin`, `must_change_password=False`), 5 hosts (3 healthy, 1 failed with auth error, 1 pending), `PUBLIC_IP=1.2.3.4`, 17 synthetic history events. Total history rows after seed: 27 (1 from `set_ip` + 5 from `create_host` + 4 from `update_host_status` + 17 manual). Refusal path uses `sys.exit(1)` with a message on stderr. `last_update` overrides bring host timestamps into the relative-past so the dashboard reads "5 minutes ago", "1 hour ago", etc.
- `dev/docker-compose.yaml` — added `../scripts:/scripts:ro` to `volumes:`. Bind mount applied after `compose down && up -d`.
- `src/test/test_seed.py` — CREATED. 6 cases: row counts, admin flag, failed host present, pending host present, refusal without `--reset`, reset round-trip. Uses tmp DB + per-class generated `ENCRYPTION_KEY` so the seed's `encrypt_password` calls don't pollute `/app/data`. `sys.path.insert` lets the test import `seed` from `scripts/` regardless of pytest cwd.

### Verification table

| # | Deliverable | Evidence file | Result |
|---|------------|---------------|--------|
| 1 | `scripts/seed.py` reachable in container | `docs/tasks/evidence/T013/seed_file.txt` | PASS — `OK` |
| 2 | Mount declared in `dev/docker-compose.yaml` | `docs/tasks/evidence/T013/compose_mount.txt` | PASS — `      - ../scripts:/scripts:ro` |
| 3 | `/scripts` visible inside container | `docs/tasks/evidence/T013/mount_visible.txt` | PASS — `drwxr-xr-x ... /scripts` |
| 4 | `test_seed.py` passes | `docs/tasks/evidence/T013/test_seed.txt` | PASS — `6 passed in 2.06s` |
| 5 | Full suite + coverage | `docs/tasks/evidence/T013/tests_full.txt` | PASS — `234 passed`, coverage `96.79%` |
| 6 | `ruff check` clean | `docs/tasks/evidence/T013/ruff_check.txt` | PASS — `All checks passed!` |
| 7 | `ruff format --check` clean | `docs/tasks/evidence/T013/ruff_format.txt` | PASS — `45 files already formatted` |
| 8 | Live seed run row counts | `docs/tasks/evidence/T013/live_seed.txt` | PASS — `hosts 5`, `history 27`, `users 1`, `state 1`, `settings 1` |
| 9 | Refuses second seed without `--reset` | `docs/tasks/evidence/T013/seed_refusal.txt` | PASS — refusal message + `exit=1` |

### Design decisions

- **`sys.path.insert(0, "/app")`** in the seed module's preamble even though the dev container has `PYTHONPATH=/app` from compose. Belt-and-braces — the test suite imports the module directly without going through the container's env, so the explicit `sys.path` keeps it portable. `# noqa: E402` annotates the imports that intentionally come after the path manipulation.
- **`HOSTS` and `HISTORY_EVENTS` as module-level public constants** rather than nested in functions. Lets future tooling import the same fixtures (e.g., a future make target that resets the DB and prints a summary) without duplicating the data.
- **17 synthetic events + 10 from repo calls = 27 total history rows.** Plan asked for ≥25 (two pages at limit=20). Hitting 27 leaves a small but non-trivial second page (7 rows) — enough to show the pagination control as active.
- **Manual `last_update` override after `update_host_status`** rather than monkey-patching `datetime.now()` for the seed run. Update sets `now()`; we then issue a direct SQLAlchemy update to push it into the past. Two queries instead of one but the seed runs in <1s anyway and the code is clearer.
- **Linting fix-up after first run.** Ruff's `I001` flagged the per-test lazy imports (`import seed` followed by `from infrastructure...`) as unsorted. Auto-fixed via `ruff check --fix` — the seed module is imported on its own line before the local `from` imports inside each test method, which is what ruff prefers.
- **Smoke run wrote to the dev volume.** The `make screenshots` flow in T015 will re-seed every time, so the current state of `dev/data/dyndns.db` (5 example.com hosts + the 27 history rows) is the new baseline. If you log in to the dev UI right now, you'll see the seeded data instead of the e2e-test leftovers.
