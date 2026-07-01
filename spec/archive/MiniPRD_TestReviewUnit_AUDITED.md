# MiniPRD: TestReviewUnit
**Hypergraph Node ID:** `test_review_unit`
**File:** `tests/unit/test_review.py`
**Parent Node:** `tests_unit`
**SuperPRD:** `SuperPRD_v0.0.3_StructuralPatchDSL.md`
**Note:** This MiniPRD was MISSING from the Draft PRD blast radius — the Red Team correctly flagged this omission (RT-v0.0.3-5).

## 1. Confidence Mandate
**Score: 10/10.** Existing tests follow a clear pattern: `_valid_log()` helper builds a minimal valid log dict; tests mutate one field and assert pass or `ReportValidationError`. The v0.0.3 additions are purely additive — new test functions covering the new op enum and `at` field rules. No existing test is touched.

## 2. Atomic User Stories
- **US-1**: New tests assert `validate_interview_log` accepts `op: "append"`, `op: "delete"`, `op: "insert"` (with valid `at`).
- **US-2**: New negative tests assert `validate_interview_log` rejects invalid per-op field combinations.
- **US-3**: New test asserts `validate_interview_log` rejects unknown op strings.

## 3. Implementation Plan

- [ ] Read `tests/unit/test_review.py` fully — map existing `_valid_log` helper and `validate_interview_log` test section.
- [ ] Add `test_validate_interview_log_append_op_accepted`:
  - Log with `op: "append"`, `target: "evidence_bank"`, `value: {...}` → passes without exception.
- [ ] Add `test_validate_interview_log_delete_op_accepted`:
  - Log with `op: "delete"`, `target: "evidence_bank[0]"` (no `value`) → passes.
- [ ] Add `test_validate_interview_log_insert_op_with_at_accepted`:
  - Log with `op: "insert"`, `target: "content.sections"`, `at: 2`, `value: {...}` → passes.
- [ ] Add `test_validate_interview_log_insert_without_at_raises`:
  - `op: "insert"` with no `at` field → raises `ReportValidationError`.
- [ ] Add `test_validate_interview_log_delete_with_value_raises`:
  - `op: "delete"` with `value` field present → raises `ReportValidationError`.
- [ ] Add `test_validate_interview_log_set_with_at_raises`:
  - `op: "set"` with `at: 0` → raises `ReportValidationError`.
- [ ] Add `test_validate_interview_log_append_with_at_raises`:
  - `op: "append"` with `at: 1` → raises `ReportValidationError`.
- [ ] Add `test_validate_interview_log_delete_with_at_raises`:
  - `op: "delete"` with `at: 0` → raises `ReportValidationError`.
- [ ] Add `test_validate_interview_log_insert_negative_at_raises`:
  - `op: "insert"`, `at: -1` → raises `ReportValidationError`.
- [ ] Add `test_validate_interview_log_insert_bool_at_raises`:
  - `op: "insert"`, `at: True` → raises `ReportValidationError`.
- [ ] Add `test_validate_interview_log_unknown_op_raises`:
  - `op: "replace"` → raises `ReportValidationError`.
- [ ] Run `uv run pytest tests/unit/test_review.py -v` → all pass.
- [ ] Run `uv run ruff check . && uv run ruff format --check .`.

## 4. Negative Space (Constraints)

- **DO NOT** delete or weaken any existing `test_review.py` test.
- **DO NOT** test `at` bounds (e.g., `at > len(list)`) here — bounds checking belongs in `apply_patches`, not `validate_interview_log`.
- **DO NOT** test path syntax (e.g., `[N]`-terminated target for `append`) here — path validation belongs in `parse_path`.

## 5. Integration Tests & Verification

All tests are deterministic — fixed input dicts, assert pass or specific exception.

- **After implementation:** `uv run pytest tests/unit/test_review.py -v` exits 0.
- **Regression check:** `git diff tests/unit/test_review.py` — confirm only additions. Zero deletions.
- **M4 (validate_interview_log matrix):** The six invalid-combination negative tests directly implement SuperPRD M4.
