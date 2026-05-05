"""Tests for envault.share — bundle export/import."""

from __future__ import annotations

import json
import base64
from pathlib import Path

import pytest

from envault.crypto import generate_key, save_key
from envault.vault import save_vault
from envault.share import export_bundle, import_bundle, ShareError


ENV_CONTENT = "DB_HOST=localhost\nDB_PASS=secret\nDEBUG=true\n"


@pytest.fixture()
def vault_env(tmp_path: Path):
    key = generate_key()
    key_path = tmp_path / "envault.key"
    save_key(key, key_path)
    save_vault("prod", ENV_CONTENT, tmp_path, key_path)
    return tmp_path, key_path


def test_export_bundle_returns_bytes(vault_env):
    vault_dir, key_path = vault_env
    bundle = export_bundle("prod", vault_dir, key_path)
    assert isinstance(bundle, bytes)


def test_export_bundle_is_valid_json(vault_env):
    vault_dir, key_path = vault_env
    bundle = export_bundle("prod", vault_dir, key_path)
    data = json.loads(bundle)
    assert data["vault"] == "prod"
    assert "ciphertext" in data
    assert data["has_passphrase"] is False
    assert "key" in data


def test_export_bundle_with_passphrase_omits_key(vault_env):
    vault_dir, key_path = vault_env
    bundle = export_bundle("prod", vault_dir, key_path, passphrase="hunter2")
    data = json.loads(bundle)
    assert data["has_passphrase"] is True
    assert "key" not in data


def test_import_bundle_roundtrip(vault_env):
    vault_dir, key_path = vault_env
    bundle = export_bundle("prod", vault_dir, key_path)
    name, plaintext = import_bundle(bundle)
    assert name == "prod"
    assert plaintext == ENV_CONTENT


def test_import_bundle_roundtrip_with_passphrase(vault_env):
    vault_dir, key_path = vault_env
    bundle = export_bundle("prod", vault_dir, key_path, passphrase="s3cr3t")
    name, plaintext = import_bundle(bundle, passphrase="s3cr3t")
    assert name == "prod"
    assert plaintext == ENV_CONTENT


def test_import_bundle_wrong_passphrase_raises(vault_env):
    vault_dir, key_path = vault_env
    bundle = export_bundle("prod", vault_dir, key_path, passphrase="correct")
    with pytest.raises(ShareError, match="Decryption failed"):
        import_bundle(bundle, passphrase="wrong")


def test_import_bundle_missing_passphrase_raises(vault_env):
    vault_dir, key_path = vault_env
    bundle = export_bundle("prod", vault_dir, key_path, passphrase="needed")
    with pytest.raises(ShareError, match="passphrase"):
        import_bundle(bundle)


def test_import_bundle_invalid_json_raises():
    with pytest.raises(ShareError, match="Invalid bundle format"):
        import_bundle(b"not json at all")


def test_import_bundle_missing_fields_raises():
    bad = json.dumps({"vault": "x"}).encode()
    with pytest.raises(ShareError, match="missing required fields"):
        import_bundle(bad)
