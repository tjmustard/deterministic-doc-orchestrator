# Draft PRD: DDO v0.0.4 — Structured Persona Nomenclature (+ deprecated-op removal)

> **Phase:** Architect (Draft). Next step: `/hyper-redteam` → `/hyper-resolve` → `/hyper-execute`.
> **Source plan:** LivingMasterPlan_v0.0.4-v0.0.6 (v0.0.4 section) + v0.0.3 resolve carry-over.

---

## 1. Introduction & Goals

- **Problem Statement:** The Red Team writes each finding's `category` as ad-hoc free text (e.g.
  `"Missing Evidence"`, `"Style"`). Categories therefore drift between runs and across personas,
  cannot be referenced or aggregated, and give the downstream Interview/Refine phases no stable
  vocabulary. Separately, the v0.0.3 release deprecated two hardcoded patch ops
  (`append_evidence`, `append_review_log`) and scheduled their removal for v0.0.4 (RT-v0.0.3-13);
  leaving them in place maintains two codepaths for one capability.
- **Solution Overview:** Restructure each persona's "Attack Vectors" prose into a standardized
  ID'd Markdown table (`AV-01 … AV-NN`). Update `ddo-red-team` to read that table and bind each
  finding's `category` to the exact `AV-NN: <name>`. Add a `ddo-create-persona` skill (interactive
  Q&A loop) so new personas are authored in this format repeatably. Consistency is enforced
  **cognitively, not mechanically** — `category` stays free-text in `ddo/review.py` (no schema or
  validation-gate change). Finally, remove the two deprecated ops and their tests/docs.
- **Target Audience:** Document authors running the adversarial loop (consumers of consistent
  finding categories) and persona authors (new `ddo-create-persona` tooling). The DDO maintainers
  are the audience for the deprecation cleanup.

## 2. Confidence Mandate

- **Confidence Score:** 10 / 10. Design is confirmed in the LivingMasterPlan (D1–D8); all scope
  choices were resolved with the user on 2026-06-30 — deprecation removal IN; `ddo-create-persona`
  = interactive Q&A loop; tests = persona-table structural validation; `category` format =
  `AV-NN: <name>`; AV Name casing = **snake_case**; a minimal tutorial fix for the removed-op
  references is IN scope (full refresh stays v0.0.6); a `test_personas_unit` node is added for the
  new test file. Current-state file/line anchors verified.
- **Clarifying Questions:** None outstanding.
- **Derived facts (not requiring user input):** `ddo-*` skills have **no** `.claude/commands/`
  bridges (only `hyper-*` do), so `ddo-create-persona` needs only its `ddo/skills/*.md` file. There
  is **no persona registry** — `ddo-red-team` resolves a persona by name and reads the file directly.
  The Severity Taxonomy stays prose (only Attack Vectors get IDs).

## 3. Scope

- **In-Scope:**
  - Restructure `## Attack Vectors` in `product_critic.md` and `scientific_reviewer.md` to ID'd tables.
  - Update `ddo-red-team` to inject the table and bind `category` to `AV-NN: <name>`.
  - New skill `ddo/skills/ddo-create-persona.md` (interactive Q&A loop authoring a persona `.md`).
  - Remove deprecated ops `append_evidence` / `append_review_log` from code, skill, docs, tests.
  - New `tests/unit/test_personas.py` validating the persona attack-vector table structure.
  - Minimal tutorial fix for the removed ops: migrate the `append_evidence` usage in
    `tutorials/ddo-adversarial-loop-v0.0.2/code_samples/interview_call.py` and update the two
    "removed in v0.0.4" rows in that tutorial's `tutorial.md` (≈ 155-156).
  - Update `architecture.yml` (mark dirty + add `skill_create_persona` and `test_personas_unit`
    nodes); run hypergraph_updater.
- **Out-of-Scope:**
  - v0.0.5 (style/tone profiles); the **full** v0.0.6 tutorial refresh (only the minimal removed-op
    reconciliation above is in v0.0.4).
  - Any change to the `red_team_report` validation contract — `category` remains free-text (D1/D2).
  - A persona YAML schema or machine-enforced category whitelist (Graveyard items).
  - Cross-persona globally-unique AV IDs (D7: per-persona, AV-01-based).

## 4. User Stories (Atomic)

| ID | User Story | Acceptance Criteria | Priority |
| US-001 | As a document author, I want Red Team finding categories drawn from a fixed per-persona table so they're consistent and referenceable across runs. | 1. Both personas expose an `AV-NN`-ID'd Attack Vectors table.<br>2. `ddo-red-team` instructs the AI to emit `category` as the exact `AV-NN: <name>` from the active persona's table.<br>3. The example finding in the skill shows the new format. | High |
| US-002 | As a persona author, I want a guided skill to write a new persona in the standard format so authoring is repeatable. | 1. `ddo-create-persona` runs a paced, one-batch-at-a-time Q&A with HITL gates.<br>2. It elicits all six persona sections including a well-formed AV table (sequential, unique IDs).<br>3. Output is a new `ddo/personas/<name>.md`; never overwrites an existing persona without confirmation. | High |
| US-003 | As a maintainer, I want the deprecated ops removed so there is one structural-patch codepath. | 1. `append_evidence`/`append_review_log` removed from `apply_patches`, `OP_ENUM`, the interview skill, and README.<br>2. `apply_patches` raises `ValueError` (unknown op) and `validate_interview_log` raises `ReportValidationError` for both ops.<br>3. CHANGELOG documents the removal. | High |
| US-004 | As a maintainer, I want the persona table format guarded by a test so it cannot silently regress. | 1. `tests/unit/test_personas.py` parses every `ddo/personas/*.md` AV table and asserts structure, ID format/uniqueness, and non-empty columns.<br>2. `uv run pytest` is green. | Medium |

## 5. Technical Specifications

### Architecture & Resolved Trade-offs
- **D1/D2 — category stays free-text, enforced cognitively.** No `ddo/review.py` contract change;
  avoids backward-compat migration of existing reports and a second validation codepath.
- **D7 — AV IDs are per-persona, starting `AV-01`.** No cross-persona coordination.
- **create-persona = interactive Q&A loop** (mirrors `ddo-interview`) — higher-quality output over
  one-pass simplicity.
- **Tests = persona-table structural validation** — since no Python contract changed, the
  "fixture-based ddo-red-team tests" item is realized as a structural test on the persona files
  themselves (they are the fixtures).
- **Deprecation removal folded in** per the locked v0.0.3 decision (RT-v0.0.3-13).

### AV table format (both personas)
```markdown
## Attack Vectors

| ID    | Name                        | When to apply |
|-------|-----------------------------|---------------|
| AV-01 | <snake_case_name>           | <existing probe question> |
```
- **product_critic:** AV-01 `missing_acceptance_criteria`, AV-02 `unsupported_value_claims`,
  AV-03 `scope_creep`, AV-04 `unmeasurable_success`, AV-05 `hedging_language`,
  AV-06 `contradictory_logic`.
- **scientific_reviewer:** AV-01 `methodological_vagueness`, AV-02 `unsupported_assertions`,
  AV-03 `statistical_ambiguity`, AV-04 `overreaching_conclusions`, AV-05 `missing_limitations`,
  AV-06 `result_discussion_bleed`.
- "When to apply" = the existing prose probe verbatim. Other persona sections unchanged.

### `category` contract (cognitive, unchanged in code)
- `ddo-red-team.md` finding-contract row for `category` (≈ line 107): redefine as *"the persona's
  exact `AV-NN: <name>` from its Attack Vectors table (free-text in the schema; consistency
  enforced cognitively)."* Update the §6 example (≈ line 131) to
  `category: "AV-01: missing_acceptance_criteria"`. **No change to `validate_report`.**

### Deprecated-op removal (file:line anchors)
- `ddo/refine.py`: remove `elif op == "append_evidence"` / `"append_review_log"` branches
  (≈ 329-354); remove docstring bullets (≈ 267-269); fix unknown-op message (≈ 437-442) to list
  only `set, append, delete, insert`.
- `ddo/review.py`: drop both from `OP_ENUM` (≈ 37-46) → `{set, append, delete, insert}`; tidy the
  comment at ≈ 349.
- `ddo/skills/ddo-interview.md`: patch-shape `op:` line (≈ 90) → `set | append | delete | insert`;
  remove "Legacy Op Deprecation (v0.0.3)" section (≈ 233-240).
- `README.md` (≈ 153): drop both ops from the supported-ops list. `CHANGELOG.md`: add v0.0.4 entry.

### System Graph Blast Radius
- **Mark dirty:** `ddo_personas`, `skill_red_team`, `skill_interview`, `review_engine`, refine-engine
  node (`ddo/refine.py`).
- **Add nodes:** `skill_create_persona` (Atomic; `associated_file: ddo/skills/ddo-create-persona.md`;
  `implements: [ddo_skills]`; `depends_on: [ddo_personas]`) and `test_personas_unit`
  (per the per-test-file node convention).
- **Run:** `python .agents/scripts/hypergraph_updater.py spec/compiled/architecture.yml <dirty nodes>`.

### Execution Checklist (anticipated MiniPRDs)
- [ ] MiniPRD_Personas — restructure both AV sections to tables.
- [ ] MiniPRD_SkillRedTeam — inject table + bind `category` to `AV-NN: name`.
- [ ] MiniPRD_SkillCreatePersona — new interactive authoring skill.
- [ ] MiniPRD_DeprecationRemoval — `refine.py` + `review.py` + `ddo-interview.md` + README/CHANGELOG
      + minimal tutorial fix (`interview_call.py` sample migration + 2 `tutorial.md` rows).
- [ ] MiniPRD_TestPersonas — new `tests/unit/test_personas.py`.
- [ ] MiniPRD_TestRefineReview — flip legacy-op tests to rejection in `test_refine.py`/`test_review.py`.
- [ ] MiniPRD_Hypergraph — mark dirty, add `skill_create_persona` + `test_personas_unit` nodes, run updater.

### Dependencies
- No new libraries. Python stdlib + existing `pyyaml`. `test_personas.py` parses Markdown tables
  with stdlib `re` (no Markdown parser dependency).

## 6. Negative Constraints
- **DO NOT** add a `category` enum, whitelist, or forbidden-token scan to `ddo/review.py` — D1/D2:
  enforcement is cognitive only.
- **DO NOT** introduce a persona YAML schema or migrate existing `red_team_report_*.yaml` files.
- **DO NOT** use globally-unique AV IDs — per-persona, starting `AV-01` (D7).
- **DO NOT** let `ddo-create-persona` overwrite an existing persona without explicit confirmation,
  or auto-advance past a `[WAITING FOR USER RESPONSE]` / `[WAITING FOR USER REVIEW]` gate.
- **DO NOT** invent persona content — emit `[REQUIRES USER INPUT: <reason>]` when a field can't be
  sourced (zero-hallucination invariant).
- **DO NOT** leave any *functional* reference to the removed ops in `ddo/` (docstrings, enums,
  branches, error strings).

## 7. Risks & Mitigation
- **Risk: Tutorials reference the removed ops.** `code_samples/interview_call.py` (≈ 61) *uses*
  `append_evidence` (invalid after removal); `tutorial.md` (≈ 155-156) labels the ops "removed in
  v0.0.4". → **Mitigation (resolved):** a minimal fix is **in v0.0.4 scope** — migrate the code
  sample and update the two table rows; the full tutorial refresh stays in v0.0.6.
- **Risk: Cognitive enforcement lets `category` drift anyway.** Free-text means the AI could emit a
  malformed category. → **Mitigation:** explicit skill instruction + the example finding; the
  persona-table test guarantees the *source vocabulary* is well-formed even if a given run strays.
- **Risk: Removing ops breaks existing interview logs in the wild.** → **Mitigation:** the migration
  forms (`{op: append, target: "evidence_bank"/"meta.review_log"}`) shipped in v0.0.3; CHANGELOG
  documents the removal; rejection tests make the failure explicit and early.
- **Risk: AV name format ambiguity (snake_case vs Title Case).** → **Mitigation:** standardize on
  snake_case Names; the persona-table test asserts the format.

## 8. Success Metrics
- A Red Team run against either built-in persona emits every finding's `category` as `AV-NN: <name>`
  matching that persona's table.
- `uv run pytest` green: `test_personas.py` passes; the 4 legacy-op tests are replaced by rejection
  tests in `test_refine.py` / `test_review.py`.
- `uv run ruff check .` and `uv run ruff format --check .` exit 0.
- `apply_patches` raises `ValueError` and `validate_interview_log` raises `ReportValidationError`
  for `append_evidence` / `append_review_log`.
- `grep -rn "append_evidence\|append_review_log" ddo/` shows no functional references.
- `ddo-create-persona` produces a valid `ddo/personas/<name>.md` (passes `test_personas.py`).
- `architecture.yml` updated; `skill_create_persona` node present; hypergraph_updater run clean.

---

## Candidate Artifacts (Novel Frontier)
- A persona file produced by `ddo-create-persona` is **AI-generated, non-deterministic** content.
  It must pass through human-in-the-loop review (the skill's `[WAITING FOR USER REVIEW]` gate)
  before being committed to `ddo/personas/`. It is not promoted to `tests/fixtures/` automatically.
- Red Team `category` values remain Candidate Outputs (free-text); the persona-table test pins the
  deterministic source vocabulary they must draw from.
