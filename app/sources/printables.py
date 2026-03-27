from __future__ import annotations

import logging
import re
from collections.abc import AsyncIterator

from app.schemas.models import SearchResult
from app.sources.base import DiscoveredFile, SortOption, SourceBase, register_source

logger = logging.getLogger(__name__)


@register_source
class PrintablesSource(SourceBase):
    name = "printables"
    display_name = "Printables"
    base_url = "https://www.printables.com"
    url_pattern = re.compile(r"printables\.com/model/(\d+)")
    _graphql_url = "https://api.printables.com/graphql/"
    _CDN = "https://media.printables.com"

    _SORT_MAP: dict[str, str] = {
        "relevance": "best_match",
        "downloads": "popular",
        "likes": "rating",
        "newest": "latest",
    }

    _GQL_HEADERS = {
        "Content-Type": "application/json",
        "Origin": "https://www.printables.com",
        "Referer": "https://www.printables.com/",
    }

    # ── GraphQL helpers ──────────────────────────────────────────────────────

    async def _gql_print(self, source_id: str) -> dict:
        """Fetch print metadata via GraphQL and return the raw print dict."""
        gql = """
        query PrintProfile($id: ID!) {
            print(id: $id) {
                id name slug description likesCount downloadCount firstPublish
                image { filePath }
                user { publicUsername }
            }
        }
        """
        client = await self._get_client()
        resp = await client.post(
            self._graphql_url,
            json={"query": gql, "variables": {"id": source_id}},
            headers=self._GQL_HEADERS,
        )
        resp.raise_for_status()
        return resp.json().get("data", {}).get("print") or {}

    # ── Search ───────────────────────────────────────────────────────────────

    async def search(self, query: str, page: int = 1, sort: SortOption = "relevance") -> AsyncIterator[SearchResult]:
        client = await self._get_client()
        ordering = self._SORT_MAP.get(sort, "best_match")
        gql_query = """
        query SearchPrints($query: String!, $limit: Int!, $offset: Int, $ordering: SearchChoicesEnum) {
            result: searchPrints2(
                query: $query
                limit: $limit
                offset: $offset
                ordering: $ordering
            ) {
                items {
                    id
                    name
                    slug
                    description
                    likesCount
                    downloadCount
                    firstPublish
                    image {
                        filePath
                    }
                    user {
                        publicUsername
                    }
                }
            }
        }
        """
        per_page = 20
        offset = (page - 1) * per_page
        resp = await client.post(
            self._graphql_url,
            json={
                "query": gql_query,
                "variables": {"query": query, "limit": per_page, "offset": offset, "ordering": ordering},
            },
            headers=self._GQL_HEADERS,
        )
        resp.raise_for_status()
        data = resp.json()

        items = data.get("data", {}).get("result", {}).get("items", [])
        for item in items:
            slug = item.get("slug", "")
            model_id = item.get("id", "")
            image = item.get("image", {}) or {}
            file_path = image.get("filePath", "")
            thumb = f"{self._CDN}/{file_path}" if file_path else ""
            user = item.get("user", {}) or {}

            yield SearchResult(
                source=self.name,
                source_id=str(model_id),
                name=item.get("name", ""),
                url=f"{self.base_url}/model/{model_id}-{slug}",
                author=user.get("publicUsername", ""),
                thumbnail_url=thumb,
                description=(item.get("description", "") or "")[:500],
                license=(item.get("license", {}) or {}).get("name", ""),
                download_count=item.get("downloadCount", 0) or 0,
                like_count=item.get("likesCount", 0) or 0,
                published_at=item.get("datePublished", ""),
            )

    # ── Metadata import ──────────────────────────────────────────────────────

    async def fetch_model_metadata(self, url: str, source_id: str) -> SearchResult:
        item = await self._gql_print(source_id)
        if not item:
            raise ValueError("Model not found on Printables")
        slug = item.get("slug", "")
        image = item.get("image", {}) or {}
        fp = image.get("filePath", "")
        thumb = f"{self._CDN}/{fp}" if fp else ""
        user = item.get("user", {}) or {}
        return SearchResult(
            source=self.name,
            source_id=str(source_id),
            name=item.get("name", ""),
            url=f"{self.base_url}/model/{source_id}-{slug}",
            author=user.get("publicUsername", ""),
            thumbnail_url=thumb,
            description=(item.get("description", "") or "")[:500],
            download_count=item.get("downloadCount", 0) or 0,
            like_count=item.get("likesCount", 0) or 0,
            published_at=item.get("firstPublish", ""),
        )

    # ── File discovery ───────────────────────────────────────────────────────

    async def fetch_files(self, source_id: str) -> list[DiscoveredFile]:
        """Discover files for a Printables model via GraphQL.

        Step 1: Query stls + otherFiles to get file IDs and names.
        Step 2: Call getDownloadLink mutation to get direct download URLs.
        """
        client = await self._get_client()

        # Step 1: Fetch file list (ids + names) ---------------------------------
        gql_list = """
        query GetPrintFiles($id: ID!) {
            print(id: $id) {
                stls { id name fileSize }
                otherFiles { id name fileSize }
            }
        }
        """
        try:
            resp = await client.post(
                self._graphql_url,
                json={"query": gql_list, "variables": {"id": source_id}},
                headers=self._GQL_HEADERS,
                timeout=20.0,
            )
            resp.raise_for_status()
            print_data = resp.json().get("data", {}).get("print") or {}
        except Exception:
            logger.exception("Printables fetch_files: file list query failed for %s", source_id)
            return []

        stls = print_data.get("stls") or []
        other_files = print_data.get("otherFiles") or []
        all_files = stls + other_files
        if not all_files:
            return []

        id_to_name: dict[str, str] = {
            f["id"]: f["name"] for f in all_files if f.get("id") and f.get("name")
        }
        id_to_size: dict[str, int] = {
            f["id"]: int(f.get("fileSize") or 0) for f in all_files if f.get("id")
        }

        # Step 2: Get download URLs via mutation ---------------------------------
        files_arg = []
        stl_ids = [f["id"] for f in stls if f.get("id")]
        other_ids = [f["id"] for f in other_files if f.get("id")]
        if stl_ids:
            files_arg.append({"fileType": "stl", "ids": stl_ids})
        if other_ids:
            files_arg.append({"fileType": "other", "ids": other_ids})

        gql_dl = """
        mutation GetDownloadLinks($printId: ID!, $source: DownloadSourceEnum!, $files: [DownloadFileInput]) {
            getDownloadLink(printId: $printId, source: $source, files: $files) {
                ok
                errors { field messages }
                output { files { id link fileType } }
            }
        }
        """
        try:
            resp = await client.post(
                self._graphql_url,
                json={"query": gql_dl, "variables": {
                    "printId": source_id,
                    "source": "model_detail",
                    "files": files_arg,
                }},
                headers=self._GQL_HEADERS,
                timeout=20.0,
            )
            resp.raise_for_status()
            result = resp.json().get("data", {}).get("getDownloadLink") or {}
        except Exception:
            logger.exception("Printables fetch_files: getDownloadLink mutation failed for %s", source_id)
            return []

        if not result.get("ok"):
            logger.warning("Printables getDownloadLink ok=false for %s: %s", source_id, result.get("errors"))
            return []

        file_links = result.get("output", {}).get("files") or []
        return [
            DiscoveredFile(filename=id_to_name[fl["id"]], url=fl["link"], size_bytes=id_to_size.get(fl["id"], 0))
            for fl in file_links
            if fl.get("id") in id_to_name and fl.get("link")
        ]
