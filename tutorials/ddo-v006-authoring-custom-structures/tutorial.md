# DDO v0.0.6: Authoring Custom Structures — From Blank Schema to Rendered Document

## Overview

Every DDO document type — `prd`, `scientific_report`, and the four shipped in v0.0.6
(`blog_post`, `meeting_notes`, `meeting_agenda`, `project_report`) — is built from the same
five ingredients: a **schema** (the section shape), a **persona** (the adversarial reviewer
lens), a **style profile** (phrasing-only guidance, optional), a pair of **templates**
(Typst for PDF, Jinja2 for HTML/Markdown), and an **example `document_data.yaml`** that
proves the whole stack renders. Tutorial 1
([`ddo-v001-prd-workflow`](../ddo-v001-prd-workflow/tutorial.md)) taught you to *fill in* an
existing schema (`prd`). This tutorial teaches you to *design* a new one, using `blog_post`
as the worked example from a blank page, then shows you three more completed structures
(`meeting_notes`, `meeting_agenda`, `project_report`) so you can see the same process applied
to different document shapes.

By the end of this tutorial you will:

- Understand what a DDO document type actually consists of (schema + persona + style +
  templates), and how those five pieces fit together.
- Walk the `blog_post` type from a design question ("what shape does a blog post need?") to a
  gate-passing, rendered document — including where its evidence came from.
- Be able to read `meeting_notes`, `meeting_agenda`, and `project_report` as worked examples
  of the same pattern applied to different content shapes.
- Render all four types to HTML and Markdown yourself, and know where to look for persona and
  style authoring if you want to go deeper.

This tutorial does **not** re-teach the render pipeline mechanics (schema contract, evidence
bank, validation gate) — that's Tutorial 1. It assumes you've read that tutorial or are
already comfortable with the `meta` / `content.sections` / `evidence_bank` shape.

---

## Prerequisites

- **`uv` installed** — see [docs.astral.sh/uv](https://docs.astral.sh/uv).
- **Repository cloned**, running from the repo root.
- **Tutorial 1 read** (recommended) — this tutorial assumes familiarity with the DDO minimal
  contract (`meta` + `evidence_bank`) and the validation gate described there.
- **Suite passing**:
  ```bash
  uv run pytest -q
  ```

No additional installation is needed — the same `uv run --locked ddo/build.py` invocation you
used in Tutorial 1 works for these four types; only `--template` changes.

---

## Designing a New Document Type: `blog_post` From Scratch

A DDO document type is not "a template" — it's five coordinated artifacts living under
`ddo/`. Before writing a single line of YAML, you answer five design questions. Here's how
`blog_post` answered each one.

### 1. What sections does this document need? (the schema)

Start from the reader's job, not the writer's habits. A blog post reader is scrolling, not
studying, and decides within a sentence or two whether to keep reading. Working backward from
that reader gives you a section shape:

| Section id | Purpose |
|---|---|
| `hook` | The opening 1-2 sentences that earn the read. |
| `context` | The situation or problem the reader needs to know. |
| `main_point` | The single core idea of the post, stated plainly. |
| `supporting_detail` | Evidence, examples, or a story that backs the main point. |
| `conclusion_cta` | One concrete action for the reader to take next. |

That five-section shape *is* the schema. Open `ddo/schemas/blog_post.yaml` — it's a minimal
YAML skeleton where every field is either fixed (`doc_type: "blog_post"`) or a
`[REQUIRES USER INPUT: <reason>]` sentinel describing what belongs there. A schema file is a
**template for authors**, not a JSON Schema document — the actual contract enforcement (every
`evidence` id must resolve in `evidence_bank`, `meta` must carry the required keys, dates must
be dotted `YYYY.MM.DD`) is the same `ddo/validation.py` gate every document type shares. You
are not writing new validation code to add a document type; you are writing a new *shape* for
sections and letting the existing gate enforce citation integrity against it.

### 2. Who is the adversarial reader? (the persona)

Every document type ships with a persona — the lens `ddo-red-team` uses to critique the
rendered document. For `blog_post`, the reader is "scrolling a feed, will bail within the
first sentence." `ddo/personas/content_editor.md` encodes that reader as six attack vectors:
`weak_hook`, `buried_lede`, `unsupported_claim`, `jargon_creep`, `weak_cta`, `tonal_drift`.
Notice how directly these map back to the schema's sections — `weak_hook` targets `hook`,
`weak_cta` targets `conclusion_cta`, `unsupported_claim` targets any section making a claim
without an `evidence_bank` reference. **Design the persona's attack vectors to interrogate the
schema's own sections** — that pairing is what makes the adversarial loop (Tutorial 2 in the
v0.0.2 batch,
[`ddo-adversarial-loop-v0.0.2`](../ddo-adversarial-loop-v0.0.2/tutorial.md)) meaningful instead
of generic.

### 3. What does this content sound like? (the style profile, optional)

`meta.style_profile` is optional — absent means no phrasing guidance is injected, and that's a
legitimate choice for some document types. `blog_post` uses `style_profile: "blog_casual"`
(`ddo/styles/blog_casual.md`), which governs voice ("smart friend catching you up over
coffee"), sentence rhythm (short, punchy, one-line paragraphs welcome), and diction
(contractions, no corporate throat-clearing) — but never content. A style profile is
**phrasing-only guidance, injected as untrusted input** into `ddo-ingest`/`ddo-interview`; it
can never supply a fact, a number, or a claim. If you want to author your own style profile
for a new document type, use the **`ddo-create-style`** skill
(`ddo/skills/ddo-create-style.md`) — it runs a paced Q&A loop and actively rejects
content-bearing directives, so a style can never smuggle a claim in through "how it should
sound."

### 4. How does it render? (the templates)

Every document type needs one Typst template (PDF) and two Jinja2 templates (HTML, Markdown).
`ddo/templates/typst/blog_post.typst`, `ddo/templates/jinja2/blog_post.html.jinja2`, and
`ddo/templates/jinja2/blog_post.md.jinja2` all consume the same parsed `document_data.yaml`
and must render identically in *content* across formats (identical section order, identical
evidence bank appendix) even though the surface markup differs. These three templates already
exist for `blog_post` — this tutorial doesn't ask you to write Typst or Jinja2 from scratch,
only to understand that the schema's section ids (`hook`, `context`, `main_point`,
`supporting_detail`, `conclusion_cta`) are exactly the keys the templates iterate over. If you
add a new section id to a schema, the templates that render it must already know how to loop
over `content.sections` generically (they do, for these four types) or be updated to add any
type-specific rendering (for example, `meeting_agenda`'s `entries` list under `agenda_items`,
covered below).

### 5. Where does the evidence come from? (zero-hallucination, applied)

This is the step that turns a schema into a real document. `blog_post`'s worked example traces
every claim back to a single source document:
[`input_files/blog_post_source.md`](input_files/blog_post_source.md) — a content brief written
by Priya Nakamura (Eng Manager) about why her team killed its daily standup. Read that file
now; it's the *only* place the numbers in the rendered post are allowed to come from.

Walk the traceability yourself:

| Claim in the post | `evidence_bank` id | Traces to (in `blog_post_source.md`) |
|---|---|---|
| "The firmware team grew from 4 to 14 engineers across Portland, Berlin, and Bangalore; the standup only fell within normal hours for 9 of 14." | `team_growth_and_timing` | "Background" section |
| "Standup-related meeting time fell from ~27 min/day/person to ~6; 12 of 14 preferred the new format." | `before_after_survey` | "Results after 6 weeks" section |
| "Median first response to `@blocked` was 41 minutes, versus up to 24 hours previously." | `blocker_response_time` | "Results after 6 weeks" section |

Every one of those three facts appears verbatim (or close to it) in the source brief. Nothing
in `input_files/blog_post_example.yaml`'s `content.sections` states a number that isn't backed
by one of these three `evidence_bank` entries — that's the zero-hallucination constraint
applied to a document type that, on its surface, looks like free-form prose. A blog post can
still be genuinely engaging writing (see the `blog_casual` style profile above) while every
factual claim in it remains audit-traceable.

Open `tutorials/ddo-v006-authoring-custom-structures/input_files/blog_post_example.yaml` now —
it's a byte-identical copy of `tests/data/blog_post_example.yaml` — and read it side-by-side
with `blog_post_source.md` to see the full mapping, not just the three claims above.

### Putting it together

```yaml
meta:
  doc_type: "blog_post"
  title: "We Killed Our Daily Standup. Here's What Happened."
  version: "0.1.0"
  date: "2026.05.20"
  author: "Priya Nakamura, Eng Manager"
  status: "draft"
  persona: "content_editor"
  style_profile: "blog_casual"
  output_formats: ["pdf", "html", "md"]
  template: "blog_post"
```

Note one contract difference from `prd`: `blog_post`'s `meta` uses a singular `author` string
field, not the `authors` list used by `prd`, `meeting_notes`, `meeting_agenda`, and
`project_report`. This is a deliberate per-type choice — a blog post has one byline, a status
report or meeting record can have several — and it's exactly the kind of decision you make at
schema-design time (question 1, above), not a rule the framework imposes on every type.

Render it and see for yourself:

```bash
uv run --locked ddo/build.py \
  --data     tutorials/ddo-v006-authoring-custom-structures/input_files/blog_post_example.yaml \
  --template blog_post \
  --format   html \
  --output   tutorials/ddo-v006-authoring-custom-structures/output_files/blog_post.html
```

See `output_files/blog_post.html` and `output_files/blog_post.md` in this directory for the
committed result of exactly that command (see the "Render It Yourself" section below for the
full script).

---

## Worked Examples: Three More Structures

The same five-question process (sections → persona → style → templates → evidence) produced
three more document types in v0.0.6. Rather than re-walk each one at the same depth, read them
as **worked examples** — the pattern should already feel familiar from `blog_post` above.

### `meeting_notes` — a durable, boring-by-design record

- **Schema** (`ddo/schemas/meeting_notes.yaml`): `attendees`, `agenda_covered`, `decisions`,
  `action_items`, `next_steps`. Every section answers "what happened," never "what should have
  happened."
- **Persona** (`ddo/personas/meeting_recorder.md`, `content_editor` sibling): verifies fidelity
  of the record — no editorializing, every action item has an owner.
- **Style** (`ddo/styles/notes_concise.md`): terse, factual, no narrative flourish.
- **Source → example**: [`input_files/meeting_notes_source.md`](input_files/meeting_notes_source.md)
  is the raw recorder's notes from the "Widget Sync Weekly Sync"; every decision and action
  item in [`input_files/meeting_notes_example.yaml`](input_files/meeting_notes_example.yaml)
  traces to it via the single `meeting_notes_source_20260615` evidence entry (one meeting, one
  source document — a much simpler evidence graph than `blog_post`'s three-entry bank).
- **Rendered output**: `output_files/meeting_notes.html`, `output_files/meeting_notes.md`.

### `meeting_agenda` — the one schema with a nested list

- **Schema** (`ddo/schemas/meeting_agenda.yaml`): `meeting_objective`, `agenda_items`,
  `pre_reads`, `logistics`. `agenda_items` is the interesting design choice here — it's the
  only one of the four new schemas whose section carries a nested list, `entries`, in addition
  to the usual `body`:
  ```yaml
  entries:
    - time_box: "0:00-0:10"
      topic: "..."
      owner: "..."
  ```
  Two details matter if you're designing a schema with a similar nested structure of your own:
  the field is named `entries`, **not** `items` — so that Jinja2 attribute access on the
  section object never accidentally resolves to Python's `dict.items()` method instead of your
  data — and `time_box` is treated as an **opaque string literal** everywhere it's used. No
  template parses, sums, or reformats it into a computed duration; `"0:00-0:10"` is rendered
  exactly as authored. That's a direct application of zero-hallucination to structured (not
  just prose) fields: DDO doesn't compute a total meeting length from time-box strings, because
  that would be inventing a figure no source stated.
- **Persona** (`ddo/personas/meeting_facilitator.md`): stress-tests for wasted attendee time
  and unaccountable ownership — every agenda item needs a single named owner, not a team.
- **Style** (`ddo/styles/agenda_directive.md`).
- **Source → example**: [`input_files/meeting_agenda_source.md`](input_files/meeting_agenda_source.md)
  is a five-email planning thread; [`input_files/meeting_agenda_example.yaml`](input_files/meeting_agenda_example.yaml)
  compresses it into a three-item, thirty-minute agenda with two evidence entries.
- **Rendered output**: `output_files/meeting_agenda.html`, `output_files/meeting_agenda.md`.

### `project_report` — literal metrics, no rollups

- **Schema** (`ddo/schemas/project_report.yaml`): `executive_summary`, `status`, `milestones`,
  `risks`, `metrics`, `next_steps` — six sections, the largest of the four new types.
- **Persona** (`ddo/personas/project_stakeholder.md`): stress-tests for optimistic spin, buried
  risk, and any metric that "outruns the evidence behind it."
- **Style** (`ddo/styles/executive_formal.md`).
- **Source → example**: [`input_files/project_report_source.md`](input_files/project_report_source.md)
  is a raw status-notes export (milestone board, metrics dashboard, risk log, verbatim sync
  quotes) for the fictional "Atlas Platform Migration" program.
  [`input_files/project_report_example.yaml`](input_files/project_report_example.yaml) draws
  four evidence entries from it. Look closely at the `metrics` section's schema placeholder —
  *"Literal, source-traced figures only. No computed rollups."* — and then check the rendered
  example: every number in `content.sections[metrics].body` (0 divergences across 18 days, 6h40m
  for 2.3 TB, 1 incident, 3 of 3 drills passed) appears as a literal figure in the source
  export, not a value derived by adding, averaging, or projecting from other figures. This is
  the same zero-hallucination discipline as `blog_post`'s evidence table above, applied to a
  document type whose whole job is reporting numbers.
- **Rendered output**: `output_files/project_report.html`, `output_files/project_report.md`.

---

## Render It Yourself

`code_samples/render_commands.sh` renders all four types (HTML + Markdown) using the
`input_files/*_example.yaml` copies in this directory. Run it from the repo root:

```bash
bash tutorials/ddo-v006-authoring-custom-structures/code_samples/render_commands.sh
```

It exits 0 and writes eight files into `output_files/` (`blog_post.{html,md}`,
`meeting_notes.{html,md}`, `meeting_agenda.{html,md}`, `project_report.{html,md}`) — these are
committed in this directory so you can diff a fresh render against them at any time:

```bash
diff <(uv run --locked ddo/build.py \
  --data   tutorials/ddo-v006-authoring-custom-structures/input_files/blog_post_example.yaml \
  --template blog_post --format md --output /dev/stdout) \
  tutorials/ddo-v006-authoring-custom-structures/output_files/blog_post.md
```

A clean exit (no output) confirms the render is still deterministic.

PDF rendering works identically (`--format pdf`) but is not included in `output_files/` here —
PDF output embeds a render timestamp by default (see Tutorial 1's `--timestamp` flag for
byte-identical PDFs), so it is **illustrative only** and is not guarded for byte-equality the
way the HTML/Markdown renders in this tutorial are.

---

## Starting Your Own Document Type

If you want to design a fifth document type, repeat the five questions above in order:

1. **Sections** — what does the reader need to walk away knowing, in what order? Write the
   skeleton to `ddo/schemas/<your_type>.yaml`, following the shape of the four schemas in this
   tutorial (`meta` block + `content.sections[]` with `[REQUIRES USER INPUT: ...]` sentinels +
   an `evidence_bank` comment showing the expected node shape).
2. **Persona** — what does an adversarial reader of this document type actually care about?
   Author it by hand following `ddo/personas/content_editor.md`'s structure (Domain, Reviewing
   Mission, Attack Vectors table, Severity Taxonomy, Interview Question Templates), pairing
   each attack vector to one of your schema's sections.
3. **Style (optional)** — if the document type needs phrasing guidance beyond your persona's
   domain description, use the **`ddo-create-style`** skill
   (`ddo/skills/ddo-create-style.md`) rather than hand-authoring a style file — it enforces the
   phrasing-only constraint interactively so you can't accidentally smuggle a factual claim
   into a style profile.
4. **Templates** — add `ddo/templates/typst/<your_type>.typst`,
   `ddo/templates/jinja2/<your_type>.html.jinja2`, and
   `ddo/templates/jinja2/<your_type>.md.jinja2`. If your schema needs a nested structure like
   `meeting_agenda`'s `entries`, name it something other than a Python dict method
   (`items`, `keys`, `values` are all traps) and treat any string-shaped field (like
   `time_box`) as opaque unless you have an explicit reason to parse it.
5. **Example + evidence** — write an `example.yaml` under `tests/data/` sourced from a real (or
   realistic) raw document, the same way `blog_post_example.yaml` traces to
   `blog_post_source.md` in this tutorial. Every claim needs an `evidence_bank` id; every id
   needs to resolve; zero sentinels should survive to the final file.
6. **Register the type** — add your new type name to `ddo/build.py`'s `--template` CLI
   `choices` tuple so `build.py` will route to it.

For persona authoring specifically — how to design and iterate on the Attack Vectors and
Interview Question Templates that make an adversarial review lens effective — see
**[Tutorial 3: Writing Structured Personas](../ddo-v006-writing-structured-personas/tutorial.md)**.
This tutorial only showed you *where* a persona plugs into a new document type, not how to
author one from scratch.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ddo-build: error: argument --template: invalid choice: '<type>'` | The type name isn't registered in `build.py`'s `--template` choices | Add the type name to the `choices` tuple in `ddo/build.py`, or check for a typo |
| `ddo-build: error: meta: required key 'author' missing` (blog_post) | `blog_post` uses singular `author`, not the `authors` list other types use | Check `ddo/schemas/blog_post.yaml` for the exact key name for your document type |
| `section 'agenda_items': ...` errors on a `meeting_agenda` | A nested `entries` list is malformed, or `time_box`/`topic`/`owner` is missing on an entry | Every `entries` item needs all three keys; `time_box` is a free-form string, no format is enforced |
| `content.sections[N].body: unfilled sentinel present` | A `[REQUIRES USER INPUT: ...]` placeholder from the schema skeleton was left in the example | Fill it in from your source document, or remove the section if it doesn't apply |
| Style profile changes render but a fact appears to have changed | Style profiles are phrasing-only; if content changed, the edit went to the wrong file | Content edits belong in `content.sections`/`evidence_bank`; style edits belong in `ddo/styles/<name>.md` and must never carry a claim |

---

## Related

- **Tutorial 1** — [`ddo-v001-prd-workflow`](../ddo-v001-prd-workflow/tutorial.md): the base
  render pipeline (schema contract, evidence bank, validation gate, PDF/HTML/Markdown render)
  using the `prd` type. Read this first if you haven't.
- **Tutorial 3** — [`ddo-v006-writing-structured-personas`](../ddo-v006-writing-structured-personas/tutorial.md):
  how to design and iterate on a persona's Attack Vectors from scratch — the deep-dive this
  tutorial's persona sections deliberately did not repeat.
- **Evidence bank lens** — [`ddo-v006-evidence-bank-workflow`](../ddo-v006-evidence-bank-workflow/tutorial.md):
  a read-only deep-dive on how `evidence_bank` citation integrity is enforced by
  `ddo/validation.py`, using the `prd` type's `ingest_output.yaml` fixture.
- **Adversarial loop** — [`ddo-adversarial-loop-v0.0.2`](../ddo-adversarial-loop-v0.0.2/tutorial.md):
  Red Team → Interview → Refine, the loop that actually exercises the personas and attack
  vectors this tutorial introduced.
- **`ddo-create-style` skill** (`ddo/skills/ddo-create-style.md`) — author a new style profile
  through a guided, phrasing-only-enforcing Q&A loop.
- **Schemas**: `ddo/schemas/blog_post.yaml`, `ddo/schemas/meeting_notes.yaml`,
  `ddo/schemas/meeting_agenda.yaml`, `ddo/schemas/project_report.yaml`.
- **Personas**: `ddo/personas/content_editor.md`, `ddo/personas/meeting_recorder.md`,
  `ddo/personas/meeting_facilitator.md`, `ddo/personas/project_stakeholder.md`.
- **Styles**: `ddo/styles/blog_casual.md`, `ddo/styles/notes_concise.md`,
  `ddo/styles/agenda_directive.md`, `ddo/styles/executive_formal.md`.
