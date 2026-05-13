"""CLI commands for merging vault versions."""
from __future__ import annotations

import click

from envault.crypto import load_key, decrypt
from envault.merge import merge_envs, MergeError
from envault.vault import load_vault, save_vault
from envault.history import record_version, list_versions
from envault.audit import record_event


@click.group("merge")
def merge_cmd() -> None:
    """Merge two vault versions together."""


@merge_cmd.command("run")
@click.argument("vault_name")
@click.argument("version_ours", type=int)
@click.argument("version_theirs", type=int)
@click.option("--base", "version_base", type=int, default=None,
              help="Base version for three-way merge. Defaults to version 1.")
@click.option("--strategy", type=click.Choice(["ours", "theirs"]), default="ours",
              show_default=True, help="Conflict resolution strategy.")
@click.option("--key-file", default=".envault.key", show_default=True)
def merge_run(
    vault_name: str,
    version_ours: int,
    version_theirs: int,
    version_base: int | None,
    strategy: str,
    key_file: str,
) -> None:
    """Merge VERSION_OURS and VERSION_THEIRS of VAULT_NAME."""
    try:
        key = load_key(key_file)
    except FileNotFoundError:
        raise click.ClickException(f"Key file not found: {key_file}")

    versions = list_versions(vault_name)
    if not versions:
        raise click.ClickException(f"No versions found for vault '{vault_name}'.")

    def _load_version(v: int) -> str:
        data = load_vault(vault_name, v)
        return decrypt(data["ciphertext"], key)

    try:
        base_v = version_base if version_base is not None else versions[0]["version"]
        base_text = _load_version(base_v)
        ours_text = _load_version(version_ours)
        theirs_text = _load_version(version_theirs)
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc))

    try:
        result = merge_envs(base_text, ours_text, theirs_text, strategy=strategy)
    except MergeError as exc:
        raise click.ClickException(str(exc))

    if result.has_conflicts:
        click.echo(click.style("Conflicts detected:", fg="yellow"))
        for c in result.conflicts:
            click.echo(f"  {c}")
        click.echo(f"Strategy '{strategy}' applied automatically.")

    merged_text = "\n".join(f"{k}={v}" for k, v in result.merged.items())

    from envault.crypto import encrypt
    ciphertext = encrypt(merged_text, key)
    new_version = record_version(vault_name, merged_text)
    save_vault(vault_name, new_version, {"ciphertext": ciphertext})
    record_event(vault_name, "merge", version=new_version)

    click.echo(result.summary())
    click.echo(click.style(f"Saved as version {new_version}.", fg="green"))
