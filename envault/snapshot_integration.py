"""High-level helpers that integrate snapshots with history and vault restore."""

from __future__ import annotations

from envault.history import get_version, list_versions
from envault.snapshot import SnapshotError, get_snapshot, save_snapshot


def snapshot_current(vault_name: str, label: str, note: str = "") -> int:
    """Snapshot the latest recorded version of vault_name under label.

    Returns the version number that was snapshotted.
    Raises SnapshotError if no history exists or label already taken.
    """
    versions = list_versions(vault_name)
    if not versions:
        raise SnapshotError(f"No history found for vault '{vault_name}'.")
    latest = versions[-1]["version"]
    save_snapshot(vault_name, label, latest, note=note)
    return latest


def resolve_snapshot_version(vault_name: str, label: str) -> int:
    """Return the version number for a snapshot label.

    Raises SnapshotError if the snapshot does not exist.
    """
    entry = get_snapshot(vault_name, label)
    if entry is None:
        raise SnapshotError(f"Snapshot '{label}' not found for vault '{vault_name}'.")
    return entry["version"]


def snapshot_exists(vault_name: str, label: str) -> bool:
    """Return True if a snapshot with the given label exists."""
    return get_snapshot(vault_name, label) is not None


def get_snapshot_summary(vault_name: str, label: str) -> str:
    """Return a human-readable summary line for a snapshot."""
    entry = get_snapshot(vault_name, label)
    if entry is None:
        return f"[{vault_name}] '{label}': not found"
    note_part = f" — {entry['note']}" if entry.get("note") else ""
    return f"[{vault_name}] '{label}': version {entry['version']}{note_part}"
