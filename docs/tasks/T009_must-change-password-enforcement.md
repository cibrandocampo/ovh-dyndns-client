# T009 — Enforcement de `must_change_password` (split de dependencies)

## Context

La bandera `must_change_password` se devuelve al frontend en el response de login pero el backend no bloquea endpoints. Un usuario con credenciales `admin/admin` (default) puede operar la API entera sin cambiar la contraseña: la bandera es decoración. Esta task hace que sea **enforced**: split de la dependency de auth en dos niveles, y solo `/api/auth/change-password` queda accesible mientras la flag siga a `True`.

Plan: [docs/plans/security-hardening.md](../plans/security-hardening.md), sección 4.

**Dependencies**: None (estructuralmente independiente de T006-T008).

## Objective

Que cualquier endpoint protegido distinto de `/api/auth/change-password` devuelva `403 Password change required` cuando el usuario tiene `must_change_password=True`. `/login` sigue sin auth, `/change-password` sigue accesible para que el usuario pueda completar el cambio.

## Step 1 — Refactor de `src/api/dependencies.py`

Renombrar `get_current_user` actual a **`get_authenticated_user`**: la dependency "low-level" que solo verifica el JWT.

Añadir una dependency nueva **`get_current_user`** que envuelve a la anterior y comprueba el flag:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .auth import decode_token
from infrastructure.database import SqliteRepository

security = HTTPBearer()


async def get_authenticated_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Verifica el JWT y devuelve el usuario. NO comprueba must_change_password."""
    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"username": username}


async def get_current_user(
    user: dict = Depends(get_authenticated_user),
) -> dict:
    """Verifica JWT + que la password no esté pendiente de cambio."""
    repository = SqliteRepository()
    if repository.get_user_must_change_password(user["username"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Password change required",
        )
    return user
```

NOTA: `SqliteRepository.get_user_must_change_password` ya existe (`repository.py:269`). Verificar la firma.

## Step 2 — Cambiar dependency en `src/api/routers/auth.py`

El endpoint `change_password` (línea ~48) usa actualmente `get_current_user`. Cambiar a `get_authenticated_user`:

```python
from api.dependencies import get_authenticated_user

@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_authenticated_user),  # ← cambio
):
    ...
```

El resto de routers (`hosts`, `status`, `history`, `settings`) **no cambian**: siguen usando `get_current_user` y heredan automáticamente el nuevo enforcement.

## Step 3 — Verificar que `/api/auth/login` sigue sin dependency

`/login` no debe llevar `Depends(...)` de auth — es el único punto de entrada sin token. Confirmar que el código actual no lo tiene (no debería).

## Step 4 — Tests unitarios — `src/test/test_must_change_password.py`

Crear nuevo fichero con `TestClient` (httpx). Casos a cubrir:

- Setup: crear usuario con `must_change_password=True`, hacer login y obtener token.
- `GET /api/hosts/` con ese token → `403 Password change required`.
- `GET /api/status/` con ese token → `403`.
- `PUT /api/settings/` con ese token → `403`.
- `POST /api/auth/change-password` con ese token + datos válidos → `200 OK` (sigue accesible).
- Tras el cambio, `must_change_password` queda a `False`, y el mismo token (todavía válido por TTL) ya da acceso a `/api/hosts/`. Verificar caso.
- Usuario con `must_change_password=False` (admin que ya cambió) accede normalmente a todos los endpoints (no regresión).

Patrón sugerido (similar a `test_api.py` existente):

```python
from fastapi.testclient import TestClient
from api.main import app, init_admin_user

client = TestClient(app)
```

Aislar la DB con un fichero SQLite temporal (`monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))` + `init_db()`).

## Step 5 — Verificar tests E2E (Playwright)

La suite E2E (`e2e/tests/auth.spec.js`) probablemente cubre el flujo de cambio de password. Verificar que sigue funcionando: con admin/admin (que viene con `must_change_password=True`), el frontend debe redirigir a `/change-password-page` y permitir cambiar. Tras el cambio, acceso normal.

No hace falta correr Playwright en esta task (eso es T005 del otro plan; aquí basta con tests Python). Pero si los tests Python detectan regresión, no continuar.

## DoD — Definition of Done

1. `dependencies.py` exporta dos dependencies: `get_authenticated_user` (solo JWT) y `get_current_user` (JWT + check de must_change_password).
2. Solo `/api/auth/change-password` usa `get_authenticated_user`. Todos los demás endpoints protegidos usan `get_current_user`.
3. `/api/auth/login` sigue sin dependency.
4. `test_must_change_password.py` cubre los 6 casos listados.
5. La suite completa pasa.
6. Cobertura ≥ 90%.
7. Verificación manual del flow: login con usuario `must_change_password=True` → `GET /api/hosts/` devuelve 403, `POST /api/auth/change-password` devuelve 200.

## Evidence to produce

| # | Description | Command | File | PASS condition |
|---|-------------|---------|------|----------------|
| 1 | Dos dependencies definidas | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev sh -c "grep -cE '^async def (get_authenticated_user\|get_current_user)' api/dependencies.py"` | `deps_split.txt` | número = 2 |
| 2 | change_password usa authenticated_user | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev sh -c "grep -A3 'change_password' api/routers/auth.py \| grep get_authenticated_user"` | `change_pw_dep.txt` | match no vacío |
| 3 | Otros routers usan current_user | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev sh -c "grep -c get_current_user api/routers/hosts.py api/routers/status.py api/routers/history.py api/routers/settings.py"` | `routers_dep.txt` | cada fichero >= 1 |
| 4 | Tests must_change_password | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/test_must_change_password.py -v 2>&1` | `test_mcp.txt` | exit 0, ≥ 6 tests pass |
| 5 | Suite completa | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/ -v --cov=. --cov-fail-under=90 2>&1` | `tests_full.txt` | exit 0, coverage ≥ 90% |
| 6 | Lint | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff check . 2>&1` | `ruff_check.txt` | exit 0 |
| 7 | Format | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff format --check . 2>&1` | `ruff_format.txt` | exit 0 |

## Files to create/modify

| File | Action |
|------|--------|
| `src/api/dependencies.py` | MODIFY (split en dos dependencies) |
| `src/api/routers/auth.py` | MODIFY (`change_password` cambia dependency) |
| `src/test/test_must_change_password.py` | CREATE |

## Execution evidence

**Date**: 2026-05-03
**Modified files**:
- `src/api/dependencies.py` — split into two dependencies. `get_authenticated_user` is now the low-level JWT-only check (renamed from the previous `get_current_user`). The new `get_current_user` wraps it and adds the `must_change_password` check, returning HTTP 403 with detail `"Password change required"` when the flag is set. Imports `SqliteRepository` to query the user's flag at every protected request.
- `src/api/routers/auth.py` — `change_password` swapped its dependency from `get_current_user` to `get_authenticated_user` so users in the forced-change flow can still rotate their password. All other routers (`hosts`, `status`, `history`, `settings`) keep using `get_current_user` and inherit the new enforcement automatically.
- `src/test/test_must_change_password.py` — CREATED. 7 tests via FastAPI `TestClient` covering: hosts/status/history endpoints blocked with 403 when the flag is true, settings PUT blocked, change-password allowed and unblocks the token after success, regression test that a user without the flag passes every endpoint.

### Verification table

| # | Deliverable | Evidence file | Result |
|---|------------|---------------|--------|
| 1 | Two dependencies defined | `docs/tasks/evidence/T009/deps_split.txt` | PASS — `2` |
| 2 | `change_password` uses `get_authenticated_user` | `docs/tasks/evidence/T009/change_pw_dep.txt` | PASS — `Depends(get_authenticated_user)` matched |
| 3 | Other routers use `get_current_user` | `docs/tasks/evidence/T009/routers_dep.txt` | PASS — `hosts.py:6`, `status.py:4`, `history.py:2`, `settings.py:3` (all ≥ 1) |
| 4 | `test_must_change_password.py` passes | `docs/tasks/evidence/T009/test_mcp.txt` | PASS — `7 passed in 3.91s` |
| 5 | Full suite + coverage gate (≥ 90%) | `docs/tasks/evidence/T009/tests_full.txt` | PASS — `212 passed`, coverage `95.71%` |
| 6 | `ruff check` clean | `docs/tasks/evidence/T009/ruff_check.txt` | PASS — `All checks passed!` |
| 7 | `ruff format --check` clean | `docs/tasks/evidence/T009/ruff_format.txt` | PASS — `42 files already formatted` |

### Design decisions

- **Dependency-injection composition over mid-handler checks.** The new `get_current_user` simply wraps `get_authenticated_user` via `Depends(...)` and runs the flag check. This means every existing protected route inherits the new enforcement with zero changes to the routes themselves — only the dependency chain changes. Bug-resistant: forgetting to apply enforcement to a new endpoint is impossible as long as it depends on `get_current_user`, which is already the convention.
- **`get_authenticated_user` only on `/api/auth/change-password`.** The change-password endpoint is the single escape hatch from the forced-change state. Anything else that legitimately needs to bypass the flag in the future (e.g., a `/api/auth/me` self-info endpoint?) would also use `get_authenticated_user`. By default, every new route should use `get_current_user`.
- **DB query on every protected request.** `get_current_user` reads `users.must_change_password` from SQLite each time. SQLite is local and the query is `SELECT WHERE username=?` over a tiny table — sub-millisecond. Caching in the JWT itself was rejected: stale tokens after a password change would still be blocked, defeating the test that confirms "after change, same token works". The DB query gives an authoritative, up-to-the-millisecond answer.
- **`detail="Password change required"`** is a deliberate, machine-parseable string. The frontend can switch on it to redirect users to the change-password page automatically.
- **InsecureKeyLengthWarning still appears** because the test secret (`"test-secret-mcp"`) is 15 bytes < 32. Same as previous tasks; will disappear in production with autogenerated 32-byte secrets from T007.
