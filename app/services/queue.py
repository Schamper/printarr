from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.library import ModelFile, QueueItem
from app.schemas.models import QueueItemCreate, QueueItemUpdate, ReorderItem


async def list_items(db: AsyncSession) -> list[QueueItem]:
    stmt = (
        select(QueueItem)
        .options(joinedload(QueueItem.model), joinedload(QueueItem.file))
        .order_by(QueueItem.sort_order, QueueItem.added_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def add_item(db: AsyncSession, data: QueueItemCreate) -> QueueItem:
    # Resolve library_model_id from the file
    file = await db.get(ModelFile, data.file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    # Set sort_order to end of queue
    stmt = select(QueueItem.sort_order).order_by(QueueItem.sort_order.desc()).limit(1)
    result = await db.execute(stmt)
    max_order = result.scalar_one_or_none() or 0

    item = QueueItem(
        file_id=data.file_id,
        library_model_id=file.library_model_id,
        notes=data.notes,
        filament_type=data.filament_type,
        filament_color=data.filament_color,
        copies=data.copies,
        sort_order=max_order + 1,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item, attribute_names=["model", "file"])
    return item


async def update_item(db: AsyncSession, item_id: int, data: QueueItemUpdate) -> QueueItem | None:
    item = await db.get(QueueItem, item_id)
    if not item:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await db.commit()
    await db.refresh(item, attribute_names=["model", "file"])
    return item


async def delete_item(db: AsyncSession, item_id: int) -> bool:
    item = await db.get(QueueItem, item_id)
    if not item:
        return False
    await db.delete(item)
    await db.commit()
    return True


async def reorder_items(db: AsyncSession, items: list[ReorderItem]) -> None:
    for reorder in items:
        item = await db.get(QueueItem, reorder.id)
        if item:
            item.sort_order = reorder.sort_order
    await db.commit()
