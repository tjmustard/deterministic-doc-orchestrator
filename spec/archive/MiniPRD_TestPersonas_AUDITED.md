# MiniPRD: TestPersonas — rewrite test_personas.py as a glob AV-table validator

**Hypergraph Node ID:** test_personas_unit  *(ALREADY EXISTS — mark dirty + rewrite, NOT add)*
**Parent Node:** ddo_personas

## 1. The Confidence Mandate
- **Confidence Score:** 10/10. The existing file is an RT#12 smoke test hardcoded to
  `_PERSONA_NAMES = ["product_critic","scientific_reviewer"]` (line 16). Full validator contract is
  locked (SuperPRD §4 US-004, RT-02/04/06/13).
- **Clarifying Questions:** None.

## 2. Atomic User Stories
- **US-004:** As a maintainer, I want the persona AV-table format guarded by a test so it cannot
  silently regress, and so create-persona'd personas are covered.

## 3. Implementation Plan (Task List)
- [ ] **Rewrite** `tests/unit/test_personas.py` (do not create new). Replace the hardcoded
      `_PERSONA_NAMES` list with a **glob** over `ddo/personas/*.md` (RT-02), parametrizing the tests
      over every discovered persona.
- [ ] Parse the `## Attack Vectors` table with stdlib `re` (no Markdown library).
- [ ] Assert, per persona:
  - [ ] The table exists and has the `| ID | Name | When to apply |` header.
  - [ ] IDs are `AV-NN`, **sequential from AV-01**, and unique.
  - [ ] Names match `^[a-z][a-z0-9_]*$` (no leading digit, no `__`, no trailing `_`) and are **unique**.
  - [ ] Names contain **no escaped underscore** `\_` — raw `_` only (RT-04).
  - [ ] No cell contains a literal `\|` / unescaped `|` beyond the column delimiters (RT-06).
  - [ ] All three columns are **non-empty** for every row.
  - [ ] **No sentinel tokens** `[REQUIRES USER INPUT:` or `[[DDO::REQUIRES_INPUT:` anywhere (RT-13).
- [ ] Ensure `uv run pytest tests/unit/test_personas.py` is green against both built-ins.

## 4. The Negative Space (Constraints)
- **DO NOT** hardcode persona names or an AV **count** of 6 — glob the directory; counts are variable.
- **DO NOT** add a Markdown-parser dependency — stdlib `re` only.
- **DO NOT** validate report-side `category` values here — this test guards the persona **source** only
  (the `review.py` whitelist prohibition does not apply to this test).

## 5. Integration Tests & Verification
- **Test 1 (Deterministic):** Both built-in personas pass all assertions; `uv run pytest` green.
- **Test 2 (Deterministic):** A persona with a sentinel token, an escaped `\_`, a duplicate AV ID, or a
  non-sequential ID **fails** the test (each negative case exercised via a temp fixture or parametrization).
