"""Pre/post lock and unlock hook support for envault."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import List, Optional

HOOKS_FILE = ".envault-hooks.json"


class HookError(Exception):
    """Raised when a hook script fails."""


def _hooks_path(vault_dir: Path) -> Path:
    return vault_dir / HOOKS_FILE


def _load_hooks(vault_dir: Path) -> dict:
    path = _hooks_path(vault_dir)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_hooks(vault_dir: Path, hooks: dict) -> None:
    path = _hooks_path(vault_dir)
    path.write_text(json.dumps(hooks, indent=2))


def set_hook(vault_dir: Path, event: str, command: str) -> None:
    """Register a shell command to run on the given event.

    Supported events: pre-lock, post-lock, pre-unlock, post-unlock.
    """
    valid_events = {"pre-lock", "post-lock", "pre-unlock", "post-unlock"}
    if event not in valid_events:
        raise HookError(f"Unknown event '{event}'. Valid events: {sorted(valid_events)}")
    hooks = _load_hooks(vault_dir)
    hooks[event] = command
    _save_hooks(vault_dir, hooks)


def get_hook(vault_dir: Path, event: str) -> Optional[str]:
    """Return the command registered for the given event, or None."""
    hooks = _load_hooks(vault_dir)
    return hooks.get(event)


def delete_hook(vault_dir: Path, event: str) -> bool:
    """Remove a hook. Returns True if it existed, False otherwise."""
    hooks = _load_hooks(vault_dir)
    if event not in hooks:
        return False
    del hooks[event]
    _save_hooks(vault_dir, hooks)
    return True


def list_hooks(vault_dir: Path) -> dict:
    """Return all registered hooks as {event: command}."""
    return _load_hooks(vault_dir)


def run_hook(vault_dir: Path, event: str, env: Optional[dict] = None) -> None:
    """Execute the hook for the given event if one is registered.

    Raises HookError if the command exits with a non-zero status.
    """
    command = get_hook(vault_dir, event)
    if command is None:
        return
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        raise HookError(
            f"Hook '{event}' failed (exit {result.returncode}):\n{result.stderr.strip()}"
        )
