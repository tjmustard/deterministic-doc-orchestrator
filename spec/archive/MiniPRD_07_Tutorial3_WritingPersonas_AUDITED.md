# MiniPRD: Tutorial3_WritingPersonas — authoring a persona via `ddo-create-persona`

**Hypergraph Node ID:** `tutorials` *(content for the NEW node registered in MP-8)*
**Parent Node:** `ddo_system`
**DAG:** Blocked-by MP-1..MP-4 (uses the four new personas as specimens).

## 1. The Confidence Mandate
- **Confidence Score:** 10/10. Hand-authored tutorial demonstrating the existing
  `ddo-create-persona` skill and the v0.0.4 AV-table format; no new skill, no new persona
  (the four specimens are authored in MP-1..MP-4).
- **Clarifying Questions:** None.

## 2. Atomic User Stories
- **US-003:** As a user, I want a tutorial on writing structured personas so I can build my own review lens.

## 3. Implementation Plan (Task List)
- [ ] Create `tutorials/ddo-v006-writing-structured-personas/` with the full convention.
- [ ] `tutorial.md` walks the **v0.0.4 AV-table persona format** and drives the
      **`ddo-create-persona`** skill end-to-end (interactive/HITL steps as walkthrough prose,
      not CI-executed).
- [ ] Cite the four new personas (`content_editor`, `meeting_recorder`, `meeting_facilitator`,
      `project_stakeholder`) as **specimens** — reference them by path; do not copy their full
      bodies into `input_files/` unless registered in `EXPECTED_MIRRORS` (avoid an unmapped copy,
      RT-02). Prefer in-repo path references.
- [ ] Explain the persona → Red Team injection contract (persona is untrusted, scoped input;
      stem gate `^[a-z][a-z0-9_]*$`), and how `test_personas.py` auto-covers new personas.
- [ ] `code_samples/*.py` (if any) ruff-clean/runnable (RT-06).

## 4. The Negative Space (Constraints)
- **DO NOT** add a new skill — demonstrate the existing `ddo-create-persona` (SuperPRD §6).
- **DO NOT** copy a persona file into `input_files/` without registering it in `EXPECTED_MIRRORS`
  (an unmapped copy would be an unguarded drift surface, RT-02).
- **DO NOT** present persona authoring as a CI-executed step — it is interactive/HITL walkthrough prose.
- **DO NOT** invent a new tutorial layout.

## 5. Integration Tests & Verification
- **Test 1 (Deterministic):** `test_personas.py` already passes for the four cited specimens
  (authored in MP-1..MP-4); any referenced path is covered by MP-8's `test_tutorial_refs.py`
  existence check.
- **Test 2 (Novel):** `tutorial.md` prose is a Candidate Artifact → HITL sign-off; not parsed
  programmatically.
