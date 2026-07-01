# MiniPRD: ReviewEngine
**Hypergraph Node ID:** `review_engine`
**File:** `ddo/review.py`
**Parent Node:** `ddo_core`
**SuperPRD:** `SuperPRD_v0.0.3_StructuralPatchDSL.md`

## 1. Confidence Mandate
**Score: 9/10.** `validate_interview_log` currently validates `finding_id`, `decision`, `detail`, and `patch` presence but does NOT validate `op` type or `at` field at all. The extension adds op-level validation. Clarifying question: confirm no other caller of `validate_interview_log` in the codebase passes non-standard ops that would break with the new strict validation.

## 2. Atomic User Stories
- **US-1**: `validate_interview_log` accepts the new op enum values `"append"`, `"delete"`, `"insert"` alongside the existing `"set"`, `"append_evidence"`, `"append_review_log"`.
- **US-2**: `validate_interview_log` enforces per-op field rules: `insert` requires `at` field; `delete` forbids `value` field; all structural ops except `append_evidence`/`append_review_log` require `target` field.
- **US-3**: `validate_interview_log` validates the `at` field type when present: `isinstance(at, int) and not isinstance(at, bool) and at >= 0`.
- **US-4**: `validate_interview_log` rejects unknown op values with a clear `ReportValidationError`.

## 3. Implementation Plan

- [ ] Read `ddo/review.py` fully — locate `validate_interview_log` and all callers.
- [ ] Grep for any caller passing `op` values to `validate_interview_log` that are NOT in the new valid set.
- [ ] Add `OP_ENUM` constant (or equivalent) to `ddo/review.py`:
  ```python
  OP_ENUM: frozenset[str] = frozenset({
      "set", "append", "delete", "insert",
      "append_evidence", "append_review_log",
  })
  ```
- [ ] In `validate_interview_log`, for each resolution where `patch` is not null:
  - Validate `op in OP_ENUM` (reject unknown ops).
  - For `op in {"set", "append", "delete", "insert"}`: require `target` field.
  - For `op == "insert"`: require `at` field; validate `isinstance(at, int) and not isinstance(at, bool) and at >= 0`.
  - For `op != "insert"`: reject `at` field if present.
  - For `op == "delete"`: reject `value` field if present.
  - For `op in {"append_evidence", "append_review_log"}`: no `target` field required (hardcoded ops).
- [ ] Run `uv run ruff check . && uv run ruff format --check .`.

## 4. Negative Space (Constraints)

- **DO NOT** validate `target` path syntax in `validate_interview_log` — path validation belongs to `parse_path` in `ddo/refine.py`.
- **DO NOT** validate `value` contents in `validate_interview_log` — structural schema validation happens via `validate()` post-mutation.
- **DO NOT** modify any other function in `ddo/review.py`.
- **DO NOT** add a hard `at >= 0` semantics check beyond the type constraint — bounds checking (`at <= len(list)`) belongs in `apply_patches`.

## 5. Integration Tests & Verification

- **Test (deterministic):** `validate_interview_log` with `op: "append"` + `target` + `value` → passes.
- **Test (deterministic):** `validate_interview_log` with `op: "delete"` + `target` (no `value`) → passes.
- **Test (deterministic):** `validate_interview_log` with `op: "insert"` + `target` + `at: 2` + `value` → passes.
- **Negative test:** `op: "insert"` without `at` field → raises `ReportValidationError`.
- **Negative test:** `op: "delete"` with `value` field → raises `ReportValidationError`.
- **Negative test:** `op: "set"` with `at` field → raises `ReportValidationError`.
- **Negative test:** `op: "insert"` with `at: -1` → raises `ReportValidationError`.
- **Negative test:** `op: "insert"` with `at: True` → raises `ReportValidationError`.
- **Negative test:** `op: "replace"` (unknown op) → raises `ReportValidationError`.
- **Negative test:** `op: "append"` with `[N]`-terminated target (path validation note: only validated in parse_path, but a unit test can confirm behavior end-to-end via `apply_patches`).
