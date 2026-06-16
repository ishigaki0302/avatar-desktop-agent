"""Tests for memory write & consolidation (Phase 14)."""

from pathlib import Path

from agent.logger.interaction_logger import InteractionLogger
from agent.memory.embeddings import HashEmbedder
from agent.memory.store import MemoryStore
from agent.memory.writer import MemoryOperation, MemoryWriter, is_explicit_memory_request


def _writer(tmp_path: Path) -> tuple[MemoryStore, MemoryWriter]:
    db = tmp_path / "app.sqlite"
    store = MemoryStore(db)
    return store, MemoryWriter(store, embedder=HashEmbedder())


def test_explicit_request_detection() -> None:
    assert is_explicit_memory_request("コーヒーが好きって覚えておいて")
    assert is_explicit_memory_request("これメモして")
    assert not is_explicit_memory_request("今日はいい天気だね")


def test_write_explicit_saves_high_importance_memory(tmp_path: Path) -> None:
    _store, writer = _writer(tmp_path)
    saved = writer.write_explicit("私はコーヒーが好き、覚えておいて")
    assert saved is not None
    assert saved.importance == 5
    assert saved.source == "explicit"
    assert "コーヒー" in saved.content
    # Non-explicit input writes nothing.
    assert writer.write_explicit("こんにちは") is None


def test_apply_operations_create_update_delete_noop(tmp_path: Path) -> None:
    store, writer = _writer(tmp_path)
    seed = store.add_memory("semantic", "Windows を使っている")

    ops = [
        MemoryOperation(operation="CREATE", content="知識編集を研究している"),
        MemoryOperation(operation="UPDATE", target_id=seed.id, content="Linux を使っている"),
        MemoryOperation(operation="NOOP", content="どうでもいい雑談"),
    ]
    applied = writer.apply(ops)
    assert len(applied) == 2  # CREATE + UPDATE return memories, NOOP does not

    contents = {m.content for m in store.search_memories(limit=50)}
    assert "知識編集を研究している" in contents
    assert "Linux を使っている" in contents
    assert "Windows を使っている" not in contents  # updated in place


def test_delete_supersedes_memory(tmp_path: Path) -> None:
    store, writer = _writer(tmp_path)
    mem = store.add_memory("semantic", "古い事実")
    writer.apply([MemoryOperation(operation="DELETE", target_id=mem.id)])
    assert store.search_memories("古い") == []
    assert store.get_memory(mem.id) is not None  # kept for history


def test_consolidate_merges_duplicates(tmp_path: Path) -> None:
    store, writer = _writer(tmp_path)
    store.add_memory("semantic", "ユーザー は コーヒー が 好き")
    store.add_memory("semantic", "ユーザー は コーヒー が 好き")  # duplicate
    store.add_memory("semantic", "ユーザー は 紅茶 が 好き")  # distinct

    merged = writer.consolidate_duplicates()
    assert merged == 1
    # One of the duplicates remains active; the distinct one stays.
    active = store.search_memories(limit=50)
    assert len(active) == 2


def test_write_logs_memory_access(tmp_path: Path) -> None:
    db = tmp_path / "app.sqlite"
    store = MemoryStore(db)
    writer = MemoryWriter(store, embedder=HashEmbedder())
    logger = InteractionLogger(db)
    session = logger.start_session(model="gemma4:31b")
    turn_id = logger.log_turn(session.id, user_input="覚えておいて").id

    writer.write_explicit("コーヒーが好き、覚えておいて", logger=logger, turn_id=turn_id)
    accesses = logger.get_memory_accesses(turn_id)
    assert len(accesses) == 1
    assert accesses[0].access_type == "write"
