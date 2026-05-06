"""CLI commands for snapshot management."""

from __future__ import annotations

import click

from envault.snapshot import SnapshotError, delete_snapshot, get_snapshot, list_snapshots, save_snapshot


@click.group("snapshot")
def snapshot_cmd() -> None:
    """Manage named snapshots of vault versions."""


@snapshot_cmd.command("save")
@click.argument("vault")
@click.argument("label")
@click.argument("version", type=int)
@click.option("--note", default="", help="Optional note for this snapshot.")
def snapshot_save(vault: str, label: str, version: int, note: str) -> None:
    """Save a named snapshot pointing to VERSION in VAULT."""
    try:
        save_snapshot(vault, label, version, note)
        click.echo(f"Snapshot '{label}' saved for vault '{vault}' at version {version}.")
    except SnapshotError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@snapshot_cmd.command("get")
@click.argument("vault")
@click.argument("label")
def snapshot_get(vault: str, label: str) -> None:
    """Show version number for a named snapshot."""
    entry = get_snapshot(vault, label)
    if entry is None:
        click.echo(f"Snapshot '{label}' not found.", err=True)
        raise SystemExit(1)
    note_part = f"  # {entry['note']}" if entry.get("note") else ""
    click.echo(f"{label} -> version {entry['version']}{note_part}")


@snapshot_cmd.command("delete")
@click.argument("vault")
@click.argument("label")
def snapshot_delete(vault: str, label: str) -> None:
    """Delete a named snapshot."""
    removed = delete_snapshot(vault, label)
    if not removed:
        click.echo(f"Snapshot '{label}' not found.", err=True)
        raise SystemExit(1)
    click.echo(f"Snapshot '{label}' deleted.")


@snapshot_cmd.command("list")
@click.argument("vault")
def snapshot_list(vault: str) -> None:
    """List all snapshots for VAULT."""
    entries = list_snapshots(vault)
    if not entries:
        click.echo("No snapshots found.")
        return
    for entry in entries:
        note_part = f"  # {entry['note']}" if entry.get("note") else ""
        click.echo(f"{entry['label']} -> version {entry['version']}{note_part}")
