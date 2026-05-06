"""Watch a .env file for changes and auto-lock on modification."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Callable, Optional


class WatchError(Exception):
    """Raised when a watch operation fails."""


def _file_hash(path: Path) -> str:
    """Return the SHA-256 hex digest of a file's contents."""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def watch_env(
    env_path: Path,
    on_change: Callable[[Path], None],
    *,
    interval: float = 1.0,
    max_iterations: Optional[int] = None,
) -> None:
    """Poll *env_path* every *interval* seconds and call *on_change* when it changes.

    Parameters
    ----------
    env_path:
        Path to the .env file to monitor.
    on_change:
        Callback invoked with *env_path* whenever a change is detected.
    interval:
        Polling interval in seconds.
    max_iterations:
        Stop after this many iterations (useful for testing; ``None`` runs forever).
    """
    if not env_path.exists():
        raise WatchError(f"File not found: {env_path}")

    last_hash = _file_hash(env_path)
    iterations = 0

    while max_iterations is None or iterations < max_iterations:
        time.sleep(interval)
        iterations += 1

        if not env_path.exists():
            raise WatchError(f"File disappeared during watch: {env_path}")

        current_hash = _file_hash(env_path)
        if current_hash != last_hash:
            last_hash = current_hash
            on_change(env_path)
