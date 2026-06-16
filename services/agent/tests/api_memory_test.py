"""API-level tests for the memory / task / profile endpoints (Phase 12)."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agent.app import app, get_memory_store, get_profile_store
from agent.memory.profile import ProfileStore
from agent.memory.store import MemoryStore


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    app.dependency_overrides[get_memory_store] = lambda: MemoryStore(tmp_path / "app.sqlite")
    app.dependency_overrides[get_profile_store] = lambda: ProfileStore(tmp_path / "memory" / "profile.md")
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_memory_create_and_search(client: TestClient) -> None:
    created = client.post("/memories", json={"type": "semantic", "content": "知識編集を研究", "importance": 5})
    assert created.status_code == 201

    hits = client.get("/memories", params={"q": "研究"})
    assert hits.status_code == 200
    assert len(hits.json()) == 1
    assert hits.json()[0]["importance"] == 5


def test_task_create_and_filter(client: TestClient) -> None:
    created = client.post("/tasks", json={"title": "ログ基盤を実装"})
    assert created.status_code == 201
    task_id = created.json()["id"]

    client.patch(f"/tasks/{task_id}", json={"status": "in_progress"})
    listed = client.get("/tasks", params={"status": "in_progress"})
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_profile_roundtrip(client: TestClient) -> None:
    assert client.get("/profile").json()["content"] == ""
    client.put("/profile", json={"content": "# Profile\n- 呼び名: 石垣さん\n"})
    assert "石垣さん" in client.get("/profile").json()["content"]
