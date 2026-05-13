"""Access control: manage per-vault read/write permissions for named principals."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

VALID_PERMISSIONS = {"read", "write", "admin"}


class AccessError(Exception):
    pass


def _access_path(vault_name: str, base_dir: Optional[Path] = None) -> Path:
    root = base_dir or Path(".envault")
    return root / vault_name / "access.json"


def _load_acl(vault_name: str, base_dir: Optional[Path] = None) -> Dict[str, List[str]]:
    path = _access_path(vault_name, base_dir)
    if not path.exists():
        return {}
    with path.open("r") as fh:
        return json.load(fh)


def _save_acl(vault_name: str, acl: Dict[str, List[str]], base_dir: Optional[Path] = None) -> None:
    path = _access_path(vault_name, base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump(acl, fh, indent=2)


def grant(vault_name: str, principal: str, permission: str, base_dir: Optional[Path] = None) -> None:
    """Grant a permission to a principal on a vault."""
    if permission not in VALID_PERMISSIONS:
        raise AccessError(f"Invalid permission '{permission}'. Choose from: {sorted(VALID_PERMISSIONS)}")
    acl = _load_acl(vault_name, base_dir)
    perms = set(acl.get(principal, []))
    perms.add(permission)
    acl[principal] = sorted(perms)
    _save_acl(vault_name, acl, base_dir)


def revoke(vault_name: str, principal: str, permission: str, base_dir: Optional[Path] = None) -> bool:
    """Revoke a permission from a principal. Returns True if anything changed."""
    acl = _load_acl(vault_name, base_dir)
    perms = set(acl.get(principal, []))
    if permission not in perms:
        return False
    perms.discard(permission)
    if perms:
        acl[principal] = sorted(perms)
    else:
        acl.pop(principal, None)
    _save_acl(vault_name, acl, base_dir)
    return True


def get_permissions(vault_name: str, principal: str, base_dir: Optional[Path] = None) -> List[str]:
    """Return list of permissions for a principal."""
    acl = _load_acl(vault_name, base_dir)
    return acl.get(principal, [])


def list_principals(vault_name: str, base_dir: Optional[Path] = None) -> Dict[str, List[str]]:
    """Return full ACL mapping for a vault."""
    return _load_acl(vault_name, base_dir)


def has_permission(vault_name: str, principal: str, permission: str, base_dir: Optional[Path] = None) -> bool:
    """Check whether a principal holds a specific permission."""
    perms = get_permissions(vault_name, principal, base_dir)
    return permission in perms or "admin" in perms
