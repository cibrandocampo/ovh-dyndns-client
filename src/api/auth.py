import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from jwt.exceptions import PyJWTError

from infrastructure.secrets import get_or_create_jwt_secret

DEFAULT_JWT_EXPIRATION_HOURS = 24
ALGORITHM = "HS256"


def get_jwt_secret() -> str:
    return get_or_create_jwt_secret()


def get_jwt_expiration_hours() -> int:
    try:
        return int(os.getenv("JWT_EXPIRATION_HOURS", DEFAULT_JWT_EXPIRATION_HOURS))
    except ValueError:
        return DEFAULT_JWT_EXPIRATION_HOURS


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


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
