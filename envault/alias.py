"""Vault alias management — map short names to vault names."""

from __future__ import annotations

import json
from pathlib import Path


class AliasError(Exception):
    """Raised for alias-related failures."""


def _aliases_path(vault_dir: Path) -> Path:
    return vault_dir / ".envault" / "aliases.json"


def _load_aliases(vault_dir: Path) -> dict[str, str]:
    path = _aliases_path(vault_dir)
    if not path.exists():
        return {}
    with path.open() as fh:
        return json.load(fh)


def _save_aliases(vault_dir: Path, aliases: dict[str, str]) -> None:
    path = _aliases_path(vault_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump(aliases, fh, indent=2)


def set_alias(vault_dir: Path, alias: str, vault_name: str) -> None:
    """Map *alias* to *vault_name*."""
    if not alias or not alias.isidentifier():
        raise AliasError(f"Invalid alias name: {alias!r}. Must be a valid identifier.")
    aliases = _load_aliases(vault_dir)
    aliases[alias] = vault_name
    _save_aliases(vault_dir, aliases)


def get_alias(vault_dir: Path, alias: str) -> str | None:
    """Return the vault name for *alias*, or None if not set."""
    return _load_aliases(vault_dir).get(alias)


def delete_alias(vault_dir: Path, alias: str) -> bool:
    """Remove *alias*. Returns True if it existed, False otherwise."""
    aliases = _load_aliases(vault_dir)
    if alias not in aliases:
        return False
    del aliases[alias]
    _save_aliases(vault_dir, aliases)
    return True


def list_aliases(vault_dir: Path) -> dict[str, str]:
    """Return a copy of all defined aliases."""
    return dict(_load_aliases(vault_dir))


def resolve_alias(vault_dir: Path, name: str) -> str:
    """Return the vault name for *name*, resolving alias if necessary."""
    resolved = get_alias(vault_dir, name)
    return resolved if resolved is not None else name
