# Process Document: DDO v0.0.6 Architect Interview (Expanded Ecosystem Tutorials)

**Generated:** 2026-07-01T11:29:48-07:00
**Session Focus:** HACF Phase 1 (`/hyper-architect`) — extract requirements for DDO v0.0.6 (Expanded Ecosystem Tutorials) and produce a Draft PRD.

## Problem Statement

DDO had shipped through v0.0.5 but remained unapproachable to newcomers and demonstrated only two formal document types (`prd`, `scientific_report`). The v0.0.6 slice of the Living Master Plan calls for user-facing tutorials plus an ecosystem expansion (new document types). This session ran the architect interview to convert that plan slice into a structured Draft PRD ready for adversarial review.

## Starting State

- Git `HEAD` at `6f36c47` (v0.0.5 released).
- `spec/compiled/architecture.yml` fully `clean` (35 nodes); v0.0.4 (structured persona nomenclature + `ddo-create-persona`) and v0.0.5 (style profiles + `ddo-create-style`) both landed and audited.
- Existing domain surface: 2 doc types (schema + 3 templates each), 7 skills, 3 styles, 2 personas, unit + integration suites (216 tests, 2 human-gated skips).
- `spec/active/` empty except `.gitkeep`.
- Source plan: `PRDs/LivingMasterPlan_v0.0.4-v0.0.6.md` (v0.0.6 section, open questions, confirmed decisions D1–D8).
- **Pre-existing but overlooked:** a git-tracked top-level `tutorials/` directory already contained two tutorials (`ddo-v001-prd-workflow/`, `ddo-adversarial-loop-v0.0.2/`) using a per-tutorial directory convention. This was NOT surfaced during the interview (see Patterns & Lessons).

## Approach & Methodology

Spec-driven, single HACF phase: `/hyper-architect`. Followed the skill's five-phase state machine (Core Mutation → Data/Boundaries/Blast Radius → Personas/Permissions → Novel Frontier → Draft Generation), asking one question per turn with an explicit recommended default, and reading the codebase before asking anything derivable from it. Because `architecture.yml` was populated, the session ran in Iterative mode — every question framed against how v0.0.6 collides with the existing system graph.

## Steps Taken

1. Read `.agents/skills/hyper-architect/SKILL.md` to load the phase rules (one-question-at-a-time, codebase-first, decision-tree traversal).
2. Read the v0.0.6 section of `PRDs/LivingMasterPlan_v0.0.4-v0.0.6.md` — captured the three-tutorial scope, D8 (four new doc types), and open question #2 (tutorial location).
3. Explored the codebase: read `architecture.yml` (35 clean nodes), listed `ddo/schemas|templates|personas|styles|skills`, `tests/fixtures`, and checked for a `docs/` dir (absent). Confirmed the template/schema-pair pattern and the parametrized `EXAMPLES` determinism harness in `tests/integration/conftest.py` + `test_render_determinism.py`. **Gap: did not check for an existing `tutorials/` dir.**
4. Ran Phase 1 (Core Mutation): proposed the framing "tutorials are the deliverable; four new tested doc types are supporting fixtures + ecosystem expansion." User accepted verbatim.
5. Ran Phase 2 (Data/Boundaries/Blast Radius) across several one-question turns:
   - Tutorial location → user chose **top-level `tutorials/`** (overriding the plan's `docs/tutorials/` suggestion).
   - Regression depth → four new types become full regression citizens via `tests/data/` example YAMLs + `EXAMPLES` enrollment (M1/M2/M3/M3b); golden baselines deferred to human sign-off.
   - Formats → all three (`pdf`/`html`/`md`) per type → 12 templates, clean cross-product harness.
   - Persona/style assignment → user chose to **author new dedicated personas AND styles** (full 1:1 worked-example symmetry) rather than reuse existing.
   - Tutorial file shape → **plain hand-authored Markdown** (not dogfooded through the pipeline).
6. Ran Phase 3 (Personas/Permissions): concluded no new actors and no new permission model; only the existing `DDO_FIXTURE_SIGNOFF` gate applies. Confirmed advance via AskUserQuestion.
7. Ran Phase 4 (Novel Frontier): classified outputs; chose **by-reference anchoring + HITL walkthrough + a cheap `test_tutorial_refs.py` path-existence guard** over a full executable-doc framework.
8. Ran Phase 5 (Draft Generation): read the SuperPRD schema from `AGENTS.md`, wrote `spec/active/Draft_PRD.md` (confidence 8/10, four clarifying questions logged for Red Team).
9. Recorded status in project memory (`project_ddo_v006.md` + `MEMORY.md` index).

## Key Decisions & Rationale

| Decision | Alternatives Considered | Reason Chosen |
|---|---|---|
| Tutorials in top-level `tutorials/` | `docs/tutorials/` (plan default); `Documents/tutorials/` | User directive; version-controlled + diff-reviewable; `Documents/` is gitignored |
| Plain hand-authored Markdown tutorials | Dogfooded as rendered DDO documents | Meta-docs about the pipeline; schema/evidence-bank contract adds friction with no teaching benefit |
| 4 new doc types, all 3 formats each (12 templates) | Per-type format subsets | Keeps determinism harness a clean `EXAMPLES × formats` cross-product; no special-casing |
| Full regression enrollment via `EXAMPLES` | Lighter "renders exit 0" smoke check | Nearly free (one tuple + one YAML); prevents silent divergence per plan intent |
| Dedicated new persona AND style per type (4+4) | Reuse existing personas/styles | User chose teaching value / full worked-example symmetry |
| By-reference anchoring + path guard | No guard; full executable-doc testing | Loop/persona-authoring steps aren't automatable; executable-doc parsing is brittle |
| No Python / no schema-contract / no new skills | Schema surgery, new validation | v0.0.6 is domain files + docs + tests; minimal contract unchanged |

## Artifacts Created / Modified

| Artifact | Path | Change |
|---|---|---|
| Draft PRD | `spec/active/Draft_PRD.md` | created |
| v0.0.6 status memory | `~/.claude/.../memory/project_ddo_v006.md` | created |
| Memory index | `~/.claude/.../memory/MEMORY.md` | updated (v0.0.6 line) |
| This process document | `spec/process/process_20260701_112948_ddo-v006-architect-interview.md` | created |

## Results & Outcomes

A complete Draft PRD for v0.0.6 exists at `spec/active/Draft_PRD.md`, structured per the SuperPRD schema: framing, confidence mandate (8/10 + 4 clarifying questions), in/out-of-scope, 7 atomic user stories, technical specs (trade-offs, blast radius, proposed 7-MiniPRD execution checklist, per-schema section shapes), negative constraints, risks, and success metrics. The document is ready to hand to `/hyper-redteam`.

**Defect discovered post-session and reconciled during this process-document session:** the initial Draft PRD framed `tutorials/` as a brand-new directory and assumed tutorials are flat single Markdown files. In reality `tutorials/` already exists (git-tracked) with an established per-tutorial *directory* convention (`tutorial.md` + `input_files/` + `output_files/` + `code_samples/` + `screenshots/`), two tutorials already ship there (`ddo-v001-prd-workflow/`, `ddo-adversarial-loop-v0.0.2/`), and the "anchoring" mechanism is a byte-identical fixture copy into `input_files/` (verified: `ddo-v001-prd-workflow/input_files/prd_example.yaml` == `tests/data/prd_example.yaml`). `spec/active/Draft_PRD.md` was then corrected to: (a) treat `tutorials/` as existing; (b) make each new tutorial a convention-conformant directory named `ddo-v006-<slug>`; (c) upgrade the anti-rot guard from "referenced paths exist" to a byte-equality assertion between `input_files/` copies and their `tests/data/` sources; (d) reposition Tutorial 1 as an evidence/citation-integrity lens distinct from the existing loop tutorial. The `tutorials` node is genuinely new to `architecture.yml` (registration will also bring the two shipped tutorials under graph tracking).

## How to Reproduce

Prerequisite: repo at a v0.0.5-equivalent state (git `HEAD` ≈ `6f36c47`), `architecture.yml` clean, `uv` toolchain available.

1. Start a fresh conversation. Invoke `/hyper-architect` with the v0.0.6 plan reference (`@PRDs/LivingMasterPlan_v0.0.4-v0.0.6.md`).
2. The skill reads its SKILL.md and runs the five-phase interview. Answer one question per turn. Expected: recommended defaults offered at each step.
3. Before Phase 2 answers, **independently verify the actual state of `tutorials/`** (`ls tutorials/`, `git ls-files tutorials/`) — do not assume it is new.
4. On Phase 5, the skill writes `spec/active/Draft_PRD.md`. Expected artifact: a SuperPRD-schema Draft PRD.
5. Record status in memory. Then, in a new conversation, run `/hyper-redteam` on the Draft PRD.

Gotcha / order-dependency: the interview is codebase-first — its accuracy depends entirely on the codebase survey in Phase 2. An incomplete survey (e.g. checking `docs/` but not `tutorials/`) silently produces an inaccurate Draft PRD that only surfaces later.

## Patterns & Lessons

- **Codebase-first must be exhaustive on the exact directory a decision targets.** The interview asked "where should tutorials live?" and resolved to `tutorials/` without ever running `ls tutorials/`. Because a sibling check (`docs/` absent) was run and reported, the absence-framing felt authoritative. Lesson: when a decision names a concrete path, stat that path directly before asserting it is new — don't infer novelty from a neighbor's absence.
- **Existing conventions outrank plan defaults.** The user's "top-level `tutorials/`" choice happened to match the pre-existing convention, but the Draft PRD still described it as greenfield. Discovering an established directory layout should retro-feed the design (tutorial-as-directory, not tutorial-as-flat-file).
- **The `EXAMPLES` list is the single lever for regression enrollment** — adding a `(template, basename)` tuple to both `conftest.py` and `test_render_determinism.py` auto-confers M1/M2/M3/M3b. Cheap, high-leverage; worth stating explicitly in any doc-type MiniPRD.
- **Glob-based validators (`test_personas.py`, `test_styles.py`) auto-cover new files** — new personas/styles need no test wiring, only format conformance.
- **Retrospective process docs catch architect-phase blind spots** — this defect (existing `tutorials/`) was found only while gathering context for this document, before it reached Red Team. Running `/hyper-process-document` after an architect session is a useful cheap audit.
