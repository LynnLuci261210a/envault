"""Tests for envault.gc (garbage collection of old vault versions)."""

from __future__ import annotations

import pytest

from envault.gc import GCError, GCResult, collect
from envault.history import _history_path, _save_raw
from envault.pin import _pins_path, _save_pins
from envault.snapshot import _snapshots_path, _save_snapshots


@pytest.fixture()
def tmp_vault(tmp_path, monkeypatch):
    """Redirect all storage paths to tmp_path."""
    monkeypatch.setattr("envault.history.VAULT_DIR", tmp_path)
    monkeypatch.setattr("envault.gc._history_path", lambda name: tmp_path / f"{name}.history.json")
    monkeypatch.setattr("envault.gc._load_raw", lambda name: _load_raw_local(tmp_path, name))
    monkeypatch.setattr("envault.gc._save_raw", lambda name, data: _save_raw_local(tmp_path, name, data))
    monkeypatch.setattr("envault.gc._load_pins", lambda name: _load_pins_local(tmp_path, name))
    monkeypatch.setattr("envault.gc._load_snapshots", lambda name: _load_snaps_local(tmp_path, name))
    return tmp_path


# ---------------------------------------------------------------------------
# Tiny local helpers so tests don't need real vault infrastructure
# ---------------------------------------------------------------------------
import json


def _hist_file(base, name):
    return base / f"{name}.history.json"


def _load_raw_local(base, name):
    p = _hist_file(base, name)
    if not p.exists():
        raise FileNotFoundError(name)
    return json.loads(p.read_text())


def _save_raw_local(base, name, data):
    _hist_file(base, name).write_text(json.dumps(data))


def _make_versions(base, name, count):
    versions = [
        {"version": i + 1, "ciphertext": "A" * 100, "timestamp": f"2024-01-{i+1:02d}"}
        for i in range(count)
    ]
    _save_raw_local(base, name, {"versions": versions})


def _load_pins_local(base, name):
    p = base / f"{name}.pins.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _load_snaps_local(base, name):
    p = base / f"{name}.snapshots.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text())


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_collect_removes_old_versions(tmp_vault):
    _make_versions(tmp_vault, "myenv", 10)
    result = collect("myenv", keep=5)
    assert isinstance(result, GCResult)
    assert len(result.versions_removed) == 5
    assert result.versions_kept == 5
    # Oldest versions (1-5) should be removed
    assert result.versions_removed == [1, 2, 3, 4, 5]


def test_collect_keeps_minimum_versions(tmp_vault):
    _make_versions(tmp_vault, "myenv", 3)
    result = collect("myenv", keep=5)
    assert result.versions_removed == []
    assert result.versions_kept == 3


def test_collect_no_history_raises(tmp_vault):
    with pytest.raises(GCError, match="No history found"):
        collect("nonexistent", keep=3)


def test_collect_keep_less_than_one_raises(tmp_vault):
    _make_versions(tmp_vault, "myenv", 5)
    with pytest.raises(GCError, match="keep must be at least 1"):
        collect("myenv", keep=0)


def test_collect_protects_pinned_versions(tmp_vault):
    _make_versions(tmp_vault, "myenv", 8)
    # Pin version 2 (which would otherwise be collected)
    (tmp_vault / "myenv.pins.json").write_text(json.dumps({"stable": 2}))
    result = collect("myenv", keep=3)
    # Versions 8, 7, 6 kept by recency; version 2 kept by pin
    assert 2 not in result.versions_removed
    assert result.versions_kept == 4


def test_collect_protects_snapshot_versions(tmp_vault):
    _make_versions(tmp_vault, "myenv", 8)
    snaps = {"release-1.0": {"version": 1, "note": "first release"}}
    (tmp_vault / "myenv.snapshots.json").write_text(json.dumps(snaps))
    result = collect("myenv", keep=3)
    assert 1 not in result.versions_removed


def test_collect_empty_history_returns_zero(tmp_vault):
    _save_raw_local(tmp_vault, "myenv", {"versions": []})
    result = collect("myenv", keep=5)
    assert result.versions_removed == []
    assert result.versions_kept == 0
    assert result.bytes_freed == 0


def test_gc_result_summary_nothing(tmp_vault):
    _save_raw_local(tmp_vault, "myenv", {"versions": []})
    result = collect("myenv", keep=5)
    assert "Nothing to collect" in result.summary()


def test_gc_result_summary_with_removals(tmp_vault):
    _make_versions(tmp_vault, "myenv", 7)
    result = collect("myenv", keep=5)
    summary = result.summary()
    assert "Removed" in summary
    assert "freed" in summary
    assert "myenv" in summary
