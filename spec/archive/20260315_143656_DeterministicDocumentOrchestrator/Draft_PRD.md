# Draft PRD: Deterministic Document Orchestrator

## Metadata
- **Project Name**: Deterministic Document Orchestrator
- **Version**: 1.0.0
- **Status**: Draft
- **Owner**: Architect Agent

---

## 1. Introduction & Goals

### 1.1 Problem Statement
Manual creation of complex, high-stakes documents (e.g., patent invention disclosures, PRDs, legal briefs) is slow, inconsistent, and error-prone. LLMs fail when given monolithic context — they hallucinate, lose nuance, and flatten technical precision into generic prose.

The root cause is the **Specification Alignment Problem**: probabilistic reasoning (LLM text generation) is coupled with state management (deciding what to generate next), causing context collapse.

### 1.2 Solution Overview
A general-purpose, multi-agent CLI orchestrator that:
1. Decouples LLM reasoning from deterministic state management via a YAML state graph.
2. Breaks document generation into modular, isolated phases (Extract → Red Team → Interview → Integrate).
3. Enforces adversarial quality control through configurable, reusable persona agents.
4. Provides two interfaces: Claude Code slash commands (design-time) and a Python CLI (runtime automation).

The system is document-type-agnostic. Any document type can be orchestrated by defining a template schema and one or more adversarial personas.

### 1.3 Target Audience
A single human operator (the document author) who:
- Provides raw input as plain Markdown or text transcripts.
- Uses slash commands to configure document types and personas.
- Uses the Python CLI to run the automated pipeline.
- Performs final human review and approval of all AI-generated outputs before use.

---

## 2. Confidence Mandate
**Confidence Score**: 8/10

**Clarifying Questions** (for Red Team to stress-test):
- [ ] How should the system handle a module where the transcript provides insufficient data — halt the pipeline or continue with `[NEEDS_CLARIFICATION]` markers and flag for human review?
- [ ] When multiple personas interrogate the same module, should questions be deduplicated, or is a verbatim union acceptable?
- [ ] Should the `/forge_persona` update flow diff the existing persona file and show the user what changed, or overwrite silently?
- [ ] What is the rollback strategy if the Integration Agent produces a compiled output the user rejects?

---

## 3. Scope

### 3.1 In-Scope
- Per-job isolated workspace directory with its own `state_graph.yml`
- YAML-driven deterministic state machine (`orchestrator.py`)
- Plain Markdown/text-only inputs (no audio, no STT)
- Modular document sections as first-class units (modules)
- Multiple simultaneous adversarial personas per module, all contributing to a single master questionnaire
- `/forge_persona` skill: creates a new adversarial persona with guided interview
- `/forge_persona --update <persona_id>` option (or equivalent): modifies an existing persona
- Versioned, reusable persona artifacts stored in `.agents/schemas/personas/`
- `/extract [module_id]` skill: populates draft from transcript
- `/redteam [module_id] [persona_id]` skill: appends adversarial questions to master questionnaire
- `/interview [module_id]` skill: paces Q&A, 3 questions at a time
- `/integrate [module_id]` skill: synthesizes final compiled output
- `/audit_state` script: reconciles `state_graph.yml` against the filesystem
- Archive manager: timestamps and flushes active drafts post-integration
- All AI-generated outputs (drafts, questions, integrated documents) routed to `tests/candidate_outputs/` for human review before promotion to `tests/fixtures/`
- `template-architect` skill pathway: reverse-engineers a document into a reusable template schema

### 3.2 Out-of-Scope
- Audio file ingestion or Speech-to-Text integration
- Multi-user / team collaboration (single operator only)
- External database (SQLite, PostgreSQL, Redis) — YAML is the database
- Approval workflow integration (approval happens outside this system)
- CI/CD pipeline triggering
- Web UI or API server
- LLM-driven graph traversal (all routing is deterministic Python)

---

## 4. User Stories (Atomic)

| ID | User Story | Acceptance Criteria | Priority |
| :--- | :--- | :--- | :--- |
| US-001 | As an operator, I want to initialize a new job workspace so that each document generation run is fully isolated. | 1. Running `init_workspace.py <job_name>` creates the full directory structure with an empty `state_graph.yml`.<br>2. Existing jobs are not affected. | High |
| US-002 | As an operator, I want to define a new adversarial persona using a guided skill so that I don't need to hand-write prompt files. | 1. `/forge_persona` asks targeted questions about document type and adversarial angle.<br>2. Outputs a validated `.md` persona file to `.agents/schemas/personas/`.<br>3. Persona is immediately selectable by `module_id` in `state_graph.yml`. | High |
| US-003 | As an operator, I want to update an existing persona so that I can tune its behavior without recreating it from scratch. | 1. `/forge_persona --update <persona_id>` loads the existing file and presents the current definition.<br>2. User edits are applied and the file is saved with a changelog comment. | High |
| US-004 | As an operator, I want to extract a module draft from a transcript so that the AI maps raw notes to the document schema. | 1. `/extract [module_id]` reads `transcripts/raw_input.md` and the module template.<br>2. Outputs `active/draft_[module_id].md` with `[NEEDS_CLARIFICATION]` for any missing data.<br>3. `state_graph.yml` status advances to `extracted`. | High |
| US-005 | As an operator, I want multiple adversarial personas to interrogate a module simultaneously so that the draft is stress-tested from multiple angles. | 1. `/redteam [module_id] [persona_id]` can be called for each persona assigned to the module.<br>2. All personas append questions to a single `active/module_[module_id]_questions.md`.<br>3. Questions are not deduplicated automatically (human reviews the full list). | High |
| US-006 | As an operator, I want to be interviewed 3 questions at a time so that I am not overwhelmed by a 50+ question list. | 1. `/interview [module_id]` reads the master questionnaire and presents exactly 3 unanswered questions per turn.<br>2. Answers are appended to `transcripts/module_[module_id]_answers.md`.<br>3. The skill halts and saves state when the operator ends the session. | High |
| US-007 | As an operator, I want the integration agent to synthesize the final document from the baseline draft and Q&A answers so that the output is complete and defensible. | 1. `/integrate [module_id]` reads both the draft and the answers transcript.<br>2. Outputs `compiled/final_[module_id].md`.<br>3. Output is routed to `tests/candidate_outputs/` for review. | High |
| US-008 | As an operator, I want the Python CLI to automate the pipeline so that I don't manually invoke each skill step. | 1. `python orchestrator.py` reads `state_graph.yml` and calls the correct skill per module status.<br>2. Pipeline halts gracefully at `pending_interview` for human input.<br>3. On subprocess failure, the CLI fails loudly with the error; no auto-retry. | High |
| US-009 | As an operator, I want the state graph to be reconcilable against the filesystem so that a crash or manual file move doesn't corrupt the pipeline. | 1. `python audit_state.py` scans the filesystem and updates `state_graph.yml` statuses to match reality.<br>2. Prints a human-readable diff of any changes made. | Medium |
| US-010 | As an operator, I want AI-generated outputs reviewed before being treated as test fixtures so that hallucinations don't silently become ground truth. | 1. All three output types (draft, questions, integrated doc) are written to `tests/candidate_outputs/`.<br>2. A human moves approved files to `tests/fixtures/` manually.<br>3. MiniPRD test type is updated to `deterministic` only after human approval. | High |

---

## 5. Technical Specifications (The Blueprint)

### 5.1 Architecture & Resolved Trade-offs

**Data Flow:**
```
[Human: raw transcript (Markdown/text)]
        ↓
[/extract] → active/draft_[module_id].md
        ↓
[/redteam × N personas] → active/module_[module_id]_questions.md (fan-in)
        ↓
[/interview] → transcripts/module_[module_id]_answers.md
        ↓
[/integrate] → compiled/final_[module_id].md → tests/candidate_outputs/
        ↓
[Human approval] → tests/fixtures/
```

**State Machine Statuses (per module):**
```
pending_extraction → extracted → pending_interview → pending_integration → integrated
```

**Resolved Trade-offs Log:**
- **Issue:** LLM-driven routing vs. deterministic routing
- **Options Considered:** Agent decides next step dynamically vs. Python reads YAML and routes
- **Resolution:** Deterministic Python routing only. LLMs are never given graph traversal responsibility.

- **Issue:** Single workspace vs. per-job isolation
- **Options Considered:** Shared global workspace vs. isolated directories per job
- **Resolution:** Per-job isolated workspace. Each job has its own `state_graph.yml`, `active/`, `compiled/`, `transcripts/`, and `archive/` directories.

- **Issue:** Persona scope (ephemeral vs. reusable)
- **Options Considered:** Persona files scoped to the job vs. global persona library
- **Resolution:** Personas are global, versioned artifacts in `.agents/schemas/personas/`. Jobs reference personas by ID. This enables reuse across document types.

### 5.2 System Graph Blast Radius
Architecture is greenfield — no existing nodes in `spec/compiled/architecture.yml`. New nodes to be created:

- `orchestrator_core` — Python state machine and YAML graph
- `workspace_init` — `init_workspace.py` scaffolding script
- `skill_forge_persona` — `/forge_persona` Claude Code skill
- `skill_extract` — `/extract` Claude Code skill
- `skill_redteam` — `/redteam` Claude Code skill
- `skill_interview` — `/interview` Claude Code skill
- `skill_integrate` — `/integrate` Claude Code skill
- `audit_state` — `audit_state.py` reconciliation script
- `archive_manager` — `archive_manager.py` flush script
- `candidate_output_router` — convention/protocol routing AI outputs to review directory
- `persona_library` — `.agents/schemas/personas/` versioned store

### 5.3 Execution Checklist (MiniPRDs)
- [ ] `spec/compiled/MiniPRD_WorkspaceInit.md` — `init_workspace.py` and directory structure
- [ ] `spec/compiled/MiniPRD_StateGraph.md` — `state_graph.yml` schema and YAML parser
- [ ] `spec/compiled/MiniPRD_Orchestrator.md` — `orchestrator.py` state machine loop
- [ ] `spec/compiled/MiniPRD_ForgePersona.md` — `/forge_persona` skill (create + update)
- [ ] `spec/compiled/MiniPRD_Extract.md` — `/extract` skill
- [ ] `spec/compiled/MiniPRD_RedTeam.md` — `/redteam` skill (multi-persona fan-in)
- [ ] `spec/compiled/MiniPRD_Interview.md` — `/interview` skill (3-questions-at-a-time pacing)
- [ ] `spec/compiled/MiniPRD_Integrate.md` — `/integrate` skill
- [ ] `spec/compiled/MiniPRD_AuditState.md` — `audit_state.py` reconciliation
- [ ] `spec/compiled/MiniPRD_ArchiveManager.md` — `archive_manager.py` flush script
- [ ] `spec/compiled/MiniPRD_CandidateOutputProtocol.md` — `tests/candidate_outputs/` review workflow

### 5.4 API Contracts / Schema

**state_graph.yml schema:**
```yaml
document_meta:
  title: string
  type: string           # e.g. "invention_disclosure", "prd", "legal_brief"
  global_status: string  # "in_progress" | "completed"

personas:
  - id: string
    status: string       # "clean" | "dirty" (dirty = modified since last use)
    associated_file: string  # path to .agents/schemas/personas/<id>.md

inputs:
  - id: string
    status: string       # "clean"
    associated_file: string  # path to transcripts/

modules:
  - id: string
    status: string       # pending_extraction | extracted | pending_interview | pending_integration | integrated
    associated_files:
      template: string
      draft: string
      compiled: string
    applied_personas: [string]   # list of persona IDs (multiple supported)
    adversarial_state:
      status: string     # idle | interview_in_progress | ready_for_integration
      master_questionnaire: string
      answers_transcript: string
```

**Per-Job Workspace Directory Structure:**
```
<job_name>/
├── transcripts/
│   ├── raw_input.md
│   └── module_<id>_answers.md
├── active/
│   ├── draft_<module_id>.md
│   └── module_<module_id>_questions.md
├── compiled/
│   └── final_<module_id>.md
├── archive/
│   └── <timestamp>_draft_<module_id>.md
└── state_graph.yml
```

**Global Shared Artifacts (repo-level):**
```
.agents/schemas/personas/<persona_id>.md
.agents/schemas/templates/<template_id>.md
```

### 5.5 Dependencies
- Python 3.x (stdlib only: `yaml`, `os`, `sys`, `shutil`, `subprocess`, `datetime`, `pathlib`)
- `pyyaml` (already confirmed installed)
- Claude Code (slash command runtime)
- No external APIs, databases, or cloud services

---

## 6. Negative Constraints (The "Do NOTs")

- **DO NOT** use an LLM to decide routing or next-step logic — all control flow is deterministic Python.
- **DO NOT** introduce any database (SQLite, PostgreSQL, Redis, etc.) — YAML is the sole state store.
- **DO NOT** ingest audio files or integrate with any STT service.
- **DO NOT** auto-retry a failed LLM skill — fail loudly and halt.
- **DO NOT** write to the `archive/` directory from any skill or agent — only `archive_manager.py` may do this.
- **DO NOT** allow LLMs to read from `archive/` — it is write-only for humans and the archive script.
- **DO NOT** promote any AI-generated output to `tests/fixtures/` automatically — human approval is required.
- **DO NOT** build multi-user or team collaboration features.
- **DO NOT** expose any web API or server interface.

---

## 7. Risks & Mitigation

- **Risk 1**: State graph drift — the YAML goes out of sync after a crash or manual file edit.
  → **Mitigation**: `audit_state.py` reconciles YAML against filesystem. Operator runs it to recover.

- **Risk 2**: Persona fan-in produces duplicate or contradictory questions, confusing the inventor.
  → **Mitigation**: Questions are not auto-deduplicated (human reviews the full list per scope). The `/interview` pacing agent can be extended in a future iteration to flag potential duplicates.

- **Risk 3**: Integration Agent re-introduces hallucinations from the adversarial Q&A phase.
  → **Mitigation**: All integrated outputs route to `tests/candidate_outputs/` for mandatory human review before any downstream use.

- **Risk 4**: A job workspace is initialized with the wrong template or persona, producing a corrupt draft.
  → **Mitigation**: `init_workspace.py` validates that referenced template and persona files exist before creating the workspace. Fails loudly if not.

- **Risk 5**: The `/forge_persona --update` flow silently overwrites a persona used by active jobs.
  → **Mitigation**: The update skill checks `state_graph.yml` files (across all known workspaces or via a registry) and warns the operator if the persona is referenced by an in-progress job.

---

## 8. Success Metrics

- A complete document (all modules `integrated`) can be produced end-to-end without manual intervention beyond the `/interview` Q&A step.
- The Python CLI accurately reflects `state_graph.yml` status in every run with zero false-positive state advances.
- A new document type can be onboarded by a new operator in under 30 minutes using `/forge_persona` and a template file, with no code changes required.
- All AI-generated outputs are traceable to their source transcript and persona via the state graph.
- Zero instances of an LLM making a routing decision — all control flow is verifiably deterministic.
