"""Tests for envault.watch_cmd CLI commands."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.crypto import generate_key, save_key
from envault.watch_cmd import watch_cmd


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_watch_start_missing_env_file(runner: CliRunner, tmp_path: Path) -> None:
    with runner.isolated_filesystem(temp_dir=tmp_path):
        key = generate_key()
        save_key(key, Path(".envault.key"))
        result = runner.invoke(watch_cmd, ["start", "missing.env"])
    assert result.exit_code != 0
    assert "not found" in result.output.lower()


def test_watch_start_missing_key_file(runner: CliRunner, tmp_path: Path) -> None:
    with runner.isolated_filesystem(temp_dir=tmp_path):
        Path(".env").write_text("KEY=val\n")
        result = runner.invoke(watch_cmd, ["start", ".env"])
    assert result.exit_code != 0
    assert "key file not found" in result.output.lower()


def test_watch_start_detects_change_and_locks(runner: CliRunner, tmp_path: Path) -> None:
    """Run watch with max_iterations patched to 0 after a forced change."""
    import threading
    import time

    with runner.isolated_filesystem(temp_dir=tmp_path):
        env = Path(".env")
        env.write_text("KEY=initial\n")
        key = generate_key()
        save_key(key, Path(".envault.key"))

        # Patch watch_env so it only runs briefly and triggers one change
        import envault.watch_cmd as wc_mod
        import envault.watch as w_mod

        original_watch = w_mod.watch_env

        def _patched_watch(path, on_change, *, interval=1.0, max_iterations=None):
            # Simulate one change then stop
            env.write_text("KEY=changed\n")
            on_change(path)

        wc_mod.watch_env = _patched_watch
        try:
            result = runner.invoke(watch_cmd, ["start", ".env", "--vault", "test"])
        finally:
            wc_mod.watch_env = original_watch

    assert result.exit_code == 0
    assert "updated" in result.output
