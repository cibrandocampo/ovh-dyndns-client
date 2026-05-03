# T008 — Cifrado at-rest de passwords OVH (Fernet) + migración idempotente

## Context

Las credenciales OVH (`hosts.password`) se almacenan en plaintext en la columna `String` de SQLite. Quien acceda al volumen `data/` se lleva todas las credenciales DynHost. Esta task introduce cifrado at-rest con Fernet (AES-128-CBC + HMAC-SHA256, autenticado), un prefijo de versión (`enc:v1:`) para detectar plaintext heredado y una migración idempotente que cifra los valores existentes al primer arranque post-deploy.

Tras la ejecución, ninguna password OVH legible queda en disco — la columna sigue siendo `String`, pero su contenido es base64 cifrado.

Plan: [docs/plans/security-hardening.md](../plans/security-hardening.md), sección 3.

**Dependencies**: T007 (consume `get_or_create_encryption_key()` del módulo `secrets.py`).

## Objective

Que `create_host` / `update_host` cifren la password antes de persistir, que `get_hosts` / `get_pending_hosts` / `get_host_by_hostname` la descifren al materializar `HostConfig`, y que `migrate_plaintext_passwords()` se ejecute al arrancar para migrar instalaciones existentes.

## Step 1 — Crear `src/infrastructure/crypto.py`

Nuevo módulo con la API de cifrado:

```python
from cryptography.fernet import Fernet, InvalidToken

from infrastructure.secrets import get_or_create_encryption_key

ENCRYPTED_PREFIX = "enc:v1:"


def _fernet() -> Fernet:
    return Fernet(get_or_create_encryption_key())


def is_encrypted(value: str) -> bool:
    """True si el valor lleva el prefijo de versión."""
    return value.startswith(ENCRYPTED_PREFIX)


def encrypt_password(plain: str) -> str:
    """Cifra y devuelve `enc:v1:<base64>`."""
    token = _fernet().encrypt(plain.encode("utf-8")).decode("utf-8")
    return f"{ENCRYPTED_PREFIX}{token}"


def decrypt_password(stored: str) -> str:
    """Descifra. Si el valor no tiene prefijo, lo devuelve tal cual (legacy plaintext)."""
    if not is_encrypted(stored):
        return stored  # plaintext heredado, devolver sin tocar (la migración lo encriptará)
    payload = stored[len(ENCRYPTED_PREFIX):]
    try:
        return _fernet().decrypt(payload.encode("utf-8")).decode("utf-8")
    except InvalidToken as e:
        raise RuntimeError(
            "Failed to decrypt host password. Encryption key may have changed."
        ) from e
```

## Step 2 — Integrar cifrado en `src/infrastructure/database/repository.py`

Modificar cuatro métodos. **Cifrar al persistir**, **descifrar al leer**.

### `create_host` (línea ~122)

```python
from infrastructure.crypto import encrypt_password

def create_host(self, hostname: str, username: str, password: str) -> dict:
    with get_db_session() as db:
        host = Host(
            hostname=hostname,
            username=username,
            password=encrypt_password(password),  # ← cifrado
        )
        # ... resto igual ...
```

### `update_host` (línea ~142)

```python
if password is not None:
    host.password = encrypt_password(password)  # ← cifrado
```

### `get_hosts` (línea ~59) y `get_pending_hosts` (línea ~68)

```python
from infrastructure.crypto import decrypt_password

# En el list-comprehension que construye HostConfig:
return [
    HostConfig(
        hostname=host.hostname,
        username=host.username,
        password=SecretStr(decrypt_password(host.password)),  # ← descifrado
    )
    for host in hosts
]
```

### `get_host_by_hostname` (línea ~79)

Igual: aplicar `decrypt_password(host.password)` al construir el `HostConfig`.

NOTA: los métodos `get_all_hosts` y `get_host_by_id` (línea ~89 y ~106) **no devuelven la password** (la omiten en el dict). No requieren cambio.

## Step 3 — Función de migración `migrate_plaintext_passwords`

En `src/infrastructure/database/database.py`, añadir:

```python
def migrate_plaintext_passwords() -> int:
    """
    Idempotente. Recorre la tabla hosts. Para cada fila cuyo `password`
    NO empieza con `enc:v1:`, lo cifra y reescribe.

    Returns:
        Número de filas migradas.
    """
    from infrastructure.crypto import encrypt_password, is_encrypted
    from .models import Host

    migrated = 0
    with get_db_session() as db:
        hosts = db.query(Host).all()
        for host in hosts:
            if not is_encrypted(host.password):
                host.password = encrypt_password(host.password)
                migrated += 1
    return migrated
```

`get_db_session` ya hace commit/rollback. No hace falta lock — la app aún no está exponiendo el API cuando esto corre (se invoca antes de arrancar uvicorn).

## Step 4 — Wirear `migrate_plaintext_passwords()` en `src/main.py`

Después de `init_db()` y de las validaciones de keys de T007, **antes** de `init_admin_user()`:

```python
from infrastructure.database import migrate_plaintext_passwords

migrated = migrate_plaintext_passwords()
if migrated:
    logger.info(f"Encrypted {migrated} legacy plaintext host password(s)")
```

`migrate_plaintext_passwords` debe estar exportado en `src/infrastructure/database/__init__.py` si esa es la convención del proyecto.

## Step 5 — Tests unitarios — `src/test/test_crypto.py`

Crear nuevo fichero con suite que cubra:

- `encrypt_password("foo")` devuelve string que empieza por `enc:v1:`.
- `decrypt_password(encrypt_password("foo"))` devuelve `"foo"` (round-trip).
- `decrypt_password("plaintext-legacy")` (sin prefijo) devuelve `"plaintext-legacy"` sin error (legacy passthrough).
- `is_encrypted("enc:v1:..")` → `True`. `is_encrypted("foo")` → `False`.
- Dos llamadas consecutivas de `encrypt_password("foo")` producen ciphertext distinto (Fernet incluye nonce/timestamp aleatorio) pero ambos descifran a `"foo"`.
- `decrypt_password("enc:v1:invalid-base64")` lanza `RuntimeError`.

Aislar la encryption key con `tmp_path` y `monkeypatch.setenv("DATA_DIR", str(tmp_path))` o `monkeypatch.setenv("ENCRYPTION_KEY", Fernet.generate_key().decode())`.

## Step 6 — Tests de migración — `src/test/test_repository.py` (extender)

Añadir tests al fichero existente:

- `test_create_host_persists_encrypted`: tras `create_host(...)`, leer `Host.password` directamente con SQLAlchemy y verificar que empieza por `enc:v1:` y no contiene la password en plano.
- `test_get_hosts_returns_decrypted`: `create_host("h", "u", "p")` y luego `get_hosts()` devuelve `HostConfig` con `password.get_secret_value() == "p"`.
- `test_update_host_re_encrypts`: tras `update_host(id, password="new")`, la fila almacena ciphertext nuevo distinto del anterior.
- `test_migrate_plaintext_passwords_encrypts_legacy`: insertar manualmente una fila con `password="plain123"` (sin pasar por `create_host`), ejecutar `migrate_plaintext_passwords()`, verificar que la fila ahora empieza por `enc:v1:` y que `get_hosts()` devuelve `"plain123"`.
- `test_migrate_plaintext_passwords_idempotent`: ejecutar dos veces; la segunda devuelve `0`.

## Step 7 — Verificar test_repository_extended.py

El fichero `test_repository_extended.py` ya existe; revisar que no contiene asserts contra plaintext stored. Si los hay, adaptar.

## DoD — Definition of Done

1. `src/infrastructure/crypto.py` existe con `encrypt_password`, `decrypt_password`, `is_encrypted`, constante `ENCRYPTED_PREFIX = "enc:v1:"`.
2. `repository.py` cifra en `create_host` y `update_host`, descifra en `get_hosts`, `get_pending_hosts`, `get_host_by_hostname`.
3. `database.py` (o equivalente) expone `migrate_plaintext_passwords()` idempotente.
4. `main.py` ejecuta `migrate_plaintext_passwords()` tras `init_db()`.
5. `test_crypto.py` cubre los 6 casos listados.
6. `test_repository.py` cubre los 5 casos de cifrado/migración.
7. Una inspección directa de la DB tras crear un host muestra ciphertext, no plaintext.
8. Suite completa pasa con coverage ≥ 90%.
9. Round-trip end-to-end manual verificable: insertar host vía API, leerlo vía API, password recuperada idéntica.

## Evidence to produce

| # | Description | Command | File | PASS condition |
|---|-------------|---------|------|----------------|
| 1 | crypto.py existe | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev test -f infrastructure/crypto.py && echo OK` | `crypto_file.txt` | imprime `OK` |
| 2 | Tests crypto | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/test_crypto.py -v 2>&1` | `test_crypto.txt` | exit 0, ≥ 6 tests pass |
| 3 | Tests repository extendidos | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/test_repository.py -v 2>&1` | `test_repo.txt` | exit 0, incluye los nuevos tests de cifrado/migración |
| 4 | Inspección DB tras crear host | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -c "from infrastructure.database import init_db, SqliteRepository; init_db(); r=SqliteRepository(); r.create_host('test.example', 'u', 'plain-pass'); from infrastructure.database.database import get_db_session; from infrastructure.database.models import Host; s=get_db_session().__enter__(); h=s.query(Host).filter_by(hostname='test.example').first(); print('OK' if h.password.startswith('enc:v1:') else 'FAIL')"` | `db_inspect.txt` | imprime `OK` |
| 5 | Migración idempotente — dos pasadas | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -c "from infrastructure.database import migrate_plaintext_passwords; print(migrate_plaintext_passwords()); print(migrate_plaintext_passwords())"` | `migrate_idempotent.txt` | la segunda llamada imprime `0` |
| 6 | Suite completa con coverage | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/ -v --cov=. --cov-report=term-missing --cov-fail-under=90 2>&1` | `tests_full.txt` | exit 0, coverage ≥ 90% |
| 7 | Lint | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff check . 2>&1` | `ruff_check.txt` | exit 0 |
| 8 | Format | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff format --check . 2>&1` | `ruff_format.txt` | exit 0 |

## Files to create/modify

| File | Action |
|------|--------|
| `src/infrastructure/crypto.py` | CREATE |
| `src/infrastructure/database/repository.py` | MODIFY (4 métodos: create/update/get_hosts/get_pending/get_by_hostname) |
| `src/infrastructure/database/database.py` | MODIFY (añadir `migrate_plaintext_passwords`, eliminar constante duplicada) |
| `src/infrastructure/database/__init__.py` | MODIFY (re-exportar `migrate_plaintext_passwords`) |
| `src/main.py` | MODIFY (invocar migración) |
| `src/test/test_crypto.py` | CREATE |
| `src/test/test_repository.py` | MODIFY (extender + ENCRYPTION_KEY en setUpClass) |
| `src/test/test_repository_extended.py` | MODIFY (ENCRYPTION_KEY en setUpClass) |
| `src/test/test_api.py` | MODIFY (ENCRYPTION_KEY en setUpClass) |
| `src/test/test_api_extended.py` | MODIFY (ENCRYPTION_KEY en setUpClass) |

## Execution evidence

**Date**: 2026-05-03
**Modified files**:
- `src/infrastructure/crypto.py` — CREATED. Public API: `encrypt_password`, `decrypt_password`, `is_encrypted`, constant `ENCRYPTED_PREFIX = "enc:v1:"`. Built on `cryptography.fernet.Fernet`. `decrypt_password` of a non-prefixed value passes through unchanged (legacy passthrough — the migration handles it on next boot). `decrypt_password` of a corrupt prefixed value raises `RuntimeError`.
- `src/infrastructure/database/database.py` — added `migrate_plaintext_passwords()` (idempotent: returns the count of rows newly encrypted; 0 means nothing to do). Removed the local `ENCRYPTED_PASSWORD_PREFIX` constant introduced in T007 — `has_encrypted_hosts()` now lazy-imports `ENCRYPTED_PREFIX` from `crypto.py` (single source of truth).
- `src/infrastructure/database/__init__.py` — re-exports `migrate_plaintext_passwords`.
- `src/infrastructure/database/repository.py` — `create_host` and `update_host` call `encrypt_password(plain)` before persisting. `get_hosts`, `get_pending_hosts`, `get_host_by_hostname` call `decrypt_password(stored)` when materialising `HostConfig`. `get_all_hosts` and `get_host_by_id` are untouched (they don't expose passwords).
- `src/main.py` — calls `migrate_plaintext_passwords()` after `init_db()` + key validation (T007) and before `init_admin_user()`. Logs the count when non-zero, stays silent on the steady state.
- `src/test/test_crypto.py` — CREATED. 9 tests across `is_encrypted`, `encrypt_password` (round-trip, distinct ciphertexts, unicode), `decrypt_password` (round-trip, unicode, legacy passthrough, `RuntimeError` on corrupted ciphertext). Each test class isolates `ENCRYPTION_KEY` via env var.
- `src/test/test_repository.py` — added `ENCRYPTION_KEY` env var in `setUpClass`. Five new tests cover encrypted persistence, decrypted retrieval, re-encryption on update, plaintext migration (single-row + idempotent two-pass).
- `src/test/test_repository_extended.py`, `src/test/test_api.py`, `src/test/test_api_extended.py` — added `ENCRYPTION_KEY = Fernet.generate_key()` in `setUpClass`. Required because every `create_host` call now invokes `encrypt_password` which transitively reads the key; without the env var the test would write a real key file under the dev's bind-mounted `/app/data`.

### Verification table

| # | Deliverable | Evidence file | Result |
|---|------------|---------------|--------|
| 1 | `infrastructure/crypto.py` exists | `docs/tasks/evidence/T008/crypto_file.txt` | PASS — `OK` |
| 2 | `test_crypto.py` passes | `docs/tasks/evidence/T008/test_crypto.txt` | PASS — `9 passed in 0.03s` |
| 3 | `test_repository.py` passes (12 pre-existing + 5 new) | `docs/tasks/evidence/T008/test_repo.txt` | PASS — `17 passed in 0.30s` |
| 4 | DB inspection: stored value is `enc:v1:` ciphertext, plaintext is absent | `docs/tasks/evidence/T008/db_inspect.txt` | PASS — `stored=enc:v1:gAAAAABp95Xn-zAEDgGHvDf...` + `OK` |
| 5 | Idempotent migration: first pass migrates, second is a no-op | `docs/tasks/evidence/T008/migrate_idempotent.txt` | PASS — `first=2`, `second=0` |
| 6 | Full suite + coverage gate (≥ 90%) | `docs/tasks/evidence/T008/tests_full.txt` | PASS — `205 passed`, coverage `95.59%`. `crypto.py` at 100%, `repository.py` at 100%. |
| 7 | `ruff check` clean | `docs/tasks/evidence/T008/ruff_check.txt` | PASS — `All checks passed!` |
| 8 | `ruff format --check` clean | `docs/tasks/evidence/T008/ruff_format.txt` | PASS — `41 files already formatted` (after running `ruff format infrastructure/crypto.py` to add the slice-colon spacing the formatter wanted). |

### Design decisions

- **Single source of truth for `ENCRYPTED_PREFIX`.** T007 defined `ENCRYPTED_PASSWORD_PREFIX = "enc:v1:"` in `database.py` as a placeholder; T008 promotes the constant to `crypto.py` and removes the duplicate. `has_encrypted_hosts()` and `migrate_plaintext_passwords()` lazy-import the symbol so `database.py` keeps zero import-time dependency on the cipher layer (avoids a ripple if we ever swap Fernet).
- **Lazy imports in `database.py` migration helpers.** Both `has_encrypted_hosts` and `migrate_plaintext_passwords` import `infrastructure.crypto` inside their function body. Reason: `database.py` is imported very early (model setup), and we don't want to drag the cipher / `cryptography` package into the import graph until something actually needs it.
- **Tests register `ENCRYPTION_KEY` via env var, not by writing a file.** Four test classes that touch the repository now set `os.environ["ENCRYPTION_KEY"] = Fernet.generate_key().decode("utf-8")` in `setUpClass`. Without this, the first `create_host` of every test run would call `get_or_create_encryption_key()`, generate a fresh key and persist it under `/app/data/.encryption_key` — polluting the dev volume and silently coupling tests through that file.
- **Legacy passthrough on decrypt.** `decrypt_password` returns non-prefixed values unchanged. Reason: covers the brief window between deploy and the boot-time migration on existing installs, and lets reads of unmigrated rows succeed instead of crashing the API. The migration is what actually upgrades them; this is just defensive.
- **Idempotent migration via prefix check.** Migration scans every row, encrypts only those without the `enc:v1:` prefix. Counter returned so the boot log can record exactly how many rows were upgraded — useful evidence on the first deploy of this PR. On the steady state it returns `0` and the log line is suppressed.
- **`ruff format` reformatted `crypto.py` to add a space inside the slice colon** (`stored[len(ENCRYPTED_PREFIX) :]`). Standard PEP 8 + ruff-format style for slices. Applied without code changes.
- **`main.py` keeps showing 0% coverage**. Entrypoint code; covered at integration time only. Overall 95.59% well above the 90% gate.
