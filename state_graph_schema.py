#!/usr/bin/env python3
"""State Graph Schema and YAML I/O Module.

Provides the canonical schema definition and atomic read/write functions for
state_graph.yml. All orchestrator components must use these functions — never
write directly to state_graph.yml.

Schema (§5.5):
  document_meta:
    title: str
    type: str                     # e.g. "document", "prd"
    global_status: str            # "in_progress" | "completed"
    confidence_score: int         # 1-10; warns at pipeline start if < 7

  personas:
    - id: str
      version: int
      status: str                 # "clean" | "dirty"
      associated_file: str        # .agents/schemas/personas/<id>.md
      changelog: list[str]

  inputs:
    - id: str
      status: str                 # "clean"
      associated_file: str        # transcripts/raw_input.md

  modules:
    - id: str
      status: str                 # see VALID_STATUSES
      skip_adversarial: bool      # optional; default false
      max_questions: int          # optional; default 50
      associated_files:
        template: str
        draft: str
        compiled: str
      applied_personas: list[str]
      adversarial_state:
        status: str               # idle | interview_in_progress | ready_for_integration
        last_answered_index: int
        master_questionnaire: str
        answers_transcript: str
      candidate_outputs:
        draft_approved: bool
        questions_approved: bool
        compiled_approved: bool
"""

import os
import sys
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_STATUSES = [
    "pending_extraction",
    "extracted",
    "pending_interview",
    "pending_integration",
    "integrated",
    "failed",
]

STATE_GRAPH_FILENAME = "state_graph.yml"

# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------


def load_state(workspace_path: Path) -> dict:
    """Read and parse state_graph.yml from the given workspace.

    Args:
        workspace_path: Path to the workspace directory.

    Returns:
        Parsed state data as a dict.

    Raises:
        SystemExit: If the file is missing or contains invalid YAML.
    """
    state_file = workspace_path / STATE_GRAPH_FILENAME
    if not state_file.exists():
        print(
            f"ERROR: State graph not found at '{state_file}'. "
            "Run init_workspace.py first.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        data = yaml.safe_load(state_file.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        print(
            f"ERROR: Invalid YAML in '{state_file}': {exc}",
            file=sys.stderr,
        )
        sys.exit(1)

    if not isinstance(data, dict):
        print(
            f"ERROR: '{state_file}' did not parse to a mapping.",
            file=sys.stderr,
        )
        sys.exit(1)

    return data


def save_state(workspace_path: Path, state_data: dict) -> None:
    """Atomically write state_data to state_graph.yml.

    Writes to a .tmp file first, then calls os.replace() so a crash during
    the write never corrupts the live file.

    Args:
        workspace_path: Path to the workspace directory.
        state_data: State dict to serialise.
    """
    state_file = workspace_path / STATE_GRAPH_FILENAME
    tmp_file = workspace_path / f"{STATE_GRAPH_FILENAME}.tmp"

    tmp_file.write_text(
        yaml.dump(state_data, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )
    os.replace(str(tmp_file), str(state_file))


# ---------------------------------------------------------------------------
# Module accessors
# ---------------------------------------------------------------------------


def get_module(state: dict, module_id: str) -> dict:
    """Return the module dict for the given module ID.

    Args:
        state: Parsed state_graph dict.
        module_id: ID of the module to retrieve.

    Returns:
        The module dict.

    Raises:
        KeyError: If no module with the given ID exists.
    """
    for module in state.get("modules", []):
        if module.get("id") == module_id:
            return module
    raise KeyError(f"Module '{module_id}' not found in state graph.")


def set_module_status(state: dict, module_id: str, status: str) -> dict:
    """Update a module's status field in the state dict.

    Does NOT write to disk — caller must call save_state() afterwards.

    Args:
        state: Parsed state_graph dict (mutated in place).
        module_id: ID of the module to update.
        status: New status value; must be in VALID_STATUSES.

    Returns:
        The updated state dict.

    Raises:
        ValueError: If the status is not in VALID_STATUSES.
        KeyError: If the module_id does not exist.
    """
    if status not in VALID_STATUSES:
        raise ValueError(
            f"Invalid status '{status}'. Must be one of: {VALID_STATUSES}"
        )
    module = get_module(state, module_id)
    module["status"] = status
    return state
