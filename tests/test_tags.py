"""Tests for envault.tags module."""

import pytest
from pathlib import Path
from envault.tags import set_tag, get_tag, delete_tag, list_tags, _tags_path


@pytest.fixture
def tmp_tags(tmp_path):
    """Fixture providing a temp directory for tag storage."""
    return tmp_path


def test_set_tag_creates_file(tmp_tags):
    set_tag("myapp", "production", 3, base_dir=tmp_tags)
    assert _tags_path("myapp", tmp_tags).exists()


def test_get_tag_returns_version(tmp_tags):
    set_tag("myapp", "staging", 5, base_dir=tmp_tags)
    assert get_tag("myapp", "staging", base_dir=tmp_tags) == 5


def test_get_tag_missing_returns_none(tmp_tags):
    assert get_tag("myapp", "nonexistent", base_dir=tmp_tags) is None


def test_set_tag_overwrites_existing(tmp_tags):
    set_tag("myapp", "production", 1, base_dir=tmp_tags)
    set_tag("myapp", "production", 7, base_dir=tmp_tags)
    assert get_tag("myapp", "production", base_dir=tmp_tags) == 7


def test_delete_tag_removes_entry(tmp_tags):
    set_tag("myapp", "release", 2, base_dir=tmp_tags)
    result = delete_tag("myapp", "release", base_dir=tmp_tags)
    assert result is True
    assert get_tag("myapp", "release", base_dir=tmp_tags) is None


def test_delete_tag_nonexistent_returns_false(tmp_tags):
    result = delete_tag("myapp", "ghost", base_dir=tmp_tags)
    assert result is False


def test_list_tags_empty(tmp_tags):
    assert list_tags("myapp", base_dir=tmp_tags) == {}


def test_list_tags_returns_all(tmp_tags):
    set_tag("myapp", "production", 4, base_dir=tmp_tags)
    set_tag("myapp", "staging", 6, base_dir=tmp_tags)
    tags = list_tags("myapp", base_dir=tmp_tags)
    assert tags == {"production": 4, "staging": 6}


def test_tags_isolated_per_vault(tmp_tags):
    set_tag("app1", "production", 1, base_dir=tmp_tags)
    set_tag("app2", "production", 9, base_dir=tmp_tags)
    assert get_tag("app1", "production", base_dir=tmp_tags) == 1
    assert get_tag("app2", "production", base_dir=tmp_tags) == 9


def test_delete_tag_leaves_others_intact(tmp_tags):
    set_tag("myapp", "production", 3, base_dir=tmp_tags)
    set_tag("myapp", "staging", 5, base_dir=tmp_tags)
    delete_tag("myapp", "staging", base_dir=tmp_tags)
    assert get_tag("myapp", "production", base_dir=tmp_tags) == 3
    assert get_tag("myapp", "staging", base_dir=tmp_tags) is None
