"""Tests for envault.env_schema."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.env_schema import (
    SchemaError,
    SchemaIssue,
    SchemaResult,
    load_schema,
    save_schema,
    validate_env,
)


@pytest.fixture()
def tmp_vault(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


# --- SchemaResult ---

def test_schema_result_ok_when_no_issues():
    result = SchemaResult()
    assert result.ok is True


def test_schema_result_not_ok_with_issues():
    result = SchemaResult(issues=[SchemaIssue("KEY", "missing")])
    assert result.ok is False


def test_schema_result_summary_ok():
    assert "passed" in SchemaResult().summary()


def test_schema_result_summary_fail():
    result = SchemaResult(issues=[SchemaIssue("FOO", "required key is missing")])
    summary = result.summary()
    assert "failed" in summary
    assert "FOO" in summary


def test_schema_issue_str():
    issue = SchemaIssue("BAR", "bad value")
    assert str(issue) == "BAR: bad value"


# --- save / load schema ---

def test_save_schema_creates_file(tmp_vault):
    schema = {"KEY": {"required": True}}
    path = save_schema("myapp", schema)
    assert path.exists()


def test_load_schema_roundtrip(tmp_vault):
    schema = {"API_URL": {"required": True, "type": "string"}}
    save_schema("myapp", schema)
    loaded = load_schema("myapp")
    assert loaded == schema


def test_load_schema_missing_raises(tmp_vault):
    with pytest.raises(SchemaError, match="No schema found"):
        load_schema("ghost")


def test_load_schema_invalid_json_raises(tmp_vault):
    path = Path(".envault") / "bad" / "schema.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("not json")
    with pytest.raises(SchemaError, match="Invalid schema JSON"):
        load_schema("bad")


# --- validate_env ---

def test_validate_required_key_present():
    result = validate_env({"HOST": "localhost"}, {"HOST": {"required": True}})
    assert result.ok


def test_validate_required_key_missing():
    result = validate_env({}, {"HOST": {"required": True}})
    assert not result.ok
    assert any(i.key == "HOST" for i in result.issues)


def test_validate_optional_key_absent_is_ok():
    result = validate_env({}, {"DEBUG": {"required": False}})
    assert result.ok


def test_validate_int_type_valid():
    result = validate_env({"PORT": "8080"}, {"PORT": {"type": "int"}})
    assert result.ok


def test_validate_int_type_invalid():
    result = validate_env({"PORT": "abc"}, {"PORT": {"type": "int"}})
    assert not result.ok
    assert any("integer" in i.message for i in result.issues)


def test_validate_pattern_match():
    result = validate_env({"ENV": "prod"}, {"ENV": {"pattern": "^(prod|staging|dev)$"}})
    assert result.ok


def test_validate_pattern_no_match():
    result = validate_env({"ENV": "unknown"}, {"ENV": {"pattern": "^(prod|staging|dev)$"}})
    assert not result.ok


def test_validate_allowed_values_valid():
    result = validate_env({"LOG": "info"}, {"LOG": {"allowed": ["debug", "info", "warn"]}})
    assert result.ok


def test_validate_allowed_values_invalid():
    result = validate_env({"LOG": "verbose"}, {"LOG": {"allowed": ["debug", "info"]}})
    assert not result.ok
    assert any("allowed" in i.message for i in result.issues)
