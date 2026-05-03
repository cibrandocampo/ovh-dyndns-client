from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from api.auth import create_access_token, hash_password, verify_password
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


class MessageResponse(BaseModel):
    message: str


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, payload: LoginRequest):
    """Authenticate user and return JWT token.

    Rate-limited to 5 requests per minute per client IP to mitigate
    brute-force attempts. `request` is required for slowapi to extract
    the client address; the JSON body lives in `payload`.
    """
    repository = SqliteRepository()
    user = repository.get_user_by_username(payload.username)

    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user["username"]})
    return TokenResponse(access_token=access_token, must_change_password=user["must_change_password"])


@router.post("/change-password", response_model=MessageResponse)
@limiter.limit("10/minute")
async def change_password(
    request: Request,
    payload: ChangePasswordRequest,
    current_user: dict = Depends(get_authenticated_user),
):
    """Change user password.

    Rate-limited to 10 requests per minute per client IP.
    """
    repository = SqliteRepository()
    user = repository.get_user_by_username(current_user["username"])

    if not user or not verify_password(payload.current_password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    new_hash = hash_password(payload.new_password)
    repository.update_user_password(current_user["username"], new_hash)

    return MessageResponse(message="Password changed successfully")
