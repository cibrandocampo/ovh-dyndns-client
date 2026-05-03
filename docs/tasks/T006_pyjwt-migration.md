# T006 — Migrar `python-jose` → `PyJWT` y adaptar tests

## Context

`python-jose[cryptography]` lleva años sin releases activos y arrastra CVE-2024-33663 (algorithm confusion) y CVE-2024-33664 (DoS por JWE). Esta task lo sustituye por `PyJWT`, librería mantenida y estándar de facto en el ecosistema Python para JWT. La superficie de uso en el proyecto es mínima (`jwt.encode`, `jwt.decode`, captura de excepción) y el mapeo es 1:1 con HS256.

Plan: [docs/plans/security-hardening.md](../plans/security-hardening.md), sección 1.

**Dependencies**: None.

## Objective

Que `src/api/auth.py` use `PyJWT` en lugar de `python-jose`, los tests existentes adaptados sigan en verde, y `requirements.txt` ya no liste `python-jose[cryptography]`.

## Step 1 — Actualizar `requirements.txt`

En `requirements.txt`, eliminar:

```
python-jose[cryptography]~=3.5.0
```

Y añadir en su lugar (en el bloque "Authentication"):

```
PyJWT~=2.10
```

NOTA: no añadir `cryptography` explícito en este punto. T008 lo necesitará para Fernet y allí se añade. Si ya está como dep transitiva de algún otro paquete, no duplicar.

## Step 2 — Migrar `src/api/auth.py`

El fichero actual importa de `jose`:

```python
from jose import JWTError, jwt
```

Sustituir por la API de PyJWT:

```python
import jwt
from jwt.exceptions import PyJWTError
```

`jwt.encode(...)` y `jwt.decode(...)` mantienen la misma firma con HS256:

- `jwt.encode(to_encode, secret, algorithm=ALGORITHM)` — idéntico.
- `jwt.decode(token, secret, algorithms=[ALGORITHM])` — idéntico.

Reemplazar `except JWTError` por `except PyJWTError`. La función `decode_token` queda funcionalmente igual.

NOTA importante de comportamiento: PyJWT 2.x devuelve **`str`** en `encode()` (mientras que python-jose ya lo hacía también en 3.x). No hace falta `.decode("utf-8")`.

## Step 3 — Adaptar `src/test/test_auth.py`

El fichero importa `DEFAULT_JWT_SECRET` y otros símbolos del módulo. Esta task **no elimina** el default todavía (eso es T007). Solo verificar que los tests existentes siguen pasando con la nueva librería.

Si algún test fallara por:
- Diferencia en el formato de retorno (`bytes` vs `str`): adaptar.
- Diferencia en mensaje de error de excepción: el test no debería depender del mensaje exacto, solo de que la función devuelva `None` ante token inválido.

Cambios esperados: ninguno o mínimos.

## Step 4 — Reconstruir el contenedor de dev

El cambio en `requirements.txt` exige rebuild del contenedor de dev (no es bind-mount):

```bash
docker compose -f dev/docker-compose.yaml down
docker compose -f dev/docker-compose.yaml build
docker compose -f dev/docker-compose.yaml up -d
```

## Step 5 — Verificar que `python-jose` ya no está instalado

```bash
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev pip list | grep -i jose
```

Salida esperada: vacía.

```bash
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev pip list | grep -i pyjwt
```

Salida esperada: `PyJWT 2.10.x`.

## DoD — Definition of Done

1. `requirements.txt` no contiene `python-jose` y sí contiene `PyJWT~=2.10`.
2. `src/api/auth.py` no importa nada de `jose`; sí importa `jwt` y `PyJWTError`.
3. Tests unitarios existentes pasan (`docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/test_auth.py -v`).
4. Suite completa pasa (`pytest test/ -v`).
5. Lint y format pasan (`ruff check .` y `ruff format --check .`).
6. `python-jose` no está instalado en el contenedor.

## Evidence to produce

| # | Description | Command | File | PASS condition |
|---|-------------|---------|------|----------------|
| 1 | Sin python-jose en requirements | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev sh -c "grep -c python-jose requirements.txt 2>/dev/null \|\| echo 0"` | `req_no_jose.txt` | imprime `0` |
| 2 | PyJWT en requirements | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev sh -c "grep -E '^PyJWT' /app/../requirements.txt 2>/dev/null \|\| grep -E '^PyJWT' /requirements.txt 2>/dev/null \|\| true"` | `req_pyjwt.txt` | match `PyJWT~=2.10` (NOTA: la ruta exacta de requirements.txt depende del montaje; ajustar según convención del repo) |
| 3 | Sin imports de jose | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev sh -c "grep -rE 'from jose\|import jose' api/ \|\| echo CLEAN"` | `no_jose_imports.txt` | imprime `CLEAN` |
| 4 | python-jose no instalado | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev sh -c "pip list 2>/dev/null \| grep -i jose \|\| echo NOT_INSTALLED"` | `pip_no_jose.txt` | imprime `NOT_INSTALLED` |
| 5 | PyJWT instalado | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev pip show PyJWT` | `pip_pyjwt.txt` | versión >= 2.10 |
| 6 | Tests test_auth | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/test_auth.py -v 2>&1` | `test_auth.txt` | exit 0, all green |
| 7 | Suite completa | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/ -v 2>&1` | `tests_full.txt` | exit 0, all green |
| 8 | Lint | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff check . 2>&1` | `ruff_check.txt` | exit 0, "All checks passed!" |
| 9 | Format | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff format --check . 2>&1` | `ruff_format.txt` | exit 0 |

## Files to create/modify

| File | Action |
|------|--------|
| `requirements.txt` | MODIFY |
| `dev/dev-requirements.txt` | MODIFY (also lists `python-jose`; must stay in sync) |
| `src/api/auth.py` | MODIFY |
| `src/test/test_auth.py` | UNCHANGED (tests still green) |

## Execution evidence

**Date**: 2026-05-03
**Modified files**:
- `requirements.txt` — replaced `python-jose[cryptography]~=3.5.0` with `PyJWT~=2.10` in the Authentication block.
- `dev/dev-requirements.txt` — replaced `python-jose[cryptography]>=3.3.0` with `PyJWT>=2.10`. Sync was required: the dev container builds from this file, not from the root `requirements.txt`. Without this, the dev environment would import `jwt` and find no module.
- `src/api/auth.py` — swapped `from jose import JWTError, jwt` for `import jwt` + `from jwt.exceptions import PyJWTError`. The single `except JWTError:` in `decode_token` became `except PyJWTError:`. `jwt.encode(...)` and `jwt.decode(...)` signatures are 1:1 between python-jose 3.x and PyJWT 2.x for HS256, so no other changes were needed.

### Verification table

| # | Deliverable | Evidence file | Result |
|---|------------|---------------|--------|
| 1 | `python-jose` removed from `requirements.txt` | `docs/tasks/evidence/T006/req_no_jose.txt` | PASS — `0` |
| 2 | `PyJWT~=2.10` present in `requirements.txt` | `docs/tasks/evidence/T006/req_pyjwt.txt` | PASS — `PyJWT~=2.10` |
| 3 | No `jose` imports in `src/api/` | `docs/tasks/evidence/T006/no_jose_imports.txt` | PASS — `CLEAN` |
| 4 | `python-jose` not installed in dev container | `docs/tasks/evidence/T006/pip_no_jose.txt` | PASS — `NOT_INSTALLED` |
| 5 | `PyJWT >= 2.10` installed | `docs/tasks/evidence/T006/pip_pyjwt.txt` | PASS — `Version: 2.12.1` |
| 6 | `test_auth.py` passes | `docs/tasks/evidence/T006/test_auth.txt` | PASS — `24 passed` |
| 7 | Full suite passes | `docs/tasks/evidence/T006/tests_full.txt` | PASS — `179 passed, 80 warnings in 20.25s` |
| 8 | Ruff check clean | `docs/tasks/evidence/T006/ruff_check.txt` | PASS — `All checks passed!` |
| 9 | Ruff format clean | `docs/tasks/evidence/T006/ruff_format.txt` | PASS — `37 files already formatted` |

### Design decisions

- **Synced `dev/dev-requirements.txt` along with `requirements.txt`.** The task only listed `requirements.txt`, but the dev image builds from `dev/dev-requirements.txt` (per `dev/Dockerfile`). Updating only the production file would have left the dev container unable to import `jwt`. Sync is a real coupling — not optional. Worth tracking as future cleanup: collapse to a single requirements file with extras, or have `dev-requirements.txt` `-r` include the root one.
- **PyJWT version installed: 2.12.1**, well above the `~=2.10` floor (which permits 2.10.x to 2.99.x in PEP 440 semantics — actually `~=2.10` means `>=2.10, <3.0`). The compatible release operator gives security patches for free without breaking changes.
- **`InsecureKeyLengthWarning` is informational, not a failure.** PyJWT 2.10+ warns on HMAC keys shorter than 32 bytes (RFC 7518 §3.2). Test fixtures use short literal secrets (`"test-jwt-secret-key"` = 19 bytes, `"my-custom-secret"` = 16 bytes). 80 warnings appear in the suite output but tests still pass. Production warnings will disappear in T007 once `secrets.token_urlsafe(32)` autogenerates 32-byte keys. Could be silenced earlier by lengthening the test fixtures, but I left them as-is — the warning is exactly the signal we want and changing test inputs unrelated to this migration would muddy the diff.
- **No change to `test_auth.py`.** All 24 existing tests passed unchanged, including the ones that decode tampered tokens (PyJWT raises subclasses of `PyJWTError`, our `except PyJWTError:` catches them all the same way as `except JWTError:` did with python-jose).
- **`DEFAULT_JWT_SECRET` and `get_jwt_secret_default` test left in place.** They will be removed in T007 when the secret moves to auto-generation; T006 is strictly a library swap.
