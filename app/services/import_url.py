from __future__ import annotations

from app.schemas.models import SearchResult
from app.sources.base import get_source, match_any_source


async def fetch_from_url(url: str) -> SearchResult:
    """Fetch model metadata from a source URL by delegating to the source class."""
    ident = match_any_source(url)
    if not ident:
        raise ValueError(f"Unrecognized model URL: {url}")

    source_name, source_id = ident
    source_cls = get_source(source_name)
    if not source_cls:
        raise ValueError(f"Source not registered: {source_name}")

    instance = source_cls()
    try:
        return await instance.fetch_model_metadata(url, source_id)
    finally:
        await instance.close()
