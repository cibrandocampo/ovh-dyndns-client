"""Pytest auto-config shared by every test module.

Currently provides a single function-scoped autouse fixture that resets
the ``slowapi`` limiter before every test so login/change-password
counters do not leak between cases. Running existing test suites without
this would fail intermittently — TestClient requests all originate from
``127.0.0.1`` and slowapi keys buckets by client IP, so once one test
has consumed the bucket the next test cannot issue a login.
"""

import pytest


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Reset slowapi counters between tests to keep them independent."""
    try:
        from api.main import limiter

        limiter.reset()
    except Exception:  # pragma: no cover — defensive against early collection failures
        # If the app failed to import just yield; the test will fail with
        # a more useful error than a fixture crash.
        pass
    yield
