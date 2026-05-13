"""Garbage collection for old vault versions and orphaned data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import NamedTuple

from envault.history import _history_path, _load_raw, _save_raw
from envault.snapshot import _snapshots_path, _load_snapshots
from envault.pin import _pins_path, _load_pins
from envault.vault import _vault_path


class GCError(Exception):
    pass


class GCResult(NamedTuple):
    vault_name: str
    versions_removed: list[int]
    versions_kept: int
    bytes_freed: int

    def summary(self) -> str:
        if not self.versions_removed:
            return f"[{self.vault_name}] Nothing to collect."
        removed = ", ".join(f"v{v}" for v in self.versions_removed)
        return (
            f"[{self.vault_name}] Removed {len(self.versions_removed)} version(s) "
            f"({removed}), freed {self.bytes_freed} bytes. "
            f"{self.versions_kept} version(s) retained."
        )


def _pinned_versions(vault_name: str) -> set[int]:
    """Return set of version numbers that are pinned or snapshotted."""
    pinned: set[int] = set()
    try:
        pins = _load_pins(vault_name)
        pinned.update(pins.values())
    except Exception:
        pass
    try:
        snapshots = _load_snapshots(vault_name)
        for entry in snapshots.values():
            if isinstance(entry, dict) and "version" in entry:
                pinned.add(int(entry["version"]))
    except Exception:
        pass
    return pinned


def collect(vault_name: str, keep: int = 5) -> GCResult:
    """Remove old vault versions, keeping the most recent *keep* versions
    plus any that are pinned or referenced by a snapshot.

    Args:
        vault_name: Name of the vault to collect.
        keep: Minimum number of recent versions to retain (default 5).

    Returns:
        GCResult describing what was removed.

    Raises:
        GCError: If keep < 1 or the history cannot be loaded.
    """
    if keep < 1:
        raise GCError("keep must be at least 1")

    try:
        raw = _load_raw(vault_name)
    except FileNotFoundError:
        raise GCError(f"No history found for vault '{vault_name}'")

    versions: list[dict] = raw.get("versions", [])
    if not versions:
        return GCResult(vault_name, [], 0, 0)

    protected = _pinned_versions(vault_name)

    # Sort descending by version number
    versions_sorted = sorted(versions, key=lambda v: v["version"], reverse=True)
    keep_set: set[int] = {v["version"] for v in versions_sorted[:keep]}
    keep_set |= protected

    removed_versions: list[int] = []
    bytes_freed = 0
    surviving: list[dict] = []

    for entry in versions:
        vnum = entry["version"]
        if vnum in keep_set:
            surviving.append(entry)
        else:
            # Estimate size from stored ciphertext if present
            ct = entry.get("ciphertext", "")
            bytes_freed += len(ct.encode()) if isinstance(ct, str) else 0
            removed_versions.append(vnum)

    raw["versions"] = surviving
    _save_raw(vault_name, raw)

    removed_versions.sort()
    return GCResult(
        vault_name=vault_name,
        versions_removed=removed_versions,
        versions_kept=len(surviving),
        bytes_freed=bytes_freed,
    )
