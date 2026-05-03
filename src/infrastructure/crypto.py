"""Symmetric encryption for OVH host passwords at rest.

Uses Fernet (AES-128-CBC + HMAC-SHA256, authenticated). Stored values carry
a version prefix (`enc:v1:`) so the repository can tell ciphertext apart
from legacy plaintext during the boot-time migration in
``infrastructure.database.migrate_plaintext_passwords``.
"""

from cryptography.fernet import Fernet, InvalidToken

from infrastructure.secrets import get_or_create_encryption_key

ENCRYPTED_PREFIX = "enc:v1:"


def _fernet() -> Fernet:
    """Build a Fernet using the runtime encryption key.

    Resolved on every call so changes to the underlying key (env var,
    persisted file) take effect immediately and tests can rotate keys.
    """
    return Fernet(get_or_create_encryption_key())


def is_encrypted(value: str) -> bool:
    """True when the stored value carries the version prefix."""
    return value.startswith(ENCRYPTED_PREFIX)


def encrypt_password(plain: str) -> str:
    """Encrypt and return ``enc:v1:<base64-fernet-token>``."""
    token = _fernet().encrypt(plain.encode("utf-8")).decode("utf-8")
    return f"{ENCRYPTED_PREFIX}{token}"


def decrypt_password(stored: str) -> str:
    """Decrypt a stored password.

    Values without the version prefix are returned untouched (legacy
    plaintext). The boot-time migration is responsible for upgrading them
    on the next start-up; reads in the meantime keep working.

    Raises ``RuntimeError`` if a value WITH the prefix fails to decrypt
    (e.g. the encryption key was rotated without re-encrypting hosts).
    """
    if not is_encrypted(stored):
        return stored
    payload = stored[len(ENCRYPTED_PREFIX) :]
    try:
        return _fernet().decrypt(payload.encode("utf-8")).decode("utf-8")
    except InvalidToken as e:
        raise RuntimeError("Failed to decrypt host password. Encryption key may have changed.") from e
