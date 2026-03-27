from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings import IndexerConfig
from app.sources.base import SourceBase, get_all_sources

logger = logging.getLogger(__name__)


async def _get_enabled_sources(db: AsyncSession) -> list[SourceBase]:
    """Instantiate enabled source modules with their stored API keys."""
    source_classes = get_all_sources()
    result = await db.execute(select(IndexerConfig))
    configs: dict[str, IndexerConfig] = {c.name: c for c in result.scalars().all()}

    sources: list[SourceBase] = []
    for name, cls in source_classes.items():
        cfg = configs.get(name)
        if cfg and not cfg.enabled:
            continue
        api_key = cfg.api_key if cfg else ""
        sources.append(cls(api_key=api_key))
    return sources


async def _search_single_source(
    source: SourceBase,
    query: str,
    page: int,
    library_ids: set[str],
    sort: str = "relevance",
) -> list[dict]:
    """Collect SSE events for a single source."""
    events: list[dict] = []
    count = 0
    try:
        async for result in source.safe_search(query, page, sort):
            result.in_library = f"{result.source}:{result.source_id}" in library_ids
            events.append({"event": "result", "data": result.model_dump(mode="json")})
            count += 1
    except Exception:
        logger.exception("Source %s failed", source.name)
        events.append({"event": "source_error", "data": {"source": source.name, "display_name": source.display_name}})
        return events
    finally:
        await source.close()

    events.append({"event": "source_done", "data": {"source": source.name, "count": count}})
    return events


async def stream_search(
    query: str,
    db: AsyncSession,
    page: int = 1,
    sources_filter: list[str] | None = None,
    sort: str = "relevance",
) -> AsyncIterator[dict]:
    """Main search generator that yields dicts for sse-starlette."""
    from app.models.library import LibraryModel

    sources = await _get_enabled_sources(db)
    if sources_filter:
        sources = [s for s in sources if s.name in sources_filter]

    # Get library model IDs for "in_library" flag
    lib_result = await db.execute(select(LibraryModel.source, LibraryModel.source_id))
    library_ids = {f"{row[0]}:{row[1]}" for row in lib_result.all()}

    # Emit source_start for ALL sources upfront so the UI shows them immediately
    for source in sources:
        configured = not source.requires_api_key or bool(source.api_key)
        yield {
            "event": "source_start",
            "data": json.dumps(
                {
                    "source": source.name,
                    "display_name": source.display_name,
                    "configured": configured,
                }
            ),
        }

    # Only actually search sources that are configured
    runnable = [s for s in sources if not s.requires_api_key or bool(s.api_key)]

    # Run all runnable sources concurrently, yield events as each completes
    tasks = {asyncio.create_task(_search_single_source(s, query, page, library_ids, sort)): s.name for s in runnable}

    for coro in asyncio.as_completed(tasks):
        events = await coro
        for ev in events:
            yield {
                "event": ev["event"],
                "data": json.dumps(ev.get("data", ""), default=str),
            }

    yield {"event": "done", "data": "{}"}
