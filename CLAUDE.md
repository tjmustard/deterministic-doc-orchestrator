# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **HACF as a Toolchain:** This project uses the Hypergraph Coding Agent Framework
> (HACF) as its development toolchain. The skills in `.agents/skills/`, the scripts
> in `.agents/scripts/`, and the schemas in `.agents/schemas/` are development tools —
> they are **not** subjects of this project's plans, PRDs, or architecture docs.
> When you create SuperPRDs, MiniPRDs, or architecture nodes, you are documenting
> **this project**, not the HACF framework itself.

> **For Human Developers:** See `README.md` for the complete usage guide, available slash
> commands, and setup instructions.

---

## Project: Deterministic Document Orchestrator (DDO)

DDO is an AI-augmented document engine that transforms structured YAML source files into reproducible PDFs, HTML, and Markdown via a strict 5-phase pipeline: **Ingest → Render → Red Team → Interview → Refine**. HACF drives the state machine and cognitive loops; DDO provides the domain layer (schemas, templates, personas). The pipeline is governed by mandatory human-in-the-loop gates and a zero-hallucination constraint — every generated word must trace back to a version-controlled YAML source.

### Key Design Invariants

These apply to all code and AI-generated content in this project:

- **YAML is the source of truth.** Never patch a rendered document directly. Always patch `document_data.yaml`, then re-render via `ddo-render`.
- **Zero hallucination.** If a schema field cannot be verifiably filled from source material, write the literal string `[REQUIRES USER INPUT: <reason>]`. Never invent dates, metrics, or technical specifics.
- **HITL gates are mandatory.** Each pipeline phase ends with `[WAITING FOR USER REVIEW]`. Do not auto-advance to the next phase.
- **Red Team reads Jinja2, not PDF.** The adversarial critique targets the Markdown/HTML render because both formats derive deterministically from the same YAML, making the critique mathematically valid for the PDF while guaranteeing 100% accurate AI parsing.
- **Mutations are YAML-only.** `red_team_report.yaml` and `interview_log.yaml` are the machine-readable data layer. The ephemeral human-review Markdown is read-only and must never be parsed programmatically.

---

## Directory Structure

```
ddo/
├── schemas/     # Minimal-contract YAML definitions (meta + evidence_bank required)
├── templates/   # Typst (.typst) and Jinja2 (.jinja2) rendering templates
├── personas/    # Adversarial review lenses (product_critic, scientific_reviewer)
├── skills/      # ddo-*.md HACF cognitive node definitions
└── build.py     # PEP 723 hermetic build orchestrator (invoke via `uv run`)

Documents/       # Generated output — gitignored; structure: YYYY.MM.DD_DocType_Title/
PRDs/            # Project-level planning documents and domain schemas
spec/compiled/   # Ground truth: architecture.yml, SuperPRD, MiniPRDs
spec/active/     # Working drafts — temporary, archived after each phase
tests/fixtures/  # Verified regression baselines
tests/candidate_outputs/  # Unverified AI outputs — blocked from agent reads
```

---

## Commands

```bash
# Render a document (core build step)
uv run ddo/build.py --data <path/to/document_data.yaml> --template <template_name> --format <pdf|html|md> --output <output_path>

# Lint — both must exit 0 before any PR
uv run ruff check .
uv run ruff format --check .

# Tests
uv run pytest                    # all tests
uv run pytest tests/unit/        # unit only
uv run pytest tests/integration/ # integration only

# Hypergraph maintenance — run after modifying any architecture node
python .agents/scripts/hypergraph_updater.py spec/compiled/architecture.yml <node_id>

# Archive specs after a specification phase completes
python .agents/scripts/archive_specs.py <Feature_Name>
```

---

## Schema Contract

Every `document_data.yaml` file must satisfy the DDO minimal contract:

1. A `meta` block (includes `doc_type`, `title`, `version`, `date`, `persona`, `template`, `output_formats`).
2. An `evidence_bank` array — every claim in `content.sections[*].evidence` must reference an ID present here.

See `PRDs/product_requirements_document_schema.yaml` and `PRDs/scientific_report_schema.yaml` for the canonical schemas.

---

## For Claude Code: System Mandates

Read `AGENTS.md` for the full framework system mandates that apply to all IDEs.

**Claude Code-specific overrides and additions:**

### Tool Names
When skills say "read/write/run/edit a file," use these Claude Code tools:

| Action | Tool |
|---|---|
| Read a file | **Read** tool |
| Write a file | **Write** tool |
| Edit a file | **Edit** tool |
| Run a shell command | **Bash** tool |
| Ask the user a question | **AskUserQuestion** tool |
| Search file patterns | **Glob** tool |
| Search file contents | **Grep** tool |

### Skill Invocation
Skills are available as slash commands in `.claude/commands/`. Each command is a thin bridge
that reads its corresponding `.agents/skills/hyper-<name>/SKILL.md`. When the user invokes a command,
the skill file provides the full instructions.

### Task Tracking
For any task involving 3 or more steps, use the built-in task tools **before** starting work:
- **TaskCreate** — create tasks with clear subjects
- **TaskUpdate** — mark `in_progress` when starting, `completed` when done
- **TaskList** — check overall progress

### Context Window Management
When a skill instructs you to "open a new context window": **complete the current agent turn**,
then inform the user to start a new conversation thread for the next phase. This prevents
cross-contamination between adversarial agents (the Red Team must not see the Architect's
conversation history).

---

## Schema Definitions

See `AGENTS.md` → "Schema Definitions" for SuperPRD, MiniPRD, and architecture.yml schemas.
These are the templates to use when creating specifications for **this project**.
