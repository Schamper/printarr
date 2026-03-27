from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.models import (
    ImportURLRequest,
    LibraryModelCreate,
    LibraryModelRead,
    ModelFileRead,
    TagsUpdate,
)
from app.services import files as files_service
from app.services import library as library_service
from app.services.files import auto_discover_files
from app.services.import_url import fetch_from_url

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/library", tags=["library"])


@router.get("/tags", response_model=list[str])
async def list_tags(db: AsyncSession = Depends(get_db)):
    """All unique tags used across the library."""
    return await library_service.get_all_tags(db)


@router.get("", response_model=list[LibraryModelRead])
async def list_models(
    search: str | None = None,
    tag: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    models = await library_service.list_models(db, search=search, tag=tag)
    result = []
    for m in models:
        data = LibraryModelRead.model_validate(m)
        data.in_queue = len(m.queue_items) > 0
        data.tags = list(m.tags or [])
        data.files_count = len(m.files)
        result.append(data)
    return result


@router.get("/{model_id}", response_model=LibraryModelRead)
async def get_model(model_id: int, db: AsyncSession = Depends(get_db)):
    model = await library_service.get_model(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.post("", response_model=LibraryModelRead, status_code=201)
async def add_model(
    data: LibraryModelCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    model = await library_service.add_model(db, data)
    background_tasks.add_task(auto_discover_files, model.id, model.source, model.source_id)
    return model


@router.post("/import-url", response_model=LibraryModelRead, status_code=201)
async def import_from_url(
    req: ImportURLRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Import a model into the library from a source URL."""
    try:
        search_result = await fetch_from_url(req.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as exc:
        logger.exception("Failed to import from URL: %s", req.url)
        raise HTTPException(status_code=502, detail="Failed to fetch model from URL") from exc

    if await library_service.is_in_library(db, search_result.source, search_result.source_id):
        raise HTTPException(status_code=409, detail="Model already in library")

    create_data = LibraryModelCreate(
        source=search_result.source,
        source_id=search_result.source_id,
        url=search_result.url,
        name=search_result.name,
        author=search_result.author,
        description=search_result.description,
        thumbnail_url=search_result.thumbnail_url,
        license=search_result.license,
        download_count=search_result.download_count,
        like_count=search_result.like_count,
    )
    model = await library_service.add_model(db, create_data)
    background_tasks.add_task(auto_discover_files, model.id, model.source, model.source_id)
    return model


@router.post("/{model_id}/discover-files", response_model=list[ModelFileRead])
async def discover_files(model_id: int, db: AsyncSession = Depends(get_db)):
    """Re-run file discovery for a library model and return all its files."""
    model = await library_service.get_model(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    await files_service.discover_files(db, model.id, model.source, model.source_id)
    return await files_service.list_files(db, model.id)


@router.put("/{model_id}/tags", response_model=LibraryModelRead)
async def update_tags(model_id: int, data: TagsUpdate, db: AsyncSession = Depends(get_db)):
    model = await library_service.update_tags(db, model_id, data.tags)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    result = LibraryModelRead.model_validate(model)
    result.tags = list(model.tags or [])
    return result


@router.delete("/{model_id}", status_code=204)
async def delete_model(model_id: int, db: AsyncSession = Depends(get_db)):
    ok = await library_service.delete_model(db, model_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Model not found")
