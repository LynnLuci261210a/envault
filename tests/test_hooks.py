"""Tests for envault.hooks module."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from envault.hooks import (
    HookError,
    delete_hook,
    get_hook,
    list_hooks,
    run_hook,
    set_hook,
)


@pytest.fixture()
def tmp_vault(tmp_path: Path) -> Path:
    return tmp_path


def test_set_hook_creates_file(tmp_vault: Path) -> None:
    set_hook(tmp_vault, "pre-lock", "echo hello")
    hooks_file = tmp_vault / ".envault-hooks.json"
    assert hooks_file.exists()


def test_set_hook_stores_command(tmp_vault: Path) -> None:
    set_hook(tmp_vault, "post-unlock", "make load-env")
    hooks = json.loads((tmp_vault / ".envault-hooks.json").read_text())
    assert hooks["post-unlock"] == "make load-env"


def test_set_hook_invalid_event_raises(tmp_vault: Path) -> None:
    with pytest.raises(HookError, match="Unknown event"):
        set_hook(tmp_vault, "on-deploy", "echo nope")


def test_get_hook_returns_command(tmp_vault: Path) -> None:
    set_hook(tmp_vault, "pre-unlock", "./scripts/check.sh")
    assert get_hook(tmp_vault, "pre-unlock") == "./scripts/check.sh"


def test_get_hook_missing_returns_none(tmp_vault: Path) -> None:
    assert get_hook(tmp_vault, "pre-lock") is None


def test_delete_hook_removes_entry(tmp_vault: Path) -> None:
    set_hook(tmp_vault, "post-lock", "echo done")
    result = delete_hook(tmp_vault, "post-lock")
    assert result is True
    assert get_hook(tmp_vault, "post-lock") is None


def test_delete_hook_missing_returns_false(tmp_vault: Path) -> None:
    assert delete_hook(tmp_vault, "post-lock") is False


def test_list_hooks_returns_all(tmp_vault: Path) -> None:
    set_hook(tmp_vault, "pre-lock", "echo a")
    set_hook(tmp_vault, "post-unlock", "echo b")
    hooks = list_hooks(tmp_vault)
    assert hooks == {"pre-lock": "echo a", "post-unlock": "echo b"}


def test_list_hooks_empty(tmp_vault: Path) -> None:
    assert list_hooks(tmp_vault) == {}


def test_run_hook_executes_command(tmp_vault: Path) -> None:
    set_hook(tmp_vault, "post-lock", "true")
    # Should not raise
    run_hook(tmp_vault, "post-lock")


def test_run_hook_no_hook_registered_is_noop(tmp_vault: Path) -> None:
    run_hook(tmp_vault, "pre-lock")  # nothing registered — must not raise


def test_run_hook_failing_command_raises(tmp_vault: Path) -> None:
    set_hook(tmp_vault, "pre-unlock", "exit 1")
    with pytest.raises(HookError, match="failed"):
        run_hook(tmp_vault, "pre-unlock")


def test_set_hook_overwrites_existing(tmp_vault: Path) -> None:
    set_hook(tmp_vault, "pre-lock", "echo first")
    set_hook(tmp_vault, "pre-lock", "echo second")
    assert get_hook(tmp_vault, "pre-lock") == "echo second"
