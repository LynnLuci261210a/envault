"""High-level helpers that integrate the watcher with audit and hooks."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from envault.audit import record_event
from envault.crypto import load_key
from envault.hook_runner import fire_hook
from envault.vault import save_vault
from envault.watch import WatchError, watch_env


def watched_lock(
    env_path: Path,
    vault_name: str,
    key_path: Path,
    *,
    interval: float = 2.0,
    max_iterations: Optional[int] = None,
    base_dir: Optional[Path] = None,
) -> None:
    """Watch *env_path* and re-encrypt into *vault_name* on every change.

    Fires ``pre-lock`` / ``post-lock`` hooks and records an audit event for
    each auto-lock cycle.

    Parameters
    ----------
    env_path:
        The plaintext .env file to monitor.
    vault_name:
        Vault to write encrypted contents into.
    key_path:
        Path to the encryption key file.
    interval:
        Polling interval in seconds.
    max_iterations:
        Cap on poll iterations (``None`` = infinite).
    base_dir:
        Base directory used for vault / audit / hook storage.
        Defaults to the current working directory.
    """
    key = load_key(key_path)
    _base = base_dir or Path(".")

    def _on_change(path: Path) -> None:
        fire_hook(vault_name, "pre-lock", base_dir=_base)
        plaintext = path.read_bytes()
        save_vault(vault_name, plaintext, key, base_dir=_base)
        record_event(vault_name, "auto-lock", base_dir=_base)
        fire_hook(vault_name, "post-lock", base_dir=_base)

    watch_env(env_path, _on_change, interval=interval, max_iterations=max_iterations)
