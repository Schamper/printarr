from __future__ import annotations

import abc
import logging
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

import httpx

from app.schemas.models import SearchResult

logger = logging.getLogger(__name__)


# Canonical sort values shared by all sources
SortOption = str  # "relevance" | "downloads" | "likes" | "newest"


@dataclass
class DiscoveredFile:
    """A file URL discovered from a source's model page."""

    filename: str
    url: str
    file_type: str = field(default="")
    size_bytes: int = field(default=0)


class SourceBase(abc.ABC):
    """Common interface for all model sources (indexers)."""

    name: str  # e.g. "thingiverse"
    display_name: str  # e.g. "Thingiverse"
    base_url: str
    requires_api_key: bool = False  # True if source won't work without API key
    api_key_label: str = "API Key"  # Human-readable label for the key field
    url_pattern: re.Pattern | None = None  # Regex to detect + extract source_id from a URL

    @classmethod
    def match_url(cls, url: str) -> str | None:
        """Return source_id string if url matches this source, None if not a match.

        An empty string means the source was recognised but has no extractable ID
        (the source must derive the ID itself from the URL).
        """
        if cls.url_pattern is None:
            return None
        m = cls.url_pattern.search(url)
        if not m:
            return None
        return m.group(1) if m.lastindex else ""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
                headers={"User-Agent": "Printarr/0.1"},
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    @abc.abstractmethod
    async def search(self, query: str, page: int = 1, sort: SortOption = "relevance") -> AsyncIterator[SearchResult]:
        """Yield search results one at a time."""
        ...

    async def fetch_files(self, source_id: str) -> list[DiscoveredFile]:  # noqa: ARG002
        """Return downloadable files for this model. Override per source."""
        return []

    async def fetch_model_metadata(self, url: str, source_id: str) -> SearchResult:  # noqa: ARG002
        """Fetch full model metadata from a canonical URL. Override per source."""
        raise NotImplementedError(f"{self.__class__.__name__} does not implement fetch_model_metadata")

    async def safe_search(self, query: str, page: int = 1, sort: SortOption = "relevance") -> AsyncIterator[SearchResult]:
        """Wrapper that catches exceptions so one broken source can't crash the stream.

        Logs the error and re-raises so the caller can emit a source_error event.
        """
        try:
            async for result in self.search(query, page, sort):
                yield result
        except Exception:
            logger.exception("Source %s failed for query %r", self.name, query)
            raise


# -- Registry --

_SOURCES: dict[str, type[SourceBase]] = {}


def register_source(cls: type[SourceBase]) -> type[SourceBase]:
    _SOURCES[cls.name] = cls
    return cls


def get_all_sources() -> dict[str, type[SourceBase]]:
    return dict(_SOURCES)


def get_source(name: str) -> type[SourceBase] | None:
    return _SOURCES.get(name)


def match_any_source(url: str) -> tuple[str, str] | None:
    """Return (source_name, source_id) for the first source whose url_pattern matches url."""
    for name, cls in _SOURCES.items():
        sid = cls.match_url(url)
        if sid is not None:
            return name, sid
    return None


# Import all sources to trigger registration
def _load_sources() -> None:
    import app.sources.cults3d  # noqa: F401
    import app.sources.makeronline  # noqa: F401
    import app.sources.makerworld  # noqa: F401
    import app.sources.printables  # noqa: F401
    import app.sources.thingiverse  # noqa: F401


_load_sources()
