from __future__ import annotations

import logging
import re
from collections.abc import AsyncIterator

from app.schemas.models import SearchResult
from app.sources.base import DiscoveredFile, SortOption, SourceBase, register_source

logger = logging.getLogger(__name__)

# MakerOnline CDN base
_CDN = "https://cdn-acop.makeronline.com"

# Model page URL: https://www.makeronline.com/model/{slug}/{id}.html
_MODEL_URL_BASE = "https://www.makeronline.com/model"


def _make_slug(title: str) -> str:
    """Build a URL slug from a model title the same way MakerOnline does."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", title)
    return slug.strip("-")


@register_source
class MakerOnlineSource(SourceBase):
    """Source for makeronline.com"""

    name = "makeronline"
    display_name = "MakerOnline"
    base_url = "https://www.makeronline.com"
    url_pattern = re.compile(r"makeronline\.com/model/[^/]+/(\d+)")
    _api_base = "https://makeronline.com"

    _SORT_MAP: dict[str, str] = {
        "relevance": "0",
        "downloads": "2",
        "likes": "1",
        "newest": "3",
    }

    _SEARCH_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Origin": "https://makeronline.com",
        "Referer": "https://makeronline.com/en/search/modelList",
    }

    async def search(self, query: str, page: int = 1, sort: SortOption = "relevance") -> AsyncIterator[SearchResult]:
        client = await self._get_client()
        per_page = 20
        offset = (page - 1) * per_page

        try:
            resp = await client.post(
                f"{self._api_base}/api/search/model",
                json={
                    "keyword": query,
                    "category_id": "",
                    "page": page,
                    "page_size": per_page,
                    "print_type": 0,
                    "pure_search": 0,
                    "sort": self._SORT_MAP.get(sort, "0"),
                },
                headers=self._SEARCH_HEADERS,
                timeout=20.0,
            )
            resp.raise_for_status()
        except Exception:
            logger.exception("MakerOnline search request failed for query %r", query)
            return

        data = resp.json()
        if data.get("code") != 0:
            logger.warning(
                "MakerOnline API error for %r: code=%s message=%s",
                query, data.get("code"), data.get("message"),
            )
            return

        items = data.get("data", {}).get("data", [])
        if not isinstance(items, list):
            return

        for item in items:
            model_id = str(item.get("mold_id", "") or item.get("id", ""))
            title = item.get("title", "")
            if not (model_id and title):
                continue

            # Prefer the API-provided URL; fall back to slug construction.
            url = item.get("target_url") or f"{self.base_url}/model/{_make_slug(title)}/{model_id}.html"
            thumbnail = item.get("mold_image", "")

            yield SearchResult(
                source=self.name,
                source_id=model_id,
                name=title,
                url=url,
                thumbnail_url=thumbnail,
                author=item.get("show_user_name", item.get("user_name", "")),
                description=(item.get("description", "") or "")[:500],
                download_count=item.get("download_num", 0) or 0,
                like_count=item.get("like_num", 0) or 0,
            )

    async def fetch_model_metadata(self, url: str, source_id: str) -> SearchResult:
        """Scrape the model page for full metadata."""
        from bs4 import BeautifulSoup

        client = await self._get_client()
        try:
            resp = await client.get(
                url,
                headers={
                    "User-Agent": self._SEARCH_HEADERS["User-Agent"],
                    "Accept": "text/html,application/xhtml+xml",
                },
                timeout=20.0,
            )
            resp.raise_for_status()
        except Exception:
            logger.exception("MakerOnline fetch_model_metadata failed for %s", url)
            return SearchResult(source=self.name, source_id=source_id, name="", url=url)

        soup = BeautifulSoup(resp.text, "html.parser")
        og_title = soup.select_one("meta[property='og:title']")
        name = og_title["content"] if og_title and og_title.get("content") else ""
        if not name:
            h1 = soup.select_one("h1")
            name = h1.get_text(strip=True) if h1 else ""
        og_img = soup.select_one("meta[property='og:image']")
        thumbnail = og_img["content"] if og_img and og_img.get("content") else ""
        og_desc = soup.select_one("meta[property='og:description'], meta[name='description']")
        description = (og_desc["content"] if og_desc and og_desc.get("content") else "")[:500]

        return SearchResult(
            source=self.name,
            source_id=source_id,
            name=name,
            url=url,
            thumbnail_url=thumbnail,
            description=description,
        )

    async def fetch_files(self, source_id: str) -> list[DiscoveredFile]:
        """MakerOnline files require authentication; not publicly accessible."""
        return []
