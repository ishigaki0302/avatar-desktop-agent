"""Tests for web / browser tools (Phase 18), using the deterministic StubWebClient."""

from pathlib import Path

import pytest

from agent.memory.store import MemoryStore
from agent.tools.base import ToolError
from agent.tools.registry import build_default_registry
from agent.tools.web import SearchResult, StubWebClient, WebSourceStore, WebTools, assert_safe_url


def _web_tools(tmp_path: Path) -> WebTools:
    client = StubWebClient(
        results=[
            SearchResult(title="知識編集の研究", url="https://example.com/a", snippet="..."),
            SearchResult(title="別の話題", url="https://example.com/b"),
        ],
        pages={"https://example.com/a": ("知識編集の研究", "本文: 知識編集とは...")},
    )
    return WebTools(client, WebSourceStore(tmp_path / "app.sqlite"))


def test_search_returns_results(tmp_path: Path) -> None:
    results = _web_tools(tmp_path).search("知識編集", limit=5)
    assert len(results) == 2
    assert results[0]["url"] == "https://example.com/a"


def test_read_url_saves_source(tmp_path: Path) -> None:
    db = tmp_path / "app.sqlite"
    tools = WebTools(
        StubWebClient(pages={"https://example.com/a": ("タイトル", "本文")}),
        WebSourceStore(db),
    )
    out = tools.read_url("https://example.com/a", query="知識編集")
    assert out["title"] == "タイトル"

    sources = WebSourceStore(db).list_sources()
    assert len(sources) == 1
    assert sources[0].url == "https://example.com/a"
    assert sources[0].query == "知識編集"


def test_ssrf_guard_blocks_localhost() -> None:
    with pytest.raises(ToolError, match="local/internal"):
        assert_safe_url("http://127.0.0.1:8123/secret")


def test_ssrf_guard_blocks_non_http() -> None:
    with pytest.raises(ToolError, match="http"):
        assert_safe_url("file:///etc/passwd")


def test_web_tools_require_confirmation(tmp_path: Path) -> None:
    client = StubWebClient(results=[SearchResult(title="t", url="https://example.com/a")])
    registry = build_default_registry(
        tmp_path,
        MemoryStore(tmp_path / "app.sqlite"),
        client,
        WebSourceStore(tmp_path / "app.sqlite"),
    )
    # Without confirm → refused.
    refused = registry.run("web.search", {"query": "x"})
    assert not refused.ok
    assert "confirmation required" in refused.error
    # With confirm → runs.
    allowed = registry.run("web.search", {"query": "x"}, confirm=True)
    assert allowed.ok
    assert len(allowed.output) == 1


def test_web_tools_registered_with_confirmation_flag(tmp_path: Path) -> None:
    registry = build_default_registry(
        tmp_path,
        MemoryStore(tmp_path / "app.sqlite"),
        StubWebClient(),
        WebSourceStore(tmp_path / "app.sqlite"),
    )
    specs = {s.name: s for s in registry.specs()}
    assert specs["web.search"].requires_confirmation
    assert specs["browser.read"].requires_confirmation
    assert not specs["filesystem.read"].requires_confirmation
