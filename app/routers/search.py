from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.database import get_db
from app.services.search import stream_search

router = APIRouter(prefix="/api/search", tags=["search"])


VALID_SORTS = {"relevance", "downloads", "likes", "newest"}


@router.get("")
async def search(
    q: str = Query(..., min_length=1, max_length=200),
    page: int = Query(1, ge=1),
    sort: str = Query("relevance", description="Sort order: relevance, downloads, likes, newest"),
    sources: str | None = Query(None, description="Comma-separated source names"),
    db: AsyncSession = Depends(get_db),
):
    """Stream search results from all enabled sources via SSE."""
    if sort not in VALID_SORTS:
        sort = "relevance"
    sources_filter = [s.strip() for s in sources.split(",") if s.strip()] if sources else None

    return EventSourceResponse(
        stream_search(q, db, page=page, sources_filter=sources_filter, sort=sort),
        media_type="text/event-stream",
    )
