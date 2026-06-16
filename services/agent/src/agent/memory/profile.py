"""Profile memory (Phase 12).

The profile is a single Markdown document representing the user's *current*
state (呼び名・口調・研究テーマ・禁止事項 等). Unlike episodic memory it is
overwritten in place: it always reflects the latest truth.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class ProfileStore:
    """Read/write access to the profile Markdown document."""

    def __init__(self, profile_path: Path) -> None:
        self._path = profile_path

    def read(self) -> str:
        """Return the profile text, or an empty string if it does not exist yet."""
        if not self._path.exists():
            return ""
        return self._path.read_text(encoding="utf-8")

    def write(self, content: str) -> None:
        """Overwrite the profile document (current truth)."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(content, encoding="utf-8")
