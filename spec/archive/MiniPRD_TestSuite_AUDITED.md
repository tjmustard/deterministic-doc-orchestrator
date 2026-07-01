# MiniPRD: Test Suite + Fixture Bootstrap

**Hypergraph Node ID:** `test_suite`
**Parent Node:** `ddo_pipeline`
**Depends on:** `build_orchestrator`, `validation_gate`, `schemas`, `templates`, `skill_ingest`, `skill_render`

## 1. The Confidence Mandate
- **Confidence Score:** 8/10.
- **Clarifying Question (resolved):** Store golden PDF binary, or text + hash? → **Store extracted text + a content hash** (RT #4/R4); never commit the PDF binary.

## 2. Atomic User Stories
- **US-006:** As a maintainer, I have a regression suite that locks determinism and validation so future changes can't silently break the core guarantees.

## 3. Implementation Plan (Task List)
- [ ] **Fix `.gitignore` (surgical matrix, RT #8):** delete wholesale `/tests` + `/spec`; un-ignore `tests/{unit,integration,fixtures}`, `spec/{compiled,process}`; **keep** ignoring `tests/candidate_outputs/`, `Documents/`, `spec/{active,archive}/`. Verify with `git status --porcelain` + `git check-ignore`.
- [ ] Add the **fixture sign-off guard** (pre-commit/CI): reject diffs to `tests/fixtures/` lacking a human sign-off token.
- [ ] `tests/unit/test_validation_gate.py` — all pass + fail paths (see ValidationGate MiniPRD).
- [ ] `test_html_md_byte_identical` — render both example docs to HTML/MD; assert byte-equality vs. frozen fixtures (normalized LF + `C.UTF-8` + stripped trailing ws).
- [ ] `test_pdf_content_identical` — two PDF renders → extracted-text equality; store text + hash, not the binary.
- [ ] `test_pdf_timestamp_byte_identical` — same `--timestamp` → byte-identical (gated on the spike).
- [ ] `test_slug_containment` — malicious/illegal titles cannot escape `Documents/`.
- [ ] `test_ingest_contract_and_renderability` — fixture source → schema-valid, renderable YAML (no content equality).
- [ ] `test_personas_well_formed` — both migrated personas parse / are well-formed.
- [ ] One-time human sign-off promoting the render baselines into `tests/fixtures/`.
- [ ] Confirm `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .` all exit 0.

## 4. The Negative Space (Constraints)
- **DO NOT** let an agent write/promote `tests/fixtures/` — human sign-off only (guard-enforced).
- **DO NOT** read `tests/candidate_outputs/` or `spec/archive/`.
- **DO NOT** assert content equality on `ddo-ingest` output.
- **DO NOT** commit PDF binaries — store extracted text + hash.
- **DO NOT** write determinism tests that depend on host-specific line endings/locale — normalize first.

## 5. Integration Tests & Verification
- **Test 1 (Deterministic):** full `uv run pytest` green; `ruff check`/`format --check` exit 0.
- **Test 2 (Deterministic):** `git status --porcelain` shows new test/spec files stageable; `git check-ignore tests/candidate_outputs/ Documents/` confirms both stay ignored.
- **Test 3 (Novel):** an attempt to modify a fixture without the sign-off token → guard rejects the diff.
