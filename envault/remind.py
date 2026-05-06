"""Rotation reminders: track when a vault was last rotated and warn if overdue."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

REMINDER_FILE = ".envault_remind.json"
DEFAULT_MAX_AGE_DAYS = 30


def _remind_path(vault_dir: str = ".") -> Path:
    return Path(vault_dir) / REMINDER_FILE


def _load(vault_dir: str = ".") -> dict:
    p = _remind_path(vault_dir)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save(data: dict, vault_dir: str = ".") -> None:
    _remind_path(vault_dir).write_text(json.dumps(data, indent=2))


def record_rotation(vault_name: str, vault_dir: str = ".") -> str:
    """Record the current UTC timestamp as the last rotation time for *vault_name*.
    Returns the ISO-formatted timestamp string."""
    data = _load(vault_dir)
    ts = datetime.now(timezone.utc).isoformat()
    data[vault_name] = {"last_rotated": ts}
    _save(data, vault_dir)
    return ts


def get_last_rotation(vault_name: str, vault_dir: str = ".") -> Optional[datetime]:
    """Return the last rotation datetime for *vault_name*, or None if never recorded."""
    data = _load(vault_dir)
    entry = data.get(vault_name)
    if not entry:
        return None
    return datetime.fromisoformat(entry["last_rotated"])


def is_overdue(vault_name: str, max_age_days: int = DEFAULT_MAX_AGE_DAYS,
               vault_dir: str = ".") -> bool:
    """Return True if the vault has never been rotated or was rotated more than
    *max_age_days* days ago."""
    last = get_last_rotation(vault_name, vault_dir)
    if last is None:
        return True
    age = datetime.now(timezone.utc) - last
    return age.days >= max_age_days


def days_since_rotation(vault_name: str, vault_dir: str = ".") -> Optional[int]:
    """Return the number of whole days since the last rotation, or None."""
    last = get_last_rotation(vault_name, vault_dir)
    if last is None:
        return None
    return (datetime.now(timezone.utc) - last).days
