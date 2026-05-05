"""Sharing support: export encrypted vault bundles for handoff."""

from __future__ import annotations

import json
import base64
from pathlib import Path
from typing import Optional

from envault.crypto import encrypt, decrypt, generate_key, save_key, load_key
from envault.vault import load_vault


class ShareError(Exception):
    """Raised when a share/import operation fails."""


def export_bundle(
    vault_name: str,
    vault_dir: Path,
    key_path: Path,
    passphrase: Optional[str] = None,
) -> bytes:
    """Return a self-contained JSON bundle (bytes) containing the vault
    re-encrypted with a one-time key derived from *passphrase* (or a
    freshly-generated random key when *passphrase* is None).

    The bundle is base64-encoded so it can be safely copied as text.
    """
    plaintext = load_vault(vault_name, vault_dir, key_path)
    env_bytes = plaintext.encode()

    share_key = generate_key(passphrase=passphrase)
    ciphertext = encrypt(env_bytes, share_key)

    bundle = {
        "vault": vault_name,
        "ciphertext": base64.b64encode(ciphertext).decode(),
        "has_passphrase": passphrase is not None,
    }
    if passphrase is None:
        bundle["key"] = base64.b64encode(share_key).decode()

    return json.dumps(bundle).encode()


def import_bundle(
    bundle_bytes: bytes,
    passphrase: Optional[str] = None,
) -> tuple[str, str]:
    """Parse *bundle_bytes* and return ``(vault_name, plaintext_env)``.

    Raises :class:`ShareError` on any decryption or format problem.
    """
    try:
        bundle = json.loads(bundle_bytes)
    except json.JSONDecodeError as exc:
        raise ShareError(f"Invalid bundle format: {exc}") from exc

    required = {"vault", "ciphertext", "has_passphrase"}
    if not required.issubset(bundle):
        raise ShareError("Bundle is missing required fields.")

    ciphertext = base64.b64decode(bundle["ciphertext"])

    if bundle["has_passphrase"]:
        if passphrase is None:
            raise ShareError("Bundle requires a passphrase but none was provided.")
        key = generate_key(passphrase=passphrase)
    else:
        if "key" not in bundle:
            raise ShareError("Bundle is missing the embedded key.")
        key = base64.b64decode(bundle["key"])

    try:
        plaintext = decrypt(ciphertext, key).decode()
    except Exception as exc:
        raise ShareError(f"Decryption failed — wrong passphrase or corrupted bundle: {exc}") from exc

    return bundle["vault"], plaintext
