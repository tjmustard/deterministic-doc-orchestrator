# DDO v0.0.1: From Topic to Document — PRD YAML Workflow

## Overview

This tutorial walks you through the full DDO v0.0.1 document-generation
pipeline using a Product Requirements Document (PRD) as the example artifact.
You will start from a structured YAML source file, validate it against the DDO
contract, and render it to PDF, HTML, and Markdown — all from a single command.

DDO's central guarantee: **identical YAML + identical template = identical
output**. The document you produce is not the output of an AI generation step;
it is a deterministic function of your source file. Every word in the rendered
PDF traces back to a version-controlled YAML node.

By the end of this tutorial you will:

- Understand the PRD schema contract (the `meta` block and `evidence_bank`).
- Author a valid `document_data.yaml` from scratch.
- Run the validation gate and interpret its error messages.
- Render your document to all three output formats.
- Know what output to expect and how to reproduce it exactly.

---

## Prerequisites

Before starting, ensure the following are in place:

- **`uv` installed** — DDO's build orchestrator (`build.py`) is a PEP 723
  script invoked via `uv run --locked`. Install uv from
  [docs.astral.sh/uv](https://docs.astral.sh/uv).
- **Repository cloned** — this tutorial runs from the root of the
  `deterministic-doc-orchestrator` repository.
- **Suite passing** — verify your environment is clean:
  ```bash
  uv run pytest -q
  # Expected: 188 passed
  ```
- **Basic YAML familiarity** — you should be able to read and edit `.yaml`
  files with a text editor. No prior Python knowledge is required to follow
  this tutorial.

No additional installation is needed. All Python dependencies (Typst for PDF,
Jinja2 for HTML/Markdown) are declared inside `ddo/build.py` itself and
resolved by `uv run --locked` on first use.

---

## Understanding the PRD Schema

A DDO document starts as a `document_data.yaml` file that satisfies the
**DDO minimal contract**: a required `meta` block and a required `evidence_bank`
array. Everything else (the actual content) is dynamic.

### The `meta` block

```yaml
meta:
  doc_type: "prd"          # fixed — selects schema validation rules
  title: "My Document"     # required, non-empty
  version: "0.1.0"         # required, non-empty
  date: "2026.06.27"       # required — must match YYYY.MM.DD exactly
  authors:
    - "Dana Lee, Product"
  status: "draft"
  persona: "product_critic"
  output_formats: ["pdf", "html", "md"]
  template: "prd"          # tells build.py which template family to use
```

Three fields enforce hard contract rules: `title` and `version` must be
non-empty strings; `date` must match the dotted format `YYYY.MM.DD` (the
validation gate rejects any other format, including ISO-8601 `2026-06-27`).

### Content sections

Each section has an `id`, `title`, `body`, optional `claims`, and an `evidence`
list whose entries **must reference IDs present in `evidence_bank`**:

```yaml
content:
  sections:
    - id: "problem_statement"
      title: "1. Problem Statement"
      body: >-
        The manual re-keying step introduces transcription errors.
      claims:
        - "Manual re-keying is the primary source of telemetry errors."
      evidence: ["support_ticket_audit"]
```

### The `evidence_bank`

Every claim traces back to a named evidence entry:

```yaml
evidence_bank:
  - id: "support_ticket_audit"
    type: "data"
    content: "412 of 530 sampled billing disputes traced to a telemetry mismatch."
    source: "Internal support ticket audit, 2026.01–2026.03."
```

The validation gate enforces two invariants:
- Every `id` in a section's `evidence` list must exist in `evidence_bank`.
- No two entries in `evidence_bank` may share the same `id`.

### Walkthrough: `input_files/prd_example.yaml`

Open `tutorials/ddo-v001-prd-workflow/input_files/prd_example.yaml`. It
demonstrates a complete, gate-passing PRD with 6 sections and 3 evidence
entries. You'll use this as your starting point in Step 1.

---

## Step 1: Author Your `document_data.yaml`

Copy the example file as your starting point:

```bash
cp tutorials/ddo-v001-prd-workflow/input_files/prd_example.yaml \
   my_document_data.yaml
```

Open `my_document_data.yaml` in your editor. You'll replace the placeholder
content with your own document's details.

### The zero-hallucination rule

DDO enforces a strict constraint: **every field must come from a verifiable
source**. If you cannot fill a field from your source material, write the
sentinel token rather than guessing:

```yaml
date: "[[DDO::REQUIRES_INPUT: supply the exact dotted date YYYY.MM.DD]]"
```

The validation gate will refuse to render any document that still contains
this token. This prevents half-finished content from ever becoming a
deliverable by accident.

### What to fill in

1. **`meta` block** — update `title`, `version`, `date` (dotted `YYYY.MM.DD`),
   and `authors` for your document. Leave `template: "prd"` and
   `output_formats: ["pdf", "html", "md"]` as-is.

2. **`content.sections`** — replace each section's `body` with your content.
   The PRD schema includes: `problem_statement`, `target_audience`,
   `user_stories`, `requirements`, `success_metrics`, `out_of_scope`.
   You can add or remove sections — the schema is dynamic.

3. **`evidence_bank`** — for each claim in your sections, add an entry:
   ```yaml
   evidence_bank:
     - id: "my_source_001"
       type: "data"        # data | interview | decision | document
       content: "Verbatim or paraphrased key fact from the source."
       source: "Source name, date, location."
   ```
   Then reference `"my_source_001"` in the `evidence` list of the section
   that uses it.

### A note on the `claims` field

`claims` is a list of short declarative sentences that summarize the
strongest factual assertions in a section's `body`. They are referenced by
`evidence` IDs but are not enforced by the gate — think of them as
self-documentation that makes the evidence→claim linkage explicit for human
reviewers.

---

## Step 2: Validate with the Gate

The validation gate runs automatically when you invoke `build.py`. There is
no separate lint step. To validate (and render HTML as a quick smoke-check):

```bash
uv run --locked ddo/build.py \
  --data     my_document_data.yaml \
  --template prd \
  --format   html \
  --output   /tmp/smoke.html
```

If the document is valid, `build.py` renders immediately and exits 0.
If it is invalid, it exits non-zero with a single precise error message and
**does not write any output file**.

### Reading the error messages

| Error message | Cause | Fix |
|---|---|---|
| `meta: required key 'date' missing` | The `date` field is absent from `meta` | Add `date: "YYYY.MM.DD"` |
| `meta.date: expected YYYY.MM.DD, got '2026-06-27'` | Wrong date format (dashes not dots) | Change to `"2026.06.27"` |
| `meta.title: must be non-empty` | Empty string or missing title | Supply a non-empty title |
| `evidence_bank: duplicate id 'my_source_001'` | Two entries share the same id | Rename one entry and update its references |
| `section 'requirements': evidence ref 'ev-001' not in evidence_bank` | Dangling reference | Add the missing evidence entry or remove the reference |
| `content.sections[N].body: unfilled sentinel present` | A `[[DDO::REQUIRES_INPUT:` token remains in a body | Fill the gap or remove the field |

### The gate is your ally

The gate fails on the **first** error only. Fix, re-run, and it will either
pass or surface the next issue. Work through errors one at a time.

---

## Step 3: Render to PDF, HTML, and Markdown

Invoke `build.py` once per output format. Use absolute paths for `--output`
(or paths relative to the repo root) to avoid ambiguity:

```bash
# HTML
uv run --locked ddo/build.py \
  --data     my_document_data.yaml \
  --template prd \
  --format   html \
  --output   Documents/my-doc/output/my-doc.html

# Markdown
uv run --locked ddo/build.py \
  --data     my_document_data.yaml \
  --template prd \
  --format   md \
  --output   Documents/my-doc/output/my-doc.md

# PDF
uv run --locked ddo/build.py \
  --data     my_document_data.yaml \
  --template prd \
  --format   pdf \
  --output   Documents/my-doc/output/my-doc.pdf
```

`build.py` creates the parent directory automatically — you do not need to
`mkdir` first.

See `tutorials/ddo-v001-prd-workflow/code_samples/render_commands.sh` for a
ready-to-adapt shell script covering all three formats plus the `--timestamp`
variant.

### Output path convention

The `ddo-render` skill derives output paths from `meta` automatically, placing
files at:

```
Documents/<meta.date>_<meta.doc_type>_<slug>/output/<slug>.<ext>
```

where `<slug>` is your `meta.title` lowercased and sanitized
(`[a-z0-9]` only, other characters collapsed to `-`, capped at 80 characters).

For a document with `title: "Acme Widget Sync Service"` and
`date: "2026.06.27"`, the PDF would land at:

```
Documents/2026.06.27_prd_acme-widget-sync-service/output/acme-widget-sync-service.pdf
```

### Byte-identical PDF (optional)

By default, PDF metadata includes the render timestamp and will differ between
runs. To get byte-for-byte identical PDFs (useful for checksums or diff-free
CI):

```bash
uv run --locked ddo/build.py \
  --data      my_document_data.yaml \
  --template  prd \
  --format    pdf \
  --output    Documents/my-doc/output/my-doc.pdf \
  --timestamp 1000000000
```

Two renders with the same `--timestamp` value produce byte-identical output.

### Verify determinism

After rendering HTML and Markdown, you can verify they are byte-identical
across runs with the integration test:

```bash
uv run pytest tests/integration/test_render_determinism.py -q
```

---

## Expected Output

After completing all three steps, you should have:

### File layout

```
Documents/
└── 2026.06.27_prd_acme-widget-sync-service/
    └── output/
        ├── acme-widget-sync-service.html   (~15 KB for a 6-section PRD)
        ├── acme-widget-sync-service.md     (~12 KB)
        └── acme-widget-sync-service.pdf    (~75 KB)
```

### HTML render

The HTML file is a self-contained page with:
- A document header (`title`, `version`, `date`, `authors`).
- One `<section>` per content section, with headings matching the `title`
  fields in your YAML.
- No inline scripts or external resources — safe to open in any browser
  or embed in a static site.

See `tutorials/ddo-v001-prd-workflow/output_files/prd_example.html` for a
complete rendered example.

### Markdown render

The Markdown file mirrors the HTML structure and is compatible with GitHub
Flavored Markdown, Obsidian, and most static site generators.

See `tutorials/ddo-v001-prd-workflow/output_files/prd_example.md`.

### PDF render

The PDF is rendered in-process by the `typst` library using the bundled
DejaVu font family. No system Typst installation or internet access is
required. The font and dependency versions are pinned in
`ddo/build.py.lock`, so the same YAML produces the same PDF on any
machine with the same `uv` version.

### Determinism guarantee

Run the same command twice (or add `--timestamp N` for the PDF) — the
HTML and Markdown outputs are byte-identical. The PDF text layer is
identical; byte-identity requires `--timestamp`.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ddo-build: error: meta: required key 'date' missing` | `date` field absent from `meta` | Add `date: "YYYY.MM.DD"` to the `meta` block |
| `ddo-build: error: meta.date: expected YYYY.MM.DD, got '...'` | Date uses wrong format (dashes, slashes, ISO-8601) | Change to dotted format: `"2026.06.27"` |
| `ddo-build: error: meta.title: must be non-empty` | `title` is empty or missing | Supply a non-empty string |
| `ddo-build: error: evidence_bank: duplicate id '...'` | Two evidence entries share the same `id` | Rename one entry and update its references in `evidence` lists |
| `ddo-build: error: section '...': evidence ref '...' not in evidence_bank` | A section references an evidence `id` that doesn't exist | Add the missing entry to `evidence_bank`, or remove the stale reference |
| `ddo-build: error: content.sections[N].body: unfilled sentinel present` | A `[[DDO::REQUIRES_INPUT:` token remains in a section body | Fill the gap with real content, or remove the field |
| `uv run` fails with `no lockfile found` | `ddo/build.py.lock` is missing | Run `uv lock --script ddo/build.py` to regenerate it |
| PDF renders but is not byte-identical between runs | Missing `--timestamp` flag | Add `--timestamp <unix_seconds>` to both render invocations |
| `PathContainmentError: path escapes Documents/` | `meta.title` contains `../` or other escape sequences | Fix the title; verify the `meta.title` value is a normal document name |
| `ValidationError: content is empty — no renderable sections` | No sections defined, or all sections have empty bodies | Add at least one section with a non-empty `body` |

---

## Related

- **`ddo/skills/ddo-ingest.md`** — the `ddo-ingest` skill automates Step 1:
  given local raw source documents, it maps them into a schema-shaped
  `document_data.yaml` under a zero-hallucination constraint, flags every
  gap it cannot fill, writes atomically, and halts at a human-review gate.
  Use it when you have unstructured source material (meeting notes, research
  papers, design docs) that you want to transform into a structured PRD or
  scientific report.

- **`tests/fixtures/ingest_output.yaml`** — a real-world example of a
  complete, human-approved `document_data.yaml`: the DDO project's own PRD,
  authored and gate-verified during the v0.0.1 development process. It
  demonstrates all 7 standard sections, 12 evidence entries, and the full
  meta contract. Use it as a reference for a fully-realized document.

- **Scientific report tutorial (coming soon)** — the same ingest → validate
  → render workflow applies to `scientific_report` documents. To preview it
  now, swap `--template prd` for `--template scientific_report` and use
  `tests/data/scientific_report_example.yaml` as your starting point. A
  dedicated tutorial (`tutorials/ddo-v001-scientific-report-workflow/`) is
  planned.

- **DDO adversarial review loop** — the skills `ddo-red-team`,
  `ddo-interview`, and `ddo-refine` shipped in v0.0.2 and are fully
  available. They read the Markdown/HTML render, critique it through a
  configurable persona lens, and propose targeted patches to
  `document_data.yaml`. See
  [`tutorials/ddo-adversarial-loop-v0.0.2/tutorial.md`](../ddo-adversarial-loop-v0.0.2/tutorial.md).
