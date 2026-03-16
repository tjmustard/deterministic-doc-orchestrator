# deterministic-doc-orchestrator

A multi-agent CLI pipeline that uses deterministic YAML-driven state management to generate and rigorously stress-test complex technical documents (patent disclosures, PRDs, legal briefs, and more).

LLM reasoning is strictly confined to individual skill steps. All routing, state transitions, and file management are handled by deterministic Python — no AI ever decides what happens next.

---

## How it works

```
[Transcript] → /extract → /redteam × N personas → /interview → /integrate → /promote → [Approved Doc]
```

Each document section is a **module** with an explicit status in `state_graph.yml`. `orchestrator.py` reads that file and calls the correct skill subprocess — advancing, halting, or failing deterministically based on status alone.

---

## Installation

**Prerequisites:** Python 3, `pip`, `git`, a Claude Code (or compatible) agentic IDE.

```bash
# Interactive (choose which IDEs to support)
bash install.sh

# Non-interactive (installs all IDEs)
bash install.sh -y

# Specific IDEs only
bash install.sh --ides="claude,windsurf"
```

The installer:
- Copies `.agents/`, `spec/`, `tests/`, `docs/`, `.agentignore` into your repo.
- Copies IDE-specific config files (e.g. `CLAUDE.md`, `GEMINI.md`, `.claude/`).
- Installs the `pyyaml` Python dependency.
- Optionally adds IDE paths to `.gitignore`.

**Upgrade an existing installation:**

```bash
bash install.sh          # prompts per-directory
bash install.sh -y       # accepts all updates
```

---

## Quick start

```bash
# 1. Scaffold a workspace for a new job
python init_workspace.py my_patent \
  --personas patent_examiner skeptic \
  --templates invention_disclosure

# 2. Run the orchestrator — it drives the full pipeline automatically
python orchestrator.py --workspace ./my_patent

# 3. The orchestrator halts at pending_interview. Run the interview skill,
#    then re-run the orchestrator to continue.

# 4. After integration, review and approve outputs
#    /promote my_patent_module   (in your agentic IDE)
```

---

## CLI reference

### `init_workspace.py` — scaffold a job workspace

```
python init_workspace.py <job_name> [OPTIONS]
```

| Option | Description |
|---|---|
| `--workspace-root <path>` | Parent directory for the workspace (default: `.`) |
| `--personas <id> ...` | Persona IDs to validate against `.agents/schemas/personas/` |
| `--templates <id> ...` | Template IDs to validate against `.agents/schemas/templates/` |
| `--force` | Wipe and recreate an existing workspace |

Creates: `<job_name>/{state_graph.yml, transcripts/, active/, compiled/, archive/, personas_snapshot/}`

Validates all referenced persona and template files **before** touching the filesystem.

---

### `orchestrator.py` — YAML-driven state machine

```
python orchestrator.py --workspace <path> [--reset <module_id>]
```

| Option | Description |
|---|---|
| `--workspace <path>` | Path to the workspace directory (required) |
| `--reset <module_id>` | Archive compiled output and revert module to `pending_integration` |

**What it does on each run:**

1. Acquires `<workspace>/.orchestrator.lock` — aborts if it already exists.
2. Validates state YAML, warns if `confidence_score < 7`, checks all referenced files exist, scans `active/`, `transcripts/`, `compiled/` for symlinks.
3. Snapshots global persona files into `<workspace>/personas_snapshot/`.
4. Iterates over modules in order, invoking `claude /{skill} --workspace <path>` subprocesses:

| Module status | Action |
|---|---|
| `pending_extraction` | Run `/extract`; advance to `extracted` or set `failed` |
| `extracted` | Run `/redteam` per persona; advance to `pending_interview` (or `pending_integration` if `skip_adversarial: true`) |
| `pending_interview` | **Halt** — operator must run `/interview`, then re-run orchestrator |
| `pending_integration` | Run `/integrate`; advance to `integrated`; archive active draft |
| `integrated` | Skip |
| `failed` | **Halt** with error — investigate, run `audit_state.py`, retry |

On any subprocess failure: sets module status to `failed`, writes state atomically, exits 1. Lockfile is always cleaned up via `try/finally`.

---

### `extract.py` — map transcript to template schema

```
python extract.py <module_id> --workspace <path>
```

| Option | Description |
|---|---|
| `--workspace <path>` | Path to the workspace directory (required) |

Loads `state_graph.yml`, resolves the module's template from `associated_files.template`, validates that `transcripts/raw_input.md` is non-empty, then calls `claude -p` with a Technical Scraper prompt to extract draft content. Writes `active/draft_<module_id>.md`, copies it to `tests/candidate_outputs/`, and atomically advances the module status to `extracted`.

Aborts with exit code 1 (state unchanged) if the transcript is missing/empty or the claude subprocess fails. Prints a WARNING if any `[NEEDS_CLARIFICATION]` markers are present, but does **not** halt — the red-team interrogates gaps downstream.

Normally invoked by `orchestrator.py` via `claude /extract`. Can be run standalone for debugging.

---

### `redteam.py` — adversarial questionnaire generator

```
python redteam.py <module_id> <persona_id> --workspace <path>
```

| Option | Description |
|---|---|
| `--workspace <path>` | Path to the workspace directory (required) |

Loads `state_graph.yml`, resolves `active/draft_<module_id>.md` (aborts if missing), and locates the persona from `personas_snapshot/<persona_id>.md` — falling back to `.agents/schemas/personas/<persona_id>.md` if no snapshot exists yet.

Reads `active/module_<module_id>_questions.md` and counts existing numbered questions (`^\d+\.`) to calculate remaining capacity against `module.max_questions` (default 50). If capacity is exhausted, prints a WARNING and exits 0 without appending. Otherwise, calls `claude -p` with the persona framing + full draft content and generates adversarial questions targeting every claim, assumption, and `[NEEDS_CLARIFICATION]` marker.

If the LLM generates more questions than the remaining capacity, truncates with a WARNING. Appends a `## Persona: <id>` header block to the questionnaire, copies the full questionnaire to `tests/candidate_outputs/`, and atomically sets `adversarial_state.status` to `interview_in_progress`.

Multiple personas are run sequentially — call once per persona. The question cap is shared across all personas for a given module.

Normally invoked by `orchestrator.py` for each persona in `applied_personas`. Can be run standalone for debugging or to add a persona mid-pipeline.

---

### `interview.py` — resumable paced Q&A

```
python interview.py <module_id> --workspace <path>
```

| Option | Description |
|---|---|
| `--workspace <path>` | Path to the workspace directory (required) |

Loads `state_graph.yml`, reads `adversarial_state.last_answered_index` (default `0`), and parses `active/module_<module_id>_questions.md` for numbered questions (`^\d+\.`). Presents unanswered questions in batches of 3. Saves `last_answered_index` atomically to `state_graph.yml` after each answer. Operator types `DONE` at the initial gate prompt or after any batch of 3 to pause and exit — progress is preserved. Re-running resumes from the next unanswered question. On completion of all questions, advances module status to `pending_integration` and `adversarial_state.status` to `ready_for_integration`. Never modifies the questionnaire file.

Normally invoked interactively by the operator after the orchestrator halts at `pending_interview`. Can be run standalone.

---

### `integrate.py` — synthesize draft + Q&A answers into a final candidate document

```
python integrate.py <module_id> --workspace <path>
```

| Option | Description |
|---|---|
| `--workspace <path>` | Path to the workspace directory (required) |

Loads `state_graph.yml`, resolves `active/draft_<module_id>.md` (aborts if missing), and validates that `transcripts/module_<module_id>_answers.md` is non-empty (aborts with exit code 1 if absent or empty, with the message: `ERROR: No answers transcript found for module '<id>'. Run /interview first.`).

Constructs a Resolution Agent prompt containing the original template schema, the baseline draft (labeled `BASELINE DRAFT:`), and the answers transcript (labeled `ADVERSARIAL Q&A ANSWERS:`), then calls `claude -p` to synthesize a final, defensible document section. Writes the output to `tests/candidate_outputs/final_<module_id>.md` only — never to `compiled/`. Does **not** update `state_graph.yml`; status advances to `integrated` only after `/promote` approves the candidate output.

Prints: `Integration complete. Review the output at tests/candidate_outputs/final_<module_id>.md. Run /promote <module_id> to approve and move to compiled/`

Normally invoked by `orchestrator.py` after `pending_integration` status is reached. Can be run standalone for debugging.

---

### `promote.py` — review and approve candidate outputs

```
python promote.py <module_id> --workspace <path>
```

| Option | Description |
|---|---|
| `--workspace <path>` | Path to the workspace directory (required) |

Loads `state_graph.yml`, then locates the three candidate output files for the module in `tests/candidate_outputs/` — `draft_<module_id>.md`, `module_<module_id>_questions.md`, and `final_<module_id>.md` — skipping any that do not exist. Presents each file's full contents to the operator in pipeline order (draft → questions → final) and prompts for an explicit decision.

**On `APPROVE`:** moves the file to `tests/fixtures/` using `shutil.move()`, sets the corresponding approval flag (`candidate_outputs.draft_approved`, `questions_approved`, or `compiled_approved`) to `true` in `state_graph.yml`, and writes state atomically before prompting for the next file.

**On `REJECT <reason>`:** appends `{"file": ..., "reason": ..., "timestamp": "<ISO8601>"}` to a `rejections` list on the module in `state_graph.yml`, resets module status to `pending_integration`, saves state atomically, and halts — remaining files are not reviewed. Fix the issue and re-run `/integrate`.

If all pending candidate outputs are approved, sets module status to `integrated`, calls `archive_manager.archive_draft()` to flush the active draft, and prints confirmation.

If no candidate output files are present, prints an informative message and exits cleanly with no state change.

> **Note:** Nothing is ever automatically approved. `APPROVE` must be typed explicitly for each file. `tests/fixtures/` is append-only — `/promote` never deletes files from it.

Normally invoked interactively by the operator after `/integrate` completes. Can be run standalone.

---

### `audit_state.py` — reconcile state after a crash

```
python audit_state.py --workspace <path>
```

Scans the workspace filesystem and reconciles `state_graph.yml`. Detects drifted or failed modules after a crash or manual file move, prints a human-readable diff, and writes corrected statuses back atomically.

---

### `archive_manager.py` — archive files with collision-proof timestamps

```
python archive_manager.py --module <module_id> --workspace <path>
```

Moves `active/draft_<module_id>.md` to `archive/<timestamp_us>_draft_<module_id>.md`. Timestamps use microsecond precision (`%Y%m%d_%H%M%S_%f`) to prevent collisions on rapid sequential calls.

Also importable directly:

```python
from archive_manager import archive_draft, archive_compiled

archive_draft("novelty", workspace_path)       # archives active/draft_novelty.md
archive_compiled("novelty", workspace_path)    # archives compiled/final_novelty.md
```

---

## Slash commands (agentic IDE)

| Command | Description |
|---|---|
| `/template-architect` | Guided interview to create a new document-type template in `.agents/schemas/templates/` |
| `/forge_persona` | Create a new adversarial persona in `.agents/schemas/personas/` |
| `/forge_persona --update <id>` | Update an existing persona (warns if active jobs reference it) |
| `/extract <module_id>` | Map transcript to template; write `active/draft_<id>.md`; mark `extracted` |
| `/redteam <module_id> <persona_id>` | Append adversarial questions to master questionnaire (50-question cap) |
| `/interview <module_id>` | Pace Q&A 3 questions at a time; type `DONE` to pause; resumes from last index |
| `/integrate <module_id>` | Synthesize final compiled doc from draft + Q&A answers |
| `/promote <module_id>` | Present candidate outputs for APPROVE/REJECT; approved files move to `tests/fixtures/` |
| `/hyper-redteam` | Framework-level PRD stress-test — OWASP/scalability/logic analysis of `spec/active/Draft_PRD.md` |

---

## Workspace structure

```
<job_name>/
├── .orchestrator.lock            # Created at pipeline start, deleted on exit
├── state_graph.yml               # Deterministic state — always written atomically
├── personas_snapshot/            # Frozen copy of personas at pipeline start
├── transcripts/
│   ├── raw_input.md              # Operator-provided source transcript
│   └── module_<id>_answers.md   # Q&A answers from /interview
├── active/
│   ├── draft_<module_id>.md
│   └── module_<module_id>_questions.md
├── compiled/
│   └── final_<module_id>.md
└── archive/
    └── <timestamp_us>_draft_<module_id>.md
```

**Global (repo-level):**

```
.agentignore                        # Blocks agents from reading **/archive/**
.agents/
├── workspace_registry.yml          # Index of all initialized workspaces
├── schemas/
│   ├── personas/<id>.md            # Versioned adversarial personas
│   └── templates/<id>.md          # Document type templates
└── scripts/
    ├── hypergraph_updater.py
    └── archive_specs.py
tests/
├── candidate_outputs/              # AI-generated, awaiting human review
└── fixtures/                       # Human-approved ground truth
```

---

## Uninstall

The framework installs only files and directories into your repo — no system-level changes, no daemons, no entries outside the project directory.

**Remove all framework files:**

```bash
# Core framework
rm -rf .agents/ spec/ tests/ docs/ .agentignore

# Python scripts (if added at repo root)
rm -f init_workspace.py orchestrator.py audit_state.py archive_manager.py state_graph_schema.py extract.py redteam.py interview.py integrate.py promote.py

# IDE-specific files — remove whichever you installed:
rm -rf .claude/ .windsurf/ .cursor/ .clinerules/ .roo/
rm -f CLAUDE.md GEMINI.md AGENTS.md install.sh
```

**Remove the Python dependency (only if nothing else uses it):**

```bash
pip uninstall pyyaml
```

**Clean up `.gitignore` entries** (if you added IDE paths during install): remove the `# Hypergraph Coding Agent Framework — IDE config` block and the entries below it.

**Remove workspace directories** created by `init_workspace.py` (these are wherever you ran the script — check `.agents/workspace_registry.yml` for the full list before deleting):

```bash
# Example — adjust paths per your registry
rm -rf ./my_patent ./my_prd
```
