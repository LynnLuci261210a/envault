"""Key rotation: re-encrypt a vault under a new key."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from envault.crypto import decrypt, encrypt, generate_key, load_key, save_key
from envault.vault import load_vault, save_vault
from envault.audit import record_event


class RotationError(Exception):
    """Raised when key rotation fails."""


def rotate_key(
    vault_name: str,
    old_key_path: Path,
    new_key_path: Optional[Path] = None,
    passphrase: Optional[str] = None,
    *,
    vault_dir: Optional[Path] = None,
    keys_dir: Optional[Path] = None,
) -> Path:
    """Re-encrypt *vault_name* under a freshly generated key.

    Parameters
    ----------
    vault_name:
        Name of the vault to rotate.
    old_key_path:
        Path to the current encryption key file.
    new_key_path:
        Destination for the new key file.  Defaults to *old_key_path*
        (overwrites in-place after successful rotation).
    passphrase:
        Optional passphrase used to derive the new key.
    vault_dir / keys_dir:
        Override directories (forwarded to vault helpers).

    Returns
    -------
    Path
        Path where the new key was saved.
    """
    # Load current vault payload
    try:
        vault = load_vault(vault_name, vault_dir=vault_dir)
    except FileNotFoundError as exc:
        raise RotationError(f"Vault '{vault_name}' not found.") from exc

    old_key = load_key(old_key_path)

    # Decrypt existing ciphertext
    try:
        plaintext: bytes = decrypt(vault["ciphertext"], old_key)
    except Exception as exc:
        raise RotationError("Failed to decrypt vault with the provided key.") from exc

    # Generate new key and re-encrypt
    new_key = generate_key(passphrase=passphrase)
    new_ciphertext = encrypt(plaintext, new_key)

    # Persist updated vault
    vault["ciphertext"] = new_ciphertext
    save_vault(vault_name, vault, vault_dir=vault_dir)

    # Save new key
    dest = new_key_path or old_key_path
    save_key(new_key, dest)

    record_event(
        vault_name,
        "rotate",
        version=vault.get("version"),
        detail=f"key rotated -> {dest}",
    )

    return dest
