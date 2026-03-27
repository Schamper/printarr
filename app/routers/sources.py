from __future__ import annotations

from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from app.sources.base import get_all_sources

router = APIRouter(prefix="/api/sources", tags=["sources"])

# Domains allowed for image proxying — prevents SSRF to internal hosts.
_PROXY_ALLOWED_HOSTS = {
    "cdn.thingiverse.com",
    "cdn.makerworld.com",
    "makerworld.bblmw.com",
    "cdn-acop.makeronline.com",
    "files.printables.com",
    "media.printables.com",
    "cdn.myminifactory.com",
    "images.myminifactory.com",
    "cdn.thangs.com",
    "images.cults3d.com",
    "videos.cults3d.com",
    "files.cults3d.com",
}


@router.get("/proxy-image")
async def proxy_image(url: str = Query(...)):
    """Proxy an external CDN image through the server.

    Required because some CDNs (e.g. Thingiverse) return 403 to browser
    requests via Cloudflare bot-detection, but allow server-side fetches.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or parsed.hostname not in _PROXY_ALLOWED_HOSTS:
        raise HTTPException(status_code=400, detail="URL not allowed")

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
            r = await client.get(url)
            r.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail="Upstream image fetch failed") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Could not fetch image") from exc

    content_type = r.headers.get("content-type", "image/jpeg")
    return Response(
        content=r.content,
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )


@router.get("")
async def list_sources():
    """Return all registered source metadata."""
    return [{"name": cls.name, "display_name": cls.display_name, "base_url": cls.base_url} for cls in get_all_sources().values()]
