"""Runtime configuration loaded from environment variables / .env."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.

    Mirrors the TS-side `OLLAMA_*` env vars so a single `.env` can drive both.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma4:31b"
    ollama_timeout_ms: int = 120_000
    storage_dir: str = "./storage"


settings = Settings()
