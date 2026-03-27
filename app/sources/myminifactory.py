from __future__ import annotations

import logging
import re
from collections.abc import AsyncIterator

from app.schemas.models import SearchResult
from app.sources.base import DiscoveredFile, SortOption, SourceBase, register_source

logger = logging.getLogger(__name__)


@register_source
class MyMiniFactorySource(SourceBase):
    name = "myminifactory"
    display_name = "MyMiniFactory"
    base_url = "https://www.myminifactory.com/api/v2"
    requires_api_key = True
    url_pattern = re.compile(r"myminifactory\.com/object[/-]([^\s?#/]+)")
    api_key_label = "API Key"

    _SORT_MAP: dict[str, str] = {
        "relevance": "",
        "downloads": "downloads",
        "likes": "likes",
        "newest": "date",
    }

    async def search(self, query: str, page: int = 1, sort: SortOption = "relevance") -> AsyncIterator[SearchResult]:
        if not self.api_key:
            logger.warning("MyMiniFactory API key not configured, skipping")
            return

        client = await self._get_client()
        per_page = 20
        params: dict[str, str | int] = {"q": query, "page": page, "per_page": per_page}
        if self.api_key:
            params["key"] = self.api_key
        mmf_sort = self._SORT_MAP.get(sort, "")
        if mmf_sort:
            params["sort_by"] = mmf_sort
        resp = await client.get(
            f"{self.base_url}/search",
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()

        items = data.get("items", data.get("objects", []))
        for item in items:
            obj_id = item.get("id", "")
            yield SearchResult(
                source=self.name,
                source_id=str(obj_id),
                name=item.get("name", ""),
                url=item.get("url", f"https://www.myminifactory.com/object/{obj_id}"),
                author=item.get("designer", {}).get("username", "") if isinstance(item.get("designer"), dict) else "",
                thumbnail_url=item.get("images", [{}])[0].get("thumbnail", {}).get("url", "") if item.get("images") else "",
                description=(item.get("description", "") or "")[:500],
                license=item.get("license", ""),
                download_count=item.get("downloads", 0) or 0,
                like_count=item.get("likes", 0) or 0,
            )

    async def fetch_model_metadata(self, url: str, source_id: str) -> SearchResult:
        client = await self._get_client()
        params: dict = {}
        if self.api_key:
            params["key"] = self.api_key
        resp = await client.get(f"{self.base_url}/objects/{source_id}", params=params)
        if resp.status_code == 200:
            item = resp.json()
            thumb = ""
            if item.get("images"):
                thumb = item["images"][0].get("thumbnail", {}).get("url", "")
            return SearchResult(
                source=self.name,
                source_id=str(source_id),
                name=item.get("name", ""),
                url=item.get("url", url),
                author=item.get("designer", {}).get("username", "") if isinstance(item.get("designer"), dict) else "",
                thumbnail_url=thumb,
                description=(item.get("description", "") or "")[:500],
                download_count=item.get("downloads", 0) or 0,
                like_count=item.get("likes", 0) or 0,
            )
        return SearchResult(source=self.name, source_id=str(source_id), name="", url=url)

    async def fetch_files(self, source_id: str) -> list[DiscoveredFile]:
        client = await self._get_client()
        params: dict = {}
        if self.api_key:
            params["key"] = self.api_key
        try:
            resp = await client.get(f"{self.base_url}/objects/{source_id}", params=params)
            resp.raise_for_status()
        except Exception:
            logger.exception("MyMiniFactory fetch_files failed for %s", source_id)
            return []

        results: list[DiscoveredFile] = []
        for f in resp.json().get("files", []):
            url = f.get("download_url", "")
            filename = f.get("filename", f.get("name", ""))
            if url and filename:
                results.append(DiscoveredFile(filename=filename, url=url))
        return results
