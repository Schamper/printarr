from __future__ import annotations

import logging
import re
from collections.abc import AsyncIterator

from bs4 import BeautifulSoup

from app.schemas.models import SearchResult
from app.sources.base import DiscoveredFile, SortOption, SourceBase, register_source

logger = logging.getLogger(__name__)


@register_source
class ThingiverseSource(SourceBase):
    name = "thingiverse"
    display_name = "Thingiverse"
    base_url = "https://www.thingiverse.com"
    url_pattern = re.compile(r"thingiverse\.com/thing[:/](\d+)")
    _api_url = "https://api.thingiverse.com"
    requires_api_key = True
    api_key_label = "App Token"

    _SORT_MAP: dict[str, str] = {
        "relevance": "relevant",
        "downloads": "popular",
        "likes": "makes",
        "newest": "newest",
    }

    async def search(self, query: str, page: int = 1, sort: SortOption = "relevance") -> AsyncIterator[SearchResult]:
        if not self.api_key:
            logger.warning("Thingiverse API token not configured, skipping")
            return

        client = await self._get_client()
        per_page = 20
        resp = await client.get(
            f"{self._api_url}/search/{query}",
            params={"page": page, "per_page": per_page, "sort": self._SORT_MAP.get(sort, "relevant")},
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        resp.raise_for_status()
        data = resp.json()

        hits = data if isinstance(data, list) else data.get("hits", data.get("items", []))
        for item in hits:
            yield SearchResult(
                source=self.name,
                source_id=str(item.get("id", "")),
                name=item.get("name", ""),
                url=item.get("public_url", f"{self.base_url}/thing:{item.get('id')}"),
                author=item.get("creator", {}).get("name", "") if isinstance(item.get("creator"), dict) else "",
                thumbnail_url=item.get("preview_image") or item.get("thumbnail", ""),
                description=item.get("description", "")[:500],
                license=item.get("license", ""),
                download_count=item.get("download_count", 0) or 0,
                like_count=item.get("like_count", 0) or 0,
            )

    async def fetch_model_metadata(self, url: str, source_id: str) -> SearchResult:
        client = await self._get_client()
        resp = await client.get(
            f"{self._api_url}/things/{source_id}",
            headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
        )
        if resp.status_code == 200:
            item = resp.json()
            return SearchResult(
                source=self.name,
                source_id=str(source_id),
                name=item.get("name", ""),
                url=item.get("public_url", url),
                author=item.get("creator", {}).get("name", "") if isinstance(item.get("creator"), dict) else "",
                thumbnail_url=item.get("thumbnail", ""),
                description=(item.get("description", "") or "")[:500],
                download_count=item.get("download_count", 0) or 0,
                like_count=item.get("like_count", 0) or 0,
            )
        # Fallback: scrape HTML
        resp = await client.get(url, headers={"Accept": "text/html"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        title_tag = soup.select_one('meta[property="og:title"]')
        name = title_tag["content"] if title_tag and title_tag.get("content") else ""
        img_tag = soup.select_one('meta[property="og:image"]')
        thumb = img_tag["content"] if img_tag and img_tag.get("content") else ""
        return SearchResult(source=self.name, source_id=str(source_id), name=name, url=url, thumbnail_url=thumb)

    async def fetch_files(self, source_id: str) -> list[DiscoveredFile]:
        if not self.api_key:
            return []
        client = await self._get_client()
        try:
            resp = await client.get(
                f"{self._api_url}/things/{source_id}/files",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            resp.raise_for_status()
        except Exception:
            logger.exception("Thingiverse fetch_files failed for %s", source_id)
            return []

        results: list[DiscoveredFile] = []
        for f in resp.json() if isinstance(resp.json(), list) else []:
            name = f.get("name", "")
            url = f.get("download_url", "")
            if name and url:
                results.append(DiscoveredFile(filename=name, url=url))
        return results
