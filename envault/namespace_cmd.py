"""CLI commands for namespace management."""

from __future__ import annotations

import click

from envault.namespace import (
    NamespaceError,
    add_vault,
    delete_namespace,
    get_namespace,
    list_namespaces,
    list_vaults,
    remove_vault,
)


@click.group("namespace")
def namespace_cmd() -> None:
    """Manage vault namespaces."""


@namespace_cmd.command("add")
@click.argument("namespace")
@click.argument("vault")
def namespace_add(namespace: str, vault: str) -> None:
    """Add VAULT to NAMESPACE."""
    try:
        add_vault(namespace, vault)
        click.echo(f"Vault '{vault}' added to namespace '{namespace}'.")
    except NamespaceError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@namespace_cmd.command("remove")
@click.argument("namespace")
@click.argument("vault")
def namespace_remove(namespace: str, vault: str) -> None:
    """Remove VAULT from NAMESPACE."""
    removed = remove_vault(namespace, vault)
    if removed:
        click.echo(f"Vault '{vault}' removed from namespace '{namespace}'.")
    else:
        click.echo(f"Vault '{vault}' not found in namespace '{namespace}'.", err=True)
        raise SystemExit(1)


@namespace_cmd.command("list")
@click.argument("namespace", required=False)
def namespace_list(namespace: str | None) -> None:
    """List vaults in NAMESPACE, or list all namespaces."""
    if namespace:
        vaults = list_vaults(namespace)
        if not vaults:
            click.echo(f"No vaults in namespace '{namespace}'.")
        else:
            for v in vaults:
                click.echo(v)
    else:
        namespaces = list_namespaces()
        if not namespaces:
            click.echo("No namespaces defined.")
        else:
            for ns in namespaces:
                click.echo(ns)


@namespace_cmd.command("which")
@click.argument("vault")
def namespace_which(vault: str) -> None:
    """Show which namespace VAULT belongs to."""
    ns = get_namespace(vault)
    if ns:
        click.echo(ns)
    else:
        click.echo(f"Vault '{vault}' is not in any namespace.", err=True)
        raise SystemExit(1)


@namespace_cmd.command("delete")
@click.argument("namespace")
def namespace_delete(namespace: str) -> None:
    """Delete an entire NAMESPACE (does not delete vaults)."""
    deleted = delete_namespace(namespace)
    if deleted:
        click.echo(f"Namespace '{namespace}' deleted.")
    else:
        click.echo(f"Namespace '{namespace}' not found.", err=True)
        raise SystemExit(1)
