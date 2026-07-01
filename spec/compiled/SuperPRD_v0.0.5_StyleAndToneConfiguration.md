# SuperPRD: DDO v0.0.5 — Style and Tone Configuration

> **Phase:** Resolution (compiled). Source: `spec/active/Draft_PRD.md` +
> `spec/active/RedTeam_Report.md` (10 findings RT-1..RT-10, all triaged below).
> **Resolved by:** `/hyper-resolve` — 2026-06-30. User decisions logged in §5.2.
> **Next step:** `/hyper-execute` each MiniPRD in `spec/compiled/` in DAG order (§5.3),
> then `hypergraph_updater.py` + `/hyper-audit`.

---

## 1. Introduction & Goals

### Problem Statement
DDO authors have no version-controlled way to control the **register** (tone, voice,
formality) of AI-generated prose. The Ingest and Interview phases emit text in whatever
default voice the agent picks, so a casual blog post and a formal enterprise PRD read the
same, and register drifts between runs and between phases of a single document.

The Red Team (RT-7) sharpened the honest framing of this goal: cognitive enforcement
cannot make a non-deterministic authoring step *reproducible*; it can only **anchor**
register to a version-controlled reference the human reviews against. The goal is therefore
restated as: *register is anchored to a named, version-controlled profile that is loaded
into context, echoed in the post-condition summary, and named at the HITL gate* — verifiable
plumbing, with register-conformance itself judged by the human, not by CI.

### Solution Overview
Introduce **style profiles** — version-controlled Markdown files in a new `ddo/styles/`
directory, referenced from `document_data.yaml` via an optional `meta.style_profile` field.
During the two prose-authoring phases (`ddo-ingest`, `ddo-interview`) the referenced profile
is loaded up front as a **governing, phrasing-only constraint** scoped to
`content.sections[*].body` prose. Consistency is enforced **cognitively**, not mechanically
— no validation-gate changes, no forbidden-token scanning, no Python module changes. A new
interactive `ddo-create-style` skill assists authoring profiles, mirroring
`ddo-create-persona`.

Three Red Team hardenings are baked into the design so cognitive enforcement does not silently
erode the project's keystone invariant:
1. **Fabrication is routed into the sentinel channel** (RT-1): a style directive that would
   require a fact absent from source must emit `[[DDO::REQUIRES_INPUT:]]` rather than invent
   it — converting an undetectable failure (silent fabrication) into a render-blocking one.
2. **The profile is consumed as untrusted phrasing-only guidance** (RT-2): the injection
   framing sandboxes it, so a hand-authored/edited profile cannot smuggle content or
   instructions into the authoring context regardless of how it was written.
3. **Stored `style_profile` is distrusted on every read** (RT-4): the stem gate re-validates
   the value before any Read regardless of provenance, closing the refine-channel traversal
   storage path.

### Target Audience
DDO document authors (who set `meta.style_profile`) and style authors (who create reusable
profiles). Single-user, local, no-network tool.

**Foundation:** v0.0.4 (Structured Persona Nomenclature + `ddo-create-persona`) has landed
and is audited. v0.0.5 mirrors that persona machinery for styles. Scoped **strictly to
v0.0.5**; v0.0.6 (tutorials) is out of scope.

---

## 2. Confidence Mandate
- **Confidence Score:** 10 / 10. All 10 Red Team findings have a documented decision (§5.2).
  The two Critical findings (RT-1 style-induced fabrication, RT-2 un-scanned injection channel)
  were resolved by routing fabrication pressure into the sentinel channel and by read-time
  sandboxing. The four Major findings (RT-3 loop convergence, RT-4 stored-value traversal,
  RT-5 evidence over-application, RT-6 bootstrapping) were adjudicated with the user on
  2026-06-30. The four Minor findings (RT-7..RT-10) were approved as proposed defaults, with
  RT-10 (persona-sink parity) upgraded to close-now since RT-3 already edits the same file.
- **Clarifying Questions:** None outstanding.

---

## 3. Scope

### In-Scope
- New `ddo/styles/` directory (Module node `ddo_styles`), mirroring `ddo/personas/`.
- Three built-in profiles: `formal_professional.md`, `conversational.md`,
  `technical_precise.md`, each in the required 5-section structure, authored to contain
  **zero content-bearing or quantitative/factual imperatives** (RT-1/RT-2).
- Optional `meta.style_profile` field added to `ddo/schemas/prd.yaml` and
  `ddo/schemas/scientific_report.yaml`, with **live per-doc-type defaults**
  (`formal_professional` / `technical_precise`). **MP-1 and MP-2 land atomically** — a schema
  default MUST NOT reference a profile absent from the same change (RT-6).
- Style injection into **`ddo-ingest`** (initial section prose) and **`ddo-interview`**
  (revision / `add_evidence` prose), as an up-front governing constraint that is:
  - scoped to `content.sections[*].body` **only** — never `evidence_bank[*]` or `meta.*` (RT-5);
  - framed as **untrusted phrasing-only** guidance (RT-2);
  - carries the **sentinel-routing instruction** for would-be fabrications (RT-1);
  - re-validates the **stored** stem on every read, regardless of provenance (RT-4);
  - echoes the resolved profile path in the post-condition summary and names it at the
    `[WAITING FOR USER REVIEW]` gate (RT-7).
- New `ddo-create-style` skill (Atomic node `skill_create_style`) — interactive paced Q&A
  mirroring `ddo-create-persona`, including cognitive rejection of content-bearing directives
  and an explicit ban on quantitative/factual imperatives in `Diction`/`Avoid` (RT-1/RT-2).
- New `tests/unit/test_styles.py` (Atomic node `test_styles_unit`) — glob structural validator
  with a `test_style_dir_has_files` guard and negative-case parity with `test_personas.py` (RT-9).
- Cognitive stem-validation gate (`^[a-z][a-z0-9_]*$`) and cognitive hard-fail on a
  referenced-but-missing profile; **any present-but-invalid value (`""`, `null`/`~`,
  whitespace-only) is a hard-fail, never a silent no-op** (RT-8).
- **Close the parallel `meta.persona` traversal gap in `ddo-red-team.md`** with the identical
  stem gate + hard-fail (RT-10), and **surface the active `style_profile` in the Red Team
  report header** so the critique is register-aware (RT-3). Both land in `skill_red_team`.

### Out-of-Scope
- **No changes to `ddo-refine` / `refine.py`** — it is mechanical (applies pre-authored patch
  `value`s via `apply_patches`) and authors no prose. RT-4 is handled cognitively at read-time,
  **not** by a refine write-time block, so this invariant holds.
- **No Python module changes** — `validation.py`, `build.py`, `review.py`, `refine.py`,
  `ingest.py`, `paths.py` are untouched. No `ddo_core` dependency in any new skill.
- **No validation-gate / render changes** — `style_profile` is render-invisible; templates
  never read it. No forbidden-token scan, no machine-parsed style rule (D4 / Graveyard).
- **No coupling of persona↔style in schema/validation** (RT-3 rejected the enforce-in-schema
  option) — pairing guidance is documentary + register-aware critique only.
- **No YAML style schema.** **No fixture promotion / no re-promotion of
  `tests/fixtures/ingest_output.yaml`** — zero regression-fixture churn.
- **v0.0.6 tutorials** and any new document types.

### Accepted-risk caveats (surfaced, not mitigated further)
- **`--force` re-ingest restyles legacy docs** (RT-6): a pre-v0.0.5 `document_data.yaml`
  re-ingested with `--force` picks up the live schema default and is authored under it.
  Byte-identical-to-v0.0.4 behavior holds only for YAML that is *never re-ingested*.
- **Un-scanned profile content** (RT-2): a hand-authored/edited profile is a trusted
  instruction channel on the authoring side; read-time sandboxing bounds its effect, but
  **HITL review of every profile at merge is the only authoring-side gate**. Known-accepted.

---

## 4. User Stories (Atomic)

| ID | User Story | Acceptance Criteria | Priority |
| :--- | :--- | :--- | :--- |
| US-001 | As a document author, I want to set `meta.style_profile` so AI-generated prose is anchored to a consistent, named register. | 1. `ddo-ingest` reads `ddo/styles/<stem>.md` and bounds `content.sections[*].body` prose to it.<br>2. `ddo-interview` applies the same profile when composing revision prose.<br>3. The profile governs phrasing only — no content introduced.<br>4. **(RT-7, observable)** The resolved profile path is echoed in the ingest/interview post-condition summary and named at the `[WAITING FOR USER REVIEW]` gate, so the human reviews prose against a named reference. | High |
| US-002 | As a document author, when I reference a profile that does not exist, I want the skill to halt and tell me. | 1. Skill Reads `ddo/styles/<stem>.md`; if absent, it halts.<br>2. The halt names the missing file and lists available `ddo/styles/*.md`.<br>3. No prose is authored. | High |
| US-003 | As an author with a pre-v0.0.5 document, I want YAML without `style_profile` to behave exactly as before. | 1. **Absent** `meta.style_profile` → clean no-op.<br>2. Existing `Documents/` YAML and golden render baselines unchanged.<br>3. **(RT-8)** A *present-but-invalid* value (`""`, `null`/`~`, whitespace-only) is a **hard-fail**, NOT a no-op. | High |
| US-004 | As a style author, I want an interactive `ddo-create-style` skill to author a profile in the standard structure. | 1. Paced Q&A ≤2 questions/turn across the 5 sections.<br>2. Sentinel resolution before write.<br>3. Draft-preview `[WAITING FOR USER REVIEW]` gate + `APPROVE`.<br>4. Cognitive Read-based overwrite guard + literal-filename re-confirm.<br>5. **(RT-1/RT-2)** Rejects content-bearing directives; bans quantitative/factual imperatives in `Diction`/`Avoid`; a 3–5 example rubric anchors phrasing-vs-content-vs-framing judgments. | High |
| US-005 | As a maintainer, I want `test_styles.py` to enforce the structural contract on all `ddo/styles/*.md`. | 1. Glob over `ddo/styles/*.md`.<br>2. Asserts title heading + all 5 required section headings.<br>3. Asserts non-empty bodies.<br>4. Asserts sentinel-absence.<br>5. Does **not** assert prose content.<br>6. **(RT-9)** Includes `test_style_dir_has_files` guard + negative cases (missing heading, empty body, sentinel present), mirroring `test_personas.py`. | High |
| US-006 | As a security-conscious maintainer, I want `style_profile` stems validated against a strict charset before any Read. | 1. Stem must match `^[a-z][a-z0-9_]*$` before any Read.<br>2. `.`, `/`, `..` structurally rejected.<br>3. Validation happens in both injection skills and `ddo-create-style`, pre-resolution.<br>4. **(RT-4)** The gate re-fires on **stored** values on every read, regardless of provenance (author- or refine-set). | High |
| US-007 | As a document author, I want sensible register out of the box. | 1. `prd.yaml` ships `style_profile: "formal_professional"`.<br>2. `scientific_report.yaml` ships `style_profile: "technical_precise"`.<br>3. Both referenced files exist and resolve **in the same change** (RT-6 atomic landing). | Medium |
| US-008 | As a loop operator, I want the adversarial critique to be aware of the intended register so it does not oscillate. | 1. **(RT-3)** The Red Team report header surfaces the active `style_profile` alongside the persona.<br>2. Recommended aligned pairings are documented.<br>3. **(RT-10)** `ddo-red-team.md` validates the `persona` stem with the identical gate + hard-fail. | Medium |

---

## 5. Technical Specifications

### 5.1 Architecture & Resolved Trade-offs
- **Pattern:** Styles mirror personas one-for-one. `ddo/styles/` ↔ `ddo/personas/`;
  `ddo-create-style` ↔ `ddo-create-persona`; `test_styles.py` ↔ `test_personas.py`.
- **Injection sites:** `ddo-ingest` (initial prose) + `ddo-interview` (revision prose).
  `ddo-refine` remains excluded — mechanical, authors no prose.
- **Style file contract:** test-enforced **heading** structure, free-prose **bodies**.
  Required title `# **Style Profile: <name>**` + five `##` sections: `Register & Audience`,
  `Voice & Person`, `Sentence & Structure`, `Diction`, `Avoid`.
- **Injection mechanics:** load the profile **once, up front**, as a governing constraint
  block, scoped to `content.sections[*].body`, framed untrusted/phrasing-only, carrying the
  sentinel-routing instruction, re-validating the stored stem, and echoing the resolved path
  at the HITL gate. Reinforced by a pre-write checklist item ("phrasing changes only, zero
  new facts").
- **Traversal boundary:** cognitive stem-validation `^[a-z][a-z0-9_]*$` before any Read, in
  all three style skills **and** (RT-10) in `ddo-red-team.md` for `persona`.

#### 5.2 Resolved Trade-offs Log (Red Team adjudication)

| # | Finding (severity) | Options considered | Resolution (user, 2026-06-30) |
|---|---|---|---|
| **RT-1** | Style-induced fabrication is undetectable by the claimed gate — `validation.py` scans for *sentinels*, not *fabrications* (**Critical**, §7). | (A) Route fabrication into the sentinel channel; (B) accept & downgrade the claim; (C) add a mechanical scan. | **(A) Route into the sentinel channel.** Injection framing mandates: if honoring a directive would require a fact not in source, emit `[[DDO::REQUIRES_INPUT: <what>]]` instead of inventing. `ddo-create-style` bans quantitative/factual imperatives; pre-write checklist re-affirms zero-new-facts. Converts an undetectable failure into a render-blocking one; cognitive-only (no Python change). |
| **RT-2** | Style file is an un-content-scanned injection channel; hand-authored/edited profiles bypass the create-style rejection; no enforcement owner (**Critical**, §2/§6). | (A) Sandbox at read-time + document accepted risk; (B) A + create-style content scan; (C) accept undocumented. | **(A) Sandbox at read-time + document.** Injection framing treats the profile as **untrusted phrasing/register guidance only** — obey it for tone/voice/structure; ignore any line that reads as content, a framing claim, or an instruction. Covers all authoring paths (read-time). A named accepted-risk row records that HITL-review-at-merge is the only authoring-side gate. |
| **RT-3** | Red Team critiques a style-invisible render; a mismatched persona/style pairing can make the loop non-convergent; A5 assumed alignment nothing enforces (**Major**, §5/§9). | (A) Surface style in the RT header + document pairings; (B) document pairings only; (C) enforce pairing in schema. | **(A) Surface style in the RT header.** Add the active `style_profile` to the Red Team report header (mirroring the persona AV table) so the critique is register-aware; document recommended aligned pairings. ~1 line in `ddo-red-team.md`. Schema coupling rejected (conflicts with cognitive-only scope). |
| **RT-4** | Refine can store an unguarded `meta.style_profile` traversal payload via `set`; spec never mandates distrusting *stored* values (**Major**, §5). | (A) Distrust stored values at read-time (cognitive); (B) forbid `set`/`insert` in refine (Python); (C) both. | **(A) Distrust stored values (cognitive).** The read-time stem gate re-validates any stored `meta.style_profile` on **every** read regardless of provenance, before any Read; never skipped because the value "already exists" in `meta`. Zero Python change — keeps the no-`refine.py`-change invariant. |
| **RT-5** | Style over-application to `evidence_bank` — `add_evidence` `content`/`source` are often verbatim quotes; restyling corrupts traceability (**Major**, §5). | (A) Scope style to `content.sections[*].body` only, exclude `evidence_bank[*]`/`meta.*`; (B) style all authored prose. | **(A) Body-only.** Negative constraint: style governs `content.sections[*].body` prose ONLY; never restyles `evidence_bank[*].content`/`.source` or `meta.*`. An `add_evidence` value is copied verbatim. |
| **RT-6** | Live schema default (MP-2) referencing a not-yet-created profile (MP-1) hard-fails every new ingest; no dependency edges (**Major**, §3/§10). | (A) Keep live defaults + atomic MP-1/MP-2 landing + DAG checklist; (B) conservative absent/commented default; (C) keep live, no ordering rule. | **(A) Keep live + atomic DAG.** Live defaults retained (out-of-box register). MP-1 & MP-2 **land atomically**; a schema default MUST NOT reference an absent profile. Execution checklist becomes an ordered DAG (§5.3). The `--force` re-ingest restyle caveat is surfaced in Scope. |
| **RT-7** | US-001 has no falsifiable AC; metrics measure plumbing, not register (**Minor**, §1/§4/§8). | Approved default. | **Approved.** US-001 gains an observable AC (resolved path echoed in the post-condition summary + named at the HITL gate). Success Metrics split into **mechanical (CI-gated)** vs **human-judged (HITL-gated)**; register-conformance is labeled the latter. |
| **RT-8** | Empty/null/whitespace `style_profile` is an undefined US-002/US-003 boundary (**Minor**, §4). | Approved default. | **Approved.** Any *present-but-invalid* value (`""`, `null`/`~`, whitespace-only) is a **hard-fail** like US-002 — never a silent no-op. Only a truly absent field is the US-003 no-op. |
| **RT-9** | `test_styles.py` passes vacuously on an empty dir; needs a dir-guard + negative parity (**Minor**, §4/§8/§10). | Approved default. | **Approved.** Add `test_style_dir_has_files` guard + negative cases (missing heading, empty body, sentinel present), mirroring `test_personas.py`. Folded into MP-5 and the metrics. |
| **RT-10** | Deferred `meta.persona` traversal gap (verified real) leaves asymmetric hardening — same sink, one door closed, one open (**Minor**, §9). | (A) Close it now (RT-3 already edits `ddo-red-team.md`); (B) defer + document; (C) defer silently. | **(A) Close it now.** Apply the identical `^[a-z][a-z0-9_]*$` stem gate + hard-fail to `persona` resolution in `ddo-red-team.md`. Marginal cost ~3 lines since RT-3 already touches that file; both file-resolution sinks are hardened identically. A6's deferral is superseded. |

### 5.3 System Graph Blast Radius & Execution Checklist (DAG)
The following nodes in `spec/compiled/architecture.yml` are affected:

**New nodes**
- `ddo_styles` — `Module`, `associated_file: ddo/styles/`, `implements: [ddo_system]`.
- `skill_create_style` — `Atomic`, `associated_file: ddo/skills/ddo-create-style.md`,
  `implements: [ddo_skills]`, `depends_on: [ddo_styles]`.
- `test_styles_unit` — `Atomic`, `associated_file: tests/unit/test_styles.py`,
  `implements: [tests_unit]`, `depends_on: [ddo_styles]`.

**Modified nodes → `needs_review`**
- `ddo_schemas` — `meta.style_profile` + live defaults in `prd.yaml`/`scientific_report.yaml`.
- `ddo_skills` — module description + `ddo-ingest.md` style injection (no dedicated Atomic node).
- `skill_interview` — style injection for revision prose.
- `skill_red_team` — RT-3 header + RT-10 persona stem gate.

**Explicitly NOT touched:** `skill_refine`, `refine_engine`, `review_engine`,
`validation_gate`, `build_orchestrator`, `ingest_helpers`, `path_deriver`, and all
render/determinism test nodes.

**Execution DAG** (`/hyper-execute` in this order; `blocks`/`blocked-by` noted):
```
MP-1 (Styles) ──┬─> MP-2 (SchemaStyleField)   [ATOMIC with MP-1]
                ├─> MP-3 (StyleInjection)
                └─> MP-5 (TestStyles)
MP-4 (SkillCreateStyle) ─────────────────────> MP-7 (Hypergraph)
MP-6 (RedTeamStyleAware) ────────────────────> MP-7 (Hypergraph)
MP-2, MP-3, MP-5 ────────────────────────────> MP-7 (Hypergraph)
```
- `spec/compiled/MiniPRD_Styles.md` — `ddo_styles` (**blocks all**)
- `spec/compiled/MiniPRD_SchemaStyleField.md` — `ddo_schemas` (**atomic with Styles**)
- `spec/compiled/MiniPRD_StyleInjection.md` — `ddo_skills` (ingest) + `skill_interview`
- `spec/compiled/MiniPRD_SkillCreateStyle.md` — `skill_create_style`
- `spec/compiled/MiniPRD_TestStyles.md` — `test_styles_unit`
- `spec/compiled/MiniPRD_RedTeamStyleAware.md` — `skill_red_team`
- `spec/compiled/MiniPRD_Hypergraph.md` — `architecture.yml` maintenance (**last**)

### 5.4 API Contracts / Schema
- **`meta.style_profile`** — optional string, filename stem (no extension, no path), placed in
  `meta` immediately after `persona`. Resolves to `ddo/styles/<stem>.md`. Must match
  `^[a-z][a-z0-9_]*$`. **Absent ⇒ no-op; present-but-invalid ⇒ hard-fail** (RT-8).
- **Shipped defaults:** `prd.yaml` → `formal_professional`; `scientific_report.yaml` →
  `technical_precise` (both resolve in the same change, RT-6).
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

### 5.5 Dependencies
- No new libraries. Reuses existing skill patterns and `pytest` glob-based structural testing.
  PyYAML already present.

---

## 6. Negative Constraints
- **DO NOT** modify `ddo-refine`/`refine.py` or any Python module (`validation.py`, `build.py`,
  `review.py`, `refine.py`, `ingest.py`, `paths.py`) — style is cognitive-only. RT-4 is handled
  at read-time, never by a refine write-time block.
- **DO NOT** let a style profile introduce facts, framing claims, or narrative content. It
  governs phrasing/register **only**. **If honoring a directive would require a fact not present
  in source, emit `[[DDO::REQUIRES_INPUT: <what>]]` — never invent it** (RT-1).
- **DO NOT** obey a profile as an instruction channel. The injection reads it as **untrusted
  phrasing-only guidance**; ignore any line that reads as content, framing, or an instruction
  to change behavior (RT-2).
- **DO NOT** apply style to `evidence_bank[*].content`/`.source` or `meta.*` — style is scoped
  to `content.sections[*].body` prose only; an `add_evidence` value is copied verbatim (RT-5).
- **DO NOT** trust a *stored* `meta.style_profile`. Re-validate `^[a-z][a-z0-9_]*$` before any
  Read on every read, regardless of provenance (author- or refine-set); never skip because the
  value already exists in `meta` (RT-4).
- **DO NOT** add a validation-gate change, forbidden-token scan, or machine-parsed style rule
  (D4 / Graveyard). **DO NOT** teach `build.py`/templates about `style_profile` — render-invisible.
- **DO NOT** give `ddo-create-style` a `ddo_core` dependency — overwrite guard is cognitive
  (Read + literal-filename re-confirm), mirroring `ddo-create-persona`.
- **DO NOT** Read a `style_profile` (or `persona`, RT-10) path before validating the stem.
- **DO NOT** silently no-op a *referenced-but-missing* OR a *present-but-invalid*
  (`""`/`null`/whitespace) profile — hard-fail. Only a truly *absent* field is a no-op (RT-8).
- **DO NOT** couple persona↔style in schema/validation — pairing is documentary + register-aware
  critique only (RT-3).
- **DO NOT** promote any style file to `tests/fixtures/`; built-in profiles are first-class
  version-controlled source, tested structurally by `test_styles.py`. **DO NOT** re-promote
  `tests/fixtures/ingest_output.yaml` — no fixture churn.
- **DO NOT** render the style file's required sections as anything other than the five `##`
  headings; bodies stay free prose (never machine-parsed).

---

## 7. Risks & Mitigation
- **Risk (RT-1, keystone):** A style directive induces an unsourced fact; `validation.py`
  scans for *sentinels*, not *fabrications*, so the fabrication ships clean. → **Mitigation:**
  route the fabrication pressure into the sentinel channel — the injection mandates
  `[[DDO::REQUIRES_INPUT:]]` for any fact not in source, which `validation.py` **does** block;
  `ddo-create-style` bans quantitative/factual imperatives; pre-write checklist re-affirms
  zero-new-facts. Converts an undetectable failure into a detectable one.
- **Risk (RT-2):** A profile carries content/injection directives and bypasses the
  authoring-time rejection (hand-authored/edited path). → **Mitigation:** read-time sandbox
  framing (untrusted, phrasing-only) bounds effect on all paths; **accepted residual:**
  HITL review of every profile at merge is the only authoring-side gate. Known-accepted.
- **Risk (RT-3):** Mismatched persona/style pairing oscillates the adversarial loop. →
  **Mitigation:** surface `style_profile` in the RT header (register-aware critique) + document
  aligned pairings.
- **Risk (RT-4):** Refine stores a traversal payload in `meta.style_profile`, detonating on a
  later read. → **Mitigation:** read-time gate distrusts stored values on every read.
- **Risk (RT-5):** Restyling corrupts verbatim evidence quotes. → **Mitigation:** body-only scope.
- **Risk (RT-6):** Out-of-order rollout hard-fails every new ingest. → **Mitigation:** atomic
  MP-1/MP-2 landing + DAG. **Accepted caveat:** `--force` re-ingest restyles legacy docs.
- **Risk:** Cognitive enforcement is not mechanically guaranteed. → **Mitigation:** accepted
  trade-off (D2/D4); value is reproducible *structure* + anchored register, not AI policing;
  HITL gates catch drift; up-front governing injection + pre-write checklist maximize adherence.
- **Risk:** Typo'd profile silently drops register. → **Mitigation:** cognitive hard-fail names
  the file and lists available profiles.

---

## 8. Success Metrics

**Mechanical (CI-gated):**
- All three built-in profiles exist in `ddo/styles/` and pass `test_styles.py` (incl.
  `test_style_dir_has_files` + negative cases).
- `test_styles.py` auto-covers any future profile via glob (including `create-style` output).
- A referenced-but-missing **or** present-but-invalid (`""`/`null`/whitespace) `style_profile`
  halts with a file-named, alternatives-listed message in both injection skills.
- A `style_profile` (or `persona`, RT-10) containing `/`, `.`, or `..` is rejected before any Read.
- Absent `style_profile` ⇒ byte-identical behavior to v0.0.4 (for YAML never re-ingested).
- Full suite (existing 183 tests + new `test_styles.py`) passes; `ruff check` and
  `ruff format --check` exit 0. No diff to any Python module; no re-promotion of `tests/fixtures/`.

**Human-judged (HITL-gated):**
- `meta.style_profile` present + valid ⇒ both `ddo-ingest` and `ddo-interview` **load** the
  profile (observable: resolved path echoed in the post-condition summary and named at the
  `[WAITING FOR USER REVIEW]` gate) — register-conformance itself is reviewed by the human
  against that named reference, not asserted by CI.
- `ddo-create-style` produces a valid 5-section profile through paced Q&A, gated by `APPROVE`
  and the cognitive overwrite guard, with zero content-bearing directives.
- The Red Team report header surfaces the active `style_profile` (register-aware critique).

---

## 9. Provenance
- **Draft:** `spec/active/Draft_PRD.md` (`/hyper-architect`, 2026-06-30, 9 decisions A1–A9).
- **Red Team:** `spec/active/RedTeam_Report.md` (`/hyper-redteam`, 10 findings RT-1..RT-10).
- **Resolution:** this document (`/hyper-resolve`, 2026-06-30). A6's deferral of the
  `meta.persona` traversal gap is **superseded** by RT-10 (close-now).

**[WAITING FOR USER REVIEW]**
