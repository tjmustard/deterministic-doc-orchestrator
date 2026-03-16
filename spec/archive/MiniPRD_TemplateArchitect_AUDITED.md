# MiniPRD: Template Architect Skill
**Hypergraph Node ID:** `skill_template_architect`
**Parent Node:** `template_library`

## 1. The Confidence Mandate
**Agent Instruction:** Before generating any plans or writing code, analyze this document and output a Confidence Score (1-10). If the score is below 9, list strictly the clarifying questions needed to reach 10.

## 2. Atomic User Stories
* **US-001:** As a power user, I want `/template-architect` to guide me through defining a new document type template so that the `/extract` skill knows exactly how to map transcript content to document sections.
* **US-002:** As a power user, I want the generated template to be saved to `.agents/schemas/templates/` so that it is immediately available for use in new workspaces.
* **US-003:** As a power user, I want the template to pass structural validation before being saved so that malformed templates never enter the library.

## 3. Implementation Plan (Task List)
- [ ] Task 1: Conduct a structured interview with the operator (max 2 questions per turn):
  - What is the name and type of the document? (e.g., "My Document", "Technical Design Doc")
  - What are the top-level sections this document must contain? (Operator lists them)
  - For each section: What specific data points or fields must be present? (Operator describes)
  - For each field: Is this field required or optional? What does a good answer look like?
  - What are the most common failure modes — what do authors typically get wrong or omit?
- [ ] Task 2: From the interview, synthesize the template structure:
  - Top-level `#` heading: Document type name.
  - `**Agent Instruction:**` block at the top: instructs the `/extract` skill to map transcript to schema; includes "DO NOT hallucinate. If data is missing, output `[NEEDS_CLARIFICATION]`."
  - One `##` section per top-level document section.
  - Under each section: bullet points with field names in bold + `[Insert from transcript]` placeholder.
  - Optional fields marked with `(optional)`.
  - A `## Common Failure Modes` section at the bottom listing the operator-identified pitfalls as agent guardrails.
- [ ] Task 3: Display the generated template to the operator for review before saving.
- [ ] Task 4: Run `validate_template()` on the generated content. If it fails, show the operator which check failed and regenerate.
- [ ] Task 5: Derive a `template_id` from the document type name (snake_case, e.g., `my_document`). Save to `.agents/schemas/templates/<template_id>.md`.
- [ ] Task 6: Print confirmation: template ID, file path, and instructions for referencing it in `state_graph.yml`.

## 4. The Negative Space (Constraints)
* **DO NOT** save the template until the operator has reviewed and confirmed the output.
* **DO NOT** save a template that fails `validate_template()`.
* **DO NOT** overwrite an existing template with the same ID without explicit operator confirmation.
* **DO NOT** hallucinate section content — all structure must come from the operator interview.

## 5. Integration Tests & Verification
* **Test 1 (Novel):** Conduct the full interview for a "Software Architecture Decision Record" document type. Expected Output: a template `.md` file saved to `.agents/schemas/templates/software_architecture_decision_record.md` that passes `validate_template()` — Candidate Artifact routing protocol triggered for human review.
* **Test 2 (Deterministic):** Attempt to save a template with no `[Insert from transcript]` placeholder. Expected: `validate_template()` raises error; template is not saved; operator is shown the failure reason.
* **Test 3 (Deterministic):** Attempt to save a template with an ID that already exists in `.agents/schemas/templates/`. Expected: operator is prompted for confirmation before overwrite proceeds.
