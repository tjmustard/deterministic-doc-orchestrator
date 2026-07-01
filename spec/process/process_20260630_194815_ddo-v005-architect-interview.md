# Process Document: DDO v0.0.5 — Architect Interview (Style and Tone Configuration)

**Generated:** 2026-06-30T19:48:15 (local) / 2026-07-01T02:48:15Z
**Session Focus:** Run `/hyper-architect` (HACF Phase 1) for DDO v0.0.5 — Style and Tone
Configuration — sourcing scope from `PRDs/LivingMasterPlan_v0.0.4-v0.0.6.md`, producing a
Draft PRD ready for Red Team.

## Problem Statement

DDO document authors have no way to control the *register* (tone, voice, formality) of
AI-generated prose. A casual blog post and a formal enterprise PRD read identically, and
register can drift between runs and even between the Ingest and Interview phases of a single
document. v0.0.5 was pre-scoped in the Living Master Plan to add reusable "style profiles,"
but several design questions were still open (Q4 injection mechanics, Q7 create-style scope)
and the plan's proposed injection sites had not been checked against the actual code.

## Starting State

- Git `HEAD` at `a9172f0` (v0.0.4). Working tree clean.
- v0.0.4 (Structured Persona Nomenclature + `ddo-create-persona`) complete and audited; 183
  tests passing; all 26 hypergraph nodes `clean` (`spec/compiled/architecture.yml`).
- The persona machinery that v0.0.5 mirrors already existed: `ddo/personas/*.md` with AV-NN
  tables, `ddo/skills/ddo-create-persona.md` (interactive Q&A skill), and
  `tests/unit/test_personas.py` (glob-based structural validator).
- **No `ddo/styles/` directory existed** — greenfield for this feature.
- `spec/active/` was empty (only `.gitkeep`) — no prior Draft PRD in flight.
- Design intent captured in `PRDs/LivingMasterPlan_v0.0.4-v0.0.6.md` (D1–D8 locked; open
  questions Q4, Q7; injection sites listed as `ddo-ingest` + `ddo-refine`).

## Approach & Methodology

Spec-driven, single HACF phase: `/hyper-architect`. The skill mandates a codebase-first,
one-question-at-a-time adversarial interview with a recommended default on every turn. Because
`architecture.yml` was populated and clean, the session ran in **Iterative** mode — every
question was framed against how v0.0.5 collides with the existing system graph. The sequencing
followed the skill's state machine (Phase 1 Core Mutation → Phase 2 Boundaries/Blast Radius →
Phase 3 Personas/Permissions → Phase 4 Novel Frontier → Phase 5 Draft Generation), with the
plan's two open questions folded in before generation.

## Steps Taken

1. **Oriented on the planning corpus.** Listed `PRDs/` at the user's request; identified
   `LivingMasterPlan_v0.0.4-v0.0.6.md` as the v0.0.5 source of scope. Read it in full.
2. **Invoked `/hyper-architect`** with argument `v0.0.5 in PRDs/LivingMasterPlan_v0.0.4-v0.0.6.md`;
   read `.agents/skills/hyper-architect/SKILL.md` to load the interview protocol.
3. **Codebase-first exploration (before asking anything).** Read `spec/compiled/architecture.yml`
   (26 nodes, all `clean` → confirmed Iterative state), surveyed the `ddo/` tree (confirmed
   `ddo/styles/` absent), and read the five files v0.0.5 collides with: `ddo/skills/ddo-ingest.md`,
   `ddo/skills/ddo-refine.md`, `ddo/skills/ddo-create-persona.md`, `ddo/personas/product_critic.md`,
   `ddo/schemas/prd.yaml`.
   **Key discovery:** `ddo-refine` is purely *mechanical* — it applies pre-authored patch
   `value`s via `apply_patches` and never composes prose. This contradicts the Living Master
   Plan, which named `ddo-refine` as a style-injection site. The prose-authoring step in the
   loop is actually `ddo-interview`.
4. **Phase 1 — Core Mutation.** Proposed and confirmed the foundational invariant: **style
   governs phrasing/register only, never content** (protects the zero-hallucination/traceability
   guarantee; a careless profile must not smuggle in unsourced content). Accepted.
5. **Phase 2 — Boundaries & Blast Radius (four one-at-a-time decisions).**
   a. **Injection sites corrected** from `ingest + refine` to **`ingest + interview`**;
      `ddo-refine` explicitly excluded (mechanical). Modified nodes: `ddo_skills` + `skill_interview`.
   b. **Style file contract** = test-enforced *heading* structure, free-prose *bodies*; five
      required sections (`Register & Audience`, `Voice & Person`, `Sentence & Structure`,
      `Diction`, `Avoid`). Splits the difference between rigid persona AV-tables and unstructured prose.
   c. **Missing-file behavior** = cognitive hard-fail (name file, list available); absent field
      = clean no-op; no Python change (`style_profile` is render-invisible).
   d. **Schema field** `meta.style_profile` after `persona`; filename stem → `ddo/styles/<stem>.md`;
      **live per-doc-type defaults** (`formal_professional` for PRD, `technical_precise` for
      scientific_report).
6. **Phase 3 — Personas & Permissions.** Single genuine security boundary: path traversal via
   a crafted `meta.style_profile`. Confirmed a cognitive **stem-validation gate**
   `^[a-z][a-z0-9_]*$` before any Read, in both injection skills and `ddo-create-style`; scoped
   to `style_profile` (parallel `meta.persona` gap deferred to a separate future issue).
7. **Phase 4 — Novel Frontier.** Confirmed **no Candidate Artifact / fixture routing**: style
   quality is subjective and HITL-governed; built-in profiles are first-class tested-source
   (`test_styles.py`), not fixtures; and because `style_profile` is render-invisible, there is
   **zero regression-fixture churn** (`tests/fixtures/ingest_output.yaml` needs no re-promotion).
8. **Resolved the plan's two open questions.** Q7 → `ddo-create-style` is an **interactive paced
   Q&A** mirroring `ddo-create-persona` (not one-pass). Q4 → **up-front governing-constraint
   injection** + a pre-write checklist re-affirming style adherence and the phrasing-only invariant.
9. **Phase 5 — Draft Generation.** Read the SuperPRD schema in `AGENTS.md`, then wrote
   `spec/active/Draft_PRD.md` (SuperPRD-shaped: goals, confidence 8/10 + clarifying questions,
   scope, 7 user stories, technical spec + blast radius, negative constraints, risks, success
   metrics, a 9-row decision log A1–A9, and a 6-item MiniPRD execution checklist).
10. **Recorded status in memory.** Created `project_ddo_v005.md` and added its index line to
    `MEMORY.md`.

## Key Decisions & Rationale

| Decision | Alternatives Considered | Reason Chosen |
|---|---|---|
| Style governs phrasing/register only, never content (first-class invariant) | Let style profiles carry framing/narrative directives | Protects zero-hallucination; keeps the sentinel/evidence gate the sole authority on *what* the document says |
| Inject at `ddo-ingest` + `ddo-interview`; exclude `ddo-refine` | Follow the plan literally (`ingest` + `refine`) | Codebase shows `ddo-refine` is mechanical (`apply_patches`) and authors no prose; the loop's revision prose is composed in `ddo-interview` |
| Style file: test-enforced headings, free-prose bodies (5 sections) | Rigid machine-parsed rules (like persona AV-tables); or pure unstructured prose | Gives `test_styles.py` a real contract without machine-parsing prose (honors D4); keeps `create-style` output predictable |
| Referenced-but-missing profile → cognitive hard-fail; absent → no-op | Silently no-op a bad reference | Silent-wrong-output (unstyled prose from a typo) is worse than halting; mirrors `ddo-red-team` persona resolution |
| Live per-doc-type schema defaults (`formal_professional` / `technical_precise`) | Ship the field absent/commented (opt-in) | Shipped profiles guarantee resolution; new docs get value out of the box; legacy YAML still no-ops (D5) |
| Stem-validation gate `^[a-z][a-z0-9_]*$`, scoped to `style_profile` | Add `ddo_core` path containment; or fix `meta.persona` too | `ddo/` tree has no containment; cognitive gate matches the no-`ddo_core` constraint; widening scope to persona deferred |
| No Candidate Artifact routing; profiles are tested-source | Promote profiles/prose to `tests/fixtures/` | Style-bounded prose is subjective/non-fixturable; `style_profile` is render-invisible so baselines are untouched → zero fixture churn |
| `ddo-create-style` = interactive Q&A (mirror `ddo-create-persona`) | One-pass generation | Interview loop yields more complete files; reuses a battle-tested skill skeleton (D3) |
| Up-front governing-constraint injection + pre-write checklist | Trailing per-section reminder | Binds output more strongly; matches how `ddo-red-team` loads its persona lens |

## Artifacts Created / Modified

| Artifact | Path | Change |
|---|---|---|
| Draft PRD (v0.0.5) | `spec/active/Draft_PRD.md` | created (~19 KB) |
| v0.0.5 status memory | `~/.claude/.../memory/project_ddo_v005.md` | created |
| Memory index | `~/.claude/.../memory/MEMORY.md` | updated (added v0.0.5 line) |
| This process document | `spec/process/process_20260630_194815_ddo-v005-architect-interview.md` | created |

No source code, schemas, skills, tests, or `architecture.yml` were modified this session — the
architect phase produces a specification only.

## Results & Outcomes

A complete, Red-Team-ready Draft PRD for v0.0.5 exists at `spec/active/Draft_PRD.md`. It locks
nine design decisions (A1–A9), corrects the Living Master Plan's injection-site error, defines a
blast radius (new nodes `ddo_styles`, `skill_create_style`, `test_styles_unit`; `needs_review`
on `ddo_schemas`, `ddo_skills`, `skill_interview`), and proposes six candidate MiniPRDs
(MP-1..MP-6). Self-assessed confidence 8/10 with four clarifying questions surfaced for the Red
Team. Project memory reflects the new phase state.

## How to Reproduce

**Prerequisite state:** on `main` at commit `a9172f0` (v0.0.4), clean working tree, v0.0.4
landed, `spec/compiled/architecture.yml` present with all nodes `clean`, and
`PRDs/LivingMasterPlan_v0.0.4-v0.0.6.md` present.

1. In a fresh conversation, run `/hyper-architect` with argument
   `v0.0.5 in PRDs/LivingMasterPlan_v0.0.4-v0.0.6.md`.
2. The agent reads `spec/compiled/architecture.yml` and the five collision files
   (`ddo-ingest.md`, `ddo-refine.md`, `ddo-create-persona.md`, `product_critic.md`, `prd.yaml`)
   **before** asking anything. Expect it to flag that `ddo-refine` authors no prose.
3. Answer the interview one question per turn (nine decision points: Phase 1 invariant; four
   Phase 2 boundary calls; Phase 3 traversal gate; Phase 4 novel-frontier call; Q7 create-style
   scope; Q4 injection mechanics). Accept the recommended defaults to reproduce this Draft.
4. At Phase 5 the agent reads the SuperPRD schema in `AGENTS.md` and writes
   `spec/active/Draft_PRD.md`.
5. **Next (separate step, fresh context):** run `/hyper-redteam` on the Draft, then
   `/hyper-resolve` to compile the SuperPRD + MiniPRDs.

**Gotcha / order-dependency:** the Red Team must run in a *fresh* conversation so it is
firewalled from the architect's reasoning. Do not chain it into this session.

## Patterns & Lessons

- **Codebase-first caught a spec error.** Reading `ddo-refine.md` before interviewing revealed
  it is mechanical, overturning the plan's `ingest + refine` injection claim. The one-question
  protocol's "read before you ask" rule paid for itself in the first exploration pass.
- **"Mirror the persona pattern" was the load-bearing heuristic.** Styles ↔ personas,
  `ddo-create-style` ↔ `ddo-create-persona`, `test_styles.py` ↔ `test_personas.py`. Most
  decisions reduced to "do what v0.0.4 already proved."
- **Render-invisibility is the linchpin.** Because `style_profile` never reaches
  `build.py`/templates, the whole feature stays cognitive-only: no Python changes, no validation
  gate change, no fixture churn, and the missing-file check *cannot* live in `validation.py`.
  Recognizing this early kept the blast radius minimal.
- **Fold plan-flagged open questions (Q4, Q7) into the interview before Phase 5.** They are not
  "novel frontier" items, so they would otherwise be missed by a literal phase walk; resolving
  them explicitly kept the Draft complete.
