"""Snapshot management: capture and restore named snapshots of vault state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

SNAPSHOT_DIR = ".envault/snapshots"


class SnapshotError(Exception):
    pass


def _snapshots_path(vault_name: str) -> Path:
    return Path(SNAPSHOT_DIR) / f"{vault_name}.json"


def _load_snapshots(vault_name: str) -> Dict[str, dict]:
    path = _snapshots_path(vault_name)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_snapshots(vault_name: str, data: Dict[str, dict]) -> None:
    path = _snapshots_path(vault_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def save_snapshot(vault_name: str, label: str, version: int, note: str = "") -> None:
    """Associate a named label with a vault version number."""
    snapshots = _load_snapshots(vault_name)
    if label in snapshots:
        raise SnapshotError(f"Snapshot '{label}' already exists for vault '{vault_name}'.")
    snapshots[label] = {"version": version, "note": note}
    _save_snapshots(vault_name, snapshots)


def get_snapshot(vault_name: str, label: str) -> Optional[dict]:
    """Return snapshot metadata or None if not found."""
    return _load_snapshots(vault_name).get(label)


def delete_snapshot(vault_name: str, label: str) -> bool:
    """Delete a snapshot by label. Returns True if deleted, False if not found."""
    snapshots = _load_snapshots(vault_name)
    if label not in snapshots:
        return False
    del snapshots[label]
    _save_snapshots(vault_name, snapshots)
    return True


def list_snapshots(vault_name: str) -> List[dict]:
    """Return all snapshots for a vault as a list of dicts with 'label' key."""
    snapshots = _load_snapshots(vault_name)
    return [
        {"label": label, **meta}
        for label, meta in sorted(snapshots.items())
    ]
