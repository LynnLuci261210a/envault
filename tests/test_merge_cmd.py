"""Tests for envault.merge_cmd CLI commands."""
from __future__ import annotations

import json
import os
import pytest
from click.testing import CliRunner

from envault.merge_cmd import merge_cmd
from envault.crypto import generate_key, save_key, encrypt
from envault.vault import save_vault
from envault.history import record_version


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_env(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    key = generate_key()
    save_key(key, ".envault.key")

    base_text = "DB_HOST=localhost\nSECRET=old\n"
    ours_text = "DB_HOST=localhost\nSECRET=new_ours\n"
    theirs_text = "DB_HOST=prod\nSECRET=new_theirs\n"

    vault_name = "myapp"
    for text in (base_text, ours_text, theirs_text):
        ct = encrypt(text, key)
        v = record_version(vault_name, text)
        save_vault(vault_name, v, {"ciphertext": ct})

    return {"vault": vault_name, "key": key, "dir": tmp_path}


def test_merge_run_clean(runner, vault_env):
    result = runner.invoke(
        merge_cmd,
        ["run", "myapp", "1", "2", "--base", "1"],
    )
    assert result.exit_code == 0, result.output
    assert "cleanly" in result.output or "Saved" in result.output


def test_merge_run_conflict_ours_strategy(runner, vault_env):
    result = runner.invoke(
        merge_cmd,
        ["run", "myapp", "2", "3", "--base", "1", "--strategy", "ours"],
    )
    assert result.exit_code == 0, result.output
    assert "Saved" in result.output


def test_merge_run_conflict_theirs_strategy(runner, vault_env):
    result = runner.invoke(
        merge_cmd,
        ["run", "myapp", "2", "3", "--base", "1", "--strategy", "theirs"],
    )
    assert result.exit_code == 0, result.output


def test_merge_run_missing_key_file(runner, vault_env):
    result = runner.invoke(
        merge_cmd,
        ["run", "myapp", "1", "2", "--key-file", "nonexistent.key"],
    )
    assert result.exit_code != 0
    assert "Key file not found" in result.output


def test_merge_run_missing_vault(runner, vault_env):
    result = runner.invoke(
        merge_cmd,
        ["run", "ghost", "1", "2"],
    )
    assert result.exit_code != 0
