# SuperPRD: DDO v0.0.6 — Expanded Ecosystem Tutorials

> **Phase:** Resolution (compiled). Source: `spec/active/Draft_PRD.md` +
> `spec/active/RedTeam_Report.md` (15 findings RT-01..RT-15, all triaged below).
> **Resolved by:** `/hyper-resolve` — 2026-07-02. User decisions logged in §5.2.
> **Next step:** `/hyper-execute` each MiniPRD in `spec/compiled/` in DAG order (§5.3),
> then `hypergraph_updater.py` + `/hyper-audit`.

---

## 1. Introduction & Goals

### Problem Statement
DDO today is unapproachable to a newcomer beyond the two shipped tutorials (a v0.0.1 render
walkthrough and a v0.0.2 adversarial-loop walkthrough), and it only demonstrates two formal
document types (`prd`, `scientific_report`). New users cannot learn the newer v0.0.4/v0.0.5
capabilities, and the system fails to demonstrate its breadth across casual-to-formal work.

The Red Team sharpened one honesty problem in the original goal: the Draft's "complete
workflow / end-to-end pipeline" claim was **not** uniformly true across the three proposed
tutorials — two of three (evidence-lens, persona-authoring) inspect/author rather than run
the pipeline; only Tutorial 2 renders (RT-15). The goal is therefore restated per tutorial
(§4) rather than as a single blanket value-loop sentence.

### Solution Overview
Add **three new golden-path tutorials** to the existing `tutorials/` tree — each a directory
following the established convention (`tutorial.md` + `input_files/` + `output_files/` +
`code_samples/` + `screenshots/`) — and back them with **four new, fully regression-tested
document types**, each shipped as a complete worked example: schema + 3 templates + example
YAML + a dedicated persona + a dedicated style.

Five Red Team hardenings are baked into the design so the one new *enforcement* surface (the
anti-rot guard) is real rather than theatre, and so the zero-hallucination invariant is not
silently eroded by the new casual register:

1. **The anti-rot guard is a walk + explicit `EXPECTED_MIRRORS` map** (RT-01/02/05): it walks
   each `input_files/`, byte-compares every mapped copy against a source that may live in
   **either `tests/data/` or `tests/fixtures/`**, requires every `input_files/*.yaml` to be
   *either mapped or explicitly marked standalone*, and asserts the map is non-empty and
   includes Tutorial 1's `ingest_output.yaml`. A guard that checks zero pairs can no longer
   pass green.
2. **Casual evidence is sourced, never invented** (RT-04): `validation.py:106` hard-fails on
   `total_refs == 0`, so every casual example carries a **minimal but genuine** `evidence_bank`
   whose entries trace to a real narrative source doc shipped in the tutorial's `input_files/`
   — exactly as the adversarial-loop tutorial cites `copolyester-optimization.md`. No contract
   surgery, no Python change.
3. **Persona/style references are CI-verified** (RT-08/10): a new `test_schema_meta_refs.py`
   asserts every schema's and every example's `meta.persona`/`meta.style_profile` resolves to
   a real file, and that each example's section ids conform to its schema — closing the
   silent-green typo path and the US-004/US-005 ordering hazard.
4. **`output_files/` renders are guarded** (RT-07): the committed `.html`/`.md` renders are
   asserted byte-identical to a fresh `build.py` render, so the first thing a tutorial promises
   (reproducibility) cannot rot. PDF snapshots are declared illustrative-only (Typst
   font/glyph fragility, RT-12).
5. **Casual register is stress-tested for determinism now** (RT-09/12): all four templates are
   pure functions of the YAML (no clock/locale), and at least one casual example carries a
   deliberately non-ASCII value to force the font-coverage question at fixture-authoring time.

### Target Audience
New DDO users (learning the pipeline) and existing users (authoring their own document types,
personas, and styles).

---

## 2. Confidence Mandate
- **Confidence Score:** 10 / 10. All 15 Red Team findings have a documented decision (§5.2).
  The two Critical findings (RT-01 guard scope misses `tests/fixtures/`, RT-02 guard
  reference-discovery unspecified) are resolved by a single explicit-map guard design. The
  five Major findings (RT-04 evidence-mandatory contract, RT-05 ungated fixture replica, RT-06
  ruff on `code_samples`, RT-07 unguarded `output_files`, RT-08 persona/style resolution) were
  adjudicated with the user on 2026-07-02. The eight Minor findings (RT-03, RT-09..RT-15) were
  approved as proposed defaults (§5.2). The token-budget question is resolved by splitting the
  four document types into four self-contained per-type MiniPRDs (§5.3).
- **Clarifying Questions:** None remaining.

---

## 3. Scope

### In-Scope
- **Three new tutorial directories** under the existing top-level `tutorials/` tree, each
  conforming to the established convention, named `ddo-v006-<slug>`:
  - **`ddo-v006-evidence-bank-workflow`** — Tutorial 1: evidence referencing & citation
    integrity, anchored to the human-promoted `tests/fixtures/ingest_output.yaml`; framed as a
    citation-integrity **lens**, explicitly **not** a second loop walkthrough (RT-15,
    falsifiable per US-001 AC3).
  - **`ddo-v006-authoring-custom-structures`** — Tutorial 2: introduces the four new document
    types; `blog_post` is the from-scratch primary walkthrough, the other three are worked
    examples. **This is the tutorial that renders** (RT-15).
  - **`ddo-v006-writing-structured-personas`** — Tutorial 3: authoring a persona via
    `ddo-create-persona` (v0.0.4 AV-table format); uses the four new personas as specimens.
- **Four new document types**, each a complete self-contained worked example:
  | Doc type | Schema | Templates | Persona (new) | Style (new) |
  |---|---|---|---|---|
  | `blog_post` | `ddo/schemas/blog_post.yaml` | `typst/`,`jinja2/*.html`,`jinja2/*.md` | `content_editor` | `blog_casual` |
  | `meeting_notes` | `ddo/schemas/meeting_notes.yaml` | ×3 | `meeting_recorder` | `notes_concise` |
  | `meeting_agenda` | `ddo/schemas/meeting_agenda.yaml` | ×3 | `meeting_facilitator` | `agenda_directive` |
  | `project_report` | `ddo/schemas/project_report.yaml` | ×3 | `project_stakeholder` | `executive_formal` |
- **12 new templates** — `ddo/templates/typst/<type>.typst` + `ddo/templates/jinja2/<type>.html.jinja2`
  + `ddo/templates/jinja2/<type>.md.jinja2` for each type. Every type supports all three formats.
- **4 new example YAMLs** in `tests/data/`, each enrolled in a single **consolidated**
  `EXAMPLES` list (RT-03) → inherits M1/M2/M3/M3b determinism coverage. Each carries a genuine
  `evidence_bank` grounded in a real narrative source doc (RT-04).
- **4 new narrative source docs** (one per type) shipped in Tutorial 2's `input_files/`,
  providing the traceable ground truth for each casual example's evidence (RT-04).
- **4 new personas** (AV-table, v0.0.4) and **4 new styles** (five-section, v0.0.5) — authored
  as conforming files; auto-covered by glob-based `test_personas.py` / `test_styles.py`.
- **New test surfaces:**
  - `tests/unit/test_tutorial_refs.py` — the anti-rot guard: `input_files/` walk + explicit
    `EXPECTED_MIRRORS` map covering `tests/data/` **and** `tests/fixtures/` (RT-01/02/05).
  - `tests/integration/test_schema_meta_refs.py` — persona/style resolution + soft
    schema-conformance for every schema and every `tests/data/*.yaml` (RT-08/10).
  - `output_files/` determinism guard (`.html`/`.md` byte-equality vs. fresh render) (RT-07).
  - `EXAMPLES` consolidated to one module-level list imported by both integration files (RT-03).
  - A `slow` pytest marker gating the full determinism cross-product; default `pytest` runs a
    fast subset, CI runs the full matrix (RT-11).
- **Register the `tutorials/` tree as a hypergraph `Module` node** (`tutorials`), reframed as
  meta-documentation demonstrating the pipeline (§5.1); plus a `test_tutorial_refs_unit` node.
- Hypergraph update (`hypergraph_updater.py`) for all affected + new nodes.

### Out-of-Scope
- **No Python module changes** to `ddo/*.py` — the render/validate/mutate machinery is
  unchanged. *(Note: new/edited `tests/*.py` is explicitly in-scope — the RT-06 wording
  ambiguity is resolved here in favour of `ddo/*.py` only.)*
- **No schema-contract changes** — the DDO minimal contract (`meta` + `evidence_bank` + ≥1
  evidence ref) is retained verbatim for all four new types. RT-04 is discharged by sourcing
  evidence, **not** by relaxing `validation.py`.
- **No new skills** — reuse the existing seven; tutorials *demonstrate* `ddo-create-persona` /
  `ddo-create-style`, they don't add skills.
- **No changes to the two existing tutorials** beyond incidental (they are not rewritten).
- **No executable-doc test framework** — tutorials are not parsed/run; anchoring is by
  fixture-copy + byte-equality guard.
- **No dogfooding of `tutorial.md`** — each is plain hand-authored Markdown.
- **No new actors or permission model.**
- **No directory-level ruff exclusion** — new `code_samples/*.py` are constrained ruff-clean
  instead (RT-06).
- Golden-baseline *promotion* into `tests/fixtures/` for the four new types is a **downstream
  human-gated step** (`DDO_FIXTURE_SIGNOFF=1`), flagged but not force-completed in execution.

### Accepted-risk caveats (surfaced, not mitigated further)
- **Ungated `input_files/` replica of a signed fixture** (RT-05): Tutorial 1's copy of
  `tests/fixtures/ingest_output.yaml` lives under `tutorials/`, outside `DDO_FIXTURE_SIGNOFF`.
  The guard enforces **sameness** (byte-equality against the fixture), not **provenance** — the
  gate boundary is documented in Tutorial 1's `tutorial.md`, and the fixture remains canonical
  (fixture → copy direction). Full provenance enforcement is out-of-scope.
- **Content-directive absence in styles is HITL-only** (RT-14): `test_styles.py` enforces
  structure + sentinel-absence, **not** the absence of quantitative/content-bearing imperatives.
  §7 is corrected accordingly; no lexical scanner is added (matches v0.0.5).

---

## 4. User Stories (Atomic)

| ID | User Story | Acceptance Criteria | Priority |
|---|---|---|---|
| US-001 | As a **new user**, I want a tutorial focused on the evidence-bank / citation-integrity workflow so I understand how claims trace to sources. | 1. `tutorials/ddo-v006-evidence-bank-workflow/` exists with the full directory convention.<br>2. `input_files/` mirrors the human-promoted `tests/fixtures/ingest_output.yaml`, byte-identical (guarded).<br>3. **(RT-15, falsifiable)** `tutorial.md` contains **zero** `ddo-refine`/`ddo-interview` command invocations and links to the loop tutorial rather than re-walking it. | High |
| US-002 | As a **user**, I want to author a new document type by example so I can model my own structures. | 1. `tutorials/ddo-v006-authoring-custom-structures/` walks `blog_post` from scratch.<br>2. The other three types appear as worked examples.<br>3. Each `input_files/*.yaml` copy is byte-identical to its `tests/data/` source (guarded).<br>4. **(RT-15)** At least one command block renders a type via `build.py` with exit 0. | High |
| US-003 | As a **user**, I want a tutorial on writing structured personas so I can build my own review lens. | 1. `tutorials/ddo-v006-writing-structured-personas/` uses the v0.0.4 AV-table format.<br>2. It drives `ddo-create-persona`.<br>3. It cites the four new personas as specimens. | High |
| US-004 | As a **user**, I want four new document types that render deterministically so they are trustworthy examples. | 1. Each type has a schema + 3 templates + example YAML.<br>2. Each is in the consolidated `EXAMPLES`.<br>3. `uv run pytest tests/integration/` passes M1/M2/M3/M3b for all four.<br>4. **(RT-04)** Each example carries a genuine `evidence_bank` grounded in a real `input_files/` narrative doc — none is evidence-free. | High |
| US-005 | As a **user**, I want each new type to ship a dedicated persona and style so I have complete worked examples of both v0.0.4 and v0.0.5. | 1. 4 personas pass `test_personas.py`.<br>2. 4 styles pass `test_styles.py`.<br>3. **(RT-08, CI-enforced)** `test_schema_meta_refs.py` asserts each schema's & example's `meta.persona`/`meta.style_profile` resolve to the new files. | High |
| US-006 | As a **maintainer**, I want tutorials guarded against fixture rot so renamed/drifted fixtures fail CI loudly. | 1. **(RT-01/02)** `test_tutorial_refs.py` walks `input_files/` and byte-compares each mapped copy against an `EXPECTED_MIRRORS` source in `tests/data/` **or** `tests/fixtures/`.<br>2. It asserts the map is non-empty, includes `ingest_output.yaml`, and that every `input_files/*.yaml` is mapped or explicitly standalone.<br>3. It runs in the default `pytest` suite. | High |
| US-007 | As a **contributor**, I want lint + tests green so v0.0.6 meets the merge bar. | 1. `uv run ruff check .` exits 0 (incl. new `code_samples/*.py`, RT-06).<br>2. `uv run ruff format --check .` exits 0.<br>3. `uv run pytest` passes. | High |
| US-008 | As a **maintainer**, I want the committed tutorial renders to stay reproducible so a newcomer's first render matches. | 1. **(RT-07)** An `output_files/` guard asserts each committed `.html`/`.md` equals a fresh `build.py` render of its input.<br>2. PDF snapshots are declared illustrative-only (RT-12). | Medium |

---

## 5. Technical Specifications

### 5.1 Architecture & Resolved Trade-offs

- **Tutorials live in the existing top-level `tutorials/` tree**, each a **directory**
  `tutorials/ddo-v006-<slug>/` mirroring the shipped `ddo-v001-prd-workflow/` and
  `ddo-adversarial-loop-v0.0.2/` layout.
- **Each `tutorial.md` is plain hand-authored Markdown, not DDO-rendered.** The pipeline is
  dogfooded by the four example docs and their **guarded** `output_files/` renders (RT-07).
- **The anti-rot guard is the design's only new enforcement surface** and is specified precisely
  (RT-01/02/05): an `input_files/` **walk** (no prose parsing, RT-13 — three naming schemes
  coexist so no name-pattern discovery) plus an explicit in-repo `EXPECTED_MIRRORS` mapping
  `{input_path: source_path}` spanning `tests/data/` **and** `tests/fixtures/`.
- **Casual evidence is sourced from a real narrative doc** (RT-04): each casual example's
  `evidence_bank` traces to a `input_files/<type>_source.md` narrative doc, mirroring the
  adversarial-loop convention. Zero-hallucination is preserved; `validation.py` is untouched.
- **Persona/style resolution + schema conformance are CI-verified** (RT-08/10) via
  `test_schema_meta_refs.py`, eliminating the silent-green typo and the US-004/US-005 ordering
  hazard structurally (each per-type MiniPRD ships persona+style+schema atomically — §5.3).
- **`output_files/` `.html`/`.md` are determinism-guarded; PDF snapshots are illustrative-only**
  (RT-07/12): text renders are byte-stable and cheap to re-verify; PDF byte-determinism in a
  committed snapshot is fragile under new fonts/glyphs and is not asserted.
- **Every new type supports all three formats** — preserves the determinism harness as a clean
  `EXAMPLES × ["pdf","html","md"]` cross-product.
- **Full 1:1 worked-example symmetry** — each doc type ships its own persona *and* style.
- **Templates are pure functions of the YAML** (RT-09): no `now()`/clock/locale reads; M3b
  already catches timestamp non-determinism.
- **Suite runtime is bounded** (RT-11): `EXAMPLES` grows 2 → 6, tripling determinism
  subprocesses; the full cross-product (plus PDF multi-render and the `output_files` guard) is
  gated behind a `slow` marker. Default `pytest` runs a fast subset; CI runs the full matrix.
- **`tutorials` is registered as meta-documentation** (graph-modeling note): it is a `Module`
  node whose description frames it as tutorials *about* the pipeline (per CLAUDE.md's
  toolchain-framing discipline), retaining `implements: ddo_system` as the closest available
  relation.

### 5.2 Red Team Decision Log (RT-01 .. RT-15)

| ID | Sev | Finding | Decision (user-adjudicated 2026-07-02) |
|---|---|---|---|
| RT-01 | Critical | Guard scope is `tests/data/`; Tutorial 1 anchors to `tests/fixtures/ingest_output.yaml`, never checked. | **Explicit `EXPECTED_MIRRORS` map spanning `tests/data/` AND `tests/fixtures/`.** Map asserted non-empty & includes `ingest_output.yaml`. |
| RT-02 | Critical | Guard reference-discovery + pairing unspecified (robust vs. theatre). | **`input_files/` walk (no prose parsing) + `EXPECTED_MIRRORS` map.** Every `input_files/*.yaml` must be mapped or explicitly marked standalone. |
| RT-04 | Major | `validation.py:106` mandates ≥1 evidence ref; casual types cannot be evidence-free. | **Source casual evidence from a real `input_files/<type>_source.md` narrative doc.** No contract/Python change. Stated in §5.1 + §7. |
| RT-05 | Major | Tutorial 1 creates an ungated replica of a `DDO_FIXTURE_SIGNOFF`-protected fixture. | **Guard enforces sameness (byte-equality vs. fixture); provenance boundary documented in Tutorial 1.** Full provenance enforcement out-of-scope (accepted risk). |
| RT-06 | Major | `tutorials/` is ruff-linted; new `code_samples/*.py` can sink US-007. | **Constrain `code_samples/*.py` ruff-clean; forbid directory-level ruff exclusion.** (`.md`/`.sh` are not linted by ruff — no config needed.) |
| RT-07 | Major | `output_files/` renders unguarded; "dogfooded by output_files" can rot. | **Add an `output_files/` determinism guard for `.html`/`.md`.** PDF snapshots illustrative-only (RT-12). |
| RT-08 | Major | US-005 AC3 (persona/style resolve) has no CI surface; typo ships silently. | **Add `test_schema_meta_refs.py`** asserting persona/style resolution for every schema & example. |
| RT-03 | Minor | `EXAMPLES` duplicated across two files; divergence → silent under-coverage. | **Consolidate to one module-level list imported by both** integration files. |
| RT-09 | Minor | Confirm all 4 templates are clock/locale-free (M3b). | **Author templates as pure functions of YAML; assert at authoring.** No new test (M3b covers it). |
| RT-10 | Minor | No binding between example YAML sections and its schema's declared sections. | **Soft schema-conformance check** folded into `test_schema_meta_refs.py` (example section ids ⊆/= schema sections). |
| RT-11 | Minor | Integration subprocess count ~3×; no per-suite time budget (missing NFR). | **`slow` marker gates full matrix; default `pytest` runs fast subset; CI runs full.** Stated budget (§5.5). |
| RT-12 | Minor | New casual/non-ASCII register untested against Typst font coverage. | **Add one deliberately non-ASCII value** (accented attendee name in `meeting_notes`). PDF `output_files` illustrative-only. |
| RT-13 | Minor | Three tutorial naming schemes coexist; discovery must not assume one. | **Guard by directory walk, never name pattern** (already implied by `EXPECTED_MIRRORS`). |
| RT-14 | Minor | "No content-bearing style imperatives" is HITL-only; §7 overstates `test_styles.py`. | **Correct §7 wording to HITL-only.** No lexical scanner added. |
| RT-15 | Minor | Success metric assigns "render a document" to the non-rendering Tutorial 1. | **Reassign render metric/story to Tutorial 2; make US-001 AC3 falsifiable** (zero loop-command invocations + cross-link). |

### 5.3 Execution Checklist (compiled MiniPRDs — DAG order)

The four document types are split into **four self-contained per-type MiniPRDs** (token-budget
resolution): each ships its persona + style + schema + 3 templates + example YAML + narrative
source doc + `EXAMPLES` enrollment as one atomic worked example, structurally eliminating the
RT-08 ordering hazard.

| MiniPRD | File | Node(s) | Depends on |
|---|---|---|---|
| **MP-0** Harness Prep | `MiniPRD_00_HarnessPrep.md` | `render_fixture`, `test_render_determinism`, `tests_integration` | — |
| **MP-1** blog_post | `MiniPRD_01_BlogPost.md` | `ddo_schemas`, `ddo_templates`, `ddo_personas`, `ddo_styles` | MP-0 |
| **MP-2** meeting_notes | `MiniPRD_02_MeetingNotes.md` | same | MP-0 |
| **MP-3** meeting_agenda | `MiniPRD_03_MeetingAgenda.md` | same | MP-0 |
| **MP-4** project_report | `MiniPRD_04_ProjectReport.md` | same | MP-0 |
| **MP-5** Tutorial 1 (evidence-bank) | `MiniPRD_05_Tutorial1_EvidenceBank.md` | `tutorials` | MP-0 |
| **MP-6** Tutorial 2 (authoring) | `MiniPRD_06_Tutorial2_AuthoringStructures.md` | `tutorials` | MP-1..MP-4 |
| **MP-7** Tutorial 3 (personas) | `MiniPRD_07_Tutorial3_WritingPersonas.md` | `tutorials` | MP-1..MP-4 |
| **MP-8** Anti-Rot Guard + Hypergraph | `MiniPRD_08_AntiRotGuard_Hypergraph.md` | `test_tutorial_refs_unit` (new), `tutorials` (register), `tests_unit`, `ddo_system` | MP-5..MP-7 |

### 5.4 System Graph Blast Radius (`architecture.yml`)

**New nodes:**
- `tutorials` — `Module`, `associated_file: tutorials/`, `implements: ddo_system`. Description
  framed as meta-documentation demonstrating the pipeline (registers the 2 shipped + 3 new
  tutorials).
- `test_tutorial_refs_unit` — `Atomic`, `associated_file: tests/unit/test_tutorial_refs.py`,
  `implements: tests_unit`, `depends_on: tutorials`.

**Existing nodes → `needs_review`:**
- `ddo_schemas` (+4 schemas), `ddo_templates` (+12 templates), `ddo_personas` (+4 personas),
  `ddo_styles` (+4 styles) — and their **descriptions** updated to drop the stale
  `prd/scientific_report`-only enumerations.
- `render_fixture` (consolidated `EXAMPLES`), `test_render_determinism` (`EXAMPLES` import +
  `slow` marker), `tests_unit` (new test file), `tests_integration` (widened coverage +
  `test_schema_meta_refs.py` + `output_files` guard).
- `ddo_core` — verify its prose does not enumerate the two old types (RT-5 blast-radius gap);
  mark `needs_review` if it does.
- `ddo_system` description updated to note the v0.0.6 ecosystem expansion + `tutorials`
  registration.

### 5.5 NFR — Integration-Suite Wall-Clock Budget (RT-11)
- **Default `pytest`** (fast subset, `-m "not slow"`): target **< ~90s** on a warm `uv` cache —
  runs one determinism format per example + all unit tests + the two new guards.
- **Full matrix** (`slow` included, as CI runs): the complete `EXAMPLES × [pdf,html,md] ×
  {M1,M2,M3,M3b}` cross-product plus the `output_files` guard. Budget is a **target to validate
  at execution**, not a measured guarantee; if the full matrix approaches CI timeout, further
  shard by format.

### 5.6 API Contracts / Schema (section shapes)

All four schemas satisfy the **unchanged** DDO minimal contract: a `meta` block (`doc_type`,
`title`, `version`, `date`, `authors`, `status`, `persona`, `style_profile`, `output_formats`,
`template`, `review_log`) + `content.sections[*]` (`id`, `title`, `body`, `claims`, `evidence`)
+ an `evidence_bank` array (≥1 referenced entry).

- **`blog_post`** — persona `content_editor`, style `blog_casual`. Sections: `hook`, `context`,
  `main_point`, `supporting_detail`, `conclusion_cta`.
- **`meeting_notes`** — persona `meeting_recorder`, style `notes_concise`. Sections:
  `attendees`, `agenda_covered`, `decisions`, `action_items`, `next_steps`. *(Carries the
  non-ASCII fixture value, RT-12.)*
- **`meeting_agenda`** — persona `meeting_facilitator`, style `agenda_directive`. Sections:
  `meeting_objective`, `agenda_items` (time-boxed, owner-attributed — **string literals**, no
  computed durations, RT-09), `pre_reads`, `logistics`.
- **`project_report`** — persona `project_stakeholder`, style `executive_formal`. Sections:
  `executive_summary`, `status`, `milestones`, `risks`, `metrics`, `next_steps`.

### 5.7 Dependencies
- No new libraries. Existing `uv` / PEP 723 hermetic build, `typst`, `jinja2`, `pytest`,
  `ruff`, `pyyaml`.
- **Hard dependency:** v0.0.4 (AV-table persona + `ddo-create-persona`) and v0.0.5 (styles +
  `ddo-create-style`) — both landed.
- **Convention dependency:** the shipped tutorial directory layout is the template for the
  three new tutorial directories.

---

## 6. Negative Constraints
- **DO NOT** modify any `ddo/*.py` module — v0.0.6 is domain files + docs + tests only.
  (Editing/adding `tests/*.py` **is** permitted — this resolves the §3 vs §6 wording ambiguity.)
- **DO NOT** change the DDO minimal contract or add per-type validation. RT-04 is discharged by
  **sourcing** evidence, never by relaxing `validation.py`.
- **DO NOT** give a casual example an empty `evidence_bank` — it will hard-fail `validation.py:106`.
- **DO NOT** invent a new tutorial layout — follow the existing
  `tutorials/<name>/{tutorial.md,input_files,output_files,code_samples,screenshots}` convention.
- **DO NOT** let a tutorial `input_files/*.yaml` drift from its mapped source — keep byte-identical
  (guarded by `test_tutorial_refs.py` against `tests/data/` **or** `tests/fixtures/`).
- **DO NOT** discover tutorial references by prose/regex or by name pattern — walk `input_files/`
  and use the explicit `EXPECTED_MIRRORS` map (RT-02/13).
- **DO NOT** author `tests/fixtures/ingest_output.yaml` or `tests/fixtures/loop/*` — Tutorial 1
  references the existing human-promoted fixtures only.
- **DO NOT** rewrite or restructure the two existing shipped tutorials.
- **DO NOT** duplicate the `ddo-adversarial-loop-v0.0.2` tutorial — Tutorial 1 is a citation
  lens with **zero** `ddo-refine`/`ddo-interview` invocations (RT-15).
- **DO NOT** give any new type a partial format set — all four support `pdf`/`html`/`md`.
- **DO NOT** exclude `tutorials/` (or any subdirectory) from ruff — keep `code_samples/*.py`
  ruff-clean instead (RT-06).
- **DO NOT** read a clock/locale in any template — templates are pure functions of the YAML (RT-09).
- **DO NOT** assert PDF byte-equality on committed `output_files/` snapshots — text only (RT-07/12).
- **DO NOT** fabricate or hand-promote golden baselines into `tests/fixtures/` — promotion is
  human-gated via `DDO_FIXTURE_SIGNOFF=1`.
- **DO NOT** embed content-bearing/quantitative imperatives in the new style files (v0.0.5
  rubric); styles are phrasing/register-only. *(Enforced at HITL authoring, not by
  `test_styles.py` — RT-14.)*
- **DO NOT** build an executable-doc test framework that parses/runs tutorial command blocks.
- **DO NOT** add a new skill; reuse the existing seven.

---

## 7. Risks & Mitigation
- **Risk:** A casual example ships evidence-free and hard-fails `validation.py:106` (RT-04). →
  **Mitigation:** each casual `evidence_bank` is sourced from a real `input_files/<type>_source.md`
  narrative doc; `test_schema_meta_refs.py` + the determinism suite catch a contentless doc.
- **Risk:** New `code_samples/*.py` sink the ruff gate (RT-06). → **Mitigation:** samples are
  authored ruff-clean/runnable (matching the existing 3 green samples); a negative constraint
  forbids dir-level ruff exclusion.
- **Risk:** The anti-rot guard passes green while checking nothing (RT-01/02). → **Mitigation:**
  `EXPECTED_MIRRORS` is asserted non-empty, must include `ingest_output.yaml`, and every
  `input_files/*.yaml` must be mapped or explicitly standalone.
- **Risk:** A typo'd `meta.persona`/`meta.style_profile` ships silently (RT-08). →
  **Mitigation:** `test_schema_meta_refs.py` resolves every reference to a real file in CI.
- **Risk:** Committed `output_files/` renders drift from `build.py` (RT-07). → **Mitigation:**
  `.html`/`.md` byte-equality guard; PDF declared illustrative-only.
- **Risk:** Casual/non-ASCII register breaks Typst byte-determinism (RT-12). → **Mitigation:**
  a deliberate non-ASCII value forces the font question at authoring; PDF `output_files` unguarded.
- **Risk:** Integration suite runtime triples (RT-11). → **Mitigation:** `slow`-marker-gated
  full matrix; fast default; stated budget (§5.5).
- **Risk:** MiniPRD over the 50k output-token budget. → **Mitigation:** four self-contained
  per-type MiniPRDs (§5.3).
- **Risk:** New styles smuggle content directives, violating the v0.0.5 contract. →
  **Mitigation:** apply the `ddo-create-style` rejection rubric during authoring.
  **`test_styles.py` enforces structure + sentinel-absence only — content-directive absence is
  HITL-reviewed, not CI-enforced (RT-14).**
- **Risk:** Tutorial 1 perceived as redundant with the loop tutorial. → **Mitigation:** zero
  loop-command invocations + cross-link (US-001 AC3, RT-15).

---

## 8. Success Metrics
- `tutorials/` gains three convention-conformant directories; **`test_tutorial_refs.py` asserts
  ≥5 mapped pairs including `ingest_output.yaml` and all four new `tests/data/*.yaml`**, every
  one byte-identical to its source (RT-01/02).
- Four new document types each render `pdf`/`html`/`md` with exit 0 and pass M1/M2/M3/M3b.
- **`test_schema_meta_refs.py` green:** every schema's & example's `meta.persona`/
  `meta.style_profile` resolves, and every example's sections conform to its schema (RT-08/10).
- `test_personas.py` and `test_styles.py` pass with the four new personas and four new styles.
- **`output_files/` guard green:** each committed `.html`/`.md` equals a fresh `build.py` render
  (RT-07).
- `uv run ruff check .` and `uv run ruff format --check .` both exit 0; `uv run pytest` passes
  (fast default); the full `slow` matrix passes in CI.
- The `tutorials` node is registered and all affected `architecture.yml` nodes reconcile to
  `clean` after `/hyper-audit`.
- A newcomer can follow **Tutorial 2** end-to-end and produce a rendered, evidence-linked
  document with exit 0 (HITL-verified) — the render metric now belongs to the tutorial that
  actually renders (RT-15).
