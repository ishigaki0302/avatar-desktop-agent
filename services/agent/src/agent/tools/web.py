"""Web / browser tools (Phase 18).

Pluggable web client (HttpWebClient real / StubWebClient for tests/offline) plus
a source store so fetched pages can be cited later. Outbound fetches are guarded
against SSRF (localhost / private IPs / non-http schemes are refused). Marking
these tools as external + confirmation-gated happens in the registry.
"""

from __future__ import annotations

import html
import ipaddress
import re
import socket
import ssl
from contextlib import closing
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Protocol, runtime_checkable
from urllib.parse import urlparse
from uuid import uuid4

import httpx
import truststore
from pydantic import BaseModel

from agent.logger.db import connect
from agent.tools.base import ToolError

if TYPE_CHECKING:
    from pathlib import Path

_FETCH_TIMEOUT_S = 20.0
_MAX_CONTENT_CHARS = 20_000
_DEFAULT_SEARCH_LIMIT = 5
# Verify TLS against the OS trust store so corporate MITM proxies (self-signed
# root CA) work — the default certifi bundle rejects them.
_VERIFY = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
_TAG_RE = re.compile(r"<[^>]+>")
_SCRIPT_STYLE_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_WS_RE = re.compile(r"\s+")

_CREATE_SOURCES = """
CREATE TABLE IF NOT EXISTS web_sources (
  id         TEXT PRIMARY KEY,
  url        TEXT NOT NULL,
  title      TEXT,
  content    TEXT,
  query      TEXT,
  fetched_at TEXT NOT NULL
)
"""


class SearchResult(BaseModel):
    """A single web search hit."""

    title: str
    url: str
    snippet: str = ""


class WebSource(BaseModel):
    """A fetched page persisted for citation."""

    id: str
    url: str
    title: str | None = None
    content: str | None = None
    query: str | None = None
    fetched_at: str


@runtime_checkable
class WebClient(Protocol):
    """Performs web searches and page fetches."""

    def search(self, query: str, limit: int) -> list[SearchResult]: ...
    def fetch(self, url: str) -> tuple[str, str]: ...  # (title, text)


def _html_to_text(raw: str) -> str:
    without_scripts = _SCRIPT_STYLE_RE.sub(" ", raw)
    text = _TAG_RE.sub(" ", without_scripts)
    return _WS_RE.sub(" ", html.unescape(text)).strip()


def _extract_title(raw: str) -> str:
    match = _TITLE_RE.search(raw)
    return _WS_RE.sub(" ", html.unescape(match.group(1))).strip() if match else ""


def assert_safe_url(url: str) -> None:
    """Reject non-http(s) schemes and localhost / private / loopback hosts (SSRF guard)."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ToolError("only http(s) URLs are allowed")
    host = parsed.hostname
    if not host:
        raise ToolError("invalid URL host")
    try:
        infos = socket.getaddrinfo(host, None)
    except OSError as exc:
        raise ToolError(f"cannot resolve host: {host}") from exc
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise ToolError("access to local/internal addresses is denied")


class HttpWebClient:
    """Real web client over httpx. Search uses DuckDuckGo's HTML endpoint (best-effort)."""

    _RESULT_RE = re.compile(r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.DOTALL)

    def search(self, query: str, limit: int) -> list[SearchResult]:
        res = httpx.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query},
            timeout=_FETCH_TIMEOUT_S,
            headers={"User-Agent": "Mozilla/5.0 (avatar-agent)"},
            verify=_VERIFY,
        )
        res.raise_for_status()
        results: list[SearchResult] = []
        for url, title_html in self._RESULT_RE.findall(res.text)[:limit]:
            results.append(SearchResult(title=_html_to_text(title_html), url=url, snippet=""))
        return results

    def fetch(self, url: str) -> tuple[str, str]:
        assert_safe_url(url)
        res = httpx.get(
            url,
            timeout=_FETCH_TIMEOUT_S,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (avatar-agent)"},
            verify=_VERIFY,
        )
        res.raise_for_status()
        return _extract_title(res.text), _html_to_text(res.text)[:_MAX_CONTENT_CHARS]


class StubWebClient:
    """Deterministic offline web client (tests / offline mode)."""

    def __init__(
        self,
        results: list[SearchResult] | None = None,
        pages: dict[str, tuple[str, str]] | None = None,
    ) -> None:
        self._results = results or []
        self._pages = pages or {}

    def search(self, query: str, limit: int) -> list[SearchResult]:
        _ = query
        return self._results[:limit]

    def fetch(self, url: str) -> tuple[str, str]:
        assert_safe_url(url)
        return self._pages.get(url, ("", f"stub content for {url}"))


class WebSourceStore:
    """Persists fetched web sources for later citation."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        with closing(connect(db_path)) as conn, conn:
            conn.execute(_CREATE_SOURCES)

    def save(self, url: str, title: str | None, content: str | None, query: str | None) -> WebSource:
        source = WebSource(
            id=uuid4().hex,
            url=url,
            title=title,
            content=content,
            query=query,
            fetched_at=datetime.now(tz=UTC).isoformat(),
        )
        with closing(connect(self._db_path)) as conn, conn:
            conn.execute(
                "INSERT INTO web_sources (id, url, title, content, query, fetched_at) VALUES (?, ?, ?, ?, ?, ?)",
                (source.id, source.url, source.title, source.content, source.query, source.fetched_at),
            )
        return source

    def list_sources(self, *, limit: int = 50) -> list[WebSource]:
        with closing(connect(self._db_path)) as conn:
            rows = conn.execute(
                "SELECT * FROM web_sources ORDER BY fetched_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [WebSource(**dict(row)) for row in rows]


class WebTools:
    """web.search / browser.read backed by a WebClient + source store."""

    def __init__(self, client: WebClient, sources: WebSourceStore) -> None:
        self._client = client
        self._sources = sources

    def search(self, query: str, limit: int = _DEFAULT_SEARCH_LIMIT) -> list[dict[str, object]]:
        try:
            results = self._client.search(query, limit)
        except (httpx.HTTPError, OSError) as exc:
            raise ToolError(f"web search failed: {exc}") from exc
        return [r.model_dump() for r in results]

    def read_url(self, url: str, query: str | None = None) -> dict[str, object]:
        try:
            title, text = self._client.fetch(url)
        except (httpx.HTTPError, OSError) as exc:
            raise ToolError(f"fetch failed: {exc}") from exc
        source = self._sources.save(url, title, text, query)
        return {"url": url, "title": title, "content": text, "source_id": source.id}
