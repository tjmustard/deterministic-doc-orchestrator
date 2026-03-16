#!/usr/bin/env python3
"""Promote Skill — Candidate Output Review.

Presents each pending candidate output for a module to the operator for
explicit APPROVE/REJECT review. APPROVE moves the file to tests/fixtures/
and logs the event in state_graph.yml. REJECT logs a reason, resets the
module to pending_integration, and halts further review.

Usage:
    python promote.py <module_id> --workspace <path>

Internal flags (used by integration tests):
    --repo-root PATH    Override the repository root (for test path isolation).
"""

import argparse
import datetime
import shutil
import sys
from pathlib import Path

from archive_manager import archive_draft
from state_graph_schema import get_module, load_state, save_state

# Ordered candidate output slot definitions: (filename_template, approval_flag)
_CANDIDATE_SLOTS = [
    ("draft_{module_id}.md", "draft_approved"),
    ("module_{module_id}_questions.md", "questions_approved"),
    ("final_{module_id}.md", "compiled_approved"),
]


# ---------------------------------------------------------------------------
# Pure helpers (importable by tests)
# ---------------------------------------------------------------------------


def resolve_pending_candidates(
    module_id: str,
    candidate_dir: Path,
) -> list[tuple[Path, str]]:
    """Return (path, approval_flag) pairs for candidate files that exist on disk.

    Files are returned in pipeline order: draft → questions → final.
    Slots whose files are not present are silently skipped.

    Args:
        module_id: Module ID used to build candidate filenames.
        candidate_dir: Directory containing candidate output files.

    Returns:
        List of (file_path, approval_flag) tuples for existing files.
    """
    results = []
    for filename_template, flag in _CANDIDATE_SLOTS:
        filename = filename_template.format(module_id=module_id)
        path = candidate_dir / filename
        if path.exists():
            results.append((path, flag))
    return results


def _ensure_candidate_outputs(module: dict) -> dict:
    """Ensure module has a candidate_outputs sub-dict; return it.

    Initialises the sub-dict with all flags False if absent.

    Args:
        module: Module dict from the parsed state graph (mutated in place).

    Returns:
        The candidate_outputs dict (guaranteed non-None).
    """
    if "candidate_outputs" not in module or module["candidate_outputs"] is None:
        module["candidate_outputs"] = {
            "draft_approved": False,
            "questions_approved": False,
            "compiled_approved": False,
        }
    return module["candidate_outputs"]


def _append_rejection(module: dict, filename: str, reason: str) -> None:
    """Append a rejection record to the module's rejections list.

    Mutates the module dict in place; caller must call save_state() afterwards.

    Args:
        module: Module dict (mutated in place).
        filename: Filename of the rejected candidate output.
        reason: Human-supplied rejection reason.
    """
    if "rejections" not in module or module["rejections"] is None:
        module["rejections"] = []
    module["rejections"].append(
        {
            "file": filename,
            "reason": reason,
            "timestamp": datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
        }
    )


# ---------------------------------------------------------------------------
# Core pipeline
# ---------------------------------------------------------------------------


def run_promote(
    module_id: str,
    workspace_path: Path,
    repo_root: Path,
    input_fn=input,
) -> None:
    """Execute the full promote review loop for one module.

    Task 1 — Load state_graph.yml and identify existing candidate output files.
    Task 2 — Present each file's contents and prompt APPROVE / REJECT <reason>.
    Task 3 — On APPROVE: move file to tests/fixtures/, update approval flag.
    Task 4 — On REJECT: log reason, reset module to pending_integration, halt.
    Task 5 — On all approved: set status to 'integrated', call archive_draft.

    Args:
        module_id: ID of the module to review.
        workspace_path: Resolved path to the workspace directory.
        repo_root: Resolved repository root (tests/ lives here).
        input_fn: Callable used to read operator input. Override in tests.

    Raises:
        SystemExit: With code 1 on validation failures.
    """
    # Task 1: Load state and validate module.
    state = load_state(workspace_path)
    try:
        module = get_module(state, module_id)
    except KeyError:
        print(
            f"ERROR: Module '{module_id}' not found in state_graph.yml.",
            file=sys.stderr,
        )
        sys.exit(1)

    candidate_dir = repo_root / "tests" / "candidate_outputs"
    fixtures_dir = repo_root / "tests" / "fixtures"

    pending = resolve_pending_candidates(module_id, candidate_dir)

    if not pending:
        print(
            f"No candidate outputs pending review for module '{module_id}'. "
            "Nothing to promote."
        )
        return

    fixtures_dir.mkdir(parents=True, exist_ok=True)
    _ensure_candidate_outputs(module)

    # Task 2 → 4: Review each candidate in order.
    for file_path, approval_flag in pending:
        filename = file_path.name
        contents = file_path.read_text(encoding="utf-8")

        print(f"\n{'=' * 72}")
        print(f"FILE: {filename}")
        print(f"{'=' * 72}")
        print(contents)
        print(f"{'=' * 72}")

        raw = input_fn(
            'Type APPROVE to accept this output, or REJECT <reason> to flag it for re-run.\n> '
        ).strip()

        if raw.upper() == "APPROVE":
            # Task 3: Move to fixtures/, update approval flag, persist state.
            dest = fixtures_dir / filename
            shutil.move(str(file_path), str(dest))
            module["candidate_outputs"][approval_flag] = True
            save_state(workspace_path, state)
            print(f"APPROVED: {filename} moved to tests/fixtures/.")

        elif raw.upper().startswith("REJECT"):
            # Task 4: Log rejection, reset status, halt.
            reason = raw[len("REJECT"):].strip()
            _append_rejection(module, filename, reason)
            module["status"] = "pending_integration"
            save_state(workspace_path, state)
            print(
                f"REJECTED: {filename}. Module reset to pending_integration. "
                "Reason logged. Fix the issue and re-run /integrate."
            )
            return  # Halt — do not review remaining candidates.

        else:
            print(
                f"ERROR: Unrecognised input '{raw}'. "
                "Expected 'APPROVE' or 'REJECT <reason>'.",
                file=sys.stderr,
            )
            sys.exit(1)

    # Task 5: All pending candidates approved — advance to integrated.
    module["status"] = "integrated"
    save_state(workspace_path, state)
    archive_draft(module_id, workspace_path)
    print(f"Module '{module_id}' fully approved and integrated.")


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
            "Promote skill — present candidate outputs for APPROVE/REJECT review, "
            "move approved files to tests/fixtures/, and advance module status."
        ),
    )
    parser.add_argument(
        "module_id",
        help="ID of the module to review (must exist in state_graph.yml).",
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
        help=argparse.SUPPRESS,  # Internal: redirects tests/ paths in integration tests.
    )
    return parser


def main() -> None:
    """Parse arguments and run the promote pipeline."""
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

    run_promote(
        module_id=args.module_id,
        workspace_path=workspace_path,
        repo_root=repo_root,
    )


if __name__ == "__main__":
    main()
