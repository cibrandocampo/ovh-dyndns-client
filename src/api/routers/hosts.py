from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from api.dependencies import get_current_user
from infrastructure.database import SqliteRepository

router = APIRouter(prefix="/api/hosts", tags=["hosts"])


class HostCreate(BaseModel):
    hostname: str
    username: str
    password: str


class HostUpdate(BaseModel):
    hostname: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


class HostResponse(BaseModel):
    id: int
    hostname: str
    username: str
    last_update: Optional[str] = None
    last_status: Optional[bool] = None
    last_error: Optional[str] = None
    created_at: Optional[str] = None


@router.get("/", response_model=list[HostResponse])
async def list_hosts(current_user: dict = Depends(get_current_user)):
    """List all configured hosts."""
    repository = SqliteRepository()
    return repository.get_all_hosts()


@router.post("/", response_model=HostResponse, status_code=status.HTTP_201_CREATED)
async def create_host(host: HostCreate, current_user: dict = Depends(get_current_user)):
    """Create a new host."""
    repository = SqliteRepository()
    try:
        return repository.create_host(
            hostname=host.hostname,
            username=host.username,
            password=host.password
        )
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Host with hostname '{host.hostname}' already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{host_id}", response_model=HostResponse)
async def get_host(host_id: int, current_user: dict = Depends(get_current_user)):
    """Get a specific host by ID."""
    repository = SqliteRepository()
    host = repository.get_host_by_id(host_id)
    if not host:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Host with ID {host_id} not found"
        )
    return host


@router.put("/{host_id}", response_model=HostResponse)
async def update_host(host_id: int, host: HostUpdate, current_user: dict = Depends(get_current_user)):
    """Update an existing host."""
    repository = SqliteRepository()
    updated = repository.update_host(
        host_id=host_id,
        hostname=host.hostname,
        username=host.username,
        password=host.password
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Host with ID {host_id} not found"
        )
    return updated


@router.delete("/{host_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_host(host_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a host."""
    repository = SqliteRepository()
    if not repository.delete_host(host_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Host with ID {host_id} not found"
        )
