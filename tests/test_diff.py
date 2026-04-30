"""Tests for envault.diff module."""

import pytest
from envault.diff import DiffResult, parse_env, diff_envs, format_diff


ENV_A = """
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mydb
SECRET_KEY=abc123
"""

ENV_B = """
# Database
DB_HOST=prod.example.com
DB_PORT=5432
DB_NAME=mydb
NEW_VAR=hello
"""


def test_parse_env_basic():
    result = parse_env("FOO=bar\nBAZ=qux")
    assert result == {"FOO": "bar", "BAZ": "qux"}


def test_parse_env_ignores_comments():
    result = parse_env("# comment\nFOO=bar")
    assert "# comment" not in result
    assert result["FOO"] == "bar"


def test_parse_env_ignores_blank_lines():
    result = parse_env("\n\nFOO=bar\n\n")
    assert result == {"FOO": "bar"}


def test_parse_env_handles_equals_in_value():
    result = parse_env("TOKEN=abc=def=ghi")
    assert result["TOKEN"] == "abc=def=ghi"


def test_diff_envs_detects_added():
    diff = diff_envs(ENV_A, ENV_B)
    assert "NEW_VAR" in diff.added


def test_diff_envs_detects_removed():
    diff = diff_envs(ENV_A, ENV_B)
    assert "SECRET_KEY" in diff.removed


def test_diff_envs_detects_changed():
    diff = diff_envs(ENV_A, ENV_B)
    assert "DB_HOST" in diff.changed


def test_diff_envs_detects_unchanged():
    diff = diff_envs(ENV_A, ENV_B)
    assert "DB_PORT" in diff.unchanged
    assert "DB_NAME" in diff.unchanged


def test_diff_result_has_changes():
    diff = diff_envs(ENV_A, ENV_B)
    assert diff.has_changes is True


def test_diff_result_no_changes():
    diff = diff_envs(ENV_A, ENV_A)
    assert diff.has_changes is False


def test_diff_summary():
    diff = diff_envs(ENV_A, ENV_B)
    summary = diff.summary()
    assert "added" in summary
    assert "removed" in summary
    assert "changed" in summary


def test_diff_summary_no_changes():
    diff = diff_envs(ENV_A, ENV_A)
    assert diff.summary() == "No changes"


def test_format_diff_shows_symbols():
    diff = diff_envs(ENV_A, ENV_B)
    output = format_diff(diff)
    assert "+" in output
    assert "-" in output
    assert "~" in output


def test_format_diff_show_values():
    diff = diff_envs(ENV_A, ENV_B)
    output = format_diff(diff, show_values=True, old=ENV_A, new=ENV_B)
    assert "prod.example.com" in output
    assert "localhost" in output


def test_format_diff_no_changes_message():
    diff = diff_envs(ENV_A, ENV_A)
    output = format_diff(diff)
    assert "no changes" in output
