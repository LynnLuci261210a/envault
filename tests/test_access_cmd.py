"""Tests for envault.access_cmd CLI commands."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.access_cmd import access_cmd
from envault.access import grant
from pathlib import Path
import os


@pytest.fixture
def runner():
    return CliRunner()


def test_access_grant_and_show(runner, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(access_cmd, ["grant", "myvault", "alice", "read"])
    assert result.exit_code == 0
    assert "Granted" in result.output

    result = runner.invoke(access_cmd, ["show", "myvault", "alice"])
    assert result.exit_code == 0
    assert "read" in result.output


def test_access_grant_invalid_permission(runner, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(access_cmd, ["grant", "myvault", "alice", "superuser"])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_access_revoke(runner, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(access_cmd, ["grant", "myvault", "bob", "write"])
    result = runner.invoke(access_cmd, ["revoke", "myvault", "bob", "write"])
    assert result.exit_code == 0
    assert "Revoked" in result.output


def test_access_revoke_absent(runner, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(access_cmd, ["revoke", "myvault", "ghost", "read"])
    assert result.exit_code == 0
    assert "did not hold" in result.output


def test_access_check_allowed(runner, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(access_cmd, ["grant", "myvault", "carol", "read"])
    result = runner.invoke(access_cmd, ["check", "myvault", "carol", "read"])
    assert result.exit_code == 0
    assert "ALLOWED" in result.output


def test_access_check_denied(runner, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(access_cmd, ["check", "myvault", "nobody", "write"])
    assert result.exit_code == 1
    assert "DENIED" in result.output


def test_access_show_all_principals(runner, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(access_cmd, ["grant", "myvault", "alice", "read"])
    runner.invoke(access_cmd, ["grant", "myvault", "bob", "admin"])
    result = runner.invoke(access_cmd, ["show", "myvault"])
    assert result.exit_code == 0
    assert "alice" in result.output
    assert "bob" in result.output


def test_access_show_empty_vault(runner, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(access_cmd, ["show", "emptyvault"])
    assert result.exit_code == 0
    assert "No access entries" in result.output
