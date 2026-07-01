# MiniPRD: TestRefineReview — flip legacy-op tests + add rejection tests

**Hypergraph Node ID:** test_refine_unit  *(also touches test_review_unit)*
**Parent Node:** ddo_core

## 1. The Confidence Mandate
- **Confidence Score:** 10/10. Ground truth verified: all 4 legacy-op tests live in `test_refine.py`
  (lines 226/245/263/390); `test_review.py` has **zero** op-named tests, so its rejection tests are
  net-new (RT-07). Both error surfaces must be independently asserted (RT-15).
- **Clarifying Questions:** None.

## 2. Atomic User Stories
- **US-003 (verification half):** As a maintainer, I want the removed ops to fail loudly at **both**
  the `apply_patches` and `validate_interview_log` surfaces, with the old success-path tests flipped
  to rejection tests.

## 3. Implementation Plan (Task List)
- [ ] In `tests/unit/test_refine.py`, **flip** the 4 legacy-op tests:
  - [ ] `test_apply_patches_append_evidence` (≈ 226) → assert `apply_patches` raises `ValueError`.
  - [ ] `…_append_review_log_creates_list` (≈ 245) → assert `ValueError`.
  - [ ] `…_append_review_log_extends_existing` (≈ 263) → assert `ValueError`.
  - [ ] `…_append_evidence_non_dict_raises` (≈ 390) → assert the unknown-op `ValueError` (op is gone).
- [ ] In `tests/unit/test_review.py`, **add** net-new rejection tests asserting `validate_interview_log`
      raises `ReportValidationError` for a log carrying `append_evidence` and for one carrying
      `append_review_log` (RT-07).
- [ ] Confirm **both** surfaces are independently reachable (RT-15): the `apply_patches` `ValueError`
      path is exercised directly (not shadowed by `validate_interview_log` running first), and the
      `validate_interview_log` `ReportValidationError` path is exercised on a log that flows through
      validation.

## 4. The Negative Space (Constraints)
- **DO NOT** keep any test that asserts a *successful* `append_evidence`/`append_review_log` apply.
- **DO NOT** assume one rejection surface covers the other — assert both (RT-15).
- **DO NOT** rename/renumber unrelated tests in these files.

## 5. Integration Tests & Verification
- **Test 1 (Deterministic):** `uv run pytest tests/unit/test_refine.py tests/unit/test_review.py` green;
  the 4 flipped tests pass as rejection tests; the new review rejection tests pass.
- **Test 2 (Deterministic):** A hand-edited interview log with a removed op that **skips** validation
  and hits `apply_patches` raises `ValueError`; the same op routed through `validate_interview_log`
  raises `ReportValidationError` — both proven.
