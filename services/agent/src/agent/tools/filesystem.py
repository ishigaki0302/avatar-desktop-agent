"""Safe, read-only filesystem tools (Phase 17).

Only list/read within an allowed root. No write/delete/exec. Path traversal
outside the root and access to credential-ish files are denied.
"""

from __future__ import annotations

import fnmatch
import os
from pathlib import Path

from agent.tools.base import ToolError

# Substrings that mark a path as sensitive — reading/listing these is refused.
_DENY_SUBSTRINGS = (
    ".env",
    ".key",
    ".pem",
    ".pfx",
    ".p12",
    "id_rsa",
    "id_ed25519",
    ".ssh",
    "credential",
    ".secret",
    ".npmrc",
    ".git/",
    ".aws",
)
_MAX_READ_BYTES = 1_000_000
# Directory names pruned during recursive search (noise / heavy / sensitive).
_SKIP_DIRS = frozenset({"node_modules", "__pycache__", ".venv", "venv", "Library", ".Trash", "dist", "build"})
_SEARCH_MAX_RESULTS = 50
_SEARCH_MAX_SCAN = 20_000


class FilesystemTools:
    """Read-only filesystem access scoped to a root directory."""

    def __init__(self, root: Path) -> None:
        self._root = Path(root).expanduser().resolve()

    def _resolve(self, rel_path: str) -> Path:
        target = (self._root / rel_path).resolve()
        if target != self._root and self._root not in target.parents:
            raise ToolError("path escapes the allowed root")
        if any(token in str(target).lower() for token in _DENY_SUBSTRINGS):
            raise ToolError("access to a sensitive path is denied")
        return target

    def list_dir(self, path: str = ".") -> list[dict[str, object]]:
        target = self._resolve(path)
        if not target.is_dir():
            raise ToolError("not a directory")
        entries: list[dict[str, object]] = []
        for entry in sorted(target.iterdir(), key=lambda p: p.name):
            is_file = entry.is_file()
            entries.append(
                {
                    "name": entry.name,
                    "type": "file" if is_file else "dir",
                    "size": entry.stat().st_size if is_file else None,
                },
            )
        return entries

    def read_file(self, path: str) -> dict[str, object]:
        target = self._resolve(path)
        if not target.is_file():
            raise ToolError("not a file")
        size = target.stat().st_size
        if size > _MAX_READ_BYTES:
            raise ToolError(f"file too large ({size} bytes, limit {_MAX_READ_BYTES})")
        return {"path": path, "content": target.read_text(encoding="utf-8", errors="replace")}

    def search(self, pattern: str, path: str = ".") -> list[dict[str, object]]:
        """Recursively find files matching a glob `pattern` (e.g. '*.pptx') under the root.

        Prunes hidden / heavy dirs, skips sensitive files, and is capped in results
        and files scanned so a large home directory stays responsive.
        """
        base = self._resolve(path)
        if not base.is_dir():
            raise ToolError("not a directory")
        needle = pattern.lower()
        results: list[dict[str, object]] = []
        scanned = 0
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in _SKIP_DIRS]
            for name in filenames:
                scanned += 1
                if scanned > _SEARCH_MAX_SCAN:
                    return results
                if not fnmatch.fnmatch(name.lower(), needle):
                    continue
                full = Path(dirpath) / name
                if any(token in str(full).lower() for token in _DENY_SUBSTRINGS):
                    continue
                results.append({"path": str(full.relative_to(self._root)), "size": full.stat().st_size})
                if len(results) >= _SEARCH_MAX_RESULTS:
                    return results
        return results
