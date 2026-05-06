"""Tests for envault/profile_cmd.py CLI commands."""

import pytest
from click.testing import CliRunner
from pathlib import Path

from envault.profile_cmd import profile_cmd


@pytest.fixture
def runner():
    return CliRunner()


def test_profile_set_and_get(runner, tmp_path):
    result = runner.invoke(profile_cmd, ["set", "dev", "dev-vault", "--dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "dev" in result.output

    result = runner.invoke(profile_cmd, ["get", "dev", "--dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "dev-vault" in result.output


def test_profile_get_missing(runner, tmp_path):
    result = runner.invoke(profile_cmd, ["get", "ghost", "--dir", str(tmp_path)])
    assert result.exit_code != 0


def test_profile_delete(runner, tmp_path):
    runner.invoke(profile_cmd, ["set", "staging", "s-vault", "--dir", str(tmp_path)])
    result = runner.invoke(profile_cmd, ["delete", "staging", "--dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "Deleted" in result.output


def test_profile_delete_missing(runner, tmp_path):
    result = runner.invoke(profile_cmd, ["delete", "nope", "--dir", str(tmp_path)])
    assert result.exit_code != 0


def test_profile_list_empty(runner, tmp_path):
    result = runner.invoke(profile_cmd, ["list", "--dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "No profiles" in result.output


def test_profile_list_shows_entries(runner, tmp_path):
    runner.invoke(profile_cmd, ["set", "dev", "dev-vault", "--dir", str(tmp_path)])
    runner.invoke(profile_cmd, ["set", "prod", "prod-vault", "--dir", str(tmp_path)])
    result = runner.invoke(profile_cmd, ["list", "--dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "dev" in result.output
    assert "prod" in result.output
