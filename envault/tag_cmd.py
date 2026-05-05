"""CLI commands for managing vault version tags."""

from __future__ import annotations

import click
from envault.tags import set_tag, get_tag, delete_tag, list_tags
from envault.history import list_versions


@click.group("tag")
def tag_cmd():
    """Manage named tags for vault versions."""


@tag_cmd.command("set")
@click.argument("vault_name")
@click.argument("tag")
@click.argument("version", type=int)
def tag_set(vault_name: str, tag: str, version: int):
    """Assign TAG to a specific VERSION of VAULT_NAME."""
    versions = list_versions(vault_name)
    version_numbers = [v["version"] for v in versions]
    if version not in version_numbers:
        raise click.ClickException(
            f"Version {version} does not exist for vault '{vault_name}'. "
            f"Available: {version_numbers}"
        )
    set_tag(vault_name, tag, version)
    click.echo(f"Tag '{tag}' -> version {version} set for vault '{vault_name}'.")


@tag_cmd.command("get")
@click.argument("vault_name")
@click.argument("tag")
def tag_get(vault_name: str, tag: str):
    """Show which version TAG points to in VAULT_NAME."""
    version = get_tag(vault_name, tag)
    if version is None:
        raise click.ClickException(f"Tag '{tag}' not found for vault '{vault_name}'.")
    click.echo(f"{tag} -> version {version}")


@tag_cmd.command("delete")
@click.argument("vault_name")
@click.argument("tag")
def tag_delete(vault_name: str, tag: str):
    """Remove TAG from VAULT_NAME."""
    removed = delete_tag(vault_name, tag)
    if not removed:
        raise click.ClickException(f"Tag '{tag}' not found for vault '{vault_name}'.")
    click.echo(f"Tag '{tag}' removed from vault '{vault_name}'.")


@tag_cmd.command("list")
@click.argument("vault_name")
def tag_list(vault_name: str):
    """List all tags for VAULT_NAME."""
    tags = list_tags(vault_name)
    if not tags:
        click.echo(f"No tags set for vault '{vault_name}'.")
        return
    for tag, version in sorted(tags.items()):
        click.echo(f"  {tag:<20} -> v{version}")
