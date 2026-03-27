from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings import AppSetting, IndexerConfig, SettingCategory
from app.schemas.models import IndexerConfigUpdate
from app.sources.base import get_all_sources


async def ensure_indexer_configs(db: AsyncSession) -> None:
    """Create default IndexerConfig rows for any registered sources that don't have one."""
    source_classes = get_all_sources()
    result = await db.execute(select(IndexerConfig.name))
    existing = {row[0] for row in result.all()}

    for name in source_classes:
        if name not in existing:
            db.add(IndexerConfig(name=name, enabled=True, api_key="", priority=0))

    await db.commit()


async def list_indexers(db: AsyncSession) -> list[dict]:
    """List indexers enriched with live source class metadata."""
    source_classes = get_all_sources()
    result = await db.execute(select(IndexerConfig).order_by(IndexerConfig.priority))
    configs = list(result.scalars().all())
    enriched = []
    for cfg in configs:
        cls = source_classes.get(cfg.name)
        enriched.append({
            "id": cfg.id,
            "name": cfg.name,
            "display_name": cls.display_name if cls else cfg.name.capitalize(),
            "enabled": cfg.enabled,
            "has_api_key": bool(cfg.api_key),
            "priority": cfg.priority,
            "requires_api_key": cls.requires_api_key if cls else False,
            "api_key_label": cls.api_key_label if cls else "API Key",
        })
    return enriched


async def update_indexer(
    db: AsyncSession, name: str, data: IndexerConfigUpdate
) -> dict | None:
    source_classes = get_all_sources()
    result = await db.execute(select(IndexerConfig).where(IndexerConfig.name == name))
    cfg = result.scalar_one_or_none()
    if not cfg:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(cfg, field, value)
    await db.commit()
    await db.refresh(cfg)
    cls = source_classes.get(cfg.name)
    return {
        "id": cfg.id,
        "name": cfg.name,
        "display_name": cls.display_name if cls else cfg.name.capitalize(),
        "enabled": cfg.enabled,
        "has_api_key": bool(cfg.api_key),
        "priority": cfg.priority,
        "requires_api_key": cls.requires_api_key if cls else False,
        "api_key_label": cls.api_key_label if cls else "API Key",
    }


async def get_setting(db: AsyncSession, key: str) -> str | None:
    result = await db.execute(select(AppSetting).where(AppSetting.key == key))
    setting = result.scalar_one_or_none()
    return setting.value if setting else None


async def set_setting(db: AsyncSession, key: str, value: str, category: SettingCategory = SettingCategory.GENERAL) -> AppSetting:
    result = await db.execute(select(AppSetting).where(AppSetting.key == key))
    setting = result.scalar_one_or_none()
    if setting:
        setting.value = value
    else:
        setting = AppSetting(key=key, value=value, category=category)
        db.add(setting)
    await db.commit()
    await db.refresh(setting)
    return setting


async def get_all_settings(db: AsyncSession) -> list[AppSetting]:
    result = await db.execute(select(AppSetting))
    return list(result.scalars().all())
