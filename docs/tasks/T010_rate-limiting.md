# T010 — Rate limiting con `slowapi` en `/api/auth/*`

## Context

`/api/auth/login` no tiene rate limiting: con credenciales por defecto `admin/admin` y bcrypt (rápido en check), un atacante puede iterar contraseñas sin freno. Esta task añade `slowapi` (Flask-Limiter para Starlette/FastAPI) en memoria, configurado por IP, con límites razonables: 5/min en `/login` y 10/min en `/change-password`.

Plan: [docs/plans/security-hardening.md](../plans/security-hardening.md), sección 5.

**Dependencies**: T009 (ambas tasks tocan `routers/auth.py`; encadenadas evitan colisión en mismo fichero).

## Objective

Que el sexto intento de `/api/auth/login` desde una misma IP en menos de un minuto devuelva `429 Too Many Requests`. Igual con `/api/auth/change-password` al undécimo intento.

## Step 1 — Añadir `slowapi` a `requirements.txt`

En el bloque "Authentication" o "API":

```
slowapi~=0.1.9
```

NOTA: rebuild del dev container al final (`docker compose -f dev/docker-compose.yaml build`).

## Step 2 — Configurar `Limiter` en `src/api/main.py`

En la creación del `FastAPI`, antes o después de los `include_router`, añadir el setup de slowapi:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)


def create_app() -> FastAPI:
    application = FastAPI(...)

    # Rate limiting
    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # ... include_router ...
    return application
```

Exportar `limiter` para que el router de auth pueda decorar con él.

## Step 3 — Decoradores en `src/api/routers/auth.py`

Importar el `limiter` desde `api.main` y aplicar:

```python
from fastapi import Request

from api.main import limiter

@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, payload: LoginRequest):
    # NOTA importante: slowapi exige que el primer parámetro sea `request: Request`
    # (lo usa para extraer la IP). El payload pasa a posición 2.
    ...

@router.post("/change-password", response_model=MessageResponse)
@limiter.limit("10/minute")
async def change_password(
    request: Request,
    payload: ChangePasswordRequest,
    current_user: dict = Depends(get_authenticated_user),
):
    ...
```

NOTA crítica: slowapi requiere que la función reciba `Request` como argumento explícito. Si los handlers actuales no lo tienen, hay que añadirlo. **El frontend no necesita cambios** — `Request` lo inyecta FastAPI automáticamente desde la petición HTTP.

## Step 4 — Adaptar firma del request body

Al añadir `request: Request`, el parámetro del body cambia de nombre (era `request: LoginRequest`, ahora es `request: Request` + `payload: LoginRequest`). Renombrar todas las referencias internas:

```python
async def login(request: Request, payload: LoginRequest):
    repository = SqliteRepository()
    user = repository.get_user_by_username(payload.username)  # ← antes era request.username

    if not user or not verify_password(payload.password, user["password_hash"]):
        ...

    access_token = create_access_token(data={"sub": user["username"]})
    ...
```

Mismo cambio en `change_password`: `request.current_password` → `payload.current_password`, etc.

## Step 5 — Tests unitarios — `src/test/test_rate_limit.py`

Crear nuevo fichero. Escenarios:

- `test_login_rate_limit_allows_first_5`: hacer 5 POST a `/api/auth/login` con credenciales inválidas → todas devuelven 401, ninguna 429.
- `test_login_rate_limit_blocks_6th`: el 6º intento devuelve 429.
- `test_change_password_rate_limit_blocks_11th`: 10 intentos OK (con token autenticado), el 11º devuelve 429.

Aislar el `Limiter` entre tests: slowapi guarda contadores en memoria del `app.state.limiter._storage`. En cada test, **resetear el storage**:

```python
@pytest.fixture(autouse=True)
def reset_limiter():
    from api.main import limiter
    limiter.reset()  # API de slowapi para limpiar contadores
    yield
```

Si `limiter.reset()` no funciona en la versión instalada, usar `limiter._storage.reset()` o instanciar un app nuevo por test.

## Step 6 — Verificar manualmente con curl

Tras levantar el dev container:

```bash
for i in 1 2 3 4 5 6; do
  echo "Attempt $i:"
  docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev sh -c \
    "curl -s -o /dev/null -w '%{http_code}\n' \
     -X POST http://localhost:8000/api/auth/login \
     -H 'Content-Type: application/json' \
     -d '{\"username\":\"x\",\"password\":\"x\"}'"
done
```

Esperado: `401 401 401 401 401 429`.

## DoD — Definition of Done

1. `slowapi~=0.1.9` añadido a `requirements.txt` e instalado.
2. `api/main.py` instancia `Limiter` y lo registra en `app.state` + exception handler.
3. `routers/auth.py` decora `login` con `@limiter.limit("5/minute")` y `change_password` con `@limiter.limit("10/minute")`.
4. Las firmas de `login` y `change_password` aceptan `Request` como primer parámetro.
5. El renombrado de `request: LoginRequest` → `payload: LoginRequest` (y similar para change-password) es consistente: ninguna referencia interna sigue usando el viejo nombre.
6. `test_rate_limit.py` cubre los 3 casos listados.
7. Verificación manual con curl: el 6º intento de login devuelve 429.
8. Suite completa pasa con coverage ≥ 90%.

## Evidence to produce

| # | Description | Command | File | PASS condition |
|---|-------------|---------|------|----------------|
| 1 | slowapi instalado | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev pip show slowapi` | `slowapi_pkg.txt` | versión presente >= 0.1.9 |
| 2 | Limiter en main.py | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev sh -c "grep -cE 'Limiter\|RateLimitExceeded' api/main.py"` | `limiter_main.txt` | número >= 2 |
| 3 | Decoradores en routers/auth.py | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev sh -c "grep -cE '@limiter\\.limit' api/routers/auth.py"` | `limit_decorators.txt` | número = 2 |
| 4 | Tests rate limit | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/test_rate_limit.py -v 2>&1` | `test_rl.txt` | exit 0, ≥ 3 tests pass |
| 5 | Curl loop login | (script Step 6) | `curl_login.txt` | última línea = `429`, las cinco anteriores = `401` |
| 6 | Suite completa con coverage | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/ -v --cov=. --cov-fail-under=90 2>&1` | `tests_full.txt` | exit 0, coverage ≥ 90% |
| 7 | Lint | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff check . 2>&1` | `ruff_check.txt` | exit 0 |
| 8 | Format | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff format --check . 2>&1` | `ruff_format.txt` | exit 0 |

## Files to create/modify

| File | Action |
|------|--------|
| `requirements.txt` | MODIFY (añadir `slowapi~=0.1.9`) |
| `dev/dev-requirements.txt` | MODIFY (sync) |
| `src/api/main.py` | MODIFY (instanciar `Limiter`, exception handler, ordenar imports) |
| `src/api/routers/auth.py` | MODIFY (decoradores, `Request` param, rename `request`→`payload`) |
| `src/test/test_rate_limit.py` | CREATE |
| `src/test/conftest.py` | CREATE (autouse fixture que resetea el limiter entre tests) |

## Execution evidence

**Date**: 2026-05-03
**Modified files**:
- `requirements.txt` and `dev/dev-requirements.txt` — added `slowapi~=0.1.9` / `slowapi>=0.1.9`. Dev container rebuilt.
- `src/api/main.py` — instantiates `limiter = Limiter(key_func=get_remote_address)` at module top level, BEFORE the routers import (decorators in `routers/auth.py` reference it at module-load time). Exception handler `_rate_limit_exceeded_handler` and `application.state.limiter = limiter` registered inside `create_app`. The router import has a `# noqa: E402` because it must come after the limiter definition.
- `src/api/routers/auth.py` — login and change-password handlers now take `request: Request` as their first positional argument (slowapi extracts the IP from it) and the JSON body parameter renamed from `request: <Model>` to `payload: <Model>`. All internal references updated. `@limiter.limit("5/minute")` on login, `@limiter.limit("10/minute")` on change-password.
- `src/test/conftest.py` — CREATED. Function-scoped autouse fixture that calls `limiter.reset()` before every test. Without it, prior tests fill the IP bucket (TestClient always issues from `127.0.0.1`) and subsequent tests cannot log in.
- `src/test/test_rate_limit.py` — CREATED. Two test classes:
  - `TestLoginRateLimit` — 3 cases: first 5 wrong logins return 401, the 6th returns 429, and successful logins also burn the budget (limiter is outcome-agnostic).
  - `TestChangePasswordRateLimit` — 1 case: 10 wrong-current-password attempts return 400, the 11th returns 429.

### Verification table

| # | Deliverable | Evidence file | Result |
|---|------------|---------------|--------|
| 1 | `slowapi` installed | `docs/tasks/evidence/T010/slowapi_pkg.txt` | PASS — `Version: 0.1.9` |
| 2 | `Limiter` / `RateLimitExceeded` referenced in `main.py` | `docs/tasks/evidence/T010/limiter_main.txt` | PASS — `5` (≥ 2 required) |
| 3 | Two `@limiter.limit` decorators in `routers/auth.py` | `docs/tasks/evidence/T010/limit_decorators.txt` | PASS — `2` |
| 4 | `test_rate_limit.py` passes | `docs/tasks/evidence/T010/test_rl.txt` | PASS — `4 passed in 6.11s` (3 required minimum) |
| 5 | Live HTTP loop: 6th attempt returns 429 | `docs/tasks/evidence/T010/curl_login.txt` | PASS — `Attempts: [401, 401, 401, 401, 401, 429]` |
| 6 | Full suite + coverage gate (≥ 90%) | `docs/tasks/evidence/T010/tests_full.txt` | PASS — `216 passed`, coverage `95.75%` |
| 7 | `ruff check` clean | `docs/tasks/evidence/T010/ruff_check.txt` | PASS — `All checks passed!` |
| 8 | `ruff format --check` clean | `docs/tasks/evidence/T010/ruff_format.txt` | PASS — `44 files already formatted` |

### Design decisions

- **Limiter defined BEFORE routers import.** First attempt placed `limiter = Limiter(...)` after the `from .routers import ...` line. That triggered a circular-import error (`api.routers.auth` imports `limiter` from a half-loaded `api.main`). Fixed by reordering: limiter is now the first non-import statement in `main.py`, with a `# noqa: E402` comment on the deferred routers import. Could be moved to a dedicated `api/limiter.py` module if more decorators surface, but for two handlers the in-place definition is the lighter touch.
- **`payload` instead of `request` for the body model.** slowapi reaches for `request: Request` to read the client IP via `get_remote_address`. Both handlers used to call their body parameter `request: LoginRequest` / `request: ChangePasswordRequest`. Renamed every internal reference (`request.username` → `payload.username`, etc.) to keep the new positional `request: Request` unambiguous.
- **Pydantic 422 vs slowapi 429 — order matters.** When the JSON body fails Pydantic validation FastAPI returns 422 before the handler runs and slowapi never sees the request. The change-password rate-limit test originally sent `"new_password": "newpw"` (5 chars) which 422'd on `Field(..., min_length=6)` and never consumed the bucket. Switched to `"valid-newpw"` (11 chars) so the request reaches the handler, returns 400 for the wrong current password, and counts toward the limit.
- **`limiter.reset()` in a function-scoped autouse fixture.** Tests using `TestClient` all originate from `127.0.0.1`. Without resetting, the first test of the run could exhaust the bucket and break every subsequent login. The fixture in `conftest.py` runs before every test (including unittest TestCase setUp) and is cheap (in-memory storage).
- **In-memory storage is sufficient for this single-instance service.** Counters reset on every container restart; a determined attacker could just wait or restart, but the goal is mitigating brute-force at human/machine speed, not stopping a slow patient adversary. Multi-instance deployments would need Redis-backed storage — out of scope for this PR; tracked in the plan's "What is NOT included" list.
- **`get_remote_address` sees the proxy IP under a reverse proxy.** Documented as a known limitation (X-Forwarded-For handling is not configured here). For self-hosted single-instance behind nginx/Traefik, the remediation is to make the proxy preserve the client IP — frontend operator's responsibility, not this PR's.
