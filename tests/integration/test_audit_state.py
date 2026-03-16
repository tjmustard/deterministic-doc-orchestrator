"""Integration tests for audit_state.py.

Covers the 5 deterministic scenarios from MiniPRD_AuditState.md § 5.
"""

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parents[2]))

from audit_state import reconcile
from state_graph_schema import load_state, save_state

LOCK_FILENAME = ".orchestrator.lock"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _minimal_state(module_id: str = "novelty", status: str = "pending_extraction") -> dict:
    return {
        "document_meta": {"title": "Test", "confidence_score": 9},
        "modules": [{"id": module_id, "status": status}],
    }


def _scaffold_workspace(workspace: Path, module_id: str, status: str) -> dict:
    """Write a state_graph.yml and return the state dict."""
    state = _minimal_state(module_id, status)
    save_state(workspace, state)
    return state


def _make_draft(workspace: Path, module_id: str) -> Path:
    active = workspace / "active"
    active.mkdir(parents=True, exist_ok=True)
    draft = active / f"draft_{module_id}.md"
    draft.write_text("# Draft\n", encoding="utf-8")
    return draft


def _make_compiled(workspace: Path, module_id: str) -> Path:
    compiled = workspace / "compiled"
    compiled.mkdir(parents=True, exist_ok=True)
    final = compiled / f"final_{module_id}.md"
    final.write_text("# Final\n", encoding="utf-8")
    return final


# ---------------------------------------------------------------------------
# Test 1 (MiniPRD) — Rule 1: compiled exists → forced to integrated
# ---------------------------------------------------------------------------


def test_compiled_exists_forces_integrated(tmp_path: Path) -> None:
    """Rule 1: if compiled/final_<id>.md exists and status != integrated, force integrated."""
    state = _scaffold_workspace(tmp_path, "novelty", "pending_integration")
    _make_compiled(tmp_path, "novelty")

    state, changes, alerts = reconcile(tmp_path, state)

    assert any("novelty" in c and "integrated" in c for c in changes)
    module = next(m for m in state["modules"] if m["id"] == "novelty")
    assert module["status"] == "integrated"


def test_compiled_exists_saves_to_disk(tmp_path: Path) -> None:
    """Rule 1 fix is persisted to disk when changes are present."""
    state = _scaffold_workspace(tmp_path, "novelty", "pending_integration")
    _make_compiled(tmp_path, "novelty")

    state, changes, _ = reconcile(tmp_path, state)
    if changes:
        save_state(tmp_path, state)

    loaded = load_state(tmp_path)
    module = next(m for m in loaded["modules"] if m["id"] == "novelty")
    assert module["status"] == "integrated"


# ---------------------------------------------------------------------------
# Test 2 (MiniPRD) — Rule 2: draft missing → reverted to pending_extraction
# ---------------------------------------------------------------------------


def test_draft_missing_reverts_to_pending_extraction(tmp_path: Path) -> None:
    """Rule 2: status in [extracted, pending_interview, pending_integration] but no draft → revert."""
    state = _scaffold_workspace(tmp_path, "novelty", "extracted")
    # Deliberately do NOT create active/draft_novelty.md.

    state, changes, alerts = reconcile(tmp_path, state)

    assert any("novelty" in c and "pending_extraction" in c for c in changes)
    module = next(m for m in state["modules"] if m["id"] == "novelty")
    assert module["status"] == "pending_extraction"


def test_draft_present_no_revert(tmp_path: Path) -> None:
    """Rule 2: if draft file exists, status is NOT reverted."""
    state = _scaffold_workspace(tmp_path, "novelty", "extracted")
    _make_draft(tmp_path, "novelty")

    state, changes, alerts = reconcile(tmp_path, state)

    revert_changes = [c for c in changes if "pending_extraction" in c]
    assert not revert_changes


# ---------------------------------------------------------------------------
# Test 3 (MiniPRD) — Rule 3: failed module → ALERT, status unchanged
# ---------------------------------------------------------------------------


def test_failed_module_produces_alert(tmp_path: Path) -> None:
    """Rule 3: failed module emits AUDIT ALERT."""
    state = _scaffold_workspace(tmp_path, "novelty", "failed")

    state, changes, alerts = reconcile(tmp_path, state)

    assert any("novelty" in a and "failed" in a for a in alerts)


def test_failed_module_status_unchanged(tmp_path: Path) -> None:
    """Rule 3: failed module status must NOT be auto-recovered."""
    state = _scaffold_workspace(tmp_path, "novelty", "failed")

    state, changes, alerts = reconcile(tmp_path, state)

    failed_changes = [c for c in changes if "novelty" in c]
    assert not failed_changes
    module = next(m for m in state["modules"] if m["id"] == "novelty")
    assert module["status"] == "failed"


# ---------------------------------------------------------------------------
# Test 4 (MiniPRD) — Rule 4: stale lockfile → ALERT, lockfile NOT deleted
# ---------------------------------------------------------------------------


def test_stale_lock_produces_alert(tmp_path: Path) -> None:
    """Rule 4: stale .orchestrator.lock emits AUDIT ALERT."""
    state = _scaffold_workspace(tmp_path, "novelty", "pending_extraction")
    (tmp_path / LOCK_FILENAME).touch()

    state, changes, alerts = reconcile(tmp_path, state)

    assert any(LOCK_FILENAME in a for a in alerts)


def test_stale_lock_not_deleted(tmp_path: Path) -> None:
    """Rule 4: reconcile() must NOT delete the lockfile."""
    state = _scaffold_workspace(tmp_path, "novelty", "pending_extraction")
    lock = tmp_path / LOCK_FILENAME
    lock.touch()

    reconcile(tmp_path, state)

    assert lock.exists()


# ---------------------------------------------------------------------------
# Test 5 (MiniPRD) — consistent workspace → "consistent" message, no changes
# ---------------------------------------------------------------------------


def test_consistent_workspace_no_changes(tmp_path: Path, capsys) -> None:
    """Rule 5: no issues → reconcile returns no changes or alerts."""
    state = _scaffold_workspace(tmp_path, "novelty", "pending_extraction")
    # pending_extraction requires no draft, and no compiled file exists.

    state, changes, alerts = reconcile(tmp_path, state)

    assert not changes
    assert not alerts


def test_consistent_workspace_prints_consistent_message(tmp_path: Path, capsys) -> None:
    """Rule 5: print_summary with empty changes/alerts prints 'consistent' message."""
    from audit_state import print_summary

    print_summary([], [])

    captured = capsys.readouterr()
    assert "consistent" in captured.out.lower()
