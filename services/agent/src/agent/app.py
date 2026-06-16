"""FastAPI entry point for the avatar-agent backend."""

from __future__ import annotations

from fastapi import FastAPI

from agent.config import settings

app = FastAPI(title="avatar-agent", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe. Returns the active model so the UI can display it."""
    return {"status": "ok", "model": settings.ollama_model}
