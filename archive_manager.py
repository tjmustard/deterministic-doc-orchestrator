#!/usr/bin/env python3
"""Archive Manager Script.

Moves files from a workspace's active/ directory to archive/ with
microsecond-precision timestamps to prevent filename collisions.

Only this module may write to archive/; all other agents are blocked by
.agentignore.

Usage:
    python archive_manager.py --module <module_id> --workspace <path>
"""

import argparse
import datetime
import shutil
import sys
from pathlib import Path


def archive_compiled(module_id: str, workspace_path: Path) -> None:
    """Move compiled/final_<module_id>.md to archive/ with a microsecond timestamp.

    If the source file does not exist, logs an INFO message and returns without
    raising an exception.

    Args:
        module_id: The module whose compiled file should be archived.
        workspace_path: Path to the workspace directory.
    """
    src_file = workspace_path / "compiled" / f"final_{module_id}.md"
    archive_dir = workspace_path / "archive"

    if not src_file.exists():
        print(
            f"INFO: No compiled file found for {module_id} at {src_file}. "
            "Skipping archive."
        )
        return

    archive_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    archived_filename = f"{timestamp}_final_{module_id}.md"
    dest = archive_dir / archived_filename

    shutil.move(str(src_file), str(dest))
    print(f"SUCCESS: Archived {src_file.name} → {dest}")


# ---------------------------------------------------------------------------
# Core function
# ---------------------------------------------------------------------------


def archive_draft(module_id: str, workspace_path: Path) -> None:
    """Move active/draft_<module_id>.md to archive/ with a microsecond timestamp.

    If the source file does not exist, logs an INFO message and returns without
    raising an exception.

    Args:
        module_id: The module whose draft file should be archived.
        workspace_path: Path to the workspace directory.
    """
    src_file = workspace_path / "active" / f"draft_{module_id}.md"
    archive_dir = workspace_path / "archive"

    if not src_file.exists():
        print(
            f"INFO: No active draft found for {module_id} at {src_file}. "
            "Skipping archive."
        )
        return

    archive_dir.mkdir(parents=True, exist_ok=True)

    # Microsecond precision (%f) prevents collision on rapid sequential calls.
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    archived_filename = f"{timestamp}_draft_{module_id}.md"
    dest = archive_dir / archived_filename

    shutil.move(str(src_file), str(dest))
    print(f"SUCCESS: Archived {src_file.name} → {dest}")


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        description="Archive an active module draft with a microsecond timestamp.",
    )
    parser.add_argument(
        "--module",
        required=True,
        metavar="MODULE_ID",
        help="ID of the module whose draft should be archived.",
    )
    parser.add_argument(
        "--workspace",
        required=True,
        metavar="PATH",
        help="Path to the workspace directory.",
    )
    return parser


def main() -> None:
    """Parse arguments and run archive_draft."""
    parser = build_parser()
    args = parser.parse_args()

    workspace_path = Path(args.workspace).resolve()
    if not workspace_path.is_dir():
        print(
            f"ERROR: Workspace directory not found: '{workspace_path}'",
            file=sys.stderr,
        )
        sys.exit(1)

    archive_draft(module_id=args.module, workspace_path=workspace_path)


if __name__ == "__main__":
    main()
