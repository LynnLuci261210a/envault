"""Tests for envault.merge."""
from __future__ import annotations

import pytest

from envault.merge import merge_envs, MergeResult, MergeConflict, MergeError


BASE = """DB_HOST=localhost
DB_PORT=5432
SECRET=old_secret
"""

OURS = """DB_HOST=localhost
DB_PORT=5432
SECRET=new_secret_ours
NEW_KEY=added_by_ours
"""

THEIRS = """DB_HOST=production.db
DB_PORT=5432
SECRET=new_secret_theirs
"""


def test_merge_no_conflict_ours_only():
    result = merge_envs(BASE, OURS, BASE)
    assert not result.has_conflicts
    assert result.merged["SECRET"] == "new_secret_ours"
    assert result.merged["NEW_KEY"] == "added_by_ours"


def test_merge_no_conflict_theirs_only():
    result = merge_envs(BASE, BASE, THEIRS)
    assert not result.has_conflicts
    assert result.merged["DB_HOST"] == "production.db"
    assert result.merged["SECRET"] == "new_secret_theirs"


def test_merge_conflict_detected():
    result = merge_envs(BASE, OURS, THEIRS)
    assert result.has_conflicts
    keys_in_conflict = [c.key for c in result.conflicts]
    assert "SECRET" in keys_in_conflict


def test_merge_conflict_strategy_ours():
    result = merge_envs(BASE, OURS, THEIRS, strategy="ours")
    assert result.merged["SECRET"] == "new_secret_ours"


def test_merge_conflict_strategy_theirs():
    result = merge_envs(BASE, OURS, THEIRS, strategy="theirs")
    assert result.merged["SECRET"] == "new_secret_theirs"


def test_merge_key_added_only_in_ours():
    result = merge_envs(BASE, OURS, THEIRS, strategy="ours")
    assert result.merged["NEW_KEY"] == "added_by_ours"


def test_merge_key_removed_in_theirs():
    # THEIRS removes SECRET compared to BASE; OURS changes it — conflict
    theirs_no_secret = "DB_HOST=localhost\nDB_PORT=5432\n"
    result = merge_envs(BASE, OURS, theirs_no_secret, strategy="ours")
    conflict_keys = [c.key for c in result.conflicts]
    assert "SECRET" in conflict_keys


def test_merge_invalid_strategy_raises():
    with pytest.raises(MergeError, match="Unknown strategy"):
        merge_envs(BASE, OURS, THEIRS, strategy="invalid")


def test_merge_result_summary_clean():
    result = merge_envs(BASE, BASE, BASE)
    assert "cleanly" in result.summary()


def test_merge_result_summary_with_conflicts():
    result = merge_envs(BASE, OURS, THEIRS)
    summary = result.summary()
    assert "conflict" in summary.lower()


def test_merge_conflict_str():
    c = MergeConflict(key="FOO", base_value="a", ours="b", theirs="c")
    s = str(c)
    assert "FOO" in s
    assert "ours" in s
    assert "theirs" in s


def test_merge_both_unchanged_key_preserved():
    result = merge_envs(BASE, BASE, BASE)
    assert result.merged["DB_HOST"] == "localhost"
    assert result.merged["DB_PORT"] == "5432"
