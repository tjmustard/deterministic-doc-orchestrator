# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning: `0.0.x` = pre-SuperPRD implementation increments. `0.1.0` = first complete SuperPRD fulfilled.

---

## [Unreleased]

---

## [0.0.10] - 2026-03-15

### Added
- **`tests/integration/test_state_graph_schema.py`** — 9 deterministic tests covering all MiniPRD_StateGraph §5 scenarios: `load_state()` missing file exits with code 1 and prints `"State graph not found"`; invalid YAML exits with code 1; `save_state()` leaves no stale `.tmp` file after a clean write; save/load roundtrip preserves data faithfully; `set_module_status()` raises `ValueError` for any status outside `VALID_STATUSES`; accepts every valid status; `get_module()` raises `KeyError` containing the missing module ID.
- **`tests/integration/test_archive_manager.py`** — 5 deterministic tests covering all MiniPRD_ArchiveManager §5 scenarios: `archive_draft()` moves the source file and removes it from `active/`; two rapid sequential calls produce distinct filenames (microsecond collision prevention); missing source file prints `INFO` and returns without exception and without creating `archive/`; archived filename matches `^\d{8}_\d{6}_\d{6}_draft_\w+\.md$`.
- **`tests/integration/test_audit_state.py`** — 10 deterministic tests covering all MiniPRD_AuditState §5 scenarios: Rule 1 (compiled exists) forces status to `integrated` and persists to disk; Rule 2 (draft missing) reverts status to `pending_extraction` but does not revert when draft is present; Rule 3 (failed module) emits `AUDIT ALERT` and leaves status unchanged; Rule 4 (stale lockfile) emits `AUDIT ALERT` and does not delete the file; Rule 5 (consistent workspace) returns empty changes/alerts and `print_summary()` prints "consistent".
- **`tests/integration/test_orchestrator.py`** — 17 deterministic tests covering all MiniPRD_Orchestrator §5 scenarios: existing lockfile aborts with non-zero exit and error message, does not delete the pre-existing lock; pre-flight aborts on missing template file; pre-flight aborts on symlink in `active/` or `compiled/`; `--reset` sets module to `pending_integration`, archives compiled file, and cleans up lockfile; skill failure sets module status to `failed`, exits 1, and cleans up lockfile. Plus unit tests for `acquire_lock()`, `release_lock()`, and `execute_skill()`.

### Changed
- **Terminology purge — document-type agnosticism** — removed all uses of "patent", "invention", "legal brief", and "legal" from every file outside `docs/`. These references were context-poisoning LLM skill steps and biasing pipeline output toward specific domains. Affected files: `state_graph_schema.py`, `redteam.py`, `README.md`, all test fixtures, `spec/compiled/SuperPRD.md`, `spec/compiled/architecture.yml`, `spec/archive/` MiniPRDs, `.agents/memory/productContext.md`, `.agents/skills/forge_persona/SKILL.md`, `.agents/skills/template-architect/SKILL.md`. Replacements: `"patent_examiner_adversary"` → `"document_examiner_adversary"`, `"invention_disclosure"` → `"document"`, `"Legal Counsel"` → `"Critic"`, example document lists now read `PRDs, design docs, technical specs`.
- **`README.md`** — added document-type agnosticism callout; updated Quick Start example to use generic `my_document` / `document_examiner` identifiers.
- **`.agents/memory/systemPatterns.md`** — added "Document-Type Agnosticism" section codifying the prohibition on domain-specific terminology in pipeline code, tests, and skills.
- **`.agents/memory/activeContext.md`** — updated to reflect full test coverage and complete MiniPRD status table.
- **`.agents/memory/productContext.md`** — updated goals and operator persona description to remove domain-specific framing.

---

## [0.0.9] - 2026-03-15

### Added
- **`/forge_persona`** — formally audited and archived `MiniPRD_ForgePersona`. All pipeline MiniPRDs from the SuperPRD are now complete. The skill (SKILL.md + `.claude/commands/forge_persona.md`) was scaffolded at v0.0.3; this release closes the audit loop: 3-batch CREATE interview, anti-overwrite check, operator CONFIRM gate, versioned frontmatter, `workspace_registry.yml` active-job warning on `--update`, timestamped changelog append, diff summary on save.

---

## [0.0.8] - 2026-03-15

### Added
- **`/template-architect`** — new slash command skill backed by `.agents/skills/template-architect/SKILL.md`. Conducts a paced 3-batch guided interview (max 2 questions per turn) to define a new document type template from scratch. Synthesizes interview answers into a structured Markdown template with a `#` title, `**Agent Instruction:**` block, `##` sections, bold field names, `[Insert from transcript]` placeholders, optional field markers, and a `## Common Failure Modes` guardrail section. Validates the generated template inline (checks for `##` section heading and `[Insert from transcript]` placeholder, matching `validate_template()` in `init_workspace.py`); re-enters operator review on failure. Anti-overwrite check prompts `CONFIRM` before overwriting an existing template ID. Saves to `.agents/schemas/templates/<template_id>.md` after operator `CONFIRM` and validation pass. Prints save path and `state_graph.yml` reference instructions on completion.
- **`.claude/commands/template-architect.md`** — Claude Code command bridge delegating to `.agents/skills/template-architect/SKILL.md`.

---

## [0.0.7] - 2026-03-15

### Added
- **`promote.py`** — Python CLI backing the `/promote` pipeline skill. Loads `state_graph.yml` via `load_state()`; resolves existing candidate output files (`draft_<id>.md`, `module_<id>_questions.md`, `final_<id>.md`) from `tests/candidate_outputs/` in pipeline order, skipping absent slots. For each present file: prints filename + full contents, prompts operator for `APPROVE` or `REJECT <reason>`. On `APPROVE`: `shutil.move()` to `tests/fixtures/`, sets the corresponding `candidate_outputs` flag (`draft_approved` / `questions_approved` / `compiled_approved`) to `true`, saves state atomically. On `REJECT`: appends `{"file", "reason", "timestamp": ISO8601}` to `module.rejections` list, resets status to `pending_integration`, saves state atomically, halts — remaining files are not reviewed. On full loop completion: sets status to `integrated`, calls `archive_manager.archive_draft()`, prints confirmation. If no candidate files are present, prints informative message and exits 0 with no state change. Supports `--repo-root` (hidden flag, test path isolation). Injectable `input_fn` parameter enables deterministic testing without subprocess.
- **`tests/integration/test_promote.py`** — 8 tests: full APPROVE moves all three files to `tests/fixtures/`, sets all approval flags `true`, and advances status to `integrated`; APPROVE-then-REJECT halts after rejection, leaves final file in `candidate_outputs/`, logs rejection reason + timestamp, resets status to `pending_integration`; no candidate files exits cleanly with informative message; pre-existing `tests/fixtures/` file is untouched after partial approval. Plus unit tests for `resolve_pending_candidates()` (existence filter, pipeline order), `_ensure_candidate_outputs()` (initialises absent sub-dict), and `_append_rejection()` (initialises absent list).

---

## [0.0.6] - 2026-03-15

### Added
- **`integrate.py`** — Python CLI backing the `/integrate` pipeline skill. Loads `state_graph.yml` via `load_state()`; resolves `active/draft_<module_id>.md` (aborts exit 1 if missing); validates `transcripts/module_<module_id>_answers.md` is non-empty (aborts exit 1 if absent or empty: `ERROR: No answers transcript found for module '<id>'. Run /interview first.`); resolves `associated_files.template`. Constructs a Resolution Agent prompt (system instruction + template schema + baseline draft labeled `BASELINE DRAFT:` + answers transcript labeled `ADVERSARIAL Q&A ANSWERS:`) and invokes `claude -p`. Writes integrated content to `tests/candidate_outputs/final_<module_id>.md` only — never to `compiled/`. Does not call `save_state()` or advance module status; that is `/promote`'s responsibility. Prints instruction to run `/promote <module_id>`. Supports `--mock-integration` (hidden flag, returns draft prefixed with `<!-- MOCK INTEGRATED -->` for deterministic testing) and `--repo-root` (test path isolation).
- **`tests/integration/test_integrate.py`** — 9 tests (1 novel skipped): empty answers transcript aborts with exit 1 and error message; missing answers transcript aborts; `compiled/final_<module_id>.md` does NOT exist after `/integrate` (candidate routing enforced); `state_graph.yml` module status unchanged after `/integrate` (status stays `pending_integration`); `/promote` instruction appears in stdout. Plus unit tests for `validate_answers()` and `_mock_integration()`.

---

## [0.0.5] - 2026-03-15

### Added
- **`redteam.py`** — Python CLI backing the `/redteam` pipeline skill. Loads `state_graph.yml`, resolves `active/draft_<module_id>.md` (aborts exit 1 if missing), and resolves the persona file from `personas_snapshot/<id>.md` with fallback to `.agents/schemas/personas/<id>.md`. Reads `active/module_<module_id>_questions.md` (if exists) and counts numbered lines (`^\d+\.`) to calculate remaining capacity against `module.max_questions` (default 50). If `remaining_capacity <= 0`, prints a cap-reached WARNING and exits 0 without appending. Otherwise constructs a red-team prompt (persona content + full draft + generation instruction referencing `[NEEDS_CLARIFICATION]`) and invokes `claude -p`. Parses numbered lines from LLM output; truncates with WARNING if count exceeds remaining capacity. Appends `\n## Persona: <id>\n<questions>\n` to the questionnaire. Copies the full questionnaire to `tests/candidate_outputs/`. Sets `adversarial_state.status` to `interview_in_progress` atomically via `save_state()`. Prints persona ID, questions added, total count, and remaining capacity. Supports `--mock-redteam` (hidden flag, always returns 5 deterministic questions for test coverage of truncation path) and `--repo-root` (test path isolation).
- **`tests/integration/test_redteam.py`** — 10 tests (1 novel skipped): cap-reached exits 0 with WARNING and no append; truncation warning when generated count exceeds remaining capacity; `[NEEDS_CLARIFICATION]` marker in draft surfaces in questionnaire output; plus unit tests for `count_existing_questions()`, `parse_generated_questions()`, `resolve_persona_path()` (snapshot preference, global fallback, missing persona exit 1).

---

## [0.0.4] - 2026-03-15

### Added
- `interview.py` — Python CLI backing the `/interview` pipeline skill. Loads `state_graph.yml`, reads `adversarial_state.last_answered_index` (default `0`), parses `active/module_<id>_questions.md` for `^\d+\.` numbered questions. Offers a pre-session DONE gate before presenting any questions; presents unanswered questions in batches of 3; after every 3rd answer (when more remain) prompts DONE/continue. Atomically saves `last_answered_index` to `state_graph.yml` after each answer. On full completion, validates the answers file grew then sets module status to `pending_integration` and `adversarial_state.status` to `ready_for_integration`. Never modifies the questionnaire file. Supports injectable `input_fn` for deterministic testing.
- `tests/integration/test_interview.py` — 9 tests covering: answer 3 + DONE (index=3, status unchanged), resume skips answered questions, fully-answered early exit, complete all 9 advances status, DONE-immediately guard (no state change). Plus unit tests for `parse_questionnaire()` and `append_answer()`.

---

## [0.0.3] - 2026-03-15

### Added
- `extract.py` — Python CLI that backs the `/extract` pipeline skill. Validates the workspace transcript, builds the Technical Scraper extraction prompt, invokes `claude -p` as a subprocess, counts `[NEEDS_CLARIFICATION]` gaps (warns but does not halt), writes `active/draft_<module_id>.md`, copies to `tests/candidate_outputs/`, and atomically advances `state_graph.yml` to `extracted`. Exits code 1 without touching state if the transcript is empty or the LLM subprocess fails. Supports `--mock-extraction` (hidden flag, replaces LLM call with a deterministic stub for tests) and `--repo-root` (test path isolation).
- `tests/integration/test_extract.py` — 8 tests covering: empty transcript abort (exit 1, state unchanged), missing transcript abort, partial-transcript gap warning + state advancement, candidate output routing, and unit tests for `count_gaps()` and `validate_transcript()`. Live-LLM Test 1 is `pytest.mark.skip`'d with manual-run instructions.

---

## [0.0.2] - 2026-03-15

### Added
- `audit_state.py` — 4-rule filesystem reconciler: force-integrates modules with orphaned compiled files, reverts draft-missing modules to `pending_extraction`, alerts on `failed` modules and stale lockfiles; supports `associated_files` path overrides in `state_graph.yml`
- Pipeline skills: `/extract`, `/forge_persona`, `/integrate`, `/interview`, `/promote` — full operator-facing slash commands covering the extract → red-team → interview → integrate → promote lifecycle
- `/hyper-redteam` — framework-level PRD stress-test (OWASP, scalability, logic analysis of `spec/active/Draft_PRD.md`); split out from the old `/redteam` to separate pipeline from framework-level concerns
- `.agents/schemas/personas/` and `.agents/schemas/templates/` — schema directories now tracked in the repo; `init_workspace.py` and `forge_persona` read/write here

### Changed
- `/redteam` rewritten as a pipeline skill: workspace-scoped, persona-driven, 50-question cap per module, persona snapshot resolution, atomic questionnaire append; old framework-level PRD analysis moved to `/hyper-redteam`
- `init_workspace.py` guard logic: non-workspace directories (no `state_graph.yml`) are now always rejected regardless of `--force`, preventing blast-radius on unrelated directories; error message now distinguishes "already initialized" from "foreign directory"; adds suppressed `--repo-root` flag for test isolation

### Removed
- `docs/MasterSOP.md`, `docs/Troubleshooting.md`, `docs/Tutorial.md`, `docs/Whitepaper.md` — replaced by skills (`/sop`, `/troubleshooting`, `/tutorial`) and the consolidated docs below
- Root-level `Agentic-Orchestrator.md`, `Agentic-Orchestrator-Article.md`, `Core-Structureal-Blueprint.md` — moved to `docs/`

---

## [0.0.1] - 2026-03-15

### Added
- `state_graph_schema.py` — canonical state I/O module: `load_state()`, `save_state()` (atomic via `os.replace()`), `get_module()`, `set_module_status()`, `VALID_STATUSES`
- `archive_manager.py` — `archive_draft()` and `archive_compiled()` with microsecond-precision timestamps to prevent collision; CLI entrypoint
- `orchestrator.py` — YAML-driven state machine: lockfile, pre-flight validation (missing files, symlink scan, confidence score warning), persona snapshot, full module lifecycle loop, `--reset` mode
- `README.md` — full usage guide: installation, CLI reference, slash commands, workspace structure, uninstall instructions
- `CHANGELOG.md` — this file
