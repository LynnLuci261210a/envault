"""Tests for envault.hook_cmd CLI commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envault.hook_cmd import hook_cmd


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_hook_set_and_get(runner: CliRunner, tmp_path: Path) -> None:
    with patch("envault.hook_cmd.VAULT_DIR", tmp_path):
        result = runner.invoke(hook_cmd, ["set", "pre-lock", "echo hi"])
        assert result.exit_code == 0
        assert "pre-lock" in result.output

        result = runner.invoke(hook_cmd, ["get", "pre-lock"])
        assert result.exit_code == 0
        assert "echo hi" in result.output


def test_hook_get_missing(runner: CliRunner, tmp_path: Path) -> None:
    with patch("envault.hook_cmd.VAULT_DIR", tmp_path):
        result = runner.invoke(hook_cmd, ["get", "post-lock"])
        assert result.exit_code == 0
        assert "No hook" in result.output


def test_hook_set_invalid_event(runner: CliRunner, tmp_path: Path) -> None:
    with patch("envault.hook_cmd.VAULT_DIR", tmp_path):
        result = runner.invoke(hook_cmd, ["set", "on-deploy", "echo nope"])
        assert result.exit_code != 0
        assert "Unknown event" in result.output


def test_hook_delete(runner: CliRunner, tmp_path: Path) -> None:
    with patch("envault.hook_cmd.VAULT_DIR", tmp_path):
        runner.invoke(hook_cmd, ["set", "post-unlock", "echo bye"])
        result = runner.invoke(hook_cmd, ["delete", "post-unlock"])
        assert result.exit_code == 0
        assert "deleted" in result.output


def test_hook_delete_missing(runner: CliRunner, tmp_path: Path) -> None:
    with patch("envault.hook_cmd.VAULT_DIR", tmp_path):
        result = runner.invoke(hook_cmd, ["delete", "pre-lock"])
        assert result.exit_code == 0
        assert "No hook" in result.output


def test_hook_list_empty(runner: CliRunner, tmp_path: Path) -> None:
    with patch("envault.hook_cmd.VAULT_DIR", tmp_path):
        result = runner.invoke(hook_cmd, ["list"])
        assert result.exit_code == 0
        assert "No hooks" in result.output


def test_hook_list_shows_all(runner: CliRunner, tmp_path: Path) -> None:
    with patch("envault.hook_cmd.VAULT_DIR", tmp_path):
        runner.invoke(hook_cmd, ["set", "pre-lock", "echo a"])
        runner.invoke(hook_cmd, ["set", "post-unlock", "echo b"])
        result = runner.invoke(hook_cmd, ["list"])
        assert result.exit_code == 0
        assert "pre-lock" in result.output
        assert "post-unlock" in result.output
