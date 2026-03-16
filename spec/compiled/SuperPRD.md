# SuperPRD: Deterministic Document Orchestrator

## Metadata
- **Project Name**: Deterministic Document Orchestrator
- **Version**: 1.1.0
- **Status**: Approved
- **Owner**: Resolution Agent

---

## 1. Introduction & Goals

### 1.1 Problem Statement
Manual creation of complex, high-stakes documents (e.g., PRDs, design docs, technical specs) is slow, inconsistent, and error-prone. LLMs fail when given monolithic context — they hallucinate, lose nuance, and flatten technical precision into generic prose.

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
- Uses slash commands to configure document types, templates, and personas.
- Uses the Python CLI to run the automated pipeline.
- Performs final human review and approval of all AI-generated outputs via the `/promote` skill.

---

## 2. Confidence Mandate
**Confidence Score**: 9/10
**Status**: All Red Team blockers resolved.

---

## 3. Scope

### 3.1 In-Scope
- Per-job isolated workspace directory with its own `state_graph.yml`
- YAML-driven deterministic state machine (`orchestrator.py`)
- Plain Markdown/text-only inputs (no audio, no STT)
- Modular document sections as first-class units (modules)
- Optional `skip_adversarial: true` flag per module to bypass red-team and interview phases
- Multiple simultaneous adversarial personas per module, contributing to a single master questionnaire (cap: 50 questions total per module)
- Global workspace registry at `.agents/workspace_registry.yml`
- Persona snapshot at pipeline start into `<workspace>/personas_snapshot/`
- `.agentignore` enforcing `**/archive/**` read restriction
- **Skills (Claude Code slash commands):**
  - `/template-architect` — guides power users in creating a structured Markdown template file for a new document type
  - `/forge_persona` — creates a new adversarial persona via guided interview; validates against active jobs via workspace registry
  - `/forge_persona --update <persona_id>` — modifies an existing persona; increments version, appends changelog entry
  - `/extract [module_id]` — maps transcript to template schema; writes `[NEEDS_CLARIFICATION]` for missing data; routes output to `tests/candidate_outputs/`
  - `/redteam [module_id] [persona_id]` — appends adversarial questions to master questionnaire; truncates at 50-question total cap; routes output to `tests/candidate_outputs/`
  - `/interview [module_id]` — paces Q&A 3 questions at a time; operator types `DONE` to pause; re-run resumes from last answered question via `adversarial_state.last_answered_index`
  - `/integrate [module_id]` — synthesizes final compiled output from draft + Q&A answers; routes to `tests/candidate_outputs/`
  - `/promote [module_id]` — presents candidate outputs for operator review; `APPROVE` moves to `tests/fixtures/` and logs to `state_graph.yml`; `REJECT` logs reason and flags module for re-run
- **Python scripts:**
  - `init_workspace.py` — scaffolds workspace directory; validates template/persona files exist; runs `validate_template()`; appends to workspace registry; idempotent with `--force` override
  - `orchestrator.py` — state machine loop; atomic YAML writes via `os.replace()`; lockfile at startup; pre-flight validation of all referenced files; symlink check in `active/`, `transcripts/`, `compiled/`; soft confidence warning if score < 7; `--reset <module_id>` flag to archive compiled output and revert to `pending_integration`
  - `audit_state.py` — reconciles `state_graph.yml` against filesystem; detects and reports `failed` modules; prints human-readable diff
  - `archive_manager.py` — timestamps with microsecond precision (`%Y%m%d_%H%M%S_%f`); moves files from `active/` to `archive/`

### 3.2 Out-of-Scope
- Audio file ingestion or Speech-to-Text integration
- Multi-user / team collaboration (single operator only)
- External database (SQLite, PostgreSQL, Redis) — YAML is the database
- Approval workflow integration (approval happens via `/promote` skill, not external systems)
- CI/CD pipeline triggering
- Web UI or API server
- LLM-driven graph traversal (all routing is deterministic Python)
- Automatic promotion of AI outputs to `tests/fixtures/` without human approval

---

## 4. User Stories (Atomic)

| ID | User Story | Acceptance Criteria | Priority |
| :--- | :--- | :--- | :--- |
| US-001 | As an operator, I want to initialize a new job workspace so that each document generation run is fully isolated. | 1. `init_workspace.py <job_name>` creates full directory structure with empty `state_graph.yml`.<br>2. Validates all referenced template/persona files exist before creating workspace.<br>3. If workspace exists with non-empty `state_graph.yml`, aborts with error. `--force` wipes and recreates.<br>4. Appends workspace path to `.agents/workspace_registry.yml`. | High |
| US-002 | As a power user, I want a guided skill to create a Markdown template for a new document type so that the pipeline knows how to structure extracted content. | 1. `/template-architect` interviews the operator about document structure and required sections.<br>2. Outputs a validated template `.md` file to `.agents/schemas/templates/`.<br>3. Template passes `validate_template()` checks (minimum: one `##` section, `[Insert from transcript]` placeholders). | High |
| US-003 | As an operator, I want to define a new adversarial persona using a guided skill so that I don't need to hand-write prompt files. | 1. `/forge_persona` asks targeted questions about document type and adversarial angle.<br>2. Outputs a validated `.md` persona file to `.agents/schemas/personas/` with `version: 1` and empty `changelog`.<br>3. Persona is immediately selectable by ID in `state_graph.yml`. | High |
| US-004 | As an operator, I want to update an existing persona so that I can tune its behavior without recreating it from scratch. | 1. `/forge_persona --update <persona_id>` loads the existing file and presents the current definition.<br>2. Checks workspace registry for active jobs using this persona; warns operator if found.<br>3. Saves with incremented version number and appended changelog entry. | High |
| US-005 | As an operator, I want to extract a module draft from a transcript so that the AI maps raw notes to the document schema. | 1. `/extract [module_id]` reads `transcripts/raw_input.md` and the module template.<br>2. Outputs `active/draft_[module_id].md` with `[NEEDS_CLARIFICATION]` for missing data.<br>3. Routes output to `tests/candidate_outputs/`.<br>4. `state_graph.yml` status advances to `extracted`. | High |
| US-006 | As an operator, I want multiple adversarial personas to interrogate a module simultaneously so that the draft is stress-tested from multiple angles. | 1. `/redteam [module_id] [persona_id]` appends questions to a single master questionnaire.<br>2. Total questions across all personas capped at 50; truncates with warning if exceeded.<br>3. Routes questionnaire to `tests/candidate_outputs/`.<br>4. `[NEEDS_CLARIFICATION]` markers in the draft are valid red-team targets. | High |
| US-007 | As an operator, I want to be interviewed 3 questions at a time and resume across sessions so that I am not overwhelmed. | 1. `/interview [module_id]` reads master questionnaire and presents 3 unanswered questions per turn.<br>2. Operator types `DONE` to end session; `state_graph.yml` saves `last_answered_index`.<br>3. Re-running the skill resumes from the next unanswered question.<br>4. Answers appended to `transcripts/module_[module_id]_answers.md`. | High |
| US-008 | As an operator, I want the integration agent to synthesize the final document so that the output is complete and defensible. | 1. `/integrate [module_id]` reads draft and Q&A answers transcript.<br>2. Outputs `compiled/final_[module_id].md`.<br>3. Routes to `tests/candidate_outputs/`. | High |
| US-009 | As an operator, I want to review and approve AI-generated outputs so that hallucinations don't silently become ground truth. | 1. `/promote [module_id]` presents each file in `tests/candidate_outputs/` for the module.<br>2. `APPROVE` moves file to `tests/fixtures/`, logs event to `state_graph.yml`.<br>3. `REJECT` logs reason and flags module for re-run. | High |
| US-010 | As an operator, I want the Python CLI to automate the pipeline so that I don't manually invoke each skill step. | 1. `python orchestrator.py` reads `state_graph.yml` and calls the correct skill per module status.<br>2. Acquires lockfile at startup; aborts if lockfile exists.<br>3. Performs pre-flight: validates all referenced persona/template files exist; checks for symlinks; warns if confidence < 7.<br>4. Pipeline halts gracefully at `pending_interview` for human input.<br>5. On subprocess failure, writes `status: failed` to YAML and halts with error. No auto-retry. | High |
| US-011 | As an operator, I want to reset a failed or rejected module so that I can re-run integration without manual YAML editing. | 1. `python orchestrator.py --reset <module_id>` moves compiled output to `archive/` with microsecond timestamp.<br>2. Resets module status to `pending_integration` in `state_graph.yml`.<br>3. Prints confirmation and next step. | High |
| US-012 | As an operator, I want the state graph to be reconcilable against the filesystem so that a crash or manual file move doesn't corrupt the pipeline. | 1. `python audit_state.py` scans filesystem and updates `state_graph.yml` statuses.<br>2. Detects and reports `failed` modules.<br>3. Prints human-readable diff of any changes made. | Medium |

---

## 5. Technical Specifications (The Blueprint)

### 5.1 Architecture & Resolved Trade-offs

**Data Flow:**
```
[Human: raw transcript (Markdown/text)]
        ↓
[/extract] → active/draft_[module_id].md → tests/candidate_outputs/
        ↓
[/redteam × N personas, cap 50 total] → active/module_[module_id]_questions.md → tests/candidate_outputs/
        ↓
[/interview, resumable, DONE to pause] → transcripts/module_[module_id]_answers.md
        ↓
[/integrate] → compiled/final_[module_id].md → tests/candidate_outputs/
        ↓
[/promote] → tests/fixtures/ (human approval gate)
```

**Module State Machine:**
```
pending_extraction → extracted → pending_interview → pending_integration → integrated
                                                                        ↘ failed (on subprocess error)
                                       ↑ (--reset moves back from integrated)
```

**Modules with `skip_adversarial: true`:**
```
pending_extraction → extracted → pending_integration → integrated
```

### 5.2 Resolved Trade-offs Log

| Issue | Options | Resolution |
|---|---|---|
| LLM routing vs. deterministic routing | Agent decides next step vs. Python reads YAML | Deterministic Python only. LLMs never traverse the graph. |
| Single workspace vs. per-job isolation | Shared global workspace vs. isolated directories | Per-job isolated workspace with its own `state_graph.yml`. |
| Persona scope (ephemeral vs. reusable) | Job-scoped vs. global library | Global versioned library + per-run snapshot for isolation. |
| Atomic YAML writes (C-1) | Direct write vs. write-then-rename | `os.replace()` atomic write pattern. |
| File locking (C-2) | Lockfile vs. accept risk | Lockfile at `<workspace>/.orchestrator.lock`. |
| Archive collision (C-3) | Second-precision vs. microsecond | Microsecond timestamps (`%Y%m%d_%H%M%S_%f`). |
| Incomplete transcript (C-4) | Hard halt vs. continue with markers | Continue with `[NEEDS_CLARIFICATION]`; pre-flight warns operator; red-team interrogates gaps. |
| Failed state (C-5) | No failed state vs. explicit terminal state | `failed` status added; `--reset` flag to recover. |
| Duplicate workspace init (C-6) | Abort vs. abort with `--force` | Abort by default; `--force` wipes and recreates. |
| Pre-flight validation (C-7) | Run-time check vs. init-time only | Both: `init_workspace.py` and `orchestrator.py` pre-flight. |
| Interview session end (C-8) | Keyword vs. exhaustion only | `DONE` to pause; `last_answered_index` enables resume. |
| template-architect (C-9) | Defer vs. promote | Promoted to full in-scope with MiniPRD. |
| Workspace registry (C-10) | Registry file vs. no registry | `.agents/workspace_registry.yml` appended by `init_workspace.py`. |
| Integration rejection (C-11) | Manual YAML vs. `--reset` flag | `orchestrator.py --reset <module_id>` resets to `pending_integration`. |
| Persona mutation isolation (C-12) | Accept risk vs. snapshot | Persona snapshot into `<workspace>/personas_snapshot/` at pipeline start. |
| Archive read restriction (C-13) | Document-only vs. `.agentignore` | `.agentignore` containing `**/archive/**`. |
| Phase skip (NFR-1) | Fixed pipeline vs. optional skip | `skip_adversarial: true` flag per module. |
| Question cap (NFR-2) | No cap vs. configurable cap | 50 questions total per module across all personas (default). |
| Template validation (NFR-3) | Trust operator vs. validate | `validate_template()` in `init_workspace.py`. |
| Confidence enforcement (NFR-4) | Hard block vs. soft warning | Soft warning; operator confirms to proceed if score < 7. |
| Symlink check (NFR-5) | Skip vs. pre-flight scan | Pre-flight symlink scan in `orchestrator.py`. |
| Candidate output promotion | Manual only vs. skill-assisted | `/promote` skill automates review and promotion to `tests/fixtures/`. |

### 5.3 System Graph Blast Radius
New nodes (greenfield):

| Node ID | Description |
|---|---|
| `orchestrator_core` | Python state machine, atomic YAML writes, lockfile, pre-flight validation |
| `workspace_init` | `init_workspace.py`: scaffolding, validation, registry append |
| `workspace_registry` | `.agents/workspace_registry.yml`: global job index |
| `persona_library` | `.agents/schemas/personas/`: versioned persona store |
| `persona_snapshot` | `<workspace>/personas_snapshot/`: run-time isolation copy |
| `template_library` | `.agents/schemas/templates/`: document type templates |
| `skill_template_architect` | `/template-architect`: guided template creation |
| `skill_forge_persona` | `/forge_persona`: persona create + update |
| `skill_extract` | `/extract`: transcript-to-draft mapping |
| `skill_redteam` | `/redteam`: multi-persona adversarial fan-in |
| `skill_interview` | `/interview`: resumable paced Q&A |
| `skill_integrate` | `/integrate`: final synthesis |
| `skill_promote` | `/promote`: candidate output review + promotion |
| `audit_state` | `audit_state.py`: YAML reconciliation |
| `archive_manager` | `archive_manager.py`: timestamped archival |
| `candidate_output_protocol` | `tests/candidate_outputs/` + `tests/fixtures/` review workflow |

### 5.4 Execution Checklist (MiniPRDs)
- [ ] `spec/compiled/MiniPRD_WorkspaceInit.md`
- [ ] `spec/compiled/MiniPRD_StateGraph.md`
- [ ] `spec/compiled/MiniPRD_Orchestrator.md`
- [ ] `spec/compiled/MiniPRD_TemplateArchitect.md`
- [ ] `spec/compiled/MiniPRD_ForgePersona.md`
- [ ] `spec/compiled/MiniPRD_Extract.md`
- [ ] `spec/compiled/MiniPRD_RedTeam.md`
- [ ] `spec/compiled/MiniPRD_Interview.md`
- [ ] `spec/compiled/MiniPRD_Integrate.md`
- [ ] `spec/compiled/MiniPRD_Promote.md`
- [ ] `spec/compiled/MiniPRD_AuditState.md`
- [ ] `spec/compiled/MiniPRD_ArchiveManager.md`

### 5.5 State Graph Schema (Canonical)

```yaml
document_meta:
  title: string
  type: string                    # e.g. "document", "prd"
  global_status: string           # "in_progress" | "completed"
  confidence_score: int           # 1-10; warns if < 7 at pipeline start

personas:
  - id: string
    version: int
    status: string                # "clean" | "dirty"
    associated_file: string       # .agents/schemas/personas/<id>.md
    changelog: [string]

inputs:
  - id: string
    status: string                # "clean"
    associated_file: string       # transcripts/raw_input.md

modules:
  - id: string
    status: string                # pending_extraction | extracted | pending_interview
                                  # | pending_integration | integrated | failed
    skip_adversarial: bool        # optional; default false
    max_questions: int            # optional; default 50 (total across all personas)
    associated_files:
      template: string
      draft: string
      compiled: string
    applied_personas: [string]    # list of persona IDs
    adversarial_state:
      status: string              # idle | interview_in_progress | ready_for_integration
      last_answered_index: int    # tracks resume point for /interview
      master_questionnaire: string
      answers_transcript: string
    candidate_outputs:
      draft_approved: bool
      questions_approved: bool
      compiled_approved: bool
```

### 5.6 Workspace Directory Structure

```
<job_name>/
├── .orchestrator.lock            # Created at pipeline start, deleted on exit
├── state_graph.yml               # Deterministic state — written atomically
├── personas_snapshot/            # Copied at pipeline start from global library
│   └── <persona_id>.md
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
.agentignore                              # Contains: **/archive/**
.agents/
├── workspace_registry.yml               # Appended by init_workspace.py
├── schemas/
│   ├── personas/<persona_id>.md         # Versioned persona files
│   └── templates/<template_id>.md      # Document type templates
└── scripts/
    ├── orchestrator.py
    ├── init_workspace.py
    ├── audit_state.py
    └── archive_manager.py
tests/
├── candidate_outputs/                   # AI-generated, awaiting human review
└── fixtures/                            # Human-approved ground truth
```

### 5.7 Dependencies
- Python 3.x (stdlib: `yaml`, `os`, `sys`, `shutil`, `subprocess`, `datetime`, `pathlib`, `fcntl` for lockfile)
- `pyyaml`
- Claude Code (slash command runtime)
- No external APIs, databases, or cloud services

---

## 6. Negative Constraints (The "Do NOTs")

- **DO NOT** use an LLM to decide routing or next-step logic — all control flow is deterministic Python.
- **DO NOT** introduce any database — YAML is the sole state store.
- **DO NOT** ingest audio files or integrate with any STT service.
- **DO NOT** auto-retry a failed LLM skill — write `failed` status and halt loudly.
- **DO NOT** write to `archive/` from any skill or agent — only `archive_manager.py` may do this.
- **DO NOT** allow LLMs to read from `archive/` — enforced by `.agentignore`.
- **DO NOT** promote any AI-generated output to `tests/fixtures/` automatically — `/promote` skill requires human `APPROVE` input.
- **DO NOT** write `state_graph.yml` non-atomically — always use `os.replace()` pattern.
- **DO NOT** start `orchestrator.py` if `.orchestrator.lock` exists.
- **DO NOT** build multi-user or team collaboration features.
- **DO NOT** expose any web API or server interface.

---

## 7. Risks & Mitigation

| Risk | Mitigation |
|---|---|
| State graph drift after crash | `audit_state.py` reconciles YAML vs. filesystem. Recommended pre-run step after any crash. |
| Persona fan-in produces 50+ questions | Hard cap enforced by `/redteam`; truncates with warning. |
| Integration Agent hallucinations propagate | All outputs route to `candidate_outputs/`; `/promote` requires explicit human `APPROVE`. |
| Wrong template/persona at init time | `init_workspace.py` validates all referenced files exist before creating workspace. |
| Persona updated mid-pipeline for active job | Persona snapshot copied at pipeline start; live mutations have no effect on running jobs. |
| Operator rejects integrated output | `orchestrator.py --reset <module_id>` safely resets to `pending_integration`. |
| Symlink bypasses filesystem firewall | Pre-flight symlink scan in `orchestrator.py` aborts if any found. |
| Concurrent `orchestrator.py` runs | Lockfile at `<workspace>/.orchestrator.lock` blocks second invocation. |
| YAML corruption on crash | Atomic write via `os.replace()` — partial writes never overwrite the live file. |

---

## 8. Success Metrics

1. A complete document requires operator interaction at exactly three touchpoints: (1) transcript preparation, (2) interview Q&A, (3) output approval via `/promote`. No additional manual steps required.
2. The Python CLI accurately reflects `state_graph.yml` status in every run with zero false-positive state advances — verified by deterministic tests in `tests/`.
3. Onboarding benchmark: given a new operator and a 500-word plain-text transcript, running `/forge_persona`, `/extract`, and `python orchestrator.py` completes all phases to `integrated` state.
4. All AI-generated outputs are traceable to their source transcript and persona via `state_graph.yml`.
5. Zero instances of an LLM making a routing decision — all control flow is verifiably deterministic Python.
