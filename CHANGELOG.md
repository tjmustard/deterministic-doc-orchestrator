# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning: `0.0.x` = pre-SuperPRD implementation increments. `0.1.0` = first complete SuperPRD fulfilled.

---

## [Unreleased]

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
