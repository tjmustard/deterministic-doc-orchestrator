# Living Master Plan — DDO v0.0.4 / v0.0.5 / v0.0.6

**Session date:** 2026-06-29
**Foundation:** v0.0.2 adversarial loop shipped and audited (158 tests, all clean).
**Scope:** Three sequential feature versions, all post-v0.0.3.
**Research method:** First Principles — broad sweep → challenge assumptions → narrow design.

---

## Project Objectives

1. **v0.0.4 — Structured Persona Nomenclature:** Standardize attack vector vocabulary in persona Markdown files so the Red Team produces consistent, referenceable finding categories across runs. Add `ddo-create-persona` to make persona authoring assisted and repeatable.
2. **v0.0.5 — Style and Tone Configuration:** Give document authors a way to configure the AI's writing register via Markdown style profile files, injected cognitively into generation and refinement phases. Add `ddo-create-style` skill for profile authoring.
3. **v0.0.6 — Expanded Ecosystem Tutorials:** Anchor three golden-path tutorials to the existing regression fixture suite, covering the core DDO workflows and the new capabilities introduced in v0.0.4 and v0.0.5.

---

## Current Hypotheses & Architecture

### v0.0.4 — Structured Persona Nomenclature

**Design (confirmed):**

The existing persona Markdown files (`ddo/personas/product_critic.md`, `scientific_reviewer.md`) already have an "Attack Vectors" section written as numbered prose. In v0.0.4, this section is restructured to a standardized table format with explicit IDs:

```markdown
## Attack Vectors

| ID    | Name                          | When to apply                                      |
|-------|-------------------------------|-----------------------------------------------------|
| AV-01 | missing_acceptance_criteria   | PRD lacks testable success criteria                 |
| AV-02 | scope_ambiguity               | Feature boundaries are undefined or open-ended      |
| AV-03 | unvalidated_assumptions       | Claims made without cited evidence                  |
```

The `ddo-red-team` skill is updated to read and inject this table and explicitly instruct the AI to use the exact `ID` and `Name` from the persona's list when writing each finding's `category`.

**No Python module changes.** No `ddo.review` or `ddo.validation` changes. No YAML schema migration. The validation contract for `red_team_report_vN.yaml` is unchanged — `category` remains a free-text string. Consistency is enforced cognitively, not mechanically. This is the same tradeoff accepted for style injection (v0.0.5).

**New skill:** `ddo-create-persona` — assists users in authoring a new persona Markdown file from scratch: domain definition, attack vector table, severity taxonomy, format rules, interview question templates. Output is a `.md` file in `ddo/personas/`.

### v0.0.5 — Style and Tone

**Design (confirmed):**

Style profiles are Markdown files in a new `ddo/styles/` directory — same pattern as personas. Users can hand-edit them or use `ddo-create-style`. Reference in `document_data.yaml` via `meta.style_profile: formal_professional` (filename stem, no extension).

The `ddo-ingest` and `ddo-refine` skills read the referenced style profile and inject it as contextual bounding for all AI-generated prose. Pure cognitive injection — no forbidden-token scanning, no validation gate changes.

DDO ships built-in profiles:
- `formal_professional` — standard business/enterprise documents
- `conversational` — accessible, first-person, shorter sentences
- `technical_precise` — dense, passive voice acceptable, precision over readability

**No Python module changes.** `meta.style_profile` is an optional field; if absent, the existing behavior (no style bounding) is preserved.

**New skill:** `ddo-create-style` — assists users in defining a new style profile: tone, register, voice, sentence length preferences, things to avoid (prose description, not machine-parsed).

### v0.0.6 — Expanded Ecosystem Tutorials

**Design (confirmed direction, Tutorial 2 document type TBD):**

Three tutorial documents, co-located in `docs/tutorials/` (or `Documents/tutorials/` — TBD). Each tutorial is anchored to fixtures in `tests/fixtures/` so tutorial examples cannot silently diverge from the regression suite.

- **Tutorial 1 — Evidence Bank Workflow:** Uses the existing `tests/fixtures/ingest_output.yaml` golden baseline. Walks through the full Ingest → Red Team → Interview → Refine cycle with focus on evidence referencing and citation integrity.
- **Tutorial 2 — Authoring Custom Structures:** Introduces four new schema + template pairs: `blog_post`, `meeting_notes` (synopsis), `meeting_agenda`, `project_report`. Adds `tests/fixtures/` entries for each, feeding back into the regression suite. The tutorial walks through authoring one of these from scratch; the remaining three serve as worked examples.
- **Tutorial 3 — Writing Structured Personas:** Uses the v0.0.4 attack vector table format. Walks through authoring a new persona from scratch, using `ddo-create-persona`. Depends on v0.0.4 landing.

---

## Actionable Steps

### v0.0.4

- [ ] Restructure `ddo/personas/product_critic.md` attack vector section to standardized table format with IDs
- [ ] Restructure `ddo/personas/scientific_reviewer.md` attack vector section to same format
- [ ] Update `ddo-red-team` skill: inject attack vector table; instruct AI to use exact ID + Name per finding
- [ ] Author `ddo/skills/ddo-create-persona.md` skill
- [ ] Write unit tests for the updated `ddo-red-team` skill behavior (fixture-based)
- [ ] Update `architecture.yml`: persona nodes to `needs_review`; run hypergraph_updater

### v0.0.5

- [ ] Create `ddo/styles/` directory
- [ ] Author `ddo/styles/formal_professional.md`
- [ ] Author `ddo/styles/conversational.md`
- [ ] Author `ddo/styles/technical_precise.md`
- [ ] Add `meta.style_profile` as optional field to `ddo/schemas/prd.yaml` and `ddo/schemas/scientific_report.yaml`
- [ ] Update `ddo-ingest` skill: load and inject style profile if `meta.style_profile` is set
- [ ] Update `ddo-refine` skill: load and inject style profile if `meta.style_profile` is set
- [ ] Author `ddo/skills/ddo-create-style.md` skill
- [ ] Write tests: style profile loading, injection contract, absent `meta.style_profile` no-op
- [ ] Update `architecture.yml`: style nodes to `needs_review`; run hypergraph_updater

### v0.0.6

- [ ] Decide tutorial output location (`docs/tutorials/` vs. `Documents/tutorials/`)
- [ ] Write Tutorial 1: Evidence Bank Workflow (uses `tests/fixtures/ingest_output.yaml`)
- [ ] Author four new schemas + templates: `blog_post`, `meeting_notes`, `meeting_agenda`, `project_report`; add fixtures to `tests/fixtures/`
- [ ] Write Tutorial 2: Authoring Custom Structures (blog_post as primary walkthrough; others as worked examples)
- [ ] Write Tutorial 3: Writing Structured Personas (requires v0.0.4 complete)
- [ ] Verify all tutorial examples execute without error against their fixtures
- [ ] Update `architecture.yml`; run hypergraph_updater

---

## Known Constraints & Open Questions

1. **v0.0.3 dependency:** v0.0.3 (structural patch operations) must land before any of these three versions begin. v0.0.4 through v0.0.6 are explicitly post-v0.0.3.

2. **Tutorial output location:** `docs/tutorials/` (documentation-first, independent of Documents/) vs. `Documents/tutorials/` (inside the gitignored output zone, which would mean tutorials aren't version-controlled — probably wrong). Likely `docs/tutorials/` but needs a decision.

4. **Style profile injection point:** Does the style profile inject at the beginning of the skill's system prompt, or as a user-turn prefix? This affects how strongly it bounds the AI's output. TBD during v0.0.5 implementation.

5. **`ddo-create-persona` skill scope:** Does it produce a ready-to-use `.md` file in one pass, or does it run an interactive Q&A loop (similar to `ddo-interview`)? The interview-loop pattern would produce better results but is more complex.

6. **`ddo-create-persona` skill scope:** Does it produce a ready-to-use `.md` file in one pass, or does it run an interactive Q&A loop (similar to `ddo-interview`)? The interview-loop pattern would produce better results but is more complex.

7. **`ddo-create-style` skill scope:** Same question as above — one-pass or interactive Q&A?

---

## Decisions Confirmed

| # | Decision | Rationale |
|---|---|---|
| D1 | No YAML persona schema; attack vectors stay in Markdown | Avoids `ddo.review` surgery, backward compat break, two-codepath maintenance |
| D2 | Category validation is cognitive, not mechanical | Same tradeoff as style injection; system value is reproducible structure, not AI policing |
| D3 | Style profiles are Markdown files in `ddo/styles/` | Mirrors persona pattern exactly; zero new infrastructure |
| D4 | No forbidden-token scan in validation gate | Cognitive injection is sufficient; hard enforcement requires machine-parseable rules, adds complexity |
| D5 | `meta.style_profile` is optional; absence is a no-op | Backward compat; existing documents unaffected |
| D6 | `ddo-create-persona` belongs in v0.0.4 | Natural pairing: standardize format, then provide tooling to author new ones |
| D7 | Attack vector IDs are per-persona, starting from `AV-01` | Simpler; no cross-persona coordination overhead; globally unique IDs solve a problem not yet demonstrated |
| D8 | Tutorial 2 introduces four document types: `blog_post`, `meeting_notes`, `meeting_agenda`, `project_report` | Concrete, real-world examples that cover the full range of DDO use cases from casual to formal |

---

## The Graveyard

| Idea | Why discarded |
|---|---|
| Persona YAML schema with attack vector IDs validated in `ddo.review` | Required backward compat migration for existing personas and reports, two codepaths in `ddo.review`, schema surgery — cost too high for the consistency gain |
| Global `writing_style.yaml` enforcing forbidden tokens in validation gate | Forbidden-token scan requires machine-parseable rules; Markdown prose ("I don't like em-dashes") isn't parseable as a rule; cognitive injection achieves the same goal at zero infra cost |
| Style and persona coupling (persona carries style rules) | Two different concerns at two different phases — critique register belongs in persona, generation register belongs in style profile |
