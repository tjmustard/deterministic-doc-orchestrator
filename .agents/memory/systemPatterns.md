
# System Patterns

## Purpose
This file documents the "How" — architectural decisions, design patterns, tech stack choices, and project conventions.

## Architecture

A deterministic state machine (`orchestrator.py`) drives a sequential pipeline of LLM skill subprocesses. LLM calls are strictly isolated to individual skill steps; all routing, file I/O, and status transitions are handled by deterministic Python code. State is the single source of truth: `state_graph.yml` in each workspace.

```
Transcript → extract → redteam × N → interview → integrate → promote → Approved Doc
```

Each step is a standalone Python CLI that reads/writes `state_graph.yml` via `state_graph_schema.py` and exits with a clear code. The orchestrator reads exit codes and current state — it never interprets LLM output.

## Tech Stack

- **Runtime:** Python 3.12
- **State format:** YAML (`pyyaml`) — `state_graph.yml` per workspace
- **LLM calls:** `claude -p <prompt>` subprocess (Claude CLI)
- **Testing:** pytest with `tmp_path` isolation; subprocess-based integration tests; injectable function parameters for unit testing without subprocess
- **No web framework, no database, no daemon** — pure CLI tools

## Design Patterns

- **Atomic state writes:** All `state_graph.yml` writes use `write to .tmp → os.replace()` via `save_state()`. A crash mid-write never corrupts the live file.
- **Snapshot-first persona resolution:** `redteam.py` checks `personas_snapshot/<id>.md` before falling back to `.agents/schemas/personas/<id>.md`. Live mutations to the global library have no effect on running jobs.
- **Injectable function parameters:** LLM-calling functions (`_call_claude`, `_mock_generation`, etc.) are injectable as `Callable` parameters so tests can inject deterministic stubs without subprocess. The `--mock-*` CLI flags select the stub at runtime.
- **Candidate output routing:** Every AI-generated artifact is written to `tests/candidate_outputs/` before human review. Nothing goes to `tests/fixtures/` without explicit `/promote` approval.
- **Hidden internal flags:** `--mock-*` and `--repo-root` are suppressed via `argparse.SUPPRESS` — they exist for test isolation only and are never documented to operators.
- **Pure helper separation:** All parseable, testable logic lives in importable module-level functions (e.g. `count_existing_questions()`, `parse_questionnaire()`). `main()` only handles CLI wiring.

- **SKILL.md-based skills:** Library-management skills (`/template-architect`, `/forge_persona`) are implemented as agent instruction files (`.agents/skills/<name>/SKILL.md`) rather than Python CLIs. They conduct interactive guided interviews, apply inline validation logic, and write directly to the schema library. No integration test file is created for these — the human review gate (`CONFIRM` before save) is the test boundary.

## Conventions

- **File naming:** skill scripts at repo root (`extract.py`, `redteam.py`, `interview.py`, `integrate.py`). Tests at `tests/integration/test_<skill>.py`.
- **Status progression:** `pending_extraction → extracted → pending_interview → pending_integration → integrated`. Set via `set_module_status()` + `save_state()`.
- **Error exits:** All fatal errors print to `sys.stderr`, exit code 1. Graceful skips (e.g. cap reached) print to `stdout`, exit code 0.
- **Question counting:** Numbered lines matching `^\d+\.` across the full questionnaire file — regardless of persona section headers.
- **Questionnaire append format:** `\n## Persona: <id>\n<numbered_list>\n` — one block per persona call; never rewrite or deduplicate.
