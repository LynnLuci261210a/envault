"""CLI commands for vault signing and verification."""

import click

from envault.crypto import load_key
from envault.sign import SignError, delete_signature, sign_vault, signature_info, verify_vault
from envault.vault import load_vault


@click.group("sign")
def sign_cmd():
    """Sign and verify vault integrity."""


@sign_cmd.command("create")
@click.argument("vault_name")
@click.option("--key-file", default=".envault.key", show_default=True, help="Path to key file.")
def sign_create(vault_name: str, key_file: str):
    """Create an HMAC signature for VAULT_NAME."""
    try:
        key = load_key(key_file)
        raw = load_vault(vault_name)
        import json
        ciphertext = json.dumps(raw).encode()
        sig = sign_vault(vault_name, ciphertext, key)
        click.echo(f"Signed vault '{vault_name}': {sig[:16]}...")
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc))


@sign_cmd.command("verify")
@click.argument("vault_name")
@click.option("--key-file", default=".envault.key", show_default=True, help="Path to key file.")
def sign_verify(vault_name: str, key_file: str):
    """Verify the HMAC signature of VAULT_NAME."""
    try:
        key = load_key(key_file)
        raw = load_vault(vault_name)
        import json
        ciphertext = json.dumps(raw).encode()
        present = verify_vault(vault_name, ciphertext, key)
        if not present:
            click.echo(f"No signature found for vault '{vault_name}'.")
        else:
            click.echo(f"Vault '{vault_name}' signature OK.")
    except SignError as exc:
        raise click.ClickException(str(exc))
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc))


@sign_cmd.command("info")
@click.argument("vault_name")
def sign_info(vault_name: str):
    """Show signature metadata for VAULT_NAME."""
    info = signature_info(vault_name)
    if info is None:
        click.echo(f"No signature file for vault '{vault_name}'.")
    else:
        click.echo(f"Algorithm : {info.get('alg')}")
        click.echo(f"Signature : {info.get('sig')}")


@sign_cmd.command("delete")
@click.argument("vault_name")
def sign_delete(vault_name: str):
    """Remove the signature file for VAULT_NAME."""
    removed = delete_signature(vault_name)
    if removed:
        click.echo(f"Signature for '{vault_name}' deleted.")
    else:
        click.echo(f"No signature file found for '{vault_name}'.")
