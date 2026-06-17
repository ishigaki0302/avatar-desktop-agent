"""Tests for the SQLite-backed interaction logger (Phase 9)."""

from pathlib import Path

from agent.logger.interaction_logger import InteractionLogger


def test_logs_all_turns_including_casual_talk(tmp_path: Path) -> None:
    db = tmp_path / "app.sqlite"
    logger = InteractionLogger(db)

    session = logger.start_session(model="gemma4:31b", title="test")
    logger.log_turn(
        session.id,
        user_input="今日やること整理して",
        assistant_output="まずは…",
        model="gemma4:31b",
        latency_ms=1200,
    )
    # Casual chat / opinions must be stored too, not just task requests.
    logger.log_turn(session.id, user_input="昨日見た映画、微妙だった", assistant_output="そうなんだ", emotion="sad")
    logger.log_turn(session.id, user_input="今の回答ちょっと違う", assistant_output="ごめん、直すね", status="ok")

    turns = logger.get_turns(session.id)
    assert len(turns) == 3
    # turn_index is assigned sequentially from 0.
    assert [t.turn_index for t in turns] == [0, 1, 2]
    assert turns[1].user_input == "昨日見た映画、微妙だった"
    assert turns[0].model == "gemma4:31b"
    assert turns[0].latency_ms == 1200


def test_persists_across_logger_instances(tmp_path: Path) -> None:
    db = tmp_path / "app.sqlite"
    first = InteractionLogger(db)
    session = first.start_session(model="gemma4:31b")
    first.log_turn(session.id, user_input="覚えておいて")
    first.end_session(session.id, summary="短い雑談")

    # A fresh instance on the same file must see the persisted data.
    second = InteractionLogger(db)
    reloaded = second.get_session(session.id)
    assert reloaded is not None
    assert reloaded.ended_at is not None
    assert reloaded.summary == "短い雑談"
    assert len(second.get_turns(session.id)) == 1


def test_update_turn_fills_in_assistant_side(tmp_path: Path) -> None:
    db = tmp_path / "app.sqlite"
    logger = InteractionLogger(db)
    session = logger.start_session(model="gemma4:31b")
    # Open the turn with only the user input (as the bridge does before tools run).
    turn = logger.log_turn(session.id, user_input="今日の天気は")
    assert turn.assistant_output is None

    updated = logger.update_turn(turn.id, assistant_output="晴れだよ", emotion="happy", latency_ms=1200)
    assert updated is not None
    assert updated.assistant_output == "晴れだよ"
    assert updated.emotion == "happy"
    assert updated.latency_ms == 1200
    # user_input is preserved (COALESCE leaves untouched fields).
    assert updated.user_input == "今日の天気は"


def test_sessions_are_listed_independently(tmp_path: Path) -> None:
    logger = InteractionLogger(tmp_path / "app.sqlite")
    a = logger.start_session(model="gemma4:31b")
    b = logger.start_session(model="gemma4:12b")
    logger.log_turn(a.id, user_input="A-1")

    ids = {s.id for s in logger.list_sessions()}
    assert {a.id, b.id} <= ids
    assert logger.get_turns(b.id) == []
