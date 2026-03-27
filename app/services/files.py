from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.library import ModelFile
from app.schemas.models import ModelFileCreate

logger = logging.getLogger(__name__)

_KNOWN_TYPES = {"stl", "step", "stp", "obj", "3mf", "amf", "gcode"}


def _detect_type(filename: str) -> str:
    ext = Path(filename).suffix.lower().lstrip(".")
    if ext == "stp":
        return "step"
    return ext if ext in _KNOWN_TYPES else ext


async def list_files(db: AsyncSession, library_model_id: int) -> list[ModelFile]:
    stmt = (
        select(ModelFile)
        .where(ModelFile.library_model_id == library_model_id)
        .order_by(ModelFile.filename)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def add_file(db: AsyncSession, library_model_id: int, data: ModelFileCreate) -> ModelFile:
    file = ModelFile(
        library_model_id=library_model_id,
        filename=data.filename,
        original_url=data.original_url,
        file_type=data.file_type or _detect_type(data.filename),
        size_bytes=data.size_bytes,
    )
    db.add(file)
    await db.commit()
    await db.refresh(file)
    return file


async def delete_file(db: AsyncSession, file_id: int) -> bool:
    file = await db.get(ModelFile, file_id)
    if not file:
        return False
    await db.delete(file)
    await db.commit()
    return True


async def _store_discovered(
    db: AsyncSession, library_model_id: int, discovered: list
) -> list[ModelFile]:
    """Persist discovered files, skipping duplicates by URL."""
    existing = await list_files(db, library_model_id)
    existing_urls = {f.original_url for f in existing}
    added: list[ModelFile] = []
    for f in discovered:
        if f.url not in existing_urls:
            added.append(
                await add_file(
                    db,
                    library_model_id,
                    ModelFileCreate(filename=f.filename, original_url=f.url, file_type=f.file_type, size_bytes=f.size_bytes),
                )
            )
            existing_urls.add(f.url)
    return added


async def discover_files(db: AsyncSession, library_model_id: int, source: str, source_id: str) -> list[ModelFile]:
    """Discover + persist files for a model using its source. Returns newly added files."""
    from sqlalchemy import select as sa_select

    from app.models.settings import IndexerConfig
    from app.sources.base import get_source

    source_cls = get_source(source)
    if not source_cls:
        return []

    result = await db.execute(sa_select(IndexerConfig).where(IndexerConfig.name == source))
    cfg = result.scalar_one_or_none()
    api_key = cfg.api_key if cfg else ""

    instance = source_cls(api_key=api_key)
    try:
        discovered = await instance.fetch_files(source_id)
    except Exception:
        logger.exception("File discovery failed for %s:%s", source, source_id)
        return []
    finally:
        await instance.close()

    return await _store_discovered(db, library_model_id, discovered)


async def auto_discover_files(library_model_id: int, source: str, source_id: str) -> None:
    """Background task wrapper: creates its own DB session for post-response execution."""
    from app.database import get_session_factory

    factory = get_session_factory()
    async with factory() as db:
        await discover_files(db, library_model_id, source, source_id)
