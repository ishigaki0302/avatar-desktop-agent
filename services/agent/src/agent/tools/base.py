"""Shared tool types (Phase 17)."""

from __future__ import annotations

from pydantic import BaseModel


class ToolError(Exception):
    """Raised when a tool refuses or fails to run (validation, safety, IO)."""


class ToolSpec(BaseModel):
    """Public description of a tool for listing / LLM tool selection."""

    name: str
    description: str
    args_schema: dict[str, object]


class ToolResult(BaseModel):
    """Outcome of a tool invocation."""

    ok: bool
    output: object | None = None
    error: str | None = None
