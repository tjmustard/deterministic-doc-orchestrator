# Draft PRD: DDO v0.0.3 — Structural Patch DSL Expansion

**Version:** 0.1.0 (Draft)
**Date:** 2026-06-29
**Status:** Draft — ready for Red Team
**Author:** Architect Agent (hyper-architect v0.0.3)

---

## 1. Introduction & Goals

### Problem Statement
The `ddo-refine` patch DSL introduced in v0.0.2 only supports `set` on leaf-scalar fields (strings, integers, booleans). This blocks the AI interview agent from repairing an entire class of legitimate Red Team findings: those requiring structural mutations — adding a new evidence entry, removing a stale claim, inserting a new document section. When a finding calls for a structural change, the only available workarounds are:
1. The agent generates a `set` on a serialized string representation (wrong — not a valid schema value)
2. The human manually edits `document_data.yaml` outside the pipeline (breaks the YAML-is-sole-source-of-truth invariant)
3. The finding is deferred indefinitely (reduces quality of the final document)

### Solution Overview
Extend `ddo/refine.py`'s `apply_patches` function and the associated path-DSL parser to support three new operation types: `append`, `delete`, and `insert`. Update `ddo-interview` and `ddo-refine` skills to generate and display these operations. Add a dangling-reference guard for `delete` operations. Add a new signed-off integration fixture.

### Target Audience
- Solo human author/reviewer using the DDO pipeline
- AI interview agent (`ddo-interview` skill) that generates patch batches
- AI refine agent (`ddo-refine` skill) that applies patches and commits

---

## 2. Confidence Mandate

**Score: 8/10** (pre-Red Team)

Clarifying questions resolved:
- Operations in scope: ✅ `append`, `delete`, `insert at N`
- Delete safety model: ✅ refuse with dangling-ref error (no cascade)
- Insert position encoding: ✅ separate `at: N` field in patch schema
- Actor model: ✅ unchanged (single-user, no concurrency)
- Novel frontier: ✅ existing Before/After diff gate covers AI-generated values
- Integration fixture strategy: ✅ new parametrized fixture alongside existing `interview_log_v1.yaml`

Residual uncertainty (Red Team targets):
- Interaction between `insert` at index N and out-of-bounds N (N > len(list))
- Behavior when `append`/`insert` value violates the evidence_bank reference constraint (ID collision)
- Whether `ddo-interview` skill reliably generates correct complex `value` YAML for nested structures

---

## 3. Scope

### In-Scope

1. **`append` operation** — add a new element to the end of a list-typed field at the specified path.
2. **`delete` operation** — remove the element at a specific index from a list-typed field. Path must end in `[N]`.
3. **`insert` operation** — insert a new element at position `at: N` within a list-typed field at the specified path.
4. **Dangling-ref guard for `delete`** — if a `delete` targets an `evidence_bank[N]` entry whose ID is still referenced by any `content.sections[*].evidence[]` entry, refuse with a structured error listing all dangling paths. The guard only applies to `evidence_bank` deletions (the only reference-integrity constraint in the current schema).
5. **`review_engine.validate_interview_log` update** — accept new op types (`append`, `delete`, `insert`) and the optional `at` field on patch entries.
6. **`skill_interview` update** — cognitive instructions for generating correct structural patch syntax.
7. **`skill_refine` update** — cognitive instructions for showing structural ops in Before/After diff and handling dangling-ref errors.
8. **New integration fixture** — `tests/fixtures/loop/interview_log_v1_structural.yaml` exercising all three ops; promoted under `DDO_FIXTURE_SIGNOFF=1`.
9. **Parametrized loop test** — `test_loop_integration` runs both the existing `interview_log_v1.yaml` case and the new structural fixture case.

### Out-of-Scope (explicit deferrals)

- **Type-changing `set`** — changing a scalar to a list/dict or vice versa remains blocked.
- **Auto-vivify for `append`/`insert`** — the target list must already exist at the path. No new key creation.
- **Cascade deletion of dangling refs** — refuse only; agent must fix refs first.
- **Nested list operations within a single patch** — e.g., appending to a list within the `value` of an `append` patch is not supported in one atomic patch.
- **Non-evidence-bank reference integrity** — the dangling-ref guard applies only to `evidence_bank` deletions, not to arbitrary cross-references in `content.sections`.
- **`review_history/` cap/prune** — remains deferred to v0.0.4+.
- **Composite `ddo-run` macro** — remains deferred.
- **New document types** — remains deferred.
- **File locking / multi-user** — single-user/no-concurrency invariant unchanged.

---

## 4. User Stories

### US-1: Append a new evidence_bank entry
**As** an AI interview agent,
**I want** to generate an `append` patch targeting `evidence_bank`,
**So that** I can resolve a finding like "insufficient evidence for claim X" by adding a new source entry to the evidence bank.

**Acceptance Criteria:**
- Patch `{path: "evidence_bank", op: "append", value: {id: "eN", type: "...", content: "...", source: "..."}}` applies successfully.
- The appended element appears at index `len(evidence_bank)` in the mutated `document_data.yaml`.
- Full `validate()` runs post-mutation and passes before commit.
- `document_data_pre_vN.yaml` snapshot is taken before mutation.
- Patch with `op: "append"` and a `[int]`-terminated path (ambiguous) is rejected with a clear error.

**Priority:** P0

---

### US-2: Delete a stale list element
**As** an AI interview agent,
**I want** to generate a `delete` patch targeting `evidence_bank[N]` or `content.sections[N].claims[M]`,
**So that** I can remove an obsolete or incorrect element from any list-typed field.

**Acceptance Criteria:**
- Patch `{path: "evidence_bank[2]", op: "delete"}` removes element at index 2 (zero-based), shifts higher-index elements down.
- `value` field is ignored/forbidden for `delete` ops (rejected with error if present).
- Out-of-bounds index (N ≥ len(list)) raises a clear error; document is not mutated.
- Full `validate()` runs post-mutation and passes before commit.
- `document_data_pre_vN.yaml` snapshot is taken before mutation.

**Priority:** P0

---

### US-3: Dangling-ref guard on evidence_bank delete
**As** a human reviewer,
**I want** the refine engine to refuse a `delete` on an `evidence_bank[N]` entry that is still referenced by any `content.sections[*].evidence[]` list,
**So that** the pipeline never silently produces a document with broken evidence references.

**Acceptance Criteria:**
- If `evidence_bank[N].id` appears in any `content.sections[K].evidence[M]`, the patch is rejected before any mutation.
- The error output lists every referencing path in structured form (e.g., `content.sections[0].evidence[1]`).
- `document_data.yaml` and the snapshot file are not written on rejection.
- Deleting an `evidence_bank` entry whose ID is NOT referenced proceeds normally (US-2).
- The guard applies ONLY to `evidence_bank` deletions; deleting from `content.sections[N].claims` or other lists has no ref-check.

**Priority:** P0

---

### US-4: Insert at a specific index
**As** an AI interview agent,
**I want** to generate an `insert` patch with a target list path and `at: N` field,
**So that** I can add a new element at a specific position (e.g., prepend a new section, insert a claim before index 2).

**Acceptance Criteria:**
- Patch `{path: "content.sections", op: "insert", at: 2, value: {...}}` inserts the element at index 2; existing elements at index ≥ 2 shift up.
- `at: 0` inserts at the front; `at: len(list)` is equivalent to `append`.
- `at: N` where N > len(list) is rejected with a clear bounds error; document is not mutated.
- `at` field is required for `op: "insert"`; missing `at` is a validation error on the patch itself (rejected before mutation).
- Full `validate()` runs post-mutation and passes before commit.
- `document_data_pre_vN.yaml` snapshot is taken before mutation.

**Priority:** P1

---

### US-5: Interview skill generates structural patch syntax
**As** a human reviewer,
**I want** the `ddo-interview` skill to automatically generate correct `append`/`delete`/`insert` patch syntax when a Red Team finding calls for structural changes,
**So that** I don't need to hand-craft YAML for structural repairs.

**Acceptance Criteria:**
- When a finding's resolution requires adding an element, the skill generates `op: "append"` or `op: "insert"` with a complete, schema-valid `value`.
- When a finding's resolution requires removing an element, the skill generates `op: "delete"` with the correct `[N]`-terminated path.
- The skill notes that structural `value` content is AI-generated and explicitly shows the full `value` in the decision prompt for human review.
- Skill instructions clarify the dangling-ref risk for `delete` on `evidence_bank` entries (agent should patch refs first).

**Priority:** P1

---

### US-6: Integration test coverage for structural ops
**As** a developer,
**I want** the loop integration test to exercise at least one `append`, one `delete`, and one `insert` patch through the full refine pipeline,
**So that** structural op regressions are caught before merge.

**Acceptance Criteria:**
- `tests/fixtures/loop/interview_log_v1_structural.yaml` exists and is promoted under `DDO_FIXTURE_SIGNOFF=1`.
- `test_loop_integration` is parametrized with both `interview_log_v1.yaml` (existing) and `interview_log_v1_structural.yaml` (new).
- The structural fixture case passes all existing loop test assertions: no sentinels, `validate()`-clean, 3-format render success.
- The structural fixture is built against the existing `document_data_with_gap.yaml` base document.

**Priority:** P1

---

## 5. Technical Specifications

### 5.1 Architecture

#### Patch DSL Schema (interview_log_vN.yaml)

Extended op enum and patch entry fields:

```yaml
# Existing (unchanged)
- path: "meta.version"
  op: "set"
  value: "0.2.0"

# New: append
- path: "evidence_bank"
  op: "append"
  value:
    id: "e5"
    type: "claim"
    content: "Supporting evidence text"
    source: "User review 2026-06-29"

# New: delete (path ends in [N])
- path: "evidence_bank[2]"
  op: "delete"
  # value field absent or forbidden

# New: insert (at: N required)
- path: "content.sections"
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
| op | Path form | `at` field | `value` field |
|---|---|---|---|
| `set` | dotted + optional `[N]` | forbidden | required (scalar) |
| `append` | dotted, no trailing `[N]` | forbidden | required (any YAML) |
| `delete` | dotted + required trailing `[N]` | forbidden | forbidden |
| `insert` | dotted, no trailing `[N]` | required (int ≥ 0) | required (any YAML) |

#### ddo/refine.py changes

1. **Path parser extension** — the existing hand-rolled parser already handles dotted + `[N]`. Extend to:
   - For `append`/`insert`: validate path resolves to a list; reject if path ends in `[N]`.
   - For `delete`: validate path ends in `[N]`; resolve parent list + index.

2. **`apply_patches` extension** — three new branches after the existing `set` branch:
   - `append`: navigate to list, `list.append(value)`.
   - `delete`: navigate to parent list, `_dangling_ref_check(doc, path, index)`, `list.pop(index)`.
   - `insert`: navigate to list, validate `at <= len(list)`, `list.insert(at, value)`.

3. **`_dangling_ref_check(doc, evidence_bank_path, index)` helper** — only invoked for `delete` on paths that resolve to `evidence_bank`:
   - Extract `id = doc["evidence_bank"][index]["id"]`
   - Scan all `doc["content"]["sections"][*]["evidence"]` lists for the id
   - If any refs found: raise `DanglingRefError` with structured list of paths

4. **Purity invariant preserved** — `apply_patches` remains a pure function (no I/O). All new branches operate on the in-memory document dict.

5. **`refine_structural_check` update** — existing structural check validates list-typed fields remain lists after mutation. No changes needed (validation gate + structural check already cover this).

#### ddo/review.py changes

`validate_interview_log` update:
- Accept `op` values: `"set"`, `"append"`, `"delete"`, `"insert"` (currently only `"set"` passes)
- Accept optional `at` field on patch entries (integer ≥ 0, required when `op == "insert"`, forbidden otherwise)
- Reject `value` field on `delete` ops
- Reject `at` field on `set`/`append`/`delete` ops

#### Skill updates

**`ddo/skills/ddo-interview.md`:**
- Add section: "Structural Patch Syntax" — when a finding requires list mutation, use `append`/`delete`/`insert` with the schemas above
- Add note: for `delete` on any `evidence_bank[N]` entry, check if the ID is referenced in `content.sections[*].evidence[]` and patch refs first (separate patch entries)
- Add note: `value` content in `append`/`insert` is AI-generated; display the full value to the human in the decision prompt

**`ddo/skills/ddo-refine.md`:**
- Update Before/After diff section: structural ops produce multi-line diffs (added/removed YAML objects); display as-is
- Add: if refine reports `DanglingRefError`, output the error and prompt the interview agent to fix refs first

### 5.2 Resolved Trade-offs

| # | Finding | Resolution |
|---|---|---|
| RT-v0.0.3-1 | Insert out-of-bounds (at > len) | Reject with bounds error; document not mutated |
| RT-v0.0.3-2 | Append/insert value ID collision in evidence_bank | Post-mutation `validate()` catches duplicate IDs (existing reference integrity check) |
| RT-v0.0.3-3 | Dangling-ref cascade vs refuse | Refuse with structured error (fail-closed; mirrors no-auto-vivify invariant) |
| RT-v0.0.3-4 | Insert `at` encoding in path vs separate field | Separate `at: N` field (path grammar stays unambiguous) |
| RT-v0.0.3-5 | Novel frontier for AI-generated values | Existing Before/After diff HITL gate is sufficient; no new Candidate Artifact protocol |

### 5.3 Blast Radius

**Definite changes (6 nodes):**
- `refine_engine` (`ddo/refine.py`) — core patch application + dangling-ref guard
- `skill_refine` (`ddo/skills/ddo-refine.md`) — cognitive node update
- `skill_interview` (`ddo/skills/ddo-interview.md`) — structural patch generation instructions
- `review_engine` (`ddo/review.py`) — `validate_interview_log` op enum + `at` field
- `test_refine_unit` (`tests/unit/test_refine.py`) — new unit tests
- `test_loop_integration` (`tests/integration/test_loop.py`) — parametrized

**New artifacts (2 nodes):**
- `tests/fixtures/loop/interview_log_v1_structural.yaml` — new signed-off fixture (Atomic node)
- Architecture node for `dangling_ref_guard` helper (Atomic node within `refine_engine`)

**Not touched:**
- `build_orchestrator`, `validation_gate`, `path_deriver`, `ingest_helpers`
- `ddo_templates`, `ddo_schemas`, `ddo_personas`
- All render tests, ingest tests, validation tests

### 5.4 Execution Checklist

1. Read current `ddo/refine.py` — map existing path parser and `apply_patches` function
2. Read current `ddo/review.py` — map `validate_interview_log` schema
3. Read current `tests/unit/test_refine.py` — identify where new test cases plug in
4. Read current `tests/integration/test_loop.py` + `tests/fixtures/loop/document_data_with_gap.yaml` — understand fixture structure before designing new structural fixture
5. Implement `_dangling_ref_check` in `ddo/refine.py`
6. Extend path parser for `append`/`delete`/`insert` path validation rules
7. Extend `apply_patches` with three new op branches
8. Update `validate_interview_log` in `ddo/review.py`
9. Write new unit tests in `tests/unit/test_refine.py`
10. Design `tests/fixtures/loop/interview_log_v1_structural.yaml` (content: one append + one delete on a non-referenced entry + one insert)
11. Parametrize `test_loop_integration`
12. Update `ddo/skills/ddo-interview.md`
13. Update `ddo/skills/ddo-refine.md`
14. Run `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`
15. Run `DDO_FIXTURE_SIGNOFF=1 uv run pytest tests/integration/test_loop.py` to promote structural fixture
16. Run `python .agents/scripts/hypergraph_updater.py spec/compiled/architecture.yml refine_engine` (and affected nodes)

### 5.5 Dependencies

- No new runtime Python packages
- `ddo.refine` depends on `ddo.validation` (validate() — unchanged)
- `ddo.refine` depends on `ddo.paths` (path containment — unchanged)
- New `_dangling_ref_check` is internal to `ddo.refine` (no cross-module dep)

---

## 6. Negative Constraints

1. **DO NOT** implement type-changing `set` (scalar → list, list → scalar)
2. **DO NOT** auto-vivify a list that doesn't exist at the target path for `append`/`insert`
3. **DO NOT** cascade-delete dangling refs when an `evidence_bank` entry is deleted — refuse with error
4. **DO NOT** allow `value` field on `delete` patches
5. **DO NOT** allow `at` field on `set`/`append`/`delete` patches
6. **DO NOT** allow `[N]`-terminated paths for `append` or `insert` (ambiguous; must point to the list)
7. **DO NOT** use `eval` or dynamic code execution in the path parser (invariant from v0.0.2)
8. **DO NOT** modify `validate()` in `ddo/validation.py` — it is the post-mutation gate and must remain unchanged
9. **DO NOT** relax the single-user/no-concurrency invariant
10. **DO NOT** add a second HITL confirmation step for structural ops — the existing Before/After diff is sufficient
11. **DO NOT** apply nested list operations within a single patch (e.g., appending to a list inside an `insert` value is not a structural op error — it's valid YAML in the `value`; the patch itself only inserts one element)
12. **DO NOT** extend the dangling-ref guard beyond `evidence_bank` deletions in v0.0.3

---

## 7. Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `ddo-interview` AI generates malformed structural `value` (wrong schema, missing required keys) | Medium | Medium | `validate()` post-mutation catches schema violations; refine refuses to commit |
| Insert `at: N` = `len(list)` treated inconsistently with `append` | Low | Low | Spec explicitly defines `at: len(list)` ≡ `append`; unit test asserts this |
| Dangling-ref guard misses an indirect reference (e.g., sentinel string, nested ref) | Low | High | Guard only scans the direct `content.sections[*].evidence[]` list; indirect refs are a v0.0.4+ concern |
| `validate_interview_log` too strict / too permissive on new op types | Medium | Medium | Dedicated unit tests for all valid and invalid op + field combinations |
| Structural fixture fails to sign off due to complex nested value | Low | Medium | Design fixture value as minimal valid schema (e.g., append a minimal evidence entry with all required fields) |

---

## 8. Success Metrics

1. `uv run pytest` exits 0 with all existing 111 tests passing + new structural op tests
2. `DDO_FIXTURE_SIGNOFF=1 uv run pytest tests/integration/test_loop.py` exits 0 with both parametrized cases
3. `uv run ruff check . && uv run ruff format --check .` exit 0
4. A manual end-to-end run of `ddo-interview` + `ddo-refine` with a structural finding (append to evidence_bank) completes successfully with a visible Before/After diff and committed mutation
5. A manual test of dangling-ref guard: attempt to delete a referenced `evidence_bank` entry → refine refuses with structured error listing the ref path(s)

---

*Draft PRD generated by hyper-architect v0.0.3 — 2026-06-29. Ready for /hyper-redteam in a new conversation.*
