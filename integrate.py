#!/usr/bin/env python3
"""Integrate Skill — Synthesize baseline draft + Q&A answers into a final document.

Reads the workspace's active draft and adversarial Q&A answers transcript,
synthesizes them into a final, defensible document section using a Resolution
Agent prompt, and routes the output to tests/candidate_outputs/ for operator
review via /promote.

Usage:
    python integrate.py <module_id> --workspace <path>

Internal flags (used by integration tests):
    --mock-integration  Return a fixed deterministic integrated document instead
                        of calling the Claude CLI. Never use in production.
    --repo-root PATH    Override the repository root (for test path isolation).
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Callable

from state_graph_schema import get_module, load_state

SYSTEM_INSTRUCTION = (
    "You are a Resolution Agent. Your role is to synthesize a baseline document "
    "draft with adversarial Q&A answers into a final, precise, and defensible "
    "document section. Follow the template schema strictly. DO NOT hallucinate. "
    "DO NOT introduce claims not supported by either the draft or the answers transcript."
)


# ---------------------------------------------------------------------------
# Pure helpers (importable by tests)
# ---------------------------------------------------------------------------


def validate_answers(workspace_path: Path, module_id: str) -> str:
    """Read and return the answers transcript content, or abort if missing/empty.

    Args:
        workspace_path: Path to the workspace directory.
        module_id: Module ID used to resolve the answers transcript path.

    Returns:
        Non-empty answers transcript content string.

    Raises:
        SystemExit: With code 1 if the answers transcript is absent or empty.
    """
    answers_path = workspace_path / "transcripts" / f"module_{module_id}_answers.md"
    content = ""
    if answers_path.exists():
        content = answers_path.read_text(encoding="utf-8")
    if not content.strip():
        print(
            f"ERROR: No answers transcript found for module '{module_id}'. "
            "Run /interview first.",
            file=sys.stderr,
        )
        sys.exit(1)
    return content


# ---------------------------------------------------------------------------
# Integration functions
# ---------------------------------------------------------------------------


def _mock_integration(
    template_content: str,  # noqa: ARG001
    draft_content: str,
    answers_content: str,  # noqa: ARG001
) -> str:
    """Test stub: return the draft prefixed with a deterministic integration marker.

    Args:
        template_content: Unused in mock mode.
        draft_content: The original draft content.
        answers_content: Unused in mock mode.

    Returns:
        Draft content prefixed with a mock integration header.
    """
    return f"<!-- MOCK INTEGRATED -->\n{draft_content}"


def _call_claude(
    template_content: str,
    draft_content: str,
    answers_content: str,
) -> str:
    """Invoke the Claude CLI to synthesize the integrated document.

    Constructs the Resolution Agent prompt (system instruction + template schema
    + baseline draft + Q&A answers) and pipes it to `claude -p`.
    Exits with code 1 if the subprocess fails.

    Args:
        template_content: Original template structure (schema reference).
        draft_content: Baseline draft text to be updated.
        answers_content: Adversarial Q&A answers transcript.

    Returns:
        Integrated document string from Claude.

    Raises:
        SystemExit: With code 1 if the claude subprocess exits non-zero.
    """
    prompt = (
        f"{SYSTEM_INSTRUCTION}\n\n"
        f"TEMPLATE SCHEMA:\n{template_content}\n\n"
        f"BASELINE DRAFT:\n{draft_content}\n\n"
        f"ADVERSARIAL Q&A ANSWERS:\n{answers_content}\n\n"
        "Update each section of the baseline draft using the relevant Q&A answers. "
        "Strengthen claims, fill [NEEDS_CLARIFICATION] gaps where answers are available, "
        "and document any remaining gaps that still lack answers."
    )
    result = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        print(
            f"ERROR: Claude integration failed (exit {result.returncode}):\n{result.stderr}",
            file=sys.stderr,
        )
        sys.exit(1)
    return result.stdout.strip()


# ---------------------------------------------------------------------------
# Core pipeline
# ---------------------------------------------------------------------------


def run_integrate(
    module_id: str,
    workspace_path: Path,
    repo_root: Path,
    integration_fn: Callable[[str, str, str], str] = _call_claude,
) -> None:
    """Execute the full integrate pipeline for one module.

    Task 1 — Load state and resolve module, draft, answers, and template paths.
    Task 2 — Validate answers transcript (abort if empty).
    Task 3 — Read draft and template; invoke integration_fn with full context.
    Task 4 — Capture integrated content.
    Task 5 — Write output to tests/candidate_outputs/final_<module_id>.md only.
    Task 6 — Print instruction to run /promote.
    Task 7 — Do NOT update state_graph.yml (status advances only on /promote APPROVE).

    Args:
        module_id: ID of the module to integrate.
        workspace_path: Resolved path to the workspace directory.
        repo_root: Resolved repository root for candidate_outputs/ path.
        integration_fn: Callable(template_content, draft_content, answers_content)
                        -> integrated_content. Defaults to _call_claude; inject
                        _mock_integration in tests.

    Raises:
        SystemExit: With code 1 on any validation or integration failure.
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

    template_rel = module.get("associated_files", {}).get("template")
    if not template_rel:
        print(
            f"ERROR: Module '{module_id}' has no associated_files.template "
            "in state_graph.yml.",
            file=sys.stderr,
        )
        sys.exit(1)

    template_path = Path(template_rel)
    if not template_path.is_absolute():
        template_path = workspace_path / template_path
    if not template_path.exists():
        print(
            f"ERROR: Template file not found: '{template_path}'.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Task 2: Validate answers transcript.
    answers_content = validate_answers(workspace_path, module_id)

    # Task 3: Read draft and template; invoke integration.
    draft_content = draft_path.read_text(encoding="utf-8")
    template_content = template_path.read_text(encoding="utf-8")

    # Task 4: Capture integrated content.
    integrated_content = integration_fn(template_content, draft_content, answers_content)

    # Task 5: Write to candidate_outputs/ only — never to compiled/.
    candidate_path = repo_root / "tests" / "candidate_outputs" / f"final_{module_id}.md"
    candidate_path.parent.mkdir(parents=True, exist_ok=True)
    candidate_path.write_text(integrated_content, encoding="utf-8")

    # Task 6: Print /promote instruction.
    print(
        f"Integration complete. Review the output at "
        f"tests/candidate_outputs/final_{module_id}.md. "
        f"Run /promote {module_id} to approve and move to compiled/."
    )

    # Task 7: Do NOT update state_graph.yml — status advances only on /promote APPROVE.


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
            "Integrate skill — synthesize baseline draft + Q&A answers into a "
            "final candidate document routed to tests/candidate_outputs/."
        ),
    )
    parser.add_argument(
        "module_id",
        help="ID of the module to integrate (must exist in state_graph.yml).",
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
        "--mock-integration",
        action="store_true",
        help=argparse.SUPPRESS,  # Internal: replaces LLM call with deterministic stub.
    )
    return parser


def main() -> None:
    """Parse arguments and run the integrate pipeline."""
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

    integration_fn = _mock_integration if args.mock_integration else _call_claude

    run_integrate(
        module_id=args.module_id,
        workspace_path=workspace_path,
        repo_root=repo_root,
        integration_fn=integration_fn,
    )


if __name__ == "__main__":
    main()
