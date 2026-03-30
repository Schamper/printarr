from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Paths
    data_dir: Path = Path("/config")

    # Server
    port: int = 6969
    log_level: str = "INFO"

    # Source API keys
    thingiverse_api_token: str = ""

    @property
    def database_url(self) -> str:
        db_path = self.data_dir / "printarr.db"
        return f"sqlite+aiosqlite:///{db_path}"


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    global _settings
    _settings = None
