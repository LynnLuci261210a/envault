"""Tests for envault.watch."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from envault.watch import WatchError, _file_hash, watch_env


def test_file_hash_returns_string(tmp_path: Path) -> None:
    f = tmp_path / ".env"
    f.write_text("KEY=value\n")
    result = _file_hash(f)
    assert isinstance(result, str)
    assert len(result) == 64  # SHA-256 hex


def test_file_hash_changes_on_content_change(tmp_path: Path) -> None:
    f = tmp_path / ".env"
    f.write_text("KEY=value\n")
    h1 = _file_hash(f)
    f.write_text("KEY=other\n")
    h2 = _file_hash(f)
    assert h1 != h2


def test_watch_env_raises_if_file_missing(tmp_path: Path) -> None:
    with pytest.raises(WatchError, match="File not found"):
        watch_env(tmp_path / "nonexistent.env", lambda p: None, interval=0.01, max_iterations=1)


def test_watch_env_calls_on_change(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("A=1\n")

    called: list[Path] = []

    def _mutate_then_stop(path: Path) -> None:
        called.append(path)

    # Mutate the file before the first poll tick via a thread-like trick:
    # we run max_iterations=2 and modify the file after creation.
    import threading

    def _modify() -> None:
        time.sleep(0.05)
        env.write_text("A=2\n")

    t = threading.Thread(target=_modify, daemon=True)
    t.start()
    watch_env(env, _mutate_then_stop, interval=0.02, max_iterations=10)
    t.join()

    assert len(called) >= 1
    assert called[0] == env


def test_watch_env_no_change_no_callback(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("A=1\n")
    called: list[Path] = []
    watch_env(env, lambda p: called.append(p), interval=0.01, max_iterations=3)
    assert called == []


def test_watch_env_raises_if_file_disappears(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("A=1\n")

    import threading

    def _delete() -> None:
        time.sleep(0.03)
        env.unlink()

    t = threading.Thread(target=_delete, daemon=True)
    t.start()
    with pytest.raises(WatchError, match="disappeared"):
        watch_env(env, lambda p: None, interval=0.02, max_iterations=10)
    t.join()
