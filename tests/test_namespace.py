"""Tests for envault.namespace."""

from __future__ import annotations

import pytest

from envault.namespace import (
    NamespaceError,
    add_vault,
    delete_namespace,
    get_namespace,
    list_namespaces,
    list_vaults,
    remove_vault,
)


@pytest.fixture(autouse=True)
def tmp_namespace(tmp_path, monkeypatch):
    import envault.namespace as ns_mod
    monkeypatch.setattr(ns_mod, "ENVAULT_DIR", tmp_path / ".envault")
    yield


def test_add_vault_creates_namespace():
    add_vault("production", "app")
    assert "production" in list_namespaces()


def test_add_vault_stores_vault_name():
    add_vault("staging", "api")
    assert "api" in list_vaults("staging")


def test_add_vault_idempotent():
    add_vault("prod", "web")
    add_vault("prod", "web")
    assert list_vaults("prod").count("web") == 1


def test_add_vault_multiple_vaults():
    add_vault("dev", "frontend")
    add_vault("dev", "backend")
    vaults = list_vaults("dev")
    assert "frontend" in vaults
    assert "backend" in vaults


def test_add_vault_empty_name_raises():
    with pytest.raises(NamespaceError):
        add_vault("", "myvault")


def test_remove_vault_returns_true():
    add_vault("ns", "v1")
    assert remove_vault("ns", "v1") is True


def test_remove_vault_absent_returns_false():
    assert remove_vault("ns", "ghost") is False


def test_remove_vault_cleans_empty_namespace():
    add_vault("solo", "only")
    remove_vault("solo", "only")
    assert "solo" not in list_namespaces()


def test_list_vaults_empty_namespace():
    assert list_vaults("nonexistent") == []


def test_list_namespaces_sorted():
    add_vault("zebra", "z")
    add_vault("alpha", "a")
    ns = list_namespaces()
    assert ns == sorted(ns)


def test_get_namespace_returns_correct():
    add_vault("myns", "myvault")
    assert get_namespace("myvault") == "myns"


def test_get_namespace_missing_returns_none():
    assert get_namespace("unknown") is None


def test_delete_namespace_returns_true():
    add_vault("temp", "v")
    assert delete_namespace("temp") is True


def test_delete_namespace_missing_returns_false():
    assert delete_namespace("nope") is False


def test_delete_namespace_removes_all_vaults():
    add_vault("gone", "v1")
    add_vault("gone", "v2")
    delete_namespace("gone")
    assert list_vaults("gone") == []
