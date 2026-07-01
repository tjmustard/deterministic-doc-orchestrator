# MiniPRD: Personas — AV-NN Attack Vector Tables

**Hypergraph Node ID:** ddo_personas
**Parent Node:** ddo_domain

## 1. The Confidence Mandate
- **Confidence Score:** 10/10. Both built-in personas and their six existing probes are known; the AV
  names and canonical encoding are locked (SuperPRD §5.1, RT-04/RT-06).
- **Clarifying Questions:** None.

## 2. Atomic User Stories
- **US-001:** As a document author, I want each persona's Attack Vectors as an `AV-NN`-ID'd table so
  Red Team `category` values are consistent and referenceable within that persona's runs.

## 3. Implementation Plan (Task List)
- [ ] In `ddo/personas/product_critic.md`, replace the `## Attack Vectors` prose with a 3-column table
      `| ID | Name | When to apply |` — rows AV-01..AV-06 = `missing_acceptance_criteria`,
      `unsupported_value_claims`, `scope_creep`, `unmeasurable_success`, `hedging_language`,
      `contradictory_logic`. "When to apply" cell = the existing probe text **verbatim**.
- [ ] In `ddo/personas/scientific_reviewer.md`, same restructure — AV-01..AV-06 =
      `methodological_vagueness`, `unsupported_assertions`, `statistical_ambiguity`,
      `overreaching_conclusions`, `missing_limitations`, `result_discussion_bleed`.
- [ ] Use **raw underscores** in Name cells (`missing_acceptance_criteria`), never escaped `\_` (RT-04).
- [ ] Verify no probe text contains a literal `|`; if any does, rephrase to remove it (RT-06).
- [ ] Leave all other persona sections (Domain, Reviewing Mission, Severity Taxonomy, Format Rules,
      Interview Question Templates) unchanged.

## 4. The Negative Space (Constraints)
- **DO NOT** escape underscores (`\_`) in AV-name cells — raw `_` only (RT-04).
- **DO NOT** introduce a literal `|` into any "When to apply" cell (RT-06).
- **DO NOT** use globally-unique AV IDs — per-persona, AV-01-based (D7).
- **DO NOT** add, drop, or reword the six probes' *meaning*; the "When to apply" text is the probe verbatim.
- **DO NOT** invent persona content — these are migrations of existing prose, not new vectors.

## 5. Integration Tests & Verification
- **Test 1 (Deterministic):** `tests/unit/test_personas.py` globs both files → both tables parse, all
  IDs are `AV-01..AV-06` sequential/unique, names match `^[a-z][a-z0-9_]*$` and are unique, no escaped
  `\_`, no literal `|`, all columns non-empty, no sentinel tokens. (See MiniPRD_TestPersonas.)
- **Test 2 (Novel):** A Red Team run against either persona emits `category: "AV-0N: <name>"` drawn
  from the table — the source vocabulary is now deterministic (candidate `category` routing unchanged).
