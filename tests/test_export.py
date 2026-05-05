"""Tests for envault.export module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.export import (
    export_env,
    to_dotenv,
    to_json,
    to_shell_export,
    _parse_env_pairs,
)

SAMPLE_ENV = """# Database config
DB_HOST=localhost
DB_PORT=5432
DB_NAME=myapp
SECRET_KEY=s3cr3t=with=equals
"""


def test_parse_env_pairs_basic():
    pairs = _parse_env_pairs(SAMPLE_ENV)
    assert pairs["DB_HOST"] == "localhost"
    assert pairs["DB_PORT"] == "5432"
    assert pairs["DB_NAME"] == "myapp"


def test_parse_env_pairs_ignores_comments():
    pairs = _parse_env_pairs(SAMPLE_ENV)
    assert all(not k.startswith("#") for k in pairs)


def test_parse_env_pairs_handles_equals_in_value():
    pairs = _parse_env_pairs(SAMPLE_ENV)
    assert pairs["SECRET_KEY"] == "s3cr3t=with=equals"


def test_to_dotenv_returns_string():
    result = to_dotenv(SAMPLE_ENV)
    assert "DB_HOST=localhost" in result
    assert result.endswith("\n")


def test_to_dotenv_writes_file(tmp_path: Path):
    out = tmp_path / "output.env"
    to_dotenv(SAMPLE_ENV, output_path=out)
    assert out.exists()
    assert "DB_PORT=5432" in out.read_text()


def test_to_json_returns_valid_json():
    result = to_json(SAMPLE_ENV)
    data = json.loads(result)
    assert data["DB_HOST"] == "localhost"
    assert data["SECRET_KEY"] == "s3cr3t=with=equals"


def test_to_json_writes_file(tmp_path: Path):
    out = tmp_path / "output.json"
    to_json(SAMPLE_ENV, output_path=out)
    data = json.loads(out.read_text())
    assert data["DB_NAME"] == "myapp"


def test_to_shell_export_format():
    result = to_shell_export(SAMPLE_ENV)
    assert 'export DB_HOST="localhost"' in result
    assert 'export SECRET_KEY="s3cr3t=with=equals"' in result
    assert result.endswith("\n")


def test_to_shell_export_writes_file(tmp_path: Path):
    out = tmp_path / "exports.sh"
    to_shell_export(SAMPLE_ENV, output_path=out)
    content = out.read_text()
    assert 'export DB_PORT="5432"' in content


def test_export_env_dispatches_dotenv():
    result = export_env(SAMPLE_ENV, fmt="dotenv")
    assert "DB_HOST=localhost" in result


def test_export_env_dispatches_json():
    result = export_env(SAMPLE_ENV, fmt="json")
    data = json.loads(result)
    assert "DB_HOST" in data


def test_export_env_dispatches_shell():
    result = export_env(SAMPLE_ENV, fmt="shell")
    assert "export" in result


def test_export_env_invalid_format_raises():
    with pytest.raises(ValueError, match="Unsupported format"):
        export_env(SAMPLE_ENV, fmt="yaml")
