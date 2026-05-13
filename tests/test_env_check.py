"""Tests for envault.env_check."""
import pytest

from envault.env_check import CheckResult, check_required


ENV_TEXT = """
# database settings
DB_HOST=localhost
DB_PORT=5432
DB_NAME=myapp
DB_PASSWORD=secret
EMPTY_KEY=
"""


# ---------------------------------------------------------------------------
# CheckResult helpers
# ---------------------------------------------------------------------------

def test_check_result_ok_when_no_missing():
    r = CheckResult(present=["A", "B"], missing=[])
    assert r.ok is True


def test_check_result_not_ok_when_missing():
    r = CheckResult(present=["A"], missing=["B"])
    assert r.ok is False


def test_check_result_summary_ok():
    r = CheckResult(present=["A"], missing=[])
    assert "[OK]" in r.summary()
    assert "A" in r.summary()


def test_check_result_summary_fail():
    r = CheckResult(present=["A"], missing=["B"])
    summary = r.summary()
    assert "[FAIL]" in summary
    assert "B" in summary


# ---------------------------------------------------------------------------
# check_required — happy path
# ---------------------------------------------------------------------------

def test_all_keys_present():
    result = check_required(ENV_TEXT, ["DB_HOST", "DB_PORT", "DB_NAME"])
    assert result.ok
    assert set(result.present) == {"DB_HOST", "DB_PORT", "DB_NAME"}
    assert result.missing == []


def test_missing_key_detected():
    result = check_required(ENV_TEXT, ["DB_HOST", "MISSING_KEY"])
    assert not result.ok
    assert "MISSING_KEY" in result.missing
    assert "DB_HOST" in result.present


def test_empty_value_treated_as_missing_by_default():
    result = check_required(ENV_TEXT, ["EMPTY_KEY"])
    assert not result.ok
    assert "EMPTY_KEY" in result.missing


def test_empty_value_allowed_when_flag_set():
    result = check_required(ENV_TEXT, ["EMPTY_KEY"], allow_empty=True)
    assert result.ok
    assert "EMPTY_KEY" in result.present


def test_empty_required_list_is_always_ok():
    result = check_required(ENV_TEXT, [])
    assert result.ok
    assert result.missing == []
    assert result.present == []


def test_comments_and_blank_lines_ignored():
    env = "# comment\n\nKEY=value\n"
    result = check_required(env, ["KEY"])
    assert result.ok


def test_value_with_equals_sign_parsed_correctly():
    env = "TOKEN=abc=def==\n"
    result = check_required(env, ["TOKEN"])
    assert result.ok


def test_multiple_missing_keys_all_reported():
    result = check_required(ENV_TEXT, ["A", "B", "C"])
    assert set(result.missing) == {"A", "B", "C"}
    assert result.present == []
