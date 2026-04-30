"""Tests for envault.history module."""

import pytest
from pathlib import Path
from unittest.mock import patch

from envault import history as hist


@pytest.fixture(autouse=True)
def tmp_history(tmp_path, monkeypatch):
    """Redirect HISTORY_DIR to a temp directory for all tests."""
    fake_dir = tmp_path / ".envault" / "history"
    monkeypatch.setattr(hist, "HISTORY_DIR", fake_dir)
    return fake_dir


def test_record_version_returns_version_number():
    v = hist.record_version("myapp", "deadbeef")
    assert v == 1


def test_record_version_increments():
    hist.record_version("myapp", "aabbcc")
    v2 = hist.record_version("myapp", "ddeeff")
    assert v2 == 2


def test_record_version_creates_file(tmp_history):
    hist.record_version("myapp", "aabbcc")
    assert (tmp_history / "myapp.history.json").exists()


def test_list_versions_empty():
    result = hist.list_versions("nonexistent")
    assert result == []


def test_list_versions_returns_metadata():
    hist.record_version("myapp", "aabb", note="initial")
    hist.record_version("myapp", "ccdd", note="update")
    versions = hist.list_versions("myapp")
    assert len(versions) == 2
    assert versions[0]["version"] == 1
    assert versions[0]["note"] == "initial"
    assert versions[1]["version"] == 2
    assert "ciphertext" not in versions[0]


def test_list_versions_has_timestamp():
    hist.record_version("myapp", "aabb")
    versions = hist.list_versions("myapp")
    assert "timestamp" in versions[0]
    assert versions[0]["timestamp"] > 0


def test_get_version_returns_ciphertext():
    hist.record_version("myapp", "cafebabe")
    hist.record_version("myapp", "deadbeef")
    assert hist.get_version("myapp", 1) == "cafebabe"
    assert hist.get_version("myapp", 2) == "deadbeef"


def test_get_version_missing_returns_none():
    result = hist.get_version("myapp", 99)
    assert result is None


def test_latest_version_none_when_empty():
    assert hist.latest_version("myapp") is None


def test_latest_version_returns_last():
    hist.record_version("myapp", "v1")
    hist.record_version("myapp", "v2")
    latest = hist.latest_version("myapp")
    assert latest["version"] == 2
    assert latest["ciphertext"] == "v2"


def test_delete_history_removes_file(tmp_history):
    hist.record_version("myapp", "data")
    assert hist.delete_history("myapp") is True
    assert not (tmp_history / "myapp.history.json").exists()


def test_delete_history_nonexistent_returns_false():
    assert hist.delete_history("ghost") is False
