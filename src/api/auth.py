import hashlib
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from jwt.exceptions import PyJWTError

from infrastructure.secrets import get_or_create_jwt_secret

DEFAULT_JWT_EXPIRATION_HOURS = 24
ALGORITHM = "HS256"
BCRYPT_MAX_BYTES = 72


def get_jwt_secret() -> str:
    return get_or_create_jwt_secret()


def get_jwt_expiration_hours() -> int:
    try:
        return int(os.getenv("JWT_EXPIRATION_HOURS", DEFAULT_JWT_EXPIRATION_HOURS))
    except ValueError:
        return DEFAULT_JWT_EXPIRATION_HOURS


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.

    bcrypt raises on inputs over 72 bytes; no stored password can be that
    long, so such input simply does not match.
    """
    plain = plain_password.encode("utf-8")
    if len(plain) > BCRYPT_MAX_BYTES:
        return False
    return bcrypt.checkpw(plain, hashed_password.encode("utf-8"))


def password_fingerprint(password_hash: str) -> str:
    """Short digest of the stored hash, embedded in tokens as the `pwd` claim.

    The bcrypt hash is re-salted on every change, so tokens issued before a
    password change stop matching and are rejected.
    """
    return hashlib.sha256(password_hash.encode("utf-8")).hexdigest()[:16]


def hash_password(password: str) -> str:
    """Hash a password for storage."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=get_jwt_expiration_hours()))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, get_jwt_secret(), algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token."""
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[ALGORITHM])
        return payload
    except PyJWTError:
        return None


def get_admin_credentials() -> tuple[str, str]:
    """Get admin credentials from environment variables."""
    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD", "admin")
    return username, password
