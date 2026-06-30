
# Active Context
## Purpose
This file updates dynamically after *every task completion*. It captures the "Now" of the project: what was just done, what is currently being worked on, and any immediate blockers or open questions.

## Usage
- Agent writes here after completing a task.
- Agent reads this *first* to understand where to pick up.

## Current Sprint Goal
**DDO v0.0.4 — COMPLETE ✅ (2026-06-30)**

Structured Persona Nomenclature fully implemented, audited, and released. 183 tests passing.

## v0.0.4 Implementation Summary

### New Files
- `ddo/skills/ddo-create-persona.md` — interactive paced Q&A skill for authoring new personas (AV-NN table format, HITL gated, cognitive overwrite guard, no ddo_core dependency)
- `spec/compiled/SuperPRD_v0.0.4_StructuredPersonaNomenclature.md` — specification for this release

### Changed
- `ddo/personas/product_critic.md` — `## Attack Vectors` restructured to 3-column AV-NN table (AV-01..AV-06)
- `ddo/personas/scientific_reviewer.md` — same AV-NN table restructure (AV-01..AV-06)
- `ddo/skills/ddo-red-team.md` — echoes AV table into report context; binds category to `AV-NN: <name>`; hard-fails on missing table (RT-05)
- `ddo/skills/ddo-interview.md` — op list updated to `set | append | delete | insert`; legacy deprecation section removed
- `ddo/refine.py` — `append_evidence`/`append_review_log` branches removed; unknown-op error lists `set, append, delete, insert` only
- `ddo/review.py` — `OP_ENUM` reduced to `frozenset({"set","append","delete","insert"})`
- `tests/unit/test_personas.py` — rewritten as glob-based AV-table validator (stdlib re; parametrized over ddo/personas/*.md)
- `tests/unit/test_refine.py` — 4 legacy-op tests flipped to ValueError rejection
- `tests/unit/test_review.py` — 2 net-new ReportValidationError rejection tests for removed ops
- `tutorials/ddo-adversarial-loop-v0.0.2/code_samples/interview_call.py` — migrated to `op: append`
- `tutorials/ddo-adversarial-loop-v0.0.2/tutorial.md` — deprecated-ops rows reworded to past tense

### Hypergraph (spec/compiled/architecture.yml)
- `skill_create_persona` node added (Atomic, ddo_skills/ddo_personas deps, no ddo_core)
- All 26 nodes now `status: clean`

### Documentation Updated (v0.0.4)
- `CHANGELOG.md` — `## [0.0.4]` block completed with Added/Changed/Removed/Documentation sections
- `README.md` — badge v0.0.3 → v0.0.4; skills listing adds ddo-create-persona.md; Red Team phase updated; roadmap v0.0.4 section added; test count 188 → 183
- `.agents/memory/activeContext.md` — this file

## v0.0.3 Implementation Summary

### New in `ddo/refine.py`
- `DanglingRefError(Exception)` — carries `paths: list[str]`; raised by `_dangling_ref_check` before a `delete` on `evidence_bank` proceeds
- `_dangling_ref_check(doc, index)` — scans `content.sections[*].evidence[]` for the entry's `id`; uses `dict.get()` throughout (never raises `KeyError` on malformed input)
- `apply_patches` extended with `append`, `delete`, `insert` op branches; all operate on the deep copy; mid-batch exception leaves original dict unchanged (atomicity)
- `parse_path` NC-13 whitelist: key segments `[a-zA-Z_][a-zA-Z0-9_]*`; index brackets `\d+` only

### Changed in `ddo/review.py`
- `validate_interview_log`: `OP_ENUM` constant (frozenset of 6 valid ops); per-op field rules (`insert` requires `at`; `delete` forbids `value`; structural ops require `target`); `at` type validation

### Updated Skills
- `ddo/skills/ddo-interview.md`: structural patch YAML examples (`target:` field); sequential-index warning; dangling-ref advisory; `append_evidence`/`append_review_log` deprecated (removed in v0.0.4)
- `ddo/skills/ddo-refine.md`: `DanglingRefError` handling section; multi-line diff note; human authorization gate framing

### Tests & Spec
- `tests/unit/test_refine.py` — 17 new tests (total ~57): append/delete/insert ops, atomicity, sequential-index shift documentation, dangling ref edge cases
- `tests/unit/test_review.py` — 11 new tests (total ~51): OP_ENUM acceptance + 6 invalid per-op field combination rejections
- `tests/integration/test_loop.py` — refactored to `test_loop_pass[@parametrize]` with `id="set-based"` and `id="structural"` cases; both use `shutil.copy` for isolation
- `tests/fixtures/loop/interview_log_v1_structural.yaml` — human-approved structural fixture (append + delete + insert)
- `spec/compiled/architecture.yml` — 7 nodes reconciled `needs_review` → `clean` (ddo_system, ddo_core, ddo_skills, tests_unit, tests_integration, documents_output, skill_red_team)

### Documentation Updated (v0.0.3)
- `pyproject.toml` — version `0.0.2` → `0.0.3`
- `CHANGELOG.md` — `## [0.0.3] - 2026-06-30` block added
- `README.md` — badge v0.0.2 → v0.0.3; Phase 5 updated with new ops and DanglingRefError; roadmap v0.0.3 section added; test count 159 → 188
- `.agents/memory/activeContext.md` — this file
- `.agents/memory/systemPatterns.md` — v0.0.3 patterns added

## Key Design Decisions (v0.0.3)

| Decision | Rationale |
|---|---|
| `DanglingRefError` has structured `.paths` attribute | `ddo-refine` can display a precise list to the human without string-parsing the exception message |
| `_dangling_ref_check` uses `dict.get()` throughout | Malformed docs (missing `content`/`sections`) must not raise `KeyError` — they produce no dangling refs |
| `at > len(list)` raises in `apply_patches` but `at == len` is valid (append-equivalent) | Matches Python `list.insert` semantics; avoids a confusing special case |
| `isinstance(at, bool)` explicit rejection | `bool` is a subclass of `int` in Python; `True` (=1) and `False` (=0) would be silently accepted without this guard |
| Sequential-index shift documented, not fixed | A batch with `insert at: 0` then `delete [3]` shifts indices — this is intentional and documented via a test |
| `append_evidence`/`append_review_log` deprecated, not removed | Backwards compat for v0.0.3; hardcoded removal planned for v0.0.4 |

### Tutorial Audit & Fixes (2026-06-30)
- `/hyper-tutorial-audit` run on both tutorials; audit files saved to `tutorials/*/audit_2026-06-30.md`
- `tutorials/ddo-v001-prd-workflow/tutorial.md` — fixed stale test count (78→188); Related section updated from "v0.0.2 roadmap" to shipped link
- `tutorials/ddo-adversarial-loop-v0.0.2/tutorial.md` — comprehensive v0.0.3 update: new ops table, `DanglingRefError`, NC-13 whitelist, sequential-index warning, pre-validation note, 4 new troubleshooting rows, stale row fixed
- `tutorials/ddo-adversarial-loop-v0.0.2/output_files/interview_log_v1.yaml` — F-004 migrated from `append_evidence` to `{op: append, target: "evidence_bank"}`
- Both tutorials are now accurate against v0.0.3

## Next Steps (v0.0.5+)
- Scientific report workflow tutorial (`tutorials/ddo-v001-scientific-report-workflow/`)
