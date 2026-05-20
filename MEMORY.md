# MEMORY — ovh-dyndns-client

> See `.claude/skills/memory-conventions/SKILL.md` for guidelines on what to record here.
> Keep entries short (one paragraph max). Remove entries that are no longer true.

## Architecture Decisions

- **Decision**: hexagonal architecture (ports & adapters) with strict layer separation: `domain`, `application`, `api`, `infrastructure`. **Why**: the project connects to two external services (OVH API and ipify), which need to be swappable without touching business logic. **Date**: 2024-01.

- **Decision**: SQLite over a client-server database. **Why**: single-process, single-user tool that runs in one Docker container. Operational simplicity outweighs the scalability limitations. **Date**: 2024-01.

- **Decision**: APScheduler for the DNS update loop instead of a cron job. **Why**: allows the update interval to be configured at runtime via the UI without restarting the container. **Date**: 2024-01.

## Gotchas

- **Dev compose file extension**: the dev stack uses `.yaml` (not `.yml`): `dev/docker-compose.yaml`. Commands that use `.yml` will fail silently or fall back to the prod compose.

- **Service name in dev**: the Docker service name is `ovh-dyndns-dev` (hyphen), but the container name is `ovh_dyndns_dev` (underscore). Use the service name with `docker compose exec`; the container name is only for `docker exec`. Always add `-w /app` to `exec` to avoid ruff scanning the Python stdlib instead of the project.

- **Source bind mount**: `dev/docker-compose.yaml` mounts `src/` into the container. Changes to files outside `src/` (e.g., `test/`, root config) are not reflected without a container restart.

- **DISABLE_SCHEDULER**: set `DISABLE_SCHEDULER=1` when running the app in test mode to prevent the background scheduler from interfering with API tests.

- **Password change flow**: the first login always triggers a `must_change_password` redirect. E2E tests must handle this via `Promise.race` or the `login()` helper; plain navigation to `/` will fail.

## Environment

- **Dev credentials**: `admin` / `admin123` (set in `dev/docker-compose.yaml` env block).
- **Dev port**: the app runs on `8000` in both dev and prod containers. No port prefix convention needed (single service).
- **Coverage threshold**: minimum 70% enforced in CI (`--cov-fail-under=70`).

## Recurring Patterns

- **Date.now() in E2E hostnames**: always use `Date.now()` as a suffix when creating hosts in E2E tests to avoid duplicate-key failures across test runs.
- **networkidle before row counts**: always `waitForLoadState('networkidle')` before counting table rows in E2E; the table is loaded asynchronously.
- **Evidence via tee**: all QA command output is saved with `2>&1 | tee docs/tasks/evidence/$TASK_ID/<file>.txt` so it exists both in the terminal and on disk.

## Current Context

<!-- Current project phase, priorities, or constraints affecting ongoing work. -->
