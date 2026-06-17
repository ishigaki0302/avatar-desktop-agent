"""TTS engines + sentence splitting (Phase 19).

Pluggable so the service runs text-only by default (NoopTTSEngine) and tests stay
deterministic. VoicevoxEngine (opt-in) calls a local VOICEVOX HTTP API. Long text
is split into sentences for chunked synthesis / lip-sync timing on the UI side.
"""

from __future__ import annotations

import re
from typing import Protocol, runtime_checkable

import httpx

from agent.config import settings

# Japanese sentence terminators (full-width period/exclamation/question) are
# intentional here; the regex must match them to split Japanese text.
_SENTENCE_RE = re.compile(r"[^。．！？!?\n]+[。．！？!?]?")  # noqa: RUF001
_TTS_TIMEOUT_S = 30.0


def split_sentences(text: str) -> list[str]:
    """Split text into sentences on Japanese/ASCII terminators and newlines."""
    return [s.strip() for s in _SENTENCE_RE.findall(text) if s.strip()]


@runtime_checkable
class TTSEngine(Protocol):
    """Synthesizes speech audio (WAV bytes) from text; empty bytes if unavailable."""

    def synthesize(self, text: str) -> bytes: ...


class NoopTTSEngine:
    """No-op engine for text-only mode / tests (returns no audio)."""

    def synthesize(self, text: str) -> bytes:
        _ = text
        return b""


class VoicevoxEngine:
    """Synthesize via a local VOICEVOX HTTP API (opt-in; requires VOICEVOX running)."""

    def __init__(self, base_url: str, speaker: int) -> None:
        self._base_url = base_url
        self._speaker = speaker

    def synthesize(self, text: str) -> bytes:
        query = httpx.post(
            f"{self._base_url}/audio_query",
            params={"text": text, "speaker": self._speaker},
            timeout=_TTS_TIMEOUT_S,
        )
        query.raise_for_status()
        synthesis = httpx.post(
            f"{self._base_url}/synthesis",
            params={"speaker": self._speaker},
            json=query.json(),
            timeout=_TTS_TIMEOUT_S,
        )
        synthesis.raise_for_status()
        return synthesis.content


def get_tts_engine() -> TTSEngine:
    """Return the configured TTS engine (noop by default, voicevox when requested)."""
    if settings.tts_backend == "voicevox":
        return VoicevoxEngine(settings.voicevox_url, settings.voicevox_speaker)
    return NoopTTSEngine()
