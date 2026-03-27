from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

from app.config import get_settings
from app.database import get_engine, get_session_factory
from app.models.base import Base
from app.routers import files as files_router
from app.routers import library, queue, search, settings, sources

logger = logging.getLogger("printarr")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    s = get_settings()
    logging.basicConfig(level=s.log_level.upper(), format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
    logger.info("Printarr starting — data_dir=%s", s.data_dir)

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Ensure default indexer configs exist
    from app.services.settings import ensure_indexer_configs

    factory = get_session_factory()
    async with factory() as db:
        await ensure_indexer_configs(db)

    logger.info("Database initialized")
    yield

    # Shutdown
    await engine.dispose()
    logger.info("Printarr stopped")


app = FastAPI(title="Printarr", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers
app.include_router(search.router)
app.include_router(library.router)
app.include_router(files_router.router)
app.include_router(queue.router)
app.include_router(settings.router)
app.include_router(sources.router)

# Serve frontend static files (built by Vite into static/ at project root)
_static_dir = Path(__file__).resolve().parent.parent / "static"
if _static_dir.is_dir():
    # Serve Vite-bundled assets at /assets
    _assets_dir = _static_dir / "assets"
    if _assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(_assets_dir)), name="static-assets")

    # SPA catch-all: serve index.html for any non-API route
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        return FileResponse(str(_static_dir / "index.html"))


def run() -> None:
    import uvicorn

    s = get_settings()
    uvicorn.run("app.main:app", host="0.0.0.0", port=s.port, log_level=s.log_level.lower())
