"""Integration tests for interview.py.

Covers the 5 deterministic scenarios from MiniPRD_Interview.md § 5.
All tests use tmp_path (pytest's isolated temp directory) so they never
touch the live repo state.

Operator input is simulated by piping a pre-built stdin string to the subprocess.
The interview flow:
  1. Initial gate prompt:  "Type DONE to pause, or press Enter to begin."
  2. For each question:    multi-line input, terminated by blank line.
  3. After every 3rd answer (when more remain):
     "3 questions answered. Type DONE to pause, or press Enter to continue."
"""

import subprocess
import sys
from pathlib import Path

import yaml

SCRIPT = Path(__file__).parents[2] / "interview.py"

# Nine numbered questions across two fictional persona sections.
_QUESTIONNAIRE = """\
## Persona: Skeptic

1. What evidence supports claim A?
2. How was experiment B validated?
3. What are the failure modes of approach C?

## Persona: Economist

4. What is the market size for product D?
5. Who are the primary competitors for offering E?
6. What is the estimated cost of production for F?

## Persona: Critic

7. Is claim G already documented?
8. Does feature H overlap with any existing implementations?
9. What context covers document I?
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_workspace(
    tmp_path: Path,
    last_answered_index: int = 0,
    job_name: str = "test_job",
) -> Path:
    """Scaffold a minimal workspace with a questionnaire and state_graph.yml.

    Args:
        tmp_path: Pytest temporary directory root.
        last_answered_index: Value to pre-set in adversarial_state.
        job_name: Name of the workspace subdirectory.

    Returns:
        Path to the created workspace directory.
    """
    workspace = tmp_path / job_name
    for subdir in ("transcripts", "active", "compiled", "archive", "personas_snapshot"):
        (workspace / subdir).mkdir(parents=True)

    # Write the questionnaire.
    q_path = workspace / "active" / "module_novelty_questions.md"
    q_path.write_text(_QUESTIONNAIRE, encoding="utf-8")

    state_graph = {
        "job_name": job_name,
        "global_status": "in_progress",
        "confidence_score": 0,
        "modules": [
            {
                "id": "novelty",
                "status": "pending_interview",
                "associated_files": {
                    "template": "active/template.md",
                    "draft": "active/draft_novelty.md",
                    "compiled": "compiled/final_novelty.md",
                },
                "adversarial_state": {
                    "status": "interview_in_progress",
                    "last_answered_index": last_answered_index,
                    "master_questionnaire": "active/module_novelty_questions.md",
                    "answers_transcript": "transcripts/module_novelty_answers.md",
                },
            }
        ],
    }
    (workspace / "state_graph.yml").write_text(
        yaml.dump(state_graph, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )
    return workspace


def run_interview(args: list[str], stdin: str, cwd: Path) -> subprocess.CompletedProcess:
    """Run interview.py as a subprocess with piped stdin."""
    return subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        input=stdin,
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


def load_state(workspace: Path) -> dict:
    """Load state_graph.yml from workspace."""
    return yaml.safe_load((workspace / "state_graph.yml").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Test 1 — Answer 3 questions, type DONE
# ---------------------------------------------------------------------------


def test_answer_three_then_done(tmp_path: Path) -> None:
    """Test 1: 9 questions, answer 3, type DONE.

    Expected:
    - last_answered_index = 3 in state_graph.yml
    - 3 answers in transcripts/module_novelty_answers.md
    - module status unchanged (still pending_interview)
    """
    workspace = make_workspace(tmp_path, last_answered_index=0)

    # Stdin: press Enter at gate, 3 answers (blank-line terminated), DONE at batch prompt.
    stdin = "\n".join([
        "",           # gate: press Enter to begin
        "Answer 1",   # Q1 line 1
        "",           # Q1 blank-line submit
        "Answer 2",   # Q2
        "",
        "Answer 3",   # Q3
        "",
        "DONE",       # batch prompt after Q3
        "",
    ])

    result = run_interview(["novelty", "--workspace", str(workspace)], stdin, tmp_path)

    assert result.returncode == 0, result.stderr

    state = load_state(workspace)
    module = state["modules"][0]
    assert module["adversarial_state"]["last_answered_index"] == 3
    assert module["status"] == "pending_interview"  # unchanged

    answers_path = workspace / "transcripts" / "module_novelty_answers.md"
    assert answers_path.exists()
    text = answers_path.read_text(encoding="utf-8")
    assert text.count("## Q") == 3
    assert "Answer 1" in text
    assert "Answer 2" in text
    assert "Answer 3" in text


# ---------------------------------------------------------------------------
# Test 2 — Resume: skip already-answered questions
# ---------------------------------------------------------------------------


def test_resume_skips_answered_questions(tmp_path: Path) -> None:
    """Test 2: last_answered_index = 3, must present Q4,5,6 — not Q1,2,3.

    Expected:
    - Output contains 'Question 4 of 9' (not 'Question 1 of 9')
    - last_answered_index = 6 after DONE
    """
    workspace = make_workspace(tmp_path, last_answered_index=3)

    stdin = "\n".join([
        "",           # gate
        "Answer 4",
        "",
        "Answer 5",
        "",
        "Answer 6",
        "",
        "DONE",       # batch prompt after Q6
        "",
    ])

    result = run_interview(["novelty", "--workspace", str(workspace)], stdin, tmp_path)

    assert result.returncode == 0, result.stderr

    # Must NOT present Q1-3.
    assert "Question 1 of 9" not in result.stdout
    assert "Question 4 of 9" in result.stdout

    state = load_state(workspace)
    assert state["modules"][0]["adversarial_state"]["last_answered_index"] == 6


# ---------------------------------------------------------------------------
# Test 3 — Already fully answered: no Q&A, exit 0
# ---------------------------------------------------------------------------


def test_fully_answered_exits_cleanly(tmp_path: Path) -> None:
    """Test 3: last_answered_index = 9 with 9 total questions.

    Expected:
    - Prints 'All questions have been answered' message
    - Exits with code 0
    - Module status unchanged
    """
    workspace = make_workspace(tmp_path, last_answered_index=9)

    result = run_interview(["novelty", "--workspace", str(workspace)], "", tmp_path)

    assert result.returncode == 0, result.stderr
    assert "all questions have been answered" in result.stdout.lower()

    state = load_state(workspace)
    assert state["modules"][0]["status"] == "pending_interview"  # unchanged


# ---------------------------------------------------------------------------
# Test 4 — Complete all 9 questions without DONE
# ---------------------------------------------------------------------------


def test_complete_all_questions_advances_status(tmp_path: Path) -> None:
    """Test 4: Answer all 9 questions in one sitting.

    Expected:
    - last_answered_index = 9
    - module status = pending_integration
    - adversarial_state.status = ready_for_integration
    - All 9 answers in answers file
    """
    workspace = make_workspace(tmp_path, last_answered_index=0)

    # Gate → 9 answers → press Enter at batch-3 → press Enter at batch-6 → done
    lines = [""]  # gate
    for i in range(1, 10):
        lines.append(f"Answer {i}")
        lines.append("")  # blank-line submit
        if i in (3, 6):
            lines.append("")  # batch prompt: press Enter to continue

    stdin = "\n".join(lines)

    result = run_interview(["novelty", "--workspace", str(workspace)], stdin, tmp_path)

    assert result.returncode == 0, result.stderr
    assert "interview complete" in result.stdout.lower()

    state = load_state(workspace)
    module = state["modules"][0]
    assert module["adversarial_state"]["last_answered_index"] == 9
    assert module["status"] == "pending_integration"
    assert module["adversarial_state"]["status"] == "ready_for_integration"

    answers_path = workspace / "transcripts" / "module_novelty_answers.md"
    assert answers_path.exists()
    text = answers_path.read_text(encoding="utf-8")
    assert text.count("## Q") == 9


# ---------------------------------------------------------------------------
# Test 5 — DONE immediately: no answers, no status change
# ---------------------------------------------------------------------------


def test_done_immediately_no_changes(tmp_path: Path) -> None:
    """Test 5: Operator types DONE at the initial gate prompt.

    Expected:
    - last_answered_index unchanged (0)
    - Module status unchanged (pending_interview)
    - Answers file absent or unchanged
    """
    workspace = make_workspace(tmp_path, last_answered_index=0)

    result = run_interview(["novelty", "--workspace", str(workspace)], "DONE\n", tmp_path)

    assert result.returncode == 0, result.stderr

    state = load_state(workspace)
    module = state["modules"][0]
    assert module["adversarial_state"]["last_answered_index"] == 0
    assert module["status"] == "pending_interview"  # unchanged

    answers_path = workspace / "transcripts" / "module_novelty_answers.md"
    # Either the file doesn't exist or it's empty.
    if answers_path.exists():
        assert answers_path.read_text(encoding="utf-8").strip() == ""


# ---------------------------------------------------------------------------
# Unit tests for pure helpers
# ---------------------------------------------------------------------------


def test_parse_questionnaire_extracts_numbered_lines() -> None:
    from interview import parse_questionnaire

    text = """\
## Persona: A
1. First question?
2. Second question?

## Persona: B
3. Third question?
"""
    questions = parse_questionnaire(text)
    assert questions == ["First question?", "Second question?", "Third question?"]


def test_parse_questionnaire_empty_text() -> None:
    from interview import parse_questionnaire

    assert parse_questionnaire("") == []
    assert parse_questionnaire("## Heading only\nNo numbered lines.") == []


def test_append_answer_creates_file(tmp_path: Path) -> None:
    from interview import append_answer

    answers_path = tmp_path / "transcripts" / "module_novelty_answers.md"
    append_answer(answers_path, 1, "What is X?", "It is Y.")

    text = answers_path.read_text(encoding="utf-8")
    assert "## Q1: What is X?" in text
    assert "It is Y." in text


def test_append_answer_is_cumulative(tmp_path: Path) -> None:
    from interview import append_answer

    answers_path = tmp_path / "transcripts" / "module_novelty_answers.md"
    append_answer(answers_path, 1, "Q1?", "A1")
    append_answer(answers_path, 2, "Q2?", "A2")

    text = answers_path.read_text(encoding="utf-8")
    assert text.count("## Q") == 2
