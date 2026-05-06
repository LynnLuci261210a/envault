"""CLI commands for managing envault lifecycle hooks."""

from __future__ import annotations

from pathlib import Path

import click

from envault.hooks import HookError, delete_hook, get_hook, list_hooks, set_hook

VAULT_DIR = Path(".")


@click.group("hook")
def hook_cmd() -> None:
    """Manage pre/post lock and unlock hooks."""


@hook_cmd.command("set")
@click.argument("event")
@click.argument("command")
def hook_set(event: str, command: str) -> None:
    """Register COMMAND to run on EVENT.

    EVENT must be one of: pre-lock, post-lock, pre-unlock, post-unlock.
    """
    try:
        set_hook(VAULT_DIR, event, command)
        click.echo(f"Hook '{event}' set to: {command}")
    except HookError as exc:
        raise click.ClickException(str(exc)) from exc


@hook_cmd.command("get")
@click.argument("event")
def hook_get(event: str) -> None:
    """Print the command registered for EVENT."""
    command = get_hook(VAULT_DIR, event)
    if command is None:
        click.echo(f"No hook registered for '{event}'.")
    else:
        click.echo(command)


@hook_cmd.command("delete")
@click.argument("event")
def hook_delete(event: str) -> None:
    """Remove the hook for EVENT."""
    removed = delete_hook(VAULT_DIR, event)
    if removed:
        click.echo(f"Hook '{event}' deleted.")
    else:
        click.echo(f"No hook registered for '{event}'.")


@hook_cmd.command("list")
def hook_list() -> None:
    """List all registered hooks."""
    hooks = list_hooks(VAULT_DIR)
    if not hooks:
        click.echo("No hooks registered.")
        return
    for event, command in sorted(hooks.items()):
        click.echo(f"{event}: {command}")
