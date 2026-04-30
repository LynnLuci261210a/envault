"""Integration tests for the envault CLI."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli import cli

SAMPLE_ENV = "API_KEY=abc123\nDEBUG=true\n"


@pytest.fixture
def runner():
    return CliRunner()


def test_init_creates_key(runner, tmp_path):
    key_path = tmp_path / "master.key"
    result = runner.invoke(cli, ["init", "--key-path", str(key_path)])
    assert result.exit_code == 0
    assert key_path.exists()
    assert "Master key saved" in result.output


def test_init_refuses_overwrite(runner, tmp_path):
    key_path = tmp_path / "master.key"
    runner.invoke(cli, ["init", "--key-path", str(key_path)])
    result = runner.invoke(cli, ["init", "--key-path", str(key_path)])
    assert result.exit_code != 0
    assert "already exists" in result.output


def test_lock_and_unlock_roundtrip(runner, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    key_path = tmp_path / ".envault" / "master.key"
    env_file = tmp_path / ".env"
    env_file.write_text(SAMPLE_ENV)

    runner.invoke(cli, ["init", "--key-path", str(key_path)])
    result = runner.invoke(cli, ["lock", str(env_file), "myenv", "--key-path", str(key_path)])
    assert result.exit_code == 0
    assert "Encrypted" in result.output

    out_file = tmp_path / "recovered.env"
    result = runner.invoke(cli, ["unlock", "myenv", "-o", str(out_file), "--key-path", str(key_path)])
    assert result.exit_code == 0
    assert out_file.read_text() == SAMPLE_ENV


def test_unlock_missing_vault(runner, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    key_path = tmp_path / ".envault" / "master.key"
    runner.invoke(cli, ["init", "--key-path", str(key_path)])
    result = runner.invoke(cli, ["unlock", "ghost", "--key-path", str(key_path)])
    assert result.exit_code != 0


def test_list_empty(runner, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    assert "No vaults found" in result.output


def test_list_shows_vaults(runner, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    key_path = tmp_path / ".envault" / "master.key"
    env_file = tmp_path / ".env"
    env_file.write_text(SAMPLE_ENV)
    runner.invoke(cli, ["init", "--key-path", str(key_path)])
    runner.invoke(cli, ["lock", str(env_file), "prod", "--key-path", str(key_path)])
    result = runner.invoke(cli, ["list"])
    assert "prod" in result.output


def test_delete_vault(runner, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    key_path = tmp_path / ".envault" / "master.key"
    env_file = tmp_path / ".env"
    env_file.write_text(SAMPLE_ENV)
    runner.invoke(cli, ["init", "--key-path", str(key_path)])
    runner.invoke(cli, ["lock", str(env_file), "temp", "--key-path", str(key_path)])
    result = runner.invoke(cli, ["delete", "temp"])
    assert result.exit_code == 0
    assert "deleted" in result.output


def test_delete_missing_vault(runner, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli, ["delete", "nobody"])
    assert result.exit_code != 0
