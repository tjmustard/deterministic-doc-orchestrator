# MiniPRD: Loop Test Suite

**Hypergraph Node IDs:** `test_review_unit`, `test_refine_unit`, `test_loop_integration`
**Parent Nodes:** `tests_unit` (units), `tests_integration` (loop)
**Associated Files:** `tests/unit/test_review.py`, `tests/unit/test_refine.py`, `tests/integration/test_loop.py`
**Source SuperPRD:** `spec/compiled/SuperPRD_v0.0.2_AdversarialLoop.md`

## 1. The Confidence Mandate
- **Confidence Score: 9 / 10.** Every metric (M1–M9) maps to a named test; the candidate-routing boundary is fixed. Residual: the exact seeded-gap fixture contents (authored under sign-off).
- **Clarifying Questions:** none blocking.

## 2. Atomic User Stories
- **US-001:** As a maintainer, I want `tests/unit/test_review.py` to cover report/log contracts (pass/fail), `_vN` derivation across contiguous/partial sequences, `detect_incomplete_pass`, and byte-deterministic view/history generation (M1, M2).
- **US-002:** As a maintainer, I want `tests/unit/test_refine.py` to cover path parsing, `apply_patches` correctness, constrained-`set` rejection of corruption (M8), validate-before-write byte-unchanged abort (M3), patch correctness (M4), round-trip fidelity (M7), and pre-refine snapshot rollback (M9).
- **US-003:** As a maintainer, I want `tests/integration/test_loop.py` to drive a **seeded-gap** `document_data.yaml` + **signed-off** `interview_log` through refine and assert **sentinel-absence + `validate()`-clean + renders all 3 formats** — skipping until `DDO_FIXTURE_SIGNOFF=1`.
- **US-004:** As a maintainer, I want `uv run pytest`, `uv run ruff check .`, and `uv run ruff format --check .` to all exit 0 (M6).

## 3. Implementation Plan (Task List)
- [ ] `tests/unit/test_review.py`: contract pass/fail, `report_version` (incl. gaps), `detect_incomplete_pass` (report-without-log, source-newer-than-history), view/history byte-determinism.
- [ ] `tests/unit/test_refine.py`: `parse_path` (valid + reject eval-ish/negative/slice), `apply_patches` happy paths, **M8** constrained-`set` rejection (type change / auto-vivify / wholesale `content.sections`), **M3** byte-unchanged-on-abort, **M4** validate-clean output, **M7** key-order + snapshot fidelity, **M9** snapshot rollback.
- [ ] `tests/integration/test_loop.py`: human-gated end-to-end pass; **skips unless `DDO_FIXTURE_SIGNOFF=1`**; renders via `build.py` (deterministic path); asserts the M5 observable only.
- [ ] Keep all unit tests pure (no subprocess, no filesystem side-effects beyond `tmp_path`).
- [ ] Confirm lint + full suite exit 0.

## 4. The Negative Space (Constraints)
- **DO NOT** assert content-equality on AI-generated critique or patch *content* — structure and safety only.
- **DO NOT** fabricate or auto-promote the seeded-gap fixture or `interview_log`; they are human-gated under `DDO_FIXTURE_SIGNOFF` (sign-off guard enforced).
- **DO NOT** assert semantic "gap closed"; the M5 observable is sentinel-absence + `validate()`-clean + 3-format render.
- **DO NOT** rely on the `ddo-render` *skill* from pytest; the skill-mediated handoff is verified in the human-gated sign-off, not in automated tests (document this boundary).
- **DO NOT** read `tests/candidate_outputs/`; treat unverified AI outputs as blocked.

## 5. Integration Tests & Verification
- **Test 1 (Deterministic):** all unit tests above pass; lint clean; full `uv run pytest` exits 0.
- **Test 2 (Novel / human-gated):** `test_loop.py::test_gap_closing_pass` skips until `DDO_FIXTURE_SIGNOFF=1`, then asserts the M5 observable on the promoted fixture — the only end-to-end check, deliberately routed through the Candidate Artifact protocol.
