"""Integration tests for promote.py.

Covers the deterministic scenarios from MiniPRD_Promote.md § 5.
All tests use tmp_path (pytest's isolated temp directory) and pass --repo-root
so they never touch the live repo state.

Tests use the run_promote() function directly with an injected input_fn
to simulate operator input deterministically without a subprocess.
"""

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parents[2]))

from promote import run_promote  # noqa: E402

# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------

_DRAFT_CONTENT = "## Background\n\nThe invention relates to a self-healing polymer.\n"
_QUESTIONS_CONTENT = "## Questions\n\n1. What is the primary claim?\n"
_FINAL_CONTENT = "## Background\n\nFully resolved claim with healing agent.\n"


def make_workspace(
    tmp_path: Path,
    job_name: str = "test_job",
    module_status: str = "pending_integration",
) -> Path:
    """Scaffold a minimal workspace with state_graph.yml.

    Args:
        tmp_path: Pytest temporary directory root.
        job_name: Name of the workspace subdirectory.
        module_status: Initial module status in state_graph.yml.

    Returns:
        Path to the created workspace directory.
    """
    workspace = tmp_path / job_name
    for subdir in ("transcripts", "active", "compiled", "archive", "personas_snapshot"):
        (workspace / subdir).mkdir(parents=True)

    state_graph = {
        "job_name": job_name,
        "global_status": "in_progress",
        "confidence_score": 8,
        "modules": [
            {
                "id": "novelty",
                "status": module_status,
                "associated_files": {
                    "template": "templates/test_template.md",
                    "draft": "active/draft_novelty.md",
                    "compiled": "compiled/final_novelty.md",
                },
            }
        ],
    }
    (workspace / "state_graph.yml").write_text(
        yaml.dump(state_graph, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )
    return workspace


def seed_candidate_outputs(repo_root: Path, module_id: str, files: list[str]) -> None:
    """Write named candidate output files into tests/candidate_outputs/.

    Args:
        repo_root: Repository root (parent of tests/).
        module_id: Module ID used to populate file contents.
        files: List of filenames to create (e.g., ["draft_novelty.md"]).
    """
    cand_dir = repo_root / "tests" / "candidate_outputs"
    cand_dir.mkdir(parents=True, exist_ok=True)
    content_map = {
        f"draft_{module_id}.md": _DRAFT_CONTENT,
        f"module_{module_id}_questions.md": _QUESTIONS_CONTENT,
        f"final_{module_id}.md": _FINAL_CONTENT,
    }
    for filename in files:
        (cand_dir / filename).write_text(content_map[filename], encoding="utf-8")


# ---------------------------------------------------------------------------
# Test 1: Full APPROVE — all three files approved and integrated
# ---------------------------------------------------------------------------


def test_full_approve_moves_files_and_integrates(tmp_path: Path) -> None:
    """Test 1: APPROVE all three candidates.

    Expected:
    - All three files moved to tests/fixtures/.
    - All three approval flags True in state_graph.yml.
    - Module status == 'integrated'.
    - archive_draft called (active/draft_novelty.md absent or never present).
    - tests/candidate_outputs/ no longer contains those files.
    """
    workspace = make_workspace(tmp_path)
    repo_root = tmp_path

    all_files = [
        "draft_novelty.md",
        "module_novelty_questions.md",
        "final_novelty.md",
    ]
    seed_candidate_outputs(repo_root, "novelty", all_files)

    # Simulate operator typing APPROVE three times.
    responses = iter(["APPROVE", "APPROVE", "APPROVE"])
    run_promote("novelty", workspace, repo_root, input_fn=lambda _: next(responses))

    # All three files must be in fixtures/.
    fixtures_dir = repo_root / "tests" / "fixtures"
    for filename in all_files:
        assert (fixtures_dir / filename).exists(), f"Expected {filename} in fixtures/"

    # candidate_outputs/ must no longer contain those files.
    cand_dir = repo_root / "tests" / "candidate_outputs"
    for filename in all_files:
        assert not (cand_dir / filename).exists(), (
            f"{filename} should be removed from candidate_outputs/ after APPROVE"
        )

    # state_graph.yml must reflect fully approved state.
    state = yaml.safe_load((workspace / "state_graph.yml").read_text(encoding="utf-8"))
    module = state["modules"][0]
    assert module["status"] == "integrated"
    assert module["candidate_outputs"]["draft_approved"] is True
    assert module["candidate_outputs"]["questions_approved"] is True
    assert module["candidate_outputs"]["compiled_approved"] is True


# ---------------------------------------------------------------------------
# Test 2: APPROVE draft and questions, then REJECT final
# ---------------------------------------------------------------------------


def test_approve_then_reject_halts_and_resets(tmp_path: Path) -> None:
    """Test 2: Approve draft and questions, reject final.

    Expected:
    - draft and questions files in fixtures/.
    - final NOT moved to fixtures/.
    - rejections list contains the reason.
    - Module status == 'pending_integration'.
    """
    workspace = make_workspace(tmp_path)
    repo_root = tmp_path

    all_files = [
        "draft_novelty.md",
        "module_novelty_questions.md",
        "final_novelty.md",
    ]
    seed_candidate_outputs(repo_root, "novelty", all_files)

    rejection_reason = "The integration missed the edge case about X"
    responses = iter([
        "APPROVE",
        "APPROVE",
        f"REJECT {rejection_reason}",
    ])
    run_promote("novelty", workspace, repo_root, input_fn=lambda _: next(responses))

    fixtures_dir = repo_root / "tests" / "fixtures"
    cand_dir = repo_root / "tests" / "candidate_outputs"

    # draft and questions approved and moved.
    assert (fixtures_dir / "draft_novelty.md").exists()
    assert (fixtures_dir / "module_novelty_questions.md").exists()

    # final NOT moved.
    assert not (fixtures_dir / "final_novelty.md").exists()
    assert (cand_dir / "final_novelty.md").exists()

    state = yaml.safe_load((workspace / "state_graph.yml").read_text(encoding="utf-8"))
    module = state["modules"][0]
    assert module["status"] == "pending_integration"

    # Rejection reason must be logged.
    rejections = module.get("rejections", [])
    assert len(rejections) == 1
    assert rejections[0]["reason"] == rejection_reason
    assert rejections[0]["file"] == "final_novelty.md"
    assert "timestamp" in rejections[0]


# ---------------------------------------------------------------------------
# Test 3: No candidate output files — exits cleanly
# ---------------------------------------------------------------------------


def test_no_candidates_exits_cleanly(tmp_path: Path, capsys) -> None:
    """Test 3: No candidate files present.

    Expected: prints informative message; exits cleanly (no SystemExit).
    """
    workspace = make_workspace(tmp_path)
    repo_root = tmp_path

    # Do NOT seed any candidate outputs.
    (repo_root / "tests" / "candidate_outputs").mkdir(parents=True, exist_ok=True)

    # Should not raise or prompt the operator.
    run_promote("novelty", workspace, repo_root, input_fn=lambda _: "APPROVE")

    captured = capsys.readouterr()
    assert "no candidate" in captured.out.lower() or "nothing to promote" in captured.out.lower()

    # State must be unchanged.
    state = yaml.safe_load((workspace / "state_graph.yml").read_text(encoding="utf-8"))
    assert state["modules"][0]["status"] == "pending_integration"


# ---------------------------------------------------------------------------
# Test 4: fixtures/ isolation — only adds files, never deletes
# ---------------------------------------------------------------------------


def test_fixtures_dir_only_receives_new_files(tmp_path: Path) -> None:
    """Test 4: Approved files appear in fixtures/; candidate_outputs/ cleared of them.

    Verifies that fixtures/ accumulates (never deletes) and candidate_outputs/
    loses the moved files.
    """
    workspace = make_workspace(tmp_path)
    repo_root = tmp_path

    # Seed a pre-existing fixture to confirm it is not disturbed.
    fixtures_dir = repo_root / "tests" / "fixtures"
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    pre_existing = fixtures_dir / "existing_fixture.md"
    pre_existing.write_text("pre-existing content", encoding="utf-8")

    seed_candidate_outputs(repo_root, "novelty", ["draft_novelty.md"])

    responses = iter(["APPROVE"])
    run_promote("novelty", workspace, repo_root, input_fn=lambda _: next(responses))

    # New file added.
    assert (fixtures_dir / "draft_novelty.md").exists()
    # Pre-existing file untouched.
    assert pre_existing.exists()
    assert pre_existing.read_text(encoding="utf-8") == "pre-existing content"

    # candidate_outputs/ no longer has the approved file.
    assert not (repo_root / "tests" / "candidate_outputs" / "draft_novelty.md").exists()


# ---------------------------------------------------------------------------
# Unit tests for pure helpers
# ---------------------------------------------------------------------------


def test_resolve_pending_candidates_returns_existing_only(tmp_path: Path) -> None:
    """Only files that exist on disk are returned."""
    from promote import resolve_pending_candidates

    cand_dir = tmp_path / "candidate_outputs"
    cand_dir.mkdir()
    (cand_dir / "draft_foo.md").write_text("x", encoding="utf-8")
    # questions and final are absent.

    result = resolve_pending_candidates("foo", cand_dir)
    assert len(result) == 1
    assert result[0][0].name == "draft_foo.md"
    assert result[0][1] == "draft_approved"


def test_resolve_pending_candidates_pipeline_order(tmp_path: Path) -> None:
    """Files are returned in draft → questions → final order."""
    from promote import resolve_pending_candidates

    cand_dir = tmp_path / "candidate_outputs"
    cand_dir.mkdir()
    for filename in ["final_bar.md", "draft_bar.md", "module_bar_questions.md"]:
        (cand_dir / filename).write_text("x", encoding="utf-8")

    result = resolve_pending_candidates("bar", cand_dir)
    assert [r[0].name for r in result] == [
        "draft_bar.md",
        "module_bar_questions.md",
        "final_bar.md",
    ]


def test_ensure_candidate_outputs_initialises_when_absent() -> None:
    """_ensure_candidate_outputs creates the sub-dict if not present."""
    from promote import _ensure_candidate_outputs

    module = {"id": "foo", "status": "pending_integration"}
    out = _ensure_candidate_outputs(module)
    assert out["draft_approved"] is False
    assert out["questions_approved"] is False
    assert out["compiled_approved"] is False


def test_append_rejection_creates_list_when_absent() -> None:
    """_append_rejection initialises rejections list if not present."""
    from promote import _append_rejection

    module = {"id": "foo"}
    _append_rejection(module, "final_foo.md", "Missing edge case")
    assert len(module["rejections"]) == 1
    assert module["rejections"][0]["file"] == "final_foo.md"
    assert module["rejections"][0]["reason"] == "Missing edge case"
