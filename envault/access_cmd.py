"""CLI commands for managing vault access control."""

from __future__ import annotations

import click

from envault.access import (
    AccessError,
    grant,
    has_permission,
    list_principals,
    revoke,
    get_permissions,
)


@click.group("access")
def access_cmd() -> None:
    """Manage per-vault access permissions."""


@access_cmd.command("grant")
@click.argument("vault")
@click.argument("principal")
@click.argument("permission")
def access_grant(vault: str, principal: str, permission: str) -> None:
    """Grant PERMISSION to PRINCIPAL on VAULT."""
    try:
        grant(vault, principal, permission)
        click.echo(f"Granted '{permission}' to '{principal}' on vault '{vault}'.")
    except AccessError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@access_cmd.command("revoke")
@click.argument("vault")
@click.argument("principal")
@click.argument("permission")
def access_revoke(vault: str, principal: str, permission: str) -> None:
    """Revoke PERMISSION from PRINCIPAL on VAULT."""
    changed = revoke(vault, principal, permission)
    if changed:
        click.echo(f"Revoked '{permission}' from '{principal}' on vault '{vault}'.")
    else:
        click.echo(f"'{principal}' did not hold '{permission}' on vault '{vault}'.")


@access_cmd.command("check")
@click.argument("vault")
@click.argument("principal")
@click.argument("permission")
def access_check(vault: str, principal: str, permission: str) -> None:
    """Check whether PRINCIPAL has PERMISSION on VAULT."""
    if has_permission(vault, principal, permission):
        click.echo(f"ALLOWED: '{principal}' has '{permission}' on vault '{vault}'.")
    else:
        click.echo(f"DENIED: '{principal}' lacks '{permission}' on vault '{vault}'.")
        raise SystemExit(1)


@access_cmd.command("show")
@click.argument("vault")
@click.argument("principal", required=False)
def access_show(vault: str, principal: str | None) -> None:
    """Show permissions for VAULT, optionally filtered to PRINCIPAL."""
    if principal:
        perms = get_permissions(vault, principal)
        if perms:
            click.echo(f"{principal}: {', '.join(perms)}")
        else:
            click.echo(f"No permissions found for '{principal}' on vault '{vault}'.")
    else:
        acl = list_principals(vault)
        if not acl:
            click.echo(f"No access entries for vault '{vault}'.")
        else:
            for p, perms in sorted(acl.items()):
                click.echo(f"  {p}: {', '.join(perms)}")
