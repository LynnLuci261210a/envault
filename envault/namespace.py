"""Namespace support: group vaults under logical namespaces."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

ENVAULT_DIR = Path(".envault")


class NamespaceError(Exception):
    """Raised on namespace operation failures."""


def _namespaces_path() -> Path:
    return ENVAULT_DIR / "namespaces.json"


def _load_namespaces() -> Dict[str, List[str]]:
    p = _namespaces_path()
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_namespaces(data: Dict[str, List[str]]) -> None:
    p = _namespaces_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2))


def add_vault(namespace: str, vault_name: str) -> None:
    """Add a vault to a namespace."""
    if not namespace.strip():
        raise NamespaceError("Namespace name must not be empty.")
    data = _load_namespaces()
    vaults = data.setdefault(namespace, [])
    if vault_name not in vaults:
        vaults.append(vault_name)
    _save_namespaces(data)


def remove_vault(namespace: str, vault_name: str) -> bool:
    """Remove a vault from a namespace. Returns True if removed."""
    data = _load_namespaces()
    vaults = data.get(namespace, [])
    if vault_name not in vaults:
        return False
    vaults.remove(vault_name)
    if not vaults:
        del data[namespace]
    _save_namespaces(data)
    return True


def list_vaults(namespace: str) -> List[str]:
    """Return all vault names under a namespace."""
    return list(_load_namespaces().get(namespace, []))


def list_namespaces() -> List[str]:
    """Return all namespace names."""
    return sorted(_load_namespaces().keys())


def get_namespace(vault_name: str) -> Optional[str]:
    """Return the namespace a vault belongs to, or None."""
    for ns, vaults in _load_namespaces().items():
        if vault_name in vaults:
            return ns
    return None


def delete_namespace(namespace: str) -> bool:
    """Delete an entire namespace. Returns True if it existed."""
    data = _load_namespaces()
    if namespace not in data:
        return False
    del data[namespace]
    _save_namespaces(data)
    return True
