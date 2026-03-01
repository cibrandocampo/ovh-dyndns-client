---
name: dev-workflow
description: Development environment setup and common commands. Use when setting up the dev environment, running the app locally, or when the user asks about available development commands.
---

# Dev Workflow — ovh-dyndns-client

## Development environment

All development happens inside the `ovh_dyndns_dev` container.
The source code in `src/` is mounted as a volume — changes are immediate, no rebuild needed.

## Start the environment

```bash
docker compose -f dev/docker-compose.yaml up -d
```

Or from `dev/`:
```bash
cd dev && make up
```

## Available commands (Makefile in `dev/`)

| Target | Description |
|---|---|
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

> **Note:** the Makefile uses `docker-compose` (v1 legacy). Direct commands in `CLAUDE.md` use
> `docker compose` (v2 plugin). Both work; prefer the v2 plugin for manual commands.

## Open a shell in the container

```bash
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev bash
```

## Start the application

```bash
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python main.py
```

The app will be available at `http://localhost:8000`.

## Relevant environment variables

Defined in `dev/docker-compose.yaml`:

| Variable | Dev value | Description |
|---|---|---|
| `PYTHONPATH` | `/app` | Python module root |
| `API_PORT` | `8000` | API port |
| `DATABASE_PATH` | `/app/data/dyndns.db` | SQLite database path |
| `JWT_SECRET` | `dev-secret-key-change-in-prod` | JWT secret (dev only) |
| `LOGGER_LEVEL` | `DEBUG` | Log level |

For production, copy `env.example` to `.env` and fill in the real values.

## Project structure

```
src/
├── api/            # FastAPI: routers, auth, dependencies
├── application/    # Business logic + port interfaces
├── domain/         # Domain models
├── infrastructure/ # Config, logger, OVH/ipify clients, SQLite
├── static/         # Web UI (HTML/CSS/JS)
├── test/           # Unit tests (pytest)
└── main.py         # Entry point + scheduler
```
