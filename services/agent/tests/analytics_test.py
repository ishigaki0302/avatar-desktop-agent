"""Tests for interaction analytics (Phase 15), using the deterministic RuleAnalyzer."""

from pathlib import Path

from agent.analytics.analyzer import RuleAnalyzer
from agent.analytics.store import AnalyticsStore
from agent.logger.interaction_logger import InteractionLogger


def test_detects_correction_as_dissatisfaction() -> None:
    analysis = RuleAnalyzer().analyze("違う、そうじゃなくて")
    assert analysis.issue_type == "misunderstanding"
    assert analysis.predicted_satisfaction < 0.6
    assert analysis.evidence is not None


def test_detects_too_abstract_request() -> None:
    analysis = RuleAnalyzer().analyze("もっと具体的に説明して")
    assert analysis.issue_type == "too_abstract"


def test_positive_feedback_raises_satisfaction() -> None:
    analysis = RuleAnalyzer().analyze("いいね、助かる")
    assert analysis.predicted_satisfaction > 0.6
    assert analysis.issue_type is None


def test_high_latency_flagged_when_no_other_signal() -> None:
    analysis = RuleAnalyzer().analyze("わかった", latency_ms=45_000)
    assert analysis.issue_type == "latency"


def test_neutral_input_has_low_confidence() -> None:
    analysis = RuleAnalyzer().analyze("今日はいい天気だね")
    assert analysis.issue_type is None
    assert analysis.confidence < 0.5


def test_record_and_query_inferred_feedback(tmp_path: Path) -> None:
    db = tmp_path / "app.sqlite"
    logger = InteractionLogger(db)
    session = logger.start_session(model="gemma4:31b")
    turn_id = logger.log_turn(session.id, user_input="違う、それは浅い").id

    analytics = AnalyticsStore(db)
    analysis = RuleAnalyzer().analyze("違う、それは浅い")
    analytics.record(turn_id, analysis)

    stored = analytics.get_for_turn(turn_id)
    assert len(stored) == 1
    assert stored[0].issue_type == "misunderstanding"
    assert analytics.issue_type_counts()["misunderstanding"] == 1
