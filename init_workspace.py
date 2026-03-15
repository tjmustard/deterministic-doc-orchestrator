#!/usr/bin/env python3
"""Workspace Initialization Script.

Creates a fully structured, isolated workspace for a new document generation job.
Validates all referenced persona and template files before touching the filesystem,
and registers the new workspace in .agents/workspace_registry.yml.

Usage:
    python init_workspace.py <job_name> [--workspace-root <path>] [--force]
        [--personas <id> ...] [--templates <id> ...]
"""

import argparse
import logging
import sys
import shutil
from pathlib import Path
from typing import Optional

import yaml

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

WORKSPACE_SUBDIRS = [
    "transcripts",
    "active",
    "compiled",
    "archive",
    "personas_snapshot",
]

PERSONAS_SCHEMA_DIR = Path(".agents/schemas/personas")
TEMPLATES_SCHEMA_DIR = Path(".agents/schemas/templates")
REGISTRY_PATH = Path(".agents/workspace_registry.yml")


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def validate_persona_ids(persona_ids: list[str], repo_root: Path) -> None:
    """Validate that all persona IDs resolve to files in the schemas directory.

    Args:
        persona_ids: List of persona ID strings to check.
        repo_root: Absolute path to the repository root.

    Raises:
        SystemExit: If any persona file is missing.
    """
    missing: list[str] = []
    for pid in persona_ids:
        candidate = repo_root / PERSONAS_SCHEMA_DIR / f"{pid}.md"
        if not candidate.exists():
            missing.append(str(candidate))
    if missing:
        log.error("Missing persona file(s):")
        for path in missing:
            log.error("  %s", path)
        sys.exit(1)


def validate_template_ids(template_ids: list[str], repo_root: Path) -> None:
    """Validate that all template IDs resolve to files and pass content checks.

    Args:
        template_ids: List of template ID strings to check.
        repo_root: Absolute path to the repository root.

    Raises:
        SystemExit: If any template file is missing or fails content validation.
    """
    missing: list[str] = []
    invalid: list[str] = []
    for tid in template_ids:
        candidate = repo_root / TEMPLATES_SCHEMA_DIR / f"{tid}.md"
        if not candidate.exists():
            missing.append(str(candidate))
            continue
        try:
            validate_template(candidate)
        except ValueError as exc:
            invalid.append(f"{candidate}: {exc}")

    if missing:
        log.error("Missing template file(s):")
        for path in missing:
            log.error("  %s", path)
    if invalid:
        log.error("Invalid template file(s):")
        for msg in invalid:
            log.error("  %s", msg)
    if missing or invalid:
        sys.exit(1)


def validate_template(path: Path) -> bool:
    """Check that a template file meets minimum structural requirements.

    Args:
        path: Path to the template markdown file.

    Returns:
        True if all checks pass.

    Raises:
        ValueError: Describing the first failing check.
    """
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()

    has_section_heading = any(
        line.startswith("## ") for line in lines
    )
    if not has_section_heading:
        raise ValueError("no '## ' section heading found")

    if "[Insert from transcript]" not in content:
        raise ValueError("no '[Insert from transcript]' placeholder found")

    return True


# ---------------------------------------------------------------------------
# Workspace guard
# ---------------------------------------------------------------------------


def workspace_exists(workspace_dir: Path) -> bool:
    """Return True if the directory exists and contains a state_graph.yml.

    Args:
        workspace_dir: Path to the candidate workspace directory.

    Returns:
        True if the directory is an initialised workspace.
    """
    return workspace_dir.is_dir() and (workspace_dir / "state_graph.yml").exists()


def wipe_workspace(workspace_dir: Path) -> None:
    """Remove and recreate a confirmed workspace directory.

    Only operates on directories confirmed to be workspaces (contain
    state_graph.yml) to avoid accidentally wiping unrelated directories.

    Args:
        workspace_dir: Path to an existing workspace directory.

    Raises:
        SystemExit: If the directory is not a confirmed workspace.
    """
    if not workspace_exists(workspace_dir):
        log.error(
            "Cannot wipe '%s': directory exists but is not a valid workspace "
            "(no state_graph.yml found). Aborting to prevent data loss.",
            workspace_dir,
        )
        sys.exit(1)
    shutil.rmtree(workspace_dir)


# ---------------------------------------------------------------------------
# Core creation logic
# ---------------------------------------------------------------------------


def create_workspace(
    job_name: str,
    workspace_root: Path,
    persona_ids: list[str],
    template_ids: list[str],
    force: bool,
    repo_root: Path,
) -> None:
    """Create a fully structured workspace for a document generation job.

    Validates all referenced files before touching the filesystem.  Writes
    state_graph.yml, ensures test directories exist, and appends the new
    workspace to the registry.

    Args:
        job_name: Identifier for the new job.
        workspace_root: Directory under which the workspace folder is created.
        persona_ids: Persona IDs to validate before creation.
        template_ids: Template IDs to validate before creation.
        force: When True, overwrite an existing workspace.
        repo_root: Absolute path to the repository root.

    Raises:
        SystemExit: On any validation or filesystem error.
    """
    workspace_dir = workspace_root / job_name

    # --- Task 2: Guard against overwriting ---
    if workspace_dir.exists() and (workspace_dir / "state_graph.yml").exists():
        if not force:
            print(
                f"ERROR: Workspace '{job_name}' already initialized. "
                "Use --force to overwrite.",
                file=sys.stderr,
            )
            sys.exit(1)
        wipe_workspace(workspace_dir)
    elif workspace_dir.exists() and (workspace_dir / "state_graph.yml").exists() is False:
        # Directory exists but is not a workspace — refuse to wipe it
        if not force:
            print(
                f"ERROR: Workspace '{job_name}' already initialized. "
                "Use --force to overwrite.",
                file=sys.stderr,
            )
            sys.exit(1)

    # --- Task 3: Validate personas and templates (fail before touching FS) ---
    validate_persona_ids(persona_ids, repo_root)
    validate_template_ids(template_ids, repo_root)

    # --- Task 5: Create workspace directory structure ---
    workspace_dir.mkdir(parents=True, exist_ok=True)
    created_dirs: list[Path] = [workspace_dir]
    for subdir in WORKSPACE_SUBDIRS:
        sub_path = workspace_dir / subdir
        sub_path.mkdir()
        created_dirs.append(sub_path)

    # --- Task 6: Write minimal state_graph.yml ---
    state_graph_path = workspace_dir / "state_graph.yml"
    state_graph: dict = {
        "job_name": job_name,
        "global_status": "in_progress",
        "confidence_score": 0,
    }
    state_graph_path.write_text(
        yaml.dump(state_graph, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )

    # --- Task 7: Ensure test directories exist ---
    test_dirs = [
        repo_root / "tests" / "candidate_outputs",
        repo_root / "tests" / "fixtures",
    ]
    for td in test_dirs:
        if not td.exists():
            td.mkdir(parents=True)
            created_dirs.append(td)

    # --- Task 8: Register workspace in registry ---
    registry_path = repo_root / REGISTRY_PATH
    registry_path.parent.mkdir(parents=True, exist_ok=True)

    registry_data: dict = {"workspaces": []}
    if registry_path.exists():
        loaded = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict) and "workspaces" in loaded:
            registry_data = loaded

    absolute_workspace = str(workspace_dir.resolve())
    if absolute_workspace not in registry_data["workspaces"]:
        registry_data["workspaces"].append(absolute_workspace)

    registry_path.write_text(
        yaml.dump(registry_data, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )

    # --- Task 9: Print success summary ---
    print("=" * 60)
    print(f"Workspace '{job_name}' initialized successfully.")
    print("=" * 60)
    print("Created directories:")
    for d in created_dirs:
        print(f"  {d}")
    print(f"State graph:  {state_graph_path}")
    print(f"Registry:     {registry_path} → {absolute_workspace}")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        description="Initialize a deterministic document orchestrator workspace.",
    )
    parser.add_argument(
        "job_name",
        help="Unique name for this document generation job.",
    )
    parser.add_argument(
        "--workspace-root",
        default=".",
        metavar="PATH",
        help="Parent directory for the workspace (default: current directory).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing workspace.",
    )
    parser.add_argument(
        "--personas",
        nargs="+",
        default=[],
        metavar="ID",
        help="Persona IDs to validate against .agents/schemas/personas/.",
    )
    parser.add_argument(
        "--templates",
        nargs="+",
        default=[],
        metavar="ID",
        help="Template IDs to validate against .agents/schemas/templates/.",
    )
    return parser


def main() -> None:
    """Parse arguments and run workspace initialization."""
    parser = build_parser()
    args = parser.parse_args()

    repo_root = Path(__file__).parent.resolve()
    workspace_root = Path(args.workspace_root).resolve()

    create_workspace(
        job_name=args.job_name,
        workspace_root=workspace_root,
        persona_ids=args.personas,
        template_ids=args.templates,
        force=args.force,
        repo_root=repo_root,
    )


if __name__ == "__main__":
    main()
