"""Profile management: named environment profiles (e.g. dev, staging, prod)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


class ProfileError(Exception):
    pass


def _profiles_path(vault_dir: Path) -> Path:
    return vault_dir / ".envault" / "profiles.json"


def _load_profiles(vault_dir: Path) -> Dict[str, str]:
    path = _profiles_path(vault_dir)
    if not path.exists():
        return {}
    with path.open("r") as f:
        return json.load(f)


def _save_profiles(vault_dir: Path, profiles: Dict[str, str]) -> None:
    path = _profiles_path(vault_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(profiles, f, indent=2)


def set_profile(vault_dir: Path, name: str, vault_name: str) -> None:
    """Associate a profile name with a vault name."""
    profiles = _load_profiles(vault_dir)
    profiles[name] = vault_name
    _save_profiles(vault_dir, profiles)


def get_profile(vault_dir: Path, name: str) -> Optional[str]:
    """Return the vault name for a profile, or None if not set."""
    return _load_profiles(vault_dir).get(name)


def delete_profile(vault_dir: Path, name: str) -> bool:
    """Delete a profile. Returns True if it existed, False otherwise."""
    profiles = _load_profiles(vault_dir)
    if name not in profiles:
        return False
    del profiles[name]
    _save_profiles(vault_dir, profiles)
    return True


def list_profiles(vault_dir: Path) -> List[Dict[str, str]]:
    """Return all profiles as a list of {name, vault} dicts."""
    profiles = _load_profiles(vault_dir)
    return [{"name": k, "vault": v} for k, v in sorted(profiles.items())]
