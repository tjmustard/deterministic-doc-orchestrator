# MiniPRD: DeprecationRemoval — remove append_evidence / append_review_log

**Hypergraph Node ID:** refine_engine  *(also touches review_engine, skill_interview)*
**Parent Node:** ddo_core

## 1. The Confidence Mandate
- **Confidence Score:** 10/10. All anchors verified (`refine.py:267-269/329-354/437-442`,
  `review.py:37-46/349`, `ddo-interview.md:90/233-240`, `README.md:153`). RT-14 confirms no
  in-the-wild logs carry the ops.
- **Clarifying Questions:** None.

## 2. Atomic User Stories
- **US-003:** As a maintainer, I want the two deprecated ops removed so there is one structural-patch
  codepath, with explicit rejection of the old ops and reconciled docs/tutorial.

## 3. Implementation Plan (Task List)
- [ ] `ddo/refine.py`: delete the `elif op == "append_evidence"` / `"append_review_log"` branches
      (≈ 329-354); remove the docstring bullets (≈ 267-269); fix the unknown-op error message
      (≈ 437-442) to list only `set, append, delete, insert`.
- [ ] `ddo/review.py`: remove both from `OP_ENUM` (≈ 37-46) → `{set, append, delete, insert}`; tidy
      the comment at ≈ 349.
- [ ] `ddo/skills/ddo-interview.md`: update the patch-shape `op:` line (≈ 90) → `set | append | delete | insert`;
      remove the "Legacy Op Deprecation (v0.0.3)" section (≈ 233-240).
- [ ] `README.md` (≈ 153): drop both ops from the supported-ops list.
- [ ] `CHANGELOG.md`: add a v0.0.4 entry recording the removal + migration forms.
- [ ] **Tutorial code sample (RT-08):** in `tutorials/ddo-adversarial-loop-v0.0.2/code_samples/interview_call.py`,
      migrate **both** the `:41` comment (`add_evidence -> append_evidence`) and the `:61` op to
      `{op: append, target: "evidence_bank", value: {...}}`.
- [ ] **Tutorial prose (RT-09):** reword `tutorial.md` rows 155-156 to past tense
      ("removed in v0.0.4 — migrate: `{op: append, target: …}`"), do **not** delete the rows.
- [ ] Leave `tutorials/.../audit_2026-06-30.md` **untouched** — frozen historical record (RT-08).

## 4. The Negative Space (Constraints)
- **DO NOT** leave any *functional* reference to the removed ops in `ddo/` or in the tutorial code sample.
- **DO NOT** rewrite `audit_2026-06-30.md` (frozen dated audit — RT-08).
- **DO NOT** delete the `tutorial.md` migration rows — reword them (RT-09).
- **DO NOT** remove the historical CHANGELOG entries for v0.0.3 (they correctly retain the op names).

## 5. Integration Tests & Verification
- **Test 1 (Deterministic):** `grep -rn "append_evidence\|append_review_log" ddo/` → no functional
  references. `grep -rn ... tutorials/` → matches **only** the `audit_2026-06-30.md` allow-list
  (code sample + `tutorial.md` migration rows are clean of the bare op names).
- **Test 2 (Deterministic):** `apply_patches({op: append_evidence})` raises `ValueError`;
  `validate_interview_log` raises `ReportValidationError` for both ops (see MiniPRD_TestRefineReview).
