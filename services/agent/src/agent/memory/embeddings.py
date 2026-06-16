"""Embedding backends (Phase 13).

Pluggable so retrieval stays testable without a running model:
- HashEmbedder: deterministic, dependency-free. Default; used in tests/offline.
- OllamaEmbedder: real semantic embeddings via Ollama (EmbeddingGemma etc.).

The production path is OllamaEmbedder; HashEmbedder is a token-overlap stand-in.
"""

from __future__ import annotations

import hashlib
import math
from typing import Protocol, runtime_checkable

import httpx

from agent.config import settings

_HASH_DIM = 256
_EMBED_TIMEOUT_S = 30.0


@runtime_checkable
class Embedder(Protocol):
    """Maps texts to fixed-length vectors."""

    def embed(self, texts: list[str]) -> list[list[float]]: ...


def _normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0:
        return vec
    return [x / norm for x in vec]


class HashEmbedder:
    """Deterministic bag-of-tokens hashing embedder (no external dependency)."""

    def __init__(self, dim: int = _HASH_DIM) -> None:
        self._dim = dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        vec = [0.0] * self._dim
        for token in text.lower().split():
            digest = hashlib.sha1(token.encode("utf-8")).digest()  # noqa: S324 (non-crypto use)
            bucket = int.from_bytes(digest[:4], "big") % self._dim
            sign = 1.0 if digest[4] & 1 else -1.0
            vec[bucket] += sign
        return _normalize(vec)


class OllamaEmbedder:
    """Semantic embeddings via Ollama's /api/embed endpoint."""

    def __init__(self, base_url: str, model: str) -> None:
        self._base_url = base_url
        self._model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        res = httpx.post(
            f"{self._base_url}/api/embed",
            json={"model": self._model, "input": texts},
            timeout=_EMBED_TIMEOUT_S,
        )
        res.raise_for_status()
        data = res.json()
        return [_normalize(vec) for vec in data["embeddings"]]


def get_embedder() -> Embedder:
    """Return the configured embedder (hash by default, ollama when requested)."""
    if settings.embedding_backend == "ollama":
        return OllamaEmbedder(settings.ollama_base_url, settings.embedding_model)
    return HashEmbedder()
