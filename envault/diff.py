"""Diff utilities for comparing vault versions and .env files."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class DiffResult:
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    changed: List[str] = field(default_factory=list)
    unchanged: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        parts = []
        if self.added:
            parts.append(f"+{len(self.added)} added")
        if self.removed:
            parts.append(f"-{len(self.removed)} removed")
        if self.changed:
            parts.append(f"~{len(self.changed)} changed")
        if not parts:
            return "No changes"
        return ", ".join(parts)


def parse_env(content: str) -> Dict[str, str]:
    """Parse .env file content into a key-value dict, ignoring comments."""
    result: Dict[str, str] = {}
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


def diff_envs(old: str, new: str) -> DiffResult:
    """Compare two .env file contents and return a DiffResult."""
    old_vars = parse_env(old)
    new_vars = parse_env(new)

    result = DiffResult()
    all_keys = set(old_vars) | set(new_vars)

    for key in sorted(all_keys):
        if key not in old_vars:
            result.added.append(key)
        elif key not in new_vars:
            result.removed.append(key)
        elif old_vars[key] != new_vars[key]:
            result.changed.append(key)
        else:
            result.unchanged.append(key)

    return result


def format_diff(diff: DiffResult, show_values: bool = False,
                old: str = "", new: str = "") -> str:
    """Format a DiffResult as a human-readable string."""
    lines: List[str] = []
    old_vars = parse_env(old) if old else {}
    new_vars = parse_env(new) if new else {}

    for key in diff.added:
        val = f"={new_vars[key]}" if show_values and key in new_vars else ""
        lines.append(f"  + {key}{val}")
    for key in diff.removed:
        val = f"={old_vars[key]}" if show_values and key in old_vars else ""
        lines.append(f"  - {key}{val}")
    for key in diff.changed:
        if show_values and key in old_vars and key in new_vars:
            lines.append(f"  ~ {key}: {old_vars[key]} -> {new_vars[key]}")
        else:
            lines.append(f"  ~ {key}")

    return "\n".join(lines) if lines else "  (no changes)"
