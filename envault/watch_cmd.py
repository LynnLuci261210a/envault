"""CLI commands for the watch feature."""

from __future__ import annotations

from pathlib import Path

import click

from envault.crypto import load_key
from envault.vault import save_vault
from envault.watch import WatchError, watch_env


@click.group("watch")
def watch_cmd() -> None:
    """Watch a .env file and auto-lock it on change."""


@watch_cmd.command("start")
@click.argument("env_file", default=".env")
@click.option("--vault", "vault_name", default="default", show_default=True, help="Vault name to write encrypted data into.")
@click.option("--key-file", default=".envault.key", show_default=True, help="Path to the encryption key file.")
@click.option("--interval", default=2.0, show_default=True, help="Polling interval in seconds.")
def watch_start(
    env_file: str,
    vault_name: str,
    key_file: str,
    interval: float,
) -> None:
    """Watch ENV_FILE and re-encrypt it into VAULT whenever it changes."""
    env_path = Path(env_file)
    key_path = Path(key_file)

    if not env_path.exists():
        raise click.ClickException(f"Env file not found: {env_path}")
    if not key_path.exists():
        raise click.ClickException(f"Key file not found: {key_path}. Run 'envault init' first.")

    key = load_key(key_path)
    click.echo(f"Watching {env_path} (vault={vault_name}, interval={interval}s) — Ctrl+C to stop.")

    def _on_change(path: Path) -> None:
        plaintext = path.read_bytes()
        save_vault(vault_name, plaintext, key)
        click.echo(f"  → change detected, vault '{vault_name}' updated.")

    try:
        watch_env(env_path, _on_change, interval=interval)
    except WatchError as exc:
        raise click.ClickException(str(exc)) from exc
    except KeyboardInterrupt:
        click.echo("\nWatch stopped.")
