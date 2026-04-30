"""Vault management: read, write, and list encrypted .env vault files."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from envault.crypto import decrypt, encrypt, load_key

DEFAULT_VAULT_DIR = Path(".envault")
VAULT_EXTENSION = ".vault"


def _vault_path(name: str, vault_dir: Path = DEFAULT_VAULT_DIR) -> Path:
    """Return the path for a named vault file."""
    safe_name = name.replace("/", "_").strip("_")
    return vault_dir / f"{safe_name}{VAULT_EXTENSION}"


def save_vault(
    name: str,
    env_content: str,
    key_path: Path,
    vault_dir: Path = DEFAULT_VAULT_DIR,
    passphrase: Optional[str] = None,
) -> Path:
    """Encrypt env_content and save it as a named vault file."""
    vault_dir.mkdir(parents=True, exist_ok=True)
    key = load_key(key_path, passphrase=passphrase)
    ciphertext = encrypt(env_content.encode(), key)

    metadata = {
        "name": name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "ciphertext": ciphertext.hex(),
    }

    path = _vault_path(name, vault_dir)
    path.write_text(json.dumps(metadata, indent=2))
    return path


def load_vault(
    name: str,
    key_path: Path,
    vault_dir: Path = DEFAULT_VAULT_DIR,
    passphrase: Optional[str] = None,
) -> str:
    """Load and decrypt a named vault file, returning the plaintext env content."""
    path = _vault_path(name, vault_dir)
    if not path.exists():
        raise FileNotFoundError(f"Vault '{name}' not found at {path}")

    metadata = json.loads(path.read_text())
    key = load_key(key_path, passphrase=passphrase)
    ciphertext = bytes.fromhex(metadata["ciphertext"])
    return decrypt(ciphertext, key).decode()


def list_vaults(vault_dir: Path = DEFAULT_VAULT_DIR) -> list[dict]:
    """List all vault files in the vault directory with metadata."""
    if not vault_dir.exists():
        return []

    vaults = []
    for path in sorted(vault_dir.glob(f"*{VAULT_EXTENSION}")):
        try:
            metadata = json.loads(path.read_text())
            vaults.append({
                "name": metadata.get("name", path.stem),
                "created_at": metadata.get("created_at", "unknown"),
                "path": str(path),
            })
        except (json.JSONDecodeError, KeyError):
            vaults.append({"name": path.stem, "created_at": "unknown", "path": str(path)})
    return vaults


def delete_vault(name: str, vault_dir: Path = DEFAULT_VAULT_DIR) -> bool:
    """Delete a named vault file. Returns True if deleted, False if not found."""
    path = _vault_path(name, vault_dir)
    if path.exists():
        path.unlink()
        return True
    return False
