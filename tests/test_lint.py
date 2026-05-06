"""Tests for envault.lint and envault.lint_cmd."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.lint import lint_env, lint_file, LintResult
from envault.lint_cmd import lint_cmd


# ---------------------------------------------------------------------------
# lint_env unit tests
# ---------------------------------------------------------------------------

def test_clean_env_returns_no_issues():
    content = "DB_HOST=localhost\nDB_PORT=5432\nAPP_ENV=production\n"
    result = lint_env(content)
    assert result.issues == []
    assert result.ok


def test_detects_duplicate_key():
    content = "FOO=bar\nFOO=baz\n"
    result = lint_env(content)
    errors = [i for i in result.issues if "Duplicate" in i.message]
    assert len(errors) == 1
    assert errors[0].severity == "error"


def test_detects_empty_value():
    result = lint_env("MY_VAR=\n")
    warnings = [i for i in result.issues if "empty" in i.message]
    assert len(warnings) == 1
    assert warnings[0].severity == "warning"


def test_detects_invalid_key():
    result = lint_env("my-key=value\n")
    errors = [i for i in result.issues if "invalid characters" in i.message]
    assert len(errors) == 1
    assert errors[0].severity == "error"


def test_detects_unquoted_spaces():
    result = lint_env("GREETING=hello world\n")
    warnings = [i for i in result.issues if "spaces" in i.message]
    assert len(warnings) == 1


def test_quoted_spaces_no_warning():
    result = lint_env('GREETING="hello world"\n')
    space_warnings = [i for i in result.issues if "spaces" in i.message]
    assert space_warnings == []


def test_detects_weak_secret():
    result = lint_env("PASSWORD=abc\n")
    warnings = [i for i in result.issues if "weak" in i.message]
    assert len(warnings) == 1
    assert warnings[0].severity == "warning"


def test_strong_password_no_weak_warning():
    result = lint_env("PASSWORD=s3cur3P@ssw0rd!XYZ\n")
    weak = [i for i in result.issues if "weak" in i.message]
    assert weak == []


def test_comments_and_blank_lines_ignored():
    content = "# This is a comment\n\nFOO=bar\n"
    result = lint_env(content)
    assert result.issues == []


def test_invalid_line_no_equals():
    result = lint_env("NOEQUALSSIGN\n")
    errors = [i for i in result.issues if "valid KEY=VALUE" in i.message]
    assert len(errors) == 1
    assert errors[0].severity == "error"


def test_ok_property_false_when_errors():
    result = lint_env("FOO=bar\nFOO=baz\n")
    assert not result.ok


def test_lint_file_reads_from_disk(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("KEY=value\n")
    result = lint_file(env_file)
    assert isinstance(result, LintResult)
    assert result.issues == []


# ---------------------------------------------------------------------------
# lint_cmd CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner():
    return CliRunner()


def test_lint_check_clean_file(runner: CliRunner, tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("DB_HOST=localhost\nDB_PORT=5432\n")
    result = runner.invoke(lint_cmd, ["check", str(env_file)])
    assert result.exit_code == 0
    assert "no issues" in result.output


def test_lint_check_exits_nonzero_on_errors(runner: CliRunner, tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\nFOO=baz\n")
    result = runner.invoke(lint_cmd, ["check", str(env_file)])
    assert result.exit_code == 1


def test_lint_check_strict_exits_nonzero_on_warnings(runner: CliRunner, tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("MY_VAR=\n")
    result = runner.invoke(lint_cmd, ["check", "--strict", str(env_file)])
    assert result.exit_code == 1


def test_lint_summary_outputs_status(runner: CliRunner, tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("GOOD=value\n")
    result = runner.invoke(lint_cmd, ["summary", str(env_file)])
    assert result.exit_code == 0
    assert "OK" in result.output
