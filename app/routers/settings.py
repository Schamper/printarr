from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.models import (
    AppSettingRead,
    AppSettingWrite,
    IndexerConfigRead,
    IndexerConfigUpdate,
)
from app.services import settings as settings_service

router = APIRouter(prefix="/api/settings", tags=["settings"])


# -- Indexers --

@router.get("/indexers", response_model=list[IndexerConfigRead])
async def list_indexers(db: AsyncSession = Depends(get_db)):
    return await settings_service.list_indexers(db)


@router.patch("/indexers/{name}", response_model=IndexerConfigRead)
async def update_indexer(
    name: str, data: IndexerConfigUpdate, db: AsyncSession = Depends(get_db)
):
    cfg = await settings_service.update_indexer(db, name, data)
    if not cfg:
        raise HTTPException(status_code=404, detail="Indexer not found")
    return cfg


# -- General settings --

@router.get("", response_model=list[AppSettingRead])
async def list_settings(db: AsyncSession = Depends(get_db)):
    return await settings_service.get_all_settings(db)


@router.put("")
async def update_setting(data: AppSettingWrite, db: AsyncSession = Depends(get_db)):
    setting = await settings_service.set_setting(db, data.key, data.value)
    return {"key": setting.key, "value": setting.value}
