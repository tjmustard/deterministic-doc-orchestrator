---
name: integrate
description: Synthesizes a module's baseline draft and adversarial Q&A answers into a final compiled document section. Routes output to tests/candidate_outputs/ only — status advances only after /promote approves.
---

# Integrate Skill

**Invocation:** `claude /integrate [module_id] --workspace <path>`

This skill is invoked by the orchestrator as a subprocess. It synthesizes the approved draft and Q&A answers into a final, defensible document section. Output is always routed to `tests/candidate_outputs/` first for operator review via `/promote`.

## Mode Detection

Parse `$ARGUMENTS` to extract:
- `module_id` — first positional argument
- `--workspace <path>` — the workspace directory path

If either is missing, print an error and exit with code 1.

## Execution Steps

**Step 1 — Load context**
- Resolve `workspace_path` from `--workspace`.
- Read `state_graph.yml`. Find the module matching `module_id`. If not found, abort.
- Resolve paths:
  - Draft: `<workspace>/active/draft_<module_id>.md`
  - Answers transcript: `<workspace>/transcripts/module_<module_id>_answers.md`
  - Template: `module.associated_files.template`

**Step 2 — Validate answers transcript**
- Read `transcripts/module_<module_id>_answers.md`.
- If the file is missing or empty, abort:
  `"ERROR: No answers transcript found for module '{module_id}'. Run /interview first."`
  Exit with code 1.

**Step 3 — Read inputs**
- Read the full template content (for schema structure reference).
- Read the full draft content (labeled "Baseline Draft").
- Read the full answers transcript content (labeled "Adversarial Q&A Answers").

**Step 4 — Synthesize final document**
Adopt the following role for the synthesis task:

> **System Instruction:** You are a Resolution Agent. Your role is to synthesize a baseline document draft with adversarial Q&A answers into a final, precise, and defensible document section. Follow the template schema strictly. DO NOT hallucinate. DO NOT introduce claims not supported by either the draft or the answers transcript.

Using the template schema as structure, update each section of the Baseline Draft using the relevant Q&A answers:
- Strengthen claims where the answers provide supporting evidence.
- Fill `[NEEDS_CLARIFICATION]` gaps where the answers provide information.
- For any gaps that still lack answers, document them explicitly as: `[UNRESOLVED: {description of missing information}]`.

**Step 5 — Write candidate output**
- Ensure `<workspace>/tests/candidate_outputs/` exists (create if needed).
- Write the integrated content to: `<workspace>/tests/candidate_outputs/final_<module_id>.md`
- DO NOT write to `<workspace>/compiled/final_<module_id>.md` — that path is reserved for after `/promote` approval.

**Step 6 — Do NOT update state_graph.yml**
Status advances to `integrated` ONLY after `/promote` approves the output. This skill does not touch `state_graph.yml`.

**Step 7 — Confirm**
Print:
```
Integration complete.
Candidate output: <workspace>/tests/candidate_outputs/final_{module_id}.md
Review the output, then run: /promote {module_id} --workspace {workspace_path}
```

## Constraints

- DO NOT write to `compiled/final_<module_id>.md` directly — output goes to `tests/candidate_outputs/` only.
- DO NOT advance module status — that is `/promote`'s responsibility.
- DO NOT introduce content not present in the draft or answers transcript.
- DO NOT write to `state_graph.yml` in this skill.
