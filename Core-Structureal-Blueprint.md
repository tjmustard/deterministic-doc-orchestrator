Core Structural Blueprints
1. AGENT.md (The Meta-Prompt for your Coding Assistant)
Save this in the root of your project. When you start your coding agent, tell it: "Read AGENT.md before you write any code."
``` Markdown
# AGENT INSTRUCTIONS: Building the Orchestrator Repository

**Your Role:** You are an expert Python developer and Systems Architect. You are building a deterministic CLI orchestrator that manages a multi-agent text generation pipeline.

## 1. Core Architectural Constraints (DO NOT DEVIATE)
1. **No Probabilistic Orchestration:** Do not write code that uses an LLM to decide the "next step" in the workflow. The workflow state is deterministically managed by the `.agent/schemas/state_graph.yml` file. 
2. **File System Firewall:** The scripts you write must strictly enforce the directory boundaries defined in `README.md`. Agents/Skills must never read from the `archive/` folder.
3. **No Database Dependencies:** Do not introduce SQLite, PostgreSQL, or Redis. The YAML file *is* the database.

## 2. Your Implementation Tasks
You will implement the Python scaffolding described in `README.md`. Proceed strictly in this order:

* **Task 1: Directory Initialization.** Write a script (`init_workspace.py`) that generates the exact folder structure and empty files defined in the `README.md` File System Firewall section.
* **Task 2: The YAML Parser.** Implement the read/write functions for `state_graph.yml` within the `orchestrator.py` script.
* **Task 3: The CLI Skills (Mocking Phase).** Before we wire up real LLM calls, create mock python scripts (e.g., `mock_extract.py`, `mock_redteam.py`) that simply read the input files and write dummy text to the output files.
* **Task 4: The Orchestrator Logic.** Finish implementing `orchestrator.py` so that it successfully loops through the `state_graph.yml` using the mock skills.
* **Task 5: The Archival Script.** Implement `.agent/scripts/archive_manager.py` to move files from `active/` to `archive/` with a prepended timestamp (e.g., `20260314_121843_draft_novelty.md`).

## 3. Handling Subprocesses
When implementing `orchestrator.py`, wrap all skill executions in a robust `try/except` block using Python's `subprocess` module. If a subprocess fails, the orchestrator MUST halt. Do not attempt to automatically retry an LLM skill if it fails; fail loudly so the human operator can debug.
```

2. .agent/scripts/archive_manager.py
This script is critical. It is referenced in the "Coding 4.0" whitepaper you provided. Its job is to flush the active directory so that the final Integration agent doesn't accidentally read an old, rejected draft.
Tell your coding agent to implement this logic:
``` Python
#!/usr/bin/env python3
import os
import sys
import shutil
import datetime
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent.parent.resolve()
ACTIVE_DIR = BASE_DIR / "active"
ARCHIVE_DIR = BASE_DIR / "archive"

def archive_draft(module_id: str):
    """Moves a specific active draft to the archive with a timestamp."""
    
    # Ensure archive directory exists
    if not ARCHIVE_DIR.exists():
        ARCHIVE_DIR.mkdir(parents=True)
        
    filename = f"draft_{module_id}.md"
    src_file = ACTIVE_DIR / filename
    
    if not src_file.exists():
        print(f"INFO: No active draft found for {module_id} at {src_file}")
        return

    # Generate timestamped filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    archived_filename = f"{timestamp}_{filename}"
    dst_file = ARCHIVE_DIR / archived_filename
    
    try:
        shutil.move(str(src_file), str(dst_file))
        print(f"SUCCESS: Archived {filename} -> {dst_file}")
    except Exception as e:
        print(f"ERROR: Failed to archive {filename}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python archive_manager.py <module_id>")
        sys.exit(1)
    
    archive_draft(sys.argv[1])
```

3. .agent/scripts/audit_state.py
This script reconciles the YAML file against the actual file system. If the Orchestrator script crashes, or if the user manually moves a file, this script ensures the YAML file doesn't get out of sync.
``` Python
#!/usr/bin/env python3
import yaml
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent.resolve()
STATE_GRAPH_PATH = BASE_DIR / ".agent" / "schemas" / "state_graph.yml"
ACTIVE_DIR = BASE_DIR / "active"
COMPILED_DIR = BASE_DIR / "compiled"

def load_state():
    with open(STATE_GRAPH_PATH, 'r') as f:
        return yaml.safe_load(f)

def save_state(state_data):
    with open(STATE_GRAPH_PATH, 'w') as f:
        yaml.dump(state_data, f, sort_keys=False, default_flow_style=False)

def audit():
    state = load_state()
    modules = state.get('modules', [])
    
    print("Auditing State Graph against File System...")
    
    for module in modules:
        mod_id = module['id']
        current_status = module['status']
        
        compiled_file = COMPILED_DIR / f"final_{mod_id}.md"
        draft_file = ACTIVE_DIR / f"draft_{mod_id}.md"
        
        # Rule 1: If compiled file exists, state must be 'integrated'
        if compiled_file.exists() and current_status != 'integrated':
            print(f"AUDIT FIX: {mod_id} compiled file exists. Forcing status to 'integrated'.")
            module['status'] = 'integrated'
            
        # Rule 2: If we are 'extracted' but the draft file is missing, revert to 'pending_extraction'
        elif current_status in ['extracted', 'pending_interview', 'pending_integration']:
            if not draft_file.exists():
                print(f"AUDIT FIX: {mod_id} draft file is missing! Reverting to 'pending_extraction'.")
                module['status'] = 'pending_extraction'
                
    save_state(state)
    print("Audit Complete. State graph reconciled.")

if __name__ == "__main__":
    audit()
```

Final Next Steps for Implementation
You now have the absolute complete package. To begin:
Create a new directory locally (e.g., mkdir invention_orchestrator).
Drop the README.md (from my previous response), the AGENT.md, and the two python scripts above into that directory.
Open your terminal, initialize your coding agent (e.g., claude), and paste this exact prompt:
"Read AGENT.md and README.md. I want you to execute Task 1 and Task 2. Do not proceed to Task 3 until I review your work."


