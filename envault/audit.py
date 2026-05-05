"""Audit log for envault — records lock/unlock/init operations with timestamps."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

_AUDIT_FILENAME = ".envault_audit.json"


def _audit_path(directory: str = ".") -> Path:
    return Path(directory) / _AUDIT_FILENAME


def _load_entries(directory: str = ".") -> List[Dict[str, Any]]:
    path = _audit_path(directory)
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data.get("entries", [])


def _save_entries(entries: List[Dict[str, Any]], directory: str = ".") -> None:
    path = _audit_path(directory)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"entries": entries}, fh, indent=2)


def record_event(
    action: str,
    env_name: str,
    version: int | None = None,
    user: str | None = None,
    directory: str = ".",
) -> Dict[str, Any]:
    """Append an audit event and return the recorded entry."""
    entries = _load_entries(directory)
    entry: Dict[str, Any] = {
        "action": action,
        "env_name": env_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user": user or os.environ.get("USER", "unknown"),
    }
    if version is not None:
        entry["version"] = version
    entries.append(entry)
    _save_entries(entries, directory)
    return entry


def get_events(
    directory: str = ".",
    env_name: str | None = None,
    action: str | None = None,
) -> List[Dict[str, Any]]:
    """Return audit entries, optionally filtered by env_name and/or action."""
    entries = _load_entries(directory)
    if env_name is not None:
        entries = [e for e in entries if e.get("env_name") == env_name]
    if action is not None:
        entries = [e for e in entries if e.get("action") == action]
    return entries


def clear_events(directory: str = ".") -> None:
    """Remove all audit log entries (useful for testing)."""
    _save_entries([], directory)
