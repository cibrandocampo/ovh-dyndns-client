# T011 — Timeouts en HTTP clients y drop de `ipify-py`

## Context

Ni `OvhClient.update_ip` ni `IpifyClient.get_public_ip` pasan `timeout` a sus llamadas HTTP. Si OVH o ipify se cuelgan, el scheduler (un único hilo) queda bloqueado indefinidamente. La librería `ipify-py` además lleva años sin commits y no expone parámetro de timeout — buena ocasión para dropearla y usar `requests` directo.

Plan: [docs/plans/security-hardening.md](../plans/security-hardening.md), sección 6.

**Dependencies**: None (independiente del resto).

## Objective

Que toda llamada HTTP saliente tenga `timeout=(5, 10)` (connect, read), y que `ipify-py` no aparezca en `requirements.txt` ni en imports.

## Step 1 — Eliminar `ipify-py` de `requirements.txt`

Quitar la línea:

```
ipify-py~=1.0.1
```

## Step 2 — Reescribir `src/infrastructure/clients/ipify_client.py`

Sustituir la dependencia de `ipify` por una llamada directa a `https://api.ipify.org`:

```python
import requests
from pydantic import IPvAnyAddress

from application.ports import IpProvider
from infrastructure.logger import Logger

IPIFY_URL = "https://api.ipify.org"
IPIFY_HTTP_TIMEOUT = (5, 10)  # (connect, read) seconds


class IpifyClient(IpProvider):
    """
    Client for retrieving the current public IP address using the ipify service.
    """

    def __init__(self):
        self.logger = Logger().get_logger()

    def get_public_ip(self) -> IPvAnyAddress:
        """
        Fetches and validates the current public IP address.

        Raises:
            RuntimeError: If the IP could not be retrieved or is invalid.
        """
        try:
            response = requests.get(IPIFY_URL, timeout=IPIFY_HTTP_TIMEOUT)
            response.raise_for_status()
            ip_str = response.text.strip()
            ip = IPvAnyAddress(ip_str)
            self.logger.info(f"Retrieved public IP: {ip}")
            return ip
        except (requests.RequestException, ValueError) as e:
            self.logger.error(f"Failed to retrieve public IP: {e}")
            raise RuntimeError("Unable to fetch IP from ipify") from e
```

NOTA: `ValueError` cubre el caso de `IPvAnyAddress(...)` rechazando un string que no es IP. Mantener el comportamiento del cliente original (lanzar `RuntimeError`).

## Step 3 — Añadir timeout en `src/infrastructure/clients/ovh_client.py`

Definir constante al inicio del módulo:

```python
OVH_HTTP_TIMEOUT = (5, 10)
```

En `update_ip` (línea ~90), modificar la llamada:

```python
response = requests.get(url, auth=auth, timeout=OVH_HTTP_TIMEOUT)
```

El catch existente de `requests.RequestException` ya cubre `requests.Timeout` (es subclase). No hace falta tratamiento extra.

## Step 4 — Adaptar `src/test/test_ipify_client.py`

El fichero actual probablemente mockea `ipify.get_ip()`. Cambiarlo a mockear `requests.get`:

Ejemplo adaptado:

```python
from unittest.mock import patch, MagicMock

class TestIpifyClient(unittest.TestCase):
    @patch("infrastructure.clients.ipify_client.requests.get")
    def test_get_public_ip_returns_valid_ip(self, mock_get):
        mock_get.return_value = MagicMock(
            text="192.168.1.1",
            raise_for_status=MagicMock(),
        )
        client = IpifyClient()
        ip = client.get_public_ip()
        assert str(ip) == "192.168.1.1"
        # Verifica que se pasó timeout
        mock_get.assert_called_once_with(
            "https://api.ipify.org",
            timeout=(5, 10),
        )

    @patch("infrastructure.clients.ipify_client.requests.get")
    def test_get_public_ip_raises_on_timeout(self, mock_get):
        import requests
        mock_get.side_effect = requests.Timeout("read timeout")
        client = IpifyClient()
        with pytest.raises(RuntimeError, match="Unable to fetch IP"):
            client.get_public_ip()
```

Eliminar cualquier mock de `ipify.get_ip()` o import de `ipify`.

## Step 5 — Adaptar `src/test/test_ovh_client.py`

Verificar que el mock de `requests.get` no rompe al recibir el nuevo argumento `timeout`. Si los tests usan `assert_called_with(...)` con argumentos exactos, actualizar para incluir `timeout=(5, 10)`:

```python
mock_get.assert_called_once_with(
    expected_url,
    auth=expected_auth,
    timeout=(5, 10),
)
```

Si usan `assert_called_once()` o asserts más laxos, no requieren cambio.

Añadir un test nuevo:

- `test_update_ip_handles_timeout`: simular `requests.get` levantando `requests.Timeout`, verificar que `update_ip` devuelve `(False, "Connection error: ...")` y no propaga la excepción.

## Step 6 — Reconstruir el contenedor

```bash
docker compose -f dev/docker-compose.yaml down
docker compose -f dev/docker-compose.yaml build
docker compose -f dev/docker-compose.yaml up -d
```

## Step 7 — Verificar que `ipify-py` ya no está

```bash
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev pip list | grep -i ipify
```

Salida esperada: vacía.

```bash
docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev grep -rE 'import ipify\|from ipify' infrastructure/
```

Salida esperada: vacía.

## DoD — Definition of Done

1. `ipify-py` no aparece en `requirements.txt` ni instalado.
2. `IpifyClient` usa `requests.get` directo con `timeout=(5, 10)` y URL `https://api.ipify.org`.
3. `OvhClient.update_ip` pasa `timeout=(5, 10)` a `requests.get`.
4. Tests existentes adaptados; nuevo test de timeout en `test_ovh_client.py`.
5. Suite completa pasa con coverage ≥ 90%.
6. Lint y format pasan.

## Evidence to produce

| # | Description | Command | File | PASS condition |
|---|-------------|---------|------|----------------|
| 1 | Sin ipify-py en requirements | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev sh -c "grep -c ipify-py requirements.txt 2>/dev/null \|\| echo 0"` | `req_no_ipify.txt` | imprime `0` |
| 2 | ipify-py no instalado | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev sh -c "pip list 2>/dev/null \| grep -i ipify-py \|\| echo NOT_INSTALLED"` | `pip_no_ipify.txt` | imprime `NOT_INSTALLED` |
| 3 | Sin imports de ipify | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev sh -c "grep -rE 'import ipify\|from ipify' infrastructure/ \|\| echo CLEAN"` | `no_ipify_imports.txt` | imprime `CLEAN` |
| 4 | timeout en ovh_client | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev sh -c "grep -E 'timeout\\s*=' infrastructure/clients/ovh_client.py"` | `ovh_timeout.txt` | match no vacío |
| 5 | timeout en ipify_client | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev sh -c "grep -E 'timeout\\s*=' infrastructure/clients/ipify_client.py"` | `ipify_timeout.txt` | match no vacío |
| 6 | Tests ipify | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/test_ipify_client.py -v 2>&1` | `test_ipify.txt` | exit 0, all pass |
| 7 | Tests ovh | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/test_ovh_client.py -v 2>&1` | `test_ovh.txt` | exit 0, includes new timeout test |
| 8 | Suite completa | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev python -m pytest test/ -v --cov=. --cov-fail-under=90 2>&1` | `tests_full.txt` | exit 0, coverage ≥ 90% |
| 9 | Lint | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff check . 2>&1` | `ruff_check.txt` | exit 0 |
| 10 | Format | `docker compose -f dev/docker-compose.yaml exec ovh_dyndns_dev ruff format --check . 2>&1` | `ruff_format.txt` | exit 0 |

## Files to create/modify

| File | Action |
|------|--------|
| `requirements.txt` | MODIFY (eliminar `ipify-py`) |
| `dev/dev-requirements.txt` | MODIFY (sync) |
| `src/infrastructure/clients/ipify_client.py` | MODIFY (drop ipify, requests con timeout) |
| `src/infrastructure/clients/ovh_client.py` | MODIFY (añadir timeout) |
| `src/test/test_ipify_client.py` | MODIFY (mock `requests.get` en lugar de `ipify`) |
| `src/test/test_ovh_client.py` | MODIFY (test de timeout, test de propagación de la constante) |

## Execution evidence

**Date**: 2026-05-03
**Modified files**:
- `requirements.txt` and `dev/dev-requirements.txt` — removed `ipify-py`. Dev container rebuilt.
- `src/infrastructure/clients/ipify_client.py` — dropped the `ipify` library import. Now calls `requests.get("https://api.ipify.org", timeout=(5, 10))` directly. New constants `IPIFY_URL` and `IPIFY_HTTP_TIMEOUT` exposed for tests/visibility. The exception path catches `requests.RequestException` AND `ValueError` (the latter covers `IPvAnyAddress` rejecting non-IP responses), wrapping both in `RuntimeError`.
- `src/infrastructure/clients/ovh_client.py` — added `OVH_HTTP_TIMEOUT = (5, 10)` constant; `update_ip` passes it to `requests.get`. The existing `requests.RequestException` catch already handles `requests.Timeout` (subclass), so no additional error handling needed.
- `src/test/test_ipify_client.py` — full rewrite. Mocks `requests.get` (not `ipify.get_ip`). Five tests: success with explicit timeout assertion, whitespace-stripping, request exception, timeout, invalid IP body. Removed every reference to the dropped library.
- `src/test/test_ovh_client.py` — added `test_update_ip_handles_timeout` (simulates `requests.Timeout`, expects `(False, "Connection error: …")`) and `test_update_ip_passes_timeout` (introspects `mock_get.call_args` to confirm `timeout=OVH_HTTP_TIMEOUT` was passed). Existing 8 tests still pass since they used `assert_called_once()` (relaxed).

### Verification table

| # | Deliverable | Evidence file | Result |
|---|------------|---------------|--------|
| 1 | `ipify-py` removed from `requirements.txt` | `docs/tasks/evidence/T011/req_no_ipify.txt` | PASS — `0` |
| 2 | `ipify-py` not installed in dev container | `docs/tasks/evidence/T011/pip_no_ipify.txt` | PASS — `NOT_INSTALLED` |
| 3 | No `import ipify` / `from ipify` statements (anchored regex) | `docs/tasks/evidence/T011/no_ipify_imports.txt` | PASS — `CLEAN` |
| 4 | `timeout=` present in `ovh_client.py` | `docs/tasks/evidence/T011/ovh_timeout.txt` | PASS — `requests.get(url, auth=auth, timeout=OVH_HTTP_TIMEOUT)` |
| 5 | `timeout=` present in `ipify_client.py` | `docs/tasks/evidence/T011/ipify_timeout.txt` | PASS — `requests.get(IPIFY_URL, timeout=IPIFY_HTTP_TIMEOUT)` |
| 6 | `test_ipify_client.py` passes | `docs/tasks/evidence/T011/test_ipify.txt` | PASS — `5 passed in 0.48s` |
| 7 | `test_ovh_client.py` passes (incl. new tests) | `docs/tasks/evidence/T011/test_ovh.txt` | PASS — `10 passed in 0.35s` |
| 8 | Full suite + coverage gate (≥ 90%) | `docs/tasks/evidence/T011/tests_full.txt` | PASS — `221 passed`, coverage `95.80%` |
| 9 | `ruff check` clean | `docs/tasks/evidence/T011/ruff_check.txt` | PASS — `All checks passed!` |
| 10 | `ruff format --check` clean | `docs/tasks/evidence/T011/ruff_format.txt` | PASS — `44 files already formatted` |

### Design decisions

- **`ValueError` in the ipify catch.** `IPvAnyAddress("not-an-ip")` raises `ValueError`, not a Pydantic-specific exception. Catching only `requests.RequestException` would have let bad bodies (an HTML error page, captive-portal redirect, etc.) propagate as a non-`RuntimeError`. The new test `test_get_public_ip_raises_on_invalid_ip` covers this.
- **Tuple timeout `(5, 10)` instead of a single number.** `requests` accepts a tuple `(connect_timeout, read_timeout)`. Picked 5s for the connect handshake (slow network is rare with these endpoints) and 10s for the actual read (gives OVH some slack while still bounding the scheduler thread). The single-number form would apply the same value to both phases — less precise.
- **Two new OVH tests.** `test_update_ip_handles_timeout` exercises the failure path; `test_update_ip_passes_timeout` is a propagation test that introspects `mock_get.call_args` so we don't accidentally drop the kwarg in a future refactor without breaking a test.
- **Anchored grep for the import audit.** First evidence pass for #3 false-positive'd on the string `"Unable to fetch IP from ipify"` inside `RuntimeError(...)`. Switched to a line-anchored regex (`^(\s*from ipify|\s*import ipify)`) which only catches actual import statements.
- **No constants exposed for OVH host/path beyond what already exists.** `HOST`, `PATH`, `SYS_PARAM` were already module-level; added `OVH_HTTP_TIMEOUT` next to them.
