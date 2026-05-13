"""High-level helpers that integrate signing into the lock/unlock workflow."""

import json
from typing import Optional

from envault.sign import SignError, sign_vault, verify_vault


def sign_after_lock(vault_name: str, vault_data: dict, key: bytes) -> str:
    """Sign a vault immediately after locking. Returns the hex signature."""
    raw = json.dumps(vault_data).encode()
    return sign_vault(vault_name, raw, key)


def verify_before_unlock(
    vault_name: str,
    vault_data: dict,
    key: bytes,
    *,
    strict: bool = False,
) -> Optional[bool]:
    """Verify a vault's signature before unlocking.

    Args:
        vault_name: Name of the vault.
        vault_data: Raw vault dict (as stored on disk).
        key: Symmetric key bytes used for HMAC.
        strict: If True, raise SignError when no signature file exists.

    Returns:
        True if signature verified, False if no signature present and not strict.

    Raises:
        SignError: On tamper detection or when strict=True and no sig file.
    """
    raw = json.dumps(vault_data).encode()
    present = verify_vault(vault_name, raw, key)
    if not present and strict:
        raise SignError(
            f"Vault '{vault_name}' has no signature. "
            "Run 'envault sign create <vault>' to sign it first."
        )
    return present


def is_signed(vault_name: str) -> bool:
    """Return True if a signature file exists for the given vault."""
    from envault.sign import signature_info
    return signature_info(vault_name) is not None


def signing_summary(vault_name: str) -> str:
    """Return a human-readable one-line summary of the vault's signing status."""
    from envault.sign import signature_info
    info = signature_info(vault_name)
    if info is None:
        return f"[{vault_name}] unsigned"
    sig_short = info.get("sig", "")[:12]
    alg = info.get("alg", "unknown")
    return f"[{vault_name}] signed ({alg}) sig={sig_short}..."
