import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import IntegrityError

from api.dependencies import get_current_user
from infrastructure.database import SqliteRepository
from infrastructure.logger import Logger

router = APIRouter(prefix="/api/hosts", tags=["hosts"])
logger = Logger.get_logger()

# Fully qualified domain name: dot-separated labels of 1-63 letters, digits or
# hyphens (no leading/trailing hyphen), at least two labels, 253 chars max.
_LABEL = r"(?!-)[A-Za-z0-9-]{1,63}(?<!-)"
FQDN_RE = re.compile(rf"^(?=.{{1,253}}$){_LABEL}(?:\.{_LABEL})+$")


def _validate_hostname(value: Optional[str]) -> Optional[str]:
    if value is not None and not FQDN_RE.match(value):
        raise ValueError("hostname must be a valid fully qualified domain name")
    return value


class HostCreate(BaseModel):
    hostname: str
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

    _check_hostname = field_validator("hostname")(_validate_hostname)


class HostUpdate(BaseModel):
    hostname: Optional[str] = None
    username: Optional[str] = Field(None, min_length=1)
    password: Optional[str] = Field(None, min_length=1)

    _check_hostname = field_validator("hostname")(_validate_hostname)


def _host_exists(hostname: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Host with hostname '{hostname}' already exists")


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
        return repository.create_host(hostname=host.hostname, username=host.username, password=host.password)
    except IntegrityError:
        raise _host_exists(host.hostname)
    except Exception:
        logger.exception(f"{host.hostname} | Failed to create host")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create host")


@router.get("/{host_id}", response_model=HostResponse)
async def get_host(host_id: int, current_user: dict = Depends(get_current_user)):
    """Get a specific host by ID."""
    repository = SqliteRepository()
    host = repository.get_host_by_id(host_id)
    if not host:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Host with ID {host_id} not found")
    return host


@router.put("/{host_id}", response_model=HostResponse)
async def update_host(host_id: int, host: HostUpdate, current_user: dict = Depends(get_current_user)):
    """Update an existing host."""
    repository = SqliteRepository()
    try:
        updated = repository.update_host(
            host_id=host_id, hostname=host.hostname, username=host.username, password=host.password
        )
    except IntegrityError:
        raise _host_exists(host.hostname)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Host with ID {host_id} not found")
    return updated


@router.delete("/{host_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_host(host_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a host."""
    repository = SqliteRepository()
    if not repository.delete_host(host_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Host with ID {host_id} not found")
