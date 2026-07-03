# DDO v0.0.6: Writing a Structured Persona — Driving `ddo-create-persona`

## Overview

Every Red Team pass in DDO is only as sharp as the persona lens it runs
through. `ddo-red-team` doesn't critique your document against some generic
"is this good writing?" standard — it loads a specific persona file from
`ddo/personas/`, applies that persona's Attack Vectors one at a time, and
scores findings against that persona's own severity taxonomy. Change the
persona, and the same document gets a different, but equally rigorous,
critique.

This tutorial walks through **authoring a brand-new persona from scratch**,
using the existing `ddo-create-persona` skill. It does not add a new skill,
and it does not add a new persona — four personas already ship in this
release (`content_editor`, `meeting_recorder`, `meeting_facilitator`,
`project_stakeholder`) and are cited throughout as worked specimens of the
format. By the end you will understand:

- The **v0.0.4 AV-table persona format** — the six required sections and why
  the Attack Vectors section must be a Markdown table, not prose.
- How to **drive `ddo-create-persona`** end-to-end as an interactive,
  human-in-the-loop authoring session — batch by batch, gate by gate.
- The **persona → Red Team injection contract**: why a persona file is
  treated as untrusted, scoped input, and what stem-validation gate stands
  between a `persona` value and a filesystem read.
- Why **`tests/unit/test_personas.py` needs no code change** to cover a
  persona you just wrote.

This is a **narrated walkthrough**, not a script you run in CI. Authoring a
persona is a paced Q&A conversation with mandatory `[WAITING FOR USER
RESPONSE]` and `[WAITING FOR USER REVIEW]` gates — the whole point of
`ddo-create-persona` is that nothing gets written to disk without a human
approving the exact rendered draft first.

---

## Prerequisites

- **Repository cloned** — this tutorial runs from the root of the
  `deterministic-doc-orchestrator` repository.
- **Suite passing** — verify your environment is clean before you start:
  ```bash
  uv run pytest tests/unit/test_personas.py -q
  ```
- Read `ddo/skills/ddo-create-persona.md` once before starting a real
  session — this tutorial narrates its phases but the skill file is the
  authoritative execution logic.
- No YAML or template knowledge is required. A persona file is plain
  Markdown; it never touches `document_data.yaml` schemas directly.

---

## The v0.0.4 AV-Table Persona Format

Every persona under `ddo/personas/` is a Markdown file with six required
sections, in this order:

1. `## Domain` — what kind of document this persona reviews, who the typical
   reader is, and what that reader cares about most.
2. `## Reviewing Mission` — 2-4 sentences naming the persona's adversarial
   posture and the core quality bar it enforces.
3. `## Attack Vectors` — a **table**, not a bullet list, with the exact
   header `| ID | Name | When to apply |`. Each row is one attack vector:
   a sequential `AV-NN` ID, a `snake_case` name, and a one-sentence trigger
   condition for the Red Team probe.
4. `## Severity Taxonomy` — Critical / Major / Minor, each with a one-sentence
   definition and a parenthetical example drawn from this persona's own
   vectors.
5. `## Domain-Specific Format Rules` — the structural or language rules the
   source document must follow in this domain.
6. `## Interview Question Templates` — 2-5 question templates, ideally one
   per Attack Vector, that guide the `ddo-interview` phase when a finding
   maps back to this persona.

### Why the AV table, specifically

`ddo-red-team` (see `ddo/skills/ddo-red-team.md`) hard-fails if a persona
file has no `## Attack Vectors` **table** — a prose list of vectors is not
accepted, because Red Team needs a machine-checkable `AV-NN: <name>`
category to stamp on every finding. `tests/unit/test_personas.py` enforces
the same contract locally: it parses the table with a small `re`-based
parser (no third-party Markdown library) and asserts, for every persona
file discovered under `ddo/personas/*.md`:

- The `## Attack Vectors` section exists and its table has at least one row.
- IDs match `AV-\d+`, start at `AV-01`, are sequential with no gaps, and are
  unique within the file.
- Names match `^[a-z][a-z0-9_]*$` — no double underscores, no trailing
  underscore, no escaped `\_`.
- No `When to apply` cell contains a literal `|` (it would corrupt the
  table's column count).
- No cell is empty.
- The file contains no unresolved sentinel token (`[REQUIRES USER INPUT:` or
  `[[DDO::REQUIRES_INPUT:`).

### Worked specimens

Rather than duplicating persona bodies here, read the real files — each is
a complete, gate-passing example of a different domain applying the exact
same six-section shape:

| Persona | Path | Domain |
|---|---|---|
| `product_critic` | `ddo/personas/product_critic.md` | PRDs (the original v0.0.1 specimen) |
| `content_editor` | `ddo/personas/content_editor.md` | Blog posts / short-form narrative content |
| `meeting_recorder` | `ddo/personas/meeting_recorder.md` | Meeting notes and minutes |
| `meeting_facilitator` | `ddo/personas/meeting_facilitator.md` | Meeting agendas |
| `project_stakeholder` | `ddo/personas/project_stakeholder.md` | Project status reports |

Open `ddo/personas/content_editor.md` side by side with
`ddo/personas/product_critic.md`. Notice the sections are identical in
*name and order*, but every Attack Vector, severity example, format rule,
and interview template is specific to that domain. For instance,
`content_editor` opens its Attack Vectors table with:

```
| ID    | Name        | When to apply |
|-------|-------------|-----------------------------|
| AV-01 | weak_hook   | Does the opening line fail to create curiosity, tension, or a clear promise within the first two sentences? |
```

— a vector that would make no sense for a PRD, but follows exactly the same
`| ID | Name | When to apply |` contract that `product_critic`'s
`missing_acceptance_criteria` vector does. That structural sameness across
wildly different domains is what lets `ddo-red-team` and
`test_personas.py` treat every persona identically, regardless of what it
reviews.

> **A note on this tutorial's `input_files/` directory:** it is intentionally
> empty (see `.gitkeep`). The four persona specimens above are cited **by
> path reference only** — their full bodies are not copied here. An
> unregistered copy of a persona file would be an unguarded drift surface: if
> `ddo/personas/content_editor.md` were edited later, a stray duplicate in
> this tutorial would silently go stale with no test catching it. The
> project's anti-rot guard (`EXPECTED_MIRRORS`, tracked in
> `MiniPRD_08_AntiRotGuard_Hypergraph.md`) only registers *intentional*
> mirrors of source fixtures — persona files are reference material here,
> not fixtures this tutorial owns, so the correct move is a path reference,
> not a copy.

---

## Driving `ddo-create-persona`: A Narrated Walkthrough

What follows is a **prose narration** of a real authoring session — the
turns an author and the skill would actually exchange. If you invoke the
skill yourself (`ddo-create-persona`, or the AI reads
`ddo/skills/ddo-create-persona.md` directly and follows its Execution
Logic), you will see turns shaped like this. Nothing here is a shell
command to run; it's the interactive contract the skill follows.

### Phase 0 — Establish the slug

The skill first asks for a snake_case slug, which becomes both the filename
(`ddo/personas/<slug>.md`) and the `# Persona: <slug>` heading:

```
What should this persona be called? Provide a snake_case slug (e.g. `grant_reviewer`).
The file will be written to ddo/personas/<slug>.md.

[WAITING FOR USER RESPONSE]
```

Say you're building a lens for internal design-review documents. You answer
`design_reviewer`. The skill validates the slug against
`^[a-z][a-z0-9_]*$`, checks it doesn't contain `__` or a trailing `_`, and
only proceeds once a valid slug is confirmed. This is the same pattern
`ddo-red-team` later re-validates before it will read the file — see
"The Injection Contract" below.

### Phase 1 — Domain and Reviewing Mission (Batch 1 of 4)

The skill presents **at most two questions per turn** — this batch size
limit holds for the entire session:

```
Batch 1 of 4 — Domain & Reviewing Mission

Q1. Describe the domain this persona reviews.
    Include: document type, typical reader, and what that reader cares most about.

Q2. State this persona's Reviewing Mission in 2-4 sentences.
    It should name the persona's adversarial posture and the core quality standard it enforces.

[WAITING FOR USER RESPONSE]
```

You answer both in your own words. If either answer is too thin to draft
from — say you only wrote "design docs" with no reader or stakes — the
skill does not invent the rest. It records the literal sentinel
`[REQUIRES USER INPUT: reviewing mission not yet provided]` and will
surface it again later, rather than guessing what a design reviewer cares
about. This is the zero-hallucination invariant applied to persona
authoring itself: the skill would rather show you an obviously-unfinished
placeholder than a plausible-sounding invention.

### Phase 2 — Attack Vectors (Batches 2 through N)

This is the heart of the persona. The skill explains the AV-table format
once, then asks for vectors two at a time:

```
Batch 2 of 4 — Attack Vectors

Attack Vectors will be formatted as an AV-NN table. Provide each vector as:
  - Name — snake_case identifier (e.g. `missing_acceptance_criteria`).
  - When to apply — one sentence describing when the Red Team probe fires.
             Rule: must NOT contain a literal | character.

I will assign IDs (AV-01, AV-02, ...) sequentially.

Vector AV-01:
  Name: ___
  When to apply: ___

Vector AV-02 (optional — leave blank if this is your last vector):
  Name: ___
  When to apply: ___

[WAITING FOR USER RESPONSE]
```

Say you answer:

- AV-01: `missing_rationale` — "Does a design decision lack a stated reason
  it was chosen over the alternatives considered?"
- AV-02: `no_rollback_plan` — "Does the design omit what happens if the
  chosen approach needs to be reverted after shipping?"

The skill validates each vector **immediately** — name pattern, uniqueness,
no literal `|` in the trigger sentence — before assigning the next
sequential ID, and then asks whether you want to add more:

```
Vectors so far: AV-01 through AV-02

Add more vectors? Provide the next pair (or leave both blank to close the AV table).
...
[WAITING FOR USER RESPONSE]
```

This continues until you leave both slots blank or say "done." At least one
Attack Vector is required — the skill will not let you close an empty
table, because `ddo-red-team` has nothing to critique against otherwise.

### Phase 3 — Severity Taxonomy and Format Rules (Batch 3 of 4)

```
Batch 3 of 4 — Severity Taxonomy & Format Rules

Q1. Define the three severity levels for this domain (Critical, Major, Minor).
    For each, give: a one-sentence definition and one parenthetical example.

Q2. List any domain-specific formatting or language rules the source document must follow.

[WAITING FOR USER RESPONSE]
```

Compare your own answer here against how `meeting_recorder` anchors its
severities to concrete vector names — e.g. its Critical tier reads "a
decision or action item is recorded with no traceable source, or an action
item has no owner." A good severity definition names one of *this
persona's own* Attack Vectors as the worked example, not a generic
description.

### Phase 4 — Interview Question Templates (Batch 4 of 4)

```
Batch 4 of 4 — Interview Question Templates

Provide 2-5 interview question templates — one per Attack Vector is recommended.
Format each as:
  **For <Vector Name or topic>:** "<question text>"

[WAITING FOR USER RESPONSE]
```

These templates are what `ddo-interview` reaches for when a Red Team
finding maps to one of this persona's vectors — see, for example, how
`project_stakeholder`'s "For Status Sugarcoating" template gives the
interview phase exact, ready-to-adapt phrasing rather than a generic
"please clarify."

### Phase 5 — Sentinel resolution

Before anything is assembled into a draft, the skill scans every field you
supplied for `[REQUIRES USER INPUT:` and `[[DDO::REQUIRES_INPUT:` tokens.
If your Batch 1 answer left the reviewing mission unresolved, it comes back
here:

```
The following fields still contain unresolved sentinels:

  - reviewing_mission: [REQUIRES USER INPUT: reviewing mission not yet provided]

Please supply the missing content now.

[WAITING FOR USER RESPONSE]
```

This loop repeats until zero sentinels remain. No persona reaches the
review gate with a placeholder still in it.

### Phase 6 — Draft preview and the HITL review gate

Only now does the skill assemble the full six-section draft and show it to
you in full, verbatim, followed by a hard stop:

```
--- DRAFT PERSONA: ddo/personas/design_reviewer.md ---

# **Persona: design_reviewer**

## **Domain**
...

## **Attack Vectors**

| ID | Name | When to apply |
|---|---|---|
| AV-01 | missing_rationale | Does a design decision lack a stated reason it was chosen over the alternatives considered? |
| AV-02 | no_rollback_plan | Does the design omit what happens if the chosen approach needs to be reverted after shipping? |

...

--- END DRAFT ---

Review the draft above.
  - Type APPROVE to write the file.
  - Type EDIT followed by your corrections to revise and re-display.
  - Type CANCEL to abort without writing.

[WAITING FOR USER REVIEW]
```

This is the single most important gate in the whole flow: the skill will
not write anything to disk until you type the literal word `APPROVE`.
`EDIT <corrections>` sends you back through sentinel resolution and
re-displays the draft; `CANCEL` aborts cleanly with nothing written. There
is no silent auto-advance past this marker — if you're following along
in a live session and the assistant tries to move on without your
`APPROVE`, that's a bug in the run, not the intended behavior.

### Phase 7 — Overwrite guard

If `ddo/personas/design_reviewer.md` already exists, the skill halts again
before writing — a cognitive `exists()` check via the Read tool, not a
filesystem-level lock:

```
ddo/personas/design_reviewer.md already exists.

To overwrite, type the exact filename: design_reviewer.md
To abort, press Enter or type anything else.

[WAITING FOR USER RESPONSE]
```

Only an exact, case-sensitive match of the filename authorizes an
overwrite. This guard exists specifically so an author can't accidentally
clobber `content_editor.md` by fat-fingering a slug that happens to
collide.

### Phase 8 — Write

With `APPROVE` given and (if applicable) the overwrite confirmed, the skill
runs one more checklist — zero sentinels, correct AV table header,
sequential IDs, valid names, no pipes in trigger cells — and only then
calls the Write tool. It never calls `ddo.ingest.atomic_write` or any
`ddo_core` function for this; the overwrite guard is cognitive-only by
design (so persona authoring stays decoupled from the render pipeline's
atomic-write machinery). The confirmation message names your next step
explicitly:

```
Persona written to ddo/personas/design_reviewer.md

Next steps:
  1. Run `uv run pytest tests/unit/test_personas.py` — the new persona must pass all assertions.
  2. If tests pass, the persona is usable by ddo-red-team.
  3. Do NOT auto-promote to tests/fixtures/ — human review gates promotion.
```

---

## The Persona → Red Team Injection Contract

A persona file is not a trusted, hardcoded config — it's a **name resolved
at runtime**, and `ddo-red-team` treats it accordingly. Understanding this
contract matters even if you never touch `ddo-red-team`'s implementation,
because it's the reason the authoring skill enforces a strict slug pattern
in Phase 0.

From `ddo/skills/ddo-red-team.md`, the resolution order for which persona
file to load is:

1. An explicit `persona` argument to the skill.
2. `meta.persona` read out of the document's own `document_data.yaml`.
3. If neither is present, the skill refuses to guess and asks the user to
   pick one explicitly.

Both of those sources — an argument and a value stored in a YAML file — are
**untrusted input** from the skill's point of view. Before either one is
used to build a filesystem path, it must pass a stem-validation gate:

```
^[a-z][a-z0-9_]*$
```

Any value containing `.`, `/`, or `..` is rejected outright, and the
rejection is a **named, hard failure** — not a silent fallback to a default
persona:

```
Error: persona 'value' is not a valid persona stem (must match ^[a-z][a-z0-9_]*$).
Refusing to resolve a path outside ddo/personas/.
```

Two details make this gate stronger than it might first look:

- **It is re-applied on every read, including for a *stored* value.** A
  `meta.persona` field sitting in `document_data.yaml` doesn't get a pass
  just because it "already exists" in the file — DDO treats YAML source
  data as attacker-reachable in principle (someone could hand you a
  `document_data.yaml` with a crafted `meta.persona` value), so the gate
  runs identically whether the value came from a CLI-style argument or
  from the YAML itself.
- **A missing `## Attack Vectors` table is also a hard failure**, separate
  from the stem gate. Once a persona file *is* successfully read, Red Team
  scans it for the table before doing anything else, and refuses to fall
  back to free-text categories if the table is absent. This is exactly the
  contract `test_personas.py` checks statically, and the reason Phase 6's
  draft preview always includes the fully-rendered table before you're
  ever asked to `APPROVE`.

The practical upshot for you as a persona author: as long as your slug came
out of Phase 0 validation (which every path through `ddo-create-persona`
enforces), your persona file is a legitimate, resolvable target for
`ddo-red-team` the moment it's written and passes
`tests/unit/test_personas.py` — there is no separate registration step.

---

## Why `test_personas.py` Needs No Code Change

`tests/unit/test_personas.py` discovers what it validates via a glob, not a
hardcoded list:

```python
_PERSONA_DIR = Path(__file__).resolve().parents[2] / "ddo" / "personas"
_PERSONA_PATHS = sorted(_PERSONA_DIR.glob("*.md"))
```

Every test in the file is `@pytest.mark.parametrize("path", _PERSONA_PATHS, ...)`
— meaning the moment `ddo-create-persona` writes
`ddo/personas/design_reviewer.md`, the next `uv run pytest
tests/unit/test_personas.py` run parametrizes over it automatically and
runs the full battery of AV-table structural checks (ID sequencing, name
format, non-empty cells, no literal pipes, no leftover sentinels) with zero
edits to the test file itself. This is exactly how the four personas this
tutorial cites as specimens — `content_editor`, `meeting_recorder`,
`meeting_facilitator`, `project_stakeholder` — already came to pass the
suite: nobody added a `test_content_editor_av_ids` function; they simply
exist as `.md` files under `ddo/personas/` and the glob picked them up.

You can confirm this yourself:

```bash
uv run pytest tests/unit/test_personas.py -v
```

Look at the parametrized test IDs in the output (`test_av_table_exists[content_editor]`,
`test_av_table_exists[meeting_recorder]`, etc.) — one per discovered `.md`
stem, generated entirely from what's on disk.

If you'd like a faster, local signal while you're still drafting — before
running the full suite — this tutorial ships a small read-only helper that
mirrors the same checks:

```bash
uv run tutorials/ddo-v006-writing-structured-personas/code_samples/check_persona_av_table.py \
  ddo/personas/content_editor.md
```

This script is **not** part of the test suite and is never invoked by CI —
`tests/unit/test_personas.py` remains the single authoritative gate. It
exists purely so you can sanity-check a draft's table structure by hand
without a pytest invocation, while you're still iterating inside a
`ddo-create-persona` session (e.g. during Phase 6's `EDIT` loop, before you
ever save the file).

---

## What This Tutorial Does *Not* Do

- It does not add a new skill. `ddo-create-persona` already exists and is
  used exactly as documented in `ddo/skills/ddo-create-persona.md`.
- It does not add a new persona. The four cited specimens
  (`content_editor`, `meeting_recorder`, `meeting_facilitator`,
  `project_stakeholder`) were authored as part of this release's own
  MiniPRDs, not by this tutorial.
- It does not copy any persona file's body into `input_files/`. Every
  specimen is referenced by its real, canonical path under
  `ddo/personas/` so there is exactly one copy of each persona in the
  repository and nothing here can drift out of sync with it.
- It does not treat persona authoring as a CI-executed step. Every phase
  above ends at a `[WAITING FOR USER RESPONSE]` or
  `[WAITING FOR USER REVIEW]` marker that only a human can clear.

---

## Related

- `ddo/skills/ddo-create-persona.md` — the authoritative skill this
  tutorial narrates. Read it directly before running a real authoring
  session.
- `ddo/skills/ddo-red-team.md` — the consumer of persona files; see its
  "Resolve the Persona" section for the stem-validation gate and the
  `## Attack Vectors` table hard-failure check described above.
- `tests/unit/test_personas.py` — the glob-based structural gate every
  persona file must pass, new or old.
- `ddo/personas/product_critic.md` — the original v0.0.1 specimen, PRDs.
- `ddo/personas/content_editor.md`,
  `ddo/personas/meeting_recorder.md`,
  `ddo/personas/meeting_facilitator.md`,
  `ddo/personas/project_stakeholder.md` — the four v0.0.4-format specimens
  cited throughout this tutorial.
- `tutorials/ddo-v001-prd-workflow/tutorial.md` — the PRD render workflow
  that consumes `meta.persona` as an input to `ddo-red-team`.
