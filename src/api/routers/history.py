from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from api.dependencies import get_current_user
from infrastructure.database import SqliteRepository

router = APIRouter(prefix="/api/history", tags=["history"])


class HistoryEntry(BaseModel):
    id: int
    ip: Optional[str] = None
    timestamp: Optional[str] = None
    action: str
    hostname: Optional[str] = None
    details: Optional[str] = None


class HistoryResponse(BaseModel):
    entries: list[HistoryEntry]
    total: int
    limit: int
    offset: int


@router.get("/", response_model=HistoryResponse)
async def get_history(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """Get paginated history of DNS updates and changes."""
    repository = SqliteRepository()
    entries = repository.get_history(limit=limit, offset=offset)
    total = repository.get_history_count()

    return HistoryResponse(
        entries=[HistoryEntry(**entry) for entry in entries],
        total=total,
        limit=limit,
        offset=offset
    )
