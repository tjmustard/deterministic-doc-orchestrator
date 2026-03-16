#!/usr/bin/env python3
"""Interview Skill — Resumable paced Q&A over a module's adversarial questionnaire.

Presents unanswered questions in batches of 3. Saves progress to state_graph.yml
after each answer. Operator types DONE to pause; re-running resumes from the next
unanswered question.

Usage:
    python interview.py <module_id> --workspace <path>
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Callable

from state_graph_schema import get_module, load_state, save_state, set_module_status


# ---------------------------------------------------------------------------
# Pure helpers (importable by tests)
# ---------------------------------------------------------------------------


def parse_questionnaire(text: str) -> list[str]:
    """Extract numbered questions from questionnaire markdown text.

    Questions are lines matching ``^\\d+\\.`` across all persona sections.
    The numeric prefix is stripped; only the question text is returned.

    Args:
        text: Full questionnaire file content.

    Returns:
        Ordered list of question strings.
    """
    questions = []
    for line in text.splitlines():
        match = re.match(r"^\d+\.\s+(.*)", line.strip())
        if match:
            questions.append(match.group(1).strip())
    return questions


def read_multiline_input(input_fn: Callable[[], str]) -> str:
    """Read multi-line operator input terminated by a blank line.

    Args:
        input_fn: Callable that reads one line (injectable for tests).

    Returns:
        Collected answer string (lines joined by newline, no trailing blank).
    """
    lines = []
    while True:
        try:
            line = input_fn()
        except EOFError:
            break
        if line == "":
            break
        lines.append(line)
    return "\n".join(lines)


def append_answer(
    answers_path: Path,
    global_index: int,
    question_text: str,
    answer: str,
) -> None:
    """Append one Q&A pair to the answers transcript.

    Args:
        answers_path: Path to the answers markdown file.
        global_index: 1-based question number for display.
        question_text: The full question text.
        answer: The operator's answer.
    """
    answers_path.parent.mkdir(parents=True, exist_ok=True)
    with answers_path.open("a", encoding="utf-8") as f:
        f.write(f"## Q{global_index}: {question_text}\n{answer}\n\n")


# ---------------------------------------------------------------------------
# Core pipeline
# ---------------------------------------------------------------------------


def run_interview(
    module_id: str,
    workspace_path: Path,
    input_fn: Callable[[], str] = input,
) -> None:
    """Execute the full interview pipeline for one module.

    Task 1 — Load state and read last_answered_index (default 0).
    Task 2 — Parse questionnaire into ordered question list.
    Task 3 — Resume check: exit cleanly if all questions already answered.
    Task 4 — Present questions in batches of 3; save state atomically after each.
    Task 5 — On natural completion, advance status to pending_integration.
    Task 6 — Validate answers file grew before advancing status.

    Args:
        module_id: ID of the module to interview.
        workspace_path: Resolved path to the workspace directory.
        input_fn: Callable for reading one input line. Defaults to built-in input.

    Raises:
        SystemExit: With code 1 on validation failure; code 0 on normal exit.
    """
    # Task 1: Load state, resolve module, read last_answered_index.
    state = load_state(workspace_path)
    try:
        module = get_module(state, module_id)
    except KeyError:
        print(
            f"ERROR: Module '{module_id}' not found in state_graph.yml.",
            file=sys.stderr,
        )
        sys.exit(1)

    adv = module.setdefault("adversarial_state", {})
    last_answered_index = int(adv.get("last_answered_index", 0))

    # Task 2: Parse questionnaire.
    questionnaire_path = workspace_path / "active" / f"module_{module_id}_questions.md"
    if not questionnaire_path.exists() or not questionnaire_path.read_text(encoding="utf-8").strip():
        print(
            f"ERROR: No questionnaire found for module '{module_id}'. Run /redteam first.",
            file=sys.stderr,
        )
        sys.exit(1)

    questions = parse_questionnaire(questionnaire_path.read_text(encoding="utf-8"))
    total = len(questions)
    if total == 0:
        print(
            f"ERROR: No numbered questions found in questionnaire for module '{module_id}'.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Task 3: Handle fully-answered case.
    if last_answered_index >= total:
        print(
            f"All questions have been answered. "
            f"Run /integrate {module_id} to synthesize the final document."
        )
        sys.exit(0)

    # Pre-session DONE gate: let operator pause before any questions are presented.
    unanswered_count = total - last_answered_index
    print(
        f"Starting interview for '{module_id}'. "
        f"{unanswered_count} question(s) remaining (of {total})."
    )
    print("Type DONE to pause, or press Enter to begin.")
    try:
        gate = input_fn().strip().upper()
    except EOFError:
        gate = ""
    if gate == "DONE":
        print(
            f"Session saved. Re-run /interview {module_id} "
            f"--workspace {workspace_path} "
            f"to continue from question {last_answered_index + 1}."
        )
        sys.exit(0)

    # Task 4: Paced Q&A loop.
    answers_path = workspace_path / "transcripts" / f"module_{module_id}_answers.md"
    answers_size_before = answers_path.stat().st_size if answers_path.exists() else 0

    batch_count = 0  # answers given in this session (resets only on DONE)
    for question_text in questions[last_answered_index:]:
        global_index = last_answered_index + 1  # 1-based display
        print(f"\nQuestion {global_index} of {total}: {question_text}")
        print("Your answer (blank line to submit):")
        answer = read_multiline_input(input_fn)

        append_answer(answers_path, global_index, question_text, answer)
        last_answered_index += 1
        adv["last_answered_index"] = last_answered_index
        save_state(workspace_path, state)

        batch_count += 1

        # After every 3rd answer, offer to pause — but not after the very last question.
        if batch_count % 3 == 0 and last_answered_index < total:
            print("3 questions answered. Type DONE to pause, or press Enter to continue.")
            try:
                decision = input_fn().strip().upper()
            except EOFError:
                decision = "DONE"
            if decision == "DONE":
                print(
                    f"Session saved. Re-run /interview {module_id} "
                    f"--workspace {workspace_path} "
                    f"to continue from question {last_answered_index + 1}."
                )
                sys.exit(0)

    # Tasks 5 & 6: All questions exhausted naturally.
    # Validate that answers file grew before advancing status.
    answers_size_after = answers_path.stat().st_size if answers_path.exists() else 0
    if answers_size_after <= answers_size_before:
        # No new answers were written; do not advance status.
        sys.exit(0)

    set_module_status(state, module_id, "pending_integration")
    adv["status"] = "ready_for_integration"
    save_state(workspace_path, state)

    print(
        f"Interview complete. All {total} questions answered. "
        "Run orchestrator to proceed to integration."
    )
    sys.exit(0)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Resumable paced Q&A over a module's adversarial questionnaire. "
            "Presents unanswered questions in batches of 3."
        ),
    )
    parser.add_argument(
        "module_id",
        help="ID of the module to interview (must exist in state_graph.yml).",
    )
    parser.add_argument(
        "--workspace",
        required=True,
        metavar="PATH",
        help="Path to the workspace directory.",
    )
    return parser


def main() -> None:
    """Parse arguments and run the interview pipeline."""
    parser = build_parser()
    args = parser.parse_args()

    workspace_path = Path(args.workspace).resolve()
    if not workspace_path.is_dir():
        print(
            f"ERROR: Workspace directory not found: '{workspace_path}'",
            file=sys.stderr,
        )
        sys.exit(1)

    run_interview(
        module_id=args.module_id,
        workspace_path=workspace_path,
    )


if __name__ == "__main__":
    main()
