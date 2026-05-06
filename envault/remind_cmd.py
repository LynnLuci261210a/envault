"""CLI commands for rotation reminders."""

from __future__ import annotations

import click

from envault.remind import (
    DEFAULT_MAX_AGE_DAYS,
    days_since_rotation,
    get_last_rotation,
    is_overdue,
    record_rotation,
)


@click.group("remind")
def remind_cmd() -> None:
    """Manage key-rotation reminders."""


@remind_cmd.command("mark")
@click.argument("vault_name")
def remind_mark(vault_name: str) -> None:
    """Record that VAULT_NAME was just rotated."""
    ts = record_rotation(vault_name)
    click.echo(f"Rotation recorded for '{vault_name}' at {ts}.")


@remind_cmd.command("status")
@click.argument("vault_name")
@click.option(
    "--max-age",
    default=DEFAULT_MAX_AGE_DAYS,
    show_default=True,
    help="Maximum acceptable age in days before a vault is considered overdue.",
)
def remind_status(vault_name: str, max_age: int) -> None:
    """Show rotation status for VAULT_NAME."""
    last = get_last_rotation(vault_name)
    if last is None:
        click.echo(
            f"⚠  '{vault_name}' has never been rotated.", err=False
        )
        raise SystemExit(1)

    days = days_since_rotation(vault_name)
    overdue = is_overdue(vault_name, max_age_days=max_age)
    status = "OVERDUE" if overdue else "OK"
    click.echo(
        f"Vault '{vault_name}': last rotated {days} day(s) ago "
        f"(threshold: {max_age} days) — {status}"
    )
    if overdue:
        raise SystemExit(1)


@remind_cmd.command("check")
@click.argument("vault_name")
@click.option("--max-age", default=DEFAULT_MAX_AGE_DAYS, show_default=True)
def remind_check(vault_name: str, max_age: int) -> None:
    """Exit with code 1 (and print a warning) if VAULT_NAME rotation is overdue."""
    if is_overdue(vault_name, max_age_days=max_age):
        days = days_since_rotation(vault_name)
        msg = (
            f"never been rotated"
            if days is None
            else f"last rotated {days} day(s) ago"
        )
        click.echo(
            f"Warning: vault '{vault_name}' is overdue for rotation ({msg}).",
            err=True,
        )
        raise SystemExit(1)
    click.echo(f"Vault '{vault_name}' rotation is up to date.")
