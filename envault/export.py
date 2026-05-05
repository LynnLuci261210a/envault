"""Export decrypted vault contents to various formats."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional


def _parse_env_pairs(env_text: str) -> Dict[str, str]:
    """Parse env file text into a key-value dictionary."""
    pairs: Dict[str, str] = {}
    for line in env_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        pairs[key.strip()] = value.strip()
    return pairs


def to_dotenv(env_text: str, output_path: Optional[Path] = None) -> str:
    """Return (and optionally write) the env content as a .env file."""
    content = env_text if env_text.endswith("\n") else env_text + "\n"
    if output_path is not None:
        output_path.write_text(content, encoding="utf-8")
    return content


def to_json(env_text: str, output_path: Optional[Path] = None, indent: int = 2) -> str:
    """Return (and optionally write) the env content as a JSON object."""
    pairs = _parse_env_pairs(env_text)
    content = json.dumps(pairs, indent=indent) + "\n"
    if output_path is not None:
        output_path.write_text(content, encoding="utf-8")
    return content


def to_shell_export(env_text: str, output_path: Optional[Path] = None) -> str:
    """Return (and optionally write) the env content as shell export statements."""
    pairs = _parse_env_pairs(env_text)
    lines = [f'export {k}="{v}"' for k, v in pairs.items()]
    content = "\n".join(lines) + "\n"
    if output_path is not None:
        output_path.write_text(content, encoding="utf-8")
    return content


SUPPORTED_FORMATS = ("dotenv", "json", "shell")


def export_env(
    env_text: str,
    fmt: str,
    output_path: Optional[Path] = None,
) -> str:
    """Dispatch to the appropriate export formatter.

    Args:
        env_text: Decrypted .env file contents.
        fmt: One of 'dotenv', 'json', 'shell'.
        output_path: Optional file path to write the result to.

    Returns:
        The formatted string.

    Raises:
        ValueError: If *fmt* is not a supported format.
    """
    if fmt == "dotenv":
        return to_dotenv(env_text, output_path)
    if fmt == "json":
        return to_json(env_text, output_path)
    if fmt == "shell":
        return to_shell_export(env_text, output_path)
    raise ValueError(
        f"Unsupported format {fmt!r}. Choose one of: {', '.join(SUPPORTED_FORMATS)}"
    )
