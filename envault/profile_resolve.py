"""Helpers to resolve a vault name from a profile or direct name."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from envault.profile import get_profile


class ResolveError(Exception):
    pass


def resolve_vault_name(
    name: str,
    vault_dir: Path,
    *,
    allow_profile: bool = True,
) -> str:
    """Return a vault name, resolving profile aliases if needed.

    If *name* matches a profile alias and ``allow_profile`` is True the
    associated vault name is returned.  Otherwise *name* is returned as-is.
    """
    if allow_profile:
        resolved = get_profile(vault_dir, name)
        if resolved is not None:
            return resolved
    return name


def resolve_or_raise(
    name: str,
    vault_dir: Path,
    *,
    allow_profile: bool = True,
) -> str:
    """Like :func:`resolve_vault_name` but raises :exc:`ResolveError` when
    *name* is empty after resolution.
    """
    resolved = resolve_vault_name(name, vault_dir, allow_profile=allow_profile)
    if not resolved:
        raise ResolveError(f"Cannot resolve vault name from '{name}'")
    return resolved
