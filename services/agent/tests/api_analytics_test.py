"""API-level test for the analytics endpoints (Phase 15)."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agent.analytics.store import AnalyticsStore
from agent.app import app, get_analytics_store, get_logger
from agent.logger.interaction_logger import InteractionLogger


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    db = tmp_path / "app.sqlite"
    # Analytics and the logger must share the DB: inferred_feedback_logs FKs turn_logs.
    app.dependency_overrides[get_analytics_store] = lambda: AnalyticsStore(db)
    app.dependency_overrides[get_logger] = lambda: InteractionLogger(db)
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_analyze_and_read_back(client: TestClient) -> None:
    session_id = client.post("/sessions", json={"model": "gemma4:31b"}).json()["id"]
    turn_id = client.post(f"/sessions/{session_id}/turns", json={"user_input": "違う、それは浅い"}).json()["id"]

    created = client.post(f"/turns/{turn_id}/analyze", json={"user_input": "違う、それは浅い"})
    assert created.status_code == 201
    assert created.json()["issue_type"] == "misunderstanding"

    stored = client.get(f"/turns/{turn_id}/inferred-feedback")
    assert stored.status_code == 200
    assert len(stored.json()) == 1

    counts = client.get("/analytics/issue-types")
    assert counts.json()["misunderstanding"] == 1
