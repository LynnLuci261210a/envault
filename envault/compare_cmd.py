"""CLI commands for comparing vault versions or snapshots."""

from __future__ import annotations

import click

from envault.compare import compare_refs, CompareError
from envault.profile_resolve import resolve_or_raise


@click.group(name="compare")
def compare_cmd() -> None:
    """Compare two versions or snapshots of a vault."""


@compare_cmd.command(name="run")
@click.argument("ref_a")
@click.argument("ref_b")
@click.option("--vault", "-v", default=None, help="Vault name (or active profile).")
@click.option(
    "--key",
    "-k",
    default=".envault.key",
    show_default=True,
    help="Path to the encryption key file.",
)
@click.option("--no-color", is_flag=True, default=False, help="Disable colored output.")
def compare_run(
    ref_a: str,
    ref_b: str,
    vault: str | None,
    key: str,
    no_color: bool,
) -> None:
    """Compare REF_A and REF_B (version numbers or snapshot names)."""
    try:
        vault_name = resolve_or_raise(vault)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    try:
        result = compare_refs(vault_name, ref_a, ref_b, key)
    except CompareError as exc:
        raise click.ClickException(str(exc)) from exc

    if not result.has_changes():
        click.echo(f"No differences between {ref_a} and {ref_b}.")
        return

    diff = result.diff
    lines = [result.summary(), ""]

    for k in sorted(diff.added):
        msg = f"  + {k}={diff.env_b[k]}"
        lines.append(click.style(msg, fg="green") if not no_color else msg)

    for k in sorted(diff.removed):
        msg = f"  - {k}={diff.env_a[k]}"
        lines.append(click.style(msg, fg="red") if not no_color else msg)

    for k in sorted(diff.changed):
        msg_old = f"  ~ {k}: {diff.env_a[k]!r} → {diff.env_b[k]!r}"
        lines.append(click.style(msg_old, fg="yellow") if not no_color else msg_old)

    click.echo("\n".join(lines))
