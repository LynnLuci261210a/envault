"""Command-line interface for envault."""

import sys
from pathlib import Path
from typing import Optional

import click

from envault.crypto import generate_key, save_key
from envault.vault import delete_vault, list_vaults, load_vault, save_vault

DEFAULT_KEY_PATH = Path(".envault/master.key")
DEFAULT_VAULT_DIR = Path(".envault")


@click.group()
def cli():
    """envault — encrypt and version-control .env files safely."""


@cli.command("init")
@click.option("--passphrase", default=None, help="Optional passphrase to protect the key.")
@click.option("--key-path", default=str(DEFAULT_KEY_PATH), show_default=True)
def init_cmd(passphrase: Optional[str], key_path: str):
    """Generate a new master encryption key."""
    path = Path(key_path)
    if path.exists():
        click.echo(f"Key already exists at {path}. Aborting.", err=True)
        sys.exit(1)
    key = generate_key(passphrase=passphrase)
    save_key(key, path)
    click.echo(f"Master key saved to {path}")
    click.echo("Add this file to .gitignore to keep it secret!")


@cli.command("lock")
@click.argument("env_file", type=click.Path(exists=True))
@click.argument("vault_name")
@click.option("--key-path", default=str(DEFAULT_KEY_PATH), show_default=True)
@click.option("--passphrase", default=None)
def lock_cmd(env_file: str, vault_name: str, key_path: str, passphrase: Optional[str]):
    """Encrypt an .env file into a named vault."""
    content = Path(env_file).read_text()
    out_path = save_vault(
        vault_name, content, Path(key_path),
        vault_dir=DEFAULT_VAULT_DIR, passphrase=passphrase
    )
    click.echo(f"Encrypted '{env_file}' → {out_path}")


@cli.command("unlock")
@click.argument("vault_name")
@click.option("--output", "-o", default=".env", show_default=True, help="Output file path.")
@click.option("--key-path", default=str(DEFAULT_KEY_PATH), show_default=True)
@click.option("--passphrase", default=None)
def unlock_cmd(vault_name: str, output: str, key_path: str, passphrase: Optional[str]):
    """Decrypt a vault and write the .env file."""
    try:
        content = load_vault(vault_name, Path(key_path), vault_dir=DEFAULT_VAULT_DIR, passphrase=passphrase)
    except FileNotFoundError as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)
    Path(output).write_text(content)
    click.echo(f"Decrypted vault '{vault_name}' → {output}")


@cli.command("list")
def list_cmd():
    """List all available vaults."""
    vaults = list_vaults(vault_dir=DEFAULT_VAULT_DIR)
    if not vaults:
        click.echo("No vaults found.")
        return
    click.echo(f"{'NAME':<20} {'CREATED':<30} PATH")
    click.echo("-" * 70)
    for v in vaults:
        click.echo(f"{v['name']:<20} {v['created_at']:<30} {v['path']}")


@cli.command("delete")
@click.argument("vault_name")
def delete_cmd(vault_name: str):
    """Delete a vault by name."""
    removed = delete_vault(vault_name, vault_dir=DEFAULT_VAULT_DIR)
    if removed:
        click.echo(f"Vault '{vault_name}' deleted.")
    else:
        click.echo(f"Vault '{vault_name}' not found.", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
