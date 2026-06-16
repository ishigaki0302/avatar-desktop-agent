"""Tests for the long-term memory store: memories + tasks (Phase 12)."""

from pathlib import Path

from agent.memory.store import MemoryStore


def test_memory_search_by_keyword_and_type(tmp_path: Path) -> None:
    store = MemoryStore(tmp_path / "app.sqlite")
    store.add_memory("semantic", "ユーザーは知識編集を研究している", importance=5)
    store.add_memory("semantic", "ユーザーはコーヒーが好き", importance=2)
    store.add_memory("episodic", "今日は要件定義を相談した")

    hits = store.search_memories("研究")
    assert len(hits) == 1
    assert "知識編集" in hits[0].content

    semantic = store.search_memories(memory_type="semantic")
    assert len(semantic) == 2
    # Ordered by importance DESC.
    assert semantic[0].importance == 5


def test_memory_update_and_persistence(tmp_path: Path) -> None:
    db = tmp_path / "app.sqlite"
    first = MemoryStore(db)
    mem = first.add_memory("semantic", "Windows を使っている", metadata={"confidence": "low"})

    updated = first.update_memory(mem.id, content="Linux を使っている", importance=4)
    assert updated is not None
    assert updated.content == "Linux を使っている"
    assert updated.importance == 4
    # Untouched field preserved via COALESCE.
    assert updated.metadata == {"confidence": "low"}

    reloaded = MemoryStore(db).get_memory(mem.id)
    assert reloaded is not None
    assert reloaded.content == "Linux を使っている"


def test_superseded_memory_hidden_from_search(tmp_path: Path) -> None:
    store = MemoryStore(tmp_path / "app.sqlite")
    mem = store.add_memory("semantic", "古い事実")
    store.supersede_memory(mem.id)

    assert store.search_memories("古い") == []
    assert store.search_memories("古い", include_superseded=True)[0].id == mem.id


def test_tasks_lifecycle_and_persistence(tmp_path: Path) -> None:
    db = tmp_path / "app.sqlite"
    store = MemoryStore(db)
    task = store.add_task("Interaction Logging を実装", due_date="2026-06-20")
    assert task.status == "todo"

    store.update_task(task.id, status="in_progress")
    store.add_task("memory schema を設計", status="done")

    todo = store.list_tasks(status="in_progress")
    assert len(todo) == 1
    assert todo[0].title == "Interaction Logging を実装"

    # Survives restart.
    assert len(MemoryStore(db).list_tasks()) == 2
