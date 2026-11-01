from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    app_env: str = "development"
    log_level: str = "INFO"
    ai_enabled: bool = False
    database_url: str = ""
    allowed_origins: list[str] = Field(default_factory=list)
    allowed_document_types: list[str] = Field(default_factory=lambda: ["txt", "md", "pdf", "docx"])
    max_upload_mb: int = 10
    max_docs_per_user: int = 20

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
