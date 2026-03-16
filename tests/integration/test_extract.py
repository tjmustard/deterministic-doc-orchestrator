"""Integration tests for extract.py.

Covers the deterministic scenarios from MiniPRD_Extract.md § 5.
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

SCRIPT = Path(__file__).parents[2] / "extract.py"

# Minimal template with two [Insert from transcript] placeholders.
_TEMPLATE = """\
## Background

[Insert from transcript]

## Claims

[Insert from transcript]
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def run_extract(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Run extract.py as a subprocess."""
    return subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


def make_workspace(tmp_path: Path, job_name: str = "test_job") -> Path:
    """Scaffold a minimal workspace with a test template and state_graph.yml.

    Args:
        tmp_path: Pytest temporary directory root.
        job_name: Name of the workspace subdirectory.

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
        "confidence_score": 0,
        "modules": [
            {
                "id": "novelty",
                "status": "pending_extraction",
                "associated_files": {
                    "template": str(template_path),
                    "draft": f"active/draft_novelty.md",
                    "compiled": f"compiled/final_novelty.md",
                },
            }
        ],
    }
    (workspace / "state_graph.yml").write_text(
        yaml.dump(state_graph, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )
    return workspace


def base_args(workspace: Path, tmp_path: Path) -> list[str]:
    """Return args that point all output paths into tmp_path."""
    return [
        "--workspace", str(workspace),
        "--repo-root", str(tmp_path),
        "--mock-extraction",
    ]


# ---------------------------------------------------------------------------
# Test 1 — Novel (live LLM): skipped in CI, run manually
# ---------------------------------------------------------------------------


@pytest.mark.skip(
    reason=(
        "Novel test — requires a live Claude CLI and API key. "
        "Run manually: python extract.py novelty --workspace <path>"
    )
)
def test_novel_extraction_creates_populated_draft(tmp_path: Path) -> None:
    """Test 1: Full extraction with real Claude produces a populated draft."""
    workspace = make_workspace(tmp_path)
    (workspace / "transcripts" / "raw_input.md").write_text(
        "The invention relates to a self-healing polymer composite material "
        "that recovers its original shape after deformation. "
        "Key claims: (1) polymer matrix with embedded microencapsulated healing agents, "
        "(2) recovery time under 60 seconds at room temperature.",
        encoding="utf-8",
    )

    # Note: no --mock-extraction flag — calls real claude subprocess.
    result = run_extract(
        ["novelty", "--workspace", str(workspace), "--repo-root", str(tmp_path)],
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stderr
    draft = workspace / "active" / "draft_novelty.md"
    assert draft.exists()
    assert "## Background" in draft.read_text(encoding="utf-8")
    candidate = tmp_path / "tests" / "candidate_outputs" / "draft_novelty.md"
    assert candidate.exists()
    state = yaml.safe_load((workspace / "state_graph.yml").read_text(encoding="utf-8"))
    assert state["modules"][0]["status"] == "extracted"


# ---------------------------------------------------------------------------
# Test 2 — Deterministic: empty transcript aborts
# ---------------------------------------------------------------------------


def test_empty_transcript_aborts(tmp_path: Path) -> None:
    """Test 2: An empty transcripts/raw_input.md causes a non-zero exit.

    state_graph.yml must remain unchanged (status stays 'pending_extraction').
    """
    workspace = make_workspace(tmp_path)
    # Write an empty transcript.
    (workspace / "transcripts" / "raw_input.md").write_text("", encoding="utf-8")

    result = run_extract(["novelty"] + base_args(workspace, tmp_path), cwd=tmp_path)

    assert result.returncode != 0
    assert "empty" in result.stderr.lower()

    # state_graph.yml must be unchanged.
    state = yaml.safe_load((workspace / "state_graph.yml").read_text(encoding="utf-8"))
    assert state["modules"][0]["status"] == "pending_extraction"

    # No draft file should have been created.
    assert not (workspace / "active" / "draft_novelty.md").exists()


def test_missing_transcript_aborts(tmp_path: Path) -> None:
    """Test 2 variant: absent raw_input.md is treated the same as empty."""
    workspace = make_workspace(tmp_path)
    # Do NOT write raw_input.md.

    result = run_extract(["novelty"] + base_args(workspace, tmp_path), cwd=tmp_path)

    assert result.returncode != 0
    assert "empty" in result.stderr.lower()

    state = yaml.safe_load((workspace / "state_graph.yml").read_text(encoding="utf-8"))
    assert state["modules"][0]["status"] == "pending_extraction"


# ---------------------------------------------------------------------------
# Test 3 — Deterministic: partial transcript warns about gaps
# ---------------------------------------------------------------------------


def test_partial_transcript_warns_and_advances(tmp_path: Path) -> None:
    """Test 3: Mock extraction (all gaps) prints a WARNING and advances status.

    With --mock-extraction every [Insert from transcript] becomes
    [NEEDS_CLARIFICATION], simulating a transcript that covers none of the
    template sections.  The pipeline must:
      - exit 0
      - print a WARNING with the gap count
      - write draft_novelty.md containing [NEEDS_CLARIFICATION]
      - copy to tests/candidate_outputs/
      - advance state_graph.yml status to 'extracted'
    """
    workspace = make_workspace(tmp_path)
    (workspace / "transcripts" / "raw_input.md").write_text(
        "Only partial information about the invention background is available.",
        encoding="utf-8",
    )

    result = run_extract(["novelty"] + base_args(workspace, tmp_path), cwd=tmp_path)

    assert result.returncode == 0, result.stderr

    # WARNING must be printed (to stdout).
    assert "WARNING" in result.stdout
    assert "clarification" in result.stdout.lower()

    # Draft file must exist and contain [NEEDS_CLARIFICATION].
    draft = workspace / "active" / "draft_novelty.md"
    assert draft.exists()
    draft_text = draft.read_text(encoding="utf-8")
    assert "[NEEDS_CLARIFICATION]" in draft_text

    # Gap count in WARNING matches actual occurrences in draft.
    import re
    match = re.search(r"WARNING: (\d+) section", result.stdout)
    assert match, "WARNING line not found in stdout"
    reported_count = int(match.group(1))
    assert reported_count == draft_text.count("[NEEDS_CLARIFICATION]")
    assert reported_count > 0

    # Candidate output must be present.
    candidate = tmp_path / "tests" / "candidate_outputs" / "draft_novelty.md"
    assert candidate.exists()
    assert candidate.read_text(encoding="utf-8") == draft_text

    # State must have advanced.
    state = yaml.safe_load((workspace / "state_graph.yml").read_text(encoding="utf-8"))
    assert state["modules"][0]["status"] == "extracted"

    # Confirmation lines must appear in stdout.
    assert "Status advanced to: extracted" in result.stdout
    assert "Clarification gaps:" in result.stdout


# ---------------------------------------------------------------------------
# Unit tests for pure helpers
# ---------------------------------------------------------------------------


def test_count_gaps_zero() -> None:
    from extract import count_gaps
    assert count_gaps("No gaps here.") == 0


def test_count_gaps_multiple() -> None:
    from extract import count_gaps
    text = "[NEEDS_CLARIFICATION] and [NEEDS_CLARIFICATION]"
    assert count_gaps(text) == 2


def test_validate_transcript_raises_on_empty(tmp_path: Path) -> None:
    from extract import validate_transcript
    (tmp_path / "transcripts").mkdir()
    (tmp_path / "transcripts" / "raw_input.md").write_text("   \n   ", encoding="utf-8")
    with pytest.raises(SystemExit) as exc_info:
        validate_transcript(tmp_path)
    assert exc_info.value.code == 1


def test_validate_transcript_returns_content(tmp_path: Path) -> None:
    from extract import validate_transcript
    (tmp_path / "transcripts").mkdir()
    (tmp_path / "transcripts" / "raw_input.md").write_text("some content", encoding="utf-8")
    result = validate_transcript(tmp_path)
    assert result == "some content"
