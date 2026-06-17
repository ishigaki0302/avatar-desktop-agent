"""Tests for recursive filesystem.search (file discovery)."""

from pathlib import Path

from agent.tools.filesystem import FilesystemTools


def _workspace(tmp_path: Path) -> Path:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "自己紹介.pptx").write_text("x", encoding="utf-8")
    (tmp_path / "docs" / "memo.txt").write_text("x", encoding="utf-8")
    (tmp_path / "sub" / "deep").mkdir(parents=True)
    (tmp_path / "sub" / "deep" / "slides.pptx").write_text("x", encoding="utf-8")
    # Pruned/sensitive entries that must NOT surface.
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "ignored.pptx").write_text("x", encoding="utf-8")
    (tmp_path / ".secret.pptx").write_text("x", encoding="utf-8")
    return tmp_path


def test_search_finds_files_recursively(tmp_path: Path) -> None:
    fs = FilesystemTools(_workspace(tmp_path))
    hits = {Path(h["path"]).name for h in fs.search("*.pptx")}
    assert "自己紹介.pptx" in hits
    assert "slides.pptx" in hits  # nested


def test_search_prunes_heavy_and_hidden(tmp_path: Path) -> None:
    fs = FilesystemTools(_workspace(tmp_path))
    paths = {h["path"] for h in fs.search("*.pptx")}
    assert not any("node_modules" in p for p in paths)  # pruned dir
    assert not any(".secret" in p for p in paths)  # deny-listed


def test_search_name_substring(tmp_path: Path) -> None:
    fs = FilesystemTools(_workspace(tmp_path))
    hits = {Path(h["path"]).name for h in fs.search("*自己紹介*")}
    assert hits == {"自己紹介.pptx"}


def test_search_no_match(tmp_path: Path) -> None:
    fs = FilesystemTools(_workspace(tmp_path))
    assert fs.search("*.xlsx") == []
