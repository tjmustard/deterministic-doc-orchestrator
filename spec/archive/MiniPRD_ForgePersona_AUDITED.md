# MiniPRD: Forge Persona Skill (Create + Update)
**Hypergraph Node ID:** `skill_forge_persona`
**Parent Node:** `persona_library`

## 1. The Confidence Mandate
**Agent Instruction:** Before generating any plans or writing code, analyze this document and output a Confidence Score (1-10). If the score is below 9, list strictly the clarifying questions needed to reach 10.

## 2. Atomic User Stories
* **US-001:** As an operator, I want `/forge_persona` to guide me through defining an adversarial persona so that I don't need to hand-write the prompt file.
* **US-002:** As an operator, I want `/forge_persona --update <persona_id>` to load an existing persona, show me the current definition, and apply my changes with a version increment and changelog entry.
* **US-003:** As an operator, I want the update flow to warn me if the persona is referenced by an active job so that I don't accidentally mutate a running pipeline.

## 3. Implementation Plan (Task List)

**CREATE mode (no `--update` flag):**
- [ ] Task 1: Interview the operator (max 2 questions per turn):
  - What document type will this persona interrogate? What is the persona's professional role/identity? (e.g., "Document Examiner", "Security Auditor", "Commercial Lead")
  - What is this persona's primary adversarial angle? (e.g., "prior art and obviousness", "security vulnerabilities", "market viability")
  - What are the 3 most important things this persona forces the author to prove?
  - What output constraints apply? (e.g., "numbered list only", "no conversational filler", "focus on edge cases")
- [ ] Task 2: Synthesize the persona file using this structure:
  ```markdown
  ---
  id: <persona_id>
  version: 1
  document_type: <document_type>
  changelog:
    - "v1 (YYYY-MM-DD): Initial creation."
  ---
  # Adversarial Persona: <Persona Name>
  **Agent Instruction:** <Role and primary adversarial objective.>

  **Constraints:**
  1. <Constraint 1>
  2. <Constraint 2>
  3. DO NOT output conversational filler.
  ```
- [ ] Task 3: Display the generated persona to the operator for review before saving.
- [ ] Task 4: Derive `persona_id` as snake_case from the persona name. Save to `.agents/schemas/personas/<persona_id>.md`.
- [ ] Task 5: Print confirmation with file path and instructions for adding the persona ID to `state_graph.yml`.

**UPDATE mode (`--update <persona_id>`):**
- [ ] Task 6: Load `.agents/schemas/personas/<persona_id>.md`. If not found, abort with clear error.
- [ ] Task 7: Read `.agents/workspace_registry.yml`. For each registered workspace, load its `state_graph.yml` and check if `<persona_id>` appears in any module's `applied_personas` AND the module status is not `integrated`. If found, print: `"WARNING: This persona is actively used by job '<job_name>' (module '<module_id>', status: '<status>'). Updating will NOT affect the running pipeline (snapshot is used), but future runs will use the new version. Type CONFIRM to proceed."` Require `CONFIRM` input.
- [ ] Task 8: Display the current persona content to the operator. Accept the operator's edits (re-interview the relevant sections or accept free-form edits).
- [ ] Task 9: Increment `version` in frontmatter. Append a changelog entry: `"v<N> (YYYY-MM-DD): <operator-provided summary of change>."`.
- [ ] Task 10: Save the updated file. Print diff summary showing changed sections.

## 4. The Negative Space (Constraints)
* **DO NOT** save without operator review and confirmation.
* **DO NOT** overwrite an existing persona in CREATE mode — require `--update` for modifications.
* **DO NOT** skip the workspace registry check in UPDATE mode.
* **DO NOT** modify persona files used by active jobs without explicit `CONFIRM` from the operator.

## 5. Integration Tests & Verification
* **Test 1 (Novel):** Run `/forge_persona` for a "Critic" persona reviewing software PRDs. Expected: a valid persona `.md` file saved to `.agents/schemas/personas/critic.md` with `version: 1` and a non-empty `changelog` — Candidate Artifact routing protocol triggered.
* **Test 2 (Deterministic):** Run `/forge_persona --update critic` when `critic` is referenced by an active workspace job. Expected: prints WARNING message and requires `CONFIRM` before proceeding.
* **Test 3 (Deterministic):** Run `/forge_persona --update nonexistent_persona`. Expected: aborts with file-not-found error.
* **Test 4 (Deterministic):** After a successful update, verify `version` is incremented by 1 and `changelog` has a new entry.
