---
name: template-architect
description: Guides the operator through a structured interview to produce a validated Markdown template for a new document type. Saves the output to .agents/schemas/templates/ after validate_template() passes.
---

# Template Architect Skill

**Invocation:** `claude /template-architect`

This skill conducts a paced guided interview with the operator to define a new document type template from scratch. All template structure is derived exclusively from operator answers — nothing is hallucinated.

---

## Step 1 — Conduct Interview (max 2 questions per turn)

Ask in the following batches. Wait for the operator's answers after each batch before continuing.

**Batch 1:**
1. What is the name and type of the document you want to template? (e.g., "My Document", "Technical Design Doc", "Software Architecture Decision Record")
2. What are the top-level sections this document must contain? (List all of them — you can bullet them out)

Wait for answers, then ask:

**Batch 2 (repeat per section as needed):**
For each section the operator listed, ask:
3. For the section **"[Section Name]"**: What specific data points or fields must be present? Which are required vs. optional?
4. What does a complete, high-quality answer look like for each field in this section?

Wait for answers, then ask:

**Batch 3:**
5. What are the most common failure modes — what do authors typically get wrong or omit in this type of document?

---

## Step 2 — Synthesize Template Structure

From the interview answers, generate the template in this exact format:

```markdown
# [Document Type Name]

**Agent Instruction:** You are extracting structured content from a source transcript to fill this [Document Type Name] template. Map each section to the relevant content in the transcript. DO NOT hallucinate. If data for a field is missing or ambiguous, output `[NEEDS_CLARIFICATION]` for that field.

## [Section 1 Name]

- **[Field Name]:** [Insert from transcript]
- **[Field Name]:** [Insert from transcript]
- **[Optional Field Name] (optional):** [Insert from transcript]

## [Section 2 Name]

- **[Field Name]:** [Insert from transcript]

...

## Common Failure Modes

<!-- Agent guardrails: the following pitfalls were identified by the operator. Watch for these. -->
- [Failure mode 1 from operator interview]
- [Failure mode 2 from operator interview]
```

**Rules:**
- Top-level `#` heading: document type name only.
- `**Agent Instruction:**` block immediately after the title.
- One `##` section per top-level section the operator listed.
- Each field is a bullet with the field name in bold followed by `[Insert from transcript]`.
- Optional fields are marked with `(optional)` after the field name.
- A `## Common Failure Modes` section at the bottom lists operator-identified pitfalls as agent guardrails.
- DO NOT add content not derived from the operator's answers.

---

## Step 3 — Display for Review

Show the complete generated template to the operator. Ask:
`"Review the template above. Type CONFIRM to proceed to validation, or EDIT to describe changes."`

If EDIT: apply the requested changes and re-display. Repeat until CONFIRM.

---

## Step 4 — Validate Template

Before saving, apply the following checks inline:

**Check A:** Does the template contain at least one `## ` section heading?
- If NO → print: `"VALIDATION FAILED: No '## ' section heading found. Please add at least one section."` Then re-enter Step 3 with the issue noted.

**Check B:** Does the template contain at least one `[Insert from transcript]` placeholder?
- If NO → print: `"VALIDATION FAILED: No '[Insert from transcript]' placeholder found. Every field must use this placeholder."` Then re-enter Step 3 with the issue noted.

If both checks pass → proceed to Step 5.

---

## Step 5 — Anti-Overwrite Check and Derive Template ID

**Derive template_id:** Convert the document type name to `snake_case`.
- e.g., "My Document" → `my_document`
- e.g., "Software Architecture Decision Record" → `software_architecture_decision_record`

**Anti-overwrite check:** Read `.agents/schemas/templates/<template_id>.md`.
- If the file exists → print:
  `"WARNING: A template with ID '<template_id>' already exists at .agents/schemas/templates/<template_id>.md. Type CONFIRM to overwrite, or CANCEL to abort."`
  - If operator types CANCEL → abort: `"Save cancelled. The existing template was not modified."`
  - If operator types CONFIRM → proceed.
- If the file does not exist → proceed.

---

## Step 6 — Save and Confirm

Write the validated template to `.agents/schemas/templates/<template_id>.md`.

Print:
```
Template saved: .agents/schemas/templates/<template_id>.md
Template ID: <template_id>

To use this template, reference it in your workspace's state_graph.yml:
  modules:
    - id: <module_id>
      associated_files:
        template: .agents/schemas/templates/<template_id>.md
```

---

## Constraints

- DO NOT save the template until the operator has reviewed and CONFIRMED the output.
- DO NOT save a template that fails either validation check.
- DO NOT overwrite an existing template without explicit operator CONFIRM.
- DO NOT hallucinate section content — all structure must come from the operator interview.
