"""Tests for envault.audit module."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from envault.audit import (
    record_event,
    get_events,
    clear_events,
    _audit_path,
)


@pytest.fixture
def tmp_audit(tmp_path, monkeypatch):
    """Run audit operations inside a temporary directory."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_record_event_creates_file(tmp_audit):
    record_event("lock", "production", directory=str(tmp_audit))
    assert _audit_path(str(tmp_audit)).exists()


def test_record_event_returns_entry(tmp_audit):
    entry = record_event("init", "staging", directory=str(tmp_audit))
    assert entry["action"] == "init"
    assert entry["env_name"] == "staging"
    assert "timestamp" in entry
    assert "user" in entry


def test_record_event_with_version(tmp_audit):
    entry = record_event("lock", "production", version=3, directory=str(tmp_audit))
    assert entry["version"] == 3


def test_record_event_without_version_omits_key(tmp_audit):
    entry = record_event("unlock", "dev", directory=str(tmp_audit))
    assert "version" not in entry


def test_multiple_events_accumulate(tmp_audit):
    record_event("init", "dev", directory=str(tmp_audit))
    record_event("lock", "dev", version=1, directory=str(tmp_audit))
    record_event("unlock", "dev", version=1, directory=str(tmp_audit))
    events = get_events(directory=str(tmp_audit))
    assert len(events) == 3


def test_get_events_filter_by_env_name(tmp_audit):
    record_event("lock", "production", directory=str(tmp_audit))
    record_event("lock", "staging", directory=str(tmp_audit))
    events = get_events(directory=str(tmp_audit), env_name="production")
    assert len(events) == 1
    assert events[0]["env_name"] == "production"


def test_get_events_filter_by_action(tmp_audit):
    record_event("lock", "dev", directory=str(tmp_audit))
    record_event("unlock", "dev", directory=str(tmp_audit))
    record_event("lock", "dev", directory=str(tmp_audit))
    events = get_events(directory=str(tmp_audit), action="lock")
    assert len(events) == 2


def test_get_events_filter_combined(tmp_audit):
    record_event("lock", "dev", directory=str(tmp_audit))
    record_event("lock", "prod", directory=str(tmp_audit))
    record_event("unlock", "dev", directory=str(tmp_audit))
    events = get_events(directory=str(tmp_audit), env_name="dev", action="lock")
    assert len(events) == 1


def test_get_events_empty_when_no_file(tmp_audit):
    events = get_events(directory=str(tmp_audit))
    assert events == []


def test_clear_events(tmp_audit):
    record_event("init", "dev", directory=str(tmp_audit))
    clear_events(directory=str(tmp_audit))
    events = get_events(directory=str(tmp_audit))
    assert events == []


def test_audit_file_is_valid_json(tmp_audit):
    record_event("lock", "production", version=1, directory=str(tmp_audit))
    path = _audit_path(str(tmp_audit))
    with open(path) as fh:
        data = json.load(fh)
    assert "entries" in data
    assert isinstance(data["entries"], list)
