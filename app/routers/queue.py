from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.models import QueueItemCreate, QueueItemRead, QueueItemUpdate, ReorderItem
from app.services import queue as queue_service

router = APIRouter(prefix="/api/queue", tags=["queue"])


def _item_to_read(item) -> QueueItemRead:
    """Convert a QueueItem ORM instance (with loaded model + file) to a read schema."""
    m = item.model
    f = item.file
    return QueueItemRead(
        id=item.id,
        library_model_id=item.library_model_id,
        file_id=item.file_id,
        notes=item.notes,
        filament_type=item.filament_type,
        filament_color=item.filament_color,
        copies=item.copies,
        sort_order=item.sort_order,
        added_at=item.added_at,
        model_name=m.name if m else "",
        model_source=m.source if m else "",
        model_url=m.url if m else "",
        model_author=m.author if m else "",
        model_thumbnail_url=m.thumbnail_url if m else "",
        file_filename=f.filename if f else "",
        file_original_url=f.original_url if f else "",
        file_file_type=f.file_type if f else "",
    )


@router.get("", response_model=list[QueueItemRead])
async def list_queue(db: AsyncSession = Depends(get_db)):
    items = await queue_service.list_items(db)
    return [_item_to_read(i) for i in items]


@router.post("", response_model=QueueItemRead, status_code=201)
async def add_to_queue(data: QueueItemCreate, db: AsyncSession = Depends(get_db)):
    item = await queue_service.add_item(db, data)
    return _item_to_read(item)


@router.patch("/{item_id}", response_model=QueueItemRead)
async def update_queue_item(item_id: int, data: QueueItemUpdate, db: AsyncSession = Depends(get_db)):
    item = await queue_service.update_item(db, item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found")
    return _item_to_read(item)


@router.delete("/{item_id}", status_code=204)
async def remove_from_queue(item_id: int, db: AsyncSession = Depends(get_db)):
    ok = await queue_service.delete_item(db, item_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Queue item not found")


@router.put("/reorder", status_code=204)
async def reorder_queue(items: list[ReorderItem], db: AsyncSession = Depends(get_db)):
    await queue_service.reorder_items(db, items)
