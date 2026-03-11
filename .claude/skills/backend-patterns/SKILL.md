---
name: backend-patterns
description: Backend architecture patterns and conventions for ovh-dyndns-client. Use when creating or modifying API routes, application services, domain models, or infrastructure adapters. Triggers when working on backend code or when the user asks about project conventions.
---

# Backend Patterns — ovh-dyndns-client

## Architecture

**Hexagonal (ports & adapters)** — strict separation between layers:

```
src/
├── api/            # FastAPI: routers, auth, dependencies (adapters in)
├── application/    # Business logic + port interfaces (use cases)
├── domain/         # Domain models (pure Python, no framework deps)
├── infrastructure/ # Config, logger, OVH client, ipify client, SQLite (adapters out)
├── static/         # Web UI (plain HTML/CSS/JS, no framework)
└── main.py         # Entry point: FastAPI app + APScheduler
```

### Dependency rule

`api` → `application` → `domain` ← `infrastructure`

- `domain` must never import from `api`, `application`, or `infrastructure`.
- `application` must never import from `api` or `infrastructure` directly — it defines **port interfaces** that `infrastructure` implements.
- `api` depends on `application` (calls use cases), never on `infrastructure` directly.

## API layer (`src/api/`)

- **FastAPI** with `APIRouter` per resource (hosts, settings, auth, etc.)
- Auth via **JWT** — use the `get_current_user` dependency on all protected routes
- Routers are registered in the main app at `main.py` or `api/app.py`
- Input validation via **Pydantic** models (request bodies, query params)
- HTTP responses: return Pydantic models or plain dicts; use `JSONResponse` only for special status codes

```python
from fastapi import APIRouter, Depends
from api.dependencies import get_current_user

router = APIRouter(prefix="/hosts", tags=["hosts"])

@router.get("/")
def list_hosts(user=Depends(get_current_user)):
    ...
```

## Application layer (`src/application/`)

- **Use cases** (services): one class or function per use case
- Define **port interfaces** as abstract classes or Protocols
- No framework imports — pure Python
- Receives concrete adapters via dependency injection (constructor or function parameter)

## Domain layer (`src/domain/`)

- **Plain Python dataclasses or classes** — zero framework dependencies
- Encapsulates business rules and invariants
- No I/O, no database calls, no HTTP calls

## Infrastructure layer (`src/infrastructure/`)

- **SQLite** via standard `sqlite3` (or `aiosqlite` if async) — no ORM
- **OVH API client**: updates DNS A records via OVH API
- **ipify client**: fetches current public IP
- **APScheduler**: periodic IP check + DNS update (configured in `main.py`)
- Implements the port interfaces defined in `application/`

## Testing

- **pytest** in `test/` (relative to the project root, maps to `src/test/` in the container at `/app/test/`)
- Run: `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/ -v`
- Minimum coverage: **70%** (enforced in CI)
- Use `httpx.AsyncClient` or FastAPI's `TestClient` for API tests
- Mock external calls (OVH API, ipify) in unit tests — never hit real APIs in tests

### Required for every new feature

1. **Write new tests** covering: happy path, validation errors (400/422), auth (401/403).
2. **Run the full suite** and confirm no regressions.
3. **Update `backend-patterns` SKILL.md** if a new architectural pattern is introduced.

## Formatting & linting

- **ruff** for linting and formatting — config in `src/pyproject.toml`
- Format before committing: `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff format .`
- Lint: `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff check .`
- The pre-commit hook enforces both automatically

## Environment variables

Key vars (set in `dev/docker-compose.yaml` for dev, `.env` for prod):

| Variable | Description |
|----------|-------------|
| `API_PORT` | Port the FastAPI server listens on (default: 8000) |
| `DATABASE_PATH` | SQLite database file path |
| `JWT_SECRET` | Secret for JWT signing |
| `LOGGER_LEVEL` | Log level (`DEBUG`, `INFO`, etc.) |
| `OVH_*` | OVH API credentials (endpoint, app key, secret, consumer key) |

Never hardcode secrets. Read them from env vars via the config module in `infrastructure/`.
