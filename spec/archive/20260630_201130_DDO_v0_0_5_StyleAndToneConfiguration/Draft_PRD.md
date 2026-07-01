# Draft PRD: DDO v0.0.5 — Style and Tone Configuration

> **Phase 1 artifact** produced by `/hyper-architect`. Feeds `/hyper-redteam` →
> `/hyper-resolve`. All decisions below were confirmed one-at-a-time during the
> architect interview (see §9 Decision Log). This documents **the DDO project**,
> not the HACF toolchain.

---

## 1. Introduction & Goals

- **Problem Statement:** DDO authors have no way to control the *register* (tone,
  voice, formality) of AI-generated prose. The Ingest and Interview phases produce
  text in whatever default voice the agent chooses, so a casual blog post and a
  formal enterprise PRD read the same, and register drifts between runs and between
  the Ingest and Interview phases of a single document. There is no version-controlled,
  reusable way to say "write this document formally" or "write this conversationally."
- **Solution Overview:** Introduce **style profiles** — version-controlled Markdown
  files in a new `ddo/styles/` directory, referenced from `document_data.yaml` via an
  optional `meta.style_profile` field. During the two prose-authoring phases
  (`ddo-ingest`, `ddo-interview`) the referenced profile is loaded up front as a
  **governing phrasing constraint** that bounds every sentence the agent writes.
  Consistency is enforced **cognitively**, not mechanically — no validation-gate
  changes, no forbidden-token scanning, no Python module changes. A new interactive
  `ddo-create-style` skill assists authoring new profiles, mirroring `ddo-create-persona`.
- **Target Audience:** DDO document authors (who set `meta.style_profile`) and style
  authors (who create reusable profiles). Single-user, local, no-network tool.

**Foundation:** v0.0.4 (Structured Persona Nomenclature + `ddo-create-persona`) has
landed and is audited. v0.0.5 mirrors that persona machinery for styles. This Draft is
scoped **strictly to v0.0.5**; v0.0.6 (tutorials) is out of scope.

---

## 2. Confidence Mandate

- **Confidence Score: 8/10.** The design was pre-shaped by the Living Master Plan
  (D1–D8 locked) and every open question was resolved in the interview. The residual
  −2 is subjective content authoring (the prose *inside* the three built-in profiles)
  and the items in §2 Clarifying Questions, which are appropriate for Red Team scrutiny.
- **Clarifying Questions (for Red Team):**
  1. The exact prose content of the three built-in profiles (`formal_professional`,
     `conversational`, `technical_precise`) is subjective and HITL-reviewed at authoring
     time — is a worked example of each sufficient, or does Red Team want acceptance
     criteria on *what each profile must contain*?
  2. `ddo-create-style` must reject "content-bearing directives" to uphold the Phase-1
     invariant. Is a **cognitive** rejection (agent judgment + a pre-write checklist item)
     acceptable, given D4 forbids machine-parseable style rules? There is no deterministic
     way to detect "this directive smuggles content."
  3. The parallel `meta.persona` path-traversal gap (identical latent risk in
     `ddo-red-team`) is deferred to a **separate future issue** rather than folded into
     v0.0.5. Confirm that scoping.
  4. Live per-doc-type schema defaults (`formal_professional` for PRD,
     `technical_precise` for scientific_report) change the out-of-box Ingest output for
     *new* documents. Confirm this is desired over a conservative absent/commented default.

---

## 3. Scope

### In-Scope
- New `ddo/styles/` directory (Module node `ddo_styles`), mirroring `ddo/personas/`.
- Three built-in profiles: `formal_professional.md`, `conversational.md`,
  `technical_precise.md`, each in the required 5-section structure.
- Optional `meta.style_profile` field added to `ddo/schemas/prd.yaml` and
  `ddo/schemas/scientific_report.yaml`, with **live per-doc-type defaults**.
- Style injection into **`ddo-ingest`** (initial section prose) and **`ddo-interview`**
  (revision / `add_evidence` prose), as an up-front governing constraint.
- New `ddo-create-style` skill (Atomic node `skill_create_style`) — interactive paced
  Q&A mirroring `ddo-create-persona`.
- New `tests/unit/test_styles.py` (Atomic node `test_styles_unit`) — glob-based
  structural validator over `ddo/styles/*.md`.
- Cognitive stem-validation gate (`^[a-z][a-z0-9_]*$`) and cognitive hard-fail on a
  referenced-but-missing profile.

### Out-of-Scope
- **No changes to `ddo-refine`** — it is mechanical (applies pre-authored patch values
  via `apply_patches`) and authors no prose. Explicitly excluded as an injection site.
- **No Python module changes** — `validation.py`, `build.py`, `review.py`, `refine.py`,
  `ingest.py`, `paths.py` are untouched. No `ddo_core` dependency in any new skill.
- **No validation-gate / render changes** — `style_profile` is render-invisible;
  templates never read it. No forbidden-token scanning (D4).
- **No YAML style schema / machine-parsed style rules** (Graveyard).
- **No retrofit of the `meta.persona` traversal gap** — separate future issue.
- **No fixture promotion** — v0.0.5 introduces zero regression-fixture churn; the
  promoted `tests/fixtures/ingest_output.yaml` needs no re-promotion.
- **v0.0.6 tutorials** and any new document types.

---

## 4. User Stories (Atomic)

| ID | User Story | Acceptance Criteria | Priority |
|----|------------|---------------------|----------|
| US-001 | As a document author, I want to set `meta.style_profile` so AI-generated prose matches a consistent register across a document. | 1. `ddo-ingest` reads `ddo/styles/<stem>.md` and bounds all authored prose to it. 2. `ddo-interview` applies the same profile when composing revision prose. 3. The profile governs phrasing only — no content is introduced. | High |
| US-002 | As a document author, when I reference a profile that does not exist, I want the skill to halt and tell me, so I never silently get unstyled prose. | 1. Skill Reads `ddo/styles/<stem>.md`; if absent, it halts. 2. The halt names the missing file and lists available `ddo/styles/*.md`. 3. No prose is authored. | High |
| US-003 | As a document author with a pre-v0.0.5 document, I want YAML without `style_profile` to behave exactly as before. | 1. Absent `meta.style_profile` → no style bounding (clean no-op). 2. Existing `Documents/` YAML and golden render baselines are unchanged. | High |
| US-004 | As a style author, I want an interactive `ddo-create-style` skill so I can author a new profile in the standard structure without hand-writing Markdown. | 1. Paced Q&A ≤2 questions/turn across the 5 sections. 2. Sentinel resolution before write. 3. Draft-preview `[WAITING FOR USER REVIEW]` gate + `APPROVE`. 4. Cognitive Read-based overwrite guard + literal-filename re-confirm. 5. Rejects content-bearing directives. | High |
| US-005 | As a maintainer, I want `test_styles.py` to enforce the structural contract on all `ddo/styles/*.md` so profiles stay consistent and `create-style` output is auto-covered. | 1. Glob over `ddo/styles/*.md`. 2. Asserts title heading + all 5 required section headings present. 3. Asserts non-empty bodies. 4. Asserts sentinel-absence. 5. Does **not** assert prose content. | High |
| US-006 | As a security-conscious maintainer, I want `style_profile` stems validated against a strict charset so a crafted value cannot read files outside `ddo/styles/`. | 1. Stem must match `^[a-z][a-z0-9_]*$` before any Read. 2. `.`, `/`, `..` are structurally rejected. 3. Validation happens in both injection skills and `ddo-create-style`, pre-resolution. | High |
| US-007 | As a document author, I want sensible register out of the box, so new documents are styled without extra steps. | 1. `prd.yaml` ships `style_profile: "formal_professional"`. 2. `scientific_report.yaml` ships `style_profile: "technical_precise"`. 3. Both referenced files exist and resolve. | Medium |

---

## 5. Technical Specifications

### Architecture & Resolved Trade-offs
- **Pattern:** Styles mirror personas one-for-one. `ddo/styles/` ↔ `ddo/personas/`;
  `ddo-create-style` ↔ `ddo-create-persona`; `test_styles.py` ↔ `test_personas.py`.
- **Injection sites corrected from the plan:** the Living Master Plan named
  `ddo-ingest` + `ddo-refine`. Codebase inspection shows `ddo-refine` is mechanical
  (applies patch `value`s via pure `apply_patches`; authors no prose). Corrected to
  `ddo-ingest` (initial prose) + `ddo-interview` (revision prose). Style consistency
  across a refine cycle is preserved because the patch `value` was composed under style
  at interview time.
- **Style file contract:** test-enforced **heading** structure, free-prose **bodies**.
  Required title `# **Style Profile: <name>**` and five `##` sections:
  `Register & Audience`, `Voice & Person`, `Sentence & Structure`, `Diction`, `Avoid`.
  Splits the difference between rigid persona AV-tables and unstructured free prose.
- **Injection mechanics:** load the profile **once, up front**, as a governing
  constraint block ("read before authoring any prose; these are phrasing constraints"),
  reinforced by a pre-write checklist item re-affirming style adherence **and** the
  phrasing-only-never-content invariant.
- **Missing-file behavior:** cognitive hard-fail (name file, list available). Absent
  field → clean no-op. No `validation.py`/`build.py` change; render is oblivious to
  `style_profile`.
- **Traversal boundary:** cognitive stem-validation `^[a-z][a-z0-9_]*$` before any Read,
  in all three skills. No `ddo_core` containment for the `ddo/` source tree exists; this
  is the cognitive equivalent.

### System Graph Blast Radius (`architecture.yml`)
**New nodes**
- `ddo_styles` — dimension `Module`, `associated_file: ddo/styles/`, `implements: [ddo_system]`.
  Holds the three built-in profiles. Mirrors `ddo_personas`.
- `skill_create_style` — dimension `Atomic`, `associated_file: ddo/skills/ddo-create-style.md`,
  `implements: [ddo_skills]`, `depends_on: [ddo_styles]`. Mirrors `skill_create_persona`
  (no `ddo_core` dependency).
- `test_styles_unit` — dimension `Atomic`, `associated_file: tests/unit/test_styles.py`,
  `implements: [tests_unit]`, `depends_on: [ddo_styles]`. Mirrors `test_personas_unit`.

**Modified nodes → `needs_review`**
- `ddo_schemas` — `meta.style_profile` added to `prd.yaml` + `scientific_report.yaml`.
- `ddo_skills` — module description updated; `ddo-ingest.md` gains style injection
  (the ingest skill has no dedicated Atomic node; it lives under this Module).
- `skill_interview` — gains style injection for revision prose.

**Explicitly NOT touched:** `skill_refine`, `refine_engine`, `review_engine`,
`validation_gate`, `build_orchestrator`, `ingest_helpers`, `path_deriver`, and all
render/determinism test nodes.

### API Contracts / Schema
- **`meta.style_profile`** — optional string, filename stem (no extension, no path),
  placed in `meta` immediately after `persona`. Resolves to `ddo/styles/<stem>.md`.
  Must match `^[a-z][a-z0-9_]*$`. Absent ⇒ no-op.
- **Shipped defaults:** `prd.yaml` → `formal_professional`; `scientific_report.yaml`
  → `technical_precise`.
- **Style file structure (contract):**
  ```markdown
  # **Style Profile: <name>**

  ## Register & Audience
  <free prose>

  ## Voice & Person
  <free prose>

  ## Sentence & Structure
  <free prose>

  ## Diction
  <free prose>

  ## Avoid
  <free prose>
  ```

### Dependencies
- No new libraries. Reuses existing skill patterns and `pytest` glob-based structural
  testing. PyYAML already present.

---

## 6. Negative Constraints

- **DO NOT** modify `ddo-refine` or any Python module (`validation.py`, `build.py`,
  `review.py`, `refine.py`, `ingest.py`, `paths.py`) — style is cognitive-only.
- **DO NOT** let a style profile introduce facts, framing claims, or narrative content;
  it governs phrasing/register **only**. The sentinel/evidence gate remains the sole
  authority on *what* the document says.
- **DO NOT** add a validation-gate change, a forbidden-token scan, or any
  machine-parsed style rule (D4 / Graveyard).
- **DO NOT** teach `build.py`/templates about `style_profile` — it is render-invisible.
- **DO NOT** give `ddo-create-style` a `ddo_core` dependency — overwrite guard is
  cognitive (Read + literal-filename re-confirm), mirroring `ddo-create-persona`.
- **DO NOT** Read a `style_profile` path before validating the stem against
  `^[a-z][a-z0-9_]*$`.
- **DO NOT** silently no-op a *referenced-but-missing* profile — hard-fail. Only an
  *absent* field is a no-op.
- **DO NOT** promote any style file to `tests/fixtures/`; built-in profiles are
  first-class version-controlled source, tested structurally by `test_styles.py`.
- **DO NOT** re-promote `tests/fixtures/ingest_output.yaml` — no fixture churn.
- **DO NOT** render the style file's required sections as anything other than the five
  `##` headings; bodies stay free prose (never machine-parsed).

---

## 7. Risks & Mitigation

- **Risk:** A style profile smuggles content ("open with a compelling hook") that has no
  evidence source, violating zero-hallucination. → **Mitigation:** Phase-1 invariant
  formalized; `ddo-create-style` rejects content-bearing directives; injection framing
  states "phrasing constraints only"; existing sentinel/evidence gate still governs content.
- **Risk:** Cognitive enforcement is not mechanically guaranteed (an agent could ignore
  the profile). → **Mitigation:** Accepted trade-off (D2/D4) — system value is
  reproducible *structure*, not AI policing; HITL gates catch drift. Up-front governing
  injection + pre-write checklist maximize adherence.
- **Risk:** Path traversal via a crafted `style_profile`. → **Mitigation:** strict
  `^[a-z][a-z0-9_]*$` stem gate before any Read, in all three skills.
- **Risk:** Typo'd profile silently drops intended register. → **Mitigation:** cognitive
  hard-fail names the file and lists available profiles.
- **Risk:** Live schema defaults surprise existing workflows. → **Mitigation:** only
  *new* ingests get the default; existing `Documents/` YAML lacks the field and no-ops;
  render/baselines unaffected.
- **Risk:** `test_styles.py` over-asserts and makes profiles brittle. → **Mitigation:**
  assert headings/non-empty/sentinels only — never prose content.

---

## 8. Success Metrics

- All three built-in profiles exist in `ddo/styles/` and pass `test_styles.py`.
- `test_styles.py` auto-covers any future profile via glob (including `create-style` output).
- `meta.style_profile` present + valid ⇒ both `ddo-ingest` and `ddo-interview` load and
  honor the profile; absent ⇒ byte-identical behavior to v0.0.4.
- A referenced-but-missing profile halts with a file-named, alternatives-listed message
  in both injection skills.
- A `style_profile` containing `/`, `.`, or `..` is rejected before any file Read.
- `ddo-create-style` produces a valid 5-section profile through paced Q&A, gated by
  `APPROVE` and the cognitive overwrite guard.
- Full suite (existing 183 tests + new `test_styles.py`) passes; `ruff check` and
  `ruff format --check` exit 0.
- No diff to any Python module; no re-promotion of `tests/fixtures/`.

---

## 9. Decision Log (Architect Interview)

| # | Decision | Rationale |
|---|----------|-----------|
| A1 | Style governs **phrasing/register only, never content** — first-class v0.0.5 invariant. | Protects zero-hallucination/traceability; keeps sentinel/evidence gate the sole content authority. |
| A2 | Injection sites = **`ddo-ingest` + `ddo-interview`**; `ddo-refine` **excluded**. | `ddo-refine` is mechanical (pure `apply_patches`); the loop's revision prose is authored in `ddo-interview`. Modified nodes: `ddo_skills` + `skill_interview`. |
| A3 | Style file = **test-enforced heading contract, free-prose bodies**; 5 sections (`Register & Audience`, `Voice & Person`, `Sentence & Structure`, `Diction`, `Avoid`). | Splits the difference between rigid persona AV-tables and unstructured prose; gives `test_styles.py` a real contract without machine-parsing prose (D4). |
| A4 | Referenced-but-missing profile ⇒ **cognitive hard-fail** (name file, list available); absent ⇒ no-op; no Python change. | Silent-wrong-output is worse than halting; mirrors `ddo-red-team` persona resolution; `style_profile` is render-invisible so no `validation.py` change is possible/needed. |
| A5 | `meta.style_profile` after `persona`; stem→`ddo/styles/<stem>.md`; **live per-doc-type defaults** (`formal_professional` / `technical_precise`). | Persona/style pairing = critique vs generation register; shipped profiles guarantee resolution; new docs get value out of the box; legacy YAML still no-ops (D5). |
| A6 | **Stem-validation gate `^[a-z][a-z0-9_]*$`** pre-resolution in both injection skills + `ddo-create-style`; scoped to `style_profile`; parallel `meta.persona` gap deferred to a separate issue. | Cognitive traversal boundary for the un-contained `ddo/` tree; avoids widening v0.0.5 scope. |
| A7 | **No Candidate Artifact routing**; style quality is HITL-governed; built-in profiles are tested-source (`test_styles.py`), not fixtures; **zero fixture churn**. | Style-bounded prose is subjective/non-fixturable; `style_profile` is render-invisible so baselines and `ingest_output.yaml` are untouched. |
| A8 | `ddo-create-style` = **interactive paced Q&A mirroring `ddo-create-persona`** (slug → batched ≤2/turn → sentinel resolution → draft preview HITL → cognitive overwrite guard → Write). | Interview loop yields more complete files than one-pass; reuses a battle-tested skill skeleton (D3). |
| A9 | **Up-front governing-constraint injection** + pre-write checklist re-affirmation (style adherence + phrasing-only invariant). | Binds output more strongly than a trailing hint; matches how `ddo-red-team` loads its persona lens; keeps both injection skills identical. |

---

## 10. Execution Checklist (candidate MiniPRDs for `/hyper-resolve`)

- [ ] **MP-1 `ddo_styles`** — create `ddo/styles/`; author `formal_professional.md`,
      `conversational.md`, `technical_precise.md` in the 5-section structure.
- [ ] **MP-2 `ddo_schemas`** — add optional `meta.style_profile` (after `persona`) to
      `prd.yaml` + `scientific_report.yaml` with live per-doc-type defaults.
- [ ] **MP-3 injection** — update `ddo-ingest.md` and `ddo-interview.md`: stem
      validation, missing-file hard-fail, up-front governing injection, pre-write checklist.
- [ ] **MP-4 `skill_create_style`** — author `ddo/skills/ddo-create-style.md` mirroring
      `ddo-create-persona` (incl. content-bearing-directive rejection).
- [ ] **MP-5 `test_styles_unit`** — author `tests/unit/test_styles.py` (glob structural validator).
- [ ] **MP-6 hypergraph** — add 3 new nodes; mark `ddo_schemas`, `ddo_skills`,
      `skill_interview` `needs_review`; run `hypergraph_updater.py`.

---

**[WAITING FOR USER REVIEW]**
