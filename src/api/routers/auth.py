from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.auth import verify_password, hash_password, create_access_token
from api.dependencies import get_current_user
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
async def login(request: LoginRequest):
    """Authenticate user and return JWT token."""
    repository = SqliteRepository()
    user = repository.get_user_by_username(request.username)

    if not user or not verify_password(request.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user["username"]})
    return TokenResponse(access_token=access_token, must_change_password=user["must_change_password"])


@router.post("/change-password", response_model=MessageResponse)
async def change_password(request: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    """Change user password."""
    repository = SqliteRepository()
    user = repository.get_user_by_username(current_user["username"])

    if not user or not verify_password(request.current_password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    new_hash = hash_password(request.new_password)
    repository.update_user_password(current_user["username"], new_hash)

    return MessageResponse(message="Password changed successfully")
