"""High-level helpers integrating merge with vault history and snapshots."""
from __future__ import annotations

from typing import Optional

from envault.crypto import load_key, encrypt, decrypt
from envault.vault import load_vault, save_vault
from envault.history import record_version, list_versions
from envault.audit import record_event
from envault.merge import merge_envs, MergeResult, MergeError
from envault.snapshot_integration import snapshot_exists, resolve_snapshot_version


def merge_versions(
    vault_name: str,
    ref_ours: str,
    ref_theirs: str,
    key_file: str = ".envault.key",
    base_ref: Optional[str] = None,
    strategy: str = "ours",
) -> tuple[MergeResult, int]:
    """Merge two refs (version numbers or snapshot names) and save the result.

    Returns (MergeResult, new_version_number).
    """
    key = load_key(key_file)

    def _resolve(ref: str) -> int:
        if ref.isdigit():
            return int(ref)
        if snapshot_exists(vault_name, ref):
            return resolve_snapshot_version(vault_name, ref)
        raise MergeError(f"Cannot resolve ref {ref!r} for vault '{vault_name}'.")

    def _decrypt_version(v: int) -> str:
        data = load_vault(vault_name, v)
        return decrypt(data["ciphertext"], key)

    v_ours = _resolve(ref_ours)
    v_theirs = _resolve(ref_theirs)

    if base_ref is not None:
        v_base = _resolve(base_ref)
    else:
        versions = list_versions(vault_name)
        if not versions:
            raise MergeError(f"No versions found for vault '{vault_name}'.")
        v_base = versions[0]["version"]

    base_text = _decrypt_version(v_base)
    ours_text = _decrypt_version(v_ours)
    theirs_text = _decrypt_version(v_theirs)

    result = merge_envs(base_text, ours_text, theirs_text, strategy=strategy)

    merged_text = "\n".join(f"{k}={v}" for k, v in result.merged.items())
    ciphertext = encrypt(merged_text, key)
    new_version = record_version(vault_name, merged_text)
    save_vault(vault_name, new_version, {"ciphertext": ciphertext})
    record_event(
        vault_name,
        "merge",
        version=new_version,
    )

    return result, new_version


def can_fast_forward(vault_name: str, ref_ours: str, ref_theirs: str) -> bool:
    """Return True if one side has no changes relative to the base (fast-forward possible)."""
    versions = list_versions(vault_name)
    if len(versions) < 2:
        return True
    v_nums = sorted(v["version"] for v in versions)
    try:
        a = int(ref_ours) if ref_ours.isdigit() else None
        b = int(ref_theirs) if ref_theirs.isdigit() else None
    except (ValueError, AttributeError):
        return False
    if a is None or b is None:
        return False
    return a in v_nums and b in v_nums and abs(v_nums.index(a) - v_nums.index(b)) == 1
