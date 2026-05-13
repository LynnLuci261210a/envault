"""Tests for envault/sign_cmd.py"""

import json
import pytest
from click.testing import CliRunner

from envault.sign_cmd import sign_cmd


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_env(tmp_path, monkeypatch):
    """Set up a fake vault and key, redirect path helpers."""
    import envault.sign as sign_mod
    import envault.sign_cmd as cmd_mod
    from envault.crypto import generate_key

    key = generate_key()
    key_file = tmp_path / ".envault.key"
    key_file.write_bytes(key)

    vault_data = {"ciphertext": "dGVzdA==", "nonce": "aaaaaa=="}
    vault_raw = json.dumps(vault_data).encode()

    def fake_load_key(path):
        return key_file.read_bytes()

    def fake_load_vault(name):
        return vault_data

    def fake_sigs_path(name):
        return tmp_path / f"{name}.sig.json"

    monkeypatch.setattr(cmd_mod, "load_key", fake_load_key)
    monkeypatch.setattr(cmd_mod, "load_vault", fake_load_vault)
    monkeypatch.setattr(sign_mod, "_sigs_path", fake_sigs_path)

    return {"key": key, "key_file": str(key_file), "vault_raw": vault_raw}


def test_sign_create_outputs_signature(runner, vault_env):
    result = runner.invoke(sign_cmd, ["create", "myvault", "--key-file", vault_env["key_file"]])
    assert result.exit_code == 0
    assert "Signed vault 'myvault'" in result.output


def test_sign_verify_ok(runner, vault_env):
    runner.invoke(sign_cmd, ["create", "myvault", "--key-file", vault_env["key_file"]])
    result = runner.invoke(sign_cmd, ["verify", "myvault", "--key-file", vault_env["key_file"]])
    assert result.exit_code == 0
    assert "OK" in result.output


def test_sign_verify_no_signature_reports_missing(runner, vault_env):
    result = runner.invoke(sign_cmd, ["verify", "unsigned", "--key-file", vault_env["key_file"]])
    assert result.exit_code == 0
    assert "No signature found" in result.output


def test_sign_info_shows_alg(runner, vault_env):
    runner.invoke(sign_cmd, ["create", "myvault", "--key-file", vault_env["key_file"]])
    result = runner.invoke(sign_cmd, ["info", "myvault"])
    assert result.exit_code == 0
    assert "hmac-sha256" in result.output


def test_sign_info_missing_vault(runner, vault_env):
    result = runner.invoke(sign_cmd, ["info", "ghost"])
    assert result.exit_code == 0
    assert "No signature file" in result.output


def test_sign_delete_removes_signature(runner, vault_env):
    runner.invoke(sign_cmd, ["create", "myvault", "--key-file", vault_env["key_file"]])
    result = runner.invoke(sign_cmd, ["delete", "myvault"])
    assert result.exit_code == 0
    assert "deleted" in result.output


def test_sign_delete_absent_reports_not_found(runner, vault_env):
    result = runner.invoke(sign_cmd, ["delete", "ghost"])
    assert result.exit_code == 0
    assert "No signature file found" in result.output
