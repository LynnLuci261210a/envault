"""CLI integration for diff and history commands."""

from __future__ import annotations

import click

from envault.diff import diff_envs, format_diff
from envault.history import list_versions, get_version
from envault.vault import load_vault
from envault.crypto import load_key, decrypt


@click.command("diff")
@click.argument("name")
@click.argument("env_file", type=click.Path(exists=True))
@click.option("--key-file", default=".envault.key", show_default=True,
              help="Path to the encryption key file.")
@click.option("--show-values", is_flag=True, default=False,
              help="Show actual values in diff output (caution: exposes secrets).")
def diff_cmd(name: str, env_file: str, key_file: str, show_values: bool) -> None:
    """Diff a local .env file against the latest locked vault version."""
    try:
        key = load_key(key_file)
    except FileNotFoundError:
        raise click.ClickException(f"Key file '{key_file}' not found. Run 'envault init' first.")

    try:
        vault_data = load_vault(name)
    except FileNotFoundError:
        raise click.ClickException(f"No vault found for '{name}'. Run 'envault lock' first.")

    ciphertext = bytes.fromhex(vault_data["ciphertext"])
    locked_content = decrypt(ciphertext, key)

    with open(env_file, "r") as f:
        local_content = f.read()

    diff = diff_envs(locked_content, local_content)
    click.echo(f"Diff for '{name}': {diff.summary()}")
    click.echo(format_diff(diff, show_values=show_values,
                           old=locked_content, new=local_content))


@click.command("log")
@click.argument("name")
@click.option("--limit", default=10, show_default=True,
              help="Maximum number of versions to show.")
def log_cmd(name: str, limit: int) -> None:
    """Show version history for a vault."""
    import time as _time

    versions = list_versions(name)
    if not versions:
        click.echo(f"No history found for '{name}'.")
        return

    click.echo(f"History for '{name}' ({len(versions)} version(s)):")
    for entry in versions[-limit:][::-1]:
        ts = _time.strftime("%Y-%m-%d %H:%M:%S", _time.localtime(entry["timestamp"]))
        note = f"  # {entry['note']}" if entry.get("note") else ""
        click.echo(f"  v{entry['version']}  {ts}{note}")


@click.command("restore")
@click.argument("name")
@click.argument("version", type=int)
@click.argument("output", type=click.Path())
@click.option("--key-file", default=".envault.key", show_default=True,
              help="Path to the encryption key file.")
def restore_cmd(name: str, version: int, output: str, key_file: str) -> None:
    """Restore a specific vault version to a plaintext .env file."""
    try:
        key = load_key(key_file)
    except FileNotFoundError:
        raise click.ClickException(f"Key file '{key_file}' not found.")

    ciphertext_hex = get_version(name, version)
    if ciphertext_hex is None:
        raise click.ClickException(f"Version {version} not found for '{name}'.")

    plaintext = decrypt(bytes.fromhex(ciphertext_hex), key)
    with open(output, "w") as f:
        f.write(plaintext)

    click.echo(f"Restored v{version} of '{name}' to '{output}'.")
