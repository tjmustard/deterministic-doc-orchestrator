# MiniPRD: SkillCreatePersona — interactive persona authoring skill

**Hypergraph Node ID:** skill_create_persona  *(NEW — hand-add to architecture.yml)*
**Parent Node:** ddo_skills

## 1. The Confidence Mandate
- **Confidence Score:** 10/10. Pattern mirrors `ddo-interview` (paced Q&A loop). Guard model is
  cognitive-only per user decision (RT-03); no `ddo_core` dependency (RT-12).
- **Clarifying Questions:** None.

## 2. Atomic User Stories
- **US-002:** As a persona author, I want a guided skill that writes a new persona in the standard
  `AV-NN`-table format so authoring is repeatable and HITL-gated.

## 3. Implementation Plan (Task List)
- [ ] Create `ddo/skills/ddo-create-persona.md` (HACF cognitive-node format; no `.claude/commands/`
      bridge needed — `ddo-*` skills have none).
- [ ] Define a **paced, one-batch-at-a-time Q&A loop** (≤2 questions/turn, mirroring `ddo-interview`)
      that elicits the six persona sections: Domain, Reviewing Mission, Attack Vectors (as an `AV-NN`
      table), Severity Taxonomy, Domain-Specific Format Rules, Interview Question Templates.
- [ ] For the Attack Vectors section, require sequential unique `AV-NN` IDs, snake_case raw-underscore
      Names matching `^[a-z][a-z0-9_]*$`, unique Names, no literal `|` in cells (matches test contract).
- [ ] Insert a `[WAITING FOR USER REVIEW]` gate; **write the file only after** the user approves.
- [ ] Before writing, perform a **cognitive `exists()` check** on `ddo/personas/<name>.md`; if it
      exists, refuse and require the user to re-confirm with the **literal filename** to overwrite (RT-03).
- [ ] Resolve every `[REQUIRES USER INPUT: …]` sentinel before the final write; the committed persona
      MUST contain no sentinel tokens (RT-13).
- [ ] Write via the Write tool to `ddo/personas/<name>.md`.

## 4. The Negative Space (Constraints)
- **DO NOT** reuse `ddo.ingest.atomic_write` / add a `ddo_core` dependency — guard is cognitive (RT-03/RT-12).
- **DO NOT** write the persona before the `[WAITING FOR USER REVIEW]` gate, or auto-advance any gate.
- **DO NOT** overwrite an existing persona without literal-filename re-confirmation (RT-03).
- **DO NOT** commit a persona containing `[REQUIRES USER INPUT:` / `[[DDO::REQUIRES_INPUT:` sentinels (RT-13).
- **DO NOT** invent persona content — emit `[REQUIRES USER INPUT: <reason>]` during the loop, then
  resolve it with the user before writing (zero-hallucination invariant).
- **DO NOT** promote the generated persona to `tests/fixtures/` automatically.

## 5. Integration Tests & Verification
- **Test 1 (Deterministic):** A persona authored by the skill passes `tests/unit/test_personas.py`
  (structure, ID/name format + uniqueness, raw `_`, no `|`, non-empty, sentinel-absence).
- **Test 2 (Novel):** Output is a non-deterministic Candidate Artifact — routing protocol:
  human `[WAITING FOR USER REVIEW]` sign-off → write → `test_personas.py` gate → usable by
  `ddo-red-team`; never auto-promoted to fixtures (SuperPRD Phase 3 routing).
