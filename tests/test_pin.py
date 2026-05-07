"""Tests for envault.pin module."""

from __future__ import annotations

import pytest

from envault.pin import PinError, delete_pin, get_pin, list_pins, set_pin


@pytest.fixture()
def tmp_pin(tmp_path):
    return str(tmp_path)


def test_set_pin_creates_file(tmp_pin):
    set_pin("production", 3, vault_dir=tmp_pin)
    from envault.pin import _pins_path
    assert _pins_path(tmp_pin).exists()


def test_get_pin_returns_version(tmp_pin):
    set_pin("production", 3, vault_dir=tmp_pin)
    assert get_pin("production", vault_dir=tmp_pin) == 3


def test_get_pin_missing_returns_none(tmp_pin):
    assert get_pin("nonexistent", vault_dir=tmp_pin) is None


def test_set_pin_overwrites_existing(tmp_pin):
    set_pin("staging", 1, vault_dir=tmp_pin)
    set_pin("staging", 5, vault_dir=tmp_pin)
    assert get_pin("staging", vault_dir=tmp_pin) == 5


def test_set_pin_invalid_version_raises(tmp_pin):
    with pytest.raises(PinError):
        set_pin("production", 0, vault_dir=tmp_pin)


def test_set_pin_negative_version_raises(tmp_pin):
    with pytest.raises(PinError):
        set_pin("production", -2, vault_dir=tmp_pin)


def test_delete_pin_returns_true_when_exists(tmp_pin):
    set_pin("dev", 2, vault_dir=tmp_pin)
    assert delete_pin("dev", vault_dir=tmp_pin) is True
    assert get_pin("dev", vault_dir=tmp_pin) is None


def test_delete_pin_returns_false_when_missing(tmp_pin):
    assert delete_pin("ghost", vault_dir=tmp_pin) is False


def test_list_pins_empty(tmp_pin):
    assert list_pins(vault_dir=tmp_pin) == {}


def test_list_pins_returns_all(tmp_pin):
    set_pin("production", 4, vault_dir=tmp_pin)
    set_pin("staging", 2, vault_dir=tmp_pin)
    result = list_pins(vault_dir=tmp_pin)
    assert result == {"production": 4, "staging": 2}


def test_multiple_vaults_independent(tmp_pin):
    set_pin("a", 1, vault_dir=tmp_pin)
    set_pin("b", 9, vault_dir=tmp_pin)
    delete_pin("a", vault_dir=tmp_pin)
    assert get_pin("a", vault_dir=tmp_pin) is None
    assert get_pin("b", vault_dir=tmp_pin) == 9
