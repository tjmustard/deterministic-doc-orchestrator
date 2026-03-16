---
name: forge_persona
description: Creates or updates adversarial persona files via guided interview. On --update, warns if the persona is used by an active job. Writes versioned Markdown files to .agents/schemas/personas/.
---

# Forge Persona Skill

**Invocation:**
- `claude /forge_persona` — CREATE mode: guided interview to produce a new persona.
- `claude /forge_persona --update <persona_id>` — UPDATE mode: load, modify, increment version.

This skill guides the operator through defining an adversarial reviewer persona for use in the pipeline's red-team phase.

## Mode Detection

Parse `$ARGUMENTS`:
- If `--update <persona_id>` is present → **UPDATE mode**.
- Otherwise → **CREATE mode**.

---

## CREATE Mode

**Step 1 — Conduct interview (max 2 questions per turn)**

Ask the operator the following questions in two batches:

**Batch 1:**
1. What document type will this persona interrogate? (e.g., "document", "PRD", "technical spec")
2. What is the persona's professional role/identity? (e.g., "Document Examiner", "Security Auditor", "Commercial Lead")

Wait for answers, then ask:

**Batch 2:**
3. What is this persona's primary adversarial angle? (e.g., "prior art and obviousness", "security vulnerabilities", "market viability")
4. What are the 3 most important things this persona forces the author to prove?

Wait for answers, then ask:

**Batch 3:**
5. What output constraints apply? (e.g., "numbered list only", "no conversational filler", "focus on edge cases")

**Step 2 — Derive persona ID**
Convert the persona name/role to `snake_case` for the `persona_id`. For example, "Document Examiner" → `document_examiner`.

**Step 3 — Anti-overwrite check**
Check if `.agents/schemas/personas/<persona_id>.md` already exists. If it does, abort:
`"ERROR: Persona '{persona_id}' already exists. Use --update {persona_id} to modify it."`

**Step 4 — Synthesize persona file**
Generate the persona file using this exact structure:

```markdown
---
id: <persona_id>
version: 1
document_type: <document_type>
changelog:
  - "v1 (<YYYY-MM-DD>): Initial creation."
---
# Adversarial Persona: <Persona Name>
**Agent Instruction:** <Role and primary adversarial objective in 2-3 sentences.>

**Constraints:**
1. <Constraint derived from interview answer 1>
2. <Constraint derived from interview answer 2>
3. DO NOT output conversational filler.
```

Use the actual current date (YYYY-MM-DD format) for the changelog entry.

**Step 5 — Display for review**
Show the complete generated persona to the operator. Ask:
`"Review the persona above. Type CONFIRM to save, or EDIT to describe changes."`

If EDIT: apply the operator's requested changes and re-display. Repeat until CONFIRM.

**Step 6 — Save**
Write the persona to `.agents/schemas/personas/<persona_id>.md`.

**Step 7 — Confirm**
Print:
```
Persona saved: .agents/schemas/personas/<persona_id>.md
To use this persona, add '<persona_id>' to the applied_personas list in your workspace's state_graph.yml.
```

---

## UPDATE Mode

**Step 1 — Load existing persona**
Read `.agents/schemas/personas/<persona_id>.md`. If not found, abort:
`"ERROR: Persona '{persona_id}' not found at .agents/schemas/personas/{persona_id}.md."`

**Step 2 — Check active workspace usage**
Read `.agents/workspace_registry.yml` (if it exists). For each registered workspace:
- Load `<workspace_path>/state_graph.yml`.
- For each module in `modules`, check if `<persona_id>` appears in `applied_personas` AND the module `status` is not `integrated`.
- If found, print:
  `"WARNING: This persona is actively used by job '<job_name>' (module '<module_id>', status: '<status>'). Updating will NOT affect the running pipeline (snapshot is used), but future runs will use the new version. Type CONFIRM to proceed."`
  Read operator input. If not `CONFIRM`, abort: `"Update cancelled."`

**Step 3 — Display and edit**
Display the current persona content to the operator. Ask what sections they want to change. Re-interview those specific sections or accept free-form edits.

**Step 4 — Request changelog entry**
Ask: `"Briefly describe this change for the changelog (e.g., 'Added constraint on obviousness claims')."`

**Step 5 — Update and save**
- Increment `version` in frontmatter by 1.
- Append changelog entry: `"v<N> (<YYYY-MM-DD>): <operator-provided summary>."`
- Write the updated file back to `.agents/schemas/personas/<persona_id>.md`.

**Step 6 — Confirm**
Print a summary of changed sections and the new version number:
```
Persona '<persona_id>' updated to version <N>.
Saved: .agents/schemas/personas/<persona_id>.md
```

---

## Constraints

- DO NOT save without operator review and CONFIRM.
- DO NOT overwrite an existing persona in CREATE mode — require `--update` for modifications.
- DO NOT skip the workspace registry check in UPDATE mode.
- DO NOT modify persona files used by active jobs without explicit `CONFIRM`.
