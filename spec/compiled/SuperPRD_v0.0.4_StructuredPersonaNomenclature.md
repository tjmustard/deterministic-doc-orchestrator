# SuperPRD: DDO v0.0.4 — Structured Persona Nomenclature (+ deprecated-op removal)

> **Phase:** Resolution (compiled). Source: `spec/active/Draft_PRD.md` + `spec/active/RedTeam_Report.md`
> (15 findings RT-01..RT-15, all triaged below).
> **Resolved by:** `/hyper-resolve` — 2026-06-30. User decisions logged in §5.2.
> **Next step:** `/hyper-execute` each MiniPRD in `spec/compiled/`, then `hypergraph_updater.py` + `/hyper-audit`.

---

## 1. Introduction & Goals

### Problem Statement
The Red Team writes each finding's `category` as ad-hoc free text (`"Missing Evidence"`, `"Style"`).
Categories drift between runs, so the downstream Interview/Refine phases have no stable vocabulary
to reference **within a persona's run history**. Separately, the v0.0.3 release deprecated two
hardcoded patch ops (`append_evidence`, `append_review_log`) and scheduled their removal for v0.0.4
(locked decision RT-v0.0.3-13); leaving them in place maintains two codepaths for one capability.

### Solution Overview
Restructure each persona's `## Attack Vectors` prose into a standardized ID'd Markdown table
(`AV-01 … AV-NN`). Update `ddo-red-team` to read that table and bind each finding's `category` to the
exact `AV-NN: <name>`. Add a `ddo-create-persona` skill (interactive Q&A loop) so new personas are
authored in this format repeatably. Consistency is enforced **cognitively, not mechanically** —
`category` stays free-text in `ddo/review.py` (no schema or validation-gate change). Finally, remove
the two deprecated ops and reconcile their tests/docs/tutorial references.

### Target Audience
Document authors running the adversarial loop (consumers of consistent finding categories) and
persona authors (new `ddo-create-persona` tooling). DDO maintainers are the audience for the
deprecation cleanup.

### Scope clarification (RT-10): aggregation is per-persona, not cross-persona
AV IDs are per-persona and AV-01-based (D7), so `AV-01` denotes a *different* vector in each persona.
"Referenceable / aggregatable" therefore holds **within a single persona's run history**, not across
personas. Cross-persona aggregation is explicitly out-of-scope; the goal language is scoped to match.

---

## 2. Confidence Mandate
- **Confidence Score:** 10 / 10. All 15 Red Team findings have a documented decision (§5.2). The two
  Critical findings (RT-01/RT-02) were *state-assumption corrections*, now reconciled. The two true
  architectural collisions (RT-03 containment, RT-05 legacy-persona contract) were resolved by the
  user on 2026-06-30. The determinism/NFR batch (RT-04/06/13/15 + AV-name hardening) was approved as
  the proposed defaults.
- **Clarifying Questions:** None outstanding.

---

## 3. Scope

### In-Scope
- Restructure `## Attack Vectors` in `ddo/personas/product_critic.md` and `scientific_reviewer.md`
  to ID'd tables (`AV-01..AV-06`, snake_case Name in **raw `_`**, "When to apply" = existing probe).
- Update `ddo/skills/ddo-red-team.md`: inject the active persona's table, bind `category` to the exact
  `AV-NN: <name>`, **and hard-fail (naming the persona) if the resolved persona has no AV table** (RT-05).
- New skill `ddo/skills/ddo-create-persona.md` — interactive Q&A loop authoring `ddo/personas/<name>.md`;
  **cognitive overwrite guard** (exists-check + HITL re-confirm-with-literal-filename), writes only after
  the `[WAITING FOR USER REVIEW]` gate (RT-03), never emits sentinel tokens to a committed persona (RT-13).
- Remove deprecated ops `append_evidence` / `append_review_log` from `refine.py`, `review.py`,
  `ddo-interview.md`, README, CHANGELOG.
- **Rewrite** `tests/unit/test_personas.py` (it already exists as an RT#12 smoke test) into a
  `ddo/personas/*.md` glob AV-table structural validator (RT-01/RT-02).
- Flip the 4 legacy-op tests in `tests/unit/test_refine.py` to rejection tests **and add** net-new
  `validate_interview_log` rejection tests in `tests/unit/test_review.py` (RT-07/RT-15).
- Tutorial fix: migrate `tutorials/ddo-adversarial-loop-v0.0.2/code_samples/interview_call.py`
  **both** the `:41` comment and the `:61` op; reword `tutorial.md` rows 155-156 to past tense (RT-08/RT-09).
- Update `architecture.yml`: mark dirty nodes, **hand-add** `skill_create_persona`, mark `test_personas_unit`
  dirty (it already exists), run `hypergraph_updater.py`; regenerate the 3 prose op-references (RT-14).

### Out-of-Scope
- v0.0.5 (style/tone profiles); the **full** v0.0.6 tutorial refresh.
- `tutorials/.../audit_2026-06-30.md` — a dated audit artifact, **frozen as a historical record** (RT-08).
- Any change to the `red_team_report` validation contract — `category` stays free-text (D1/D2).
- A persona YAML schema or a machine-enforced `category` whitelist in `review.py` (Graveyard items).
- Cross-persona globally-unique AV IDs (D7: per-persona, AV-01-based).
- Migration of pre-v0.0.4 reports — they retain free-text categories (RT-11, partial rollout accepted).

### Known partial rollout (RT-11)
The stable vocabulary applies to **new** reports only. Pre-v0.0.4 reports keep their free-text
categories; nothing migrates them (correct, per D1/D2). The benefit is realized going forward.

---

## 4. User Stories (Atomic)

| ID | User Story | Acceptance Criteria | Priority |
| :-- | :-- | :-- | :-- |
| US-001 | As a document author, I want Red Team finding categories drawn from a fixed per-persona table so they're consistent and referenceable across that persona's runs. | 1. Both built-in personas expose an `AV-NN`-ID'd Attack Vectors table.<br>2. `ddo-red-team` instructs the AI to emit `category` as the exact `AV-NN: <name>` from the active persona's table.<br>3. The §6 example finding in the skill shows the new format.<br>4. If the resolved persona has **no** `## Attack Vectors` table, `ddo-red-team` **hard-fails naming the persona** (RT-05). | High |
| US-002 | As a persona author, I want a guided skill to write a new persona in the standard format so authoring is repeatable. | 1. `ddo-create-persona` runs a paced, one-batch-at-a-time Q&A with HITL gates.<br>2. It elicits all six persona sections including a well-formed AV table (sequential, unique IDs).<br>3. Output is a new `ddo/personas/<name>.md`, written **only after** the `[WAITING FOR USER REVIEW]` gate.<br>4. It refuses to overwrite an existing `ddo/personas/<name>.md` unless the user re-confirms with the literal filename (cognitive guard — RT-03).<br>5. It **never** commits a persona containing `[REQUIRES USER INPUT:` / `[[DDO::REQUIRES_INPUT:` sentinels (RT-13). | High |
| US-003 | As a maintainer, I want the deprecated ops removed so there is one structural-patch codepath. | 1. `append_evidence`/`append_review_log` removed from `apply_patches`, `OP_ENUM`, `ddo-interview.md`, and README.<br>2. `apply_patches` raises `ValueError` (unknown op) **and** `validate_interview_log` raises `ReportValidationError` for both ops — both independently reachable and tested (RT-15).<br>3. CHANGELOG documents the removal.<br>4. The tutorial code sample + the two `tutorial.md` rows are reconciled (RT-08/RT-09). | High |
| US-004 | As a maintainer, I want the persona table format guarded by a test so it cannot silently regress. | 1. `tests/unit/test_personas.py` globs **every** `ddo/personas/*.md`, parses its AV table, and asserts: table structure; `AV-NN` ID format + sequentiality + uniqueness; snake_case Name matching `^[a-z][a-z0-9_]*$` (no leading digit, no `__`, no trailing `_`); **raw** underscores (no `\_`, RT-04); Name uniqueness within the persona; no literal `\|` in cells (RT-06); non-empty columns; **sentinel-absence** (RT-13).<br>2. `uv run pytest` is green. | Medium |

---

## 5. Technical Specifications

### 5.1 AV table format (both personas)
```markdown
## Attack Vectors

| ID    | Name                       | When to apply              |
|-------|----------------------------|----------------------------|
| AV-01 | missing_acceptance_criteria | <existing probe verbatim>  |
```
- **Canonical cell encoding (RT-04):** the Name column uses **raw underscores** (`missing_acceptance_criteria`),
  NOT escaped `\_`. The string read from the table must equal the string emitted to `category`.
- **No pipes (RT-06):** "When to apply" probe text must not contain a literal `|` (the stdlib-`re`
  parser uses `|` as the column delimiter). The probes today contain none; the test enforces it.
- **product_critic:** AV-01 `missing_acceptance_criteria`, AV-02 `unsupported_value_claims`,
  AV-03 `scope_creep`, AV-04 `unmeasurable_success`, AV-05 `hedging_language`, AV-06 `contradictory_logic`.
- **scientific_reviewer:** AV-01 `methodological_vagueness`, AV-02 `unsupported_assertions`,
  AV-03 `statistical_ambiguity`, AV-04 `overreaching_conclusions`, AV-05 `missing_limitations`,
  AV-06 `result_discussion_bleed`.
- "When to apply" = the existing prose probe verbatim. Other persona sections unchanged.

### 5.2 Resolved Trade-offs Log (Red Team findings)

| RT | Severity | Resolution |
|---|---|---|
| RT-01 | **Critical** | **No corruption risk.** `hypergraph_updater.propagate_blast_radius` builds `nodes = {node['id']: node …}` (dict keyed by id) and only mutates `status`; it has **no node-add capability** and upsert-by-key makes duplicate ids impossible. `test_personas_unit` already exists (architecture.yml 448-463, status clean) → **mark dirty + REWRITE the file**, not "add node / new file." `skill_create_persona` must be **hand-added** to architecture.yml, then the updater run to propagate. |
| RT-02 | **Critical** | Rewrite `tests/unit/test_personas.py`: replace the hardcoded `_PERSONA_NAMES = ["product_critic","scientific_reviewer"]` smoke test with a `ddo/personas/*.md` **glob** AV-table structural validator (so create-persona'd personas are covered). |
| RT-03 | **Major** | **Cognitive-only guard (user decision).** `ddo-create-persona` does an `exists()` check + HITL re-confirm-with-the-literal-filename, writes via the Write tool **only after** `[WAITING FOR USER REVIEW]`. No mechanical `atomic_write`/`OverwriteError` backstop. Accepted residual risk: a misfiring agent could clobber a persona; the gate is the mitigation. |
| RT-04 | **Major** | Canonical AV-name cell encoding = **raw `_`** (no escaped `\_`). `test_personas.py` forbids escaped underscores in the Name column; read-string == emit-string. |
| RT-05 | **Major** | **Hard-fail (user decision).** If the resolved persona has no `## Attack Vectors` table, `ddo-red-team` hard-fails naming the persona (mirrors the existing missing-file hard-fail). No free-text fallback. |
| RT-06 | **Minor** | Probe text in "When to apply" cells MUST NOT contain a literal `|`; `test_personas.py` asserts. Protects the stdlib-`re` parser. |
| RT-07 | **Minor** | Accounting fix: all 4 legacy-op tests live in `test_refine.py` (lines 226/245/263/390) → flip to rejection. `test_review.py` rejection tests for `validate_interview_log` are **net-new** additions. |
| RT-08 | **Major** | Fix the code sample **fully**: `interview_call.py:41` comment **and** `:61` op. Reword `tutorial.md` 155-156. **Freeze** `audit_2026-06-30.md` as a historical record (out of scope). Add a `tutorials/` grep allow-list documenting the surviving audit-doc matches as the v0.0.6 baseline. |
| RT-09 | **Minor** | `tutorial.md` rows 155-156 → **reword** to past tense ("removed in v0.0.4 — migrate: `{op: append, target: …}`"), not delete. |
| RT-10 | **Minor** | Soften goal language: aggregation/referenceability is **per-persona** (D7); cross-persona aggregation explicitly out-of-scope. |
| RT-11 | **Minor** | Acknowledge **partial rollout**: stable vocabulary holds for new reports only; pre-v0.0.4 reports keep free-text categories (no migration). |
| RT-12 | **Minor** | **Intentional:** `skill_create_persona` has **no** `ddo_core` dependency (it rides the RT-03 cognitive-only choice and does not reuse safe-write machinery). Edges: `implements: [ddo_skills]`, `depends_on: [ddo_personas]`. |
| RT-13 | **Major** | `test_personas.py` asserts **sentinel-absence** (`[REQUIRES USER INPUT:` / `[[DDO::REQUIRES_INPUT:`) in committed personas, mirroring the `validation_gate` tripwire. Backed by a `ddo-create-persona` negative constraint. |
| RT-14 | **Minor** | **Verified clean:** no in-the-wild `interview_log`/`report` YAML carries the removed ops. The only references are 3 prose descriptions in `architecture.yml` (lines 518/587/663), which regenerate when the affected nodes are marked dirty. No data migration. |
| RT-15 | **Minor** | Assert **both** error surfaces independently: `apply_patches` raises `ValueError` (unknown op) AND `validate_interview_log` raises `ReportValidationError` — both reachable, both tested. |

### 5.3 `category` contract (cognitive, unchanged in code)
- `ddo-red-team.md` `category` finding-contract row (≈ line 107): redefine as *"the active persona's
  exact `AV-NN: <name>` from its Attack Vectors table (free-text in the schema; consistency enforced
  cognitively)."* Update the §6 example (≈ line 131) to `category: "AV-01: missing_acceptance_criteria"`.
  **No change to `validate_report`.**
- Add the RT-05 hard-fail clause to the persona-resolution step of `ddo-red-team`.

### 5.4 Deprecated-op removal (file:line anchors)
- `ddo/refine.py`: remove `elif op == "append_evidence"` / `"append_review_log"` branches (≈ 329-354);
  remove docstring bullets (≈ 267-269); fix unknown-op message (≈ 437-442) to list only
  `set, append, delete, insert`.
- `ddo/review.py`: drop both from `OP_ENUM` (≈ 37-46) → `{set, append, delete, insert}`; tidy comment (≈ 349).
- `ddo/skills/ddo-interview.md`: patch-shape `op:` line (≈ 90) → `set | append | delete | insert`;
  remove "Legacy Op Deprecation (v0.0.3)" section (≈ 233-240).
- `README.md` (≈ 153): drop both ops. `CHANGELOG.md`: add v0.0.4 entry.

### 5.5 System Graph Blast Radius
- **Mark dirty:** `ddo_personas`, `skill_red_team`, `skill_interview`, `review_engine`, the refine-engine
  node (`ddo/refine.py`), and **`test_personas_unit`** (RT-01 correction — it already exists).
- **Hand-add node:** `skill_create_persona` (Atomic; `associated_file: ddo/skills/ddo-create-persona.md`;
  `implements: [ddo_skills]`; `depends_on: [ddo_personas]`; **no `ddo_core`** — RT-12).
- Regenerate the 3 prose op-references in `architecture.yml` node descriptions (RT-14).
- **Run:** `python .agents/scripts/hypergraph_updater.py spec/compiled/architecture.yml <dirty node ids>`
  then assert exactly one `test_personas_unit` and one `skill_create_persona` node (no duplicate ids).

### 5.6 Execution Checklist (MiniPRDs)
- [ ] `spec/compiled/MiniPRD_Personas.md` — AV tables for both built-in personas.
- [ ] `spec/compiled/MiniPRD_SkillRedTeam.md` — inject table, bind `category`, add hard-fail clause.
- [ ] `spec/compiled/MiniPRD_SkillCreatePersona.md` — new interactive authoring skill (cognitive guard).
- [ ] `spec/compiled/MiniPRD_DeprecationRemoval.md` — `refine.py`+`review.py`+`ddo-interview.md`+README/CHANGELOG + tutorial fix.
- [ ] `spec/compiled/MiniPRD_TestPersonas.md` — rewrite `tests/unit/test_personas.py` (glob validator).
- [ ] `spec/compiled/MiniPRD_TestRefineReview.md` — flip 4 refine tests + add review rejection tests.
- [ ] `spec/compiled/MiniPRD_Hypergraph.md` — mark dirty, hand-add node, regenerate prose, run updater.

### 5.7 Dependencies
- No new libraries. Python stdlib + existing `pyyaml`. `test_personas.py` parses Markdown tables with
  stdlib `re` (no Markdown parser dependency).

---

## 6. Negative Constraints
- **DO NOT** add a `category` enum, whitelist, or forbidden-token scan to `ddo/review.py` — D1/D2:
  enforcement is cognitive only. (This prohibition does **not** bind `test_personas.py`, which validates
  the persona **source** table, not report `category` values.)
- **DO NOT** introduce a persona YAML schema or migrate existing `red_team_report_*.yaml` files.
- **DO NOT** use globally-unique AV IDs — per-persona, starting `AV-01` (D7).
- **DO NOT** let `ddo-create-persona` overwrite an existing persona without the literal-filename
  re-confirmation, or auto-advance past a `[WAITING FOR USER RESPONSE]` / `[WAITING FOR USER REVIEW]` gate.
- **DO NOT** commit a persona file containing `[REQUIRES USER INPUT:` / `[[DDO::REQUIRES_INPUT:` sentinels (RT-13).
- **DO NOT** invent persona content — emit `[REQUIRES USER INPUT: <reason>]` during authoring when a
  field can't be sourced (zero-hallucination invariant); resolve all sentinels before the final write.
- **DO NOT** escape underscores (`\_`) in AV-name cells; use raw `_` (RT-04).
- **DO NOT** rewrite `tutorials/.../audit_2026-06-30.md` — it is a frozen dated audit record (RT-08).
- **DO NOT** leave any *functional* reference to the removed ops in `ddo/` (docstrings, enums,
  branches, error strings) or in the tutorial **code sample** (`interview_call.py`).

---

## 7. Risks & Mitigation
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Source-tree write bypasses containment (RT-03).** `ddo/personas/` is outside `Documents/`; the cognitive-only guard has no mechanical backstop. | Low | High | Write only after the `[WAITING FOR USER REVIEW]` gate; require literal-filename re-confirm to overwrite; `test_personas.py` catches malformed/sentinel-bearing results in CI. **Accepted residual risk** per user decision. |
| **Legacy/custom persona has no AV table (RT-05).** | Medium | Medium | `ddo-red-team` hard-fails naming the persona — loud and early, consistent with the existing fail-closed posture. |
| **read≠emit determinism on AV names (RT-04).** | Low | Medium | Canonical raw `_` encoding; `test_personas.py` forbids escaped `\_`. |
| **Cognitive `category` enforcement drifts at runtime.** The test pins the source vocabulary but never sees report output. | Medium | Low | Explicit skill instruction + example finding pin the *menu*; residual runtime drift is **accepted, not mitigated** (D1/D2). |
| **Removing ops breaks logs in the wild.** | Low | Medium | RT-14 grep verified clean; migration forms shipped in v0.0.3; rejection tests make failure explicit and early. |
| **Tutorial keeps stale op references after a minimal fix (RT-08).** | Medium | Low | Fix the code sample fully; freeze the audit doc; document the surviving matches via a `tutorials/` grep allow-list as the v0.0.6 baseline. |
| **Half-authored persona with sentinels becomes silently usable (RT-13).** | Low | Medium | `test_personas.py` sentinel-absence assertion + create-persona negative constraint. |

---

## 8. Success Metrics
- A Red Team run against either built-in persona emits every finding's `category` as `AV-NN: <name>`
  matching that persona's table; a persona with no AV table makes `ddo-red-team` hard-fail naming it.
- `uv run pytest` green: `test_personas.py` (glob validator) passes; the 4 legacy-op tests in
  `test_refine.py` are flipped to rejection tests **and** net-new `validate_interview_log` rejection
  tests exist in `test_review.py`.
- `uv run ruff check .` and `uv run ruff format --check .` exit 0.
- `apply_patches` raises `ValueError` and `validate_interview_log` raises `ReportValidationError` for
  `append_evidence` / `append_review_log` — both surfaces tested independently (RT-15).
- `grep -rn "append_evidence\|append_review_log" ddo/` shows no functional references.
- `grep -rn "append_evidence\|append_review_log" tutorials/` matches **only** the frozen
  `audit_2026-06-30.md` allow-list (the code sample and `tutorial.md` migration rows are clean).
- `ddo-create-persona` produces a valid `ddo/personas/<name>.md` that passes `test_personas.py`.
- `architecture.yml` updated; `skill_create_persona` present; `hypergraph_updater` run leaves exactly
  one `test_personas_unit` and one `skill_create_persona` node (no duplicate ids).

---

## Candidate Artifacts (Novel Frontier) — Phase 3 routing protocol
- A persona produced by `ddo-create-persona` is **AI-generated, non-deterministic** content written to
  the **source** tree (`ddo/personas/`), not `Documents/`/`candidate_outputs/`. The novel-frontier risk
  is that a non-deterministic artifact becomes a deterministic *input* to the adversarial loop.
- **Routing (cognitive, consistent with the RT-03 choice):** (1) the skill writes the persona **only
  after** its `[WAITING FOR USER REVIEW]` gate — the human sign-off is the promotion event; (2) the
  committed persona must pass `test_personas.py` (structure + sentinel-absence) — the mechanical
  backstop in CI; (3) `ddo-red-team` hard-fails on a persona with no valid AV table (RT-05). No new
  mechanical pre-flight gate is added inside `ddo-red-team` (would contradict the cognitive-only posture).
- The generated persona is **not** auto-promoted to `tests/fixtures/`.
- Red Team `category` values remain Candidate Outputs (free-text); the persona-table test pins the
  deterministic source vocabulary they must draw from.

---

*SuperPRD generated by Resolution Agent (hyper-resolve) — 2026-06-30. MiniPRDs: Personas, SkillRedTeam,*
*SkillCreatePersona, DeprecationRemoval, TestPersonas, TestRefineReview, Hypergraph.*
