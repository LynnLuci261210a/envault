"""Version history tracking for vault entries."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

HISTORY_DIR = Path(".envault") / "history"


def _history_path(name: str) -> Path:
    return HISTORY_DIR / f"{name}.history.json"


def _load_raw(name: str) -> List[Dict[str, Any]]:
    path = _history_path(name)
    if not path.exists():
        return []
    with path.open("r") as f:
        return json.load(f)


def _save_raw(name: str, entries: List[Dict[str, Any]]) -> None:
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    path = _history_path(name)
    with path.open("w") as f:
        json.dump(entries, f, indent=2)


def record_version(name: str, ciphertext_hex: str, note: str = "") -> int:
    """Append a new version entry. Returns the new version number."""
    entries = _load_raw(name)
    version = len(entries) + 1
    entries.append({
        "version": version,
        "timestamp": time.time(),
        "ciphertext": ciphertext_hex,
        "note": note,
    })
    _save_raw(name, entries)
    return version


def list_versions(name: str) -> List[Dict[str, Any]]:
    """Return all version metadata (without ciphertext) for a vault."""
    entries = _load_raw(name)
    return [
        {
            "version": e["version"],
            "timestamp": e["timestamp"],
            "note": e.get("note", ""),
        }
        for e in entries
    ]


def get_version(name: str, version: int) -> Optional[str]:
    """Return the ciphertext hex for a specific version, or None."""
    entries = _load_raw(name)
    for entry in entries:
        if entry["version"] == version:
            return entry["ciphertext"]
    return None


def latest_version(name: str) -> Optional[Dict[str, Any]]:
    """Return the most recent history entry, or None if no history."""
    entries = _load_raw(name)
    return entries[-1] if entries else None


def delete_history(name: str) -> bool:
    """Delete all history for a vault. Returns True if anything was deleted."""
    path = _history_path(name)
    if path.exists():
        path.unlink()
        return True
    return False
