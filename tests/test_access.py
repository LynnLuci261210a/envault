"""Tests for envault.access module."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.access import (
    AccessError,
    grant,
    revoke,
    get_permissions,
    list_principals,
    has_permission,
)


@pytest.fixture
def tmp_vault(tmp_path: Path) -> tuple[str, Path]:
    return "myvault", tmp_path


def test_grant_creates_entry(tmp_vault):
    vault, base = tmp_vault
    grant(vault, "alice", "read", base_dir=base)
    perms = get_permissions(vault, "alice", base_dir=base)
    assert "read" in perms


def test_grant_multiple_permissions(tmp_vault):
    vault, base = tmp_vault
    grant(vault, "bob", "read", base_dir=base)
    grant(vault, "bob", "write", base_dir=base)
    perms = get_permissions(vault, "bob", base_dir=base)
    assert set(perms) == {"read", "write"}


def test_grant_invalid_permission_raises(tmp_vault):
    vault, base = tmp_vault
    with pytest.raises(AccessError, match="Invalid permission"):
        grant(vault, "eve", "superuser", base_dir=base)


def test_grant_idempotent(tmp_vault):
    vault, base = tmp_vault
    grant(vault, "alice", "read", base_dir=base)
    grant(vault, "alice", "read", base_dir=base)
    perms = get_permissions(vault, "alice", base_dir=base)
    assert perms.count("read") == 1


def test_revoke_removes_permission(tmp_vault):
    vault, base = tmp_vault
    grant(vault, "alice", "read", base_dir=base)
    grant(vault, "alice", "write", base_dir=base)
    changed = revoke(vault, "alice", "read", base_dir=base)
    assert changed is True
    perms = get_permissions(vault, "alice", base_dir=base)
    assert "read" not in perms
    assert "write" in perms


def test_revoke_absent_permission_returns_false(tmp_vault):
    vault, base = tmp_vault
    changed = revoke(vault, "ghost", "read", base_dir=base)
    assert changed is False


def test_revoke_last_permission_removes_principal(tmp_vault):
    vault, base = tmp_vault
    grant(vault, "carol", "read", base_dir=base)
    revoke(vault, "carol", "read", base_dir=base)
    acl = list_principals(vault, base_dir=base)
    assert "carol" not in acl


def test_list_principals_empty_when_no_acl(tmp_vault):
    vault, base = tmp_vault
    acl = list_principals(vault, base_dir=base)
    assert acl == {}


def test_list_principals_returns_all(tmp_vault):
    vault, base = tmp_vault
    grant(vault, "alice", "read", base_dir=base)
    grant(vault, "bob", "admin", base_dir=base)
    acl = list_principals(vault, base_dir=base)
    assert "alice" in acl
    assert "bob" in acl


def test_has_permission_direct(tmp_vault):
    vault, base = tmp_vault
    grant(vault, "alice", "write", base_dir=base)
    assert has_permission(vault, "alice", "write", base_dir=base) is True
    assert has_permission(vault, "alice", "read", base_dir=base) is False


def test_has_permission_admin_grants_all(tmp_vault):
    vault, base = tmp_vault
    grant(vault, "root", "admin", base_dir=base)
    assert has_permission(vault, "root", "read", base_dir=base) is True
    assert has_permission(vault, "root", "write", base_dir=base) is True


def test_has_permission_missing_principal(tmp_vault):
    vault, base = tmp_vault
    assert has_permission(vault, "nobody", "read", base_dir=base) is False
