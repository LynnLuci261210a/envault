"""Tests for envault.search module."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from envault.crypto import generate_key, encrypt, save_key
from envault.vault import save_vault
from envault.search import search_vault, SearchResult, SearchMatch


@pytest.fixture()
def vault_env(tmp_path: Path):
    """Create a small vault with known content and return (vault_name, tmp_path)."""
    vault_name = "test"
    key = generate_key()
    save_key(vault_name, key, base_dir=str(tmp_path))

    plaintext = "DB_HOST=localhost\nDB_PORT=5432\nSECRET_KEY=supersecret\n"
    ciphertext = encrypt(plaintext, key)
    save_vault(vault_name, {"version": 1, "ciphertext": ciphertext}, base_dir=str(tmp_path))

    return vault_name, str(tmp_path)


def test_search_finds_key_match(vault_env):
    vault_name, key_dir = vault_env
    result = search_vault(vault_name, "DB_HOST", key_dir=key_dir)
    assert result.found
    assert any(m.key == "DB_HOST" and m.match_in == "key" for m in result.matches)


def test_search_finds_value_match(vault_env):
    vault_name, key_dir = vault_env
    result = search_vault(vault_name, "localhost", key_dir=key_dir)
    assert result.found
    assert any(m.key == "DB_HOST" and m.match_in == "value" for m in result.matches)


def test_search_keys_only_skips_value_match(vault_env):
    vault_name, key_dir = vault_env
    result = search_vault(vault_name, "localhost", key_dir=key_dir, keys_only=True)
    assert not result.found


def test_search_case_insensitive_by_default(vault_env):
    vault_name, key_dir = vault_env
    result = search_vault(vault_name, "db_host", key_dir=key_dir)
    assert result.found


def test_search_case_sensitive_no_match(vault_env):
    vault_name, key_dir = vault_env
    result = search_vault(vault_name, "db_host", key_dir=key_dir, case_sensitive=True)
    assert not result.found


def test_search_no_match_returns_empty_result(vault_env):
    vault_name, key_dir = vault_env
    result = search_vault(vault_name, "NONEXISTENT_KEY_XYZ", key_dir=key_dir)
    assert not result.found
    assert result.matches == []


def test_search_missing_vault_returns_empty(tmp_path):
    result = search_vault("ghost", "anything", key_dir=str(tmp_path))
    assert not result.found


def test_search_result_summary_no_matches():
    r = SearchResult()
    assert r.summary() == "No matches found."


def test_search_match_str(vault_env):
    vault_name, key_dir = vault_env
    result = search_vault(vault_name, "DB_HOST", key_dir=key_dir)
    assert result.found
    text = str(result.matches[0])
    assert "DB_HOST" in text
    assert "key" in text


def test_search_partial_query(vault_env):
    vault_name, key_dir = vault_env
    result = search_vault(vault_name, "DB_", key_dir=key_dir)
    keys_found = {m.key for m in result.matches}
    assert "DB_HOST" in keys_found
    assert "DB_PORT" in keys_found
