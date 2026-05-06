"""CLI commands for profile management."""

from __future__ import annotations

import click
from pathlib import Path

from envault.profile import (
    set_profile,
    get_profile,
    delete_profile,
    list_profiles,
)


@click.group("profile")
def profile_cmd():
    """Manage named environment profiles."""


@profile_cmd.command("set")
@click.argument("name")
@click.argument("vault")
@click.option("--dir", "vault_dir", default=".", help="Vault directory")
def profile_set(name: str, vault: str, vault_dir: str):
    """Associate PROFILE NAME with a VAULT name."""
    set_profile(Path(vault_dir), name, vault)
    click.echo(f"Profile '{name}' -> '{vault}'")


@profile_cmd.command("get")
@click.argument("name")
@click.option("--dir", "vault_dir", default=".", help="Vault directory")
def profile_get(name: str, vault_dir: str):
    """Show the vault associated with a profile NAME."""
    vault = get_profile(Path(vault_dir), name)
    if vault is None:
        click.echo(f"Profile '{name}' not found.", err=True)
        raise SystemExit(1)
    click.echo(vault)


@profile_cmd.command("delete")
@click.argument("name")
@click.option("--dir", "vault_dir", default=".", help="Vault directory")
def profile_delete(name: str, vault_dir: str):
    """Delete a profile by NAME."""
    removed = delete_profile(Path(vault_dir), name)
    if removed:
        click.echo(f"Deleted profile '{name}'.")
    else:
        click.echo(f"Profile '{name}' not found.", err=True)
        raise SystemExit(1)


@profile_cmd.command("list")
@click.option("--dir", "vault_dir", default=".", help="Vault directory")
def profile_list(vault_dir: str):
    """List all profiles."""
    profiles = list_profiles(Path(vault_dir))
    if not profiles:
        click.echo("No profiles defined.")
        return
    for p in profiles:
        click.echo(f"{p['name']:20s}  {p['vault']}")
