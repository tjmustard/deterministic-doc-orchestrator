# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning: `0.0.x` = pre-SuperPRD implementation increments. `0.1.0` = first complete SuperPRD fulfilled.

---

## [Unreleased]

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
