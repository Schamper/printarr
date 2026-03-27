from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.library import LibraryModel
from app.schemas.models import LibraryModelCreate


async def list_models(
    db: AsyncSession,
    search: str | None = None,
    tag: str | None = None,
) -> list[LibraryModel]:
    stmt = (
        select(LibraryModel)
        .options(selectinload(LibraryModel.queue_items), selectinload(LibraryModel.files))
        .order_by(LibraryModel.added_at.desc())
    )
    if search:
        stmt = stmt.where(LibraryModel.name.ilike(f"%{search}%"))
    if tag:
        stmt = stmt.where(
            sa.text(
                "EXISTS (SELECT 1 FROM json_each(library_models.tags) WHERE value = :tag_val)"
            ).bindparams(tag_val=tag)
        )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_model(db: AsyncSession, model_id: int) -> LibraryModel | None:
    return await db.get(LibraryModel, model_id)


async def add_model(db: AsyncSession, data: LibraryModelCreate) -> LibraryModel:
    model = LibraryModel(**data.model_dump())
    db.add(model)
    await db.commit()
    await db.refresh(model)
    return model


async def update_tags(db: AsyncSession, model_id: int, tags: list[str]) -> LibraryModel | None:
    model = await db.get(LibraryModel, model_id)
    if not model:
        return None
    model.tags = sorted({t.strip() for t in tags if t.strip()})
    await db.commit()
    await db.refresh(model)
    return model


async def delete_model(db: AsyncSession, model_id: int) -> bool:
    model = await db.get(LibraryModel, model_id)
    if not model:
        return False
    await db.delete(model)
    await db.commit()
    return True


async def is_in_library(db: AsyncSession, source: str, source_id: str) -> bool:
    stmt = select(LibraryModel.id).where(
        LibraryModel.source == source, LibraryModel.source_id == source_id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def get_all_tags(db: AsyncSession) -> list[str]:
    """Return all unique tags used across the library, sorted."""
    result = await db.execute(
        sa.text(
            "SELECT DISTINCT value FROM library_models, json_each(library_models.tags)"
            " WHERE value != '' ORDER BY value"
        )
    )
    return [row[0] for row in result.fetchall()]
