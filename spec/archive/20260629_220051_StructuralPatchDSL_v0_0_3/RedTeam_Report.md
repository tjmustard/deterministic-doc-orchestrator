# Red Team Report: DDO v0.0.3 — Structural Patch DSL Expansion

**Target:** `spec/active/Draft_PRD.md`  
**Red Team Date:** 2026-06-29  
**Architecture Reference:** `spec/compiled/architecture.yml`  
**Reviewer:** Red Team Agent (hyper-redteam)

---

## Executive Summary

The PRD is structurally sound and the scope is well-bounded. However, six vulnerabilities warrant action before implementation:

1. **Critical** — `validate()` warns (not fails) on duplicate evidence IDs; this directly breaks RT-v0.0.3-2's resolution and could allow silent ID collisions on `append`.
2. **Critical** — Negative `at` values (`at: -1`) are not rejected; Python's `list.insert(-1, x)` silently inserts at the wrong position.
3. **Major** — Batch atomicity is asserted but not specified: the deep-copy-at-entry invariant must be explicit or a mid-batch exception could corrupt state.
4. **Major** — Sequential-index invalidation in multi-op batches: a batch with `insert evidence_bank at: 0` followed by `delete evidence_bank[2]` will target a different element than the AI intended.
5. **Major** — `test_review_unit` is omitted from the blast radius; adding new op types to `validate_interview_log` requires new unit tests in that file.
6. **Minor** — Negative path indices (`evidence_bank[-1]`) are not addressed in the path parser; Python silently accepts them.

---

## Section 1 & 2: Introduction, Goals & Confidence Mandate

### [Introduction] Analysis

* **Clarifying Questions:**
  - The PRD describes the only available workaround when the agent faces a structural finding as either a malformed `set` patch, a manual edit, or indefinite deferral. But there is a fourth path: the interview skill's `append_evidence` and `append_review_log` operations already exist in v0.0.2 (per the `refine_engine` architecture node). Are these two legacy ops being subsumed by the new generic `append`, deprecated, or left as coexisting special cases? If they coexist, the `validate_interview_log` op enum expansion will need to keep them. If they are subsumed, every existing test that generates `op: "append_evidence"` will break.
  - The problem statement frames workaround (2) as "breaks the YAML-is-sole-source-of-truth invariant." But a human manually editing `document_data.yaml` is explicitly the HITL override path the pipeline was designed to support. Is this framing intentional — meaning the AI patch path must replace manual edits — or is manual editing still an acceptable escape hatch for complex structural mutations?

* **What-If Scenarios:**
  - What if the Architect's three workarounds are used concurrently? A human manually edits `document_data.yaml` at the same time the interview agent is generating structural patches. Since the single-user invariant is preserved (NC-9), this is "impossible by design" — but there is no file-level lock or dirty-check between snapshot time and commit time. If a human edits the file after `snapshot_source` runs but before `commit_refine` writes, the snapshot will not represent the pre-patch state of the actual committed file.
  - The confidence score of 8/10 acknowledges residual uncertainty in `insert` out-of-bounds and `append`/`insert` ID collision. But a third residual uncertainty — **negative `at` values** — is not listed. `at: -1` would NOT be caught by the current bounds check (`N > len(list)`) because `-1 > len(list)` is always false. Python's `list.insert(-1, x)` silently inserts before the last element.

* **Points for Improvement:**
  - Add explicit clarification of the `append_evidence`/`append_review_log` legacy op fate (deprecated, aliased, or coexisting) to §5.2 Resolved Trade-offs.
  - Add `at < 0` to residual uncertainty list and to the bounds-check spec in §5.1.
  - Add a snapshot-staleness note: commit_refine should assert that `document_data.yaml` has not been modified between snapshot and commit (mtime or content hash check).

---

## Section 3: Scope

### [Scope] Analysis

* **Clarifying Questions:**
  - The dangling-ref guard applies only to `evidence_bank` deletions. The out-of-scope list defers "Non-evidence-bank reference integrity" to v0.0.4+. But the symmetric risk is also present: **what stops the AI from deleting `content.sections[N]` where that section's evidence list references valid IDs?** After the delete, the evidence IDs remain in `evidence_bank` as orphans. The validate() gate description says "orphans warn, not fail." So an AI could delete the only section that uses `e3`, and the pipeline would silently produce a document with an orphaned evidence entry. This is not a DanglingRefError in the evidence→section direction; it's the opposite direction (section→evidence), which the guard explicitly doesn't cover. The PRD should acknowledge this asymmetry as a known gap.
  - "The target list must already exist at the path (no auto-vivify)" — what error type is raised? The existing `parse_path` would return a path segment list; the navigation would fail when a key is missing. Is this a `KeyError` surfaced raw, a `PathNotFoundError`, or a `ValidationError`? Distinguishing "wrong path" from "list does not exist yet" matters for the AI skill's error-recovery loop.

* **What-If Scenarios:**
  - **Index invalidation from same-batch operations:** A batch containing `insert content.sections at: 0` (shifts all section indices up) followed by `delete content.sections[2]` in the same batch would, under sequential execution, delete what was originally `content.sections[1]` (now at index 2 post-insert). If the AI authored the batch assuming a specific starting state (original index 2), the delete targets the wrong element. This is the most dangerous class of silent semantic bug in this PRD and is not addressed anywhere.
  - **Deleting the only section in `content.sections`:** If the interview skill generates a `delete content.sections[0]` on a document with a single section, `validate()` runs post-mutation. Does `validate()` enforce a minimum section count? The `refine_structural_check` checks "sections remains a list" but not "sections is non-empty." A document with an empty `content.sections` list could pass validate() and render as a blank-body artifact — a zero-error pipeline producing a zero-content document.

* **Points for Improvement:**
  - Add a minimum-length guard: reject any `delete` that would leave `content.sections` empty (either in `apply_patches` or in `refine_structural_check`).
  - Define a `PathNotFoundError` (or equivalent) distinct from `DanglingRefError` and bounds errors, so skill error messages are actionable.
  - Add an explicit "known asymmetry" note: the guard is evidence→section only; section deletion leaving orphaned evidence IDs is not guarded (warn at validate() level only).

---

## Section 4: User Stories

### [US-1: Append] Analysis

* **Clarifying Questions:**
  - AC5 states: "Patch with `op: 'append'` and a `[int]`-terminated path (ambiguous) is rejected with a clear error." But the path `evidence_bank[0]` resolves to a specific dict element, not a list. The rejection reason should be "path resolves to a non-list type" rather than "path grammar violation" — these two errors are distinguishable at navigation time. Are both error reasons in scope, or only the grammar-level one?
  - What constitutes a valid `value` for `evidence_bank` append? The schema requires `id`, `type`, `content`, `source`. If the AI generates an extra field (`url`, `relevance_score`), does `validate()` enforce strict schema conformance (reject extra keys) or only check for required keys? If extra keys pass silently, the evidence_bank could accumulate non-standard entries that break future tooling.

* **What-If Scenarios:**
  - **CRITICAL: Duplicate ID silent pass.** RT-v0.0.3-2 is resolved by: "post-mutation `validate()` catches duplicate IDs." But the `validation_gate` architecture node states: "evidence-bank uniqueness: **orphans warn, not fail**." If `validate()` only WARNS on duplicate IDs (returns without raising), then a malformed AI-generated append with a colliding ID would silently succeed. This is a direct contradiction between the resolved trade-off table and the architecture node description. One of them must be wrong. The PRD cannot rely on validate() for ID collision prevention unless the behavior is confirmed to raise (not warn) on duplicates.
  - **Append a new section with evidence referencing a non-existent ID:** `append content.sections with value: {evidence: ["e_nonexistent"]}`. validate() would catch this — but only AFTER the snapshot has been taken. The snapshot would capture a pre-mutation state, and the validation failure would refuse to commit. This is correct behavior. However, the error message should clearly indicate "rolled back; snapshot file is stale and can be deleted" to prevent confusion.

* **Points for Improvement:**
  - **Highest priority:** Confirm and document whether `validate()` raises or warns on duplicate `evidence_bank` IDs. If it warns, add a pre-mutation duplicate-ID check to `apply_patches` for `append` operations on `evidence_bank`.
  - Add a negative test: `append evidence_bank with id already in bank → validate() must raise, not warn`.
  - Clarify snapshot cleanup guidance: if post-mutation validate() fails and commit is aborted, is `document_data_pre_vN.yaml` automatically cleaned up or left for forensics?

### [US-2: Delete] Analysis

* **Clarifying Questions:**
  - AC2: "`value` field is ignored/forbidden for `delete` ops (rejected with error if present)." — "Ignored" and "forbidden (rejected)" are opposites. Which is the intended behavior? The §5.1 grammar table says `value` is "forbidden" for `delete`. The review.py changes section says "Reject `value` field on `delete` ops." So it should be rejected. But the wording in the acceptance criterion uses "ignored/forbidden" — this ambiguity should be eliminated. The §6 negative constraints (NC-4) correctly say "DO NOT allow `value` field on `delete` patches", confirming rejection. Fix the AC wording.
  - After a `delete evidence_bank[2]`, all elements that were at indices 3, 4, 5... shift to 2, 3, 4.... If the interview log contains a subsequent batch that references `evidence_bank[3]`, it now targets what was originally at index 4. Does the skill instruct the AI to avoid index-bearing references to the same parent list within the same batch, or across sequential batches?

* **What-If Scenarios:**
  - **Batch-level index aliasing:** Batch: `set evidence_bank[2].source "Updated source"` → `delete evidence_bank[2]`. The set runs first (modifying the entry), then the delete runs and removes it. Result: the set was wasted work, and the delete silently succeeds. Worse: `delete evidence_bank[2]` → `set evidence_bank[2].content "New content"`. Post-delete, `evidence_bank[2]` now points to what was originally index 3. The set silently mutates the wrong entry. This batch is semantically corrupt but syntactically valid.
  - **Delete with an out-of-bounds index on a previously-deleted list:** If an earlier operation in the batch deletes the only element of a 1-element list, and a later operation also attempts to delete from that now-empty list, the second delete gets an out-of-bounds error. This is the correct behavior, but the error message context ("list is now empty") may be confusing without sequencing information.

* **Points for Improvement:**
  - Fix AC2 wording: change "ignored/forbidden" to "forbidden (rejected with error before mutation)".
  - Add to skill_interview instructions: "Avoid generating multiple index-bearing patches targeting the same parent list in a single batch. If required, list them in the correct sequential order and note that earlier ops shift subsequent indices."
  - Add unit test: batch with `delete evidence_bank[2]` then `set evidence_bank[2].source "X"` — the set must target the post-delete element, and this behavior must be explicitly asserted (not silently accepted).

### [US-3: Dangling-Ref Guard] Analysis

* **Clarifying Questions:**
  - What is the wire format of `DanglingRefError`? The PRD says "structured error listing all dangling paths." But `skill_refine` needs to display this to the user and prompt the interview agent to fix refs first. Is `DanglingRefError` a Python exception with a `.paths` attribute (list of strings like `["content.sections[0].evidence[1]"]`)? Or is it surfaced only as a human-readable string? The structured data format must be specified so `skill_refine` can parse and display it reliably.
  - `_dangling_ref_check` scans `doc["content"]["sections"][*]["evidence"]` for the deleted entry's ID. Does this function assume the document has already passed `validate()` (guaranteeing `content`, `sections` exist and are properly typed), or does it defensively handle `KeyError`/`TypeError` when the document is malformed?

* **What-If Scenarios:**
  - **Same-batch set-then-delete alias:** Batch: `set content.sections[0].evidence[0] "e5"` (adds a reference to e5), then `delete evidence_bank[idx_of_e5]`. Under sequential execution, the set runs first — now `content.sections[0].evidence[0]` references e5. Then `_dangling_ref_check` runs on the post-set in-memory doc and correctly catches the reference. This is CORRECT behavior and should be explicitly tested, as it demonstrates that `_dangling_ref_check` operates on the post-prior-patches state, not the original document.
  - **Evidence ID referenced by a sentinel string:** If `content.sections[0].evidence[0]` is `"[[DDO::REQUIRES_INPUT:add evidence ID here]]"` (a placeholder, not an actual ID), the dangling-ref check would scan for the string match against the evidence_bank entry's ID. A sentinel value would never match a valid ID, so the delete would succeed. This is correct behavior — but explicitly stating it prevents confusion.
  - **Multiple deletions in one batch, partial dangling-ref failure:** Batch: `delete evidence_bank[2]` (dangling), then `delete evidence_bank[4]` (not dangling). Does the first DanglingRefError abort processing of the entire batch, or are remaining patches applied? `apply_patches` is pure — if it raises on patch 1, patch 2 is never applied. The batch is all-or-nothing on exception. This is correct but must be documented.

* **Points for Improvement:**
  - Define `DanglingRefError` structure formally: `class DanglingRefError(Exception): paths: list[str]` — the `paths` attribute is the authoritative structured output for `skill_refine`.
  - Add explicit assumption documentation: `_dangling_ref_check` assumes the document has passed `validate()` and can safely index `content.sections[*].evidence[]` without defensive key checks.
  - Add the "same-batch set-then-delete" scenario to the unit test matrix for `_dangling_ref_check`.
  - Add negative test: sentinel in evidence list → delete proceeds (sentinel doesn't match any evidence_bank ID).

### [US-4: Insert] Analysis

* **Clarifying Questions:**
  - The PRD defines `at: len(list)` as equivalent to `append`. But are they byte-for-byte identical in the serialized YAML output? In Python, `list.insert(len(lst), x)` and `list.append(x)` produce identical in-memory state. However, if the future implementation ever diverges (e.g., different code paths, different serializer state), this equivalence should be asserted in a unit test, not just stated in the spec.
  - `at: N where N > len(list)` is rejected. Is the check `N > len(list)` or `N >= len(list) + 1`? These are the same mathematically, but the implementation must explicitly handle the `N == len(list)` case as VALID (pass-through to insert-at-end behavior), not as out-of-bounds.

* **What-If Scenarios:**
  - **CRITICAL: Negative `at` values.** `at: -1` satisfies neither `N > len(list)` (always false for negative N on any non-degenerate list) nor any existing constraint. Python's `list.insert(-1, x)` inserts the element at position `len(list) - 1` (before the last element). This is not an error; it silently produces wrong behavior. The PRD's bounds check as written would NOT catch `at: -1`. This requires an explicit `at < 0` rejection check in both `validate_interview_log` and `apply_patches`.
  - **`at: 0` on an empty list:** `list.insert(0, x)` on `[]` produces `[x]`. This is correct and should be tested explicitly (boundary case: inserting into a zero-length list).
  - **`at` field as float or string:** AI may generate `at: 2.0` (float) or `at: "2"` (string). YAML parsers may or may not coerce these. The `validate_interview_log` check must enforce `isinstance(at, int)` strictly, not `at == int(at)`.

* **Points for Improvement:**
  - **Highest priority:** Add `at < 0` as an explicit rejection condition in both `validate_interview_log` and the `apply_patches` bounds check.
  - Add `isinstance(at, int) and not isinstance(at, bool)` check — Python `bool` is a subclass of `int`; `at: True` (= 1) and `at: False` (= 0) would silently pass an `isinstance(at, int)` check.
  - Add unit tests: `at: -1` (rejected), `at: 0` on empty list (allowed), `at: len(list)` (allowed, identical output to append).

### [US-5: Interview Skill] Analysis

* **Clarifying Questions:**
  - "The skill notes that structural `value` content is AI-generated and explicitly shows the full `value` in the decision prompt for human review." This decision prompt is part of the HITL gate in `skill_interview`. But the Before/After diff is presented in `skill_refine`. Is the AI-generated `value` shown TWICE (once in interview decision prompt, once in refine diff), or is the interview prompt the primary review point and the refine diff is the safety net? The PRD should clarify which gate is considered "sufficient" (per §5.2, RT-v0.0.3-5 says the existing Before/After diff is sufficient — but that's the refine gate, not the interview gate).
  - "Skill instructions clarify the dangling-ref risk for `delete` on `evidence_bank` entries (agent should patch refs first)." — Does the skill have access to `document_data.yaml` content during the interview phase to let the AI check references itself? If yes, this is a valid pre-patch check. If no, the skill is asking the AI to reason about a document it cannot see.

* **What-If Scenarios:**
  - **AI generates a `delete` patch with a negative index path:** `evidence_bank[-1]`. The path grammar states `delete` path must end in `[N]`. The hand-rolled parser currently accepts `[N]` where N is digits. If it only accepts `[0-9]+` (positive integers), `-1` would be rejected as a parse error. But if it accepts any bracket content, `[-1]` could silently pass the parse step and trigger negative-index Python behavior at navigation time. The path parser character whitelist must be explicit.
  - **AI generates a structurally valid `value` for insert that contains nested evidence references pointing to non-existent IDs:** The Before/After diff displays the raw `value` YAML. The human reviewer sees it but cannot easily check evidence ID validity visually. This is a gap in the review process that could allow broken evidence refs to land.

* **Points for Improvement:**
  - Clarify in §5.1 that the interview display of AI-generated `value` is the AI's self-declaration; the refine Before/After diff is the human authorization gate.
  - Specify path segment character whitelist explicitly: key segments `[a-zA-Z0-9_]`, index brackets `[0-9]+` only (no negative sign, no expressions). Add this as a constraint in the path parser spec and a rejection test case.
  - Add skill_interview instruction: when generating a structural `value` containing evidence IDs, list those IDs in the human review prompt and flag if any are not in the current `evidence_bank`.

### [US-6: Integration Test Coverage] Analysis

* **Clarifying Questions:**
  - "The structural fixture is built against the existing `document_data_with_gap.yaml` base document." — Does `document_data_with_gap.yaml` have at least 3 evidence_bank entries (to allow a non-dangling delete) and at least 2 content sections (to exercise `delete` and `insert` on `content.sections`)? The fixture design depends on the base document's shape. If not, the fixture may require a simpler test target.
  - The Candidate Artifact protocol from v0.0.2 required that fixtures in `tests/fixtures/` be human-authored or human-reviewed character-by-character before `DDO_FIXTURE_SIGNOFF=1`. Is `interview_log_v1_structural.yaml` authored by the AI (as part of `/hyper-execute`) and then reviewed by the human, or authored by the human from scratch?

* **What-If Scenarios:**
  - **Fixture authors the AI-generated `value` incorrectly:** If the structural fixture includes an `append` with a `value` missing a required field (e.g., `source` is absent from an evidence entry), the test would fail at validate() in the pipeline. The fixture authoring step must verify the `value` is schema-valid before signoff.
  - **Test parametrization ordering:** If `test_loop_integration` is parametrized with `[interview_log_v1.yaml, interview_log_v1_structural.yaml]`, and the structural fixture relies on a cumulative state from the first fixture's execution (shared `document_data_with_gap.yaml`), the tests may be order-dependent. Each parametrized case must use an independent copy of the base document (via `tmp_path` fixture copy) to avoid cross-test contamination.

* **Points for Improvement:**
  - Explicitly state in §5.4 that `interview_log_v1_structural.yaml` is an AI-generated candidate that the human must review and promote manually; do not delegate signoff to the execute agent.
  - Add isolation requirement: each parametrized loop test case must operate on its own tmp copy of the base document to prevent cross-contamination.
  - Verify `document_data_with_gap.yaml` shape before designing the structural fixture; note the minimum required structure (3+ evidence entries, 2+ sections).

---

## Section 5: Technical Specifications

### [5.1 Architecture — Patch DSL Schema] Analysis

* **Clarifying Questions:**
  - The path grammar table shows `set` with "dotted + optional `[N]`". The existing `apply_patches` for `set` enforces leaf-scalar-only (no dict/list assignment). After adding three new structural ops, does the `set` branch still enforce leaf-scalar only? Could the new parser accidentally loosen the `set` constraint by treating a path that resolves to a list as a valid `set` target (now that lists are first-class path targets for `append`/`insert`)?
  - The `refine_engine` architecture node mentions `append_evidence` and `append_review_log` as current op types. These are not in the new grammar table. This means either (a) they will be removed (breaking existing interview logs), or (b) they are kept alongside the new generic `append`. The PRD must resolve this gap to avoid a hidden breaking change.

* **What-If Scenarios:**
  - **`apply_patches` atomicity under exception:** A batch of 3 patches is processed sequentially. Patch 1 (`append`) succeeds. Patch 2 (`delete`) raises `DanglingRefError`. The in-memory `doc` dict is now partially mutated (patch 1 was applied). Does `apply_patches` return the original (via deep copy at entry) or the partially-mutated dict? The answer depends entirely on whether `deep_copy` happens at function entry (safe) or is not done (unsafe). The PRD asserts "apply_patches is a pure function (deep copy only)" but does not specify WHEN the deep copy happens. If the implementation is `for patch in patches: doc = ... apply(doc, patch)` (iterative mutation) rather than `original = deepcopy(doc); work_doc = deepcopy(doc); for patch in patches: apply(work_doc, patch)`, then an exception mid-batch leaves `doc` partially mutated in the caller's scope.
  - **`value` containing a YAML alias or anchor:** YAML `*ref` anchors resolve at parse time (by `yaml.safe_load`). If the interview_log's `value` uses a YAML alias pointing to another part of the document, `yaml.safe_load` resolves it to a plain dict. This should be safe. But if `value` is itself a reference to a very large structure, it could produce unexpected memory usage during deepcopy.

* **Points for Improvement:**
  - **Critical specification gap:** Add an explicit atomicity invariant to §5.1: "apply_patches deep-copies the input document at function entry. If any patch raises, the copy is discarded and the original input is returned unchanged. The function never mutates its input argument."
  - Resolve the `append_evidence`/`append_review_log` legacy op fate explicitly in §5.2 or a new entry in the grammar table.
  - Add a guard: after the new structural ops are added to `apply_patches`, verify the `set` branch still rejects non-scalar targets (add a regression test: `set content.sections []` must fail).

### [5.2 Resolved Trade-offs] Analysis

* **Clarifying Questions:**
  - RT-v0.0.3-2: "Append/insert value ID collision in evidence_bank — post-mutation `validate()` catches duplicate IDs." The `validation_gate` architecture node explicitly states: "evidence-bank uniqueness and reference integrity (**orphans warn, not fail**)." WARN does not raise. If validate() warns on duplicates, the `commit_refine` flow — which calls validate() as a gate — would NOT abort on duplicate IDs. RT-v0.0.3-2 is unresolved. This is the most important finding in this report.

* **What-If Scenarios:**
  - **Silent duplicate ID slip:** AI generates `append evidence_bank value: {id: "e1", ...}` where `e1` already exists. apply_patches succeeds. validate() warns (no raise). commit_refine writes the file. The document now has two entries with `id: "e1"`. Future pipeline runs that check `evidence_bank` ID uniqueness would produce inconsistent results depending on whether they find the first or second entry.

* **Points for Improvement:**
  - **Highest priority:** Before implementation, run `grep` on `ddo/validation.py` to confirm whether `evidence_bank` ID uniqueness raises `ValidationError` or only warns/logs. If it only warns, either: (a) change `validation.py` to raise on duplicates (but NC-8 says "DO NOT modify validate()"), or (b) add an explicit pre-mutation check in `apply_patches` for `evidence_bank` appends/inserts: "if new_value['id'] in existing_ids: raise DuplicateIDError".
  - Update RT-v0.0.3-2 resolution to reflect the actual validate() behavior once confirmed.

### [5.3 Blast Radius] Analysis

* **Clarifying Questions:**
  - `test_review_unit` is listed as "not touched" in the blast radius. But §5.1 specifies changes to `validate_interview_log` in `review.py` (accept new op types, `at` field). `test_review_unit` currently covers "validate_interview_log pass/fail paths, severity and decision enums." Adding new op types means `test_review_unit` MUST be extended with new test cases for the new op enum values and the `at` field. Omitting this from the blast radius is an oversight.
  - The execution checklist step 16 only lists `refine_engine` as the hypergraph node to update. But `review_engine`, `skill_interview`, `skill_refine`, and the new `dangling_ref_guard` atomic node (listed as "new artifact" in §5.3) all require architecture.yml updates. The `hypergraph_updater.py` command must be run for ALL 5+ affected nodes.

* **What-If Scenarios:**
  - **Architecture drift:** If `architecture.yml` is only partially updated (only `refine_engine`), the descriptions for `review_engine` (still listing only `set` as valid op) and `skill_interview` (no mention of structural patch syntax) will be stale. Future Red Team passes will analyze a misleading architecture graph.

* **Points for Improvement:**
  - Add `test_review_unit` to the blast radius (requires new test cases for op enum expansion).
  - Expand execution checklist step 16 to: `python .agents/scripts/hypergraph_updater.py spec/compiled/architecture.yml refine_engine review_engine skill_interview skill_refine dangling_ref_guard`.
  - Add `dangling_ref_guard` as a formal new Atomic node in the blast radius narrative with its description.

### [5.4 Execution Checklist] Analysis

* **Clarifying Questions:**
  - Step 10: "Design `tests/fixtures/loop/interview_log_v1_structural.yaml`." Step 15: "Run `DDO_FIXTURE_SIGNOFF=1`." These two steps imply the fixture is agent-designed and agent-promoted. The v0.0.2 Candidate Artifact protocol (SuperPRD RT#13, enforced by `fixture_signoff_guard.py`) requires that fixtures in `tests/fixtures/` be human-authored or human-reviewed before signoff. The checklist step must explicitly say: "Write candidate fixture, then present to human for review and character-by-character verification before step 15."
  - The checklist does not include a step for verifying that existing tests were not softened or removed. After expanding `validate_interview_log`, tests that currently assert "only `set` is valid" might need to be updated — but they must not be deleted or weakened to make the new code pass.

* **What-If Scenarios:**
  - **Execute agent self-promotes the fixture:** If `/hyper-execute` writes `interview_log_v1_structural.yaml` and then runs `DDO_FIXTURE_SIGNOFF=1` in the same automated session, the human gate is bypassed. The `fixture_signoff_guard.py` only checks whether the env var is set, not whether a human was in the loop. An automated agent with `DDO_FIXTURE_SIGNOFF=1` in its environment would silently bypass the Candidate Artifact protocol.

* **Points for Improvement:**
  - Add step 10a: "HITL GATE — present `interview_log_v1_structural.yaml` to human reviewer. Do not proceed to step 11 until reviewer confirms all three ops are syntactically correct and produce the intended mutations."
  - Add step 14a: "Verify no existing test cases were deleted or weakened. Run `git diff tests/unit/test_review.py` to confirm only additions."

---

## Section 6: Negative Constraints

### [Negative Constraints] Analysis

* **Clarifying Questions:**
  - NC-11: "DO NOT apply nested list operations within a single patch (e.g., appending to a list inside an `insert` value is not a structural op error — it's valid YAML in the `value`; the patch itself only inserts one element)." This constraint is phrased as "DO NOT apply nested list ops" but then immediately says the example is NOT an error. The constraint name and body directly contradict each other. The intended meaning appears to be: "The patch operation targets only the outermost list; nested lists within `value` are plain data and are not interpreted as ops." This should be rewritten for clarity.
  - NC-7: "DO NOT use `eval` or dynamic code execution in the path parser." The path parser is described as "hand-rolled." What is the explicit character whitelist for path segments? Without it, an AI could generate paths containing characters that exploit string formatting, os.path resolution, or other injection vectors. The whitelist should be explicit: key segments must match `[a-zA-Z_][a-zA-Z0-9_]*`; index brackets must match `\d+` (positive integers only).

* **What-If Scenarios:**
  - **NC-7 bypass via path injection:** A path like `../../etc/passwd` would be caught by `assert_within_documents` (containment check) in the write path, but the path DSL parser itself might accept it without error if it's not in the write path. Paths that resolve to Python dict keys traversed in memory pose no filesystem risk, but a path like `__class__.__init__.__globals__` could theoretically trigger unexpected attribute access if the parser is not strictly whitelist-based. This is an extreme edge case for a pure-Python dict traversal, but the whitelist constraint should be explicit.
  - **NC-8 conflict with RT-v0.0.3-2:** NC-8 says "DO NOT modify `validate()` in `ddo/validation.py`." But if validate() only warns on duplicate IDs (contradicting RT-v0.0.3-2), either NC-8 must be relaxed (to let duplicate-ID checking raise), or a new pre-mutation check must be added to `apply_patches`. The two constraints are in potential conflict depending on validate()'s actual behavior.

* **Points for Improvement:**
  - Rewrite NC-11 to: "The `value` field may contain nested lists and dicts; the structural patch operation modifies only the outermost target list. Nested list content within `value` is plain YAML data, not interpreted as further patch ops."
  - Add NC-13: "Path segment keys must match `[a-zA-Z_][a-zA-Z0-9_]*`; index brackets must match `\d+` (positive integer only, no negative sign, no expressions)."
  - Explicitly resolve the NC-8 vs RT-v0.0.3-2 tension once validate()'s duplicate-ID behavior is confirmed.

---

## Section 7: Risks & Mitigation

### [Risks & Mitigation] Analysis

* **Clarifying Questions:**
  - "Risk: Dangling-ref guard misses an indirect reference (e.g., sentinel string, nested ref)." The mitigation says "Guard only scans direct `content.sections[*].evidence[]` list." But `validate()` also checks reference integrity (orphans warn). Is the dangling-ref guard in `apply_patches` redundant with validate()'s post-mutation check? Why is the pre-mutation guard needed if validate() runs post-mutation anyway? The answer is: validate() would catch a dangling reference AFTER the delete has already mutated the document. The pre-mutation guard prevents the delete from running at all. This distinction should be stated explicitly in the risk table.

* **What-If Scenarios:**
  - **Unaddressed risk: Sequential-index invalidation in multi-op batches.** A batch containing `insert evidence_bank at: 0` (new item at index 0, everything shifts up) followed by `delete evidence_bank[3]` (targets what is now index 3, not the original index 3) produces a semantically incorrect result without raising any error. This is not in the risk table but is a genuine failure mode for AI-generated patch batches.
  - **Unaddressed risk: `_dangling_ref_check` called on a document that has never been validated.** If `apply_patches` is called directly (in tests or tooling) without a prior `validate()`, `_dangling_ref_check` may encounter missing `content`/`sections` keys and raise an unhandled `KeyError` instead of a structured `DanglingRefError`.

* **Points for Improvement:**
  - Add to risk table: "Sequential index invalidation in multi-op batches | Medium | High | Mitigation: skill_interview instructions warn AI to avoid multiple index-bearing ops on the same parent list in one batch; unit test asserts known sequential-index scenario."
  - Add to risk table: "_dangling_ref_check on unvalidated document raises KeyError | Low | Low | Mitigation: defensive key access in _dangling_ref_check with explicit check for content/sections structure."
  - Clarify in the pre-mutation guard justification: "Guard runs BEFORE mutation; validate() runs AFTER. Guard prevents the mutation from occurring. Validate() would catch the dangling reference post-mutation, but the document would already be mutated in-memory (even if commit is blocked)."

---

## Section 8: Success Metrics

### [Success Metrics] Analysis

* **Clarifying Questions:**
  - M1: "all existing 111 tests passing." After expanding `validate_interview_log`'s op enum, any test that currently asserts "only `set` is a valid op" must be updated. Are those tests being extended (new assertions added) or replaced (old assertions removed)? If assertions that enforce "non-set ops are invalid" are replaced by "these specific new ops are also valid," the old rejection behavior must be preserved by new negative test cases.
  - M4: "A manual end-to-end run of `ddo-interview` + `ddo-refine` with a structural finding (append to evidence_bank)." Who performs this and at what point in the execution checklist? This manual test is not listed as a checklist step. It should be step 17 (after all automated tests pass).

* **What-If Scenarios:**
  - **111-test count drift:** The PRD references 111 existing tests. By the time `/hyper-execute` runs, this number may have changed (if other work landed since the PRD was authored). The success metric should say "all existing tests at time of implementation passing" rather than hard-coding 111.
  - **M2 fixture promotion without human review:** As noted in §5.4, `DDO_FIXTURE_SIGNOFF=1` run by the automated execute agent bypasses the Candidate Artifact protocol. M2's phrasing "exits 0 with both parametrized cases" could be interpreted as: the agent runs this as part of automated verification. The metric should specify: "Human reviewer sets DDO_FIXTURE_SIGNOFF=1 and runs this command after character-by-character fixture review."

* **Points for Improvement:**
  - Change "111 tests" to "all tests existing at implementation time" to avoid stale count assumptions.
  - Add M6: "`validate_interview_log` rejects all four invalid combinations: `set` with `at` field, `delete` with `value`, `insert` without `at`, `append` with `[N]`-terminated path."
  - Add M7: "`apply_patches` with a mid-batch `DanglingRefError` (or any exception) returns the original input dict unchanged (atomicity regression test)."
  - Clarify that M2 and M5 require human presence (HITL gate, not automated).

---

## Blast Radius Assessment (Architecture.yml Cross-Reference)

Nodes affected beyond the PRD's stated 6+2:

| Node | Status | Change Required |
|---|---|---|
| `refine_engine` | In PRD blast radius | Description update: add `append`/`delete`/`insert` ops + `_dangling_ref_check` |
| `review_engine` | In PRD blast radius | Description update: add new op enum to `validate_interview_log` |
| `skill_interview` | In PRD blast radius | Description update: structural patch syntax + dangling-ref advisory |
| `skill_refine` | In PRD blast radius | Description update: structural op Before/After diff + DanglingRefError display |
| `test_refine_unit` | In PRD blast radius | New test cases: 3 new ops, bounds checks, atomicity, _dangling_ref_check |
| `test_loop_integration` | In PRD blast radius | Parametrize + new structural fixture |
| **`test_review_unit`** | **MISSING FROM BLAST RADIUS** | New test cases for validate_interview_log op enum + at field |
| New: `dangling_ref_guard` | New Atomic node (stated) | Create new architecture.yml node as child of `refine_engine` |
| New: `interview_log_v1_structural` | New Atomic node (stated) | Create new Atomic node under `tests_integration` |

---

## Summary of Prioritized Findings

| Priority | Finding | Section | Recommended Action |
|---|---|---|---|
| P0-CRITICAL | `validate()` warns (not fails) on duplicate evidence_bank IDs; RT-v0.0.3-2 may be unresolved | §4 US-1, §5.2 | Confirm validate() behavior; add pre-mutation duplicate-ID check in apply_patches if validate() only warns |
| P0-CRITICAL | Negative `at` values (`at: -1`) not rejected; Python silently inserts at wrong position | §4 US-4, §6 | Add `at < 0` rejection in validate_interview_log and apply_patches bounds check |
| P0-MAJOR | apply_patches atomicity not specified; mid-batch exception may leave partial mutations | §5.1 | Add explicit invariant: deep-copy at function entry; exception discards copy, not original |
| P0-MAJOR | Sequential-index invalidation in multi-op batches (insert shifts indices; later delete targets wrong element) | §3, §7 | Add risk row + skill_interview warning; add unit test for known cross-op index scenario |
| P0-MAJOR | `test_review_unit` omitted from blast radius; validate_interview_log op expansion requires new tests | §5.3 | Add test_review_unit to blast radius; add op enum + at field test cases |
| P1-MAJOR | NC-11 wording contradicts itself (says DO NOT but means IS ALLOWED) | §6 | Rewrite NC-11 for clarity |
| P1-MAJOR | Execution checklist step 10/15 allows agent to self-promote structural fixture (bypasses Candidate Artifact protocol) | §5.4 | Add explicit HITL gate step 10a; state human reviews fixture before DDO_FIXTURE_SIGNOFF=1 |
| P1-MINOR | Negative path indices (`evidence_bank[-1]`) not addressed in path parser spec | §4 US-5, §6 | Add NC-13: path index brackets must match `\d+` only (no negative sign) |
| P1-MINOR | DanglingRefError format not specified; skill_refine cannot reliably parse/display it | §4 US-3 | Define DanglingRefError with `.paths: list[str]` attribute as part of spec |
| P1-MINOR | Step 16 only updates refine_engine in hypergraph; 4+ other nodes also need updates | §5.4 | Expand step 16 to list all affected hypergraph nodes |
| P2-MINOR | `bool` is subclass of `int` in Python; `at: True/False` would pass isinstance(at, int) check | §4 US-4 | Add `not isinstance(at, bool)` to the at-field type check |
| P2-MINOR | Legacy ops (append_evidence, append_review_log) fate unresolved | §5.1 | Explicitly state: deprecated, aliased, or coexisting in §5.2 |
| P2-MINOR | Empty `content.sections` after delete is not guarded | §3, §4 US-2 | Add minimum-length guard in refine_structural_check or apply_patches |

---

*Red Team Report generated 2026-06-29. Next step: run `/hyper-resolve` to triage these findings and produce the final SuperPRD + MiniPRDs.*
