"""Tests for profile memory (Phase 12)."""

from pathlib import Path

from agent.memory.profile import ProfileStore


def test_profile_read_default_empty(tmp_path: Path) -> None:
    profile = ProfileStore(tmp_path / "memory" / "profile.md")
    assert profile.read() == ""


def test_profile_write_then_read_and_overwrite(tmp_path: Path) -> None:
    path = tmp_path / "memory" / "profile.md"
    profile = ProfileStore(path)
    profile.write("# Profile\n- 呼び名: 石垣さん\n")
    assert "石垣さん" in profile.read()

    # Profile is current truth: overwrite replaces.
    profile.write("# Profile\n- 呼び名: 石垣さん\n- 口調: カジュアル\n")
    reloaded = ProfileStore(path).read()
    assert "口調: カジュアル" in reloaded
