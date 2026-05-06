"""Helpers to fire lifecycle hooks around vault lock/unlock operations."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Generator

import click

from envault.hooks import HookError, run_hook


@contextmanager
def hook_lifecycle(
    vault_dir: Path,
    operation: str,
    *,
    abort_on_pre_failure: bool = True,
) -> Generator[None, None, None]:
    """Context manager that fires pre-<op> before and post-<op> after the block.

    Parameters
    ----------
    vault_dir:
        Directory containing the .envault-hooks.json file.
    operation:
        Either ``'lock'`` or ``'unlock'``.
    abort_on_pre_failure:
        If True (default), a failing pre-hook aborts the operation by
        re-raising HookError.  Set to False to continue despite errors.
    """
    pre_event = f"pre-{operation}"
    post_event = f"post-{operation}"

    try:
        run_hook(vault_dir, pre_event)
    except HookError as exc:
        if abort_on_pre_failure:
            raise
        click.echo(f"Warning: {exc}", err=True)

    yield

    try:
        run_hook(vault_dir, post_event)
    except HookError as exc:
        # Post-hook failure is always a warning — the operation already finished.
        click.echo(f"Warning: post-hook '{post_event}' failed: {exc}", err=True)


def fire_hook(vault_dir: Path, event: str, *, silent: bool = False) -> bool:
    """Run a single hook event and return True on success.

    Parameters
    ----------
    vault_dir:
        Directory containing the hooks file.
    event:
        The event name to fire.
    silent:
        If True, swallow HookError and return False instead of raising.
    """
    try:
        run_hook(vault_dir, event)
        return True
    except HookError as exc:
        if silent:
            return False
        raise
