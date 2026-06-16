"""Tests for the tool framework (Phase 17)."""

from pathlib import Path

import pytest

from agent.memory.store import MemoryStore
from agent.tools.base import ToolError
from agent.tools.filesystem import FilesystemTools
from agent.tools.registry import build_default_registry


def _workspace(tmp_path: Path) -> Path:
    (tmp_path / "README.md").write_text("# Hello\n本文です\n", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "note.txt").write_text("メモ", encoding="utf-8")
    (tmp_path / ".env").write_text("SECRET=xyz", encoding="utf-8")
    return tmp_path


def test_filesystem_list_and_read(tmp_path: Path) -> None:
    fs = FilesystemTools(_workspace(tmp_path))
    names = {e["name"] for e in fs.list_dir(".")}
    assert "README.md" in names
    assert fs.read_file("README.md")["content"].startswith("# Hello")


def test_filesystem_denies_sensitive_file(tmp_path: Path) -> None:
    fs = FilesystemTools(_workspace(tmp_path))
    with pytest.raises(ToolError, match="sensitive"):
        fs.read_file(".env")


def test_filesystem_denies_path_traversal(tmp_path: Path) -> None:
    fs = FilesystemTools(_workspace(tmp_path))
    with pytest.raises(ToolError, match="escapes"):
        fs.read_file("../outside.txt")


def test_registry_runs_filesystem_read(tmp_path: Path) -> None:
    registry = build_default_registry(_workspace(tmp_path), MemoryStore(tmp_path / "app.sqlite"))
    result = registry.run("filesystem.read", {"path": "README.md"})
    assert result.ok
    assert "Hello" in result.output["content"]


def test_registry_memory_write_then_search(tmp_path: Path) -> None:
    registry = build_default_registry(tmp_path, MemoryStore(tmp_path / "app.sqlite"))
    write = registry.run("memory.write", {"content": "知識編集を研究している", "importance": 5})
    assert write.ok
    found = registry.run("memory.search", {"query": "研究"})
    assert found.ok
    assert len(found.output) == 1


def test_registry_unknown_tool(tmp_path: Path) -> None:
    registry = build_default_registry(tmp_path, MemoryStore(tmp_path / "app.sqlite"))
    result = registry.run("filesystem.delete", {"path": "x"})
    assert not result.ok
    assert "unknown tool" in result.error


def test_registry_invalid_args(tmp_path: Path) -> None:
    registry = build_default_registry(tmp_path, MemoryStore(tmp_path / "app.sqlite"))
    result = registry.run("memory.write", {})  # missing required "content"
    assert not result.ok
    assert "invalid args" in result.error


def test_specs_list_all_tools(tmp_path: Path) -> None:
    registry = build_default_registry(tmp_path, MemoryStore(tmp_path / "app.sqlite"))
    names = {s.name for s in registry.specs()}
    assert names == {"filesystem.list", "filesystem.read", "memory.search", "memory.write"}
