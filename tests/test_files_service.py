from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.library import LibraryModel
from app.schemas.models import ModelFileCreate
from app.services import files as svc


async def _make_model(db: AsyncSession) -> LibraryModel:
    m = LibraryModel(source="test", source_id="f1", name="Test Model", url="http://example.com/m1")
    db.add(m)
    await db.commit()
    await db.refresh(m)
    return m


@pytest.mark.asyncio
async def test_add_and_list(db: AsyncSession) -> None:
    m = await _make_model(db)
    f = await svc.add_file(db, m.id, ModelFileCreate(filename="ship.stl", original_url="http://cdn/ship.stl"))
    assert f.id is not None
    assert f.filename == "ship.stl"
    assert f.file_type == "stl"

    listed = await svc.list_files(db, m.id)
    assert len(listed) == 1
    assert listed[0].id == f.id


@pytest.mark.asyncio
async def test_type_normalisation_stp(db: AsyncSession) -> None:
    m = await _make_model(db)
    f = await svc.add_file(db, m.id, ModelFileCreate(filename="part.stp", original_url="http://cdn/part.stp"))
    assert f.file_type == "step"


@pytest.mark.asyncio
async def test_list_empty(db: AsyncSession) -> None:
    m = await _make_model(db)
    assert await svc.list_files(db, m.id) == []


@pytest.mark.asyncio
async def test_delete(db: AsyncSession) -> None:
    m = await _make_model(db)
    f = await svc.add_file(db, m.id, ModelFileCreate(filename="del.3mf", original_url="http://cdn/del.3mf"))
    ok = await svc.delete_file(db, f.id)
    assert ok is True
    assert await svc.list_files(db, m.id) == []


@pytest.mark.asyncio
async def test_delete_nonexistent(db: AsyncSession) -> None:
    ok = await svc.delete_file(db, 99999)
    assert ok is False


@pytest.mark.asyncio
async def test_multiple_files_ordered(db: AsyncSession) -> None:
    m = await _make_model(db)
    await svc.add_file(db, m.id, ModelFileCreate(filename="z.stl", original_url="http://cdn/z.stl"))
    await svc.add_file(db, m.id, ModelFileCreate(filename="a.stl", original_url="http://cdn/a.stl"))
    listed = await svc.list_files(db, m.id)
    # list_files returns ordered by filename
    assert [f.filename for f in listed] == ["a.stl", "z.stl"]
