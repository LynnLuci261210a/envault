"""Lint .env files for common issues and best practices."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


WEAK_PATTERNS = [
    re.compile(r'^(password|secret|key|token|api_key)\s*=\s*.{0,7}$', re.IGNORECASE),
]

DUPLICATE_KEY_MSG = "Duplicate key '{}' (first seen on line {})"
EMPTY_VALUE_MSG = "Key '{}' has an empty value"
WEAK_SECRET_MSG = "Key '{}' looks like a secret but has a short/weak value"
UNQUOTED_SPACE_MSG = "Value for '{}' contains spaces but is not quoted"
INVALID_KEY_MSG = "Key '{}' contains invalid characters (use A-Z, 0-9, _)"


@dataclass
class LintIssue:
    line: int
    key: str
    message: str
    severity: str = "warning"  # "warning" | "error"

    def __str__(self) -> str:
        return f"Line {self.line} [{self.severity.upper()}] {self.message}"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")


VALID_KEY_RE = re.compile(r'^[A-Z_][A-Z0-9_]*$', re.IGNORECASE)


def lint_env(content: str) -> LintResult:
    """Lint the given .env file content and return a LintResult."""
    result = LintResult()
    seen_keys: dict[str, int] = {}

    for lineno, raw_line in enumerate(content.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue

        if '=' not in line:
            result.issues.append(LintIssue(lineno, '', f"Line {lineno} is not a valid KEY=VALUE pair", "error"))
            continue

        key, _, value = line.partition('=')
        key = key.strip()
        value = value.strip()

        if not VALID_KEY_RE.match(key):
            result.issues.append(LintIssue(lineno, key, INVALID_KEY_MSG.format(key), "error"))

        if key in seen_keys:
            result.issues.append(LintIssue(lineno, key, DUPLICATE_KEY_MSG.format(key, seen_keys[key]), "error"))
        else:
            seen_keys[key] = lineno

        if value == '':
            result.issues.append(LintIssue(lineno, key, EMPTY_VALUE_MSG.format(key), "warning"))
            continue

        unquoted = value
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            unquoted = value[1:-1]
        elif ' ' in value:
            result.issues.append(LintIssue(lineno, key, UNQUOTED_SPACE_MSG.format(key), "warning"))

        for pat in WEAK_PATTERNS:
            if pat.match(f"{key}={unquoted}"):
                result.issues.append(LintIssue(lineno, key, WEAK_SECRET_MSG.format(key), "warning"))
                break

    return result


def lint_file(path: Path) -> LintResult:
    """Lint a .env file on disk."""
    return lint_env(path.read_text())
