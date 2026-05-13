"""Tests for envault.namespace_cmd CLI commands."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.namespace_cmd import namespace_cmd


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def tmp_namespace(tmp_path, monkeypatch):
    import envault.namespace as ns_mod
    monkeypatch.setattr(ns_mod, "ENVAULT_DIR", tmp_path / ".envault")
    yield


def test_namespace_add_and_list(runner):
    result = runner.invoke(namespace_cmd, ["add", "production", "app"])
    assert result.exit_code == 0
    assert "added" in result.output

    result = runner.invoke(namespace_cmd, ["list", "production"])
    assert result.exit_code == 0
    assert "app" in result.output


def test_namespace_list_all(runner):
    runner.invoke(namespace_cmd, ["add", "ns1", "v1"])
    runner.invoke(namespace_cmd, ["add", "ns2", "v2"])
    result = runner.invoke(namespace_cmd, ["list"])
    assert result.exit_code == 0
    assert "ns1" in result.output
    assert "ns2" in result.output


def test_namespace_list_empty(runner):
    result = runner.invoke(namespace_cmd, ["list"])
    assert result.exit_code == 0
    assert "No namespaces" in result.output


def test_namespace_add_empty_name_fails(runner):
    result = runner.invoke(namespace_cmd, ["add", "", "vault"])
    assert result.exit_code != 0


def test_namespace_remove(runner):
    runner.invoke(namespace_cmd, ["add", "staging", "api"])
    result = runner.invoke(namespace_cmd, ["remove", "staging", "api"])
    assert result.exit_code == 0
    assert "removed" in result.output


def test_namespace_remove_missing(runner):
    result = runner.invoke(namespace_cmd, ["remove", "ns", "ghost"])
    assert result.exit_code != 0


def test_namespace_which(runner):
    runner.invoke(namespace_cmd, ["add", "myns", "myvault"])
    result = runner.invoke(namespace_cmd, ["which", "myvault"])
    assert result.exit_code == 0
    assert "myns" in result.output


def test_namespace_which_missing(runner):
    result = runner.invoke(namespace_cmd, ["which", "unknown"])
    assert result.exit_code != 0


def test_namespace_delete(runner):
    runner.invoke(namespace_cmd, ["add", "temp", "v"])
    result = runner.invoke(namespace_cmd, ["delete", "temp"])
    assert result.exit_code == 0
    assert "deleted" in result.output


def test_namespace_delete_missing(runner):
    result = runner.invoke(namespace_cmd, ["delete", "nope"])
    assert result.exit_code != 0
