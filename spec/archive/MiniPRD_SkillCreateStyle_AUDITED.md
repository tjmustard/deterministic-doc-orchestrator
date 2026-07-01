# MiniPRD: SkillCreateStyle — interactive style-authoring skill

**Hypergraph Node ID:** skill_create_style  *(NEW — hand-add to architecture.yml)*
**Parent Node:** ddo_skills
**Edges:** `implements: [ddo_skills]`, `depends_on: [ddo_styles]`. No `ddo_core` dependency.
**DAG:** independent of MP-1..MP-3/MP-5; feeds MP-7 (Hypergraph).

## 1. The Confidence Mandate
- **Confidence Score:** 10/10. Pattern mirrors `ddo-create-persona` (paced Q&A loop, cognitive
  overwrite guard). Guard model is cognitive-only; no `ddo_core` dependency.
- **Clarifying Questions:** None.

## 2. Atomic User Stories
- **US-004:** As a style author, I want a guided skill that writes a new profile in the standard
  5-section structure so authoring is repeatable and HITL-gated, and rejects content-bearing
  directives.

## 3. Implementation Plan (Task List)
- [ ] Create `ddo/skills/ddo-create-style.md` (HACF cognitive-node format; no `.claude/commands/`
      bridge — `ddo-*` skills have none).
- [ ] **Slug step:** elicit the profile name; validate `^[a-z][a-z0-9_]*$` before any path use
      (mirrors the stem gate; rejects `.`/`/`/`..`).
- [ ] **Paced Q&A loop** (≤2 questions/turn, mirroring `ddo-create-persona`) eliciting the five
      sections: `Register & Audience`, `Voice & Person`, `Sentence & Structure`, `Diction`, `Avoid`.
- [ ] **Content-directive rejection (RT-1/RT-2):** the skill actively rejects content-bearing
      directives and **bans quantitative/factual imperatives** in `Diction`/`Avoid`
      (e.g. "lead with a statistic", "open with a market number", "emphasize urgency with data").
- [ ] **Ship a 3–5 example rubric** in the skill so the cognitive rejection is consistently
      anchored: label examples as *phrasing* ("prefer active voice"), *content* ("open with a
      compelling market statistic"), and *ambiguous framing* ("emphasize the urgency") with the
      rule to treat framing/content as reject-or-rephrase.
- [ ] **Sentinel resolution:** resolve every `[REQUIRES USER INPUT: …]` before write; the
      committed profile MUST contain no sentinel tokens.
- [ ] **HITL gate:** draft-preview `[WAITING FOR USER REVIEW]` + `APPROVE` before write.
- [ ] **Cognitive overwrite guard:** Read-based exists-check on `ddo/styles/<name>.md`; if it
      exists, refuse and require re-confirmation with the **literal filename** (mirrors
      `ddo-create-persona`).
- [ ] Write via the Write tool to `ddo/styles/<name>.md`.

## 4. The Negative Space (Constraints)
- **DO NOT** reuse `ddo.ingest.atomic_write` / add a `ddo_core` dependency — guard is cognitive.
- **DO NOT** write before the `[WAITING FOR USER REVIEW]` gate, or auto-advance any gate.
- **DO NOT** overwrite an existing profile without literal-filename re-confirmation.
- **DO NOT** commit a profile containing sentinel tokens or content-bearing/quantitative
  imperatives (RT-1/RT-2).
- **DO NOT** Read/Write a `<name>.md` path before validating `^[a-z][a-z0-9_]*$`.
- **NOTE (RT-2 residual):** this rejection covers only the create-style authoring path;
  hand-authored/edited profiles bypass it. Read-time sandboxing (MP-3) + HITL-review-at-merge
  are the cross-path gates. Documented, known-accepted.

## 5. Integration Tests & Verification
- **Test 1 (Deterministic):** a profile authored by the skill passes `tests/unit/test_styles.py`
  (title + 5 headings, non-empty bodies, sentinel-absence).
- **Test 2 (HITL):** output is a non-deterministic Candidate Artifact — routing: human
  `[WAITING FOR USER REVIEW]` sign-off → write → `test_styles.py` gate → usable by the injection
  skills; never auto-promoted to fixtures.
