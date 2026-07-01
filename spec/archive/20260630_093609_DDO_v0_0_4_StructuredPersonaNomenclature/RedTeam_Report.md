# RedTeam Report: DDO v0.0.4 — Structured Persona Nomenclature (+ deprecated-op removal)

> **Phase:** Red Team (adversarial critique of `spec/active/Draft_PRD.md`).
> **Inputs analyzed:** `spec/active/Draft_PRD.md`, `spec/compiled/architecture.yml`, plus
> ground-truth verification against the live tree (personas, skills, `refine.py`, `review.py`,
> `test_personas.py`, tutorials).
> **Verdict:** The PRD is technically precise — **every file:line anchor it cites was verified
> accurate** (`ddo-red-team.md:107/131`, `refine.py:267-268/329-441`, `review.py:43-44`,
> `ddo-interview.md:90/237-238`, `README.md:153`). The defects below are **not** in the
> mechanics; they are in **state assumptions** (a node/file the PRD says to *create* already
> exists), **containment** (a source-tree write that bypasses DDO's safety machinery), and
> **determinism** (markdown escaping vs. raw `category` strings). These must be triaged before
> `/hyper-resolve`.

---

## TOP BLAST-RADIUS FINDINGS (read first)

- **RT-01 — `test_personas_unit` node and `tests/unit/test_personas.py` ALREADY EXIST.** The PRD
  (§3 In-Scope, §5 System Graph Blast Radius, §5 Execution Checklist "new `tests/unit/test_personas.py`")
  instructs the implementer to **add** the node and create a **new** file. Both already exist:
  `architecture.yml` lines 448–463 define `test_personas_unit` (status **clean**,
  `associated_file: tests/unit/test_personas.py`, `depends_on: [ddo_personas]`), and the file is
  present (2187 bytes, dated Jun 29). Adding a node that exists will either be a no-op or a
  duplicate-id corruption depending on `hypergraph_updater` behavior. **Correct action: `mark dirty`
  + rewrite, NOT add.** This is the single highest-severity item in the report.

- **RT-02 — The existing `test_personas.py` is a *smoke test*, not an AV-table validator, and is
  hardcoded to two persona names.** It currently parametrizes over
  `_PERSONA_NAMES = ["product_critic", "scientific_reviewer"]` (line 16) and only checks
  existence / UTF-8 / "has a heading" / frontmatter-parses. US-004 AC1 requires it to "parse **every**
  `ddo/personas/*.md` AV table" (a glob). §8 further requires that a persona produced by
  `ddo-create-persona` "passes `test_personas.py`". A third persona authored by the new skill would
  **never be covered** by the current hardcoded list. The rewrite must switch from the hardcoded
  list to a glob — this is a behavioral change to an existing clean node, not a greenfield file.

- **RT-03 — `ddo/personas/` is OUTSIDE the `Documents/` containment boundary; the new skill's
  overwrite guard is cognitive-only.** Every existing DDO write path (`ddo.ingest.atomic_write`,
  `ddo.paths.assert_within_documents`, the `OverwriteError` guard) is scoped to `Documents/`.
  `ddo-create-persona` writes to `ddo/personas/<name>.md` — a version-controlled **source** tree
  the safety machinery does not cover. §6 forbids overwriting "without explicit confirmation," but
  there is **no mechanical enforcement** — it relies entirely on the agent honoring a prompt. A
  single misfire silently clobbers a hand-authored persona with no atomic temp→replace and no
  `OverwriteError`.

---

## 1. Introduction & Goals — Analysis

* **Clarifying Questions:**
  - The problem statement says ad-hoc categories "cannot be referenced or **aggregated**." D7
    (§3, §6) makes AV IDs **per-persona, AV-01-based**, so `AV-01` denotes a *different* vector in
    `product_critic` vs `scientific_reviewer`. Does "aggregation" mean *within a single persona's
    runs* (which this solves) or *across personas* (which it does not — the `AV-NN` prefix collides
    and only the full `AV-NN: <name>` string disambiguates)? If the latter is a real goal, the design
    does not meet it.
  - "Consistency is enforced **cognitively, not mechanically**" — what is the acceptance bar for
    "enforced"? With `category` free-text and no validation gate, the only artifact that can *fail*
    is the persona table itself (via `test_personas.py`). Is a drifted `category` in a generated
    report considered a defect, a no-op, or out of scope?

* **What-If Scenarios:**
  - A report generated **before** v0.0.4 (free-text `category: "Missing Evidence"`) is re-opened by
    `ddo-interview` *after* v0.0.4 ships. The Interview/Refine phases now coexist with two category
    vocabularies in the same document's history. Nothing migrates the old reports (correctly — D1/D2),
    but the stated benefit ("stable vocabulary for downstream Interview/Refine") is only realized for
    **new** reports. Confirm this partial rollout is acceptable.
  - The AI emits a `category` that *looks* like the format but uses a stale/typo'd name
    (`"AV-01: missing_accept_criteria"`). Because enforcement is cognitive and `category` is free-text,
    this passes every gate. The downstream consumer that "references" categories now has a silent
    dangling reference with no detector.

* **Points for Improvement:**
  - State explicitly in the goals whether cross-persona aggregation is in or out; if out, soften the
    problem statement so "aggregated" doesn't over-promise relative to the D7 design.
  - Add a (cheap, advisory) NFR: `ddo-red-team` should *echo the active persona's AV table back* in
    the report header (or a comment), so a human auditing a report can resolve `AV-NN` to a name
    without opening the persona file — closing the "referenceable" loop deterministically.

## 2. Confidence Mandate — Analysis

* **Clarifying Questions:**
  - The mandate claims **10/10** confidence and "Current-state file/line anchors verified." Yet §3/§5
    direct the implementer to *create* an artifact that already exists (RT-01). A 10/10 with a
    falsifiable state error suggests the verification covered code anchors but **not** the
    architecture graph or the `tests/unit/` directory listing. Should confidence be revised down until
    RT-01/RT-02 are reconciled?
  - "AV Name casing = snake_case" is locked — but the source personas render names in **escaped
    Title-Case markdown** (`**Missing Acceptance Criteria:**`, and underscores are escaped elsewhere
    as `evidence\_bank`). Was the *table-cell encoding* of snake_case names (raw `_` vs escaped `\_`)
    decided? See RT-04.

* **What-If Scenarios:**
  - "Derived fact: there is no persona registry — `ddo-red-team` resolves a persona by name and reads
    the file directly." If true, persona discovery is a directory glob. A malformed new persona
    (created by `ddo-create-persona`) is then discoverable and selectable by `ddo-red-team`
    *before* a human has reviewed it, unless the skill writes only after its HITL gate. Confirm the
    write happens **after** `[WAITING FOR USER REVIEW]`, not before.

* **Points for Improvement:**
  - Downgrade the "Current-state … verified" claim to scope it honestly: "code anchors verified;
    architecture graph and `tests/unit/` state must be re-checked in resolve" — or fix RT-01/RT-02 in
    the PRD and *keep* 10/10.

## 3. Scope — Analysis

* **Clarifying Questions:**
  - In-Scope says "**New** `tests/unit/test_personas.py`." It is not new (RT-01/RT-02). Should this
    line read "**Rewrite** `tests/unit/test_personas.py` (replace the RT#12 smoke test with AV-table
    structural validation; switch hardcoded `_PERSONA_NAMES` to a `*.md` glob)"?
  - Out-of-Scope rejects "a persona YAML schema or machine-enforced category whitelist." But US-004
    asks the *test* to assert ID format/uniqueness/non-empty columns — that is a machine-enforced
    **persona-table** schema (on the source), distinct from a **category** whitelist (on reports). Is
    the boundary "validate the source vocabulary, never the report values"? Make that explicit so the
    implementer doesn't accidentally add report-side validation.

* **What-If Scenarios:**
  - The tutorial-fix scope is pinned to exactly two artifacts (`interview_call.py` + `tutorial.md`
    rows 155-156). Ground-truth grep shows **more** live references to the removed ops in the same
    tutorial tree: `interview_call.py:41` (comment `add_evidence -> append_evidence`) and
    `audit_2026-06-30.md` (lines 22-43, 116-117, including a literal `op: append_evidence` example at
    line 33). If "minimal fix" stops at two files, the tutorial still contains stale op references —
    re-opening RT-v0.0.3-13's "leaves no functional reference" intent for the tutorial layer.

* **Points for Improvement:**
  - Either (a) widen the minimal tutorial fix to include `interview_call.py:41` and explicitly mark
    `audit_2026-06-30.md` as a frozen historical record (out of scope by design), or (b) add a
    success-metric grep `grep -rn "append_evidence\|append_review_log" tutorials/` and document the
    *expected* surviving matches so the v0.0.6 full-refresh has a known baseline.

## 4. User Stories — Analysis

* **Clarifying Questions:**
  - US-002 AC2: "elicits all **six** persona sections including a well-formed AV table (sequential,
    unique IDs)." Are the **six sections** fixed (Domain, Reviewing Mission, Attack Vectors, Severity
    Taxonomy, Domain-Specific Format Rules, Interview Question Templates — matching the two built-ins)?
    And is the AV **count** fixed at 6, or variable? The built-ins both have exactly 6 AVs; the test
    must not hardcode 6 if create-persona allows variable counts.
  - US-004 AC1 asserts "ID format/uniqueness, and non-empty columns" — does it also assert **AV-name
    uniqueness** within a persona? Two AVs sharing a snake_case name make `AV-NN: <name>` non-unique
    on the name axis and reintroduce the ambiguity this feature exists to remove.

* **What-If Scenarios:**
  - US-002: a user runs `ddo-create-persona` and names the new persona `product_critic` (collision
    with a built-in). With only cognitive overwrite protection (RT-03), the built-in is at risk.
  - US-003 AC2 requires `apply_patches` to raise `ValueError` (unknown op) **and**
    `validate_interview_log` to raise `ReportValidationError`. Order matters: in the live pipeline,
    does `validate_interview_log` run *before* `apply_patches`? If validation rejects the op first,
    the `apply_patches` `ValueError` path becomes unreachable in production and is only exercised by a
    direct unit test. Confirm both are independently reachable so neither rejection silently rots.

* **Points for Improvement:**
  - Add an explicit acceptance criterion to US-002: "writes the persona file **only after** the
    `[WAITING FOR USER REVIEW]` gate, and refuses to write if `ddo/personas/<name>.md` exists unless
    the user re-confirms with the literal filename." Pin the guard behavior, since no mechanical guard
    backs it (RT-03).
  - Add to US-004: assert AV-name uniqueness and a strict snake_case charset (`^[a-z][a-z0-9_]*$`,
    no leading digit, no `__`, no trailing `_`).

## 5. Technical Specifications — Analysis (incl. System Graph Blast Radius)

* **Clarifying Questions:**
  - **AV-table cell encoding (RT-04):** The persona files escape markdown underscores (`evidence\_bank`,
    `product\_critic`). If the snake_case AV name is written into the table cell as
    `missing\_acceptance\_criteria` (to match house style), but `ddo-red-team` must emit
    `category: "AV-01: missing_acceptance_criteria"` (raw underscores, per §5 example), then the
    string the AI *reads from the table* differs from the string it must *emit*. Which is canonical?
    The `test_personas.py` regex must then either forbid escaped underscores in the Name column or
    normalize `\_`→`_` before asserting format. Specify this; it is a determinism trap.
  - **"When to apply" = existing probe verbatim:** the current probes are long prose containing commas,
    parentheses, and `?`. None currently contain a literal `|`, but the format mandates a Markdown
    table where `|` is the column delimiter. What is the rule if a future probe contains `|`
    (must it be escaped `\|`)? The stdlib-`re` parser (no markdown library, per §5 Dependencies) must
    handle escaped pipes or the spec must forbid `|` in probe text.
  - **`skill_create_persona` node edges:** §5 specifies `depends_on: [ddo_personas]` and
    `implements: [ddo_skills]`. Every *other* ddo skill node depends on `ddo_core` (e.g.
    `skill_red_team` → `review_engine`). If create-persona writes a file with **no** `ddo_core`
    dependency, that is consistent with RT-03 (it bypasses safe-write machinery) — is that the intent,
    or should it depend on a (new or existing) safe-write helper?

* **What-If Scenarios:**
  - **Backward-incompatible persona contract (RT-05):** After this change, `ddo-red-team` "injects the
    table and binds `category` to `AV-NN`." A persona authored under v0.0.3 (or any custom persona)
    that still uses the **numbered-list** Attack Vectors format (which is exactly what both built-ins
    look like *today*, pre-change) has no `AV-NN` table to inject. Does `ddo-red-team` hard-fail,
    fall back to free-text, or silently emit malformed categories? The PRD converts the two built-ins
    but specifies **no migration path or fallback** for personas not in this repo.
  - **Hypergraph corruption (RT-01 mechanics):** running `hypergraph_updater.py` with
    `test_personas_unit` passed as a node to *add* while it already exists — does the updater upsert
    (safe) or append a duplicate `id` (graph now has two `test_personas_unit` nodes, breaking every
    downstream `depends_on` resolution)? This must be confirmed against the updater's actual behavior
    before resolve.
  - **`OP_ENUM` shrink vs. in-the-wild logs:** removing `append_evidence`/`append_review_log` from
    `review.py:OP_ENUM` (line 43-44) means `validate_interview_log` now *rejects* any historical
    `interview_log_vN.yaml` that still carries those ops. The integration fixture
    `tests/fixtures/loop/interview_log_v1.yaml` was migrated in v0.0.3 per the CHANGELOG — but is
    there any *other* committed `interview_log` (in `Documents/`, tutorials `output_files/`, or test
    fixtures) that would now fail validation on replay? §5 does not enumerate a grep for committed
    `interview_log` files carrying the old ops.

* **Points for Improvement:**
  - **Fix the Blast Radius ledger:** change "Add nodes: … `test_personas_unit`" to "**Mark dirty:**
    `test_personas_unit`" and keep only `skill_create_persona` under "Add nodes." Add `skill_create_persona`'s
    sibling considerations: should `ddo_skills` (the module node) description be regenerated to mention
    the sixth skill? Marking it dirty would trigger that.
  - Add `tutorials_*` (the tutorial tree) to the dirty/affected set if the tutorial fix lands, so the
    hypergraph reflects the touched tutorial node (if one exists) — or note explicitly that tutorials
    are unmodeled in the graph.
  - Specify the canonical snake_case-in-cell encoding (raw `_`, no `\_`) and add it as a `test_personas.py`
    assertion, resolving RT-04 deterministically.
  - Add a fallback/contract clause to `ddo-red-team`: "if the resolved persona has no `## Attack Vectors`
    table, hard-fail naming the persona (mirroring the existing missing-file hard-fail), rather than
    emitting free-text categories." This makes RT-05 fail loud, early, and consistent with the skill's
    existing fail-closed posture.

## 6. Negative Constraints — Analysis

* **Clarifying Questions:**
  - "DO NOT leave any **functional** reference to the removed ops in `ddo/`." The success-metric grep
    (§8) is scoped to `ddo/` only. Is `README.md:153` (a *documentation* reference outside `ddo/`)
    covered by US-003 AC1 ("removed from … README")? Yes per US-003 — but confirm the §8 grep is
    intentionally narrower than the removal scope, so the implementer doesn't think a clean
    `grep … ddo/` means "done."
  - The constraints forbid a `category` enum/whitelist in `review.py`. Does that prohibition also bind
    `test_personas.py`? It must not — the test validates the **persona source table**, not report
    `category` values. Make the asymmetry explicit so the constraint isn't over-applied to the test.

* **What-If Scenarios:**
  - "DO NOT invent persona content — emit `[REQUIRES USER INPUT: <reason>]`." A persona file written
    with `[REQUIRES USER INPUT: …]` sentinels in its AV-table cells would then be *read by
    `ddo-red-team`* as a live persona. Does a persona containing unresolved sentinels pass
    `test_personas.py`? If "non-empty columns" is the only check, a sentinel is non-empty and passes —
    a half-authored persona becomes silently usable. Should the test (or the skill's gate) reject
    sentinel tokens in committed personas, mirroring the `validation_gate` sentinel scan?

* **Points for Improvement:**
  - Add a negative constraint: "`ddo-create-persona` MUST NOT commit a persona file containing
    `[REQUIRES USER INPUT:` / `[[DDO::REQUIRES_INPUT:` sentinels," and have `test_personas.py` assert
    sentinel-absence — reusing the existing zero-hallucination tripwire pattern for the source tree.

## 7. Risks & Mitigation — Analysis

* **Clarifying Questions:**
  - The "tutorials reference removed ops" risk lists `interview_call.py:61` and `tutorial.md:155-156`
    but **omits** `interview_call.py:41` (the explanatory comment) and the entire
    `audit_2026-06-30.md`. Is the residual-reference set after the "minimal fix" intentional, and is it
    documented anywhere the v0.0.6 refresh will look?
  - "tutorial.md … update the two table rows" — update them to **what**? Delete the rows, or reword
    "removed in v0.0.4" to a past-tense "removed (use `{op: append, target: …}`)"? The instruction is
    ambiguous; pick one so the result is deterministic and ruff/markdown-lint stable.

* **What-If Scenarios:**
  - The "cognitive enforcement drifts anyway" risk is mitigated by "the example finding + the
    persona-table test guarantees the *source vocabulary*." But the test does **not** see report
    output, so it cannot catch a drifted `category` at runtime — the mitigation guarantees the menu is
    well-formed, not that the waiter reads from it. Acknowledge that residual runtime drift is
    *accepted*, not *mitigated*.
  - The "removed ops break logs in the wild" risk asserts the migration form shipped in v0.0.3. The
    rejection tests make failure "explicit and early" — but only for logs that flow through
    `validate_interview_log`. A `refine` replay that calls `apply_patches` on a hand-edited log that
    skipped validation hits the `ValueError` path instead. Confirm both error surfaces are tested
    (this ties to US-003 AC2 and RT under §4).

* **Points for Improvement:**
  - Add a risk row: "**Source-tree write bypasses containment** (RT-03) — `ddo-create-persona` writes
    outside `Documents/`, so atomic-write/overwrite guards do not apply. Mitigation: write via a
    temp→`os.replace` helper with an explicit `exists()` pre-check, or reuse `ddo.ingest.atomic_write`
    pointed at `ddo/personas/` with `force=False`."
  - Add a risk row for RT-04 (escaped-underscore determinism) with the chosen canonical encoding as
    its mitigation.

## 8. Success Metrics — Analysis

* **Clarifying Questions:**
  - "the **4 legacy-op tests** are replaced by rejection tests in `test_refine.py` / `test_review.py`."
    Ground truth: all four live in `test_refine.py` (lines 226, 245, 263, 390); a grep of `tests/`
    finds **zero** op-named tests in `test_review.py`. So a `test_review.py` rejection test would be
    **new**, not a "replacement." Is the intended count "flip 4 in `test_refine.py` **and add** N new
    rejection tests in `test_review.py`," or "flip 4 total, some of which move to `test_review.py`"?
    The "4 … replaced" phrasing under-counts the `test_review.py` additions.
  - The metric `ddo-create-persona` "produces a valid `ddo/personas/<name>.md` (passes
    `test_personas.py`)" is only meaningful **after** RT-02 (glob migration). As written against the
    current hardcoded-list test, a newly created `<name>.md` is *not even loaded* by the test. Gate
    this metric on the glob rewrite.

* **What-If Scenarios:**
  - `grep -rn "append_evidence\|append_review_log" ddo/` returning empty is necessary but not
    sufficient: it would still pass while `README.md`, `tutorials/`, and `CHANGELOG.md` (historical
    entries, correctly retained) carry the strings. A reviewer trusting only the `ddo/` grep could
    declare done with the tutorial code sample still broken (`interview_call.py` is under
    `tutorials/`, not `ddo/`). Add an explicit `tutorials/` grep with an allow-list of expected
    historical matches.

* **Points for Improvement:**
  - Replace "4 legacy-op tests are replaced" with the verified accounting: "remove/flip
    `test_apply_patches_append_evidence` (226), `…_append_review_log_creates_list` (245),
    `…_append_review_log_extends_existing` (263), `…_append_evidence_non_dict_raises` (390) in
    `test_refine.py`; **add** rejection tests asserting `validate_interview_log` raises
    `ReportValidationError` for both ops in `test_review.py`."
  - Add a metric: "`hypergraph_updater` run leaves exactly one `test_personas_unit` and one
    `skill_create_persona` node (no duplicate ids)" — directly guarding RT-01.

## Candidate Artifacts (Novel Frontier) — Analysis

* **Clarifying Questions:**
  - A persona produced by `ddo-create-persona` is "AI-generated, non-deterministic content" passing
    through a HITL gate before commit to `ddo/personas/`. But `ddo/personas/` is **source**, not
    `Documents/`/`candidate_outputs/`. What prevents an un-reviewed persona from being committed and
    then *read by `ddo-red-team` as authoritative* on the next run? The Candidate-Artifact protocol
    elsewhere keys off `tests/fixtures/` sign-off; there is no analogous gate for `ddo/personas/`.

* **What-If Scenarios:**
  - The note says the generated persona "is not promoted to `tests/fixtures/` automatically." Good —
    but it **is** immediately live to `ddo-red-team` once on disk. The novel-frontier risk is not
    "promotion to fixtures"; it is "a non-deterministic artifact becoming a deterministic *input* to
    the adversarial loop." That is the artifact boundary that needs a guard.

* **Points for Improvement:**
  - Treat a freshly created persona as Candidate until `test_personas.py` passes **and** a human
    review marker is recorded; document how `ddo-red-team` should behave if asked to use a persona
    that has not cleared that bar (hard-fail vs. warn).

---

## Consolidated Triage Table (for `/hyper-resolve`)

| ID | Severity | Section | Finding |
|---|---|---|---|
| RT-01 | **Critical** | §3/§5 | `test_personas_unit` node **and** `tests/unit/test_personas.py` already exist; PRD says "add/new." Change to "mark dirty + rewrite." Guard against duplicate node id. |
| RT-02 | **Critical** | §3/§5/§8 | Existing `test_personas.py` is an RT#12 smoke test hardcoded to two names; US-004/§8 require a `*.md` glob AV-table validator. Must rewrite, not create. |
| RT-03 | **Major** | §5/§6/§7 | `ddo/personas/` is outside `Documents/` containment; create-persona overwrite guard is cognitive-only. No atomic write / `OverwriteError`. |
| RT-04 | **Major** | §5 | Persona files escape `_` (`evidence\_bank`); snake_case AV names in table cells vs raw `_` in emitted `category` → read≠emit determinism trap. Pin canonical encoding + test it. |
| RT-05 | **Major** | §5 | `ddo-red-team` now assumes every persona has an `AV-NN` table; no fallback/migration for personas still in the legacy numbered-list format (which is today's built-in format). Specify hard-fail. |
| RT-06 | **Minor** | §5 | "When to apply" = verbatim probe in a Markdown table cell; `|` would break the stdlib-`re` parser. Forbid/escape `|` in probe text. |
| RT-07 | **Minor** | §8 | "4 legacy-op tests replaced in `test_refine.py`/`test_review.py`" — all 4 are in `test_refine.py`; `test_review.py` rejection tests are net-new. Fix the accounting. |
| RT-08 | **Major** | §3/§7 | Minimal tutorial fix omits `interview_call.py:41` comment and all of `audit_2026-06-30.md` (incl. `op: append_evidence` at line 33). Decide residual-reference policy + add `tutorials/` grep. |
| RT-09 | **Minor** | §7 | tutorial.md rows 155-156 "update" is ambiguous (delete vs reword). Specify. |
| RT-10 | **Minor** | §1/§3 | Per-persona AV-01 IDs collide across personas; "aggregation" goal only met within a persona. Align goal language with D7. |
| RT-11 | **Minor** | §1/§5 | Pre-v0.0.4 reports keep free-text categories; "stable vocabulary for downstream" only holds for new reports. Acknowledge partial rollout. |
| RT-12 | **Minor** | §5 | `skill_create_persona` has no `ddo_core` dependency unlike every other ddo skill node — consistent with RT-03 (no safe-write reuse). Decide intent. |
| RT-13 | **Major** | §6/§8 | A persona with `[REQUIRES USER INPUT:` sentinels passes "non-empty columns"; becomes silently usable. Add sentinel-absence assertion. |
| RT-14 | **Minor** | §5 | `validate_interview_log` shrink may reject *other* committed `interview_log` files carrying old ops. Enumerate via grep before removal. |
| RT-15 | **Minor** | §4/§8 | Confirm both `apply_patches` `ValueError` and `validate_interview_log` `ReportValidationError` paths are independently reachable (ordering) and tested. |

---

**Final Action:** Report saved to `spec/active/RedTeam_Report.md`. Run **`/hyper-resolve`** to triage
these findings — start with **RT-01/RT-02** (the "add vs. rewrite" state error), then **RT-03/RT-04**
(containment + determinism) before any MiniPRD is compiled.

[WAITING FOR USER REVIEW]
