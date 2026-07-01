# MiniPRD: RefineEngine
**Hypergraph Node ID:** `refine_engine`
**File:** `ddo/refine.py`
**Parent Node:** `ddo_core`
**SuperPRD:** `SuperPRD_v0.0.3_StructuralPatchDSL.md`

## 1. Confidence Mandate
**Score: 9/10.** All trade-offs resolved. The atomicity invariant is already implemented (`copy.deepcopy` at line 245). The `DanglingRefError` class and `_dangling_ref_check` helper are net-new. The path parser extension follows the existing hand-rolled pattern. NC-13 character whitelist must be enforced in `parse_path`. Clarifying questions to reach 10: confirm the path parser's current regex/character handling before extending it.

## 2. Atomic User Stories
- **US-1**: Implement `DanglingRefError(Exception)` with `paths: list[str]` attribute. The `.paths` attribute is the authoritative structured output for `skill_refine` to parse and display.
- **US-2**: Implement `_dangling_ref_check(doc: dict, index: int) -> None`. Invoked only for `delete` targeting `evidence_bank[N]`. Uses `dict.get()` with empty defaults throughout — must not raise `KeyError` on malformed input.
- **US-3**: Extend `apply_patches` with `append`, `delete`, `insert` op branches. All operate on `patched` (the deep copy at entry). Exception mid-batch discards `patched` and the original input is unchanged.
- **US-4**: Extend `parse_path` to handle new path grammar rules per op type. Enforce NC-13 character whitelist for key segments (`[a-zA-Z_][a-zA-Z0-9_]*`) and index brackets (`\d+` only — no negative sign).
- **US-5**: Update the existing unknown-op error message to list new valid ops. Update the currently-failing "delete is unknown op" test target.

## 3. Implementation Plan

- [ ] Read current `ddo/refine.py` fully — map `parse_path`, `apply_patches`, existing op branches.
- [ ] Add `DanglingRefError` class immediately after existing imports/constants section.
- [ ] Add `_dangling_ref_check(doc, index)` function:
  - Extract `entry_id = doc["evidence_bank"][index]["id"]`
  - Scan `doc.get("content", {}).get("sections", [])` → each section's `.get("evidence", [])`
  - Collect all paths where `entry_id` appears
  - If any: `raise DanglingRefError(paths=[...])`
- [ ] Extend `parse_path` (or the path navigation logic) to:
  - For `append`/`insert`: verify resolved node is `list`; reject if target ends in `[N]`
  - For `delete`: require target ends in `[N]`; return (parent_list, index)
  - Reject key segments not matching `[a-zA-Z_][a-zA-Z0-9_]*`
  - Reject index content not matching `\d+`
- [ ] Add `append` branch to `apply_patches`:
  - Navigate to list via target
  - `list_node.append(value)`
- [ ] Add `delete` branch to `apply_patches`:
  - Navigate to parent list + index
  - If path resolves to `evidence_bank`: call `_dangling_ref_check(patched, index)`
  - `list_node.pop(index)`
- [ ] Add `insert` branch to `apply_patches`:
  - Validate `at`: `isinstance(at, int) and not isinstance(at, bool) and at >= 0 and at <= len(list_node)` (out-of-bounds: `at > len` raises bounds error; `at == len` is valid append-equivalent)
  - `list_node.insert(at, value)`
- [ ] Update the unknown-op error message/list to include the 3 new ops.
- [ ] Run `uv run ruff check . && uv run ruff format --check .` to verify lint-clean.

## 4. Negative Space (Constraints)

- **DO NOT** use `eval` or dynamic code execution in the path parser.
- **DO NOT** auto-vivify a missing list for `append`/`insert` — missing path is a hard error.
- **DO NOT** allow `delete` to proceed if `_dangling_ref_check` raises.
- **DO NOT** allow `at < 0`, `at: True/False`, or `at: 2.0` — the `isinstance(at, int) and not isinstance(at, bool) and at >= 0` guard rejects all three.
- **DO NOT** allow `[N]`-terminated target for `append` or `insert`.
- **DO NOT** allow `value` field on `delete` patches.
- **DO NOT** modify `validate()` in `ddo/validation.py`.
- **DO NOT** accept path index brackets containing non-digit characters (no `[-1]`, `[*]`, `[0x1]`).

## 5. Integration Tests & Verification

- **Test (deterministic):** `apply_patches(data, log)` where log has `append evidence_bank` → returned dict has `len(evidence_bank) == original + 1`.
- **Test (deterministic):** `apply_patches` with `delete evidence_bank[0]` where `evidence_bank[0].id` is referenced → raises `DanglingRefError`; original dict unchanged.
- **Test (deterministic):** `apply_patches` with `delete evidence_bank[0]` where `evidence_bank[0].id` is NOT referenced → proceeds; element removed.
- **Test (deterministic):** `apply_patches` with `insert content.sections at: 0` → element at original index 0 is now at index 1.
- **Test (deterministic):** `apply_patches` with `insert content.sections at: len(sections)` → output identical to `append`.
- **Test (deterministic):** `apply_patches` with `insert` + `at: -1` → raises `ValueError`.
- **Test (deterministic):** `apply_patches` with `insert` + `at: True` → raises `ValueError`.
- **Test (deterministic):** `apply_patches` mid-batch exception → original input dict unchanged (atomicity).
- **Test (deterministic):** Sequential-index: batch with `insert evidence_bank at: 0` then `delete evidence_bank[3]` → asserts specifically which element was deleted (documents the shift behavior explicitly).
- **Negative test:** Update existing "unknown op" test (`test_apply_patches_unknown_op_raises`) — change `"delete"` to `"replace"` (or any string not in valid op set).
