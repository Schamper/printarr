from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.library import LibraryModel, ModelFile
from app.schemas.models import QueueItemCreate, QueueItemUpdate, ReorderItem
from app.services import queue as svc


async def _make_model(db: AsyncSession, source_id: str = "q1") -> LibraryModel:
    m = LibraryModel(source="test", source_id=source_id, name="Queue Model", url="http://example.com/q1")
    db.add(m)
    await db.commit()
    await db.refresh(m)
    return m


async def _make_file(db: AsyncSession, model_id: int, filename: str = "part.stl") -> ModelFile:
    f = ModelFile(library_model_id=model_id, filename=filename, original_url="http://example.com/part.stl", file_type="stl")
    db.add(f)
    await db.commit()
    await db.refresh(f)
    return f


@pytest.mark.asyncio
async def test_add_and_list(db: AsyncSession) -> None:
    m = await _make_model(db)
    f = await _make_file(db, m.id)
    item = await svc.add_item(db, QueueItemCreate(file_id=f.id))
    assert item.id is not None
    assert item.library_model_id == m.id
    assert item.file_id == f.id
    assert item.copies == 1

    items = await svc.list_items(db)
    assert any(i.id == item.id for i in items)


@pytest.mark.asyncio
async def test_add_defaults(db: AsyncSession) -> None:
    m = await _make_model(db, "q2")
    f = await _make_file(db, m.id, "part2.stl")
    item = await svc.add_item(db, QueueItemCreate(file_id=f.id, filament_type="PLA", copies=3))
    assert item.filament_type == "PLA"
    assert item.copies == 3


@pytest.mark.asyncio
async def test_update(db: AsyncSession) -> None:
    m = await _make_model(db, "q3")
    f = await _make_file(db, m.id, "part3.stl")
    item = await svc.add_item(db, QueueItemCreate(file_id=f.id))
    updated = await svc.update_item(db, item.id, QueueItemUpdate(copies=5, notes="needs supports"))
    assert updated is not None
    assert updated.copies == 5
    assert updated.notes == "needs supports"


@pytest.mark.asyncio
async def test_update_nonexistent(db: AsyncSession) -> None:
    result = await svc.update_item(db, 99999, QueueItemUpdate(copies=2))
    assert result is None


@pytest.mark.asyncio
async def test_delete(db: AsyncSession) -> None:
    m = await _make_model(db, "q4")
    f = await _make_file(db, m.id, "part4.stl")
    item = await svc.add_item(db, QueueItemCreate(file_id=f.id))
    ok = await svc.delete_item(db, item.id)
    assert ok is True
    items = await svc.list_items(db)
    assert not any(i.id == item.id for i in items)


@pytest.mark.asyncio
async def test_delete_nonexistent(db: AsyncSession) -> None:
    ok = await svc.delete_item(db, 99999)
    assert ok is False


@pytest.mark.asyncio
async def test_reorder(db: AsyncSession) -> None:
    m = await _make_model(db, "q5")
    fa = await _make_file(db, m.id, "parta.stl")
    fb = await _make_file(db, m.id, "partb.stl")
    a = await svc.add_item(db, QueueItemCreate(file_id=fa.id))
    b = await svc.add_item(db, QueueItemCreate(file_id=fb.id))

    # Put b before a
    await svc.reorder_items(db, [
        ReorderItem(id=a.id, sort_order=20),
        ReorderItem(id=b.id, sort_order=5),
    ])

    items = await svc.list_items(db)
    ids = [i.id for i in items]
    assert ids.index(b.id) < ids.index(a.id)
