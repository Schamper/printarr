from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.library import ModelFile
from app.schemas.models import ModelFileRead
from app.services import files as files_service

router = APIRouter(prefix="/api/library/{model_id}/files", tags=["files"])


@router.get("", response_model=list[ModelFileRead])
async def list_files(model_id: int, db: AsyncSession = Depends(get_db)):
    return await files_service.list_files(db, model_id)


@router.get("/{file_id}/download")
async def download_redirect(model_id: int, file_id: int, db: AsyncSession = Depends(get_db)):
    """Redirect to the original CDN URL. Used as the slicer open URL so that
    OrcaSlicer/PrusaSlicer receive a simple localhost URL rather than a
    long CDN URL that some versions mishandle."""
    file = await db.get(ModelFile, file_id)
    if not file or file.library_model_id != model_id:
        raise HTTPException(status_code=404, detail="File not found")
    if not file.original_url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="No download URL for this file")
    return RedirectResponse(url=file.original_url, status_code=302)


@router.delete("/{file_id}", status_code=204)
async def delete_file(model_id: int, file_id: int, db: AsyncSession = Depends(get_db)):
    ok = await files_service.delete_file(db, file_id)
    if not ok:
        raise HTTPException(status_code=404, detail="File not found")
