# MiniPRD: Styles — new `ddo/styles/` module + three built-in profiles

**Hypergraph Node ID:** ddo_styles  *(NEW — hand-add to architecture.yml)*
**Parent Node:** ddo_system
**DAG:** blocks MP-2 (atomic), MP-3, MP-5. No blockers.

## 1. The Confidence Mandate
- **Confidence Score:** 10/10. Directory + file contract mirror `ddo/personas/` exactly.
  Content is HITL-authored; the only hard constraint is "phrasing-only, zero content-bearing
  or quantitative/factual imperatives" (RT-1/RT-2).
- **Clarifying Questions:** None.

## 2. Atomic User Stories
- **US-001 / US-007:** As a document author, I want built-in profiles so new documents are
  anchored to a named register out of the box.

## 3. Implementation Plan (Task List)
- [ ] Create the `ddo/styles/` directory.
- [ ] Author `ddo/styles/formal_professional.md` in the 5-section contract
      (`# **Style Profile: formal_professional**` + `## Register & Audience`, `## Voice & Person`,
      `## Sentence & Structure`, `## Diction`, `## Avoid`), non-empty free-prose bodies.
- [ ] Author `ddo/styles/conversational.md` in the same 5-section contract.
- [ ] Author `ddo/styles/technical_precise.md` in the same 5-section contract.
- [ ] In every profile, keep `Diction`/`Avoid` **phrasing-only**: no directive that would
      induce a fact, statistic, or framing claim (RT-1). Explicitly avoid imperatives like
      "lead with a statistic" / "open with a compelling market number."
- [ ] Contain **no instruction-channel language** (e.g. "ignore prior notes", "prioritize
      persuasion over hedging") — profiles are data, not instructions (RT-2).
- [ ] Contain **no sentinel tokens** (`[REQUIRES USER INPUT:` / `[[DDO::REQUIRES_INPUT:`).

## 4. The Negative Space (Constraints)
- **DO NOT** add any content-bearing, quantitative, or factual imperative to a profile (RT-1).
- **DO NOT** add instruction-channel / behavior-changing language to a profile (RT-2).
- **DO NOT** add a 6th machine-parsed field or an AV-style table — bodies are free prose (D4).
- **DO NOT** promote any profile to `tests/fixtures/`; profiles are first-class source.
- **DO NOT** author a schema default reference here without MP-2 landing atomically (RT-6).

## 5. Integration Tests & Verification
- **Test 1 (Deterministic):** All three profiles pass `tests/unit/test_styles.py` (title +
  5 headings present, non-empty bodies, sentinel-absence). `test_style_dir_has_files` sees ≥3 files.
- **Test 2 (HITL):** Profile prose is a non-deterministic Candidate Artifact — routing:
  human review at authoring → committed as source → structurally gated by `test_styles.py`;
  never auto-promoted to fixtures (SuperPRD Phase 3 / A7).
