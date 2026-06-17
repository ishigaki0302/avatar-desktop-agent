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
    # Root directory that filesystem tools (Phase 17+) may list/read/search within.
    # Defaults to the user's home so "find my files" works; narrow via TOOLS_ROOT.
    tools_root: str = "~"

    # Memory retrieval embeddings (Phase 13). "hash" = offline/deterministic default.
    embedding_backend: str = "hash"  # "hash" | "ollama"
    embedding_model: str = "embeddinggemma"

    # Interaction analytics (Phase 15). "rule" = offline/deterministic default.
    analytics_backend: str = "rule"  # "rule" | "ollama"

    # Web tools (Phase 18). "http" = real fetch/search, "stub" = offline.
    web_backend: str = "http"  # "http" | "stub"

    # TTS (Phase 19). Off by default → text-only mode works out of the box.
    tts_enabled: bool = False
    tts_backend: str = "noop"  # "noop" | "voicevox"
    voicevox_url: str = "http://127.0.0.1:50021"
    voicevox_speaker: int = 1


settings = Settings()
