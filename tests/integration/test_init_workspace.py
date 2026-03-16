"""Integration tests for init_workspace.py.

Covers the 5 deterministic scenarios from MiniPRD_WorkspaceInit.md § 5.
All tests use tmp_path (pytest's isolated temp directory) and pass --repo-root
so they never touch the live repo state.
"""

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

# Path to the script under test — resolved relative to this file so tests
# work regardless of the working directory from which pytest is invoked.
SCRIPT = Path(__file__).parents[2] / "init_workspace.py"


def run_init(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Run init_workspace.py as a subprocess."""
    return subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


def base_args(tmp_path: Path) -> list[str]:
    """Return the common args that redirect all paths into tmp_path."""
    return ["--workspace-root", str(tmp_path), "--repo-root", str(tmp_path)]


# ---------------------------------------------------------------------------
# Test 1 — Clean initialization
# ---------------------------------------------------------------------------


def test_clean_init_creates_workspace(tmp_path: Path) -> None:
    """Test 1: Running init on a clean repo creates the full workspace structure."""
    result = run_init(["test_job"] + base_args(tmp_path), cwd=tmp_path)

    assert result.returncode == 0, result.stderr

    workspace = tmp_path / "test_job"
    assert workspace.is_dir()

    # All 5 required subdirectories must exist.
    for subdir in ("transcripts", "active", "compiled", "archive", "personas_snapshot"):
        assert (workspace / subdir).is_dir(), f"Missing subdir: {subdir}"

    # state_graph.yml must exist and be valid YAML.
    state_path = workspace / "state_graph.yml"
    assert state_path.exists()
    state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    assert state["global_status"] == "in_progress"
    assert state["confidence_score"] == 0

    # Workspace must be registered.
    registry_path = tmp_path / ".agents" / "workspace_registry.yml"
    assert registry_path.exists()
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    assert str(workspace.resolve()) in registry["workspaces"]


# ---------------------------------------------------------------------------
# Test 2 — Double-init is rejected
# ---------------------------------------------------------------------------


def test_double_init_is_rejected(tmp_path: Path) -> None:
    """Test 2: Running init twice on the same job name exits non-zero."""
    run_init(["test_job"] + base_args(tmp_path), cwd=tmp_path)

    result = run_init(["test_job"] + base_args(tmp_path), cwd=tmp_path)

    assert result.returncode != 0
    assert "already initialized" in result.stderr

    # Registry must not have duplicates — workspace count unchanged.
    registry_path = tmp_path / ".agents" / "workspace_registry.yml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    workspace_str = str((tmp_path / "test_job").resolve())
    assert registry["workspaces"].count(workspace_str) == 1


# ---------------------------------------------------------------------------
# Test 3 — --force overwrites cleanly
# ---------------------------------------------------------------------------


def test_force_overwrites_existing_workspace(tmp_path: Path) -> None:
    """Test 3: --force wipes and recreates an existing valid workspace."""
    # First init — create a sentinel file inside the workspace.
    run_init(["test_job"] + base_args(tmp_path), cwd=tmp_path)
    sentinel = tmp_path / "test_job" / "transcripts" / "sentinel.txt"
    sentinel.write_text("should be gone after --force", encoding="utf-8")

    # Second init with --force.
    result = run_init(
        ["test_job"] + base_args(tmp_path) + ["--force"],
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stderr
    workspace = tmp_path / "test_job"
    assert workspace.is_dir()
    assert (workspace / "state_graph.yml").exists()

    # Sentinel must be gone — directory was wiped.
    assert not sentinel.exists()


# ---------------------------------------------------------------------------
# Test 4 — Missing persona aborts before touching filesystem
# ---------------------------------------------------------------------------


def test_missing_persona_aborts(tmp_path: Path) -> None:
    """Test 4: A non-existent persona ID causes a non-zero exit; no workspace created."""
    result = run_init(
        ["test_job"] + base_args(tmp_path) + ["--personas", "nonexistent_persona"],
        cwd=tmp_path,
    )

    assert result.returncode != 0
    # Error output must name the missing file path.
    missing = str(tmp_path / ".agents" / "schemas" / "personas" / "nonexistent_persona.md")
    assert missing in result.stderr or missing in result.stdout

    # No workspace directory should have been created.
    assert not (tmp_path / "test_job").exists()


# ---------------------------------------------------------------------------
# Test 5 — validate_template raises ValueError on missing placeholder
# ---------------------------------------------------------------------------


def test_validate_template_raises_on_missing_placeholder(tmp_path: Path) -> None:
    """Test 5: validate_template() raises ValueError when placeholder is absent."""
    from init_workspace import validate_template

    bad_template = tmp_path / "bad_template.md"
    bad_template.write_text("## Section\n\nNo placeholder here.\n", encoding="utf-8")

    with pytest.raises(ValueError, match="placeholder"):
        validate_template(bad_template)
