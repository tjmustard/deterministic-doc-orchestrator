# SuperPRD: DDO v0.0.1 — Deterministic Rendering Backbone

> **Status:** DRAFT (output of `/hyper-architect`). Next step: start a fresh conversation and run `/hyper-redteam` for adversarial analysis, then `/hyper-resolve` to compile the final SuperPRD + MiniPRDs.
>
> **Date:** 2026-06-27
> **Author:** Thomas J. L. Mustard (interviewed) + Architect Agent
> **Source material:** all of `PRDs/` (founding brief `DETERMINISTIC_DOC_ORCHESTRATOR.md`, condensed `DDO_PRD.md` v0.0.2, schema YAMLs, template stubs, persona/skill stubs).

---

## 1. Introduction & Goals

### Problem Statement
AI-assisted document generation is unreliable: the model operates as a black box that hallucinates facts, invents citations, and produces output that cannot be verified against a ground truth. The Deterministic Document Orchestrator (DDO) eliminates this by separating **data** (YAML, version-controlled, human-verified) from **presentation** (templates, deterministically applied). The AI performs cognitive work (extraction, and later critique/refinement) but never writes directly to the final document.

DDO's full vision is a 5-phase pipeline (**Ingest → Render → Red Team → Interview → Refine**). **This PRD scopes only the first milestone, v0.0.1: the deterministic rendering backbone.** Without a trustworthy, reproducible YAML→document core, the adversarial loop downstream has nothing solid to stand on. v0.0.1 delivers the headline value — *"every generated word traces back to a version-controlled YAML source"* — for two document types in three output formats.

### Solution Overview
Build the deterministic core of DDO:
- A hermetic `build.py` orchestrator (PEP 723, run via `uv run`) that renders a validated `document_data.yaml` to PDF (Typst), HTML (Jinja2), and Markdown (Jinja2), and that owns all deterministic validation.
- The two existing schemas (`prd`, `scientific_report`) and six template stubs, migrated from `PRDs/` into `ddo/` and wired to `build.py`.
- Two HACF cognitive skills: `ddo-ingest` (sources → YAML, zero-hallucination) and `ddo-render` (thin wrapper that computes output paths and invokes `build.py`).
- A regression test suite that locks in determinism and the validation contract.

### Target Audience
The system's designer and other technical users who generate structured documents (PRDs, scientific reports to start) and require reproducibility and zero hallucination. DDO is a Claude Code / HACF-driven toolkit, not a SaaS product or web service. Single-user, local-filesystem operation.

---

## 2. Confidence Mandate

- **Confidence Score: 8 / 10.** Scope, boundaries, permissions, and the deterministic/novel split were resolved one-by-one with the user during the architect interview. The remaining uncertainty is implementation-level (exact Typst Python-package API surface for timestamp control; whether the migrated template stubs render cleanly against the live schemas without edits) and is best burned down during the build phase, not the spec phase.
- **Clarifying Questions (deferred to build / red-team):**
  1. Does the `typst` PyPI package's Python API expose creation-timestamp control, or must `--timestamp` fall back to the bundled CLI entrypoint? (Spike during build.)
  2. Do the six template stubs render against the canonical schemas without modification, or do field-name mismatches exist? (Verify on migration.)
  3. Should `tests/fixtures/` store the golden PDF (binary) in git, or only its hash + the text outputs? (Decide at fixture-bootstrap time.)

---

## 3. Scope

### In-Scope (v0.0.1)
- `ddo/build.py` — hermetic PEP 723 orchestrator with the full deterministic validation gate and three-format rendering.
- `ddo/schemas/prd.yaml`, `ddo/schemas/scientific_report.yaml` — migrated + renamed from `PRDs/` (short doc-type names).
- `ddo/templates/typst/{prd,scientific_report}.typst` — migrated PDF templates.
- `ddo/templates/jinja2/{prd,scientific_report}.{html,md}.jinja2` — migrated HTML/MD templates.
- `ddo-ingest` skill (sources → `document_data.yaml`, zero-hallucination, gap-flagging).
- `ddo-render` skill (thin wrapper: derive output path from `meta`, invoke `build.py`, report result).
- `tests/unit/` + `tests/integration/` — validation-gate tests, determinism regression tests, ingest contract/render-ability test.
- Migrate the two persona stubs (`product_critic`, `scientific_reviewer`) into `ddo/personas/` for forward-compat (they are *not* exercised by any v0.0.1 code path).

### Out-of-Scope (deferred to v0.0.2+)
- **The entire adversarial loop:** `ddo-red-team`, `ddo-interview`, `ddo-refine`, and the `ddo-run` composite.
- DOCX / Pandoc output. (Only PDF/HTML/MD in v0.0.1.)
- Network / URL ingestion. (Local files only.)
- Web-source provenance capture, multi-page HTML websites, template generation (`ddo-template-gen`), `ddo-create-persona`, schema migration tooling (`ddo-migrate`), quality scoring, `review_history/` snapshots, multi-author interview.
- Any additional document types beyond `prd` and `scientific_report`.

---

## 4. User Stories (Atomic)

| ID | User Story | Acceptance Criteria | Priority |
|---|---|---|---|
| US-001 | As an author, I want to render a valid `document_data.yaml` to PDF, HTML, and Markdown via one command, so that I get reproducible documents from a single source. | 1. `uv run ddo/build.py --data <yaml> --template <t> --format <pdf\|html\|md> --output <path>` produces the file at `<path>`.<br>2. HTML and MD outputs are byte-identical across repeated runs from identical input.<br>3. PDF output is content-identical across runs (wall-clock timestamp by default). | High |
| US-002 | As an author, I want `build.py` to refuse to render an invalid document, so that I never ship a doc with broken evidence links or unfilled gaps. | 1. Missing/incomplete `meta` or missing `evidence_bank` → nonzero exit + precise message.<br>2. Any `content.sections[*].evidence` ID absent from `evidence_bank` → nonzero exit naming the ID.<br>3. Any remaining `[REQUIRES USER INPUT` substring → nonzero exit. | High |
| US-003 | As an author, I want byte-identical PDF output on demand, so that I can verify reproducibility when needed. | 1. `--timestamp <value>` pins the Typst creation timestamp.<br>2. Two runs with the same `--timestamp` produce byte-identical PDFs.<br>3. Omitting `--timestamp` uses wall-clock (default). | Medium |
| US-004 | As an author, I want to ingest raw local sources into a schema-shaped `document_data.yaml` with gaps flagged, so that I start from structure without hallucinated content. | 1. `ddo-ingest` maps source content to the chosen schema, inventing nothing.<br>2. Every unfillable field becomes `[REQUIRES USER INPUT: <reason>]`.<br>3. Output is written to `Documents/<date>_<doc_type>_<slug>/document_data.yaml`; an existing YAML is never overwritten without explicit confirmation.<br>4. Ends with `[WAITING FOR USER REVIEW]`. | High |
| US-005 | As an author, I want `ddo-render` to compute the correct output path and invoke the build, so that I don't manage paths by hand. | 1. Skill derives `output/<slug>.<ext>` under the document folder from `meta`.<br>2. Skill invokes `build.py` and reports success/failure.<br>3. Skill writes no files itself and never hand-edits a rendered artifact. | High |
| US-006 | As a maintainer, I want a regression suite that locks determinism and validation, so that future changes can't silently break the core guarantees. | 1. Unit tests cover all three validation checks (pass + fail paths).<br>2. Determinism test renders both example docs to HTML/MD and asserts equality against frozen fixtures.<br>3. Ingest test asserts produced YAML passes validation and renders to all three formats (no content equality).<br>4. `uv run ruff check .` and `uv run ruff format --check .` exit 0. | High |

---

## 5. Technical Specifications

### Architecture & Resolved Trade-offs

**The Core Mutation (value loop).** Raw sources → version-controlled `document_data.yaml` (zero-hallucination, gaps flagged) → deterministic render (Typst PDF / Jinja2 HTML+MD) → [v0.0.2+: red team → interview → refine → re-render]. The single piece of mutable state is `document_data.yaml`; every rendered file is a derived, disposable artifact.

**Determinism contract (resolved).** "Same YAML + same template = identical output" means: HTML/MD **byte-identical by default**; PDF **content-identical by default** with a **wall-clock timestamp** (so not byte-identical run-to-run). Byte-identical PDF is **opt-in** via `--timestamp`, used for manual reproducibility verification. *No hash-equality regression gate runs on PDFs.* — Trade-off: chose practical default (wall-clock) over forcing byte-equality everywhere, because Typst embeds a creation timestamp and forcing pinning by default adds friction for no routine benefit.

**`build.py` resolution rule (resolved).** Given `--template <T> --format <F>`:
- `F=pdf` → `ddo/templates/typst/<T>.typst`, rendered via the **`typst` Python package, in-process** (hermetic; no system Typst install).
- `F∈{html,md}` → `ddo/templates/jinja2/<T>.<F>.jinja2`, rendered in-process with Jinja2 via `render(**data)` (templates consume top-level keys `meta`, `content`, `evidence_bank`).
- Trade-off: chose the hermetic Typst **Python package** over a system `typst` CLI subprocess, removing an external install and honoring the "hermetic build" tenet; cost is Typst version is pinned by the package.

**Validation gate (resolved).** `build.py` is the **single deterministic validation gate**, run before any render, exiting nonzero with a precise message on the first failure:
1. **Contract** — `meta` present with `doc_type, title, version, date, persona, template, output_formats`; `evidence_bank` present as an array.
2. **Evidence-ref integrity** — every ID in any `content.sections[*].evidence` exists in `evidence_bank`.
3. **Unfilled-input scan** — abort if any `[REQUIRES USER INPUT` substring remains anywhere in the YAML.
The `ddo-render` skill is a thin wrapper; it does not duplicate these checks.

**Storage layout (resolved).**
```
ddo/
├── build.py                      # PEP 723 hermetic orchestrator
├── schemas/{prd,scientific_report}.yaml
├── templates/
│   ├── typst/{prd,scientific_report}.typst
│   └── jinja2/{prd,scientific_report}.{html,md}.jinja2
└── personas/{product_critic,scientific_reviewer}.md   # forward-compat, unused in v0.0.1

Documents/<meta.date>_<meta.doc_type>_<title-slug>/    # gitignored
├── document_data.yaml            # source of truth (root)
└── output/<title-slug>.{pdf,html,md}                  # rendered artifacts
```
Folder name: `meta.date` (already `YYYY.MM.DD`) + `meta.doc_type` (verbatim) + `title-slug` (`meta.title` lowercased, spaces→hyphens). `ddo-ingest` creates the folder + writes the YAML; the `ddo-render` skill computes the `output/` path and passes a fully-resolved `--output` to `build.py` (build.py stays ignorant of the folder convention → unit-testable).

### System Graph Blast Radius
Greenfield: `spec/compiled/architecture.yml` is empty. v0.0.1 **creates** the initial node set. Proposed nodes (to be formalized by `/hyper-discover` / `/hyper-resolve`):
- **System:** `ddo_pipeline`
- **Module:** `build_orchestrator` (build.py), `schemas`, `templates`, `skills`
- **Atomic:** `validation_gate`, `typst_renderer`, `jinja_renderer`, `template_resolver`, `path_deriver`, `skill_ingest`, `skill_render`

### Execution Checklist (candidate MiniPRDs)
1. **MiniPRD: `build.py` core** — arg parsing, template resolution, Jinja2 + Typst-package rendering, `--timestamp`.
2. **MiniPRD: validation gate** — the three checks, fail-fast, precise messages (unit-tested first).
3. **MiniPRD: schema + template migration** — move/rename the six stubs + two schemas into `ddo/`; verify each renders against its schema.
4. **MiniPRD: `ddo-render` skill** — path derivation from `meta`, build invocation, reporting.
5. **MiniPRD: `ddo-ingest` skill** — zero-hallucination extraction, gap-flagging, overwrite protection, folder creation.
6. **MiniPRD: test suite + fixture bootstrap** — validation unit tests, determinism regression, ingest contract test, one-time human sign-off on render baselines.

### API / CLI Contract
```
uv run ddo/build.py \
  --data    <path/to/document_data.yaml> \
  --template <prd|scientific_report> \
  --format  <pdf|html|md> \
  --output  <path/to/output.ext> \
  [--timestamp <value>]      # pin Typst creation timestamp for byte-identical PDF
```
Exit 0 on success; nonzero with a single precise message on the first validation failure or render error.

### Dependencies
- **Runtime (PEP 723 inline in `build.py`):** `typst`, `jinja2`, `pyyaml`.
- **Dev (`pyproject.toml` `[dependency-groups]`):** `pytest`, `ruff`.
- **Lint contract:** ruff line-length 100, Google docstring convention (`D` rules on), isort first-party `ddo`, `PRDs/` excluded.
- **Tooling:** `uv` (hermetic). No system Typst, no Pandoc.

---

## 6. Negative Constraints

- **DO NOT** patch a rendered document directly — always patch `document_data.yaml` then re-render.
- **DO NOT** invent dates, metrics, citations, or technical specifics during ingest; write `[REQUIRES USER INPUT: <reason>]` instead.
- **DO NOT** auto-advance past a phase gate; every skill ends at `[WAITING FOR USER REVIEW]`.
- **DO NOT** overwrite an existing `document_data.yaml` from `ddo-ingest` without explicit human confirmation.
- **DO NOT** duplicate validation logic in the `ddo-render` skill; `build.py` is the single gate.
- **DO NOT** add a system-Typst or Pandoc dependency; rendering stays hermetic via PEP 723.
- **DO NOT** assert exact-content equality on `ddo-ingest` output in tests.
- **DO NOT** read `spec/archive/` or `tests/candidate_outputs/`; **DO NOT** let an agent write `tests/fixtures/` (human-promoted only).
- **DO NOT** add network access in v0.0.1 (local sources only).

---

## 7. Risks & Mitigation

- **Risk:** `.gitignore` lines 45–46 ignore `/tests` and `/spec` wholesale → the v0.0.1 regression tests and specs would not be committed. → **Mitigation:** fix `.gitignore` before the build phase so `tests/` (and intended `spec/` content) are tracked; verify with `git status` that new test files are stageable.
- **Risk:** `typst` Python package may not expose creation-timestamp control → `--timestamp` cannot be implemented in-process. → **Mitigation:** spike the API early; fall back to the package's bundled CLI entrypoint for timestamp pinning while keeping deps hermetic.
- **Risk:** migrated template stubs may reference fields the canonical schemas don't provide (or vice versa) → render failures. → **Mitigation:** MiniPRD 3 verifies each template renders against its schema with a complete example before wiring.
- **Risk:** PDF binaries in `tests/fixtures/` bloat git / are non-diffable. → **Mitigation:** decide at fixture-bootstrap whether to store the PDF or only its hash + the text outputs (PDF determinism is content-level, not byte-level by default anyway).
- **Risk:** ingest non-determinism makes "is this hallucinated?" un-automatable → silent fabrication. → **Mitigation:** Candidate Artifact protocol — ingest output is human-verified at the HITL gate before it is trusted or promoted to a fixture.

---

## 8. Success Metrics

- Both example documents (`prd`, `scientific_report`) render to **PDF, HTML, and MD** via `build.py` with exit 0.
- Repeated HTML/MD renders are **byte-identical**; repeated PDF renders are **content-identical**, and `--timestamp` yields **byte-identical** PDFs.
- All three validation checks **fail closed** with precise messages on crafted-invalid inputs (covered by unit tests).
- `ddo-ingest` turns a fixed fixture source into a **schema-valid, renderable** `document_data.yaml` with gaps flagged and zero invented content (human-verified).
- `uv run pytest`, `uv run ruff check .`, and `uv run ruff format --check .` all exit 0.

---

## Appendix: Decisions Locked During the Architect Interview

| # | Decision |
|---|---|
| Q1 | v0.0.1 scope = deterministic backbone (build.py + 2 schemas + 4 templates + ingest + render); full pipeline specified, adversarial loop deferred to v0.0.2+. Versioning line: v0.0.1, v0.0.2, … (repo at v0.0.0). |
| Q2 | Determinism: HTML/MD byte-identical by default; PDF content-identical, wall-clock timestamp default; byte-identical PDF opt-in via `--timestamp`. No PDF hash gate. |
| Q3 | `ddo/` layout + `typst/<T>.typst` & `jinja2/<T>.<F>.jinja2` resolution; stubs renamed to short doc-type names on migration. |
| Q4 | `build.py` is the single deterministic validation gate (contract, evidence-ref integrity, unfilled-input scan); render skill is a thin wrapper. |
| Q5 | `Documents/<date>_<doc_type>_<slug>/` with `output/` subfolder; skill computes paths, build.py stays path-agnostic. |
| Q6 | Hermetic `typst` Python package (in-process), not a system CLI; "install Typst" prerequisite dropped. |
| Q7 | `ddo-ingest`: no overwrite without confirmation; local files only (no network) in v0.0.1. |
| Q8 | `ddo-ingest` = sole Candidate Artifact (contract-validity + render-ability tests only, content human-verified); render baselines frozen to fixtures after one-time human sign-off. |
