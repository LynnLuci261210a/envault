"""Tests for envault.template module."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.template import (
    TemplateError,
    list_placeholders,
    render_file,
    render_string,
)


# ---------------------------------------------------------------------------
# render_string
# ---------------------------------------------------------------------------

def test_render_string_basic():
    result = render_string("Hello, {{NAME}}!", {"NAME": "world"})
    assert result == "Hello, world!"


def test_render_string_multiple_placeholders():
    tpl = "{{HOST}}:{{PORT}}/{{DB}}"
    env = {"HOST": "localhost", "PORT": "5432", "DB": "mydb"}
    assert render_string(tpl, env) == "localhost:5432/mydb"


def test_render_string_repeated_placeholder():
    result = render_string("{{A}} and {{A}}", {"A": "x"})
    assert result == "x and x"


def test_render_string_strict_raises_on_missing():
    with pytest.raises(TemplateError, match="Unresolved placeholders"):
        render_string("{{MISSING}}", {}, strict=True)


def test_render_string_non_strict_leaves_placeholder():
    result = render_string("{{MISSING}}", {}, strict=False)
    assert result == "{{MISSING}}"


def test_render_string_whitespace_in_placeholder():
    result = render_string("{{ KEY }}", {"KEY": "value"})
    assert result == "value"


def test_render_string_no_placeholders():
    text = "no placeholders here"
    assert render_string(text, {}) == text


# ---------------------------------------------------------------------------
# list_placeholders
# ---------------------------------------------------------------------------

def test_list_placeholders_returns_sorted_unique():
    tpl = "{{B}} {{A}} {{B}} {{C}}"
    assert list_placeholders(tpl) == ["A", "B", "C"]


def test_list_placeholders_empty():
    assert list_placeholders("no vars here") == []


# ---------------------------------------------------------------------------
# render_file
# ---------------------------------------------------------------------------

def test_render_file_reads_and_renders(tmp_path: Path):
    src = tmp_path / "app.conf.tpl"
    src.write_text("db_url = {{DB_URL}}\n", encoding="utf-8")
    result = render_file(src, {"DB_URL": "postgres://localhost/test"})
    assert result == "db_url = postgres://localhost/test\n"


def test_render_file_writes_dest(tmp_path: Path):
    src = tmp_path / "nginx.conf.tpl"
    src.write_text("server_name {{HOST}};\n", encoding="utf-8")
    dest = tmp_path / "out" / "nginx.conf"
    render_file(src, {"HOST": "example.com"}, dest=dest)
    assert dest.exists()
    assert dest.read_text() == "server_name example.com;\n"


def test_render_file_missing_src_raises(tmp_path: Path):
    with pytest.raises(TemplateError, match="not found"):
        render_file(tmp_path / "nonexistent.tpl", {})


def test_render_file_strict_raises_on_missing_key(tmp_path: Path):
    src = tmp_path / "t.tpl"
    src.write_text("{{UNDEFINED}}", encoding="utf-8")
    with pytest.raises(TemplateError, match="UNDEFINED"):
        render_file(src, {}, strict=True)
