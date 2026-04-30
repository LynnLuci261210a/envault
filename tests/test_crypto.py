"""Tests for envault.crypto encryption/decryption utilities."""

import os
import pytest
from pathlib import Path
from envault.crypto import (
    generate_key,
    save_key,
    load_key,
    encrypt,
    decrypt,
    KEY_FILE,
)


SAMPLE_DATA = b"SECRET_KEY=supersecret\nDB_PASSWORD=hunter2"


def test_generate_key_returns_bytes():
    key = generate_key()
    assert isinstance(key, bytes)
    assert len(key) == 32


def test_generate_key_with_passphrase():
    key = generate_key(passphrase="my-passphrase")
    assert isinstance(key, bytes)
    # salt (16) + raw key (32)
    assert len(key) == 48


def test_encrypt_decrypt_roundtrip():
    key = generate_key()
    token = encrypt(SAMPLE_DATA, key)
    assert token != SAMPLE_DATA
    recovered = decrypt(token, key)
    assert recovered == SAMPLE_DATA


def test_encrypt_decrypt_roundtrip_with_passphrase():
    key = generate_key(passphrase="envault-test")
    token = encrypt(SAMPLE_DATA, key)
    recovered = decrypt(token, key)
    assert recovered == SAMPLE_DATA


def test_decrypt_wrong_key_raises():
    key1 = generate_key()
    key2 = generate_key()
    token = encrypt(SAMPLE_DATA, key1)
    with pytest.raises(ValueError, match="Decryption failed"):
        decrypt(token, key2)


def test_save_and_load_key(tmp_path):
    key_file = str(tmp_path / "test.key")
    key = generate_key()
    save_key(key, path=key_file)
    loaded = load_key(path=key_file)
    assert loaded == key


def test_save_key_sets_permissions(tmp_path):
    key_file = tmp_path / "test.key"
    key = generate_key()
    save_key(key, path=str(key_file))
    mode = oct(key_file.stat().st_mode)[-3:]
    assert mode == "600"


def test_load_key_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="Key file not found"):
        load_key(path=str(tmp_path / "nonexistent.key"))


def test_encrypt_produces_different_ciphertext_each_time():
    key = generate_key()
    token1 = encrypt(SAMPLE_DATA, key)
    token2 = encrypt(SAMPLE_DATA, key)
    # Fernet uses a random IV, so ciphertexts should differ
    assert token1 != token2
