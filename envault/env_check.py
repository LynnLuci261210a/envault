"""env_check.py — validate that a decrypted vault contains all required keys.

Usage:
    from envault.env_check import check_required, CheckResult, CheckError
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class CheckError(Exception):
    """Raised when the required-keys spec cannot be loaded."""


@dataclass
class CheckResult:
    missing: List[str] = field(default_factory=list)
    present: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.missing) == 0

    def summary(self) -> str:
        lines: List[str] = []
        if self.present:
            lines.append(f"  present ({len(self.present)}): {', '.join(sorted(self.present))}")
        if self.missing:
            lines.append(f"  missing ({len(self.missing)}): {', '.join(sorted(self.missing))}")
        status = "OK" if self.ok else "FAIL"
        return f"[{status}]\n" + "\n".join(lines)


def _parse_env_pairs(text: str) -> Dict[str, str]:
    """Parse KEY=VALUE lines, ignoring comments and blanks."""
    pairs: Dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        pairs[key.strip()] = value
    return pairs


def check_required(
    env_text: str,
    required: List[str],
    *,
    allow_empty: bool = False,
) -> CheckResult:
    """Check that *required* keys exist (and optionally are non-empty) in *env_text*.

    Args:
        env_text:    Decrypted .env file contents.
        required:    List of key names that must be present.
        allow_empty: When False (default) a key present with an empty value
                     is treated as missing.

    Returns:
        CheckResult with .ok, .missing, and .present populated.
    """
    pairs = _parse_env_pairs(env_text)
    result = CheckResult()
    for key in required:
        value: Optional[str] = pairs.get(key)
        if value is None or (not allow_empty and value.strip() == ""):
            result.missing.append(key)
        else:
            result.present.append(key)
    return result
