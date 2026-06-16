"""Tool registry: schema listing, arg validation, safe dispatch (Phase 17)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ValidationError

from agent.memory.store import MemoryType  # noqa: TC001  (pydantic field type, resolved at runtime)
from agent.tools.base import ToolError, ToolResult, ToolSpec
from agent.tools.filesystem import FilesystemTools
from agent.tools.memory_tools import MemoryTools

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from agent.memory.store import MemoryStore

_DEFAULT_SEARCH_LIMIT = 10
_DEFAULT_IMPORTANCE = 3


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


class _RegisteredTool:
    def __init__(
        self,
        name: str,
        description: str,
        args_model: type[BaseModel],
        handler: Callable[[BaseModel], object],
    ) -> None:
        self.name = name
        self.description = description
        self.args_model = args_model
        self.handler = handler


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
    ) -> None:
        self._tools[name] = _RegisteredTool(name, description, args_model, handler)

    def specs(self) -> list[ToolSpec]:
        return [
            ToolSpec(name=t.name, description=t.description, args_schema=t.args_model.model_json_schema())
            for t in self._tools.values()
        ]

    def names(self) -> list[str]:
        return list(self._tools)

    def run(self, name: str, raw_args: dict[str, object]) -> ToolResult:
        tool = self._tools.get(name)
        if tool is None:
            return ToolResult(ok=False, error=f"unknown tool: {name}")
        try:
            args = tool.args_model.model_validate(raw_args)
        except ValidationError as exc:
            return ToolResult(ok=False, error=f"invalid args: {exc.errors()}")
        try:
            output = tool.handler(args)
        except (ToolError, OSError) as exc:
            return ToolResult(ok=False, error=str(exc))
        return ToolResult(ok=True, output=output)


def build_default_registry(fs_root: Path, store: MemoryStore) -> ToolRegistry:
    """Register the Phase 17 toolset: read-only filesystem + memory search/write."""
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
    return registry
