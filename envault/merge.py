"""Merge two vault versions or .env files, with conflict detection."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


class MergeError(Exception):
    """Raised when a merge cannot be completed."""


@dataclass
class MergeConflict:
    key: str
    base_value: Optional[str]
    ours: Optional[str]
    theirs: Optional[str]

    def __str__(self) -> str:
        return (
            f"CONFLICT {self.key!r}: "
            f"base={self.base_value!r} ours={self.ours!r} theirs={self.theirs!r}"
        )


@dataclass
class MergeResult:
    merged: Dict[str, str]
    conflicts: List[MergeConflict] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return bool(self.conflicts)

    def summary(self) -> str:
        if not self.has_conflicts:
            return f"Merged cleanly ({len(self.merged)} keys)."
        lines = [f"Merged {len(self.merged)} keys with {len(self.conflicts)} conflict(s):"]
        for c in self.conflicts:
            lines.append(f"  {c}")
        return "\n".join(lines)


def _parse_env(text: str) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


def merge_envs(
    base: str,
    ours: str,
    theirs: str,
    strategy: str = "ours",
) -> MergeResult:
    """Three-way merge of env files represented as raw text.

    strategy: 'ours' | 'theirs' — which side wins on conflict.
    """
    if strategy not in ("ours", "theirs"):
        raise MergeError(f"Unknown strategy {strategy!r}. Use 'ours' or 'theirs'.")

    base_map = _parse_env(base)
    ours_map = _parse_env(ours)
    theirs_map = _parse_env(theirs)

    all_keys = set(base_map) | set(ours_map) | set(theirs_map)
    merged: Dict[str, str] = {}
    conflicts: List[MergeConflict] = []

    for key in sorted(all_keys):
        b = base_map.get(key)
        o = ours_map.get(key)
        t = theirs_map.get(key)

        ours_changed = o != b
        theirs_changed = t != b

        if not ours_changed and not theirs_changed:
            if b is not None:
                merged[key] = b
        elif ours_changed and not theirs_changed:
            if o is not None:
                merged[key] = o
        elif theirs_changed and not ours_changed:
            if t is not None:
                merged[key] = t
        else:
            # Both sides changed — conflict
            conflicts.append(MergeConflict(key=key, base_value=b, ours=o, theirs=t))
            winner = o if strategy == "ours" else t
            if winner is not None:
                merged[key] = winner

    return MergeResult(merged=merged, conflicts=conflicts)
