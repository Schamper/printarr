from __future__ import annotations

import logging
import re
from collections.abc import AsyncIterator

from bs4 import BeautifulSoup

from app.schemas.models import SearchResult
from app.sources.base import DiscoveredFile, SortOption, SourceBase, register_source  # noqa: F401

logger = logging.getLogger(__name__)


@register_source
class Cults3DSource(SourceBase):
    name = "cults3d"
    display_name = "Cults3D"
    base_url = "https://cults3d.com"
    url_pattern = re.compile(r"cults3d\.com/")

    # Cults3D uses URL path segments for sort, not query params
    _SORT_MAP: dict[str, str] = {
        "relevance": "",
        "downloads": "most-downloaded",
        "likes": "most-liked",
        "newest": "latest",
    }

    async def search(self, query: str, page: int = 1, sort: SortOption = "relevance") -> AsyncIterator[SearchResult]:
        client = await self._get_client()
        params: dict[str, str | int] = {"q": query, "page": page}
        cults_sort = self._SORT_MAP.get(sort, "")
        if cults_sort:
            params["sort"] = cults_sort
        resp = await client.get(
            f"{self.base_url}/en/search",
            params=params,
            headers={"Accept": "text/html"},
        )
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        # Cults3D uses <article class="crea tbox ..."> for each result card
        cards = soup.select("article.crea")

        for card in cards:
            link_tag = card.select_one("a.tbox-thumb")
            if not link_tag:
                continue
            href = link_tag.get("href", "")
            if not href:
                continue
            url = href if href.startswith("http") else f"{self.base_url}{href}"

            name_tag = card.select_one(".drawer-title, .tbox-title")
            name = name_tag.get_text(strip=True) if name_tag else link_tag.get("title", "")

            img_tag = card.select_one("img.painting-image")
            thumb = ""
            if img_tag:
                thumb = img_tag.get("data-src", "") or img_tag.get("src", "")

            # Price info (free vs paid)
            price_tag = card.select_one(".crea-price")
            price = price_tag.get_text(strip=True) if price_tag else ""

            source_id = href.rstrip("/").split("/")[-1] or href

            yield SearchResult(
                source=self.name,
                source_id=str(source_id),
                name=name,
                url=url,
                author="",
                thumbnail_url=thumb,
                license=price,
            )

    async def fetch_model_metadata(self, url: str, source_id: str) -> SearchResult:
        client = await self._get_client()
        resp = await client.get(url, headers={"Accept": "text/html"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        title_tag = soup.select_one("h1")
        name = title_tag.get_text(strip=True) if title_tag else ""
        img_tag = soup.select_one('meta[property="og:image"]')
        thumb = img_tag["content"] if img_tag and img_tag.get("content") else ""
        desc_tag = soup.select_one('meta[property="og:description"]')
        description = desc_tag["content"] if desc_tag and desc_tag.get("content") else ""
        author_tag = soup.select_one('a[href*="/en/users/"]')
        author = author_tag.get_text(strip=True) if author_tag else ""
        real_source_id = url.rstrip("/").split("/")[-1]

        return SearchResult(
            source=self.name,
            source_id=real_source_id,
            name=name,
            url=url,
            author=author,
            thumbnail_url=thumb,
            description=description[:500],
        )
