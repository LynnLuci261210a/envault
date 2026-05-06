"""Search across vault keys and values."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from envault.vault import load_vault
from envault.crypto import load_key, decrypt


@dataclass
class SearchMatch:
    vault: str
    version: int
    key: str
    value: str
    match_in: str  # 'key' | 'value'

    def __str__(self) -> str:
        return f"[{self.vault}@v{self.version}] {self.key}={self.value}  (matched in {self.match_in})"


@dataclass
class SearchResult:
    matches: list[SearchMatch] = field(default_factory=list)

    @property
    def found(self) -> bool:
        return len(self.matches) > 0

    def summary(self) -> str:
        if not self.found:
            return "No matches found."
        lines = [str(m) for m in self.matches]
        return "\n".join(lines)


def _parse_env_pairs(content: str) -> dict[str, str]:
    pairs: dict[str, str] = {}
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        k, _, v = stripped.partition("=")
        pairs[k.strip()] = v.strip()
    return pairs


def search_vault(
    vault_name: str,
    query: str,
    key_dir: str = ".",
    *,
    keys_only: bool = False,
    case_sensitive: bool = False,
) -> SearchResult:
    """Search a vault's latest version for keys/values matching *query*."""
    result = SearchResult()

    try:
        vault_data = load_vault(vault_name, base_dir=key_dir)
    except FileNotFoundError:
        return result

    try:
        key = load_key(vault_name, base_dir=key_dir)
    except FileNotFoundError:
        return result

    version: int = vault_data.get("version", 0)
    ciphertext: Optional[str] = vault_data.get("ciphertext")
    if not ciphertext:
        return result

    try:
        plaintext = decrypt(ciphertext, key)
    except Exception:
        return result

    pairs = _parse_env_pairs(plaintext)
    needle = query if case_sensitive else query.lower()

    for k, v in pairs.items():
        k_cmp = k if case_sensitive else k.lower()
        v_cmp = v if case_sensitive else v.lower()

        if needle in k_cmp:
            result.matches.append(SearchMatch(vault_name, version, k, v, "key"))
        elif not keys_only and needle in v_cmp:
            result.matches.append(SearchMatch(vault_name, version, k, v, "value"))

    return result
