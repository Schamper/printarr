from __future__ import annotations

import json
import logging
import re
from collections.abc import AsyncIterator

from curl_cffi.requests import AsyncSession

from app.schemas.models import SearchResult
from app.sources.base import DiscoveredFile, SortOption, SourceBase, register_source

logger = logging.getLogger(__name__)

PER_PAGE = 20


@register_source
class MakerWorldSource(SourceBase):
    name = "makerworld"
    display_name = "MakerWorld"
    base_url = "https://makerworld.com"
    url_pattern = re.compile(r"makerworld\.com/(?:\w+/)?models/(\d+)")

    _cffi_session: AsyncSession | None = None
    _build_id: str | None = None

    async def _get_session(self) -> AsyncSession:
        if self._cffi_session is None:
            self._cffi_session = AsyncSession(impersonate="chrome")
        return self._cffi_session

    _SORT_MAP: dict[str, str] = {
        "relevance": "",
        "downloads": "downloadCount",
        "likes": "likeCount",
        "newest": "newUploads",
    }

    async def _ensure_build_id(self, session: AsyncSession, query: str, sort: str = "relevance") -> tuple[str, list[dict]]:
        """Fetch the HTML search page once to obtain the Next.js buildId and page-1 designs."""
        resp = await session.get(
            f"{self.base_url}/en/search/models",
            params={"keyword": query},
        )
        resp.raise_for_status()
        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', resp.text, re.DOTALL)
        if not m:
            logger.warning("MakerWorld: __NEXT_DATA__ not found in HTML")
            return "", []
        data = json.loads(m.group(1))
        build_id = data.get("buildId", "")
        designs = data.get("props", {}).get("pageProps", {}).get("designs", [])
        return build_id, designs

    async def search(self, query: str, page: int = 1, sort: SortOption = "relevance") -> AsyncIterator[SearchResult]:
        # MakerWorld does not support server-side sorting; results are always by relevance
        session = await self._get_session()
        offset = (page - 1) * PER_PAGE

        if page == 1:
            self._build_id, designs = await self._ensure_build_id(session, query)
        else:
            if not self._build_id:
                self._build_id, _ = await self._ensure_build_id(session, query)
            resp = await session.get(
                f"{self.base_url}/_next/data/{self._build_id}/en/search/models.json",
                params={"keyword": query, "offset": str(offset)},
            )
            resp.raise_for_status()
            designs = resp.json().get("pageProps", {}).get("designs", [])

        for item in designs:
            design_id = item.get("id", item.get("designId", ""))
            slug = item.get("slug", "")
            creator = item.get("designCreator", {}) or {}

            yield SearchResult(
                source=self.name,
                source_id=str(design_id),
                name=item.get("title", item.get("name", "")),
                url=f"{self.base_url}/en/models/{design_id}{'-' + slug if slug else ''}",
                author=creator.get("name", "") if isinstance(creator, dict) else "",
                thumbnail_url=item.get("cover", item.get("thumbnail", "")),
                description=(item.get("description", "") or "")[:500],
                download_count=item.get("downloadCount", 0) or 0,
                like_count=item.get("likeCount", 0) or 0,
            )

    async def fetch_model_metadata(self, url: str, source_id: str) -> SearchResult:
        session = await self._get_session()
        resp = await session.get(url)
        resp.raise_for_status()

        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', resp.text, re.DOTALL)
        if not m:
            raise ValueError("Could not parse MakerWorld model page")
        data = json.loads(m.group(1))
        design = data.get("props", {}).get("pageProps", {}).get("design", {})
        if not design:
            raise ValueError("Model not found on MakerWorld")
        creator = design.get("designCreator", {}) or {}
        slug = design.get("slug", "")
        return SearchResult(
            source=self.name,
            source_id=str(design.get("id", source_id)),
            name=design.get("title", design.get("name", "")),
            url=f"{self.base_url}/en/models/{source_id}{'-' + slug if slug else ''}",
            author=creator.get("name", "") if isinstance(creator, dict) else "",
            thumbnail_url=design.get("cover", design.get("thumbnail", "")),
            description=(design.get("description", "") or "")[:500],
            download_count=design.get("downloadCount", 0) or 0,
            like_count=design.get("likeCount", 0) or 0,
        )

    async def close(self) -> None:
        if self._cffi_session:
            await self._cffi_session.close()
            self._cffi_session = None
        await super().close()

    async def fetch_files(self, source_id: str) -> list[DiscoveredFile]:
        session = await self._get_session()
        try:
            resp = await session.get(f"{self.base_url}/en/models/{source_id}")
            resp.raise_for_status()
        except Exception:
            logger.exception("MakerWorld fetch_files failed for %s", source_id)
            return []

        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', resp.text, re.DOTALL)
        if not m:
            return []
        try:
            data = json.loads(m.group(1))
        except Exception:
            return []

        design = data.get("props", {}).get("pageProps", {}).get("design", {})
        # MakerWorld stores files under designExtension.model_files.
        # modelUrl is only populated for authenticated users; fall back to the
        # model page URL so the user can download manually after logging in.
        model_page_url = f"{self.base_url}/en/models/{source_id}"
        raw_files = (design.get("designExtension") or {}).get("model_files") or []

        results: list[DiscoveredFile] = []
        for f in raw_files:
            filename = f.get("modelName", "")
            url = f.get("modelUrl") or model_page_url
            if filename:
                results.append(
                    DiscoveredFile(
                        filename=filename,
                        url=url,
                        size_bytes=int(f.get("modelSize") or 0),
                    )
                )
        return results
