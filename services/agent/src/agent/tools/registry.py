"""Tool registry: schema listing, arg validation, safe dispatch (Phase 17-18)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ValidationError

from agent.memory.store import MemoryType  # noqa: TC001  (pydantic field type, resolved at runtime)
from agent.tools.base import ToolError, ToolResult, ToolSpec
from agent.tools.filesystem import FilesystemTools
from agent.tools.memory_tools import MemoryTools
from agent.tools.weather import get_weather
from agent.tools.web import WebTools

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from agent.memory.store import MemoryStore
    from agent.tools.web import WebClient, WebSourceStore

_DEFAULT_SEARCH_LIMIT = 10
_DEFAULT_IMPORTANCE = 3
_DEFAULT_WEB_SEARCH_LIMIT = 5


class FilesystemListArgs(BaseModel):
    path: str = "."


class FilesystemReadArgs(BaseModel):
    path: str


class MemorySearchArgs(BaseModel):
    query: str
    memory_type: MemoryType | None = None
    limit: int = _DEFAULT_SEARCH_LIMIT


class MemoryWriteArgs(BaseModel):
    content: str
    memory_type: MemoryType = "semantic"
    importance: int = _DEFAULT_IMPORTANCE


class WebSearchArgs(BaseModel):
    query: str
    limit: int = _DEFAULT_WEB_SEARCH_LIMIT


class BrowserReadArgs(BaseModel):
    url: str
    query: str | None = None


class WeatherArgs(BaseModel):
    location: str = ""


class _RegisteredTool:
    def __init__(
        self,
        name: str,
        description: str,
        args_model: type[BaseModel],
        handler: Callable[[BaseModel], object],
        *,
        requires_confirmation: bool = False,
    ) -> None:
        self.name = name
        self.description = description
        self.args_model = args_model
        self.handler = handler
        self.requires_confirmation = requires_confirmation


class ToolRegistry:
    """Holds named tools and runs them with validation + error isolation."""

    def __init__(self) -> None:
        self._tools: dict[str, _RegisteredTool] = {}

    def register(
        self,
        name: str,
        description: str,
        args_model: type[BaseModel],
        handler: Callable[[BaseModel], object],
        *,
        requires_confirmation: bool = False,
    ) -> None:
        self._tools[name] = _RegisteredTool(
            name,
            description,
            args_model,
            handler,
            requires_confirmation=requires_confirmation,
        )

    def specs(self) -> list[ToolSpec]:
        return [
            ToolSpec(
                name=t.name,
                description=t.description,
                args_schema=t.args_model.model_json_schema(),
                requires_confirmation=t.requires_confirmation,
            )
            for t in self._tools.values()
        ]

    def names(self) -> list[str]:
        return list(self._tools)

    def run(self, name: str, raw_args: dict[str, object], *, confirm: bool = False) -> ToolResult:
        tool = self._tools.get(name)
        if tool is None:
            return ToolResult(ok=False, error=f"unknown tool: {name}")
        if tool.requires_confirmation and not confirm:
            return ToolResult(ok=False, error="confirmation required for external action")
        try:
            args = tool.args_model.model_validate(raw_args)
        except ValidationError as exc:
            return ToolResult(ok=False, error=f"invalid args: {exc.errors()}")
        try:
            output = tool.handler(args)
        except (ToolError, OSError) as exc:
            return ToolResult(ok=False, error=str(exc))
        return ToolResult(ok=True, output=output)


def build_default_registry(
    fs_root: Path,
    store: MemoryStore,
    web_client: WebClient | None = None,
    web_sources: WebSourceStore | None = None,
) -> ToolRegistry:
    """Register filesystem + memory tools, and (if provided) web tools (Phase 18)."""
    fs = FilesystemTools(fs_root)
    mem = MemoryTools(store)
    registry = ToolRegistry()
    registry.register(
        "filesystem.list",
        "指定パス(許可ルート内)のファイルとディレクトリ一覧を返す",
        FilesystemListArgs,
        lambda a: fs.list_dir(a.path),
    )
    registry.register(
        "filesystem.read",
        "指定ファイル(許可ルート内、機微ファイルは除外)の内容を返す",
        FilesystemReadArgs,
        lambda a: fs.read_file(a.path),
    )
    registry.register(
        "memory.search",
        "長期記憶をキーワード検索する",
        MemorySearchArgs,
        lambda a: mem.search(a.query, a.memory_type, a.limit),
    )
    registry.register(
        "memory.write",
        "長期記憶に新しい項目を保存する",
        MemoryWriteArgs,
        lambda a: mem.write(a.content, a.memory_type, a.importance),
    )
    registry.register(
        "weather",
        "現在の天気・気温を返す(location は都市名、空なら現在地)。外部送信のため確認が必要。",
        WeatherArgs,
        lambda a: get_weather(a.location),
        requires_confirmation=True,
    )
    if web_client is not None and web_sources is not None:
        web = WebTools(web_client, web_sources)
        registry.register(
            "web.search",
            "Web 検索を行い結果(タイトル/URL)を返す。外部送信のため確認が必要。",
            WebSearchArgs,
            lambda a: web.search(a.query, a.limit),
            requires_confirmation=True,
        )
        registry.register(
            "browser.read",
            "URL を取得し本文抽出して参照元として保存する。外部送信のため確認が必要。",
            BrowserReadArgs,
            lambda a: web.read_url(a.url, a.query),
            requires_confirmation=True,
        )
    return registry
