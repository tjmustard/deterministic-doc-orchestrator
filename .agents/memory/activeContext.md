
# Active Context
## Purpose
This file updates dynamically after *every task completion*. It captures the "Now" of the project: what was just done, what is currently being worked on, and any immediate blockers or open questions.

## Usage
- Agent writes here after completing a task.
- Agent reads this *first* to understand where to pick up.

## Current Sprint Goal
**DDO v0.0.1 — COMPLETE ✅ (2026-06-29)**

All 6 MiniPRDs implemented, audited, and archived. Full suite **78 passed / 0 skipped**, ruff clean. Documentation updated.

## v0.0.1 Implementation Summary

### Core Package (ddo/)
- `ddo/build.py` — PEP 723 hermetic orchestrator; `ddo/build.py.lock` enforced by `uv run --locked`
- `ddo/validation.py` — importable gate: meta contract → evidence integrity → sentinel scan
- `ddo/paths.py` — `sanitize_slug`, `document_dir`, `assert_within_documents` / `PathContainmentError`
- `ddo/ingest.py` — atomic write, `OverwriteError`, `fabrication_tripwire` (advisory)
- `ddo/schemas/` — `prd.yaml`, `scientific_report.yaml` (canonical minimal contracts)
- `ddo/templates/` — Typst + Jinja2 for prd/scientific_report × pdf/html/md
- `ddo/fonts/` — bundled DejaVu (hermetic PDF; no system Typst required)
- `ddo/personas/` — `product_critic.md`, `scientific_reviewer.md`
- `ddo/skills/` — `ddo-ingest.md`, `ddo-render.md`

### Tests & Scripts
- `tests/unit/` — 25+ unit tests (validation, paths, ingest, personas, fixture guard)
- `tests/integration/` — M1–M4 determinism + M5 ingest contract
- `tests/fixtures/` — 7 human-promoted golden baselines (DDO_FIXTURE_SIGNOFF=1 required to commit)
- `scripts/fixture_signoff_guard.py` — pre-commit/CI guard for fixture promotion

### Audit Findings (v0.0.1)
- **5 of 6 MiniPRDs PASSED** cleanly on first audit
- **SchemaTemplateMigration FAILED** → found real XSS bug: `select_autoescape(enabled_extensions=("html",))` silently disabled for `.jinja2` templates → **FIXED** (`autoescape=(fmt == "html")`)
- **BuildCore** false-positive on `uv.lock` (correct lock is `ddo/build.py.lock` per PEP 723)
- Golden fixture `prd_example.html` regenerated: `& User Personas` → `&amp; User Personas` (now valid HTML)
- All 6 MiniPRDs archived to `spec/archive/*_AUDITED.md`
- `spec/compiled/` now contains only `architecture.yml` (24 nodes, all `status: clean`) and `SuperPRD.md`

### Documentation Updated (v0.0.1)
- `pyproject.toml` — version `0.0.0` → `0.0.1`
- `CHANGELOG.md` — `## [0.0.1] - 2026-06-29` block added
- `README.md` — badge, prerequisites, directory structure, schema contract, roadmap all updated
- `.agents/memory/productContext.md` — DDO-specific content written
- `.agents/memory/systemPatterns.md` — DDO-specific patterns written

## v0.0.1 Post-Implementation Additions

### Tutorials (2026-06-29)
- `tutorials/ddo-v001-prd-workflow/tutorial.md` — 9-section PRD YAML workflow tutorial
- `tutorials/ddo-v001-prd-workflow/input_files/prd_example.yaml` — gate-passing example input
- `tutorials/ddo-v001-prd-workflow/output_files/` — pre-rendered HTML + MD examples
- `tutorials/ddo-v001-prd-workflow/code_samples/render_commands.sh` — render commands reference

### Process Documents (2026-06-29)
- `spec/process/process_20260629_101449_session.md` — v0.0.1 session retrospective

### Documentation Updated
- `CHANGELOG.md` — tutorial + process doc entries appended to [0.0.1]
- `README.md` — `tutorials/` entry in directory structure; Roadmap tutorial items
- `tutorials/ddo-v001-prd-workflow/tutorial.md` — fixed test count 77→78

## Next Steps (v0.0.2+)
- Red Team phase (`ddo-red-team` skill)
- Interview phase (`ddo-interview` skill)
- Refine phase (`ddo-refine` skill)
- Scientific report tutorial (`tutorials/ddo-v001-scientific-report-workflow/`)
- Commit v0.0.1 backbone (with `DDO_FIXTURE_SIGNOFF=1` for `tests/fixtures/` changes)

## Files to Commit (v0.0.1)
Fixture changes require env var:
```
DDO_FIXTURE_SIGNOFF=1 git add tests/fixtures/ && git commit ...
```
Remaining changes (build.py autoescape fix, pyproject.toml version bump, CHANGELOG, README, tutorials/, spec/process/) can commit normally.
