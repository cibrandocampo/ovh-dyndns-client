# Development Guide

## Requirements

- Docker and Docker Compose installed on your machine.
- No Python, pip, or any other tool required on the host.

## Start the environment

```bash
docker compose -f dev/docker-compose.yaml up -d
```

The `ovh_dyndns_dev` container mounts `src/` as a volume — local file changes are visible inside the container instantly, no rebuild needed.

The app will be available at **http://localhost:8000**.

## Common commands

```bash
# Open a shell in the container
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev bash

# Run the application
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python main.py

# Run tests
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/ -v

# Run tests with coverage
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/ --cov=. --cov-report=term-missing

# Lint
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff check .

# Check formatting
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff format --check .

# Apply formatting
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff format .
```

### Makefile shortcuts (from `dev/`)

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

## Pre-commit hook

Install the pre-commit hook to run linters automatically before each commit:

```bash
bash scripts/install-hooks.sh
```

The hook runs `ruff check` and `ruff format --check` inside the dev container. The dev environment must be running for it to work.

If the hook fails, fix the issue and create a **new commit** — never `--amend`.

## E2E tests (Playwright)

End-to-end tests run in a separate Docker image and use `--network host` to reach the app at `localhost:8000`. The dev app must be running first.

```bash
# Build the E2E image (only once, or after changing e2e/package.json)
docker build -f e2e/Dockerfile -t ovh-dyndns-e2e ./e2e

# Run all tests
docker run --rm --network host \
  -e E2E_USERNAME=admin \
  -e E2E_PASSWORD=admin123 \
  ovh-dyndns-e2e npx playwright test

# Run a specific spec
docker run --rm --network host \
  -e E2E_USERNAME=admin \
  -e E2E_PASSWORD=admin123 \
  ovh-dyndns-e2e npx playwright test tests/auth.spec.js
```

Default dev credentials: `admin` / `admin123` (set in `dev/docker-compose.yaml`).

## Project structure

```
src/
├── api/                          # FastAPI: routers, auth, dependencies
│   ├── main.py                   # FastAPI application setup
│   ├── auth.py                   # JWT authentication
│   ├── dependencies.py           # Shared API dependencies
│   └── routers/                  # One file per resource
│       ├── auth.py               # Authentication endpoints
│       ├── hosts.py              # Hosts CRUD
│       ├── status.py             # Status and manual trigger
│       ├── history.py            # History log
│       └── settings.py           # Settings management
├── application/                  # Business logic + port interfaces
│   ├── controller.py             # Main orchestrator (use case)
│   └── ports/                    # Abstract interfaces
│       ├── dns_updater.py        # DNS update port
│       ├── hosts_repository.py   # Hosts repository port
│       ├── ip_provider.py        # IP provider port
│       └── ip_state_store.py     # IP state storage port
├── domain/                       # Domain models — pure Python, no framework deps
│   └── hostconfig.py             # Host configuration model
├── infrastructure/               # Concrete adapters (implements ports)
│   ├── clients/
│   │   ├── ipify_client.py       # Implements IpProvider
│   │   └── ovh_client.py         # Implements DnsUpdater
│   ├── database/
│   │   ├── models.py             # SQLAlchemy models
│   │   ├── database.py           # Database connection
│   │   └── repository.py        # Implements IpStateStore & HostsRepository
│   ├── config.py                 # Environment configuration
│   └── logger.py                 # Logging system
├── static/                       # Web UI — plain HTML/CSS/JS, no framework
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
├── test/                         # Unit tests (pytest)
└── main.py                       # Entry point: wires dependencies + starts scheduler
```

## Architecture

The application uses **hexagonal architecture** (ports and adapters). The dependency rule is strict: inner layers never import from outer layers.

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (HTML/JS)                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  API layer  (FastAPI)                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Application layer  (Controller + Ports)        │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   SQLite        │ │   Ipify         │ │   OVH API       │
│   Repository    │ │   Client        │ │   Client        │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

**Ports** — abstract interfaces in `application/ports/`: `IpProvider`, `DnsUpdater`, `IpStateStore`, `HostsRepository`

**Adapters** — concrete implementations in `infrastructure/`: `IpifyClient`, `OvhClient`, `SqliteRepository`

**Wiring** — `main.py` instantiates adapters and injects them into the application layer.

This makes every adapter independently mockable in tests, and swappable without touching business logic.

## Database schema

```sql
CREATE TABLE users (
    id            INTEGER PRIMARY KEY,
    username      TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    must_change_password BOOLEAN DEFAULT TRUE
);

CREATE TABLE hosts (
    id          INTEGER PRIMARY KEY,
    hostname    TEXT UNIQUE NOT NULL,
    username    TEXT NOT NULL,
    password    TEXT NOT NULL,
    last_update DATETIME,
    last_status BOOLEAN,
    last_error  TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE state (
    id         INTEGER PRIMARY KEY DEFAULT 1,
    current_ip TEXT,
    last_check DATETIME
);

CREATE TABLE history (
    id        INTEGER PRIMARY KEY,
    ip        TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    action    TEXT,
    hostname  TEXT,
    details   TEXT
);

CREATE TABLE settings (
    id              INTEGER PRIMARY KEY DEFAULT 1,
    update_interval INTEGER DEFAULT 300,
    logger_level    TEXT DEFAULT 'INFO'
);
```

## Adding new features

Follow the hexagonal architecture:

1. **New port** — add an abstract interface in `src/application/ports/`
2. **New adapter** — implement the port in `src/infrastructure/`
3. **New API endpoint** — add a router in `src/api/routers/`, register it in `src/api/main.py`
4. **New database model** — add to `src/infrastructure/database/models.py`
5. **Wire it up** — inject the new adapter in `main.py`

Always write tests for new code. The CI coverage gate is 90%.

## Claude Code

This project is developed with [Claude Code](https://claude.ai/code), Anthropic's AI coding assistant.

Custom skills are provided in `.claude/skills/` to help Claude understand project conventions, and custom commands in `.claude/commands/` to support a structured development workflow.

### Skills

| Skill | Purpose |
|-------|---------|
| `backend-patterns` | Hexagonal architecture, FastAPI patterns, SQLite, testing conventions |
| `dev-workflow` | Docker commands, environment setup, test and lint commands |
| `git-conventions` | Commit message format, branch naming, pre-commit hook |

### Commands

| Command | Purpose |
|---------|---------|
| `/dev-1-plan` | Plan a new feature — produces a design doc in `docs/plans/` |
| `/dev-2-tasks` | Break an approved plan into executable task files in `docs/tasks/` |
| `/dev-3-run` | Implement a single task with full DoD verification and evidence |
| `/dev-4-qa` | Forensic QA — independent re-verification, produces APPROVED or RETURNED |
| `/push` | Update docs, commit, create PR, and verify the CI pipeline |
| `/fix` | Focused bug fix or small change — lightweight path straight to `/push` |
| `/audit` | Structured audit of a code area — find inconsistencies, propose and apply fixes |

The `dev-1-plan` → `dev-2-tasks` → `dev-3-run` → `dev-4-qa` → `push` pipeline ensures every feature is planned, implemented, independently verified, and CI-green before merging.
