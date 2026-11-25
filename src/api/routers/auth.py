from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator

from api.auth import (
    BCRYPT_MAX_BYTES,
    create_access_token,
    dummy_password_hash,
    hash_password,
    password_fingerprint,
    verify_password,
)
from api.dependencies import get_authenticated_user
from api.main import limiter
from infrastructure.database import SqliteRepository

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    must_change_password: bool = False


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)

    @field_validator("new_password")
    @classmethod
    def _fits_bcrypt(cls, value: str) -> str:
        if len(value.encode("utf-8")) > BCRYPT_MAX_BYTES:
            raise ValueError(f"password must be at most {BCRYPT_MAX_BYTES} bytes")
        return value


class ChangePasswordResponse(BaseModel):
    message: str
    access_token: str
    token_type: str = "bearer"


def _issue_token(username: str, password_hash: str) -> str:
    return create_access_token(data={"sub": username, "pwd": password_fingerprint(password_hash)})


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(request: Request, payload: LoginRequest):
    """Authenticate user and return JWT token.

    Rate-limited to 5 requests per minute per client IP to mitigate
    brute-force attempts. `request` is required for slowapi to extract
    the client address; the JSON body lives in `payload`.
    """
    repository = SqliteRepository()
    user = repository.get_user_by_username(payload.username)
    password_hash = user["password_hash"] if user else dummy_password_hash()

    if not verify_password(payload.password, password_hash) or not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = _issue_token(user["username"], user["password_hash"])
    return TokenResponse(access_token=access_token, must_change_password=user["must_change_password"])


@router.post("/change-password", response_model=ChangePasswordResponse)
@limiter.limit("10/minute")
def change_password(
    request: Request,
    payload: ChangePasswordRequest,
    current_user: dict = Depends(get_authenticated_user),
):
    """Change user password.

    Rate-limited to 10 requests per minute per client IP. Every token issued
    before the change is revoked; the response carries a fresh one.
    """
    repository = SqliteRepository()
    user = repository.get_user_by_username(current_user["username"])

    if not user or not verify_password(payload.current_password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    new_hash = hash_password(payload.new_password)
    repository.update_user_password(current_user["username"], new_hash)

    return ChangePasswordResponse(
        message="Password changed successfully",
        access_token=_issue_token(current_user["username"], new_hash),
    )
