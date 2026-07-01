# MiniPRD: TestLoopIntegration
**Hypergraph Node ID:** `test_loop_integration`
**File:** `tests/integration/test_loop.py`
**Parent Node:** `tests_integration`
**SuperPRD:** `SuperPRD_v0.0.3_StructuralPatchDSL.md`

## 1. Confidence Mandate
**Score: 8/10.** Two clarifying questions to reach 10:
1. Does `document_data_with_gap.yaml` need to be structured to allow a non-dangling `delete` from `evidence_bank` (i.e., at least one unreferenced entry)?  → **Yes.** Design the base document with ≥ 3 evidence entries where at least 1 is NOT referenced in any `content.sections[*].evidence[]` — this is the delete target.
2. What is the correct `tmp_path` isolation pattern?  → The existing test already uses `tmp_path / "Documents" / "loop_test"`. The parametrized cases must use independent copies of `document_data_with_gap.yaml` via `shutil.copy` to `tmp_path`, ensuring the base document on disk is not modified between cases.

## 2. Atomic User Stories
- **US-PRECONDITION**: `tests/fixtures/loop/document_data_with_gap.yaml` and `tests/fixtures/loop/interview_log_v1.yaml` are authored as candidate artifacts by the execute agent, presented to the human for character-by-character review, and signed off before the structural fixture is designed.
- **US-1**: `test_loop_integration` is parametrized over two fixture cases: the existing `interview_log_v1.yaml` (set-based gap-closing) and the new `interview_log_v1_structural.yaml` (structural ops).
- **US-2**: Each parametrized case uses an independent `tmp_path` copy of `document_data_with_gap.yaml` — no shared mutable state.
- **US-3**: The structural fixture case passes all three M5 assertions: sentinel-absence, `validate()`-clean, 3-format render success.
- **US-4**: `interview_log_v1_structural.yaml` exercises one `append` (to `evidence_bank`), one `delete` (of an unreferenced evidence entry), and one `insert` (into `content.sections`) through the full refine pipeline.

## 3. Implementation Plan

**Phase A: v0.0.2 pre-condition fixtures (HITL-gated)**
- [ ] Design `tests/fixtures/loop/document_data_with_gap.yaml`:
  - Must satisfy DDO minimal contract (`meta`, `evidence_bank`, `content.sections`).
  - Must have ≥ 3 evidence entries, ≥ 2 content sections.
  - Must have at least 1 unreferenced evidence entry (the v0.0.3 delete target).
  - Must have at least 1 `[[DDO::REQUIRES_INPUT:...]]` sentinel (the v0.0.2 gap).
  - Output as candidate artifact; present to human for character-by-character review.
- [ ] **HITL GATE A**: Human reviews `document_data_with_gap.yaml` — approves or requests changes.
- [ ] Design `tests/fixtures/loop/interview_log_v1.yaml`:
  - One `set` resolution targeting the sentinel field — replaces `[[DDO::REQUIRES_INPUT:...]]` with a real value.
  - Output as candidate artifact; present to human for review.
- [ ] **HITL GATE B**: Human reviews `interview_log_v1.yaml` — approves or requests changes.
- [ ] Create `tests/fixtures/loop/` directory if it doesn't exist.
- [ ] Write both files to `tests/fixtures/loop/`.
- [ ] Human sets `DDO_FIXTURE_SIGNOFF=1` and runs `uv run pytest tests/integration/test_loop.py` → existing `test_gap_closing_pass` must exit 0.

**Phase B: Structural fixture + parametrization (after Phase A passes)**
- [ ] Design `tests/fixtures/loop/interview_log_v1_structural.yaml`:
  - Resolution 1: `op: "append"` targeting `evidence_bank` with a new complete evidence entry (all required fields).
  - Resolution 2: `op: "delete"` targeting `evidence_bank[N]` where `N` is the unreferenced entry. Must NOT reference an entry cited in `content.sections[*].evidence[]`.
  - Resolution 3: `op: "insert"` targeting `content.sections` with `at: 0` and a minimal valid section value.
  - All three resolutions must leave the document sentinel-free and `validate()`-clean.
  - Output as candidate artifact; present to human for character-by-character review.
- [ ] **HITL GATE C** (step 10a): Human reviews `interview_log_v1_structural.yaml` — verifies all three ops are syntactically correct, schema-valid, and produce the intended mutations. Do NOT proceed until human approves.
- [ ] Read `tests/integration/test_loop.py` — identify the `_fixtures_exist()` check and `test_gap_closing_pass` signature.
- [ ] Update `_fixtures_exist()` to check all three fixture files:
  ```python
  def _fixtures_exist() -> bool:
      return (
          (_FIXTURES_LOOP / "document_data_with_gap.yaml").is_file()
          and (_FIXTURES_LOOP / "interview_log_v1.yaml").is_file()
      )
  ```
  (No change needed — the base check is unchanged; the structural fixture has its own check below.)
- [ ] Add `_structural_fixtures_exist()` helper or inline check for parametrized test.
- [ ] Parametrize `test_gap_closing_pass` (or add a new `test_structural_gap_closing_pass`):
  - Option: rename existing test to `test_loop_pass[interview_log_v1]` via `@pytest.mark.parametrize`.
  - Each case receives: `(log_filename, base_doc_filename)` → both use `document_data_with_gap.yaml` as the base.
  - Each case uses `shutil.copy(gap_data_path, tmp_path / "document_data.yaml")` to get an independent copy.
  - Skip condition: `DDO_FIXTURE_SIGNOFF=1` AND the specific fixture file exists.
- [ ] Write `tests/fixtures/loop/interview_log_v1_structural.yaml` to disk.
- [ ] Run `DDO_FIXTURE_SIGNOFF=1 uv run pytest tests/integration/test_loop.py -v` → both parametrized cases must pass.
- [ ] Run `uv run ruff check . && uv run ruff format --check .`.

## 4. Negative Space (Constraints)

- **DO NOT** let the execute agent set `DDO_FIXTURE_SIGNOFF=1` and run the test in the same automated session without HITL review.
- **DO NOT** design the structural fixture to exercise a dangling-ref delete — that would cause `DanglingRefError` and the loop test would fail. The delete target must be an unreferenced evidence entry.
- **DO NOT** share mutable state between parametrized cases — each must copy `document_data_with_gap.yaml` to its own `tmp_path`.
- **DO NOT** write fixture files to `tests/candidate_outputs/` — those are blocked from agent reads. Fixtures go to `tests/fixtures/loop/` only after human approval.
- **DO NOT** semantically validate the document's "correctness" in the test — only sentinel-absence, `validate()`-clean, and 3-format render success (as per existing M5 assertions).

## 5. Integration Tests & Verification

- **Test (human-gated, deterministic assertions):** `DDO_FIXTURE_SIGNOFF=1 uv run pytest tests/integration/test_loop.py -v` — both parametrized cases exit 0.
- **M2 (SuperPRD):** This test is the direct implementation of M2.
- **Isolation check:** Run both cases twice in opposite order — both must pass regardless of execution order (no cross-test state).
- **Regression check:** The original `interview_log_v1.yaml` case must still pass after parametrization (it must not be broken by the structural additions).
