"""CLI commands for searching vault contents."""
from __future__ import annotations

import click

from envault.search import search_vault
from envault.vault import list_vaults


@click.group("search")
def search_cmd() -> None:
    """Search vault keys and values."""


@search_cmd.command("run")
@click.argument("query")
@click.option("--vault", "-v", default=None, help="Vault name to search (default: all vaults).")
@click.option("--keys-only", is_flag=True, default=False, help="Only match against key names.")
@click.option("--case-sensitive", is_flag=True, default=False, help="Enable case-sensitive search.")
@click.option("--dir", "key_dir", default=".", show_default=True, help="Directory containing vault files.")
def search_run(
    query: str,
    vault: str | None,
    keys_only: bool,
    case_sensitive: bool,
    key_dir: str,
) -> None:
    """Search for QUERY across vault keys (and optionally values)."""
    vaults_to_search: list[str]
    if vault:
        vaults_to_search = [vault]
    else:
        vaults_to_search = list_vaults(base_dir=key_dir)
        if not vaults_to_search:
            click.echo("No vaults found.")
            return

    total_matches = 0
    for vault_name in vaults_to_search:
        result = search_vault(
            vault_name,
            query,
            key_dir=key_dir,
            keys_only=keys_only,
            case_sensitive=case_sensitive,
        )
        if result.found:
            click.echo(result.summary())
            total_matches += len(result.matches)

    if total_matches == 0:
        click.echo("No matches found.")
    else:
        click.echo(f"\n{total_matches} match(es) found.")
