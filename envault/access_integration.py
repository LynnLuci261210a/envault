"""Integration helpers: enforce access checks within vault operations."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from envault.access import AccessError, has_permission


class PermissionDenied(Exception):
    """Raised when a principal lacks the required permission."""


def require_permission(
    vault_name: str,
    principal: str,
    permission: str,
    base_dir: Optional[Path] = None,
) -> None:
    """Raise PermissionDenied if principal lacks permission on vault."""
    if not has_permission(vault_name, principal, permission, base_dir=base_dir):
        raise PermissionDenied(
            f"'{principal}' does not have '{permission}' access to vault '{vault_name}'."
        )


def check_read(vault_name: str, principal: str, base_dir: Optional[Path] = None) -> bool:
    """Return True if principal may read the vault."""
    return has_permission(vault_name, principal, "read", base_dir=base_dir)


def check_write(vault_name: str, principal: str, base_dir: Optional[Path] = None) -> bool:
    """Return True if principal may write to the vault."""
    return has_permission(vault_name, principal, "write", base_dir=base_dir)


def check_admin(vault_name: str, principal: str, base_dir: Optional[Path] = None) -> bool:
    """Return True if principal has admin rights on the vault."""
    return has_permission(vault_name, principal, "admin", base_dir=base_dir)


def enforce_read(vault_name: str, principal: str, base_dir: Optional[Path] = None) -> None:
    """Enforce read permission or raise PermissionDenied."""
    require_permission(vault_name, principal, "read", base_dir=base_dir)


def enforce_write(vault_name: str, principal: str, base_dir: Optional[Path] = None) -> None:
    """Enforce write permission or raise PermissionDenied."""
    require_permission(vault_name, principal, "write", base_dir=base_dir)


def enforce_admin(vault_name: str, principal: str, base_dir: Optional[Path] = None) -> None:
    """Enforce admin permission or raise PermissionDenied."""
    require_permission(vault_name, principal, "admin", base_dir=base_dir)
