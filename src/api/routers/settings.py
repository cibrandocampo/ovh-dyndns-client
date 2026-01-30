from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from api.dependencies import get_current_user
from infrastructure.database import SqliteRepository

router = APIRouter(prefix="/api/settings", tags=["settings"])

# Callback to notify when settings change
_on_settings_change = None


def set_settings_change_callback(callback):
    """Set callback to be called when settings change."""
    global _on_settings_change
    _on_settings_change = callback


class SettingsResponse(BaseModel):
    update_interval: int
    logger_level: str


class SettingsUpdate(BaseModel):
    update_interval: Optional[int] = Field(None, ge=60, le=86400, description="Update interval in seconds (60-86400)")
    logger_level: Optional[str] = Field(None, pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")


@router.get("/", response_model=SettingsResponse)
async def get_settings(current_user: dict = Depends(get_current_user)):
    """Get current application settings."""
    repository = SqliteRepository()
    return repository.get_settings()


@router.put("/", response_model=SettingsResponse)
async def update_settings(settings: SettingsUpdate, current_user: dict = Depends(get_current_user)):
    """Update application settings."""
    repository = SqliteRepository()
    result = repository.update_settings(
        update_interval=settings.update_interval,
        logger_level=settings.logger_level
    )

    # Notify about settings change
    if _on_settings_change:
        _on_settings_change(result)

    return result
