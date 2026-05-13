"""Import .env files from external sources into an envault vault."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from envault.crypto import load_key, encrypt
from envault.vault import save_vault, load_vault
from envault.history import record_version
from envault.audit import record_event
from envault.diff import parse_env, diff_envs, has_changes


class ImportError(Exception):  # noqa: A001
    """Raised when an import operation fails."""


def import_env_file(
    env_path: str | Path,
    vault_name: str,
    key_path: str | Path,
    *,
    base_dir: str | Path = ".",
    note: Optional[str] = None,
    skip_unchanged: bool = True,
) -> dict:
    """Import a .env file into the named vault.

    Returns a dict with keys: version, changed, diff_summary.
    Raises ImportError on any failure.
    """
    env_path = Path(env_path)
    if not env_path.exists():
        raise ImportError(f"Source file not found: {env_path}")

    raw = env_path.read_text(encoding="utf-8")

    key = load_key(key_path)

    # Check for changes vs current vault content
    changed = True
    diff_summary = ""
    try:
        existing = load_vault(vault_name, base_dir=base_dir)
        from envault.crypto import decrypt
        current_raw = decrypt(existing["ciphertext"], key).decode("utf-8")
        result = diff_envs(parse_env(current_raw), parse_env(raw))
        changed = has_changes(result)
        diff_summary = result.summary() if hasattr(result, "summary") else ""
    except FileNotFoundError:
        diff_summary = "new vault"
    except Exception:
        pass  # treat as changed if we can't compare

    if skip_unchanged and not changed:
        return {"version": None, "changed": False, "diff_summary": diff_summary}

    ciphertext = encrypt(raw.encode("utf-8"), key)
    save_vault(vault_name, {"ciphertext": ciphertext}, base_dir=base_dir)

    version = record_version(
        vault_name,
        ciphertext,
        message=note or f"imported from {env_path.name}",
        base_dir=base_dir,
    )

    record_event(
        vault_name,
        "import",
        version=version,
        detail=f"source={env_path}",
        base_dir=base_dir,
    )

    return {"version": version, "changed": True, "diff_summary": diff_summary}
