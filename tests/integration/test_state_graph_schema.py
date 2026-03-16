"""Integration tests for state_graph_schema.py.

Covers the 4 deterministic scenarios from MiniPRD_StateGraph.md § 5,
plus save/load roundtrip and valid-status mutation.
"""

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parents[2]))

from state_graph_schema import (
    VALID_STATUSES,
    get_module,
    load_state,
    save_state,
    set_module_status,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _minimal_state(module_id: str = "novelty", status: str = "pending_extraction") -> dict:
    """Return a minimal valid state graph dict."""
    return {
        "document_meta": {"title": "Test", "confidence_score": 9},
        "modules": [{"id": module_id, "status": status}],
    }


def _write_state(workspace: Path, state: dict) -> None:
    """Write state directly (bypasses atomic helper — for setup only)."""
    state_file = workspace / "state_graph.yml"
    state_file.write_text(
        yaml.dump(state, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Test 1 (MiniPRD) — atomic write: .tmp is used; yml unchanged on truncation
# ---------------------------------------------------------------------------


def test_save_state_writes_via_tmp(tmp_path: Path) -> None:
    """save_state() writes to .tmp then renames — no stale .tmp left behind."""
    state = _minimal_state()
    save_state(tmp_path, state)

    state_file = tmp_path / "state_graph.yml"
    tmp_file = tmp_path / "state_graph.yml.tmp"

    assert state_file.exists()
    # After a clean save the .tmp file must NOT persist.
    assert not tmp_file.exists()


def test_save_state_roundtrip(tmp_path: Path) -> None:
    """save_state() + load_state() round-trips the dict faithfully."""
    state = _minimal_state()
    save_state(tmp_path, state)
    loaded = load_state(tmp_path)
    assert loaded == state


# ---------------------------------------------------------------------------
# Test 2 (MiniPRD) — load_state with missing file → SystemExit(1)
# ---------------------------------------------------------------------------


def test_load_state_missing_file_exits(tmp_path: Path) -> None:
    """load_state() raises SystemExit(1) and prints 'State graph not found'."""
    with pytest.raises(SystemExit) as exc_info:
        load_state(tmp_path)
    assert exc_info.value.code == 1


def test_load_state_missing_file_message(tmp_path: Path, capsys) -> None:
    """load_state() error message contains 'State graph not found'."""
    with pytest.raises(SystemExit):
        load_state(tmp_path)
    captured = capsys.readouterr()
    assert "State graph not found" in captured.err


# ---------------------------------------------------------------------------
# Test 3 (MiniPRD) — set_module_status with invalid status → ValueError
# ---------------------------------------------------------------------------


def test_set_module_status_invalid_raises(tmp_path: Path) -> None:
    """set_module_status() raises ValueError for an unrecognised status."""
    state = _minimal_state()
    with pytest.raises(ValueError, match="invalid_status"):
        set_module_status(state, "novelty", "invalid_status")


def test_set_module_status_valid(tmp_path: Path) -> None:
    """set_module_status() accepts every VALID_STATUSES value."""
    for valid_status in VALID_STATUSES:
        state = _minimal_state()
        result = set_module_status(state, "novelty", valid_status)
        assert get_module(result, "novelty")["status"] == valid_status


# ---------------------------------------------------------------------------
# Test 4 (MiniPRD) — get_module with non-existent id → KeyError
# ---------------------------------------------------------------------------


def test_get_module_missing_raises(tmp_path: Path) -> None:
    """get_module() raises KeyError containing the missing module ID."""
    state = _minimal_state()
    with pytest.raises(KeyError, match="does_not_exist"):
        get_module(state, "does_not_exist")


def test_get_module_returns_correct_dict() -> None:
    """get_module() returns the right module when it exists."""
    state = _minimal_state("my_module")
    module = get_module(state, "my_module")
    assert module["id"] == "my_module"


# ---------------------------------------------------------------------------
# Additional — invalid YAML in state file
# ---------------------------------------------------------------------------


def test_load_state_invalid_yaml_exits(tmp_path: Path) -> None:
    """load_state() raises SystemExit(1) when state_graph.yml contains invalid YAML."""
    (tmp_path / "state_graph.yml").write_text(
        "key: [unclosed bracket\n", encoding="utf-8"
    )
    with pytest.raises(SystemExit) as exc_info:
        load_state(tmp_path)
    assert exc_info.value.code == 1
