"""CLI commands for pin management."""

from __future__ import annotations

import click

from .pin import PinError, delete_pin, get_pin, list_pins, set_pin


@click.group("pin")
def pin_cmd() -> None:
    """Pin vaults to specific versions for reproducible deployments."""


@pin_cmd.command("set")
@click.argument("vault_name")
@click.argument("version", type=int)
def pin_set(vault_name: str, version: int) -> None:
    """Pin VAULT_NAME to VERSION."""
    try:
        set_pin(vault_name, version)
        click.echo(f"Pinned '{vault_name}' to version {version}.")
    except PinError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@pin_cmd.command("get")
@click.argument("vault_name")
def pin_get(vault_name: str) -> None:
    """Show the pinned version for VAULT_NAME."""
    version = get_pin(vault_name)
    if version is None:
        click.echo(f"No pin set for '{vault_name}'.")
    else:
        click.echo(str(version))


@pin_cmd.command("delete")
@click.argument("vault_name")
def pin_delete(vault_name: str) -> None:
    """Remove the pin for VAULT_NAME."""
    removed = delete_pin(vault_name)
    if removed:
        click.echo(f"Pin for '{vault_name}' removed.")
    else:
        click.echo(f"No pin found for '{vault_name}'.")


@pin_cmd.command("list")
def pin_list() -> None:
    """List all pinned vaults."""
    pins = list_pins()
    if not pins:
        click.echo("No pins set.")
        return
    for name, version in sorted(pins.items()):
        click.echo(f"{name}: v{version}")
