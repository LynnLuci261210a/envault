"""Tests for envault/sign.py"""

import json
import pytest

from envault.sign import (
    SignError,
    _compute_hmac,
    delete_signature,
    sign_vault,
    signature_info,
    verify_vault,
)


SAMPLE_KEY = b"a" * 32
SAMPLE_DATA = b'{"ciphertext": "abc123"}'
VAULT_NAME = "test_sign_vault"


@pytest.fixture(autouse=True)
def patch_vault_path(tmp_path, monkeypatch):
    """Redirect _sigs_path to use tmp_path."""
    import envault.sign as sign_mod

    def fake_sigs_path(name):
        return tmp_path / f"{name}.sig.json"

    monkeypatch.setattr(sign_mod, "_sigs_path", fake_sigs_path)


def test_compute_hmac_returns_hex_string():
    result = _compute_hmac(SAMPLE_DATA, SAMPLE_KEY)
    assert isinstance(result, str)
    assert len(result) == 64  # sha256 hex digest


def test_compute_hmac_deterministic():
    a = _compute_hmac(SAMPLE_DATA, SAMPLE_KEY)
    b = _compute_hmac(SAMPLE_DATA, SAMPLE_KEY)
    assert a == b


def test_sign_vault_creates_file(tmp_path):
    sig = sign_vault(VAULT_NAME, SAMPLE_DATA, SAMPLE_KEY)
    assert isinstance(sig, str)
    assert len(sig) == 64


def test_sign_vault_file_contains_expected_fields(tmp_path):
    sign_vault(VAULT_NAME, SAMPLE_DATA, SAMPLE_KEY)
    info = signature_info(VAULT_NAME)
    assert info is not None
    assert info["alg"] == "hmac-sha256"
    assert "sig" in info
    assert info["version"] == 1


def test_verify_vault_returns_true_on_valid_sig():
    sign_vault(VAULT_NAME, SAMPLE_DATA, SAMPLE_KEY)
    result = verify_vault(VAULT_NAME, SAMPLE_DATA, SAMPLE_KEY)
    assert result is True


def test_verify_vault_returns_false_when_no_sig_file():
    result = verify_vault("nonexistent_vault", SAMPLE_DATA, SAMPLE_KEY)
    assert result is False


def test_verify_vault_raises_on_tampered_data():
    sign_vault(VAULT_NAME, SAMPLE_DATA, SAMPLE_KEY)
    tampered = b'{"ciphertext": "TAMPERED"}'
    with pytest.raises(SignError, match="tampered"):
        verify_vault(VAULT_NAME, tampered, SAMPLE_KEY)


def test_verify_vault_raises_on_wrong_key():
    sign_vault(VAULT_NAME, SAMPLE_DATA, SAMPLE_KEY)
    wrong_key = b"b" * 32
    with pytest.raises(SignError):
        verify_vault(VAULT_NAME, SAMPLE_DATA, wrong_key)


def test_delete_signature_removes_file():
    sign_vault(VAULT_NAME, SAMPLE_DATA, SAMPLE_KEY)
    removed = delete_signature(VAULT_NAME)
    assert removed is True
    assert signature_info(VAULT_NAME) is None


def test_delete_signature_returns_false_if_absent():
    removed = delete_signature("ghost_vault")
    assert removed is False


def test_signature_info_returns_none_when_missing():
    assert signature_info("no_such_vault") is None
