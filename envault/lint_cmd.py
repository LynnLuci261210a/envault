"""CLI commands for linting .env files."""
from __future__ import annotations

from pathlib import Path

import click

from .lint import lint_file, lint_env


@click.group("lint")
def lint_cmd() -> None:
    """Lint .env files for common issues."""


@lint_cmd.command("check")
@click.argument("env_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--strict", is_flag=True, default=False, help="Exit non-zero on warnings too.")
def lint_check(env_file: Path, strict: bool) -> None:
    """Check ENV_FILE for lint issues and report them."""
    result = lint_file(env_file)

    if not result.issues:
        click.secho(f"✔ {env_file}: no issues found.", fg="green")
        return

    for issue in result.issues:
        colour = "red" if issue.severity == "error" else "yellow"
        click.secho(str(issue), fg=colour)

    summary = f"{result.error_count} error(s), {result.warning_count} warning(s)"
    click.echo(f"\n{env_file}: {summary}")

    if not result.ok or (strict and result.warning_count):
        raise SystemExit(1)


@lint_cmd.command("summary")
@click.argument("env_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def lint_summary(env_file: Path) -> None:
    """Print a one-line summary of lint results for ENV_FILE."""
    result = lint_file(env_file)
    status = "OK" if result.ok else "FAIL"
    click.echo(
        f"{env_file}: [{status}] {result.error_count} error(s), {result.warning_count} warning(s)"
    )
