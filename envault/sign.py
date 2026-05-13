"""Signing and verification of vault contents for integrity checks."""

import hashlib
import hmac
import json
from pathlib import Path

SIGNATURE_VERSION = 1


class SignError(Exception):
    pass


def _sigs_path(vault_name: str) -> Path:
    from envault.vault import _vault_path
    base = _vault_path(vault_name).parent
    return base / f"{vault_name}.sig.json"


def _compute_hmac(data: bytes, key: bytes) -> str:
    return hmac.new(key, data, hashlib.sha256).hexdigest()


def sign_vault(vault_name: str, raw_ciphertext: bytes, key: bytes) -> str:
    """Compute and persist an HMAC signature for the vault ciphertext."""
    sig = _compute_hmac(raw_ciphertext, key)
    record = {"version": SIGNATURE_VERSION, "alg": "hmac-sha256", "sig": sig}
    path = _sigs_path(vault_name)
    path.write_text(json.dumps(record, indent=2))
    return sig


def verify_vault(vault_name: str, raw_ciphertext: bytes, key: bytes) -> bool:
    """Verify the stored HMAC signature against the vault ciphertext.

    Returns True if valid, False if signature file is missing.
    Raises SignError on tamper detection.
    """
    path = _sigs_path(vault_name)
    if not path.exists():
        return False
    record = json.loads(path.read_text())
    expected = _compute_hmac(raw_ciphertext, key)
    if not hmac.compare_digest(expected, record["sig"]):
        raise SignError(
            f"Signature mismatch for vault '{vault_name}': contents may have been tampered with."
        )
    return True


def delete_signature(vault_name: str) -> bool:
    """Remove the signature file for a vault. Returns True if deleted."""
    path = _sigs_path(vault_name)
    if path.exists():
        path.unlink()
        return True
    return False


def signature_info(vault_name: str) -> dict | None:
    """Return the raw signature record dict, or None if absent."""
    path = _sigs_path(vault_name)
    if not path.exists():
        return None
    return json.loads(path.read_text())
