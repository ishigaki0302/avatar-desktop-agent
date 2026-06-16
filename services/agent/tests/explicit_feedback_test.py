"""Tests for Phase 11 explicit feedback logging."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from agent.logger.interaction_logger import InteractionLogger


def _turn(logger: InteractionLogger) -> str:
    session = logger.start_session(model="gemma4:31b")
    return logger.log_turn(session.id, user_input="やあ", assistant_output="どうも").id


def test_feedback_is_recorded_and_readable(tmp_path: Path) -> None:
    logger = InteractionLogger(tmp_path / "app.sqlite")
    turn_id = _turn(logger)
    logger.log_explicit_feedback(turn_id, rating=2, label="too_shallow", comment="もっと具体的に")

    feedback = logger.get_feedback(turn_id)
    assert len(feedback) == 1
    assert feedback[0].rating == 2
    assert feedback[0].label == "too_shallow"
    assert feedback[0].comment == "もっと具体的に"


def test_thumbs_up_without_comment(tmp_path: Path) -> None:
    logger = InteractionLogger(tmp_path / "app.sqlite")
    turn_id = _turn(logger)
    logger.log_explicit_feedback(turn_id, rating=5, label="helpful")
    assert logger.get_feedback(turn_id)[0].comment is None


def test_rating_out_of_range_is_rejected(tmp_path: Path) -> None:
    logger = InteractionLogger(tmp_path / "app.sqlite")
    turn_id = _turn(logger)
    with pytest.raises(ValidationError):
        logger.log_explicit_feedback(turn_id, rating=9)
