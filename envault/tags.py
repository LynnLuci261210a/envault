"""Tag management for vault versions — attach labels like 'production' or 'staging' to specific versions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


def _tags_path(vault_name: str, base_dir: Optional[Path] = None) -> Path:
    root = base_dir or Path(".envault")
    return root / vault_name / "tags.json"


def _load_tags(vault_name: str, base_dir: Optional[Path] = None) -> dict[str, int]:
    path = _tags_path(vault_name, base_dir)
    if not path.exists():
        return {}
    with path.open("r") as f:
        return json.load(f)


def _save_tags(vault_name: str, tags: dict[str, int], base_dir: Optional[Path] = None) -> None:
    path = _tags_path(vault_name, base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(tags, f, indent=2)


def set_tag(vault_name: str, tag: str, version: int, base_dir: Optional[Path] = None) -> None:
    """Associate a tag label with a version number."""
    tags = _load_tags(vault_name, base_dir)
    tags[tag] = version
    _save_tags(vault_name, tags, base_dir)


def get_tag(vault_name: str, tag: str, base_dir: Optional[Path] = None) -> Optional[int]:
    """Return the version number for a tag, or None if not set."""
    tags = _load_tags(vault_name, base_dir)
    return tags.get(tag)


def delete_tag(vault_name: str, tag: str, base_dir: Optional[Path] = None) -> bool:
    """Remove a tag. Returns True if it existed, False otherwise."""
    tags = _load_tags(vault_name, base_dir)
    if tag not in tags:
        return False
    del tags[tag]
    _save_tags(vault_name, tags, base_dir)
    return True


def list_tags(vault_name: str, base_dir: Optional[Path] = None) -> dict[str, int]:
    """Return all tags and their associated version numbers."""
    return _load_tags(vault_name, base_dir)
