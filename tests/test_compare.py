"""Tests for envault.compare and envault.compare_cmd."""

from __future__ import annotations

import json
import pathlib

import pytest
from click.testing import CliRunner

from envault.compare import compare_refs, CompareError
from envault.compare_cmd import compare_cmd
from envault.crypto import generate_key, save_key, encrypt
from envault.history import record_version
from envault.snapshot import save_snapshot


ENV_V1 = "FOO=bar\nBAZ=qux\n"
ENV_V2 = "FOO=bar\nBAZ=changed\nNEW=value\n"


@pytest.fixture()
def vault_env(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    key = generate_key()
    key_path = str(tmp_path / ".envault.key")
    save_key(key, key_path)

    vault_name = "myapp"
    ct1 = encrypt(ENV_V1.encode(), key)
    ct2 = encrypt(ENV_V2.encode(), key)

    record_version(vault_name, ct1.hex(), metadata={"note": "v1"})
    record_version(vault_name, ct2.hex(), metadata={"note": "v2"})
    save_snapshot(vault_name, "stable", version=1)

    return {"vault": vault_name, "key_path": key_path, "key": key}


def test_compare_refs_detects_changes(vault_env):
    result = compare_refs("myapp", "1", "2", vault_env["key_path"])
    assert result.has_changes()
    assert "BAZ" in result.diff.changed
    assert "NEW" in result.diff.added


def test_compare_refs_no_changes_same_version(vault_env):
    result = compare_refs("myapp", "1", "1", vault_env["key_path"])
    assert not result.has_changes()


def test_compare_refs_snapshot_resolves(vault_env):
    # 'stable' snapshot points to version 1; compare with version 2
    result = compare_refs("myapp", "stable", "2", vault_env["key_path"])
    assert result.has_changes()
    assert result.ref_a == "stable"
    assert result.ref_b == "2"


def test_compare_refs_unknown_ref_raises(vault_env):
    with pytest.raises(CompareError, match="Unknown ref"):
        compare_refs("myapp", "nonexistent", "2", vault_env["key_path"])


def test_compare_refs_missing_version_raises(vault_env):
    with pytest.raises(CompareError, match="Version 99 not found"):
        compare_refs("myapp", "99", "2", vault_env["key_path"])


def test_summary_contains_vault_name(vault_env):
    result = compare_refs("myapp", "1", "2", vault_env["key_path"])
    assert "myapp" in result.summary()


# --- CLI tests ---


@pytest.fixture()
def runner():
    return CliRunner()


def test_cli_compare_shows_diff(runner, vault_env, monkeypatch):
    monkeypatch.chdir(pathlib.Path(vault_env["key_path"]).parent)
    res = runner.invoke(
        compare_cmd,
        ["run", "1", "2", "--vault", "myapp", "--key", vault_env["key_path"], "--no-color"],
    )
    assert res.exit_code == 0, res.output
    assert "BAZ" in res.output
    assert "NEW" in res.output


def test_cli_compare_no_changes(runner, vault_env, monkeypatch):
    monkeypatch.chdir(pathlib.Path(vault_env["key_path"]).parent)
    res = runner.invoke(
        compare_cmd,
        ["run", "1", "1", "--vault", "myapp", "--key", vault_env["key_path"]],
    )
    assert res.exit_code == 0
    assert "No differences" in res.output


def test_cli_compare_bad_ref(runner, vault_env, monkeypatch):
    monkeypatch.chdir(pathlib.Path(vault_env["key_path"]).parent)
    res = runner.invoke(
        compare_cmd,
        ["run", "ghost", "2", "--vault", "myapp", "--key", vault_env["key_path"]],
    )
    assert res.exit_code != 0
    assert "Error" in res.output
