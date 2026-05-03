# T007 — Módulo `infrastructure/secrets.py` (auto-generar JWT_SECRET y ENCRYPTION_KEY)

## Context

El `JWT_SECRET` actual tiene fallback inseguro: si la env var no se define, `auth.py` usa el literal `"change-this-secret-in-production"` y cualquiera puede forjar tokens. Esta task introduce gestión de secrets **persistidos en `data/`**, autogenerados al primer arranque, validados en cada arranque.

Mismo módulo gestiona la `ENCRYPTION_KEY` que T008 consumirá para cifrar las passwords OVH.

Plan: [docs/plans/security-hardening.md](../plans/security-hardening.md), sección 2.

**Dependencies**: T006 (PyJWT ya migrado; T007 modifica `auth.py` y se asume que el swap de librería ya está hecho).

## Objective

Crear `src/infrastructure/secrets.py` con dos funciones que devuelven las claves resolviendo override por env var, persistencia en `data/` y autogeneración. Integrarlo en `auth.py` (para JWT) y en `main.py` (para validación temprana de la encryption key).

## Step 1 — Crear `src/infrastructure/secrets.py`

Nuevo módulo con la siguiente API:

```python
import os
import secrets as _secrets
from pathlib import Path

DATA_DIR = Path(os.getenv("DATA_DIR", "/app/data"))
JWT_SECRET_FILE = DATA_DIR / ".jwt_secret"
ENCRYPTION_KEY_FILE = DATA_DIR / ".encryption_key"


def get_or_create_jwt_secret() -> str:
    """Resuelve JWT_SECRET: env var > fichero persistido > generar nuevo."""
    env = os.getenv("JWT_SECRET")
    if env:
        return env

    if JWT_SECRET_FILE.exists():
        return JWT_SECRET_FILE.read_text().strip()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    new_secret = _secrets.token_urlsafe(32)
    JWT_SECRET_FILE.write_text(new_secret)
    JWT_SECRET_FILE.chmod(0o600)
    return new_secret


def get_or_create_encryption_key() -> bytes:
    """Resuelve ENCRYPTION_KEY: env var > fichero persistido > generar nuevo Fernet key."""
    from cryptography.fernet import Fernet  # import diferido: dependencia opcional al usar

    env = os.getenv("ENCRYPTION_KEY")
    if env:
        return env.encode("utf-8")

    if ENCRYPTION_KEY_FILE.exists():
        return ENCRYPTION_KEY_FILE.read_bytes().strip()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    new_key = Fernet.generate_key()
    ENCRYPTION_KEY_FILE.write_bytes(new_key)
    ENCRYPTION_KEY_FILE.chmod(0o600)
    return new_key


def encryption_key_exists() -> bool:
    """True si hay key disponible (env var o fichero)."""
    return os.getenv("ENCRYPTION_KEY") is not None or ENCRYPTION_KEY_FILE.exists()
```

NOTA: `cryptography` debe estar en `requirements.txt`. Si no lo está, añadir en este step:

```
cryptography~=44.0
```

(PyJWT no lo trae como dep transitiva con HS256.)

## Step 2 — Integrar en `src/api/auth.py`

Sustituir la función `get_jwt_secret()` actual:

```python
def get_jwt_secret() -> str:
    return os.getenv("JWT_SECRET", DEFAULT_JWT_SECRET)
```

Por:

```python
from infrastructure.secrets import get_or_create_jwt_secret

def get_jwt_secret() -> str:
    return get_or_create_jwt_secret()
```

Y **eliminar** la constante `DEFAULT_JWT_SECRET` (ya no es necesaria — el fallback ahora es la auto-generación).

## Step 3 — Validación temprana en `src/main.py`

Después de `init_db()` y antes de `init_admin_user()`, añadir:

```python
from infrastructure.database import has_encrypted_hosts  # función helper, ver Step 4
from infrastructure.secrets import (
    encryption_key_exists,
    get_or_create_encryption_key,
    get_or_create_jwt_secret,
)

# Garantizar que el JWT secret existe (autogenera si falta)
get_or_create_jwt_secret()

# Validación crítica: si hay hosts cifrados pero no key, fail-fast
if has_encrypted_hosts() and not encryption_key_exists():
    raise RuntimeError(
        "Encryption key is missing but encrypted hosts found in database. "
        "Restore data/.encryption_key or set ENCRYPTION_KEY env var."
    )

# Garantizar que la encryption key existe (autogenera si falta y no hay hosts cifrados)
get_or_create_encryption_key()
```

## Step 4 — Helper `has_encrypted_hosts` en `database/__init__.py` (o `database.py`)

Este helper se usa solo en `main.py` para la validación. Puede vivir en `infrastructure/database/database.py`:

```python
def has_encrypted_hosts() -> bool:
    """True si alguna fila de hosts tiene password con prefijo enc:v1:."""
    from .models import Host
    with get_db_session() as db:
        return db.query(Host).filter(Host.password.like("enc:v1:%")).first() is not None
```

NOTA: en este punto, **ningún host tendrá ese prefijo** porque T008 aún no ha cifrado nada. La función devolverá siempre `False`. La validación en `main.py` queda preparada para cuando T008 esté en su sitio. Eso es correcto y aceptable — la función es trivial y se ejerce funcionalmente en T008.

## Step 5 — Tests unitarios — `src/test/test_secrets.py`

Crear nuevo fichero con suite que cubra:

- `get_or_create_jwt_secret()` con env var presente → devuelve la env var, no escribe fichero.
- `get_or_create_jwt_secret()` con fichero presente, sin env var → lee del fichero.
- `get_or_create_jwt_secret()` sin env var ni fichero → genera, persiste, devuelve. Llamada subsiguiente devuelve el mismo valor (idempotencia).
- `get_or_create_encryption_key()` con los tres mismos caminos.
- Permisos `0600` aplicados al fichero generado (verificar `oct(file.stat().st_mode & 0o777) == '0o600'`).
- `encryption_key_exists()` con/sin env var, con/sin fichero.

Usar `tmp_path` (pytest fixture) o `unittest.mock.patch` sobre `DATA_DIR` para aislar de `/app/data`. Patrón sugerido: monkeypatch del módulo:

```python
@pytest.fixture
def isolated_data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    # forzar reload del módulo o usar funciones que lean DATA_DIR cada vez
    ...
```

Si las constantes `JWT_SECRET_FILE` y `ENCRYPTION_KEY_FILE` se evalúan al import-time, refactorizarlas para resolverse en cada llamada (función helper `_jwt_secret_file()` que lea `os.getenv("DATA_DIR", "/app/data")` cada vez). Esto facilita los tests sin recargar módulo.

## Step 6 — Adaptar `src/test/test_auth.py`

Eliminar tests que dependan del `DEFAULT_JWT_SECRET` literal:

- `test_get_jwt_secret_default`: ya no aplica (no hay default literal). **Eliminar**.

Mantener los demás (creación/decoding de tokens, expiración, hash de password). El test `test_get_jwt_secret_from_env` sigue siendo válido — solo verificar que no rompe.

## DoD — Definition of Done

1. `src/infrastructure/secrets.py` existe con las tres funciones (`get_or_create_jwt_secret`, `get_or_create_encryption_key`, `encryption_key_exists`).
2. `cryptography~=44.0` está en `requirements.txt`.
3. `src/api/auth.py` no contiene la constante `DEFAULT_JWT_SECRET` ni el literal `"change-this-secret-in-production"`. `get_jwt_secret()` delega en `secrets.get_or_create_jwt_secret()`.
4. `src/main.py` invoca `get_or_create_jwt_secret()`, `get_or_create_encryption_key()` y la validación de `has_encrypted_hosts()`.
5. `infrastructure/database` expone `has_encrypted_hosts()`.
6. Existe `src/test/test_secrets.py` con cobertura de las tres funciones (mínimo 8 tests).
7. `test_auth.py` adaptado (eliminado `test_get_jwt_secret_default` y eliminada importación de `DEFAULT_JWT_SECRET`).
8. Suite completa pasa.
9. Cobertura ≥ 90% en CI gate.

## Evidence to produce

| # | Description | Command | File | PASS condition |
|---|-------------|---------|------|----------------|
| 1 | Módulo secrets existe | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev test -f infrastructure/secrets.py && echo OK` | `secrets_file.txt` | imprime `OK` |
| 2 | Sin DEFAULT_JWT_SECRET | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev sh -c "grep -E 'DEFAULT_JWT_SECRET\|change-this-secret' api/auth.py \|\| echo CLEAN"` | `no_default_secret.txt` | imprime `CLEAN` |
| 3 | cryptography en deps | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev pip show cryptography` | `cryptography_pkg.txt` | versión presente |
| 4 | main.py wiring | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev sh -c "grep -cE 'get_or_create_(jwt_secret\|encryption_key)\|has_encrypted_hosts' main.py"` | `main_wiring.txt` | número >= 3 |
| 5 | Tests secrets | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/test_secrets.py -v 2>&1` | `test_secrets.txt` | exit 0, ≥ 8 tests pass |
| 6 | Suite completa | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/ -v --cov=. --cov-report=term-missing --cov-fail-under=90 2>&1` | `tests_full.txt` | exit 0, coverage ≥ 90% |
| 7 | Lint | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff check . 2>&1` | `ruff_check.txt` | exit 0 |
| 8 | Format | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff format --check . 2>&1` | `ruff_format.txt` | exit 0 |

## Files to create/modify

| File | Action |
|------|--------|
| `src/infrastructure/secrets.py` | CREATE |
| `src/infrastructure/database/database.py` | MODIFY (añadir `has_encrypted_hosts` + `ENCRYPTED_PASSWORD_PREFIX`) |
| `src/infrastructure/database/__init__.py` | MODIFY (re-exportar `has_encrypted_hosts`) |
| `src/api/auth.py` | MODIFY |
| `src/main.py` | MODIFY |
| `requirements.txt` | MODIFY (añadir `cryptography~=44.0`) |
| `dev/dev-requirements.txt` | MODIFY (sync: añadir `cryptography>=44.0`) |
| `src/test/test_secrets.py` | CREATE |
| `src/test/test_auth.py` | MODIFY (eliminar test obsoleto + import) |

## Execution evidence

**Date**: 2026-05-03
**Modified files**:
- `src/infrastructure/secrets.py` — CREATED. Three public functions (`get_or_create_jwt_secret`, `get_or_create_encryption_key`, `encryption_key_exists`) + module constants. `DATA_DIR` resolved per-call via `_data_dir()` helper so tests can monkeypatch the env var without reloading the module. File generation uses `secrets.token_urlsafe(32)` for the JWT secret and `Fernet.generate_key()` for the encryption key, both written with mode `0o600`.
- `requirements.txt` — added `cryptography~=44.0` to the Authentication block.
- `dev/dev-requirements.txt` — synced: added `cryptography>=44.0` (sync rule from MEMORY: dev container builds from this file, not from the root one).
- `src/api/auth.py` — removed `DEFAULT_JWT_SECRET = "change-this-secret-in-production"`. `get_jwt_secret()` now delegates to `infrastructure.secrets.get_or_create_jwt_secret()`. `os` import kept (still used by `get_admin_credentials` and `get_jwt_expiration_hours`).
- `src/infrastructure/database/database.py` — added `ENCRYPTED_PASSWORD_PREFIX = "enc:v1:"` constant and `has_encrypted_hosts()` query helper (`Host.password.like("enc:v1:%")`). `Host` model imported eagerly (already used in `get_db_session` callers via repository).
- `src/infrastructure/database/__init__.py` — re-exports `has_encrypted_hosts` so callers import from the package root.
- `src/main.py` — wires the four new pieces: imports from `infrastructure.secrets`, calls `get_or_create_jwt_secret()` after `init_db()`, runs the consistency check `has_encrypted_hosts() and not encryption_key_exists()` (raises `RuntimeError` with a clear remediation message if violated), then calls `get_or_create_encryption_key()`. Order ensures the fail-fast triggers BEFORE any cipher use further down the boot sequence.
- `src/test/test_secrets.py` — CREATED. 13 tests covering env-var precedence, file persistence, autogeneration, idempotence, file permissions (`0o600`) and `encryption_key_exists` matrix. Each test isolates `DATA_DIR` to a `tmp` dir and scrubs `JWT_SECRET`/`ENCRYPTION_KEY` env vars in `tearDown` to avoid cross-test leakage.
- `src/test/test_auth.py` — removed `DEFAULT_JWT_SECRET` from the import block and the `test_get_jwt_secret_default` test (the constant no longer exists; the new fallback is autogeneration, covered by `test_secrets.py`).

### Verification table

| # | Deliverable | Evidence file | Result |
|---|------------|---------------|--------|
| 1 | `infrastructure/secrets.py` exists | `docs/tasks/evidence/T007/secrets_file.txt` | PASS — `OK` |
| 2 | No `DEFAULT_JWT_SECRET` / `change-this-secret` literal in `auth.py` | `docs/tasks/evidence/T007/no_default_secret.txt` | PASS — `CLEAN` |
| 3 | `cryptography` installed | `docs/tasks/evidence/T007/cryptography_pkg.txt` | PASS — `Version: 47.0.0` (≥ 44) |
| 4 | `main.py` references the new functions | `docs/tasks/evidence/T007/main_wiring.txt` | PASS — `6` (≥ 3 required) |
| 5 | `test_secrets.py` passes | `docs/tasks/evidence/T007/test_secrets.txt` | PASS — `13 passed in 0.04s` |
| 6 | Full suite + coverage gate ≥ 90% | `docs/tasks/evidence/T007/tests_full.txt` | PASS — `191 passed`, coverage `95.61%`, gate met. `infrastructure/secrets.py` at 100%. |
| 7 | `ruff check` clean | `docs/tasks/evidence/T007/ruff_check.txt` | PASS — `All checks passed!` |
| 8 | `ruff format --check` clean | `docs/tasks/evidence/T007/ruff_format.txt` | PASS — `39 files already formatted` |

### Design decisions

- **Per-call `DATA_DIR` resolution.** The constants `JWT_SECRET_FILE` and `ENCRYPTION_KEY_FILE` from the task spec were rewritten as private functions (`_jwt_secret_file()` / `_encryption_key_file()`) that re-read `DATA_DIR` on every call. This means tests can `os.environ["DATA_DIR"] = tmp_path` without reloading the module — the alternative (constants captured at import time) would have forced `importlib.reload(secrets_mod)` in every test, fragile under pytest's collection order.
- **`ENCRYPTED_PASSWORD_PREFIX` lives in `database.py`, not in a future `crypto.py`.** T008 will add `crypto.py` with the same constant. Putting the marker here now lets `has_encrypted_hosts()` work without importing the cipher layer (which doesn't exist yet) and avoids a circular dep when T008 lands. T008 should re-export the constant from `crypto.py` and re-import it here.
- **`Host` imported eagerly in `database.py`.** Previously `Host` was unused at the top level of `database.py` (only models indirectly via `Base`). The `has_encrypted_hosts()` query needs it explicitly. Moved the import to the top — no circularity (it lives in the same package).
- **Fail-fast position in `main.py`.** Placed the consistency check between `init_db()` and `init_admin_user()`. Earlier than `init_admin_user` because that path may eventually need the JWT secret. Later than `init_db()` because `has_encrypted_hosts()` queries the DB. Net result: the validation runs once, blocks the boot before any user can hit the API, and surfaces a precise error message naming the recovery step.
- **`get_or_create_jwt_secret()` called eagerly in `main.py`** instead of lazily on first auth request. Reason: the dev container starts with `tail -f /dev/null` and no secret file exists. Eagerly priming guarantees the secret file is on disk before the first login request, removing a tiny race between two concurrent first-time logins.
- **Skipped `os` removal from `auth.py`.** `os` is still used by `get_admin_credentials` and `get_jwt_expiration_hours` (env var reads). Lint passes; nothing to clean.
- **Coverage of `main.py` remains 0%**. That's the entrypoint, exercised at integration time only. Overall gate (90%) is met at 95.61%.
- **`test_secrets.py` uses `unittest.TestCase`** to match the project convention (every other test file uses unittest, not pytest fixtures). Isolation is done in `setUp/tearDown` of a private base class, mirroring the pattern in `test_api.py`.
