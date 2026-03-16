---
name: redteam
description: "[Pipeline] Loads an adversarial persona and generates targeted questions against a module draft, appending them to the master questionnaire with a 50-question cap."
trigger: /redteam
---

# Redteam Skill

**Invocation:** `claude /redteam [module_id] [persona_id] --workspace <path>`

Invoked by the orchestrator as a subprocess. Loads an adversarial persona and generates targeted questions against the module draft, appending them to the master questionnaire.

## Parse Arguments

From `$ARGUMENTS`:
- `module_id` — first positional argument
- `persona_id` — second positional argument
- `--workspace <path>` — the workspace directory path

If any are missing, print an error and exit with code 1.

## Execution Steps

**Step 1 — Load context**
- Resolve `workspace_path` from `--workspace`.
- Read `state_graph.yml`. Find the module matching `module_id`.
- Resolve the draft path: `<workspace>/active/draft_<module_id>.md`.
- Resolve the persona file: prefer `<workspace>/personas_snapshot/<persona_id>.md` (snapshot). Fall back to `.agents/schemas/personas/<persona_id>.md` if the snapshot does not exist.
- If the persona file is not found at either path, abort: `"ERROR: Persona '{persona_id}' not found in snapshot or global library."` Exit code 1.

**Step 2 — Check question cap**
- Read `<workspace>/active/module_<module_id>_questions.md` if it exists. Count existing numbered questions (lines matching `^\d+\.`).
- Read `module.max_questions` from `state_graph.yml` (default: `50`).
- `remaining_capacity = max_questions - current_count`
- If `remaining_capacity <= 0`, print:
  `"WARNING: Question cap of {max_questions} reached. Skipping persona '{persona_id}'."` Exit with code 0.

**Step 3 — Read inputs**
- Read the full draft content from `active/draft_<module_id>.md`.
- Read the persona file content as the system instruction.

**Step 4 — Generate questions**
Adopt the persona as your system instruction. Then, as that adversarial persona, generate a numbered Markdown list of targeted questions against the draft:

> Generate adversarial questions targeting every claim, assumption, and `[NEEDS_CLARIFICATION]` marker in the draft. Output strictly a numbered Markdown list. Maximum {remaining_capacity} questions. DO NOT output conversational filler.

**Step 5 — Enforce cap**
Count the generated questions. If count > `remaining_capacity`, truncate to `remaining_capacity` and print:
`"WARNING: Persona '{persona_id}' generated {count} questions. Truncated to {remaining_capacity} to stay within cap."`

**Step 6 — Append to questionnaire**
Append the following block to `<workspace>/active/module_<module_id>_questions.md`:
```
## Persona: <persona_id>
<truncated question list>
```
Create the file if it does not exist.

**Step 7 — Copy to candidate outputs**
Overwrite `<workspace>/tests/candidate_outputs/module_<module_id>_questions.md` with the full questionnaire file content.

**Step 8 — Update state**
Update `state_graph.yml` atomically:
1. Read current YAML.
2. Set `module.adversarial_state.status = "interview_in_progress"`.
3. Write to `state_graph.yml.tmp`, then rename to `state_graph.yml`.

**Step 9 — Confirm**
Print: `"Persona '{persona_id}': {added} questions added. Total: {total}. Remaining capacity: {remaining}."`

## Constraints

- DO NOT deduplicate questions automatically.
- DO NOT fail the pipeline if the cap is reached — skip gracefully with a warning.
- DO NOT use the live global persona file if a snapshot exists — always prefer the snapshot.
- DO NOT write non-atomically to `state_graph.yml`.
