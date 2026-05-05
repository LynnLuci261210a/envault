"""Tests for envault.rotate (key rotation)."""

from __future__ import annotations

from pathlib import Path

import pytest

from envault.crypto import decrypt, encrypt, generate_key, save_key
from envault.vault import load_vault, save_vault
from envault.rotate import RotationError, rotate_key


PLAINTEXT = b"SECRET=hunter2\nAPI_KEY=abc123\n"


@pytest.fixture()
def vault_setup(tmp_path: Path):
    """Create a minimal encrypted vault and key on disk."""
    vault_dir = tmp_path / "vaults"
    vault_dir.mkdir()
    keys_dir = tmp_path / "keys"
    keys_dir.mkdir()

    key = generate_key()
    key_path = keys_dir / "test.key"
    save_key(key, key_path)

    ciphertext = encrypt(PLAINTEXT, key)
    save_vault("test", {"ciphertext": ciphertext, "version": 1}, vault_dir=vault_dir)

    return {"vault_dir": vault_dir, "keys_dir": keys_dir, "key_path": key_path, "key": key}


def test_rotate_key_returns_path(vault_setup, tmp_path):
    s = vault_setup
    new_key_path = tmp_path / "new.key"
    result = rotate_key(
        "test",
        s["key_path"],
        new_key_path=new_key_path,
        vault_dir=s["vault_dir"],
    )
    assert result == new_key_path
    assert new_key_path.exists()


def test_rotate_key_new_key_decrypts_vault(vault_setup, tmp_path):
    s = vault_setup
    new_key_path = tmp_path / "new.key"
    rotate_key("test", s["key_path"], new_key_path=new_key_path, vault_dir=s["vault_dir"])

    from envault.crypto import load_key

    new_key = load_key(new_key_path)
    vault = load_vault("test", vault_dir=s["vault_dir"])
    recovered = decrypt(vault["ciphertext"], new_key)
    assert recovered == PLAINTEXT


def test_rotate_key_old_key_no_longer_works(vault_setup, tmp_path):
    s = vault_setup
    new_key_path = tmp_path / "new.key"
    rotate_key("test", s["key_path"], new_key_path=new_key_path, vault_dir=s["vault_dir"])

    vault = load_vault("test", vault_dir=s["vault_dir"])
    with pytest.raises(Exception):
        decrypt(vault["ciphertext"], s["key"])


def test_rotate_key_overwrites_old_key_by_default(vault_setup):
    s = vault_setup
    original_key_bytes = s["key_path"].read_bytes()
    rotate_key("test", s["key_path"], vault_dir=s["vault_dir"])
    new_key_bytes = s["key_path"].read_bytes()
    assert new_key_bytes != original_key_bytes


def test_rotate_key_missing_vault_raises(vault_setup, tmp_path):
    s = vault_setup
    with pytest.raises(RotationError, match="not found"):
        rotate_key("nonexistent", s["key_path"], vault_dir=s["vault_dir"])


def test_rotate_key_wrong_key_raises(vault_setup):
    s = vault_setup
    wrong_key = generate_key()
    wrong_key_path = s["keys_dir"] / "wrong.key"
    save_key(wrong_key, wrong_key_path)
    with pytest.raises(RotationError, match="decrypt"):
        rotate_key("test", wrong_key_path, vault_dir=s["vault_dir"])


def test_rotate_key_with_passphrase(vault_setup, tmp_path):
    s = vault_setup
    new_key_path = tmp_path / "pass.key"
    rotate_key(
        "test",
        s["key_path"],
        new_key_path=new_key_path,
        passphrase="my-passphrase",
        vault_dir=s["vault_dir"],
    )
    assert new_key_path.exists()
