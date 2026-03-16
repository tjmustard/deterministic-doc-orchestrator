"""Integration tests for orchestrator.py.

Covers the 6 deterministic scenarios from MiniPRD_Orchestrator.md § 5.
Uses subprocess for CLI tests and direct function calls for unit-level tests.
"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parents[2]))

from orchestrator import acquire_lock, execute_skill, preflight, release_lock, run_reset
from state_graph_schema import load_state, save_state

SCRIPT = Path(__file__).parents[2] / "orchestrator.py"
LOCK_FILENAME = ".orchestrator.lock"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _minimal_state(
    module_id: str = "novelty",
    status: str = "pending_extraction",
    confidence: int = 9,
    skip_adversarial: bool = False,
) -> dict:
    return {
        "document_meta": {"title": "Test", "confidence_score": confidence},
        "personas": [],
        "inputs": [],
        "modules": [
            {
                "id": module_id,
                "status": status,
                "skip_adversarial": skip_adversarial,
                "applied_personas": [],
                "associated_files": {"template": "", "draft": "", "compiled": ""},
            }
        ],
    }


def _scaffold(workspace: Path, state: dict) -> None:
    """Write state_graph.yml into the workspace."""
    save_state(workspace, state)


def _run_orchestrator(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        capture_output=True,
        text=True,
    )


# ---------------------------------------------------------------------------
# Test 2 (MiniPRD) — lockfile already exists → non-zero exit + error message
# ---------------------------------------------------------------------------


def test_lockfile_exists_aborts(tmp_path: Path) -> None:
    """Test 2: existing .orchestrator.lock causes non-zero exit with lockfile message."""
    _scaffold(tmp_path, _minimal_state())
    (tmp_path / LOCK_FILENAME).touch()

    result = _run_orchestrator(["--workspace", str(tmp_path)])

    assert result.returncode != 0
    assert ".orchestrator.lock" in result.stderr


def test_lockfile_not_cleaned_up_by_aborting_start(tmp_path: Path) -> None:
    """If orchestrator aborts due to existing lock, it must not delete the pre-existing lock."""
    _scaffold(tmp_path, _minimal_state())
    lock = tmp_path / LOCK_FILENAME
    lock.touch()

    _run_orchestrator(["--workspace", str(tmp_path)])

    assert lock.exists()


# ---------------------------------------------------------------------------
# Test 3 (MiniPRD) — missing associated file → pre-flight aborts before skill
# ---------------------------------------------------------------------------


def test_preflight_missing_template_aborts(tmp_path: Path) -> None:
    """Test 3: a referenced template file that does not exist causes pre-flight abort."""
    state = _minimal_state()
    state["modules"][0]["associated_files"]["template"] = "templates/missing.md"
    _scaffold(tmp_path, state)

    # The template file does not exist — preflight should abort.
    with pytest.raises(SystemExit) as exc_info:
        preflight(tmp_path, state)
    assert exc_info.value.code == 1


def test_preflight_passes_with_no_associated_files(tmp_path: Path) -> None:
    """preflight() passes cleanly when associated_files values are empty strings."""
    state = _minimal_state()
    # No files to validate — preflight should not raise.
    preflight(tmp_path, state)  # must not raise


# ---------------------------------------------------------------------------
# Test 4 (MiniPRD) — symlink in active/ → pre-flight aborts
# ---------------------------------------------------------------------------


def test_preflight_symlink_in_active_aborts(tmp_path: Path) -> None:
    """Test 4: a symlink in active/ causes pre-flight to abort with non-zero exit."""
    state = _minimal_state()
    active = tmp_path / "active"
    active.mkdir()
    # Create a real file then symlink to it.
    target = tmp_path / "real_file.md"
    target.write_text("content", encoding="utf-8")
    (active / "symlink.md").symlink_to(target)

    with pytest.raises(SystemExit) as exc_info:
        preflight(tmp_path, state)
    assert exc_info.value.code == 1


def test_preflight_symlink_in_compiled_aborts(tmp_path: Path) -> None:
    """Symlinks in compiled/ are also caught by pre-flight."""
    state = _minimal_state()
    compiled = tmp_path / "compiled"
    compiled.mkdir()
    target = tmp_path / "real.md"
    target.write_text("x", encoding="utf-8")
    (compiled / "link.md").symlink_to(target)

    with pytest.raises(SystemExit) as exc_info:
        preflight(tmp_path, state)
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# Test 5 (MiniPRD) — --reset archives compiled and sets pending_integration
# ---------------------------------------------------------------------------


def test_reset_mode_sets_pending_integration(tmp_path: Path) -> None:
    """Test 5: --reset archives compiled output and sets module to pending_integration."""
    state = _minimal_state("novelty", "integrated")
    _scaffold(tmp_path, state)

    # Create compiled/final_novelty.md so archive_compiled has something to move.
    compiled_dir = tmp_path / "compiled"
    compiled_dir.mkdir()
    (compiled_dir / "final_novelty.md").write_text("# Final\n", encoding="utf-8")

    result = _run_orchestrator(["--workspace", str(tmp_path), "--reset", "novelty"])

    assert result.returncode == 0
    loaded = load_state(tmp_path)
    module = next(m for m in loaded["modules"] if m["id"] == "novelty")
    assert module["status"] == "pending_integration"


def test_reset_mode_archives_compiled_file(tmp_path: Path) -> None:
    """Test 5: compiled file is moved to archive/ after --reset."""
    state = _minimal_state("novelty", "integrated")
    _scaffold(tmp_path, state)

    compiled_dir = tmp_path / "compiled"
    compiled_dir.mkdir()
    compiled_file = compiled_dir / "final_novelty.md"
    compiled_file.write_text("# Final\n", encoding="utf-8")

    _run_orchestrator(["--workspace", str(tmp_path), "--reset", "novelty"])

    assert not compiled_file.exists()
    archive = tmp_path / "archive"
    assert archive.is_dir()
    assert any(f.name.endswith("_final_novelty.md") for f in archive.iterdir())


def test_reset_mode_lockfile_cleaned_up(tmp_path: Path) -> None:
    """Test 5: lockfile is removed after a successful --reset."""
    state = _minimal_state("novelty", "integrated")
    _scaffold(tmp_path, state)

    _run_orchestrator(["--workspace", str(tmp_path), "--reset", "novelty"])

    assert not (tmp_path / LOCK_FILENAME).exists()


# ---------------------------------------------------------------------------
# Test 6 (MiniPRD) — skill failure → module set to failed, exit 1, lock cleaned
# ---------------------------------------------------------------------------


def test_skill_failure_sets_failed_status(tmp_path: Path) -> None:
    """Test 6: when execute_skill returns False, module status is set to failed."""
    from orchestrator import run_pipeline

    state = _minimal_state("novelty", "pending_extraction")
    _scaffold(tmp_path, state)

    with patch("orchestrator.execute_skill", return_value=False):
        with pytest.raises(SystemExit) as exc_info:
            run_pipeline(tmp_path, load_state(tmp_path))
        assert exc_info.value.code == 1

    loaded = load_state(tmp_path)
    module = next(m for m in loaded["modules"] if m["id"] == "novelty")
    assert module["status"] == "failed"


def test_skill_failure_lockfile_cleaned_up(tmp_path: Path) -> None:
    """Test 6: lockfile is removed even when a skill fails (via try/finally)."""
    state = _minimal_state("novelty", "pending_extraction", skip_adversarial=True)
    _scaffold(tmp_path, state)

    # Mock execute_skill to fail; the CLI orchestrator must still clean the lock.
    with patch("orchestrator.execute_skill", return_value=False):
        result = _run_orchestrator(["--workspace", str(tmp_path)])

    assert result.returncode == 1
    assert not (tmp_path / LOCK_FILENAME).exists()


# ---------------------------------------------------------------------------
# Auxiliary — acquire_lock / release_lock unit tests
# ---------------------------------------------------------------------------


def test_acquire_lock_creates_file(tmp_path: Path) -> None:
    """acquire_lock() creates the lockfile and returns its path."""
    lock_path = acquire_lock(tmp_path)
    assert lock_path.exists()
    release_lock(lock_path)


def test_acquire_lock_aborts_if_exists(tmp_path: Path) -> None:
    """acquire_lock() raises SystemExit(1) if lock already exists."""
    (tmp_path / LOCK_FILENAME).touch()
    with pytest.raises(SystemExit) as exc_info:
        acquire_lock(tmp_path)
    assert exc_info.value.code == 1


def test_release_lock_deletes_file(tmp_path: Path) -> None:
    """release_lock() removes the lockfile."""
    lock = acquire_lock(tmp_path)
    release_lock(lock)
    assert not lock.exists()


def test_release_lock_idempotent(tmp_path: Path) -> None:
    """release_lock() does not raise if lockfile already gone."""
    lock = tmp_path / LOCK_FILENAME
    release_lock(lock)  # must not raise


# ---------------------------------------------------------------------------
# Auxiliary — execute_skill unit tests
# ---------------------------------------------------------------------------


def test_execute_skill_returns_true_on_success() -> None:
    """execute_skill() returns True when command exits 0."""
    assert execute_skill([sys.executable, "-c", "import sys; sys.exit(0)"]) is True


def test_execute_skill_returns_false_on_failure() -> None:
    """execute_skill() returns False when command exits non-zero."""
    assert execute_skill([sys.executable, "-c", "import sys; sys.exit(1)"]) is False
