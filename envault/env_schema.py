"""Schema validation for .env files against a declared schema."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


class SchemaError(Exception):
    """Raised when schema operations fail."""


@dataclass
class SchemaIssue:
    key: str
    message: str

    def __str__(self) -> str:
        return f"{self.key}: {self.message}"


@dataclass
class SchemaResult:
    issues: List[SchemaIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.issues) == 0

    def summary(self) -> str:
        if self.ok:
            return "Schema validation passed."
        lines = [f"Schema validation failed ({len(self.issues)} issue(s)):"]
        for issue in self.issues:
            lines.append(f"  - {issue}")
        return "\n".join(lines)


def _schema_path(vault_name: str) -> Path:
    return Path(".envault") / vault_name / "schema.json"


def load_schema(vault_name: str) -> Dict:
    path = _schema_path(vault_name)
    if not path.exists():
        raise SchemaError(f"No schema found for vault '{vault_name}'")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise SchemaError(f"Invalid schema JSON: {exc}") from exc


def save_schema(vault_name: str, schema: Dict) -> Path:
    path = _schema_path(vault_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(schema, indent=2))
    return path


def validate_env(env: Dict[str, str], schema: Dict) -> SchemaResult:
    """Validate env key/value pairs against a schema dict.

    Schema format::

        {
          "KEY": {"required": true, "type": "string", "pattern": "^[A-Z]+$"},
          ...
        }
    """
    import re

    issues: List[SchemaIssue] = []
    for key, rules in schema.items():
        required = rules.get("required", False)
        if key not in env:
            if required:
                issues.append(SchemaIssue(key, "required key is missing"))
            continue
        value = env[key]
        expected_type = rules.get("type")
        if expected_type == "int":
            try:
                int(value)
            except ValueError:
                issues.append(SchemaIssue(key, f"expected integer, got {value!r}"))
        pattern = rules.get("pattern")
        if pattern and not re.fullmatch(pattern, value):
            issues.append(SchemaIssue(key, f"value {value!r} does not match pattern {pattern!r}"))
        allowed = rules.get("allowed")
        if allowed is not None and value not in allowed:
            issues.append(SchemaIssue(key, f"value {value!r} not in allowed set {allowed}"))
    return SchemaResult(issues=issues)
