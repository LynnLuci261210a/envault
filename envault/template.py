"""Template rendering: substitute .env.vault values into template files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional


class TemplateError(Exception):
    """Raised when template rendering fails."""


_PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


def render_string(template: str, env: dict[str, str], strict: bool = True) -> str:
    """Replace {{KEY}} placeholders in *template* with values from *env*.

    Args:
        template: Raw template text.
        env:      Mapping of env-var names to values.
        strict:   If True, raise TemplateError for any unresolved placeholder.

    Returns:
        Rendered string with all placeholders replaced.
    """
    missing: list[str] = []

    def _replace(match: re.Match) -> str:  # type: ignore[type-arg]
        key = match.group(1)
        if key in env:
            return env[key]
        missing.append(key)
        return match.group(0)  # leave placeholder intact when not strict

    result = _PLACEHOLDER.sub(_replace, template)

    if strict and missing:
        raise TemplateError(
            f"Unresolved placeholders: {', '.join(sorted(set(missing)))}"
        )

    return result


def render_file(
    src: Path,
    env: dict[str, str],
    dest: Optional[Path] = None,
    strict: bool = True,
) -> str:
    """Read *src*, render placeholders, optionally write to *dest*.

    Returns:
        The rendered content as a string.
    """
    if not src.exists():
        raise TemplateError(f"Template file not found: {src}")

    raw = src.read_text(encoding="utf-8")
    rendered = render_string(raw, env, strict=strict)

    if dest is not None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(rendered, encoding="utf-8")

    return rendered


def list_placeholders(template: str) -> list[str]:
    """Return sorted unique placeholder names found in *template*."""
    return sorted(set(_PLACEHOLDER.findall(template)))
