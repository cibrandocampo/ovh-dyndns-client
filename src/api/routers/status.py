from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.dependencies import get_current_user
from infrastructure.database import SqliteRepository

router = APIRouter(prefix="/api/status", tags=["status"])

# Global reference to controller (set by main.py)
_controller = None


def set_controller(controller):
    """Set the controller instance for triggering updates."""
    global _controller
    _controller = controller


class HostStatus(BaseModel):
    id: int
    hostname: str
    last_update: Optional[str] = None
    last_status: Optional[bool] = None
    last_error: Optional[str] = None


class StatusResponse(BaseModel):
    current_ip: Optional[str] = None
    last_check: Optional[str] = None
    hosts: list[HostStatus]


class TriggerResponse(BaseModel):
    message: str
    success: bool


@router.get("/", response_model=StatusResponse)
async def get_status(current_user: dict = Depends(get_current_user)):
    """Get current IP and status of all hosts."""
    repository = SqliteRepository()
    state = repository.get_state()
    hosts = repository.get_all_hosts()

    return StatusResponse(
        current_ip=state.get("current_ip"),
        last_check=state.get("last_check"),
        hosts=[
            HostStatus(
                id=h["id"],
                hostname=h["hostname"],
                last_update=h["last_update"],
                last_status=h["last_status"],
                last_error=h["last_error"]
            )
            for h in hosts
        ]
    )


@router.post("/trigger", response_model=TriggerResponse)
async def trigger_update(current_user: dict = Depends(get_current_user)):
    """Trigger an immediate DNS update."""
    if _controller is None:
        raise HTTPException(
            status_code=500,
            detail="Controller not initialized"
        )

    try:
        _controller.handler()
        return TriggerResponse(message="DNS update triggered successfully", success=True)
    except Exception as e:
        return TriggerResponse(message=f"DNS update failed: {str(e)}", success=False)
