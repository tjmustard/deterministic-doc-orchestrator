#!/usr/bin/env python3
"""RedTeam Skill — Multi-persona adversarial questionnaire generator.

Loads a persona and has it interrogate a module draft, appending adversarial
questions to the master questionnaire. Total question count across all personas
is capped at 50 (or the module's configured max_questions). Routes the
questionnaire to tests/candidate_outputs/ and atomically advances
adversarial_state.status to 'interview_in_progress'.

Usage:
    python redteam.py <module_id> <persona_id> --workspace <path>

Internal flags (used by integration tests):
    --mock-redteam      Return a fixed set of deterministic questions instead
                        of calling the Claude CLI. Never use in production.
    --repo-root PATH    Override the repository root (for test path isolation).
"""

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable

from state_graph_schema import get_module, load_state, save_state

DEFAULT_MAX_QUESTIONS = 50
_PERSONAS_REL = Path(".agents") / "schemas" / "personas"


# ---------------------------------------------------------------------------
# Pure helpers (importable by tests)
# ---------------------------------------------------------------------------


def count_existing_questions(questionnaire_text: str) -> int:
    """Count numbered questions (lines matching ^\\d+\\.) in questionnaire text.

    Args:
        questionnaire_text: Full text of the questionnaire file.

    Returns:
        Integer count of numbered question lines.
    """
    return sum(
        1
        for line in questionnaire_text.splitlines()
        if re.match(r"^\d+\.", line.strip())
    )


def parse_generated_questions(llm_output: str) -> list[str]:
    """Extract numbered question lines from LLM output.

    Args:
        llm_output: Raw text output from the LLM.

    Returns:
        Ordered list of raw question lines (including their numeric prefix).
    """
    return [
        line.strip()
        for line in llm_output.splitlines()
        if re.match(r"^\d+\.", line.strip())
    ]


def resolve_persona_path(workspace_path: Path, persona_id: str, repo_root: Path) -> Path:
    """Resolve the persona file path, preferring the workspace snapshot.

    Looks first in <workspace>/personas_snapshot/<persona_id>.md, then falls
    back to the global persona library at
    <repo_root>/.agents/schemas/personas/<persona_id>.md.

    Args:
        workspace_path: Path to the workspace directory.
        persona_id: ID of the persona to load.
        repo_root: Repository root for fallback to global persona library.

    Returns:
        Path to the persona file.

    Raises:
        SystemExit: With code 1 if neither snapshot nor global path exists.
    """
    snapshot_path = workspace_path / "personas_snapshot" / f"{persona_id}.md"
    if snapshot_path.exists():
        return snapshot_path

    global_path = repo_root / _PERSONAS_REL / f"{persona_id}.md"
    if global_path.exists():
        return global_path

    print(
        f"ERROR: Persona '{persona_id}' not found.\n"
        f"  Snapshot checked: {snapshot_path}\n"
        f"  Global path checked: {global_path}",
        file=sys.stderr,
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# LLM generation functions
# ---------------------------------------------------------------------------


def _mock_generation(
    persona_content: str,  # noqa: ARG001
    draft_content: str,  # noqa: ARG001
    remaining_capacity: int,  # noqa: ARG001
) -> str:
    """Test stub: return a fixed set of 5 deterministic numbered questions.

    Always returns all 5 questions regardless of remaining_capacity — the
    caller (run_redteam) is responsible for truncation. This lets Test 3
    exercise the truncation path by setting remaining_capacity < 5.

    Args:
        persona_content: Unused in mock mode.
        draft_content: Unused in mock mode.
        remaining_capacity: Unused in mock mode.

    Returns:
        Numbered question list string (always 5 lines).
    """
    mock_questions = [
        "1. What is the primary technical claim and has it been independently verified?",
        "2. What evidence supports the novelty assertion?",
        "3. Are there any [NEEDS_CLARIFICATION] sections that undermine the core claim?",
        "4. What prior art searches were conducted and what were the results?",
        "5. What is the commercial viability of the described document?",
    ]
    return "\n".join(mock_questions)


def _call_claude(
    persona_content: str,
    draft_content: str,
    remaining_capacity: int,
) -> str:
    """Invoke the Claude CLI to generate adversarial questions.

    Constructs a red-team prompt using the persona as the framing instruction,
    the full draft as context, and pipes it to `claude -p`.

    Args:
        persona_content: Full persona file text (system instruction framing).
        draft_content: Full module draft text.
        remaining_capacity: Maximum number of questions to generate.

    Returns:
        Raw LLM output string.

    Raises:
        SystemExit: With code 1 if the claude subprocess exits non-zero.
    """
    prompt = (
        f"{persona_content}\n\n"
        f"DRAFT DOCUMENT:\n{draft_content}\n\n"
        f"Generate adversarial questions targeting every claim, assumption, and "
        f"[NEEDS_CLARIFICATION] marker in the draft. Output strictly a numbered "
        f"Markdown list. Maximum {remaining_capacity} questions. "
        f"DO NOT output conversational filler."
    )
    result = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        print(
            f"ERROR: Claude red-team generation failed (exit {result.returncode}):\n"
            f"{result.stderr}",
            file=sys.stderr,
        )
        sys.exit(1)
    return result.stdout.strip()


# ---------------------------------------------------------------------------
# Core pipeline
# ---------------------------------------------------------------------------


def run_redteam(
    module_id: str,
    persona_id: str,
    workspace_path: Path,
    repo_root: Path,
    generation_fn: Callable[[str, str, int], str] = _call_claude,
) -> None:
    """Execute the full red-team pipeline for one module/persona pair.

    Task 1  — Load state, resolve draft and persona paths.
    Task 2  — Count existing questions; calculate remaining capacity.
    Task 3  — Skip gracefully if cap is reached.
    Tasks 4+5 — Construct prompt and invoke LLM.
    Task 6  — Count generated questions; truncate if needed.
    Task 7  — Append persona header + questions to questionnaire.
    Task 8  — Copy questionnaire to tests/candidate_outputs/.
    Task 9  — Update adversarial_state.status in state_graph.yml atomically.
    Task 10 — Print confirmation.

    Args:
        module_id: ID of the module to red-team.
        persona_id: ID of the persona to use.
        workspace_path: Resolved path to the workspace directory.
        repo_root: Resolved repository root.
        generation_fn: Callable(persona_content, draft_content, remaining_capacity)
                       -> raw_output. Defaults to _call_claude; inject
                       _mock_generation in tests.

    Raises:
        SystemExit: With code 1 on validation failure; code 0 on cap-reached skip.
    """
    # Task 1: Load state and resolve paths.
    state = load_state(workspace_path)
    try:
        module = get_module(state, module_id)
    except KeyError:
        print(
            f"ERROR: Module '{module_id}' not found in state_graph.yml.",
            file=sys.stderr,
        )
        sys.exit(1)

    draft_path = workspace_path / "active" / f"draft_{module_id}.md"
    if not draft_path.exists():
        print(
            f"ERROR: Draft not found at '{draft_path}'. Run /extract first.",
            file=sys.stderr,
        )
        sys.exit(1)
    draft_content = draft_path.read_text(encoding="utf-8")

    persona_path = resolve_persona_path(workspace_path, persona_id, repo_root)
    persona_content = persona_path.read_text(encoding="utf-8")

    max_questions = int(module.get("max_questions", DEFAULT_MAX_QUESTIONS))

    # Task 2: Count existing questions and calculate remaining capacity.
    questionnaire_path = workspace_path / "active" / f"module_{module_id}_questions.md"
    existing_text = ""
    if questionnaire_path.exists():
        existing_text = questionnaire_path.read_text(encoding="utf-8")
    current_count = count_existing_questions(existing_text)
    remaining_capacity = max_questions - current_count

    # Task 3: Skip gracefully if cap is reached.
    if remaining_capacity <= 0:
        print(
            f"WARNING: Question cap of {max_questions} reached. "
            f"Skipping persona '{persona_id}'."
        )
        sys.exit(0)

    # Tasks 4 & 5: Generate questions via LLM.
    raw_output = generation_fn(persona_content, draft_content, remaining_capacity)

    # Task 6: Count generated questions; truncate if needed.
    generated = parse_generated_questions(raw_output)
    count = len(generated)
    if count > remaining_capacity:
        print(
            f"WARNING: Persona '{persona_id}' generated {count} questions. "
            f"Truncated to {remaining_capacity} to stay within cap."
        )
        generated = generated[:remaining_capacity]
        count = remaining_capacity

    # Task 7: Append persona header + questions to questionnaire.
    questionnaire_path.parent.mkdir(parents=True, exist_ok=True)
    question_block = "\n".join(generated)
    with questionnaire_path.open("a", encoding="utf-8") as f:
        f.write(f"\n## Persona: {persona_id}\n{question_block}\n")

    # Task 8: Copy questionnaire to tests/candidate_outputs/.
    candidate_path = (
        repo_root / "tests" / "candidate_outputs" / f"module_{module_id}_questions.md"
    )
    candidate_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(questionnaire_path, candidate_path)

    # Task 9: Update adversarial_state.status atomically.
    adv = module.setdefault("adversarial_state", {})
    adv["status"] = "interview_in_progress"
    save_state(workspace_path, state)

    # Task 10: Print confirmation.
    new_total = current_count + count
    remaining_after = max_questions - new_total
    print(f"Persona: {persona_id}")
    print(f"Questions added: {count}")
    print(f"Total questions: {new_total}")
    print(f"Remaining capacity: {remaining_after}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Adversarial red-team skill — loads a persona and appends questions "
            "to the module's master questionnaire."
        ),
    )
    parser.add_argument(
        "module_id",
        help="ID of the module to red-team (must exist in state_graph.yml).",
    )
    parser.add_argument(
        "persona_id",
        help="ID of the adversarial persona to use.",
    )
    parser.add_argument(
        "--workspace",
        required=True,
        metavar="PATH",
        help="Path to the workspace directory.",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        metavar="PATH",
        help=argparse.SUPPRESS,  # Internal: redirects schema and output paths in tests.
    )
    parser.add_argument(
        "--mock-redteam",
        action="store_true",
        help=argparse.SUPPRESS,  # Internal: replaces LLM call with deterministic stub.
    )
    return parser


def main() -> None:
    """Parse arguments and run the red-team pipeline."""
    parser = build_parser()
    args = parser.parse_args()

    workspace_path = Path(args.workspace).resolve()
    if not workspace_path.is_dir():
        print(
            f"ERROR: Workspace directory not found: '{workspace_path}'",
            file=sys.stderr,
        )
        sys.exit(1)

    repo_root = (
        Path(args.repo_root).resolve()
        if args.repo_root
        else Path(__file__).parent.resolve()
    )

    generation_fn = _mock_generation if args.mock_redteam else _call_claude

    run_redteam(
        module_id=args.module_id,
        persona_id=args.persona_id,
        workspace_path=workspace_path,
        repo_root=repo_root,
        generation_fn=generation_fn,
    )


if __name__ == "__main__":
    main()
