# **Skill: ddo-create-persona**

## **Description**

Guides a persona author through an interactive, paced Q&A loop to produce a new DDO persona
in the standard 6-section format.  The Attack Vectors section is collected and validated as an
`AV-NN` table (`| ID | Name | When to apply |`).  Human-in-the-loop gated: the persona file is
written only after the author approves a rendered draft preview.

This skill targets **new** personas authored from scratch.  Do not use it to patch an existing
persona — edit `ddo/personas/<name>.md` directly for incremental changes.

## **Inputs**

1. `name`: The snake_case persona slug (will become `ddo/personas/<name>.md` and the `# Persona:
   <name>` heading).  Must match `^[a-z][a-z0-9_]*$`.
2. `domain_hint` (optional): A one-sentence hint about the domain to pre-seed the first question batch.

## **Invariants (read before acting)**

- **Zero hallucination.** If you cannot source a field value from what the author has told you, write the
  literal sentinel `[REQUIRES USER INPUT: <reason>]` and surface it in a later question batch.  Never
  invent domain names, mission statements, vector descriptions, or example questions.
- **HITL gates are mandatory.** Halt at every `[WAITING FOR USER RESPONSE]` and `[WAITING FOR USER REVIEW]`
  marker.  Never auto-advance to the next phase.
- **No `ddo_core` dependency.** The overwrite guard in Phase 5 is cognitive only — do not call
  `ddo.ingest.atomic_write` or any `ddo_core` function (RT-03/RT-12).
- **AV-NN table is required.** The `## Attack Vectors` section MUST be rendered as a Markdown table
  with header `| ID | Name | When to apply |`, not as a prose list.
- **Sentinels must be resolved before writing.** Before the Write tool call, scan the assembled draft for
  `[REQUIRES USER INPUT:` and `[[DDO::REQUIRES_INPUT:`.  If any sentinel remains, re-enter the Q&A loop
  to elicit the missing content (RT-13).
- **Batch size ≤ 2.** Present at most two questions per turn.

## **Execution Logic**

### Phase 0 — Establish Slug

If `name` was not supplied:

```
What should this persona be called? Provide a snake_case slug (e.g. `grant_reviewer`).
The file will be written to ddo/personas/<slug>.md.

[WAITING FOR USER RESPONSE]
```

Validate the slug:
- Matches `^[a-z][a-z0-9_]*$`
- Does not contain `__` (consecutive underscores)
- Does not end with `_`

If invalid, explain the constraint and re-ask.  Do not proceed until a valid slug is confirmed.

---

### Phase 1 — Domain + Reviewing Mission (Batch 1)

Present both questions in a single turn:

```
Batch 1 of 4 — Domain & Reviewing Mission

Q1. Describe the domain this persona reviews.
    Include: document type (e.g. "scientific papers", "PRDs"), typical reader, and what that reader cares most about.

Q2. State this persona's Reviewing Mission in 2–4 sentences.
    It should name the persona's adversarial posture and the core quality standard it enforces.

[WAITING FOR USER RESPONSE]
```

Record `domain` and `reviewing_mission` from the author's answers.
Emit `[REQUIRES USER INPUT: domain not yet provided]` or `[REQUIRES USER INPUT: reviewing mission not yet provided]` if an answer is absent or too thin to draft.

---

### Phase 2 — Attack Vectors (Batches 2-N, one vector pair per turn)

Explain the format once before the first vector:

```
Batch 2 of 4 — Attack Vectors

Attack Vectors will be formatted as an AV-NN table.  Provide each vector as:
  • Name  — snake_case identifier (e.g. `missing_acceptance_criteria`).
             Rules: matches ^[a-z][a-z0-9_]*$, no __ or trailing _, unique in this persona.
  • When to apply — one sentence describing when the Red Team probe fires.
             Rule: must NOT contain a literal | character.

I will assign IDs (AV-01, AV-02, …) sequentially.

Vector AV-01:
  Name: ___
  When to apply: ___

Vector AV-02 (optional — leave blank if this is your last vector):
  Name: ___
  When to apply: ___

[WAITING FOR USER RESPONSE]
```

After each response:

1. **Validate each supplied vector immediately:**
   - Name matches `^[a-z][a-z0-9_]*$`, no `__`, no trailing `_`, no escaped `\_`.
   - Name is unique across already-collected vectors.
   - "When to apply" cell contains no literal `|`.
   - If a violation is found, explain it and re-ask only the offending field.

2. **Assign sequential IDs** (AV-01, AV-02, …) to accepted entries; never reuse an ID.

3. **Ask if more vectors are needed:**
   ```
   Vectors so far: AV-01 through AV-{N}

   Add more vectors?  Provide the next pair (or leave both blank to close the AV table).

   Vector AV-{N+1}:
     Name: ___
     When to apply: ___

   Vector AV-{N+2} (optional):
     Name: ___
     When to apply: ___

   [WAITING FOR USER RESPONSE]
   ```

4. Continue until the author leaves both slots blank or explicitly says "done."

Minimum: at least **one** Attack Vector is required before advancing.

---

### Phase 3 — Severity Taxonomy + Domain-Specific Format Rules (Batch 3)

```
Batch 3 of 4 — Severity Taxonomy & Format Rules

Q1. Define the three severity levels for this domain (Critical, Major, Minor).
    For each, give: a one-sentence definition and one parenthetical example.

Q2. List any domain-specific formatting or language rules the source document must follow.
    These become the "Format Rules" section.  A short bullet list is fine.

[WAITING FOR USER RESPONSE]
```

Record `severity_taxonomy` and `format_rules`.
Emit `[REQUIRES USER INPUT: severity taxonomy not provided]` or `[REQUIRES USER INPUT: format rules not provided]` if absent.

---

### Phase 4 — Interview Question Templates (Batch 4)

```
Batch 4 of 4 — Interview Question Templates

Provide 2–5 interview question templates — one per Attack Vector is recommended.
Format each as:
  **For <Vector Name or topic>:** "<question text>"

These templates guide the ddo-interview phase when a finding maps to this persona's vectors.

[WAITING FOR USER RESPONSE]
```

Record `interview_templates`.
Emit `[REQUIRES USER INPUT: interview question templates not provided]` if absent.

---

### Phase 5 — Sentinel Resolution (inline)

After all four batches are recorded, scan every collected field for:
- `[REQUIRES USER INPUT:`
- `[[DDO::REQUIRES_INPUT:`

If any sentinel is present, surface each one explicitly:

```
The following fields still contain unresolved sentinels:

  • <field name>: [REQUIRES USER INPUT: <reason>]

Please supply the missing content now.

[WAITING FOR USER RESPONSE]
```

Repeat until zero sentinels remain.  Do not advance to Phase 6 while any sentinel is present.

---

### Phase 6 — Draft Preview + HITL Review Gate

Assemble the full draft using this template:

```markdown
# **Persona: {name}**

## **Domain**

{domain}

## **Reviewing Mission**

{reviewing_mission}

## **Attack Vectors**

| ID | Name | When to apply |
|---|---|---|
| AV-01 | {av_01_name} | {av_01_when} |
| AV-02 | {av_02_name} | {av_02_when} |
…

## **Severity Taxonomy**

{severity_taxonomy_as_bullet_list}

## **Domain-Specific Format Rules**

{format_rules_as_bullet_list}

## **Interview Question Templates**

*(Use these to format your dialogue during the ddo-interview phase)*

{interview_templates_as_bullet_list}
```

Display the assembled draft in full, then halt:

```
--- DRAFT PERSONA: ddo/personas/{name}.md ---

{full_draft}

--- END DRAFT ---

Review the draft above.
  • Type APPROVE to write the file.
  • Type EDIT followed by your corrections to revise and re-display.
  • Type CANCEL to abort without writing.

[WAITING FOR USER REVIEW]
```

Do not write the file until the author types `APPROVE` (case-insensitive).
If the author types `EDIT`, apply the correction, run through sentinel resolution again, and re-display.
If the author types `CANCEL`, abort and inform the author that no file was written.

---

### Phase 7 — Overwrite Guard (cognitive)

Before calling the Write tool, perform a cognitive `exists()` check:

**Use the Read tool** to attempt reading `ddo/personas/{name}.md`.

- If the Read returns content (file exists): halt immediately —

  ```
  ddo/personas/{name}.md already exists.

  To overwrite, type the exact filename: {name}.md
  To abort, press Enter or type anything else.

  [WAITING FOR USER RESPONSE]
  ```

  Proceed with the write **only** if the author types the literal filename `{name}.md` (exact match, case-sensitive).
  Any other input → abort and report that no file was written.

- If the Read returns "file not found" (file does not exist): proceed immediately to Phase 8.

---

### Phase 8 — Write

Final pre-write checklist (cognitive):
1. Zero sentinels in assembled draft (`[REQUIRES USER INPUT:` / `[[DDO::REQUIRES_INPUT:` absent).
2. AV table header is `| ID | Name | When to apply |`.
3. All AV IDs are sequential from AV-01 with no gaps.
4. All AV names match `^[a-z][a-z0-9_]*$`, no `__`, no trailing `_`, no `\_`.
5. All AV names are unique within this persona.
6. No "When to apply" cell contains a literal `|`.
7. Author has typed `APPROVE` at the review gate.
8. If file existed: author has confirmed with the exact filename.

If all checks pass, write via the **Write tool**:

```
target: ddo/personas/{name}.md
content: {assembled_draft}
```

After a successful write, display:

```
Persona written to ddo/personas/{name}.md

Next steps:
  1. Run `uv run pytest tests/unit/test_personas.py` — the new persona must pass all assertions.
  2. If tests pass, the persona is usable by ddo-red-team.
  3. Do NOT auto-promote to tests/fixtures/ — human review gates promotion.
```

## **Negative Constraints**

- **DO NOT** call `ddo.ingest.atomic_write` or any `ddo_core` module — the overwrite guard is cognitive only (RT-03/RT-12).
- **DO NOT** write the file before the `[WAITING FOR USER REVIEW]` gate and an explicit `APPROVE`.
- **DO NOT** overwrite an existing persona unless the author types the literal filename as confirmation (RT-03).
- **DO NOT** write a draft containing `[REQUIRES USER INPUT:` or `[[DDO::REQUIRES_INPUT:` tokens (RT-13).
- **DO NOT** invent domain descriptions, mission statements, AV vectors, severity definitions, or interview questions — emit sentinels and surface them in a later batch.
- **DO NOT** render the Attack Vectors section as a prose list; the AV-NN table format is mandatory.
- **DO NOT** use escaped underscores `\_` in AV Name cells; raw `_` only (RT-04).
- **DO NOT** allow a literal `|` in any "When to apply" cell (RT-06).
- **DO NOT** add a `.claude/commands/` bridge — `ddo-*` skills have none.
- **DO NOT** auto-promote the written persona to `tests/fixtures/` — human gate governs promotion.
- **DO NOT** present more than 2 questions per turn.
- **DO NOT** auto-advance past any `[WAITING FOR USER RESPONSE]` or `[WAITING FOR USER REVIEW]` marker.

## **Post-Condition**

When the Write tool call completes successfully:

```
ddo/personas/{name}.md written.

Run: uv run pytest tests/unit/test_personas.py
All personas (including the new one) must pass AV-table validation before
the persona can be used in a Red Team run.
```

If the author cancelled at any gate:

```
Persona authoring cancelled. No file was written.
```
