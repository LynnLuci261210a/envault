"""Tests for envault.alias."""

from __future__ import annotations

import pytest

from envault.alias import (
    AliasError,
    delete_alias,
    get_alias,
    list_aliases,
    resolve_alias,
    set_alias,
)


@pytest.fixture()
def tmp_alias(tmp_path):
    """Return a temporary vault directory."""
    return tmp_path


def test_set_alias_creates_file(tmp_alias):
    set_alias(tmp_alias, "prod", "production")
    assert (tmp_alias / ".envault" / "aliases.json").exists()


def test_get_alias_returns_vault_name(tmp_alias):
    set_alias(tmp_alias, "prod", "production")
    assert get_alias(tmp_alias, "prod") == "production"


def test_get_alias_missing_returns_none(tmp_alias):
    assert get_alias(tmp_alias, "nonexistent") is None


def test_set_alias_overwrites_existing(tmp_alias):
    set_alias(tmp_alias, "prod", "production")
    set_alias(tmp_alias, "prod", "prod-v2")
    assert get_alias(tmp_alias, "prod") == "prod-v2"


def test_set_alias_invalid_name_raises(tmp_alias):
    with pytest.raises(AliasError, match="Invalid alias name"):
        set_alias(tmp_alias, "bad-name!", "some-vault")


def test_set_alias_empty_name_raises(tmp_alias):
    with pytest.raises(AliasError, match="Invalid alias name"):
        set_alias(tmp_alias, "", "some-vault")


def test_delete_alias_returns_true_when_found(tmp_alias):
    set_alias(tmp_alias, "staging", "staging-env")
    assert delete_alias(tmp_alias, "staging") is True
    assert get_alias(tmp_alias, "staging") is None


def test_delete_alias_returns_false_when_missing(tmp_alias):
    assert delete_alias(tmp_alias, "ghost") is False


def test_list_aliases_empty(tmp_alias):
    assert list_aliases(tmp_alias) == {}


def test_list_aliases_returns_all(tmp_alias):
    set_alias(tmp_alias, "dev", "development")
    set_alias(tmp_alias, "prod", "production")
    result = list_aliases(tmp_alias)
    assert result == {"dev": "development", "prod": "production"}


def test_resolve_alias_known(tmp_alias):
    set_alias(tmp_alias, "dev", "development")
    assert resolve_alias(tmp_alias, "dev") == "development"


def test_resolve_alias_unknown_returns_name(tmp_alias):
    assert resolve_alias(tmp_alias, "unknown-vault") == "unknown-vault"
