"""Tests for TTS engine + sentence splitting + avatar events (Phase 19)."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agent.app import app, get_logger
from agent.logger.interaction_logger import InteractionLogger
from agent.tts.engine import NoopTTSEngine, split_sentences


def test_split_sentences_japanese_and_newlines() -> None:
    sentences = split_sentences("こんにちは。元気です。\nそうですね。")
    assert sentences == ["こんにちは。", "元気です。", "そうですね。"]


def test_split_sentences_ignores_empty() -> None:
    assert split_sentences("   \n  ") == []


def test_noop_engine_returns_no_audio() -> None:
    assert NoopTTSEngine().synthesize("読み上げて") == b""


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    app.dependency_overrides[get_logger] = lambda: InteractionLogger(tmp_path / "app.sqlite")
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_tts_text_only_mode(client: TestClient) -> None:
    # Default config has tts_enabled=False → text-only mode (no audio, still segments).
    res = client.post("/tts", json={"text": "こんにちは。元気です。"})
    assert res.status_code == 200
    body = res.json()
    assert body["enabled"] is False
    assert body["sentences"] == ["こんにちは。", "元気です。"]
    assert body["audio_base64"] is None


def test_avatar_event_roundtrip(client: TestClient) -> None:
    session_id = client.post("/sessions", json={"model": "gemma4:31b"}).json()["id"]
    turn_id = client.post(f"/sessions/{session_id}/turns", json={"user_input": "やあ"}).json()["id"]

    created = client.post(
        f"/turns/{turn_id}/avatar-events",
        json={"emotion": "happy", "motion": "nod", "tts_enabled": True, "tts_text": "どうも"},
    )
    assert created.status_code == 201
    assert created.json()["emotion"] == "happy"

    events = client.get(f"/turns/{turn_id}/avatar-events")
    assert events.status_code == 200
    assert len(events.json()) == 1
    assert events.json()[0]["tts_enabled"] is True
