"""Tests for envault.import_env."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.crypto import generate_key, save_key, decrypt
from envault.vault import load_vault
from envault.import_env import import_env_file, ImportError as EnvImportError


@pytest.fixture()
def env_setup(tmp_path: Path):
    key = generate_key()
    key_path = tmp_path / "vault.key"
    save_key(key, key_path)

    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\nBAZ=qux\n")

    return {"tmp": tmp_path, "key_path": key_path, "env_file": env_file, "key": key}


def test_import_creates_vault(env_setup):
    s = env_setup
    result = import_env_file(s["env_file"], "myapp", s["key_path"], base_dir=s["tmp"])
    assert result["changed"] is True
    assert result["version"] == 1
    vault = load_vault("myapp", base_dir=s["tmp"])
    assert "ciphertext" in vault


def test_import_decrypts_correctly(env_setup):
    s = env_setup
    import_env_file(s["env_file"], "myapp", s["key_path"], base_dir=s["tmp"])
    vault = load_vault("myapp", base_dir=s["tmp"])
    plaintext = decrypt(vault["ciphertext"], s["key"]).decode()
    assert "FOO=bar" in plaintext
    assert "BAZ=qux" in plaintext


def test_import_missing_file_raises(env_setup):
    s = env_setup
    with pytest.raises(EnvImportError, match="not found"):
        import_env_file(s["tmp"] / "missing.env", "myapp", s["key_path"], base_dir=s["tmp"])


def test_import_increments_version(env_setup):
    s = env_setup
    import_env_file(s["env_file"], "myapp", s["key_path"], base_dir=s["tmp"])
    s["env_file"].write_text("FOO=changed\nBAZ=qux\n")
    result = import_env_file(s["env_file"], "myapp", s["key_path"], base_dir=s["tmp"])
    assert result["version"] == 2


def test_import_skip_unchanged(env_setup):
    s = env_setup
    import_env_file(s["env_file"], "myapp", s["key_path"], base_dir=s["tmp"])
    result = import_env_file(
        s["env_file"], "myapp", s["key_path"], base_dir=s["tmp"], skip_unchanged=True
    )
    assert result["changed"] is False
    assert result["version"] is None


def test_import_force_unchanged(env_setup):
    s = env_setup
    import_env_file(s["env_file"], "myapp", s["key_path"], base_dir=s["tmp"])
    result = import_env_file(
        s["env_file"], "myapp", s["key_path"], base_dir=s["tmp"], skip_unchanged=False
    )
    assert result["changed"] is True
    assert result["version"] == 2


def test_import_records_audit_event(env_setup):
    s = env_setup
    import_env_file(s["env_file"], "myapp", s["key_path"], base_dir=s["tmp"])
    from envault.audit import get_events
    events = get_events("myapp", base_dir=s["tmp"])
    assert any(e["event"] == "import" for e in events)


def test_import_with_note(env_setup):
    s = env_setup
    import_env_file(
        s["env_file"], "myapp", s["key_path"], base_dir=s["tmp"], note="initial import"
    )
    from envault.history import list_versions
    versions = list_versions("myapp", base_dir=s["tmp"])
    assert versions[0]["message"] == "initial import"
