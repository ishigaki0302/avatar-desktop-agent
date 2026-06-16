"""Tests for dashboard aggregation (Phase 16)."""

from pathlib import Path

from agent.analytics.analyzer import RuleAnalyzer
from agent.analytics.store import AnalyticsStore
from agent.dashboard import Dashboard
from agent.logger.interaction_logger import InteractionLogger


def _seed(db: Path) -> tuple[str, str, str]:
    logger = InteractionLogger(db)
    session = logger.start_session(model="gemma4:31b", title="test")
    t1 = logger.log_turn(session.id, user_input="知識編集を研究したい", assistant_output="いいね", latency_ms=1000)
    t2 = logger.log_turn(session.id, user_input="違う、それは浅い", assistant_output="ごめん", latency_ms=2000)

    logger.log_tool_call(t1.id, "filesystem.read", status="ok")
    logger.log_tool_call(t1.id, "web.search", status="error")
    logger.log_memory_access(t1.id, "read", memory_id="m1")
    logger.log_explicit_feedback(t1.id, rating=5, label="helpful")

    AnalyticsStore(db).record(t2.id, RuleAnalyzer().analyze("違う、それは浅い"))
    return session.id, t1.id, t2.id


def test_list_sessions_rollup(tmp_path: Path) -> None:
    db = tmp_path / "app.sqlite"
    _seed(db)
    overviews = Dashboard(db).list_sessions()
    assert len(overviews) == 1
    assert overviews[0].turn_count == 2
    assert overviews[0].avg_latency_ms == 1500


def test_session_detail_includes_all_logs(tmp_path: Path) -> None:
    db = tmp_path / "app.sqlite"
    session_id, t1, _t2 = _seed(db)
    detail = Dashboard(db).session_detail(session_id)
    assert detail is not None
    assert len(detail.turns) == 2

    turn1 = next(td for td in detail.turns if td.turn.id == t1)
    assert len(turn1.tool_calls) == 2
    assert len(turn1.memory_accesses) == 1  # 使われた記憶が見える
    assert len(turn1.explicit_feedback) == 1


def test_search_finds_turn(tmp_path: Path) -> None:
    db = tmp_path / "app.sqlite"
    _seed(db)
    hits = Dashboard(db).search_turns("研究")
    assert len(hits) == 1
    assert "研究" in hits[0].user_input


def test_dissatisfaction_list(tmp_path: Path) -> None:
    db = tmp_path / "app.sqlite"
    _session, _t1, t2 = _seed(db)
    flagged = Dashboard(db).dissatisfaction()
    assert len(flagged) == 1
    assert flagged[0].turn_id == t2
    assert flagged[0].issue_type == "misunderstanding"


def test_stats_rollup(tmp_path: Path) -> None:
    db = tmp_path / "app.sqlite"
    _seed(db)
    stats = Dashboard(db).stats()
    assert stats.session_count == 1
    assert stats.turn_count == 2
    assert stats.tool_call_count == 2
    assert stats.tool_success_rate == 0.5
    assert stats.memory_access_count == 1
    assert stats.rating_counts == {"5": 1}
    assert stats.issue_type_counts == {"misunderstanding": 1}


def test_empty_dashboard(tmp_path: Path) -> None:
    db = tmp_path / "app.sqlite"
    dashboard = Dashboard(db)
    assert dashboard.list_sessions() == []
    assert dashboard.stats().turn_count == 0
    assert dashboard.session_detail("missing") is None
