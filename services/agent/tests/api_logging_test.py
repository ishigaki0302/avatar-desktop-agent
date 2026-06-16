"""API-level tests for the interaction logging endpoints (Phase 9)."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agent.app import app, get_logger
from agent.logger.interaction_logger import InteractionLogger


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    app.dependency_overrides[get_logger] = lambda: InteractionLogger(tmp_path / "app.sqlite")
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_session_and_turn_roundtrip(client: TestClient) -> None:
    created = client.post("/sessions", json={"model": "gemma4:31b"})
    assert created.status_code == 201
    session_id = created.json()["id"]

    turn = client.post(
        f"/sessions/{session_id}/turns",
        json={"user_input": "やあ", "assistant_output": "こんにちは", "emotion": "happy"},
    )
    assert turn.status_code == 201
    assert turn.json()["turn_index"] == 0

    turns = client.get(f"/sessions/{session_id}/turns")
    assert turns.status_code == 200
    assert len(turns.json()) == 1
    assert turns.json()[0]["assistant_output"] == "こんにちは"


def test_get_unknown_session_returns_404(client: TestClient) -> None:
    assert client.get("/sessions/does-not-exist").status_code == 404


def test_turn_event_logs_readable_via_api(client: TestClient, tmp_path: Path) -> None:
    session_id = client.post("/sessions", json={"model": "gemma4:31b"}).json()["id"]
    turn_id = client.post(f"/sessions/{session_id}/turns", json={"user_input": "やあ"}).json()["id"]

    # Event logs are written in-process; share the same DB file the API uses.
    logger = InteractionLogger(tmp_path / "app.sqlite")
    logger.log_tool_call(turn_id, "filesystem.list", status="ok")
    logger.log_memory_access(turn_id, "read", memory_id="m1")

    calls = client.get(f"/turns/{turn_id}/tool-calls")
    assert calls.status_code == 200
    assert len(calls.json()) == 1
    assert calls.json()[0]["tool_name"] == "filesystem.list"

    accesses = client.get(f"/turns/{turn_id}/memory-accesses")
    assert accesses.status_code == 200
    assert accesses.json()[0]["access_type"] == "read"
