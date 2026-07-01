# MiniPRD: SkillRedTeam — bind category to AV-NN + hard-fail on missing table

**Hypergraph Node ID:** skill_red_team
**Parent Node:** ddo_skills

## 1. The Confidence Mandate
- **Confidence Score:** 10/10. Anchor lines verified (`ddo-red-team.md:107` category row, `:131`
  example). The hard-fail behavior is locked (RT-05).
- **Clarifying Questions:** None.

## 2. Atomic User Stories
- **US-001:** As a document author, I want `ddo-red-team` to bind each finding's `category` to the
  active persona's exact `AV-NN: <name>` so categories are consistent.
- **US-001b:** As a maintainer, I want `ddo-red-team` to hard-fail (naming the persona) when the
  resolved persona has no Attack Vectors table, so a legacy/custom persona never yields malformed
  categories (RT-05).

## 3. Implementation Plan (Task List)
- [ ] Add a step to the persona-resolution section: after reading the persona file, **echo its
      `## Attack Vectors` table** into the report header/context so the AI (and a human auditor) can
      resolve `AV-NN` to a name without opening the persona file.
- [ ] Redefine the `category` finding-contract row (≈ line 107): *"the active persona's exact
      `AV-NN: <name>` from its Attack Vectors table (free-text in the schema; consistency enforced
      cognitively)."*
- [ ] Update the §6 example finding (≈ line 131) to `category: "AV-01: missing_acceptance_criteria"`.
- [ ] Add the **hard-fail clause** (RT-05): "If the resolved persona has no `## Attack Vectors` table,
      HARD-FAIL naming the persona (mirror the existing missing-file hard-fail). Do NOT emit free-text
      categories as a fallback."

## 4. The Negative Space (Constraints)
- **DO NOT** change `ddo/review.py` `validate_report` — `category` stays free-text (D1/D2).
- **DO NOT** add a fallback that emits free-text categories for table-less personas (RT-05).
- **DO NOT** introduce a `category` whitelist/enum anywhere in code.

## 5. Integration Tests & Verification
- **Test 1 (Deterministic):** Pointed at a persona with no AV table → `ddo-red-team` hard-fails and
  names that persona; it does not produce a report.
- **Test 2 (Novel):** Pointed at `product_critic` → every emitted finding's `category` is an
  `AV-0N: <name>` present in that persona's table (cognitive check; the source table is test-pinned).
