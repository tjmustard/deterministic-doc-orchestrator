
# Active Context
## Purpose
This file updates dynamically after *every task completion*. It captures the "Now" of the project: what was just done, what is currently being worked on, and any immediate blockers or open questions.

## Usage
- Agent writes here after completing a task.
- Agent reads this *first* to understand where to pick up.

## Current Sprint Goal
**DDO v0.0.3 — COMPLETE ✅ (2026-06-30)**

Structural Patch DSL fully implemented, audited, and released. 188 tests passing.

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

## Next Steps (v0.0.4+)
- Remove `append_evidence` and `append_review_log` ops (deprecated in v0.0.3)
- Scientific report workflow tutorial (`tutorials/ddo-v001-scientific-report-workflow/`)
