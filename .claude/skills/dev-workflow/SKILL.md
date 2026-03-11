---
name: dev-workflow
description: Development workflow and Docker commands for ovh-dyndns-client. Use when setting up the environment, running tests, linting, or debugging containers. Triggers when the user asks about development setup, Docker, or available commands.
---

# Development Workflow — ovh-dyndns-client

## Golden Rule

**NEVER run Python directly on the host.**
Always use `dev/docker-compose.yaml` — it uses bind mounts so local file changes
are reflected instantly without rebuilding.

The root `docker-compose.yaml` is for **production** (uses the published Docker Hub image).

## Start / Stop

```bash
docker compose -f dev/docker-compose.yaml up -d      # Start dev container
docker compose -f dev/docker-compose.yaml down        # Stop
docker compose -f dev/docker-compose.yaml ps          # Check status
```

## Services

| Service | Port | Purpose |
|---------|------|---------|
| `ovh_dyndns_dev` | 8000 | FastAPI dev server + source bind mount |

The app is available at `http://localhost:8000`.

## Common commands

```bash
# Shell
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev bash

# Run the application
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python main.py

# Tests
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/ -v
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/test_api.py -v            # one file
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/test_api.py::TestClass::test_method -v  # one test

# Tests with coverage
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/ --cov=. --cov-report=term-missing
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/ --cov=. --cov-report=term-missing --cov-fail-under=70

# Lint & format
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff check .
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff format --check .
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff format .
```

## Makefile shortcuts (from `dev/`)

| Target | Description |
|--------|-------------|
| `make build` | Build the dev image |
| `make up` | Start the container in the background |
| `make down` | Stop the container |
| `make shell` | Open a shell in the container |
| `make test` | Run tests |
| `make lint` | Ruff check (linting) |
| `make format` | Ruff format (apply formatting) |
| `make logs` | Show container logs |
| `make clean` | Remove containers and dev image |
| `make run` | Start the application in dev mode |

> The Makefile uses `docker-compose` (v1 legacy). Direct commands above use `docker compose` (v2 plugin). Both work; prefer v2 for manual commands.

## Quick API verification

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health    # 200
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/hosts     # 401
```

## E2E tests (Playwright — Docker, NOT host)

Playwright runs in its own Docker image. Use `--network host` so the container
can reach the app at `localhost:8000`. Requires the dev app running first.

**Build image** (only once, or after changing `e2e/package.json`):
```bash
docker build -f e2e/Dockerfile -t ovh-dyndns-e2e ./e2e
```

**Run all tests:**
```bash
docker run --rm --network host \
  -e E2E_USERNAME=admin \
  -e E2E_PASSWORD=admin123 \
  ovh-dyndns-e2e npx playwright test
```

**Run a specific spec:**
```bash
docker run --rm --network host \
  -e E2E_USERNAME=admin \
  -e E2E_PASSWORD=admin123 \
  ovh-dyndns-e2e npx playwright test tests/auth.spec.js
```

Default dev credentials: `admin` / `admin123` (set in `dev/docker-compose.yaml`).

## Environment variables

Defined in `dev/docker-compose.yaml` for dev, `.env` for prod:

| Variable | Dev value | Description |
|----------|-----------|-------------|
| `PYTHONPATH` | `/app` | Python module root |
| `API_PORT` | `8000` | API port |
| `DATABASE_PATH` | `/app/data/dyndns.db` | SQLite database path |
| `JWT_SECRET` | `dev-secret-key-change-in-prod` | JWT secret (dev only) |
| `LOGGER_LEVEL` | `DEBUG` | Log level |

For production, copy `env.example` to `.env` and fill in the real values.
