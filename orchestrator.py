#!/usr/bin/env python3
"""Deterministic Document Orchestrator — YAML-driven state machine.

Reads state_graph.yml and advances each module through its lifecycle by
invoking the correct Claude Code skill as a subprocess. All routing is
purely deterministic based on module.status — no LLM is consulted for
graph traversal.

Usage:
    python orchestrator.py --workspace <path>
    python orchestrator.py --workspace <path> --reset <module_id>
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from archive_manager import archive_compiled, archive_draft
from state_graph_schema import (
    VALID_STATUSES,
    get_module,
    load_state,
    save_state,
    set_module_status,
)

LOCK_FILENAME = ".orchestrator.lock"

# Subdirectories to scan for symlinks during pre-flight.
SYMLINK_SCAN_DIRS = ["active", "transcripts", "compiled"]


# ---------------------------------------------------------------------------
# Lockfile management
# ---------------------------------------------------------------------------


def acquire_lock(workspace_path: Path) -> Path:
    """Create the orchestrator lockfile or abort if it already exists.

    Args:
        workspace_path: Path to the workspace directory.

    Returns:
        Path to the created lockfile.

    Raises:
        SystemExit: If a lockfile already exists.
    """
    lock_path = workspace_path / LOCK_FILENAME
    if lock_path.exists():
        print(
            "ERROR: Orchestrator is already running for this workspace. "
            "If this is incorrect, delete .orchestrator.lock and retry.",
            file=sys.stderr,
        )
        sys.exit(1)
    lock_path.touch()
    return lock_path


def release_lock(lock_path: Path) -> None:
    """Delete the lockfile if it exists."""
    if lock_path.exists():
        lock_path.unlink()


# ---------------------------------------------------------------------------
# Pre-flight validation
# ---------------------------------------------------------------------------


def preflight(workspace_path: Path, state: dict) -> None:
    """Run all pre-flight checks before starting the pipeline.

    Checks:
      (a) Validates state YAML is loadable (already done before this call).
      (b) Warns if confidence_score < 7 and requires CONFIRM to proceed.
      (c) Verifies all associated_file paths in the state exist.
      (d) Scans active/, transcripts/, compiled/ for symlinks.

    Args:
        workspace_path: Path to the workspace directory.
        state: Loaded state graph dict.

    Raises:
        SystemExit: On any validation failure.
    """
    # (b) Confidence score check.
    confidence = state.get("document_meta", {}).get("confidence_score", 0)
    if confidence < 7:
        print(
            f"WARNING: confidence_score is {confidence} (< 7). "
            "The pipeline may produce low-quality output."
        )
        response = input("Type CONFIRM to proceed anyway: ").strip()
        if response != "CONFIRM":
            print("Aborted by operator.")
            sys.exit(0)

    # (c) Verify all associated files referenced in state exist.
    missing_files: list[str] = []

    for persona in state.get("personas", []):
        af = persona.get("associated_file")
        if af and not Path(af).exists():
            missing_files.append(af)

    for inp in state.get("inputs", []):
        af = inp.get("associated_file")
        if af:
            candidate = workspace_path / af if not Path(af).is_absolute() else Path(af)
            if not candidate.exists():
                missing_files.append(str(candidate))

    for module in state.get("modules", []):
        afs = module.get("associated_files", {})
        for key in ("template", "draft", "compiled"):
            af = afs.get(key)
            if af:
                candidate = (
                    workspace_path / af if not Path(af).is_absolute() else Path(af)
                )
                # draft and compiled are expected to not yet exist at this stage.
                if key == "template" and not candidate.exists():
                    missing_files.append(str(candidate))

    if missing_files:
        print("ERROR: Pre-flight failed — missing required file(s):", file=sys.stderr)
        for f in missing_files:
            print(f"  {f}", file=sys.stderr)
        sys.exit(1)

    # (d) Symlink check.
    symlinks_found: list[str] = []
    for subdir_name in SYMLINK_SCAN_DIRS:
        subdir = workspace_path / subdir_name
        if not subdir.exists():
            continue
        for item in subdir.iterdir():
            if item.is_symlink():
                symlinks_found.append(str(item))

    if symlinks_found:
        print("ERROR: Pre-flight failed — symlink(s) detected:", file=sys.stderr)
        for s in symlinks_found:
            print(f"  {s}", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Persona snapshot
# ---------------------------------------------------------------------------


def snapshot_personas(workspace_path: Path, state: dict, repo_root: Path) -> None:
    """Copy all referenced persona files into <workspace>/personas_snapshot/.

    This freezes the global persona library so live mutations have no effect
    on the running job.

    Args:
        workspace_path: Path to the workspace directory.
        state: Loaded state graph dict.
        repo_root: Absolute path to the repository root.
    """
    snapshot_dir = workspace_path / "personas_snapshot"
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    for persona in state.get("personas", []):
        af = persona.get("associated_file")
        if not af:
            continue
        src = Path(af) if Path(af).is_absolute() else repo_root / af
        if src.exists():
            dest = snapshot_dir / src.name
            shutil.copy2(str(src), str(dest))


# ---------------------------------------------------------------------------
# Skill execution
# ---------------------------------------------------------------------------


def execute_skill(command_list: list[str]) -> bool:
    """Run a skill subprocess and return True on success.

    Uses subprocess.run(check=True). On CalledProcessError, prints stderr
    and returns False. Never retries.

    Args:
        command_list: Command and arguments to execute.

    Returns:
        True if the subprocess exited with code 0, False otherwise.
    """
    try:
        subprocess.run(command_list, check=True)
        return True
    except subprocess.CalledProcessError as exc:
        if exc.stderr:
            print(exc.stderr, file=sys.stderr)
        print(
            f"ERROR: Skill command {command_list} exited with code {exc.returncode}.",
            file=sys.stderr,
        )
        return False


def _skill_cmd(skill_name: str, workspace_path: Path, *args: str) -> list[str]:
    """Build the subprocess command for a Claude Code slash command.

    Always passes --workspace so skills can locate the persona snapshot
    at <workspace>/personas_snapshot/ rather than the global library.

    Args:
        skill_name: The slash command name (e.g. "extract").
        workspace_path: Absolute path to the workspace directory.
        *args: Additional positional arguments passed to the skill.

    Returns:
        Command list for subprocess.run().
    """
    return ["claude", f"/{skill_name}", *args, "--workspace", str(workspace_path)]


# ---------------------------------------------------------------------------
# Reset mode
# ---------------------------------------------------------------------------


def run_reset(workspace_path: Path, module_id: str) -> None:
    """Archive the compiled output and revert a module to pending_integration.

    Args:
        workspace_path: Path to the workspace directory.
        module_id: ID of the module to reset.

    Raises:
        SystemExit: If the module is not found in state.
    """
    state = load_state(workspace_path)

    try:
        get_module(state, module_id)
    except KeyError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    archive_compiled(module_id, workspace_path)

    set_module_status(state, module_id, "pending_integration")
    save_state(workspace_path, state)

    print(
        f"Module '{module_id}' reset to pending_integration. "
        "Re-run the orchestrator to continue."
    )


# ---------------------------------------------------------------------------
# Main pipeline loop
# ---------------------------------------------------------------------------


def run_pipeline(workspace_path: Path, state: dict) -> None:
    """Advance each module through its lifecycle based on current status.

    Args:
        workspace_path: Path to the workspace directory.
        state: Loaded and pre-flight-validated state graph dict.

    Raises:
        SystemExit: On skill failure (exit 1) or pending_interview halt (exit 0).
    """
    modules = state.get("modules", [])

    for module in modules:
        module_id = module["id"]
        status = module.get("status")

        if status == "pending_extraction":
            print(f"[{module_id}] Running /extract...")
            if not execute_skill(_skill_cmd("extract", workspace_path, module_id)):
                set_module_status(state, module_id, "failed")
                save_state(workspace_path, state)
                print(
                    f"ERROR: /extract failed for '{module_id}'. "
                    "Module set to failed. Halting.",
                    file=sys.stderr,
                )
                sys.exit(1)
            set_module_status(state, module_id, "extracted")
            save_state(workspace_path, state)
            # Reload to pick up the updated module dict for the next iteration.
            state = load_state(workspace_path)
            module = get_module(state, module_id)
            status = module["status"]

        if status == "extracted":
            skip_adversarial = module.get("skip_adversarial", False)
            if skip_adversarial:
                set_module_status(state, module_id, "pending_integration")
                save_state(workspace_path, state)
                print(f"[{module_id}] skip_adversarial=true → advancing to pending_integration.")
                state = load_state(workspace_path)
                module = get_module(state, module_id)
                status = module["status"]
            else:
                applied_personas = module.get("applied_personas", [])
                for persona_id in applied_personas:
                    print(f"[{module_id}] Running /redteam with persona '{persona_id}'...")
                    if not execute_skill(_skill_cmd("redteam", workspace_path, module_id, persona_id)):
                        set_module_status(state, module_id, "failed")
                        save_state(workspace_path, state)
                        print(
                            f"ERROR: /redteam failed for '{module_id}'. "
                            "Module set to failed. Halting.",
                            file=sys.stderr,
                        )
                        sys.exit(1)

                set_module_status(state, module_id, "pending_interview")
                # Record adversarial state.
                module = get_module(state, module_id)
                adv = module.setdefault("adversarial_state", {})
                adv["status"] = "interview_in_progress"
                save_state(workspace_path, state)
                status = "pending_interview"

        if status == "pending_interview":
            print(
                f"ACTION REQUIRED: Run /interview {module_id} to complete the Q&A. "
                "Re-run orchestrator when done."
            )
            sys.exit(0)

        if status == "pending_integration":
            print(f"[{module_id}] Running /integrate...")
            if not execute_skill(_skill_cmd("integrate", workspace_path, module_id)):
                set_module_status(state, module_id, "failed")
                save_state(workspace_path, state)
                print(
                    f"ERROR: /integrate failed for '{module_id}'. "
                    "Module set to failed. Halting.",
                    file=sys.stderr,
                )
                sys.exit(1)
            set_module_status(state, module_id, "integrated")
            save_state(workspace_path, state)
            # Archive the active draft now that integration is complete.
            archive_draft(module_id, workspace_path)
            state = load_state(workspace_path)

        elif status == "integrated":
            print(f"[{module_id}] Already integrated — skipping.")

        elif status == "failed":
            print(
                f"ERROR: Module '{module_id}' is in failed state. "
                "Investigate the error, fix the cause, run audit_state.py, then retry.",
                file=sys.stderr,
            )
            sys.exit(1)

    print("Pipeline complete. All modules processed.")


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        description="Deterministic document orchestrator — YAML-driven state machine.",
    )
    parser.add_argument(
        "--workspace",
        required=True,
        metavar="PATH",
        help="Path to the workspace directory.",
    )
    parser.add_argument(
        "--reset",
        metavar="MODULE_ID",
        default=None,
        help="Archive the module's compiled output and revert it to pending_integration.",
    )
    return parser


def main() -> None:
    """Parse arguments and run the orchestrator."""
    parser = build_parser()
    args = parser.parse_args()

    workspace_path = Path(args.workspace).resolve()
    if not workspace_path.is_dir():
        print(
            f"ERROR: Workspace directory not found: '{workspace_path}'",
            file=sys.stderr,
        )
        sys.exit(1)

    lock_path = acquire_lock(workspace_path)

    try:
        if args.reset:
            run_reset(workspace_path, args.reset)
            return

        # Load and validate state.
        state = load_state(workspace_path)

        # Pre-flight validation.
        repo_root = Path(__file__).parent.resolve()
        preflight(workspace_path, state)

        # Snapshot personas before the loop so live mutations don't affect this run.
        snapshot_personas(workspace_path, state, repo_root)

        # Drive the pipeline.
        run_pipeline(workspace_path, state)

    finally:
        release_lock(lock_path)


if __name__ == "__main__":
    main()
