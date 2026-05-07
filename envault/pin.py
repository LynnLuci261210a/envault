"""Pin management: lock a vault to a specific version for reproducible deployments."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

PIN_FILE = ".envault-pins.json"


class PinError(Exception):
    pass


def _pins_path(vault_dir: str = ".") -> Path:
    return Path(vault_dir) / PIN_FILE


def _load_pins(vault_dir: str = ".") -> dict:
    p = _pins_path(vault_dir)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_pins(pins: dict, vault_dir: str = ".") -> None:
    _pins_path(vault_dir).write_text(json.dumps(pins, indent=2))


def set_pin(vault_name: str, version: int, vault_dir: str = ".") -> None:
    """Pin a vault to a specific version number."""
    if version < 1:
        raise PinError(f"Version must be >= 1, got {version}")
    pins = _load_pins(vault_dir)
    pins[vault_name] = version
    _save_pins(pins, vault_dir)


def get_pin(vault_name: str, vault_dir: str = ".") -> Optional[int]:
    """Return the pinned version for a vault, or None if not pinned."""
    return _load_pins(vault_dir).get(vault_name)


def delete_pin(vault_name: str, vault_dir: str = ".") -> bool:
    """Remove a pin. Returns True if it existed, False otherwise."""
    pins = _load_pins(vault_dir)
    if vault_name not in pins:
        return False
    del pins[vault_name]
    _save_pins(pins, vault_dir)
    return True


def list_pins(vault_dir: str = ".") -> dict[str, int]:
    """Return all pinned vaults as {vault_name: version}."""
    return dict(_load_pins(vault_dir))
