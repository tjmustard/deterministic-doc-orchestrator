"""Integration tests for integrate.py.

Covers the deterministic scenarios from MiniPRD_Integrate.md § 5.
All tests use tmp_path (pytest's isolated temp directory) and pass --repo-root
so they never touch the live repo state.

Test 1 (Novel) — Requires a live Claude CLI and API key.  It is skipped by
default; remove the skip marker and run manually to verify end-to-end behaviour.
"""

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

SCRIPT = Path(__file__).parents[2] / "integrate.py"

# Minimal template with two section headings and placeholders.
_TEMPLATE = """\
## Background

[Insert from transcript]

## Claims

[Insert from transcript]
"""

# Minimal draft content simulating post-extract output.
_DRAFT = """\
## Background

The document describes a self-healing polymer composite.

## Claims

[NEEDS_CLARIFICATION]
"""

# Minimal answers transcript.
_ANSWERS = """\
## Q&A Session

1. What are the primary claims?

**Answer:** The primary claim is a microencapsulated healing agent embedded in
a polymer matrix achieving sub-60-second room-temperature recovery.
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def run_integrate(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Run integrate.py as a subprocess."""
    return subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


def make_workspace(
    tmp_path: Path,
    job_name: str = "test_job",
    module_status: str = "pending_integration",
) -> Path:
    """Scaffold a minimal workspace with a test template and state_graph.yml.

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

    # Write a minimal test template into tmp_path (not inside the workspace).
    template_path = tmp_path / "templates" / "test_template.md"
    template_path.parent.mkdir(parents=True, exist_ok=True)
    template_path.write_text(_TEMPLATE, encoding="utf-8")

    state_graph = {
        "job_name": job_name,
        "global_status": "in_progress",
        "confidence_score": 8,
        "modules": [
            {
                "id": "novelty",
                "status": module_status,
                "associated_files": {
                    "template": str(template_path),
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

    # Write a pre-existing draft (simulate post-extract state).
    (workspace / "active" / "draft_novelty.md").write_text(_DRAFT, encoding="utf-8")

    return workspace


def base_args(workspace: Path, tmp_path: Path) -> list[str]:
    """Return args that point all output paths into tmp_path."""
    return [
        "--workspace", str(workspace),
        "--repo-root", str(tmp_path),
        "--mock-integration",
    ]


# ---------------------------------------------------------------------------
# Test 1 — Novel (live LLM): skipped in CI, run manually
# ---------------------------------------------------------------------------


@pytest.mark.skip(
    reason=(
        "Novel test — requires a live Claude CLI and API key. "
        "Run manually: python integrate.py novelty --workspace <path>"
    )
)
def test_novel_integration_creates_candidate_output(tmp_path: Path) -> None:
    """Test 1: Full integration with real Claude produces a candidate output."""
    workspace = make_workspace(tmp_path)
    (workspace / "transcripts" / "module_novelty_answers.md").write_text(
        _ANSWERS, encoding="utf-8"
    )

    # Note: no --mock-integration flag — calls real claude subprocess.
    result = run_integrate(
        ["novelty", "--workspace", str(workspace), "--repo-root", str(tmp_path)],
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stderr
    candidate = tmp_path / "tests" / "candidate_outputs" / "final_novelty.md"
    assert candidate.exists()
    content = candidate.read_text(encoding="utf-8")
    assert "## Background" in content or "## Claims" in content
    assert "promote" in result.stdout.lower()


# ---------------------------------------------------------------------------
# Test 2 — Deterministic: empty answers transcript aborts
# ---------------------------------------------------------------------------


def test_empty_answers_aborts(tmp_path: Path) -> None:
    """Test 2: An empty answers transcript causes a non-zero exit with error message."""
    workspace = make_workspace(tmp_path)
    # Write an empty answers transcript.
    (workspace / "transcripts" / "module_novelty_answers.md").write_text(
        "", encoding="utf-8"
    )

    result = run_integrate(["novelty"] + base_args(workspace, tmp_path), cwd=tmp_path)

    assert result.returncode != 0
    assert "no answers transcript" in result.stderr.lower()
    assert "interview" in result.stderr.lower()


def test_missing_answers_aborts(tmp_path: Path) -> None:
    """Test 2 variant: absent answers transcript is treated the same as empty."""
    workspace = make_workspace(tmp_path)
    # Do NOT write the answers transcript.

    result = run_integrate(["novelty"] + base_args(workspace, tmp_path), cwd=tmp_path)

    assert result.returncode != 0
    assert "no answers transcript" in result.stderr.lower()


# ---------------------------------------------------------------------------
# Test 3 — Deterministic: compiled/ is not written
# ---------------------------------------------------------------------------


def test_compiled_file_not_written(tmp_path: Path) -> None:
    """Test 3: compiled/final_novelty.md must NOT exist after /integrate.

    Output must go to candidate_outputs/ only.
    """
    workspace = make_workspace(tmp_path)
    (workspace / "transcripts" / "module_novelty_answers.md").write_text(
        _ANSWERS, encoding="utf-8"
    )

    result = run_integrate(["novelty"] + base_args(workspace, tmp_path), cwd=tmp_path)

    assert result.returncode == 0, result.stderr

    # candidate_outputs/ must exist with the integrated file.
    candidate = tmp_path / "tests" / "candidate_outputs" / "final_novelty.md"
    assert candidate.exists()

    # compiled/ must NOT have the final file.
    compiled = workspace / "compiled" / "final_novelty.md"
    assert not compiled.exists(), (
        f"integrate.py must NOT write to compiled/; found: {compiled}"
    )


# ---------------------------------------------------------------------------
# Test 4 — Deterministic: state_graph.yml status does not advance
# ---------------------------------------------------------------------------


def test_state_graph_status_unchanged(tmp_path: Path) -> None:
    """Test 4: state_graph.yml module status stays 'pending_integration' after /integrate.

    Status must only advance to 'integrated' when /promote APPROVEs the output.
    """
    workspace = make_workspace(tmp_path, module_status="pending_integration")
    (workspace / "transcripts" / "module_novelty_answers.md").write_text(
        _ANSWERS, encoding="utf-8"
    )

    result = run_integrate(["novelty"] + base_args(workspace, tmp_path), cwd=tmp_path)

    assert result.returncode == 0, result.stderr

    state = yaml.safe_load((workspace / "state_graph.yml").read_text(encoding="utf-8"))
    assert state["modules"][0]["status"] == "pending_integration", (
        "integrate.py must not advance module status — /promote is responsible."
    )


# ---------------------------------------------------------------------------
# Test 5 — Deterministic: /promote instruction printed
# ---------------------------------------------------------------------------


def test_promote_instruction_printed(tmp_path: Path) -> None:
    """Test 5: stdout contains the /promote instruction after successful integration."""
    workspace = make_workspace(tmp_path)
    (workspace / "transcripts" / "module_novelty_answers.md").write_text(
        _ANSWERS, encoding="utf-8"
    )

    result = run_integrate(["novelty"] + base_args(workspace, tmp_path), cwd=tmp_path)

    assert result.returncode == 0, result.stderr
    assert "promote" in result.stdout.lower()
    assert "novelty" in result.stdout


# ---------------------------------------------------------------------------
# Unit tests for pure helpers
# ---------------------------------------------------------------------------


def test_validate_answers_raises_on_empty(tmp_path: Path) -> None:
    from integrate import validate_answers

    (tmp_path / "transcripts").mkdir()
    (tmp_path / "transcripts" / "module_novelty_answers.md").write_text(
        "   \n   ", encoding="utf-8"
    )
    with pytest.raises(SystemExit) as exc_info:
        validate_answers(tmp_path, "novelty")
    assert exc_info.value.code == 1


def test_validate_answers_returns_content(tmp_path: Path) -> None:
    from integrate import validate_answers

    (tmp_path / "transcripts").mkdir()
    (tmp_path / "transcripts" / "module_novelty_answers.md").write_text(
        "Some answer content.", encoding="utf-8"
    )
    result = validate_answers(tmp_path, "novelty")
    assert result == "Some answer content."


def test_mock_integration_returns_prefixed_draft() -> None:
    from integrate import _mock_integration

    result = _mock_integration("template", "draft body", "answers")
    assert "MOCK INTEGRATED" in result
    assert "draft body" in result
