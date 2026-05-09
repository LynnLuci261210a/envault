"""Compare two vault versions or named snapshots side-by-side."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from envault.crypto import load_key, decrypt
from envault.diff import parse_env, diff_envs, DiffResult
from envault.history import list_versions, get_version
from envault.snapshot import get_snapshot
from envault.vault import load_vault


class CompareError(Exception):
    """Raised when a comparison cannot be performed."""


@dataclass
class CompareResult:
    vault_name: str
    ref_a: str
    ref_b: str
    diff: DiffResult
    labels: tuple[str, str] = field(default_factory=lambda: ("a", "b"))

    def has_changes(self) -> bool:
        return self.diff.has_changes()

    def summary(self) -> str:
        return (
            f"Comparing {self.vault_name!r}: {self.ref_a} → {self.ref_b}\n"
            + self.diff.summary()
        )


def _resolve_ref(vault_name: str, ref: str, key_path: str) -> str:
    """Decrypt and return plaintext env content for a version or snapshot ref."""
    key = load_key(key_path)

    # Try snapshot first
    snap = get_snapshot(vault_name, ref)
    if snap is not None:
        version = snap["version"]
    elif ref.isdigit():
        version = int(ref)
    else:
        raise CompareError(
            f"Unknown ref {ref!r}: not a snapshot name or integer version number."
        )

    entry = get_version(vault_name, version)
    if entry is None:
        raise CompareError(f"Version {version} not found in vault {vault_name!r}.")

    ciphertext = bytes.fromhex(entry["ciphertext"])
    return decrypt(ciphertext, key).decode()


def compare_refs(
    vault_name: str,
    ref_a: str,
    ref_b: str,
    key_path: str,
) -> CompareResult:
    """Compare two refs (version numbers or snapshot names) within a vault."""
    text_a = _resolve_ref(vault_name, ref_a, key_path)
    text_b = _resolve_ref(vault_name, ref_b, key_path)

    env_a = parse_env(text_a)
    env_b = parse_env(text_b)
    diff = diff_envs(env_a, env_b)

    return CompareResult(
        vault_name=vault_name,
        ref_a=ref_a,
        ref_b=ref_b,
        diff=diff,
        labels=(ref_a, ref_b),
    )
