"""Tests for envault.pin_cmd CLI commands."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.pin_cmd import pin_cmd


@pytest.fixture()
def runner(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return CliRunner()


def test_pin_set_and_get(runner):
    result = runner.invoke(pin_cmd, ["set", "production", "3"])
    assert result.exit_code == 0
    assert "Pinned 'production' to version 3" in result.output

    result = runner.invoke(pin_cmd, ["get", "production"])
    assert result.exit_code == 0
    assert "3" in result.output


def test_pin_get_missing(runner):
    result = runner.invoke(pin_cmd, ["get", "ghost"])
    assert result.exit_code == 0
    assert "No pin set" in result.output


def test_pin_set_invalid_version(runner):
    result = runner.invoke(pin_cmd, ["set", "production", "0"])
    assert result.exit_code != 0
    assert "Error" in result.output


def test_pin_delete(runner):
    runner.invoke(pin_cmd, ["set", "staging", "2"])
    result = runner.invoke(pin_cmd, ["delete", "staging"])
    assert result.exit_code == 0
    assert "removed" in result.output


def test_pin_delete_missing(runner):
    result = runner.invoke(pin_cmd, ["delete", "nobody"])
    assert result.exit_code == 0
    assert "No pin found" in result.output


def test_pin_list_empty(runner):
    result = runner.invoke(pin_cmd, ["list"])
    assert result.exit_code == 0
    assert "No pins set" in result.output


def test_pin_list_shows_all(runner):
    runner.invoke(pin_cmd, ["set", "production", "4"])
    runner.invoke(pin_cmd, ["set", "staging", "1"])
    result = runner.invoke(pin_cmd, ["list"])
    assert result.exit_code == 0
    assert "production: v4" in result.output
    assert "staging: v1" in result.output
