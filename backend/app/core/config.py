"""Konfigurasi aplikasi — satu-satunya tempat membaca environment variable."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL

# backend/app/core/config.py → parents[3] = root repo (saat jalan di host).
# Di container, KNOWLEDGE_BASE_DIR di-override oleh docker-compose.
_DEFAULT_KB_DIR = Path(__file__).resolve().parents[3] / "knowledge_base"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # App
    app_name: str = "LearnFlow API"
    app_version: str = "0.1.0"
    app_env: Literal["development", "production"] = "development"
    log_level: str = "info"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # PostgreSQL
    postgres_user: str = "learnflow"
    postgres_password: SecretStr = SecretStr("")
    postgres_db: str = "learnflow"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # LLM (dipakai mulai Milestone 1)
    llm_provider: Literal["gemini", "claude", "openai", "deepseek"] = "gemini"
    llm_model: str = ""
    llm_api_key: SecretStr = SecretStr("")
    llm_temperature: float = 0.2

    # Rate limit (slowapi)
    rate_limit_generate: str = "3/hour"
    rate_limit_default: str = "60/minute"

    # Knowledge base statis (JSON)
    knowledge_base_dir: Path = _DEFAULT_KB_DIR

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip().rstrip("/") for o in self.cors_origins.split(",") if o.strip()]

    @property
    def database_url(self) -> URL:
        """URL.create meng-escape karakter spesial di password (@, :, / dst)."""
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
