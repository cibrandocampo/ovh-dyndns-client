"""Persisted runtime secrets for the OVH DynDNS service.

Two values that the runtime needs at every boot:

- ``JWT_SECRET``: signs/verifies access tokens.
- ``ENCRYPTION_KEY``: Fernet key used to encrypt OVH host passwords at rest
  (consumed by ``infrastructure.crypto`` from T008 onwards).

Both follow the same resolution order:

    env var > file under ``DATA_DIR`` > generate, persist, return

Files are created with mode ``0o600`` so only the container's user can read
them. ``DATA_DIR`` defaults to ``/app/data`` (the bind-mounted volume) and
can be overridden via env var, primarily for tests.
"""

import os
import secrets as _secrets
from pathlib import Path

DEFAULT_DATA_DIR = "/app/data"
JWT_SECRET_FILENAME = ".jwt_secret"
ENCRYPTION_KEY_FILENAME = ".encryption_key"
JWT_SECRET_BYTES = 32  # url-safe token, recommended length for HS256


def _data_dir() -> Path:
    """Resolve DATA_DIR on every call so tests can monkeypatch the env var."""
    return Path(os.getenv("DATA_DIR", DEFAULT_DATA_DIR))


def _jwt_secret_file() -> Path:
    return _data_dir() / JWT_SECRET_FILENAME


def _encryption_key_file() -> Path:
    return _data_dir() / ENCRYPTION_KEY_FILENAME


def get_or_create_jwt_secret() -> str:
    """Return the JWT signing secret.

    Resolution order: ``JWT_SECRET`` env var, then persisted file, then
    auto-generate a new 32-byte URL-safe token, persist it, and return it.
    """
    env = os.getenv("JWT_SECRET")
    if env:
        return env

    path = _jwt_secret_file()
    if path.exists():
        return path.read_text().strip()

    path.parent.mkdir(parents=True, exist_ok=True)
    new_secret = _secrets.token_urlsafe(JWT_SECRET_BYTES)
    path.write_text(new_secret)
    path.chmod(0o600)
    return new_secret


def get_or_create_encryption_key() -> bytes:
    """Return the Fernet key used to encrypt host passwords at rest.

    Resolution order matches ``get_or_create_jwt_secret``. Generates a fresh
    Fernet key (44-byte base64) when neither env var nor file is present.
    """
    from cryptography.fernet import Fernet

    env = os.getenv("ENCRYPTION_KEY")
    if env:
        return env.encode("utf-8")

    path = _encryption_key_file()
    if path.exists():
        return path.read_bytes().strip()

    path.parent.mkdir(parents=True, exist_ok=True)
    new_key = Fernet.generate_key()
    path.write_bytes(new_key)
    path.chmod(0o600)
    return new_key


def encryption_key_exists() -> bool:
    """True when a key is available without generating one (env var or file)."""
    return os.getenv("ENCRYPTION_KEY") is not None or _encryption_key_file().exists()
