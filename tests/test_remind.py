"""Tests for envault.remind and remind_cmd."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envault.remind import (
    DEFAULT_MAX_AGE_DAYS,
    _remind_path,
    days_since_rotation,
    get_last_rotation,
    is_overdue,
    record_rotation,
)
from envault.remind_cmd import remind_cmd


@pytest.fixture()
def tmp_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# remind module
# ---------------------------------------------------------------------------

def test_record_rotation_creates_file(tmp_dir):
    record_rotation("production", vault_dir=str(tmp_dir))
    assert _remind_path(str(tmp_dir)).exists()


def test_record_rotation_returns_iso_string(tmp_dir):
    ts = record_rotation("production", vault_dir=str(tmp_dir))
    # Must be parseable as a datetime
    dt = datetime.fromisoformat(ts)
    assert dt.tzinfo is not None


def test_get_last_rotation_returns_none_when_missing(tmp_dir):
    assert get_last_rotation("staging", vault_dir=str(tmp_dir)) is None


def test_get_last_rotation_returns_datetime(tmp_dir):
    record_rotation("staging", vault_dir=str(tmp_dir))
    dt = get_last_rotation("staging", vault_dir=str(tmp_dir))
    assert isinstance(dt, datetime)


def test_is_overdue_never_rotated(tmp_dir):
    assert is_overdue("new-vault", vault_dir=str(tmp_dir)) is True


def test_is_overdue_fresh_rotation(tmp_dir):
    record_rotation("production", vault_dir=str(tmp_dir))
    assert is_overdue("production", max_age_days=30, vault_dir=str(tmp_dir)) is False


def test_is_overdue_old_rotation(tmp_dir):
    old_ts = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
    data = {"production": {"last_rotated": old_ts}}
    _remind_path(str(tmp_dir)).write_text(json.dumps(data))
    assert is_overdue("production", max_age_days=30, vault_dir=str(tmp_dir)) is True


def test_days_since_rotation_none_when_missing(tmp_dir):
    assert days_since_rotation("missing", vault_dir=str(tmp_dir)) is None


def test_days_since_rotation_value(tmp_dir):
    old_ts = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
    data = {"production": {"last_rotated": old_ts}}
    _remind_path(str(tmp_dir)).write_text(json.dumps(data))
    assert days_since_rotation("production", vault_dir=str(tmp_dir)) == 5


# ---------------------------------------------------------------------------
# remind_cmd CLI
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner():
    return CliRunner()


def test_remind_mark(runner, tmp_dir):
    result = runner.invoke(remind_cmd, ["mark", "production"])
    assert result.exit_code == 0
    assert "Rotation recorded" in result.output


def test_remind_status_ok(runner, tmp_dir):
    record_rotation("production", vault_dir=str(tmp_dir))
    result = runner.invoke(remind_cmd, ["status", "production", "--max-age", "30"])
    assert result.exit_code == 0
    assert "OK" in result.output


def test_remind_status_overdue(runner, tmp_dir):
    old_ts = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
    data = {"production": {"last_rotated": old_ts}}
    _remind_path(str(tmp_dir)).write_text(json.dumps(data))
    result = runner.invoke(remind_cmd, ["status", "production", "--max-age", "30"])
    assert result.exit_code == 1
    assert "OVERDUE" in result.output


def test_remind_check_passes(runner, tmp_dir):
    record_rotation("staging", vault_dir=str(tmp_dir))
    result = runner.invoke(remind_cmd, ["check", "staging"])
    assert result.exit_code == 0


def test_remind_check_fails_never_rotated(runner, tmp_dir):
    result = runner.invoke(remind_cmd, ["check", "staging"])
    assert result.exit_code == 1
