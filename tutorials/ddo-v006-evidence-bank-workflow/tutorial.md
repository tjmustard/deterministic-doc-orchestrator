# A Citation-Integrity Lens: Reading the `evidence_bank` (v0.0.6)

## Overview

DDO's zero-hallucination guarantee is not a promise about the model's good
behavior — it is a structural property of the schema plus a deterministic
gate that refuses to render anything that violates it. This tutorial is a
**lens**, not a walkthrough: it does not run a pipeline phase, mutate a
`document_data.yaml`, or render anything. It opens one already-ingested
document and teaches you to *read* the citation graph the way
`ddo/validation.py` reads it — so that when you author or review a DDO
document elsewhere, you can recognize a sound `evidence_bank` from a broken
one on sight.

If you want to see documents *change* — the Red Team → Interview → Refine
loop that patches a flawed document and re-renders it — that is a different
tutorial: **[`tutorials/ddo-adversarial-loop-v0.0.2/`](../ddo-adversarial-loop-v0.0.2/tutorial.md)**.
This tutorial does not repeat that material and does not invoke any part of
that loop.

## Provenance Boundary — read this before touching the copy

`input_files/ingest_output.yaml` in this tutorial directory is a **byte-identical
copy** of the canonical, human-promoted fixture at
[`tests/fixtures/ingest_output.yaml`](../../tests/fixtures/ingest_output.yaml).

- **The fixture at `tests/fixtures/ingest_output.yaml` is canonical.** It was
  produced by `ddo-ingest` and promoted to the test suite only after explicit
  human sign-off (the `DDO_FIXTURE_SIGNOFF` gate) — see the header comment in
  that file: *"promoted to `tests/fixtures/ingest_output.yaml` on final human
  sign-off."*
- **This tutorial's copy is a teaching mirror, not a second source of truth.**
  It exists so this tutorial is self-contained and doesn't require you to
  `cd` out of `tutorials/` to follow along. It is guarded for **sameness**
  with the canonical fixture (a byte-for-byte diff), **not** for provenance —
  copying a file does not re-run the sign-off gate, and the copy carries no
  independent authority.
- **Do not edit this copy to "fix" or extend the ground truth.** If you find
  something to change about the underlying document, the change belongs in
  `tests/fixtures/ingest_output.yaml` (via the ingest pipeline and its
  sign-off gate), not in this mirror. Editing the mirror only breaks the
  sameness guard; it does not change what the canonical fixture says.

You can verify the sameness guarantee yourself at any time:

```bash
diff tests/fixtures/ingest_output.yaml \
     tutorials/ddo-v006-evidence-bank-workflow/input_files/ingest_output.yaml
```

A clean exit (no output) means the mirror still matches the canonical
fixture.

## What you're looking at

`ingest_output.yaml` is a `prd`-schema `document_data.yaml` — the output of
`ddo-ingest` on the DDO project's own founding PRD material, before any Red
Team pass touched it. It satisfies the DDO **minimal contract**
(`ddo/schemas/prd.yaml` and `ddo/schemas/scientific_report.yaml` are the
canonical schema shapes): a `meta` block, and a `content.sections[]` /
`evidence_bank[]` pair.

```
meta:
  doc_type: "prd"
  title: "..."
  ...

content:
  sections:
    - id: "problem_statement"
      title: "1. Problem Statement"
      body: >-
        ...prose...
      claims: []
      evidence: ["ev-superprd-problem", "ev-ddo-core-tenets"]   # <- bank-id references
    ...

evidence_bank:
  - id: "ev-superprd-problem"          # <- referenced above
    type: "document"
    content: "..."
    source: "spec/compiled/SuperPRD.md, Section 1 (Problem Statement)"
  ...
```

## The citation graph: `evidence` → `evidence_bank`

Every section under `content.sections` carries an `evidence` array. Each
entry in that array is **not** the citation itself — it's an `id` string that
must resolve to exactly one entry in the top-level `evidence_bank` array.
The bank entry is where the actual claim lives: `type`, `content` (the
verbatim substantiating text), and `source` (where it came from).

This indirection is the whole point. A section's prose can reference the
same evidence multiple times, and every reference is checked, not trusted:

- `problem_statement` references `ev-superprd-problem` and `ev-ddo-core-tenets`.
- `requirements` references five separate bank entries
  (`ev-superprd-architecture`, `ev-superprd-validation-gate`,
  `ev-superprd-hermeticity`, `ev-ddo-schema-arch`, `ev-ddo-pipeline`) — one
  section can lean on several sources at once.

Open `input_files/ingest_output.yaml` and trace a few of these yourself: pick
an `id` out of any section's `evidence` list, then find the `evidence_bank`
entry with that same `id` and read its `source`. If you can't find a match,
that's exactly the failure mode the next section covers.

`code_samples/inspect_evidence_bank.py` automates this trace — it loads the
fixture, prints every section's evidence references next to their resolved
bank entries, and only reads; it never patches `document_data.yaml`.

## The zero-hallucination sentinel

DDO's rule is: if a field can't be verifiably filled from a source, the
system marks the gap explicitly instead of guessing. The gate that
`build.py` (and `ddo.validation.validate`) actually runs at render time scans
every parsed string value for a namespaced, machine-recognizable marker:

```
[[DDO::REQUIRES_INPUT: <short reason>]]
```

(This is what `ddo/validation.py`'s `_SENTINEL_TOKEN` matches on — see
`_scan_sentinel()`. `ddo-ingest` is the skill that writes this marker into a
freshly-ingested `document_data.yaml` wherever a source can't substantiate a
field.) You'll also see a related but distinct convention,
`[REQUIRES USER INPUT: <reason>]`, used as a placeholder in the *schema
templates* themselves (`ddo/schemas/prd.yaml`, `ddo/schemas/scientific_report.yaml`)
and in the persona/style-authoring skills before a document even reaches the
ingest stage — both forms exist so that "this field is unfilled" is always a
literal, grep-able string rather than an AI's silent invention. Neither
sentinel survives to a shipped document: `ingest_output.yaml` in this
tutorial contains zero occurrences of either, because the ingest pass that
produced it filled every field from a real source.

The check itself is simple and absolute — the sentinel scan doesn't try to
guess intent:

> `validate()` raises `ValidationError` on the **first** parsed string value
> anywhere in the document (any depth, any key) containing
> `[[DDO::REQUIRES_INPUT:`. There is no partial credit and no render-with-gaps
> mode. A single remaining marker fails the whole document closed.

## How `validate()` rejects a broken citation graph

`ddo/validation.py` is the single importable validation gate — the same
function `build.py` calls before any render. Three checks run in order, and
the first failure wins:

1. **Contract check** (`_check_contract`) — `meta` has all required keys,
   `title`/`version` are non-empty strings, `date` is dotted `YYYY.MM.DD`, and
   `evidence_bank` exists and is a list.
2. **Evidence integrity** (`_check_evidence_integrity`) — this is the one
   that actually walks the citation graph:
   - **Duplicate bank ids** are rejected outright
     (`evidence_bank: duplicate id 'X'`).
   - **Dangling references** — any `content.sections[*].evidence` entry whose
     id has no matching `evidence_bank` entry — are rejected outright
     (`content.sections[*].evidence: dangling evidence id 'X'`). This is the
     direct enforcement of the indirection described above: a section can
     *claim* to cite something, but if the bank entry doesn't exist, the
     document fails closed.
   - **Contentless documents** — zero sections, or zero total evidence
     references across all sections — are rejected
     (`content.sections: contentless document (0 sections or 0 evidence
     references)`). A document that cites nothing is treated the same as one
     that cites something that doesn't exist: neither is trustworthy.
   - **Orphan bank entries** (an `evidence_bank` entry nothing references)
     only **warn** — they don't fail the document. An uncited source isn't a
     hallucination risk the way a dangling reference is.
3. **Sentinel scan** (`_scan_sentinel`) — the zero-hallucination check
   described above.

`code_samples/inspect_evidence_bank.py` demonstrates check 2 concretely: it
calls `validate()` on the unmodified fixture (passes), then deep-copies the
document, appends a nonexistent id (`"ev-does-not-exist"`) to one section's
`evidence` list, and calls `validate()` again to show the exact
`ValidationError` it raises. Nothing on disk is touched — the corrupted copy
lives only in memory for the duration of the demonstration.

Run it yourself from the repo root:

```bash
PYTHONPATH=. uv run python tutorials/ddo-v006-evidence-bank-workflow/code_samples/inspect_evidence_bank.py
```

Expected tail of the output:

```
Clean document passed validate() — every claim traces to a source.

Rejected dangling reference as expected: content.sections[*].evidence: dangling evidence id 'ev-does-not-exist'
```

## What this tutorial does *not* do

- It does **not** render anything. There is no `output_files/` render for
  this tutorial, and no `ddo-render` invocation anywhere in it — the render
  metric belongs to the render-focused tutorial in this same v0.0.6 batch.
  If you're looking for a rendered artifact, you won't find one here by
  design.
- It does **not** walk the Red Team → Interview → Refine loop. That loop —
  including how a dangling reference gets *introduced or repaired* through a
  patch (`ddo.refine`'s `delete`/`DanglingRefError` machinery) — is covered
  end-to-end in
  [`tutorials/ddo-adversarial-loop-v0.0.2/tutorial.md`](../ddo-adversarial-loop-v0.0.2/tutorial.md).
  This tutorial only teaches you to *read* the citation graph and the gate
  that enforces it; it does not mutate `document_data.yaml`.

## Related

- **Fixture (canonical):** `tests/fixtures/ingest_output.yaml`
- **Fixture (this tutorial's mirror):** `input_files/ingest_output.yaml`
- **Module:** `ddo/validation.py` (`validate`, `_check_contract`,
  `_check_evidence_integrity`, `_scan_sentinel`)
- **Schemas:** `ddo/schemas/prd.yaml`, `ddo/schemas/scientific_report.yaml`
- **Skill:** `ddo/skills/ddo-ingest.md` (writes the
  `[[DDO::REQUIRES_INPUT: ...]]` gap marker; the skill this fixture's ingest
  pass ran under)
- **Code sample:** `code_samples/inspect_evidence_bank.py`
- **Loop walkthrough (separate tutorial):**
  `tutorials/ddo-adversarial-loop-v0.0.2/tutorial.md`
