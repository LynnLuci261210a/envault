"""Tests for envault.snapshot module."""

from __future__ import annotations

import pytest

from envault.snapshot import SnapshotError, delete_snapshot, get_snapshot, list_snapshots, save_snapshot


@pytest.fixture(autouse=True)
def tmp_snapshot(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    yield tmp_path


def test_save_snapshot_creates_entry():
    save_snapshot("myapp", "v1.0", 3)
    entry = get_snapshot("myapp", "v1.0")
    assert entry is not None
    assert entry["version"] == 3


def test_save_snapshot_stores_note():
    save_snapshot("myapp", "release", 5, note="production release")
    entry = get_snapshot("myapp", "release")
    assert entry["note"] == "production release"


def test_save_snapshot_duplicate_raises():
    save_snapshot("myapp", "v1.0", 1)
    with pytest.raises(SnapshotError, match="already exists"):
        save_snapshot("myapp", "v1.0", 2)


def test_get_snapshot_missing_returns_none():
    result = get_snapshot("myapp", "nonexistent")
    assert result is None


def test_delete_snapshot_removes_entry():
    save_snapshot("myapp", "beta", 2)
    removed = delete_snapshot("myapp", "beta")
    assert removed is True
    assert get_snapshot("myapp", "beta") is None


def test_delete_snapshot_missing_returns_false():
    result = delete_snapshot("myapp", "ghost")
    assert result is False


def test_list_snapshots_empty():
    entries = list_snapshots("myapp")
    assert entries == []


def test_list_snapshots_returns_all():
    save_snapshot("myapp", "alpha", 1)
    save_snapshot("myapp", "beta", 2, note="second")
    entries = list_snapshots("myapp")
    labels = [e["label"] for e in entries]
    assert "alpha" in labels
    assert "beta" in labels
    assert len(entries) == 2


def test_list_snapshots_sorted_by_label():
    save_snapshot("myapp", "z-last", 10)
    save_snapshot("myapp", "a-first", 1)
    entries = list_snapshots("myapp")
    assert entries[0]["label"] == "a-first"
    assert entries[1]["label"] == "z-last"


def test_snapshots_isolated_by_vault():
    save_snapshot("vault-a", "snap", 1)
    assert get_snapshot("vault-b", "snap") is None
