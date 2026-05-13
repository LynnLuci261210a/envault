"""Tests for envault.vault module."""

import json
from pathlib import Path

import pytest

from envault.crypto import generate_key, save_key
from envault.vault import delete_vault, list_vaults, load_vault, save_vault

SAMPLE_ENV = "DB_HOST=localhost\nDB_PORT=5432\nSECRET_KEY=supersecret\n"


@pytest.fixture
def tmp_vault_setup(tmp_path):
    key_path = tmp_path / "test.key"
    vault_dir = tmp_path / "vaults"
    key = generate_key()
    save_key(key, key_path)
    return key_path, vault_dir


def test_save_vault_creates_file(tmp_vault_setup):
    key_path, vault_dir = tmp_vault_setup
    path = save_vault("production", SAMPLE_ENV, key_path, vault_dir=vault_dir)
    assert path.exists()
    assert path.suffix == ".vault"


def test_save_vault_stores_valid_json(tmp_vault_setup):
    key_path, vault_dir = tmp_vault_setup
    path = save_vault("staging", SAMPLE_ENV, key_path, vault_dir=vault_dir)
    data = json.loads(path.read_text())
    assert "name" in data
    assert "created_at" in data
    assert "ciphertext" in data
    assert data["name"] == "staging"


def test_load_vault_roundtrip(tmp_vault_setup):
    key_path, vault_dir = tmp_vault_setup
    save_vault("dev", SAMPLE_ENV, key_path, vault_dir=vault_dir)
    result = load_vault("dev", key_path, vault_dir=vault_dir)
    assert result == SAMPLE_ENV


def test_load_vault_not_found_raises(tmp_vault_setup):
    key_path, vault_dir = tmp_vault_setup
    with pytest.raises(FileNotFoundError, match="nonexistent"):
        load_vault("nonexistent", key_path, vault_dir=vault_dir)


def test_list_vaults_empty(tmp_path):
    empty_dir = tmp_path / "empty_vaults"
    assert list_vaults(vault_dir=empty_dir) == []


def test_list_vaults_returns_entries(tmp_vault_setup):
    key_path, vault_dir = tmp_vault_setup
    save_vault("alpha", SAMPLE_ENV, key_path, vault_dir=vault_dir)
    save_vault("beta", SAMPLE_ENV, key_path, vault_dir=vault_dir)
    vaults = list_vaults(vault_dir=vault_dir)
    names = [v["name"] for v in vaults]
    assert "alpha" in names
    assert "beta" in names
    assert len(vaults) == 2


def test_delete_vault_removes_file(tmp_vault_setup):
    key_path, vault_dir = tmp_vault_setup
    save_vault("temp", SAMPLE_ENV, key_path, vault_dir=vault_dir)
    result = delete_vault("temp", vault_dir=vault_dir)
    assert result is True
    assert not (vault_dir / "temp.vault").exists()


def test_delete_vault_missing_returns_false(tmp_path):
    vault_dir = tmp_path / "vaults"
    result = delete_vault("ghost", vault_dir=vault_dir)
    assert result is False


def test_save_vault_with_passphrase(tmp_path):
    key_path = tmp_path / "pp.key"
    vault_dir = tmp_path / "vaults"
    key = generate_key(passphrase="mypass")
    save_key(key, key_path)
    save_vault("secure", SAMPLE_ENV, key_path, vault_dir=vault_dir, passphrase="mypass")
    result = load_vault("secure", key_path, vault_dir=vault_dir, passphrase="mypass")
    assert result == SAMPLE_ENV


def test_save_vault_overwrites_existing(tmp_vault_setup):
    """Saving a vault with the same name should overwrite the previous version."""
    key_path, vault_dir = tmp_vault_setup
    updated_env = "DB_HOST=remotehost\nDB_PORT=5432\n"
    save_vault("overwrite", SAMPLE_ENV, key_path, vault_dir=vault_dir)
    save_vault("overwrite", updated_env, key_path, vault_dir=vault_dir)
    result = load_vault("overwrite", key_path, vault_dir=vault_dir)
    assert result == updated_env
    assert len(list_vaults(vault_dir=vault_dir)) == 1
