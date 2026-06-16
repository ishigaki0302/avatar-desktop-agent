"""Tests for Phase 10 logs: prompt / tool / memory-access / avatar."""

from pathlib import Path

from agent.logger.interaction_logger import InteractionLogger


def _turn(logger: InteractionLogger) -> str:
    session = logger.start_session(model="gemma4:31b")
    return logger.log_turn(session.id, user_input="やあ", assistant_output="どうも").id


def test_prompt_log_records_construction(tmp_path: Path) -> None:
    logger = InteractionLogger(tmp_path / "app.sqlite")
    turn_id = _turn(logger)
    logger.log_prompt(
        turn_id,
        system_prompt="あなたはアリス",
        memory_context="名前: 田中",
        final_prompt="...",
    )
    prompts = logger.get_prompts(turn_id)
    assert len(prompts) == 1
    assert prompts[0].turn_id == turn_id
    assert prompts[0].memory_context == "名前: 田中"


def test_tool_calls_are_logged_in_order(tmp_path: Path) -> None:
    logger = InteractionLogger(tmp_path / "app.sqlite")
    turn_id = _turn(logger)
    logger.log_tool_call(turn_id, "filesystem.list", input_json='{"path": "."}', status="ok")
    logger.log_tool_call(turn_id, "filesystem.read", status="error", error="not found")

    calls = logger.get_tool_calls(turn_id)
    assert [c.tool_name for c in calls] == ["filesystem.list", "filesystem.read"]
    assert calls[1].status == "error"
    assert calls[1].error == "not found"


def test_memory_access_log_keeps_scores_and_type(tmp_path: Path) -> None:
    logger = InteractionLogger(tmp_path / "app.sqlite")
    turn_id = _turn(logger)
    logger.log_memory_access(
        turn_id,
        "read",
        memory_id="m1",
        relevance_score=0.8,
        final_score=0.7,
        reason="similar to query",
    )
    accesses = logger.get_memory_accesses(turn_id)
    assert len(accesses) == 1
    assert accesses[0].access_type == "read"
    assert accesses[0].relevance_score == 0.8


def test_avatar_event_roundtrips_bool_flag(tmp_path: Path) -> None:
    logger = InteractionLogger(tmp_path / "app.sqlite")
    turn_id = _turn(logger)
    logger.log_avatar_event(turn_id, emotion="happy", motion="nod", tts_enabled=True, tts_text="どうも")

    events = logger.get_avatar_events(turn_id)
    assert len(events) == 1
    # tts_enabled is stored as INTEGER but must come back as a bool.
    assert events[0].tts_enabled is True
    assert events[0].emotion == "happy"
