# MiniPRD: TestRefineUnit
**Hypergraph Node ID:** `test_refine_unit`
**File:** `tests/unit/test_refine.py`
**Parent Node:** `tests_unit`
**SuperPRD:** `SuperPRD_v0.0.3_StructuralPatchDSL.md`

## 1. Confidence Mandate
**Score: 9/10.** The existing test file follows a clear pattern — each function tests one behavior via `apply_patches`, `parse_path`, or `commit_refine`. The one required UPDATE (not just addition) is the existing "delete is unknown op" test at approximately line 345, which asserts `"delete"` raises `ValueError("unknown op")`. After v0.0.3, `"delete"` is valid — that test must change its `op` string to something genuinely unknown (e.g., `"replace"`). Clarifying question: confirm exact line number by reading the file before editing.

## 2. Atomic User Stories
- **US-1**: New tests for `append` op: valid append succeeds; non-list target raises; `[N]`-terminated target raises.
- **US-2**: New tests for `delete` op: valid delete without dangling ref succeeds; dangling ref raises `DanglingRefError`; out-of-bounds index raises; `value` field on delete raises (caught by `validate_interview_log` upstream, but test directly via `apply_patches` too).
- **US-3**: New tests for `insert` op: valid insert at 0 succeeds; `at: len(list)` produces same output as `append`; `at > len(list)` raises; `at: -1` raises; `at: True` raises; `at: 2.0` raises.
- **US-4**: Atomicity test: mid-batch exception leaves original input unchanged.
- **US-5**: Sequential-index documentation test: batch with `insert at: 0` then `delete [3]` — asserts which element is deleted (documents the shift behavior explicitly, per the user's decision).
- **US-6**: `_dangling_ref_check` tests: same-batch `set`-then-delete scenario (set adds ref, then delete raises DanglingRefError on post-set in-memory doc); malformed-doc input does not raise `KeyError`.
- **US-7**: Update the existing "delete is unknown op" test to use `op: "replace"` (or any non-valid op string).

## 3. Implementation Plan

- [ ] Read `tests/unit/test_refine.py` fully — map all existing tests and the `_valid_doc` / `_make_log` helper pattern.
- [ ] Identify and update the "delete is unknown op" test (approximately line 345): change `"op": "delete"` to `"op": "replace"` in the test fixture dict. Verify assertion still reads `match="unknown op"`.
- [ ] Add `test_apply_patches_append_list_succeeds`:
  - Append a valid dict to `evidence_bank` → assert `len(evidence_bank) == original + 1`.
- [ ] Add `test_apply_patches_append_non_list_target_raises`:
  - `target: "meta.title"` (a string, not a list) + `op: "append"` → raises `ValueError`.
- [ ] Add `test_apply_patches_append_index_terminated_target_raises`:
  - `target: "evidence_bank[0]"` + `op: "append"` → raises `ValueError`.
- [ ] Add `test_apply_patches_delete_non_dangling_succeeds`:
  - Delete `evidence_bank[0]` where `evidence_bank[0].id` is NOT in any `content.sections[*].evidence[]` → element removed, list shorter.
- [ ] Add `test_apply_patches_delete_dangling_raises`:
  - Delete `evidence_bank[N]` where the entry's `id` IS referenced → raises `DanglingRefError`; original input unchanged.
- [ ] Add `test_apply_patches_delete_dangling_ref_error_has_paths`:
  - Catch `DanglingRefError` → assert `e.paths` is a non-empty list of strings.
- [ ] Add `test_apply_patches_delete_oob_raises`:
  - `target: "evidence_bank[99]"` → raises `ValueError` (out-of-bounds).
- [ ] Add `test_apply_patches_insert_at_zero_succeeds`:
  - `insert content.sections at: 0` → element is at index 0; original index 0 is now at index 1.
- [ ] Add `test_apply_patches_insert_at_len_equals_append`:
  - `insert evidence_bank at: len(evidence_bank)` → output identical to `append` (element at end).
- [ ] Add `test_apply_patches_insert_at_oob_raises`:
  - `at: len(list) + 1` → raises `ValueError`.
- [ ] Add `test_apply_patches_insert_at_negative_raises`:
  - `at: -1` → raises `ValueError`.
- [ ] Add `test_apply_patches_insert_at_bool_raises`:
  - `at: True` → raises `ValueError` (bool is subclass of int; must be explicitly rejected).
- [ ] Add `test_apply_patches_insert_at_float_raises`:
  - `at: 2.0` → raises `ValueError`.
- [ ] Add `test_apply_patches_atomicity_on_mid_batch_exception`:
  - Batch: [valid `set`, `delete` with dangling ref]. After `DanglingRefError`, original input dict is unchanged (verify with `assert result == original_data` or check that `data is not patched_attempt`).
- [ ] Add `test_apply_patches_sequential_index_shift_documented`:
  - Batch: [`insert evidence_bank at: 0` with new entry], [`delete evidence_bank[2]`]. Assert that element at original index 1 (now at index 2 after insert) was deleted — explicitly documenting the shift behavior. Add a comment explaining this is intentional documentation of the sequential-execution semantic.
- [ ] Add `test_dangling_ref_check_set_before_delete_caught`:
  - Batch: [`set content.sections[0].evidence[0]` to an existing evidence ID], then [`delete evidence_bank[N]` where N is that evidence entry]. The set runs first → `_dangling_ref_check` sees the post-set doc → correctly raises `DanglingRefError`.
- [ ] Add `test_dangling_ref_check_malformed_doc_no_keyerror`:
  - Call `_dangling_ref_check` with a doc missing `content`/`sections` → does NOT raise `KeyError`; either raises `DanglingRefError` (no refs, correct) or returns cleanly.
- [ ] Run `uv run pytest tests/unit/test_refine.py -v` → all pass.
- [ ] Run `uv run ruff check . && uv run ruff format --check .`.

## 4. Negative Space (Constraints)

- **DO NOT** delete or weaken any existing test. Only add new tests + the one targeted line update.
- **DO NOT** test semantic correctness of the document content (only structural / error-path behavior).
- **DO NOT** add tests that require actual file I/O (use the existing `_valid_doc` / `_make_log` pattern — pure in-memory).
- **DO NOT** suppress the sequential-index shift test with `pytest.xfail` — it must pass and document known behavior.

## 5. Integration Tests & Verification

All tests listed above are deterministic (fixed input → exact output assertion). No Candidate Artifact routing.

- **After implementation:** `uv run pytest tests/unit/test_refine.py -v` exits 0 with all new tests passing.
- **Regression check:** `git diff tests/unit/test_refine.py` — confirm only additions + the one line change at ~345. No deletions of existing test functions.
- **M5 (atomicity):** `test_apply_patches_atomicity_on_mid_batch_exception` is the direct regression test for SuperPRD M5.
