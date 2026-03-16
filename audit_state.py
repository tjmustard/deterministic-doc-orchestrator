#!/usr/bin/env python3
"""Audit State Script — Reconcile state_graph.yml against the filesystem.

Detects and corrects drifted module statuses caused by crashes or manual file
moves. Reports all changes and alerts without touching any file except
state_graph.yml.

Usage:
    python audit_state.py --workspace <path>
"""

import argparse
import sys
from pathlib import Path

from state_graph_schema import load_state, save_state, set_module_status

LOCK_FILENAME = ".orchestrator.lock"

# Module statuses that imply a draft file should exist on disk.
DRAFT_REQUIRED_STATUSES = {"extracted", "pending_interview", "pending_integration"}


# ---------------------------------------------------------------------------
# Reconciliation
# ---------------------------------------------------------------------------


def _draft_path(workspace_path: Path, module: dict) -> Path:
    """Resolve the active draft path for a module.

    Uses associated_files.draft if set; falls back to the canonical naming
    convention active/draft_<module_id>.md.

    Args:
        workspace_path: Path to the workspace directory.
        module: Module dict from state_graph.

    Returns:
        Absolute Path to the draft file.
    """
    af = module.get("associated_files", {}).get("draft")
    if af:
        p = Path(af)
        return p if p.is_absolute() else workspace_path / p
    return workspace_path / "active" / f"draft_{module['id']}.md"


def _compiled_path(workspace_path: Path, module: dict) -> Path:
    """Resolve the compiled output path for a module.

    Uses associated_files.compiled if set; falls back to the canonical naming
    convention compiled/final_<module_id>.md.

    Args:
        workspace_path: Path to the workspace directory.
        module: Module dict from state_graph.

    Returns:
        Absolute Path to the compiled file.
    """
    af = module.get("associated_files", {}).get("compiled")
    if af:
        p = Path(af)
        return p if p.is_absolute() else workspace_path / p
    return workspace_path / "compiled" / f"final_{module['id']}.md"


def reconcile(workspace_path: Path, state: dict) -> tuple[dict, list[str], list[str]]:
    """Apply all reconciliation rules to each module in priority order.

    Rules (applied in sequence per module):
      Rule 1 — compiled exists: compiled file present but status != integrated
               → force status to integrated.
      Rule 2 — draft missing: status requires draft but draft file absent
               → revert status to pending_extraction.
      Rule 3 — failed: module in failed state → AUDIT ALERT only, no change.
      Rule 4 — stale lock: .orchestrator.lock exists → AUDIT ALERT only, no change.

    Args:
        workspace_path: Path to the workspace directory.
        state: Loaded state graph dict (mutated in place for status changes).

    Returns:
        Tuple of (updated_state, changes_log, alerts_log) where:
          - changes_log: list of "{module_id}: {old} → {new}" strings.
          - alerts_log: list of AUDIT ALERT message strings.
    """
    changes: list[str] = []
    alerts: list[str] = []

    for module in state.get("modules", []):
        module_id = module["id"]
        status = module.get("status", "")

        compiled = _compiled_path(workspace_path, module)
        draft = _draft_path(workspace_path, module)

        # Rule 1: Compiled file exists but status is not integrated.
        if compiled.exists() and status != "integrated":
            msg = (
                f"AUDIT FIX: {module_id} — compiled file exists, forced to 'integrated'."
            )
            print(msg)
            changes.append(f"{module_id}: {status} → integrated")
            set_module_status(state, module_id, "integrated")
            # Update local variable so Rule 2 sees the new status.
            status = "integrated"

        # Rule 2: Draft missing but status implies draft should exist.
        if status in DRAFT_REQUIRED_STATUSES and not draft.exists():
            msg = (
                f"AUDIT FIX: {module_id} — draft file missing, "
                "reverted to 'pending_extraction'."
            )
            print(msg)
            changes.append(f"{module_id}: {status} → pending_extraction")
            set_module_status(state, module_id, "pending_extraction")

        # Rule 3: Module is in failed state — alert only, no change.
        if status == "failed":
            alert = (
                f"AUDIT ALERT: {module_id} — module is in 'failed' state. "
                "Manual intervention required."
            )
            print(alert)
            alerts.append(alert)

    # Rule 4: Stale lockfile — alert only, never delete.
    lock_path = workspace_path / LOCK_FILENAME
    if lock_path.exists():
        alert = (
            f"AUDIT ALERT: Stale lockfile found at {lock_path}. "
            "If no orchestrator is running, delete it manually."
        )
        print(alert)
        alerts.append(alert)

    return state, changes, alerts


# ---------------------------------------------------------------------------
# Diff summary
# ---------------------------------------------------------------------------


def print_summary(changes: list[str], alerts: list[str]) -> None:
    """Print the final audit report to stdout.

    Args:
        changes: Status-change strings (module_id: old → new).
        alerts: AUDIT ALERT strings already printed during reconciliation.
    """
    print()
    print("─" * 60)
    print("AUDIT SUMMARY")
    print("─" * 60)

    if not changes and not alerts:
        print("Audit complete. State graph is consistent with filesystem.")
        return

    if changes:
        print("Status changes applied:")
        for entry in changes:
            print(f"  {entry}")

    if alerts:
        print("Alerts (no automatic action taken):")
        for alert in alerts:
            print(f"  {alert}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Reconcile state_graph.yml against the actual workspace filesystem. "
            "Safe to run after any crash or manual file operation."
        ),
    )
    parser.add_argument(
        "--workspace",
        required=True,
        metavar="PATH",
        help="Path to the workspace directory.",
    )
    return parser


def main() -> None:
    """Parse arguments and run the audit."""
    parser = build_parser()
    args = parser.parse_args()

    workspace_path = Path(args.workspace).resolve()
    if not workspace_path.is_dir():
        print(
            f"ERROR: Workspace directory not found: '{workspace_path}'",
            file=sys.stderr,
        )
        sys.exit(1)

    # Task 1: Load state.
    state = load_state(workspace_path)

    # Task 2: Snapshot pre-audit statuses for the diff report.
    # (Captured inside reconcile via the changes list.)

    # Tasks 3 & 4: Apply reconciliation rules; collect changes and alerts.
    state, changes, alerts = reconcile(workspace_path, state)

    # Task 4: Atomically save if any statuses were corrected.
    if changes:
        save_state(workspace_path, state)

    # Task 5: Print the diff summary.
    print_summary(changes, alerts)


if __name__ == "__main__":
    main()
