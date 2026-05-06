"""Tests for envault/profile.py"""

import pytest
from pathlib import Path

from envault.profile import (
    set_profile,
    get_profile,
    delete_profile,
    list_profiles,
)


@pytest.fixture
def tmp_profile(tmp_path):
    return tmp_path


def test_set_profile_creates_file(tmp_profile):
    set_profile(tmp_profile, "dev", "dev-vault")
    assert (tmp_profile / ".envault" / "profiles.json").exists()


def test_get_profile_returns_vault_name(tmp_profile):
    set_profile(tmp_profile, "staging", "staging-vault")
    assert get_profile(tmp_profile, "staging") == "staging-vault"


def test_get_profile_missing_returns_none(tmp_profile):
    assert get_profile(tmp_profile, "nonexistent") is None


def test_set_profile_overwrites_existing(tmp_profile):
    set_profile(tmp_profile, "prod", "old-vault")
    set_profile(tmp_profile, "prod", "new-vault")
    assert get_profile(tmp_profile, "prod") == "new-vault"


def test_delete_profile_removes_entry(tmp_profile):
    set_profile(tmp_profile, "dev", "dev-vault")
    result = delete_profile(tmp_profile, "dev")
    assert result is True
    assert get_profile(tmp_profile, "dev") is None


def test_delete_profile_missing_returns_false(tmp_profile):
    result = delete_profile(tmp_profile, "ghost")
    assert result is False


def test_list_profiles_empty(tmp_profile):
    assert list_profiles(tmp_profile) == []


def test_list_profiles_returns_all(tmp_profile):
    set_profile(tmp_profile, "dev", "dev-vault")
    set_profile(tmp_profile, "prod", "prod-vault")
    profiles = list_profiles(tmp_profile)
    names = [p["name"] for p in profiles]
    assert "dev" in names
    assert "prod" in names
    assert len(profiles) == 2


def test_list_profiles_sorted_alphabetically(tmp_profile):
    set_profile(tmp_profile, "staging", "s-vault")
    set_profile(tmp_profile, "dev", "d-vault")
    set_profile(tmp_profile, "prod", "p-vault")
    names = [p["name"] for p in list_profiles(tmp_profile)]
    assert names == sorted(names)
