from __future__ import annotations

import datetime

from pydantic import BaseModel

# -- Search result (normalized across all sources) --


class SearchResult(BaseModel):
    source: str
    source_id: str
    name: str
    url: str
    author: str = ""
    thumbnail_url: str = ""
    description: str = ""
    license: str = ""
    download_count: int = 0
    like_count: int = 0
    published_at: str = ""
    in_library: bool = False


class SearchEvent(BaseModel):
    """One SSE event during a search stream."""

    event: str  # "result", "source_start", "source_done", "source_error", "done"
    source: str = ""
    data: SearchResult | str | None = None


# -- Library --


class LibraryModelCreate(BaseModel):
    source: str
    source_id: str
    url: str
    name: str
    author: str = ""
    description: str = ""
    thumbnail_url: str = ""
    license: str = ""
    download_count: int = 0
    like_count: int = 0


class LibraryModelRead(BaseModel):
    id: int
    source: str
    source_id: str
    url: str
    name: str
    author: str
    description: str
    thumbnail_url: str
    license: str
    download_count: int
    like_count: int
    tags: list[str] = []
    added_at: datetime.datetime
    updated_at: datetime.datetime
    in_queue: bool = False
    files_count: int = 0

    model_config = {"from_attributes": True}


class ImportURLRequest(BaseModel):
    url: str


class TagsUpdate(BaseModel):
    tags: list[str]


# -- Files --


class ModelFileCreate(BaseModel):
    filename: str
    original_url: str
    file_type: str = ""
    size_bytes: int = 0


class ModelFileRead(BaseModel):
    id: int
    library_model_id: int
    filename: str
    original_url: str
    file_type: str
    size_bytes: int
    added_at: datetime.datetime

    model_config = {"from_attributes": True}


# -- Queue --


class QueueItemCreate(BaseModel):
    file_id: int
    notes: str = ""
    filament_type: str = ""
    filament_color: str = ""
    copies: int = 1


class QueueItemUpdate(BaseModel):
    notes: str | None = None
    filament_type: str | None = None
    filament_color: str | None = None
    copies: int | None = None
    sort_order: int | None = None


class ReorderItem(BaseModel):
    id: int
    sort_order: int


class QueueItemRead(BaseModel):
    id: int
    library_model_id: int
    file_id: int | None = None
    notes: str
    filament_type: str
    filament_color: str
    copies: int
    sort_order: int
    added_at: datetime.datetime
    # Denormalized model info for convenience
    model_name: str = ""
    model_source: str = ""
    model_url: str = ""
    model_author: str = ""
    model_thumbnail_url: str = ""
    # Denormalized file info
    file_filename: str = ""
    file_original_url: str = ""
    file_file_type: str = ""

    model_config = {"from_attributes": True}


# -- Settings --


class IndexerConfigRead(BaseModel):
    id: int
    name: str
    display_name: str = ""
    enabled: bool
    has_api_key: bool
    priority: int
    requires_api_key: bool = False
    api_key_label: str = "API Key"

    model_config = {"from_attributes": True}


class IndexerConfigUpdate(BaseModel):
    enabled: bool | None = None
    api_key: str | None = None
    priority: int | None = None


class AppSettingRead(BaseModel):
    key: str
    value: str

    model_config = {"from_attributes": True}


class AppSettingWrite(BaseModel):
    key: str
    value: str
