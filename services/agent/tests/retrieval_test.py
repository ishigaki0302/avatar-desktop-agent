"""Tests for memory retrieval (Phase 13), using the deterministic HashEmbedder."""

from pathlib import Path

from agent.logger.interaction_logger import InteractionLogger
from agent.memory.embeddings import HashEmbedder
from agent.memory.retrieval import MemoryRetriever, build_context
from agent.memory.store import MemoryStore


def _retriever(tmp_path: Path) -> tuple[MemoryStore, MemoryRetriever]:
    db = tmp_path / "app.sqlite"
    store = MemoryStore(db)
    retriever = MemoryRetriever(db, store, embedder=HashEmbedder())
    return store, retriever


def test_relevant_memory_ranks_first(tmp_path: Path) -> None:
    store, retriever = _retriever(tmp_path)
    store.add_memory("semantic", "ユーザー は 知識 編集 を 研究 している")
    store.add_memory("semantic", "ユーザー は コーヒー が 好き")

    results = retriever.retrieve("知識 編集 の 研究", limit=5)
    assert results
    assert "知識" in results[0].memory.content
    # Scores are populated.
    assert results[0].relevance > 0
    assert 0.0 <= results[0].final <= 1.0


def test_limit_caps_results(tmp_path: Path) -> None:
    store, retriever = _retriever(tmp_path)
    for i in range(6):
        store.add_memory("semantic", f"事実 番号 {i}")
    assert len(retriever.retrieve("事実", limit=3)) == 3


def test_empty_store_returns_nothing(tmp_path: Path) -> None:
    _store, retriever = _retriever(tmp_path)
    assert retriever.retrieve("なんでも") == []


def test_retrieval_writes_memory_access_logs(tmp_path: Path) -> None:
    db = tmp_path / "app.sqlite"
    store = MemoryStore(db)
    retriever = MemoryRetriever(db, store, embedder=HashEmbedder())
    logger = InteractionLogger(db)
    session = logger.start_session(model="gemma4:31b")
    turn_id = logger.log_turn(session.id, user_input="研究の話").id

    store.add_memory("semantic", "知識 編集 の 研究")
    results = retriever.retrieve("知識 編集", limit=5, logger=logger, turn_id=turn_id)
    assert results

    accesses = logger.get_memory_accesses(turn_id)
    assert len(accesses) == len(results)
    assert accesses[0].access_type == "read"
    assert accesses[0].final_score is not None


def test_build_context_includes_memories_and_tasks(tmp_path: Path) -> None:
    store, retriever = _retriever(tmp_path)
    store.add_memory("semantic", "知識 編集 の 研究")
    store.add_task("ログ基盤を実装", status="in_progress")

    results = retriever.retrieve("研究", limit=5)
    context = build_context(results, store.list_tasks(status="in_progress"))
    assert "関連する記憶" in context
    assert "現在のタスク" in context
    assert "ログ基盤を実装" in context
