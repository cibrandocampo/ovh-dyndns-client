import hmac

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from infrastructure.database import SqliteRepository

from .auth import decode_token, password_fingerprint

security = HTTPBearer()


async def get_authenticated_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Verify the JWT and return the user payload.

    Low-level dependency that only checks the token signature and the
    presence of a `sub` claim. Does NOT enforce `must_change_password`.
    Use this only for endpoints that must remain accessible during the
    forced password-change flow (currently just `/api/auth/change-password`).
    """
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

    # Tokens are bound to the password they were issued for: a password
    # change (or a deleted user) revokes every token issued before it.
    user = SqliteRepository().get_user_by_username(username)
    if user is None or not hmac.compare_digest(
        str(payload.get("pwd", "")), password_fingerprint(user["password_hash"])
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"username": username}


async def get_current_user(user: dict = Depends(get_authenticated_user)) -> dict:
    """Verify the JWT and ensure the user has changed their password.

    Default dependency for protected endpoints. Returns 403 when the user
    still has `must_change_password=True`, blocking the entire API except
    for the change-password route until the password is rotated.
    """
    repository = SqliteRepository()
    if repository.get_user_must_change_password(user["username"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Password change required",
        )
    return user
