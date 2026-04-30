"""Encryption and decryption utilities for envault using Fernet symmetric encryption."""

import os
import base64
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


KEY_FILE = ".envault.key"
SALT_SIZE = 16
ITERATIONS = 390_000


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    """Derive a Fernet-compatible key from a passphrase and salt."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))


def generate_key(passphrase: str | None = None) -> bytes:
    """Generate a new encryption key, optionally derived from a passphrase."""
    if passphrase:
        salt = os.urandom(SALT_SIZE)
        key = _derive_key(passphrase, salt)
        return salt + base64.urlsafe_b64decode(key)
    return Fernet.generate_key()


def save_key(key: bytes, path: str = KEY_FILE) -> None:
    """Persist the encryption key to a file."""
    key_path = Path(path)
    key_path.write_bytes(base64.urlsafe_b64encode(key))
    key_path.chmod(0o600)


def load_key(path: str = KEY_FILE) -> bytes:
    """Load the encryption key from a file."""
    key_path = Path(path)
    if not key_path.exists():
        raise FileNotFoundError(f"Key file not found: {path}. Run `envault init` first.")
    return base64.urlsafe_b64decode(key_path.read_bytes())


def encrypt(data: bytes, key: bytes) -> bytes:
    """Encrypt raw bytes using the provided key."""
    if len(key) > 32:
        # Key was derived with a salt prefix; strip the salt
        fernet_key = base64.urlsafe_b64encode(key[SALT_SIZE:])
    else:
        fernet_key = key
    f = Fernet(fernet_key)
    return f.encrypt(data)


def decrypt(token: bytes, key: bytes) -> bytes:
    """Decrypt a Fernet token using the provided key."""
    if len(key) > 32:
        fernet_key = base64.urlsafe_b64encode(key[SALT_SIZE:])
    else:
        fernet_key = key
    try:
        f = Fernet(fernet_key)
        return f.decrypt(token)
    except InvalidToken as exc:
        raise ValueError("Decryption failed: invalid key or corrupted data.") from exc
