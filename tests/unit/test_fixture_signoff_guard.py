"""Unit tests for the fixture sign-off guard (TestSuite Test 3, SuperPRD RT#13).

The guard makes the "agents never promote a fixture" rule mechanical: a staged
change under ``tests/fixtures/`` is rejected unless a human sign-off token is
present. These tests exercise the pure decision functions directly (no git), and
prove rejection without the token and acceptance with it.
"""

import pytest

from scripts.fixture_signoff_guard import (
    SIGNOFF_ENV_VAR,
    FixtureSignoffError,
    assert_fixture_signoff,
    fixtures_touched,
    is_signed_off,
)


def test_fixture_change_without_signoff_is_rejected():
    """A staged fixture change without the sign-off token raises, naming the path."""
    staged = ["tests/fixtures/golden_prd.html", "ddo/build.py"]
    with pytest.raises(FixtureSignoffError, match="golden_prd.html"):
        assert_fixture_signoff(staged, signed_off=False)


def test_fixture_change_with_signoff_is_allowed():
    """The identical staged fixture change passes once the human signs off."""
    staged = ["tests/fixtures/golden_prd.html"]
    assert assert_fixture_signoff(staged, signed_off=True) is None


def test_non_fixture_change_always_allowed_without_token():
    """A diff that never touches ``tests/fixtures/`` is allowed regardless of token."""
    staged = ["ddo/build.py", "tests/unit/test_x.py", "spec/compiled/SuperPRD.md"]
    assert assert_fixture_signoff(staged, signed_off=False) is None


def test_gitkeep_is_not_a_fixture_payload():
    """The structural ``.gitkeep`` placeholder never counts as a fixture change."""
    assert fixtures_touched(["tests/fixtures/.gitkeep"]) == []
    assert assert_fixture_signoff(["tests/fixtures/.gitkeep"], signed_off=False) is None


def test_fixtures_touched_lists_only_payloads_sorted():
    """``fixtures_touched`` returns the sorted fixture payload paths only."""
    staged = [
        "tests/fixtures/z_last.txt",
        "ddo/paths.py",
        "tests/fixtures/a_first.md",
        "tests/fixtures/.gitkeep",
    ]
    assert fixtures_touched(staged) == [
        "tests/fixtures/a_first.md",
        "tests/fixtures/z_last.txt",
    ]


def test_is_signed_off_reads_truthy_env_token():
    """Truthy ``DDO_FIXTURE_SIGNOFF`` values authorise; absence or 0 do not."""
    assert is_signed_off({SIGNOFF_ENV_VAR: "1"}) is True
    assert is_signed_off({SIGNOFF_ENV_VAR: "TRUE"}) is True
    assert is_signed_off({SIGNOFF_ENV_VAR: "yes"}) is True
    assert is_signed_off({SIGNOFF_ENV_VAR: "0"}) is False
    assert is_signed_off({SIGNOFF_ENV_VAR: ""}) is False
    assert is_signed_off({}) is False
