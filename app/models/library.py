from __future__ import annotations

import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class LibraryModel(Base):
    __tablename__ = "library_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Source identifiers
    source: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)

    # Model info
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    author: Mapped[str] = mapped_column(String(255), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    thumbnail_url: Mapped[str] = mapped_column(String(2048), default="")
    license: Mapped[str] = mapped_column(String(100), default="")
    download_count: Mapped[int] = mapped_column(Integer, default=0)
    like_count: Mapped[int] = mapped_column(Integer, default=0)

    # Tags (stored as JSON array, e.g. ["cosplay", "functional"])
    tags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    # Timestamps
    added_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    queue_items: Mapped[list[QueueItem]] = relationship(back_populates="model", cascade="all, delete-orphan")
    files: Mapped[list[ModelFile]] = relationship(back_populates="model", cascade="all, delete-orphan")


class QueueItem(Base):
    __tablename__ = "queue_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    library_model_id: Mapped[int] = mapped_column(Integer, ForeignKey("library_models.id"), nullable=False, index=True)
    file_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("model_files.id"), nullable=True, index=True)

    notes: Mapped[str] = mapped_column(Text, default="")
    filament_type: Mapped[str] = mapped_column(String(100), default="")
    filament_color: Mapped[str] = mapped_column(String(100), default="")
    copies: Mapped[int] = mapped_column(Integer, default=1)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, index=True)

    added_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    model: Mapped[LibraryModel] = relationship(back_populates="queue_items")
    file: Mapped[ModelFile | None] = relationship(back_populates="queue_items")


class ModelFile(Base):
    __tablename__ = "model_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    library_model_id: Mapped[int] = mapped_column(Integer, ForeignKey("library_models.id"), nullable=False, index=True)

    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    original_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), default="")  # stl, step, stp, obj, 3mf, etc.
    size_bytes: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    status: Mapped[str] = mapped_column(String(20), default="available", server_default="available")
    local_path: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    added_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    queue_items: Mapped[list[QueueItem]] = relationship(back_populates="file")

    model: Mapped[LibraryModel] = relationship(back_populates="files")
