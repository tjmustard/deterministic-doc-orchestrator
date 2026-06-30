# SuperPRD: DDO v0.0.3 — Structural Patch DSL Expansion

> **Status:** COMPILED (output of `/hyper-resolve`). Source: `spec/active/Draft_PRD.md` + `spec/active/RedTeam_Report.md`, mediated with the user.
> **Version:** v0.0.3
> **Date:** 2026-06-30
> **Author:** Thomas J. L. Mustard (interviewed) + Architect Agent + Red Team + Resolution Agent
> **Parent Node:** `ddo_system`
> **Next step:** `/hyper-execute` each MiniPRD in `spec/compiled/`, then `hypergraph_updater.py` + `/hyper-audit`.

---

## 1. Introduction & Goals

### Problem Statement
The `ddo-refine` patch DSL (v0.0.2) only supports `set` on leaf-scalar fields, plus two hardcoded ops (`append_evidence`, `append_review_log`). When a Red Team finding requires a **structural mutation** — adding a new evidence entry, removing a stale claim, inserting a new section — the pipeline has no machine-readable path to resolve it. The only workarounds are a semantically invalid `set`, a manual edit outside the pipeline, or indefinite deferral. v0.0.3 closes this gap.

### Solution Overview
Extend `ddo/refine.py`'s `apply_patches` function and the hand-rolled path-DSL parser to support three new generic operations: **`append`**, **`delete`**, and **`insert`**. Add a `DanglingRefError` guard for `delete` operations on `evidence_bank`. Update `validate_interview_log` in `ddo/review.py` to accept the new op types and the new `at` field. Update cognitive skills and add 7+ unit tests + one new human-gated integration fixture. Mark legacy ops (`append_evidence`, `append_review_log`) as deprecated (removed in v0.0.4).

### Target Audience
Solo human author/reviewer using the DDO pipeline; AI interview agent (`ddo-interview`) generating structural patch batches; AI refine agent (`ddo-refine`) applying and committing patches. Single-user, local-filesystem, Claude Code / HACF-driven (not SaaS).

### Field Name Correction (Draft PRD discrepancy)
The Draft PRD YAML examples used `path:` as the patch field name. This conflicts with the existing code, which uses `target:` (see `ddo/refine.py:254`, all existing tests). **v0.0.3 uses `target:` for all ops** — existing and new — to preserve backward compatibility and keep the blast radius minimal. "Path" remains informal shorthand in documentation only.

---

## 2. Confidence Mandate

**Score: 9/10** (post-Red Team, post-Resolution)

All 13 Red Team findings have documented decisions. The two P0-CRITICAL findings were:
- **validate() duplicate-ID behavior** — confirmed by code inspection (`validation.py:91`) to already raise `ValidationError` on duplicates. RT-v0.0.3-2 is valid as-written; the architecture node description "orphans warn, not fail" referred to *orphaned* (unreferenced) entries only. No code change needed.
- **Negative `at` values** — genuine spec gap; resolved with explicit guard in §5.1.

The `apply_patches` atomicity concern was confirmed pre-resolved (`refine.py:245`, deep copy at entry). All remaining findings resolved by the user in `/hyper-resolve`.

---

## 3. Scope

### In-Scope

1. **`append` operation** — add a new element to the end of a list-typed field. `target` must resolve to an existing list (no auto-vivify); path must not end in `[N]`.
2. **`delete` operation** — remove the element at a specific index from a list-typed field. `target` must end in `[N]`.
3. **`insert` operation** — insert a new element at position `at: N` within a list-typed field. `target` must resolve to an existing list; `at` is a separate required field (not embedded in path).
4. **`DanglingRefError` guard** — if a `delete` targets `evidence_bank[N]` and that entry's `id` is still referenced in any `content.sections[*].evidence[]`, refuse before mutation with a structured error listing all referencing paths.
5. **`validate_interview_log` update** — accept new op types and the optional `at` field; enforce per-op field rules (see §5.1 grammar table).
6. **`skill_interview` update** — structural patch generation instructions; sequential-index warning; legacy op deprecation notice.
7. **`skill_refine` update** — Before/After diff for structural ops; DanglingRefError display.
8. **New integration fixture** — `tests/fixtures/loop/interview_log_v1_structural.yaml` exercising one `append`, one `delete`, one `insert`; promoted under human sign-off.
9. **Parametrized loop test** — `test_loop_integration` runs both `interview_log_v1.yaml` and `interview_log_v1_structural.yaml`.
10. **Pre-condition**: `tests/fixtures/loop/document_data_with_gap.yaml` + `tests/fixtures/loop/interview_log_v1.yaml` (v0.0.2 loop fixtures) do not yet exist on disk. The execute agent must author both as candidate artifacts, present them to the human for character-by-character review, and receive signoff **before** designing the structural fixture. This is step 0 of the execution checklist.

### Out-of-Scope (explicit deferrals)

- **Type-changing `set`** — changing a scalar to a list/dict or vice versa remains blocked.
- **Auto-vivify** — `append`/`insert` require the target list to already exist.
- **Cascade deletion of dangling refs** — refuse only; agent must fix refs first.
- **Non-evidence-bank reference integrity** — the DanglingRefError guard applies only to `evidence_bank` deletions. Section deletions leaving orphaned evidence IDs are not guarded (warn at `validate()` level only, per existing behavior — this asymmetry is documented as a known gap).
- **`review_history/` cap/prune** — deferred to v0.0.4+.
- **Composite `ddo-run` macro** — deferred.
- **New document types** — deferred.
- **File locking / multi-user** — single-user/no-concurrency invariant unchanged.
- **Snapshot-staleness check** — the single-user invariant (NC-9) makes concurrent edit-after-snapshot impossible by design; mtime/hash check deferred to v0.0.4+.
- **`append_evidence` / `append_review_log` removal** — kept coexisting in v0.0.3, removed in v0.0.4.

### Known Gaps (documented, not fixed in v0.0.3)

- **Section→evidence asymmetry**: The DanglingRefError guard runs evidence→section only. A `delete content.sections[N]` leaving orphaned evidence IDs in `evidence_bank` is not pre-blocked; `validate()` warns post-mutation but does not fail (orphans). This is a known gap — see §5.2 RT-v0.0.3-6.
- **Sequential-index invalidation**: A batch containing `insert evidence_bank at: 0` followed by `delete evidence_bank[3]` will delete what was originally at index 2 (the insert shifted it). This is silent but correct-by-sequential-semantics. `skill_interview` warns against it; unit test documents the behavior; no batch-level rejection in v0.0.3.

---

## 4. User Stories

### US-1: Append a new list element
**As** an AI interview agent,
**I want** to generate an `append` patch targeting a list-typed field (e.g., `evidence_bank`),
**So that** I can resolve findings requiring new source entries, new sections, or new claims by adding elements without manual YAML editing.

**Acceptance Criteria:**
- `{target: "evidence_bank", op: "append", value: {id: "eN", type: "...", content: "...", source: "..."}}` applies successfully; element appears at `len(evidence_bank)`.
- `target` resolving to a non-list type raises a clear error.
- `target` ending in `[N]` is rejected with a clear error (ambiguous grammar).
- `at` field on `append` is rejected.
- Full `validate()` runs post-mutation before commit; duplicate IDs raise `ValidationError` (confirmed: `validation.py:91`).
- Pre-mutation snapshot is taken before any mutation.

**Priority:** P0

---

### US-2: Delete a stale list element
**As** an AI interview agent,
**I want** to generate a `delete` patch targeting `evidence_bank[N]` or `content.sections[N]`,
**So that** I can remove obsolete or incorrect elements from any list-typed field.

**Acceptance Criteria:**
- `{target: "evidence_bank[2]", op: "delete"}` removes element at index 2 (zero-based); higher-index elements shift down.
- `value` field on `delete` is **forbidden** (rejected with error before mutation) — not ignored.
- Out-of-bounds index (`N >= len(list)`) raises a clear bounds error; document is not mutated.
- Full `validate()` runs post-mutation before commit.
- Pre-mutation snapshot is taken.

**Priority:** P0

---

### US-3: DanglingRefError guard on evidence_bank delete
**As** a human reviewer,
**I want** the refine engine to refuse a `delete` on `evidence_bank[N]` if that entry's ID is still referenced in any `content.sections[*].evidence[]` list,
**So that** the pipeline never silently produces a document with broken evidence references.

**Acceptance Criteria:**
- If `evidence_bank[N].id` appears in any `content.sections[K].evidence[M]`, the `_dangling_ref_check` raises `DanglingRefError` before any mutation.
- `DanglingRefError` exposes a `paths: list[str]` attribute with all referencing paths (e.g., `["content.sections[0].evidence[1]"]`).
- `document_data.yaml` and the snapshot are not written on rejection.
- A `delete evidence_bank[N]` where the ID is NOT referenced proceeds normally (US-2).
- The guard runs only for `evidence_bank` deletions; other list deletes have no ref-check.
- `_dangling_ref_check` is called on the post-prior-patches in-memory doc (correct behavior in batches: a `set` patch that adds a reference before a `delete` patch is caught).

**Priority:** P0

---

### US-4: Insert at a specific index
**As** an AI interview agent,
**I want** to generate an `insert` patch with a target list and `at: N` field,
**So that** I can add elements at specific positions (e.g., prepend a section, insert a claim before index 2).

**Acceptance Criteria:**
- `{target: "content.sections", op: "insert", at: 2, value: {...}}` inserts at index 2; existing elements at index ≥ 2 shift up.
- `at: 0` inserts at front; `at: len(list)` is equivalent to `append` (unit-tested).
- `at: N` where `N > len(list)` raises a clear bounds error; document is not mutated.
- `at` field is required for `op: "insert"`; missing `at` is a pre-mutation validation error.
- `at` field must satisfy: `isinstance(at, int) and not isinstance(at, bool) and at >= 0`. Negative values, booleans (`True`/`False`), and floats (`2.0`) are all rejected.
- Full `validate()` runs post-mutation before commit.
- Pre-mutation snapshot is taken.

**Priority:** P1

---

### US-5: skill_interview generates structural patch syntax
**As** a human reviewer,
**I want** `ddo-interview` to automatically generate correct `append`/`delete`/`insert` patch YAML when a finding calls for structural changes,
**So that** I don't need to hand-craft structural repairs.

**Acceptance Criteria:**
- Skill generates correct `op: "append"` or `op: "insert"` with a complete, schema-valid `value` when a finding's resolution requires adding an element.
- Skill generates correct `op: "delete"` with `[N]`-terminated `target` when removal is needed.
- Skill displays full AI-generated `value` in the decision prompt (human authorization gate).
- Skill warns about the dangling-ref risk for `delete` on `evidence_bank` entries (AI should patch refs first using `set` patches before issuing the delete).
- Skill warns: **avoid multiple index-bearing patches on the same parent list in one batch** — earlier `insert`/`delete` ops shift indices, making later index-bearing ops on the same list semantically unreliable.
- Skill marks `append_evidence` and `append_review_log` as **deprecated** — use generic `append` with `target: "evidence_bank"` and `target: "meta.review_log"` respectively. These legacy ops will be removed in v0.0.4.

**Priority:** P1

---

### US-6: Integration test coverage for structural ops
**As** a developer,
**I want** the loop integration test to exercise at least one `append`, one `delete`, and one `insert` through the full refine pipeline,
**So that** structural op regressions are caught before merge.

**Acceptance Criteria:**
- `tests/fixtures/loop/interview_log_v1_structural.yaml` exists and is signed off under `DDO_FIXTURE_SIGNOFF=1`.
- `test_loop_integration` is parametrized over both `interview_log_v1.yaml` and `interview_log_v1_structural.yaml`.
- Each parametrized case uses its own `tmp_path` copy of `document_data_with_gap.yaml` (no shared mutable state between cases).
- The structural fixture case passes: sentinel-absence, `validate()`-clean, 3-format render success.
- The structural fixture is a candidate artifact authored by the execute agent and reviewed character-by-character by the human before sign-off (see step 10a in checklist).
- `document_data_with_gap.yaml` must have ≥ 3 evidence_bank entries and ≥ 2 content sections to allow a non-dangling delete and section-level operations.

**Priority:** P1

---

## 5. Technical Specifications

### 5.1 Patch DSL Schema

#### Extended op enum and grammar

All patches use the `target:` field name (consistent with v0.0.2 — the Draft PRD's use of `path:` was a naming error not reflected in the code).

```yaml
# Existing (unchanged)
- target: "meta.version"
  op: "set"
  value: "0.2.0"

# Existing (deprecated, kept in v0.0.3, removed in v0.0.4)
- op: "append_evidence"
  value: {id: "e5", type: "claim", content: "...", source: "..."}

# New: append
- target: "evidence_bank"
  op: "append"
  value:
    id: "e5"
    type: "claim"
    content: "Supporting evidence text"
    source: "User review 2026-06-29"

# New: delete (target ends in [N])
- target: "evidence_bank[2]"
  op: "delete"

# New: insert (at: N required, separate field)
- target: "content.sections"
  op: "insert"
  at: 0
  value:
    id: "new_section"
    title: "New Section"
    body: ""
    claims: []
    evidence: []
```

**Path grammar rules by op:**

| op | `target` form | `at` field | `value` field |
|---|---|---|---|
| `set` | dotted + optional `[N]` | forbidden | required (scalar) |
| `append` | dotted, no trailing `[N]` | forbidden | required (any YAML) |
| `delete` | dotted + required trailing `[N]` | forbidden | forbidden |
| `insert` | dotted, no trailing `[N]` | required (int, see below) | required (any YAML) |
| `append_evidence` | (hardcoded; deprecated) | n/a | required (dict) |
| `append_review_log` | (hardcoded; deprecated) | n/a | required (dict) |

**`at` field type constraint (insert only):**
`isinstance(at, int) and not isinstance(at, bool) and at >= 0`
- Negative values (`at: -1`): **rejected** — Python's `list.insert(-1, x)` silently inserts before the last element, not at the end.
- Booleans (`at: True`, `at: False`): **rejected** — `bool` is a subclass of `int` in Python; `at: True` (= 1) would silently pass `isinstance(at, int)` without this guard.
- Floats (`at: 2.0`): **rejected** — YAML parsers may coerce these; the check must enforce strict `int` type.

**Path segment character whitelist (NC-13):**
- Key segments: `[a-zA-Z_][a-zA-Z0-9_]*`
- Index brackets: `\d+` only (positive integers; no negative sign, no expressions)
- This constraint applies to all ops. A path like `evidence_bank[-1]` or `__class__` is rejected at parse time.

**Atomicity invariant (confirmed in code, stated in spec):**
`apply_patches` deep-copies the input document at function entry (`copy.deepcopy(data)`, `refine.py:245`). If any patch raises, the copy is discarded and the original input is returned unchanged. The function never mutates its input argument.

#### `ddo/refine.py` changes

1. **`DanglingRefError` class** — new exception in `ddo/refine.py`:
   ```python
   class DanglingRefError(Exception):
       def __init__(self, paths: list[str]) -> None:
           self.paths = paths
           super().__init__(f"dangling refs: {paths}")
   ```
   The `.paths` attribute is the authoritative structured output for `skill_refine` to parse and display.

2. **`_dangling_ref_check(doc, index)` helper** — invoked only for `delete` on paths resolving to `evidence_bank`. Assumes the document has already passed `validate()` structurally (defensively handles missing `content`/`sections` with `dict.get()`):
   - Extract `entry_id = doc["evidence_bank"][index]["id"]`
   - Scan all `doc.get("content", {}).get("sections", [])` → each section's `"evidence"` list
   - If refs found: raise `DanglingRefError(paths=[...])` with structured path list before any mutation

3. **`apply_patches` extension** — three new branches after the existing `set` branch. All operate on `patched` (the deep copy at entry):
   - `append`: navigate to list, `list.append(value)`
   - `delete`: navigate to parent list + index, run `_dangling_ref_check` if path resolves to `evidence_bank`, `list.pop(index)`
   - `insert`: navigate to list, validate `at <= len(list)`, `list.insert(at, value)`
   
   The existing unknown-op test (`test_apply_patches_unknown_op_raises`) currently asserts `"delete"` is unknown — this test must be updated, not deleted: add `"delete"` as a valid op and use a different unknown op string (e.g., `"replace"`) in the existing negative test.

4. **Path parser extension** — extend the existing hand-rolled parser:
   - For `append`/`insert`: validate the resolved node is a list; reject if `target` ends in `[N]`.
   - For `delete`: validate `target` ends in `[N]`; resolve parent list and integer index.
   - Reject any path segment not matching the NC-13 character whitelist.
   - Reject any index bracket not matching `\d+` (reject `[-1]`, `[*]`, `[0x1]`).

5. **Purity invariant** — `apply_patches` remains a pure function (no I/O). All new branches operate on the in-memory `patched` dict.

6. **`refine_structural_check` update** — existing check validates list-typed fields remain lists after mutation. It already raises on empty `content.sections` via an independent check. No changes required to the structural check itself.

#### `ddo/review.py` changes

`validate_interview_log` update:
- Accept `op` values: `"set"`, `"append"`, `"delete"`, `"insert"`, `"append_evidence"`, `"append_review_log"` (currently no op validation exists — validate_interview_log does not currently check op; the extension adds this check).
- For `op: "insert"`: require `at` field and validate `isinstance(at, int) and not isinstance(at, bool) and at >= 0`.
- For `op != "insert"`: reject `at` field if present.
- For `op: "delete"`: reject `value` field if present.
- For `op` in `{"append", "insert", "set"}`: require `target` field.
- For `op` in `{"append_evidence", "append_review_log"}`: `target` is not applicable (hardcoded ops).

#### Skill updates

**`ddo/skills/ddo-interview.md`:**
- Add "Structural Patch Syntax" section: when a finding requires list mutation, generate `append`/`delete`/`insert` with correct `target` + `at` (for insert) + `value` (for append/insert).
- Add dangling-ref advisory: for `delete` on `evidence_bank[N]`, first issue `set` patches to remove all refs in `content.sections[*].evidence[]`, then issue the delete.
- Add sequential-index warning: **"Avoid generating multiple index-bearing patches targeting the same parent list in one batch. Earlier `insert` or `delete` ops shift indices — later patches on the same list in the same batch will target shifted positions."**
- Add deprecation notice: `append_evidence` → use `{target: "evidence_bank", op: "append", value: {...}}`. `append_review_log` → use `{target: "meta.review_log", op: "append", value: {...}}`. These will be removed in v0.0.4.
- Clarify: the interview display of AI-generated `value` is the AI's self-declaration; the `skill_refine` Before/After diff is the human authorization gate.

**`ddo/skills/ddo-refine.md`:**
- Update Before/After diff section: structural ops produce multi-line diffs (added/removed YAML objects); display verbatim.
- Add: if refine reports `DanglingRefError`, output the `.paths` list and instruct the interview agent to issue `set` patches to remove refs first, then retry the delete.

### 5.2 Resolved Trade-offs Log

| RT # | Sev | Finding | Resolution |
|---|---|---|---|
| RT-v0.0.3-1 | Crit | `validate()` warns (not fails) on duplicate evidence_bank IDs; RT-v0.0.3-2 may be unresolved | **MOOT (code confirmed)**: `validation.py:91` raises `ValidationError` on duplicate IDs. Architecture node description "orphans warn, not fail" describes orphaned/unreferenced entries only, not duplicates. RT-v0.0.3-2 is valid as-written. No code change needed. |
| RT-v0.0.3-2 | Crit | Negative `at` values (`at: -1`) not rejected; Python silently inserts at wrong position | **RESOLVED**: Add explicit `at < 0` rejection + `bool` subclass guard + `int` type enforcement in both `validate_interview_log` and `apply_patches` bounds check. See §5.1 `at` field type constraint. |
| RT-v0.0.3-3 | Major | `apply_patches` atomicity unspecified; mid-batch exception may leave partial mutations | **MOOT (code confirmed)**: `refine.py:245` already does `copy.deepcopy(data)` at function entry. Invariant stated explicitly in §5.1. No code change needed. |
| RT-v0.0.3-4 | Major | Sequential-index invalidation in multi-op batches (insert shifts indices; later delete targets wrong element) | **ACCEPTED with mitigation**: Add `skill_interview` warning against same-parent-list multi-index batches. Add one unit test documenting the shift behavior. No batch-level rejection. Single-user HITL diff gate is the primary safety net. |
| RT-v0.0.3-5 | Major | `test_review_unit` omitted from blast radius | **RESOLVED**: Add `test_review_unit` to blast radius. At least 4 new test cases: `append` accepted, `delete` accepted, `insert` accepted (with valid `at`), `insert` without `at` rejected, `delete` with `value` rejected, negative `at` rejected. |
| RT-v0.0.3-6 | Minor | Section→evidence asymmetry: deleting a section leaves orphaned evidence IDs unguarded | **ACCEPTED (known gap)**: Guard is evidence→section only per scope. `validate()` warns on orphans post-delete but does not fail. Documented in §3 Known Gaps; addressed in v0.0.4+. |
| RT-v0.0.3-7 | Minor | NC-11 wording contradicts itself ("DO NOT apply nested list ops" then says the example is NOT an error) | **RESOLVED**: Rewritten as NC-11 in §6. |
| RT-v0.0.3-8 | Minor | Execution checklist allows agent to self-promote structural fixture | **RESOLVED**: Step 10a added — explicit HITL gate; human reviews fixture before `DDO_FIXTURE_SIGNOFF=1`. See §5.4 checklist. |
| RT-v0.0.3-9 | Minor | Negative path indices (`evidence_bank[-1]`) not addressed in path parser | **RESOLVED**: NC-13 added — path index brackets `\d+` only. Parser rejects `[-1]`, `[*]`, expressions. |
| RT-v0.0.3-10 | Minor | `DanglingRefError` format unspecified; `skill_refine` cannot parse it | **RESOLVED**: `DanglingRefError` defined with `.paths: list[str]` attribute. See §5.1. |
| RT-v0.0.3-11 | Minor | Step 16 only updates `refine_engine`; 4+ other nodes need hypergraph updates | **RESOLVED**: Step 16 expanded to 5 nodes. See §5.4. |
| RT-v0.0.3-12 | Minor | `bool` is subclass of `int`; `at: True/False` passes `isinstance(at, int)` | **RESOLVED**: Guard includes `not isinstance(at, bool)`. See §5.1. |
| RT-v0.0.3-13 | Minor | Legacy ops (`append_evidence`, `append_review_log`) fate unresolved | **RESOLVED (user)**: Keep both coexisting in v0.0.3. Mark deprecated in `skill_interview`. Remove in v0.0.4. |

### 5.3 Blast Radius

**Definite changes (7 nodes):**
- `refine_engine` (`ddo/refine.py`) — `DanglingRefError`, `_dangling_ref_check`, `apply_patches` extension, path parser extension
- `review_engine` (`ddo/review.py`) — `validate_interview_log` op enum + `at` field validation
- `skill_interview` (`ddo/skills/ddo-interview.md`) — structural patch syntax, sequential-index warning, legacy op deprecation
- `skill_refine` (`ddo/skills/ddo-refine.md`) — structural op Before/After diff, `DanglingRefError` display
- `test_refine_unit` (`tests/unit/test_refine.py`) — new unit tests + update "delete is unknown op" test
- `test_review_unit` (`tests/unit/test_review.py`) — new unit tests for op enum + `at` field validation
- `test_loop_integration` (`tests/integration/test_loop.py`) — parametrization + new structural fixture

**New artifacts (3 nodes):**
- `dangling_ref_guard` — new Atomic child node of `refine_engine` in `architecture.yml` (the `_dangling_ref_check` helper + `DanglingRefError`)
- `interview_log_v1_structural` — new Atomic node under `tests_integration` in `architecture.yml`
- `interview_log_v1` + `document_data_with_gap` — v0.0.2 loop fixture nodes (pre-condition; must be authored before structural fixture)

**Not touched:**
- `build_orchestrator`, `validation_gate`, `path_deriver`, `ingest_helpers`
- `ddo_templates`, `ddo_schemas`, `ddo_personas`
- All render tests, ingest tests, validation tests
- `ddo/validation.py` — NC-8 preserved

### 5.4 Execution Checklist

**PRE-CONDITION: Author v0.0.2 loop fixtures (blocks everything else)**
0. Author `tests/fixtures/loop/document_data_with_gap.yaml` (minimum: 3+ evidence entries, 2+ content sections, 1+ sentinel gap) as a candidate artifact. Present to human for character-by-character review. Do not proceed until human approves. Author `tests/fixtures/loop/interview_log_v1.yaml` (a `set` patch resolving the sentinel gap) as a candidate artifact. Present for review. **HITL GATE: human sets `DDO_FIXTURE_SIGNOFF=1` and confirms `test_gap_closing_pass` passes before proceeding to step 1.**

**v0.0.3 implementation:**
1. Read `ddo/refine.py` — map existing path parser (`parse_path`), `apply_patches` function, and current op branches.
2. Read `ddo/review.py` — map `validate_interview_log` (currently validates decision + patch presence, does NOT validate op type).
3. Read `tests/unit/test_refine.py` — identify where new test cases plug in; note line ~345 "unknown op" test using `"delete"` must be updated.
4. Read `tests/unit/test_review.py` — identify existing validate_interview_log tests.
5. Read `tests/integration/test_loop.py` — understand fixture loading and `tmp_path` isolation pattern.
6. Implement `DanglingRefError` class in `ddo/refine.py`.
7. Implement `_dangling_ref_check(doc, index)` in `ddo/refine.py`.
8. Extend path parser in `ddo/refine.py` to handle `append`/`delete`/`insert` path grammar + NC-13 character whitelist.
9. Extend `apply_patches` in `ddo/refine.py` with three new op branches (`append`, `delete`, `insert`).
10. Update `validate_interview_log` in `ddo/review.py` with new op enum + `at` field rules.
10a. **HITL GATE**: Design `tests/fixtures/loop/interview_log_v1_structural.yaml` (content: one `append` to `evidence_bank`, one non-dangling `delete` from `evidence_bank`, one `insert` into `content.sections`). Present to human for character-by-character review. Do NOT proceed to step 11 until human confirms all three ops are syntactically correct, schema-valid, and produce intended mutations.
11. Write new unit tests in `tests/unit/test_refine.py` (see MiniPRD_TestRefineUnit).
11a. Update the existing "delete is unknown op" test (line ~345) — change the unknown op string from `"delete"` to `"replace"`.
12. Write new unit tests in `tests/unit/test_review.py` (see MiniPRD_TestReviewUnit).
13. Parametrize `test_loop_integration` in `tests/integration/test_loop.py` over both fixtures.
14. Update `ddo/skills/ddo-interview.md`.
15. Update `ddo/skills/ddo-refine.md`.
14a. **Verify no existing tests were deleted or weakened**: run `git diff tests/unit/` — confirm only additions and the one targeted line update at ~345.
16. Run `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .` — all must exit 0.
17. Human sets `DDO_FIXTURE_SIGNOFF=1` and runs `uv run pytest tests/integration/test_loop.py` — both parametrized cases must pass.
18. Run: `python .agents/scripts/hypergraph_updater.py spec/compiled/architecture.yml refine_engine review_engine skill_interview skill_refine dangling_ref_guard`.
19. **M7 manual test**: run `ddo-interview` + `ddo-refine` with a structural finding (append to `evidence_bank`) end-to-end; verify Before/After diff and committed mutation.
20. **M8 manual test**: attempt to delete a referenced `evidence_bank` entry via `ddo-refine`; verify refine refuses with `DanglingRefError` listing the ref path(s).

### 5.5 Dependencies

- No new runtime Python packages.
- `ddo.refine` depends on `ddo.validation` (unchanged) and `ddo.paths` (unchanged).
- `DanglingRefError` and `_dangling_ref_check` are internal to `ddo.refine` (no cross-module dep).

---

## 6. Negative Constraints

1. **DO NOT** implement type-changing `set` (scalar → list, list → scalar).
2. **DO NOT** auto-vivify a list that doesn't exist at the target path for `append`/`insert`.
3. **DO NOT** cascade-delete dangling refs when an `evidence_bank` entry is deleted — refuse with `DanglingRefError`.
4. **DO NOT** allow `value` field on `delete` patches (rejected with error before mutation).
5. **DO NOT** allow `at` field on `set`/`append`/`delete` patches.
6. **DO NOT** allow `[N]`-terminated `target` for `append` or `insert` (must point to the list, not an element).
7. **DO NOT** use `eval` or dynamic code execution in the path parser (inherited from v0.0.2).
8. **DO NOT** modify `validate()` in `ddo/validation.py` — it is the post-mutation gate and must remain unchanged.
9. **DO NOT** relax the single-user/no-concurrency invariant.
10. **DO NOT** add a second HITL confirmation step for structural ops — the existing Before/After diff gate is sufficient.
11. The `value` field may contain nested lists and dicts; the structural patch operation modifies **only the outermost target list**. Nested list content within `value` is plain YAML data, not interpreted as further patch ops.
12. **DO NOT** extend the DanglingRefError guard beyond `evidence_bank` deletions in v0.0.3.
13. **DO NOT** accept path segment keys outside `[a-zA-Z_][a-zA-Z0-9_]*` or index brackets outside `\d+` (no negative sign, no expressions, no slices).

---

## 7. Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `ddo-interview` AI generates malformed structural `value` (wrong schema, missing required keys) | Medium | Medium | `validate()` post-mutation catches schema violations; refine refuses to commit |
| `insert at: N` where `N == len(list)` treated inconsistently with `append` | Low | Low | Spec defines `at: len(list)` ≡ `append`; unit test asserts identical output |
| DanglingRefError guard misses an indirect reference (sentinel string, nested ref) | Low | High | Guard only scans direct `content.sections[*].evidence[]` lists; sentinel strings never match valid IDs (correct by design); indirect refs are v0.0.4+ concern |
| Sequential-index invalidation in multi-op batches | Medium | Medium | `skill_interview` warns against same-parent-list multi-index batches; unit test documents the shift behavior; HITL diff gate shows actual result |
| `_dangling_ref_check` called on unvalidated document raises KeyError | Low | Low | Use `dict.get()` with empty defaults throughout `_dangling_ref_check`; add test for malformed-doc input |
| Fixture self-promotion bypasses Candidate Artifact protocol | Low | High | Step 10a HITL gate: human reviews fixture before `DDO_FIXTURE_SIGNOFF=1`; `fixture_signoff_guard.py` enforces env var but not human presence — human discipline is the control |
| `validate_interview_log` too strict / too permissive on new op types | Medium | Medium | Dedicated unit tests for all valid and invalid op + field combinations (see MiniPRD_TestReviewUnit) |

---

## 8. Success Metrics

1. **M1**: `uv run pytest` exits 0 with all tests existing at implementation time passing + new structural op tests (≥ 7 new unit tests across `test_refine.py` + `test_review.py`).
2. **M2**: Human sets `DDO_FIXTURE_SIGNOFF=1` and runs `uv run pytest tests/integration/test_loop.py` — both parametrized cases exit 0.
3. **M3**: `uv run ruff check . && uv run ruff format --check .` exit 0.
4. **M4**: `validate_interview_log` rejects all invalid combinations: `set` with `at` field, `delete` with `value`, `insert` without `at`, `insert` with `at: -1`, `insert` with `at: True`, `append` with `[N]`-terminated target.
5. **M5**: `apply_patches` with a mid-batch `DanglingRefError` returns the original input dict unchanged (atomicity regression test).
6. **M6**: Manual end-to-end run of `ddo-interview` + `ddo-refine` with a structural finding (append to `evidence_bank`) completes with visible Before/After diff and committed mutation.
7. **M7**: Manual test of DanglingRefError guard: attempt to delete a referenced `evidence_bank` entry → refine refuses with structured error listing the ref path(s).

---

*SuperPRD generated by Resolution Agent (hyper-resolve) — 2026-06-30. MiniPRDs: RefineEngine, ReviewEngine, SkillInterview, SkillRefine, TestRefineUnit, TestReviewUnit, TestLoopIntegration.*
