# SuperPRD: DDO v0.0.6 — Expanded Ecosystem Tutorials

> **Status:** DRAFT (Phase 1 — Architect output). Next step: `/hyper-redteam` for adversarial analysis, then `/hyper-resolve` to compile the final SuperPRD + MiniPRDs.
> **Source plan:** `PRDs/LivingMasterPlan_v0.0.4-v0.0.6.md` (v0.0.6 section).
> **Foundation:** v0.0.4 (structured persona nomenclature + `ddo-create-persona`) and v0.0.5 (style profiles + `ddo-create-style`) both landed; `architecture.yml` fully `clean`.
> **Correction (2026-07-01):** an earlier draft framed `tutorials/` as a new directory of flat Markdown files. Corrected: `tutorials/` **already exists** (git-tracked) with two shipped tutorials and an established per-tutorial *directory* convention. This draft conforms to that convention. See §5.

---

## 1. Introduction & Goals

- **Problem Statement:** DDO today is unapproachable to a newcomer beyond the two shipped tutorials (a v0.0.1 render walkthrough and a v0.0.2 adversarial-loop walkthrough), and it only demonstrates two formal document types (`prd`, `scientific_report`). New users cannot learn the newer capabilities, and the system fails to demonstrate its breadth across casual-to-formal document work.
- **Solution Overview:** Add **three new golden-path tutorials** to the existing `tutorials/` tree — each as a directory following the established convention (`tutorial.md` + `input_files/` + `output_files/` + `code_samples/` + `screenshots/`) — teaching the core DDO workflows and the v0.0.4/v0.0.5 capabilities. Back them with **four new, fully regression-tested document types**, each shipped as a complete worked example: schema + 3 templates + example YAML + a dedicated persona + a dedicated style. The tutorials are the user-facing deliverable; the four document types are the supporting fixtures that make Tutorial 2 concrete and independently expand the ecosystem.
- **Primary Value Loop:** *A user follows a tutorial and successfully executes a complete DDO workflow against a real, regression-tested fixture* — proving the pipeline works end-to-end on document types ranging from casual (`blog_post`) to formal (`project_report`).
- **Target Audience:** New DDO users (learning the pipeline) and existing users (authoring their own document types, personas, and styles).

---

## 2. Confidence Mandate

- **Confidence Score:** 8 / 10 — the design is fully specified after a five-phase architect interview and reconciled against the pre-existing `tutorials/` convention; remaining unknowns are decomposition/budget details, per-schema section shapes, and Tutorial 1's scope relative to the existing loop tutorial.
- **Clarifying Questions (for Red Team / Resolve):**
  1. **MiniPRD token budget:** Four document types × (1 schema + 3 templates + 1 example YAML) may exceed the 50k output-token ceiling for a single MiniPRD. One MiniPRD or **split per document type** (4 MiniPRDs)? (Recommendation: split per type.)
  2. **Exact section structure of each new schema** — proposed in §5 (API Contracts); needs a correctness/appropriateness pass.
  3. **Tutorial 1 vs. the existing loop tutorial:** the shipped `tutorials/ddo-adversarial-loop-v0.0.2/` already walks the full Ingest → Red Team → Interview → Refine loop. Proposed **Tutorial 1 (Evidence Bank Workflow)** must be positioned as a *distinct evidence-referencing / citation-integrity lens* (using `tests/fixtures/ingest_output.yaml`) rather than a second loop tutorial — or folded into the existing one. Confirm the distinct-lens framing (recommendation) vs. merge/drop.
  4. **Anchoring vs. duplication:** the existing convention *copies* the fixture into a tutorial's `input_files/` (byte-identical to `tests/data/`). That duplication can drift. Confirm the anti-rot guard should assert **byte-equality** between each tutorial `input_files/*.yaml` and its `tests/data/` source (recommendation), not merely path existence.
  5. **Evidence_bank in casual types:** `blog_post`/`meeting_notes` still must satisfy the DDO minimal contract. Confirm the contract is retained unchanged for all four (recommendation: yes — no schema-contract surgery).

---

## 3. Scope

### In-Scope
- Three **new tutorial directories** added under the existing top-level `tutorials/` tree, each conforming to the established convention (`tutorial.md` + `input_files/` + `output_files/` + `code_samples/` + `screenshots/`), named `ddo-v006-<slug>`:
  - **`ddo-v006-evidence-bank-workflow`** — Tutorial 1: evidence referencing & citation integrity, anchored to `tests/fixtures/ingest_output.yaml`; positioned as a citation-integrity lens distinct from the existing loop tutorial.
  - **`ddo-v006-authoring-custom-structures`** — Tutorial 2: introduces the four new document types; `blog_post` is the from-scratch primary walkthrough, the other three are worked examples.
  - **`ddo-v006-writing-structured-personas`** — Tutorial 3: authoring a persona via `ddo-create-persona` using the v0.0.4 AV-table format; uses the four new personas as specimens.
- **Register the `tutorials/` tree as a hypergraph `Module` node** (`tutorials`) — it exists on disk and is git-tracked but is currently absent from `architecture.yml`; registration brings the two pre-existing tutorials plus the three new ones under graph tracking.
- **Four new document types**, each a complete worked example:
  | Doc type | Schema | Templates | Persona (new) | Style (new) |
  |---|---|---|---|---|
  | `blog_post` | `ddo/schemas/blog_post.yaml` | `.typst`, `.md.jinja2`, `.html.jinja2` | `content_editor` | `blog_casual` |
  | `meeting_notes` | `ddo/schemas/meeting_notes.yaml` | ×3 | `meeting_recorder` | `notes_concise` |
  | `meeting_agenda` | `ddo/schemas/meeting_agenda.yaml` | ×3 | `meeting_facilitator` | `agenda_directive` |
  | `project_report` | `ddo/schemas/project_report.yaml` | ×3 | `project_stakeholder` | `executive_formal` |
- **12 new templates** (4 types × 3 formats); every type supports all three formats (`pdf`/`html`/`md`).
- **4 new example YAMLs** in `tests/data/`, each enrolled in the `EXAMPLES` list in **both** `tests/integration/conftest.py` and `tests/integration/test_render_determinism.py` → inherits M1/M2/M3/M3b determinism coverage. Tutorial 2's `input_files/` hold **byte-identical copies** of these (existing anchoring convention).
- **4 new personas** (AV-table format, v0.0.4) and **4 new styles** (five-section format, v0.0.5) — authored directly as conforming files; auto-covered by glob-based `test_personas.py` / `test_styles.py`.
- **One new anti-rot unit test** (`tests/unit/test_tutorial_refs.py`): asserts (a) every fixture/data path a tutorial references exists on disk, and (b) each tutorial `input_files/*.yaml` that mirrors a `tests/data/` fixture is **byte-identical** to it.
- Hypergraph update (`hypergraph_updater.py`) for all affected + new nodes.

### Out-of-Scope
- **No Python module changes** to `ddo.build`, `ddo.validation`, `ddo.review`, `ddo.refine`, `ddo.ingest`, `ddo.paths` — the render/validate/mutate machinery is unchanged.
- **No schema-contract changes** — the DDO minimal contract (`meta` + `evidence_bank`) is retained verbatim for all four new types.
- **No new skills** — reuse the existing seven; tutorials *demonstrate* `ddo-create-persona`/`ddo-create-style`, they don't add skills.
- **No changes to the two existing tutorials** beyond what's incidental; they are not rewritten by v0.0.6.
- **No executable-doc test framework** — tutorials are not parsed/run; anchoring is by fixture-copy + byte-equality guard.
- **No dogfooding** — each `tutorial.md` is plain hand-authored Markdown (validated by the existing convention), not a DDO-rendered document.
- **No new actors or permission model.**
- Golden-baseline *promotion* into `tests/fixtures/` (and any `output_files/` copies mirroring them) for the four new types is a **downstream human-gated step** (`DDO_FIXTURE_SIGNOFF=1`), flagged but not force-completed inside execution.

---

## 4. User Stories (Atomic)

| ID | User Story | Acceptance Criteria | Priority |
|---|---|---|---|
| US-001 | As a **new user**, I want a tutorial focused on the evidence-bank / citation-integrity workflow so that I understand how claims trace to sources. | 1. `tutorials/ddo-v006-evidence-bank-workflow/` exists with the full directory convention.<br>2. `input_files/` mirrors the M5-tested `tests/fixtures/ingest_output.yaml`.<br>3. It is framed as a citation-integrity lens, not a duplicate of the existing loop tutorial. | High |
| US-002 | As a **user**, I want to author a new document type by example so that I can model my own structures. | 1. `tutorials/ddo-v006-authoring-custom-structures/` walks `blog_post` from scratch.<br>2. The other three types appear as worked examples.<br>3. `input_files/` copies are byte-identical to the `tests/data/` sources. | High |
| US-003 | As a **user**, I want a tutorial on writing structured personas so that I can build my own review lens. | 1. `tutorials/ddo-v006-writing-structured-personas/` uses the v0.0.4 AV-table format.<br>2. It drives `ddo-create-persona`.<br>3. It cites the four new personas as specimens. | High |
| US-004 | As a **user**, I want four new document types that render deterministically so that they are trustworthy examples. | 1. Each type has a schema + 3 templates + example YAML.<br>2. Each is in `EXAMPLES`.<br>3. `uv run pytest tests/integration/` passes M1/M2/M3/M3b for all four. | High |
| US-005 | As a **user**, I want each new type to ship a dedicated persona and style so that I have complete worked examples of both v0.0.4 and v0.0.5 features. | 1. 4 personas pass `test_personas.py`.<br>2. 4 styles pass `test_styles.py`.<br>3. Each schema's `meta.persona`/`meta.style_profile` resolve to the new files. | High |
| US-006 | As a **maintainer**, I want tutorials guarded against fixture rot so that renamed or drifted fixtures fail CI loudly. | 1. A unit test enumerates tutorial-referenced paths and fails if any is missing.<br>2. It asserts each tutorial `input_files/*.yaml` mirroring a `tests/data/` fixture is byte-identical.<br>3. It runs in the default `pytest` suite. | Medium |
| US-007 | As a **contributor**, I want lint + tests green so that v0.0.6 meets the repo's merge bar. | 1. `uv run ruff check .` exits 0.<br>2. `uv run ruff format --check .` exits 0.<br>3. `uv run pytest` passes. | High |

---

## 5. Technical Specifications

### Architecture & Resolved Trade-offs

- **Tutorials live in the existing top-level `tutorials/` tree** (this matches both the user's directive and the pre-existing convention; the plan's `docs/tutorials/` suggestion is not used). Each new tutorial is a **directory** `tutorials/ddo-v006-<slug>/` mirroring the shipped `ddo-v001-prd-workflow/` and `ddo-adversarial-loop-v0.0.2/` layout — not a flat single file. *(Correction from the earlier draft, which assumed a greenfield directory of flat Markdown files.)*
- **Each `tutorial.md` is plain hand-authored Markdown, not DDO-rendered.** Validated by the existing convention — tutorials are meta-documentation *about* the pipeline. *(Trade-off: no dogfooding — accepted; the pipeline is dogfooded by the four example docs and the `output_files/` renders.)*
- **Anchoring is by fixture-copy + byte-equality guard.** The established convention copies a regression fixture into a tutorial's `input_files/` (e.g. `ddo-v001-prd-workflow/input_files/prd_example.yaml` == `tests/data/prd_example.yaml`). v0.0.6 keeps this and adds `test_tutorial_refs.py` to assert byte-equality so the copies cannot silently drift. *(Trade-off: fixtures are duplicated on disk — accepted, matching convention, now guarded.)*
- **Every new type supports all three formats.** Preserves the determinism harness as a clean `EXAMPLES × ["pdf","html","md"]` cross-product. *(Trade-off: 12 templates — accepted for uniformity + testability.)*
- **Full 1:1 worked-example symmetry:** each doc type ships its own persona *and* its own style. *(Trade-off: +4 personas, +4 styles vs. reuse — accepted for teaching value per user direction; structurally CI-validated.)*
- **Cognitive-only consistency, unchanged.** New personas inject AV taxonomy into Red Team; new styles inject phrasing-only guidance into ingest/interview — both already governed as untrusted, scoped input. No new enforcement code.
- **Verification by-reference, not by-execution.** Only the deterministic `build.py` render commands are CI-covered (via `EXAMPLES`); the interactive/human-gated loop and persona-authoring steps stay walkthrough prose. Pedagogical quality is a one-time HITL walkthrough (Candidate Artifact), and tutorials remain auditable via `/hyper-tutorial-audit` (see the shipped `audit_*.md` files). *(Trade-off: executable-doc testing rejected as brittle.)*

### System Graph Blast Radius (`architecture.yml`)

**New nodes:**
- `tutorials` — `Module`, `associated_file: tutorials/` — implements `ddo_system`. Registers the existing tree (2 shipped tutorials) plus the 3 new ones.
- `test_tutorial_refs_unit` — `Atomic`, `associated_file: tests/unit/test_tutorial_refs.py` — implements `tests_unit`; depends_on `tutorials`.

**Existing nodes → `needs_review`:**
- `ddo_schemas` (+4 schemas), `ddo_templates` (+12 templates), `ddo_personas` (+4 personas), `ddo_styles` (+4 styles).
- `render_fixture` (conftest `EXAMPLES`), `test_render_determinism` (`EXAMPLES`), `tests_unit` (new test file), `tests_integration` (widened coverage).
- `ddo_system` description updated to note v0.0.6 ecosystem expansion + `tutorials` registration.

### Execution Checklist (proposed MiniPRDs — final split decided at `/hyper-resolve`)

Ordered by dependency (personas/styles → schemas/templates → tutorials → guard/registration):

1. **MiniPRD — New Personas** (`content_editor`, `meeting_recorder`, `meeting_facilitator`, `project_stakeholder`), AV-table format.
2. **MiniPRD — New Styles** (`blog_casual`, `notes_concise`, `agenda_directive`, `executive_formal`), five-section format.
3. **MiniPRD — New Document Types** (4 schemas + 12 templates + 4 `tests/data/` example YAMLs + `EXAMPLES` enrollment). *Flag: may split per-type if over 50k-token budget.*
4. **MiniPRD — Tutorial 1 dir** (`ddo-v006-evidence-bank-workflow/`): citation-integrity lens on the existing `ingest_output.yaml`.
5. **MiniPRD — Tutorial 2 dir** (`ddo-v006-authoring-custom-structures/`): four new types; `blog_post` from scratch.
6. **MiniPRD — Tutorial 3 dir** (`ddo-v006-writing-structured-personas/`): persona authoring via `ddo-create-persona`.
7. **MiniPRD — Anti-Rot Guard + Hypergraph** (`tests/unit/test_tutorial_refs.py` byte-equality/path guard) + register the `tutorials` node.

### API Contracts / Schema (proposed section shapes — for Red Team review)

All four schemas satisfy the **unchanged** DDO minimal contract: a `meta` block (`doc_type`, `title`, `version`, `date`, `authors`, `status`, `persona`, `style_profile`, `output_formats`, `template`, `review_log`) + `content.sections[*]` (`id`, `title`, `body`, `claims`, `evidence`) + an `evidence_bank` array.

- **`blog_post`** — persona `content_editor`, style `blog_casual`. Sections: `hook`, `context`, `main_point`, `supporting_detail`, `conclusion_cta`.
- **`meeting_notes`** — persona `meeting_recorder`, style `notes_concise`. Sections: `attendees`, `agenda_covered`, `decisions`, `action_items`, `next_steps`.
- **`meeting_agenda`** — persona `meeting_facilitator`, style `agenda_directive`. Sections: `meeting_objective`, `agenda_items` (time-boxed, owner-attributed), `pre_reads`, `logistics`.
- **`project_report`** — persona `project_stakeholder`, style `executive_formal`. Sections: `executive_summary`, `status`, `milestones`, `risks`, `metrics`, `next_steps`.

### Dependencies
- No new libraries. Uses existing `uv` / PEP 723 hermetic build, `typst`, `jinja2`, `pytest`, `ruff`, `pyyaml`.
- **Hard dependency:** v0.0.4 (AV-table persona format + `ddo-create-persona`) and v0.0.5 (styles + `ddo-create-style`) — both landed.
- **Convention dependency:** the shipped tutorial directory layout (`ddo-v001-prd-workflow/`, `ddo-adversarial-loop-v0.0.2/`) is the template for the three new tutorial directories.

---

## 6. Negative Constraints

- **DO NOT** modify any `ddo/*.py` module — v0.0.6 is domain files + docs + tests only.
- **DO NOT** change the DDO minimal contract (`meta` + `evidence_bank`) or add per-type validation.
- **DO NOT** invent a new tutorial layout — new tutorials MUST follow the existing `tutorials/<name>/{tutorial.md,input_files,output_files,code_samples,screenshots}` convention.
- **DO NOT** let a tutorial `input_files/*.yaml` drift from its `tests/data/` source — keep them byte-identical (guarded by `test_tutorial_refs.py`).
- **DO NOT** rewrite or restructure the two existing shipped tutorials.
- **DO NOT** duplicate the existing `ddo-adversarial-loop-v0.0.2` tutorial — Tutorial 1 is an evidence/citation-integrity lens, not a second loop walkthrough.
- **DO NOT** give any new type a partial format set — all four support `pdf`/`html`/`md`.
- **DO NOT** fabricate or hand-promote golden baselines into `tests/fixtures/` (or `output_files/` copies mirroring them) — promotion is human-gated via `DDO_FIXTURE_SIGNOFF=1`.
- **DO NOT** author `tests/fixtures/ingest_output.yaml` or `tests/fixtures/loop/*` — Tutorial 1 references the existing human-promoted fixtures only.
- **DO NOT** embed content-bearing/quantitative imperatives in the new style files (v0.0.5 rejection rubric); styles are phrasing/register-only.
- **DO NOT** build an executable-doc test framework that parses/runs tutorial command blocks.
- **DO NOT** add a new skill; reuse the existing seven.

---

## 7. Risks & Mitigation

- **Risk:** MiniPRD #3 (four doc types) exceeds the 50k output-token budget. → **Mitigation:** split per-document-type at `/hyper-resolve`; each type is independently renderable/testable.
- **Risk:** A new type's example YAML fails determinism. → **Mitigation:** model templates on the proven `prd`/`scientific_report` templates; M2/M3 catch non-determinism in CI before promotion.
- **Risk:** Tutorial `input_files/` copies drift from their `tests/data/` sources (duplication hazard baked into the convention). → **Mitigation:** `test_tutorial_refs.py` byte-equality assertion fails CI on drift.
- **Risk:** Tutorial 1 is perceived as redundant with the existing loop tutorial. → **Mitigation:** scope it explicitly to evidence referencing / citation integrity; cross-link, don't re-walk the loop.
- **Risk:** Tutorial 1 over-promises automation of the human-gated/interactive loop. → **Mitigation:** frame loop steps as walkthrough prose; only deterministic render commands are presented as CI-covered.
- **Risk:** New persona/style prose is structurally valid but pedagogically weak. → **Mitigation:** quality is HITL-reviewed at authoring (Candidate Artifact sign-off); CI enforces structure only.
- **Risk:** New styles smuggle content directives, violating the v0.0.5 contract. → **Mitigation:** apply the `ddo-create-style` rejection rubric during authoring; `test_styles.py` enforces structure + sentinel-absence.

---

## 8. Success Metrics

- `tutorials/` gains three new convention-conformant tutorial directories; every fixture/data path they reference exists and every `input_files/` copy is byte-identical to its source (guard test green).
- Four new document types each render `pdf`/`html`/`md` with exit 0 and pass M1/M2/M3/M3b determinism.
- `test_personas.py` and `test_styles.py` pass with the four new personas and four new styles auto-discovered.
- `uv run ruff check .` and `uv run ruff format --check .` both exit 0; `uv run pytest` passes.
- The `tutorials` node is registered and all affected `architecture.yml` nodes reconcile to `clean` after `/hyper-audit`.
- A newcomer can follow Tutorial 1 end-to-end and produce a rendered, evidence-linked document (HITL-verified).
