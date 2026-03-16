"""Integration tests for redteam.py.

Covers the deterministic scenarios from MiniPRD_RedTeam.md § 5.
All tests use tmp_path (pytest's isolated temp directory) and pass --repo-root
so they never touch the live repo state.

Test 1 (Novel) — Requires a live Claude CLI and API key. It is skipped by
default; remove the skip marker and run manually to verify end-to-end behaviour.
"""

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

SCRIPT = Path(__file__).parents[2] / "redteam.py"

_PERSONA_CONTENT = """\
You are a hostile document examiner. You look for every weakness.
"""

# Draft with a [NEEDS_CLARIFICATION] marker to satisfy Test 4.
_DRAFT_CONTENT = """\
## Background

The document describes a self-healing polymer. [NEEDS_CLARIFICATION]

## Claims

1. A polymer matrix with embedded healing agents.
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_workspace(
    tmp_path: Path,
    job_name: str = "test_job",
    existing_question_count: int = 0,
    max_questions: int | None = None,
) -> Path:
    """Scaffold a minimal workspace with a draft and state_graph.yml.

    Args:
        tmp_path: Pytest temporary directory root.
        job_name: Name of the workspace subdirectory.
        existing_question_count: Pre-populate the questionnaire with this many
            numbered questions so remaining_capacity can be tested.
        max_questions: Override the module's max_questions (defaults to 50).

    Returns:
        Path to the created workspace directory.
    """
    workspace = tmp_path / job_name
    for subdir in ("transcripts", "active", "compiled", "archive", "personas_snapshot"):
        (workspace / subdir).mkdir(parents=True)

    # Write draft.
    (workspace / "active" / "draft_novelty.md").write_text(_DRAFT_CONTENT, encoding="utf-8")

    # Write persona snapshot.
    (workspace / "personas_snapshot" / "document_examiner_adversary.md").write_text(
        _PERSONA_CONTENT, encoding="utf-8"
    )

    # Pre-populate questionnaire if needed.
    if existing_question_count > 0:
        lines = [f"{i}. Pre-existing question {i}?" for i in range(1, existing_question_count + 1)]
        q_path = workspace / "active" / "module_novelty_questions.md"
        q_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    module_entry: dict = {
        "id": "novelty",
        "status": "extracted",
        "associated_files": {
            "template": "active/template.md",
            "draft": "active/draft_novelty.md",
            "compiled": "compiled/final_novelty.md",
        },
    }
    if max_questions is not None:
        module_entry["max_questions"] = max_questions

    state_graph = {
        "job_name": job_name,
        "global_status": "in_progress",
        "confidence_score": 0,
        "modules": [module_entry],
    }
    (workspace / "state_graph.yml").write_text(
        yaml.dump(state_graph, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )
    return workspace


def run_redteam(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Run redteam.py as a subprocess."""
    return subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


def base_args(workspace: Path, tmp_path: Path, persona_id: str = "document_examiner_adversary") -> list[str]:
    """Return args that point all output paths into tmp_path."""
    return [
        "novelty",
        persona_id,
        "--workspace", str(workspace),
        "--repo-root", str(tmp_path),
        "--mock-redteam",
    ]


# ---------------------------------------------------------------------------
# Test 1 — Novel (live LLM): skipped in CI, run manually
# ---------------------------------------------------------------------------


@pytest.mark.skip(
    reason=(
        "Novel test — requires a live Claude CLI and API key. "
        "Run manually: python redteam.py novelty document_examiner_adversary --workspace <path>"
    )
)
def test_novel_redteam_appends_questions(tmp_path: Path) -> None:
    """Test 1: Full red-team with real Claude appends questions to questionnaire."""
    workspace = make_workspace(tmp_path)

    result = run_redteam(
        [
            "novelty",
            "document_examiner_adversary",
            "--workspace", str(workspace),
            "--repo-root", str(tmp_path),
        ],
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stderr

    q_path = workspace / "active" / "module_novelty_questions.md"
    assert q_path.exists()
    text = q_path.read_text(encoding="utf-8")
    assert "## Persona: document_examiner_adversary" in text

    candidate = tmp_path / "tests" / "candidate_outputs" / "module_novelty_questions.md"
    assert candidate.exists()

    state = yaml.safe_load((workspace / "state_graph.yml").read_text(encoding="utf-8"))
    assert state["modules"][0]["adversarial_state"]["status"] == "interview_in_progress"


# ---------------------------------------------------------------------------
# Test 2 — Deterministic: cap already reached
# ---------------------------------------------------------------------------


def test_cap_reached_skips_gracefully(tmp_path: Path) -> None:
    """Test 2: Questionnaire already has 50 questions → warning, exit 0, no append.

    Expected:
    - Prints cap-reached WARNING
    - Exits with code 0
    - Questionnaire file unchanged
    - state_graph.yml unchanged
    """
    workspace = make_workspace(tmp_path, existing_question_count=50)
    q_path = workspace / "active" / "module_novelty_questions.md"
    original_text = q_path.read_text(encoding="utf-8")

    result = run_redteam(base_args(workspace, tmp_path), cwd=tmp_path)

    assert result.returncode == 0, result.stderr
    assert "WARNING" in result.stdout
    assert "cap" in result.stdout.lower() or "reached" in result.stdout.lower()
    assert "document_examiner_adversary" in result.stdout

    # Questionnaire must be unchanged.
    assert q_path.read_text(encoding="utf-8") == original_text

    # state_graph.yml must be unchanged (adversarial_state not set).
    state = yaml.safe_load((workspace / "state_graph.yml").read_text(encoding="utf-8"))
    assert "adversarial_state" not in state["modules"][0]


# ---------------------------------------------------------------------------
# Test 3 — Deterministic: generated questions exceed remaining capacity
# ---------------------------------------------------------------------------


def test_truncation_when_over_capacity(tmp_path: Path) -> None:
    """Test 3: 47 existing questions, mock generates 5 → truncated to 3.

    Expected:
    - Prints truncation WARNING mentioning persona and counts
    - Exactly 3 questions added (not 5)
    - Total becomes 50
    - Remaining capacity = 0
    """
    workspace = make_workspace(tmp_path, existing_question_count=47)

    result = run_redteam(base_args(workspace, tmp_path), cwd=tmp_path)

    assert result.returncode == 0, result.stderr

    # Truncation warning must be present.
    assert "WARNING" in result.stdout
    assert "document_examiner_adversary" in result.stdout
    assert "Truncated to 3" in result.stdout

    # Confirmation line must show 3 questions added.
    assert "Questions added: 3" in result.stdout
    assert "Total questions: 50" in result.stdout
    assert "Remaining capacity: 0" in result.stdout

    # Questionnaire must contain exactly the 3 truncated questions under the header.
    q_path = workspace / "active" / "module_novelty_questions.md"
    q_text = q_path.read_text(encoding="utf-8")
    assert "## Persona: document_examiner_adversary" in q_text

    # Candidate output must match questionnaire.
    candidate = tmp_path / "tests" / "candidate_outputs" / "module_novelty_questions.md"
    assert candidate.exists()
    assert candidate.read_text(encoding="utf-8") == q_text

    # state_graph.yml adversarial_state updated.
    state = yaml.safe_load((workspace / "state_graph.yml").read_text(encoding="utf-8"))
    assert state["modules"][0]["adversarial_state"]["status"] == "interview_in_progress"


# ---------------------------------------------------------------------------
# Test 4 — Deterministic: [NEEDS_CLARIFICATION] in draft is interrogated
# ---------------------------------------------------------------------------


def test_needs_clarification_marker_targeted(tmp_path: Path) -> None:
    """Test 4: Draft contains [NEEDS_CLARIFICATION] → at least one question targets it.

    The mock stub includes a question that explicitly references
    [NEEDS_CLARIFICATION], confirming the marker flows through to the output.

    Expected:
    - Questionnaire contains at least one question mentioning NEEDS_CLARIFICATION
    - adversarial_state.status = interview_in_progress
    """
    workspace = make_workspace(tmp_path)

    result = run_redteam(base_args(workspace, tmp_path), cwd=tmp_path)

    assert result.returncode == 0, result.stderr

    q_path = workspace / "active" / "module_novelty_questions.md"
    q_text = q_path.read_text(encoding="utf-8")

    # At least one question must reference the clarification marker.
    assert "NEEDS_CLARIFICATION" in q_text

    state = yaml.safe_load((workspace / "state_graph.yml").read_text(encoding="utf-8"))
    assert state["modules"][0]["adversarial_state"]["status"] == "interview_in_progress"


# ---------------------------------------------------------------------------
# Unit tests for pure helpers
# ---------------------------------------------------------------------------


def test_count_existing_questions_zero() -> None:
    from redteam import count_existing_questions

    assert count_existing_questions("") == 0
    assert count_existing_questions("## Heading only\nNo numbered lines.") == 0


def test_count_existing_questions_counts_correctly() -> None:
    from redteam import count_existing_questions

    text = "1. First?\n2. Second?\n## Persona: B\n3. Third?\n"
    assert count_existing_questions(text) == 3


def test_parse_generated_questions_extracts_lines() -> None:
    from redteam import parse_generated_questions

    output = "Some preamble\n1. Question one?\n2. Question two?\nTrailing text."
    questions = parse_generated_questions(output)
    assert questions == ["1. Question one?", "2. Question two?"]


def test_parse_generated_questions_empty() -> None:
    from redteam import parse_generated_questions

    assert parse_generated_questions("") == []
    assert parse_generated_questions("No numbered lines here.") == []


def test_resolve_persona_path_prefers_snapshot(tmp_path: Path) -> None:
    from redteam import resolve_persona_path

    workspace = tmp_path / "ws"
    (workspace / "personas_snapshot").mkdir(parents=True)
    snapshot = workspace / "personas_snapshot" / "test_persona.md"
    snapshot.write_text("snapshot content", encoding="utf-8")

    # Also write a global copy; snapshot must win.
    global_dir = tmp_path / ".agents" / "schemas" / "personas"
    global_dir.mkdir(parents=True)
    (global_dir / "test_persona.md").write_text("global content", encoding="utf-8")

    result = resolve_persona_path(workspace, "test_persona", tmp_path)
    assert result == snapshot


def test_resolve_persona_path_falls_back_to_global(tmp_path: Path) -> None:
    from redteam import resolve_persona_path

    workspace = tmp_path / "ws"
    (workspace / "personas_snapshot").mkdir(parents=True)
    # No snapshot; only global.
    global_dir = tmp_path / ".agents" / "schemas" / "personas"
    global_dir.mkdir(parents=True)
    global_path = global_dir / "test_persona.md"
    global_path.write_text("global content", encoding="utf-8")

    result = resolve_persona_path(workspace, "test_persona", tmp_path)
    assert result == global_path


def test_resolve_persona_path_exits_if_missing(tmp_path: Path) -> None:
    from redteam import resolve_persona_path

    workspace = tmp_path / "ws"
    (workspace / "personas_snapshot").mkdir(parents=True)

    with pytest.raises(SystemExit) as exc_info:
        resolve_persona_path(workspace, "nonexistent_persona", tmp_path)
    assert exc_info.value.code == 1
