"""Tests for envault.snapshot_cmd CLI commands."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.snapshot_cmd import snapshot_cmd


@pytest.fixture()
def runner(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return CliRunner()


def test_snapshot_save_and_get(runner):
    result = runner.invoke(snapshot_cmd, ["save", "myapp", "v1", "3"])
    assert result.exit_code == 0
    assert "saved" in result.output

    result = runner.invoke(snapshot_cmd, ["get", "myapp", "v1"])
    assert result.exit_code == 0
    assert "version 3" in result.output


def test_snapshot_save_with_note(runner):
    result = runner.invoke(snapshot_cmd, ["save", "myapp", "prod", "7", "--note", "stable"])
    assert result.exit_code == 0

    result = runner.invoke(snapshot_cmd, ["get", "myapp", "prod"])
    assert "stable" in result.output


def test_snapshot_save_duplicate_fails(runner):
    runner.invoke(snapshot_cmd, ["save", "myapp", "v1", "1"])
    result = runner.invoke(snapshot_cmd, ["save", "myapp", "v1", "2"])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_snapshot_get_missing(runner):
    result = runner.invoke(snapshot_cmd, ["get", "myapp", "ghost"])
    assert result.exit_code == 1
    assert "not found" in result.output


def test_snapshot_delete(runner):
    runner.invoke(snapshot_cmd, ["save", "myapp", "v1", "1"])
    result = runner.invoke(snapshot_cmd, ["delete", "myapp", "v1"])
    assert result.exit_code == 0
    assert "deleted" in result.output


def test_snapshot_delete_missing(runner):
    result = runner.invoke(snapshot_cmd, ["delete", "myapp", "ghost"])
    assert result.exit_code == 1


def test_snapshot_list_empty(runner):
    result = runner.invoke(snapshot_cmd, ["list", "myapp"])
    assert result.exit_code == 0
    assert "No snapshots" in result.output


def test_snapshot_list_shows_entries(runner):
    runner.invoke(snapshot_cmd, ["save", "myapp", "alpha", "1"])
    runner.invoke(snapshot_cmd, ["save", "myapp", "beta", "2"])
    result = runner.invoke(snapshot_cmd, ["list", "myapp"])
    assert "alpha" in result.output
    assert "beta" in result.output
