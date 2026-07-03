# RedTeam_Report.md — DDO v0.0.6 (Expanded Ecosystem Tutorials)

> **Target:** `spec/active/Draft_PRD.md` (SuperPRD DRAFT, Phase 1 Architect output).
> **Blast-radius basis:** `spec/compiled/architecture.yml` (28 clean nodes) + on-disk ground truth verified during this pass.
> **Verdict:** The design is coherent and correctly scoped as domain-files-only. However, the anti-rot guard — the single new piece of *enforcement* the whole PRD leans on — is under-specified and its stated scope contradicts Tutorial 1's anchor location. Several "CI-enforced" acceptance criteria have **no test surface** in the current repo. The zero-hallucination contract collides with casual document types in a way the Confidence Mandate waved through. Findings below are ID'd `RT-NN` for `/hyper-resolve` triage.

**Ground-truth checks performed this pass:**
- `tutorials/ddo-v001-prd-workflow/input_files/prd_example.yaml` **is** byte-identical to `tests/data/prd_example.yaml` (convention confirmed real).
- `tutorials/ddo-adversarial-loop-v0.0.2/input_files/document_data.yaml` mirrors **nothing** in `tests/data/` or `tests/fixtures/` (unique md5) — the "input_files copies a fixture" convention is **not universal**.
- `EXAMPLES` is defined **twice** — `tests/integration/conftest.py:16` **and** `tests/integration/test_render_determinism.py:19` — as two independent literals.
- `ddo/validation.py:106` — `if len(sections) == 0 or total_refs == 0: raise ValidationError`. **Zero evidence references is a hard failure.**
- `pyproject.toml:9` — ruff `exclude = ["PRDs/"]` only; `tutorials/` **is** linted (currently green).
- No test in `tests/` cross-checks `meta.persona` / `meta.style_profile` against files on disk.

---

## 1. Introduction & Goals — Analysis

* **Clarifying Questions:**
  1. The Primary Value Loop is *"a user follows a tutorial and successfully executes a complete DDO workflow against a real, regression-tested fixture."* Which of the three tutorials actually delivers an **end-to-end pipeline execution** for the newcomer? Tutorial 1 (evidence lens) and Tutorial 3 (persona authoring) are read/inspect flows; Tutorial 2 renders. Is the "complete workflow" claim honest for all three, or only Tutorial 2?
  2. The stated problem is "unapproachable to a newcomer." What is the **acceptance signal** that approachability improved — is there any measure beyond "files exist and CI is green" (which US-006/007 cover but say nothing about pedagogy)?

* **What-If Scenarios:**
  - **Reproducibility drift the user hits first.** A newcomer runs the render command in Tutorial 2 and compares to the committed `output_files/*.html|md`. If those committed renders drift from what `build.py` now produces (no guard proposed for `output_files/` — see RT-07), the *first thing the tutorial promises* (reproducibility) visibly fails on step one. The value loop breaks at the most credibility-sensitive moment.
  - **"Real, regression-tested fixture" is only true post-promotion.** M1/M2/M3 cover render determinism, but the *golden baseline* (`tests/fixtures/`) is human-gated (`DDO_FIXTURE_SIGNOFF=1`) and explicitly deferred (§3 Out-of-Scope). Until a human signs off, the fixtures the tutorials anchor to are *determinism-tested* but not *regression-baselined*. The intro overstates the guarantee for the shipped-but-unsigned state.

* **Points for Improvement:**
  - Add an explicit, per-tutorial column: *"pipeline stages exercised"* and *"CI coverage vs. HITL-only."* Right now the intro's single value-loop sentence papers over the fact that two of three tutorials never run the pipeline.
  - Define one falsifiable approachability signal (e.g., a fresh clone + `uv run` of the exact command block in Tutorial 2 producing exit 0), even if only a manual gate, so "approachable" is not purely subjective.

---

## 2. Confidence Mandate — Analysis

* **Clarifying Questions:**
  1. Q5 asks whether the minimal contract is "retained unchanged for all four" and recommends *yes*. But retaining it **forces every type to carry ≥1 evidence reference** (`validation.py:106` raises on `total_refs == 0`). Was it understood that a `blog_post` and `meeting_notes` example **cannot** be evidence-free and still validate? Where does a `meeting_notes` example's evidence *trace back to* under zero-hallucination (RT-04)?
  2. Q1 (token budget) is deferred to `/hyper-resolve` — but the split decision changes the **dependency ordering** of MiniPRDs (personas/styles must precede doc-type YAMLs that reference them). Is the ordering in §5's Execution Checklist load-bearing, or advisory?
  3. Confidence is 8/10 with "exact per-schema section shapes" listed as a *remaining unknown* (Q2). Schema section shape is the substance of half the deliverable. An 8/10 with the core artifact shape unresolved reads high — what would drop it to 6?

* **What-If Scenarios:**
  - **The self-declared unknowns are the load-bearing ones.** All three open questions (budget split, section shapes, Tutorial-1 framing) gate execution correctness. If `/hyper-resolve` defers them again, execution starts on sand.
  - **Q4 answered against the wrong scope.** Q4 recommends byte-equality between `input_files/*.yaml` and its **`tests/data/`** source. Tutorial 1's anchor (`tests/fixtures/ingest_output.yaml`) lives in **`tests/fixtures/`**, not `tests/data/`. The recommendation, as written, does not cover Tutorial 1 at all (see RT-01).

* **Points for Improvement:**
  - Resolve Q5 into an explicit statement: *"casual types carry a minimal but genuine evidence_bank; example evidence is sourced from the tutorial's own narrative source file, not invented"* — and point each casual example's evidence at a real `input_files/` source doc, exactly as the adversarial-loop tutorial does with `copolyester-optimization.md`.
  - Fold the three "open for Resolve" items into hard pre-conditions on the corresponding MiniPRDs so they cannot be silently deferred.

---

## 3. Scope — Analysis

* **Clarifying Questions:**
  1. **Anti-rot guard reference-extraction mechanism (the central unknown).** `test_tutorial_refs.py` must "enumerate tutorial-referenced paths." *How?* (a) Regex path-like tokens out of `tutorial.md` prose? (b) A hand-maintained manifest per tutorial? (c) Only `os.walk` of each `input_files/`? Each has failure modes: prose-regex yields false positives (illustrative paths) and false negatives (paths not in backticks); a manifest is itself a drift surface. The PRD never says — and this determines whether the guard is robust or theatre. **(RT-02)**
  2. **Byte-equality pairing rule.** Given `input_files/document_data.yaml` mirrors *no* `tests/data/` file, how does the guard decide which `input_files/*.yaml` should be byte-compared to which source? By basename against `tests/data/`? Then Tutorial 1's `ingest_output.yaml` (source in `tests/fixtures/`) is silently skipped → the drift it exists to catch goes undetected (**RT-01**). By an explicit map? Then the map is the drift surface.
  3. `EXAMPLES` must be edited in **both** `conftest.py` and `test_render_determinism.py`. These are **two independent literals today** (verified). Why not consolidate to one source and import, instead of institutionalizing a two-place edit that silently under-covers if they diverge? **(RT-03)**
  4. Out-of-Scope says "no Python module changes." But `EXAMPLES` enrollment *is* editing test-module Python, and `test_tutorial_refs.py` is new Python. Confirm "no Python module changes" means **`ddo/*.py` only**, not `tests/*.py` (the wording in §6 says `ddo/*.py`, but §3's blanket phrasing is looser).

* **What-If Scenarios:**
  - **Ungated replica of a human-gated fixture.** Tutorial 1 copies `tests/fixtures/ingest_output.yaml` (protected by `fixture_signoff_guard.py`, RT#13) into `input_files/`. The copy lives under `tutorials/`, which is **not** gated by `DDO_FIXTURE_SIGNOFF`. An agent can freely author/edit that copy — creating a second, *ungated* replica of ground-truth data whose whole point was to be human-authored-only. The byte-equality guard then only enforces *sameness*, not *provenance*: an agent could edit **both** the copy and (if signed) the fixture and the guard stays green. **(RT-05)**
  - **Casual `blog_post` with empty `evidence_bank` fails render.** If an author writes the "casual" example the way a real blog reads (no citations), `build.py` exits non-zero (`total_refs == 0`). US-004 AC3 ("passes M1/M2/M3/M3b") then fails and the failure looks like a determinism bug, not a contract requirement. **(RT-04)**
  - **New tutorial `code_samples/*.py` breaks the ruff gate.** `tutorials/` is *not* excluded from ruff. A pedagogical snippet (partial code, `...` elisions, unused imports for illustration) will fail `uv run ruff check .` / `format --check`, sinking US-007 — and authors will be tempted to *exclude* `tutorials/` from ruff to fix it, silently dropping the *existing* tutorials' code from lint coverage. **(RT-06)**

* **Points for Improvement:**
  - **Specify the guard precisely in-scope:** define reference discovery as *walk `input_files/` only* (no prose parsing) + an explicit, in-repo `EXPECTED_MIRRORS` mapping `{tutorial_input_path: source_path}` covering **both** `tests/data/` and `tests/fixtures/`. Assert (a) every mapped source exists, (b) byte-equality, (c) every `input_files/*.yaml` is either in the map or explicitly marked standalone (so a new drift-prone copy can't be added without a decision). This kills RT-01, RT-02, and RT-05's silent-green paths.
  - Consolidate `EXAMPLES` to a single module-level definition imported by both test files; add a guard test asserting the two are equal if consolidation is rejected. **(RT-03)**
  - Decide RT-06 explicitly: either (a) constrain all tutorial `code_samples/*.py` to be ruff-clean runnable snippets (recommended — matches the existing `render_commands.sh`/`*_call.py` precedent, already green), or (b) if elision is needed, use `# noqa`/`# fmt: off` locally rather than excluding the directory.

---

## 4. User Stories (Atomic) — Analysis

* **Clarifying Questions:**
  1. **US-005 AC3** — "each schema's `meta.persona`/`meta.style_profile` resolve to the new files." *No test in the repo checks this.* `validation.py` treats persona as optional and never checks file existence; the persona/style stem-validation lives only in the **cognitive** skills (`ddo-red-team`, `ddo-ingest`, `ddo-interview`), which CI does not run. How is AC3 *verified* rather than asserted? **(RT-08)**
  2. **US-006 AC1** — "enumerates tutorial-referenced paths and fails if any is missing." Same unresolved mechanism as RT-02. What counts as a "referenced path"?
  3. **US-001 AC3** — Tutorial 1 "framed as a citation-integrity lens, not a duplicate." This is a *prose-quality* assertion. It cannot be CI-checked and there's no reviewer sign-off artifact named. Who adjudicates "not a duplicate," and against what rubric?

* **What-If Scenarios:**
  - **Silent-green AC3.** A doc-type example YAML sets `meta.persona: content_edtior` (typo). Renders fine (persona never read at render time), CI green, US-004 passes. The *only* place the typo surfaces is a human running the Red Team skill later — outside CI. The worked example ships broken. **(RT-08)**
  - **US-004 vs US-005 ordering hazard.** US-004 (types render) and US-005 (personas/styles exist) are separate stories. If executed out of order, US-004's example YAMLs reference not-yet-authored personas — harmless at render time (masking the gap) but leaving a dangling ref that no test catches. The masking is the danger.

* **Points for Improvement:**
  - Add an explicit acceptance test (extend `test_tutorial_refs.py` or a new `test_schema_meta_refs.py`): for every `ddo/schemas/*.yaml` and every `tests/data/*.yaml`, assert `meta.persona` → `ddo/personas/<stem>.md` exists and `meta.style_profile` → `ddo/styles/<stem>.md` exists. This makes US-005 AC3 and the ordering hazard CI-enforced instead of hope-based.
  - Convert US-001 AC3 into a concrete, checkable criterion (e.g., "Tutorial 1 contains zero `ddo-refine`/`ddo-interview` command invocations; it links to the loop tutorial rather than re-walking it") so "not a duplicate" is falsifiable.

---

## 5. Technical Specifications — Analysis

* **Clarifying Questions:**
  1. **Determinism of `output_files/` renders.** §5 says "the pipeline is dogfooded by the four example docs and the `output_files/` renders." Are the committed `output_files/*.html|md` for the new tutorials asserted byte-identical to a fresh `build.py` render? Nothing in the blast radius adds such a guard. If not, they are unguarded and will rot. **(RT-07)**
  2. **`meeting_agenda` / `meeting_notes` time semantics.** Agenda items are "time-boxed"; notes have "next_steps." Do any templates compute durations, "today," or relative times? Any `now()`-style call defeats M3b timestamp-determinism. Confirm all four templates are pure functions of the YAML (no clock/locale reads). **(RT-09)**
  3. **Schema ↔ example binding.** Nothing binds an example YAML's sections to its schema's declared section list (`hook`, `context`, …). `validation.py` checks the *contract* (`meta` + `evidence_bank` + ≥1 evidence ref), not the schema's section names. What guarantees the `blog_post` *example* actually demonstrates the `blog_post` *schema* it teaches? **(RT-10)**
  4. **12 templates × format-parity.** `meeting_notes`/`meeting_agenda` in **PDF** (Typst) — is a Typst layout genuinely meaningful for a one-page agenda, or is PDF parity being paid purely to keep the `EXAMPLES × [pdf,html,md]` cross-product clean? What's the maintenance cost of 4 new Typst templates that no user would realistically render?

* **What-If Scenarios:**
  - **Integration-suite runtime triples.** `EXAMPLES` goes 2 → 6; every M1/M2/M3/M3b test is parametrized over `EXAMPLES × formats`, each a `uv run --locked` **subprocess** render (PDF tests render **multiple times** for wall-clock/timestamp determinism). This ~3× the subprocess count with no stated per-suite time budget. On a cold `uv` cache or CI runner, the suite may approach or exceed CI timeouts even though each render honors its own 30s cap. **NFR the Architect missed: integration-suite wall-clock budget.** **(RT-11)**
  - **Typst PDF non-determinism from a new font/glyph.** A casual type (emoji in a blog hook, an em-dash, a non-ASCII attendee name) can pull a glyph whose Typst rendering isn't in the pinned font set, breaking M3 byte-identity in a way the two formal examples never exercised. The new *casual register* is exactly where font-coverage assumptions break. **(RT-12)**
  - **`EXAMPLES` divergence.** A future contributor adds a 5th type to `conftest.py` only. `test_render_determinism.py`'s own `EXAMPLES` (line 19) is unchanged, so the new type gets `render_fixture` support but **zero determinism assertions** — green suite, uncovered type. **(RT-03, realized)**

* **Points for Improvement:**
  - Add an `output_files/` determinism guard (or explicitly declare `output_files/` illustrative-only and drop the "dogfooded by output_files renders" claim). Pick one; don't ship the ambiguity. **(RT-07)**
  - Add a schema-conformance assertion binding each `tests/data/*.yaml` to the section-id set its schema declares (even a soft "sections are a subset/superset" check), so the worked example provably teaches its schema. **(RT-10)**
  - State a per-suite integration time budget and, if needed, gate the full `EXAMPLES × formats × determinism` cross-product behind a marker so the default `pytest` run stays fast while CI runs the full matrix. **(RT-11)**
  - Add one deliberately non-ASCII fixture value (an accented name) to at least one casual example to force the font-coverage question *now*, at fixture-authoring time, not in a user's first render. **(RT-12)**
  - **Blast-radius gap:** §5 lists `ddo_schemas`/`ddo_templates`/`ddo_personas`/`ddo_styles`/`render_fixture`/`test_render_determinism`/`tests_unit`/`tests_integration` → `needs_review`, but **not** `ddo_core` or `ddo_skills`, whose node descriptions hard-code *"prd/scientific_report × pdf/html/md"* (`ddo_templates` desc) and *"(prd.yaml, scientific_report.yaml)"* (`ddo_schemas` desc). Those enumerations become stale on adding 4 types. Confirm the descriptions are updated (they are inside `ddo_schemas`/`ddo_templates`, which *are* flagged — good — but double-check `ddo_core`'s prose doesn't also enumerate types).

* **Points for Improvement (graph modeling):**
  - The `tutorials` node is declared `implements: ddo_system`. Tutorials are meta-documentation *about* the system, not an implementation of the pipeline — per CLAUDE.md's toolchain-framing discipline this edge is arguably wrong (closer to a doc/reference dimension). Confirm the intended semantics before `hypergraph_updater.py` bakes it in.
  - Three tutorial naming schemes now coexist: `ddo-v001-prd-workflow`, `ddo-adversarial-loop-v0.0.2`, `ddo-v006-<slug>`. Any name-pattern-based discovery (including the anti-rot guard) must not assume a single scheme. **(RT-13)**

---

## 6. Negative Constraints — Analysis

* **Clarifying Questions:**
  1. "DO NOT embed content-bearing/quantitative imperatives in the new style files" — this is enforced **only** by HITL authoring review. `test_styles.py` checks structure + sentinel-absence, **not** content-imperative absence (per its own node description: "Does not assert prose content"). §7's mitigation says "test_styles.py enforces structure + sentinel-absence" — which is true but does *not* catch content directives. Is the constraint understood to be HITL-only, with no CI backstop? **(RT-14)**
  2. "DO NOT let `input_files/*.yaml` drift" — enforced by a guard whose pairing rule is unspecified (RT-01/RT-02). A constraint whose enforcement mechanism is ambiguous is not yet a constraint.

* **What-If Scenarios:**
  - **A "phrasing-only" style that smuggles a directive slips CI.** e.g., `blog_casual`'s Diction section says *"prefer three supporting stats per claim."* That's quantitative/content-bearing, violates the v0.0.5 rubric — and `test_styles.py` passes it (no sentinel, five sections present). Only a human catches it. The negative constraint reads as CI-guaranteed but isn't. **(RT-14)**
  - **`executive_formal` overlaps `formal_professional`.** The new `executive_formal` style and the existing `formal_professional` may be near-duplicates. Nothing forbids near-identical styles; the teaching value ("worked example of authoring") is undercut if the specimen is a paraphrase of a shipped file. Not a failure, but a quality erosion the constraints don't guard.

* **Points for Improvement:**
  - Either add a lightweight lexical check to `test_styles.py` (flag numerals/quantitative tokens in Diction/Avoid as a warning) or amend §7 to stop claiming `test_styles.py` guards content-directive absence — correct the mitigation wording to "HITL rubric only." **(RT-14)**

---

## 7. Risks & Mitigation — Analysis

* **Clarifying Questions:**
  1. The risk table omits the two highest-probability failure modes this pass surfaced: (a) **casual types cannot be evidence-free** (`validation.py:106`, RT-04), and (b) **tutorial `code_samples` breaking the ruff gate** (RT-06). Both are near-certain to bite during execution. Why are they absent?
  2. "Model templates on the proven `prd`/`scientific_report` templates; M2/M3 catch non-determinism" — the proven templates were only exercised on **formal, ASCII-clean** content. What in the mitigation covers the *new* risk surface (casual register, non-ASCII, emoji) that the existing templates never met? **(RT-12)**

* **What-If Scenarios:**
  - **Mitigation is downstream of the failure.** For the token-budget risk, the mitigation ("split at `/hyper-resolve`") is correct — but for RT-04/RT-06/RT-07 there is *no* listed mitigation, so execution discovers them as red CI with misleading error messages (a contract requirement masquerading as a determinism/lint bug).

* **Points for Improvement:**
  - Add rows for RT-04 (evidence-mandatory contract → source casual evidence from a real `input_files/` narrative doc), RT-06 (ruff-clean `code_samples`), RT-07 (`output_files` determinism decision), RT-11 (suite runtime budget), and RT-08 (persona/style resolution test). Each should name the *specific* file/assertion that discharges it, not a general practice.

---

## 8. Success Metrics — Analysis

* **Clarifying Questions:**
  1. Metric: "every `input_files/` copy is byte-identical to its source (guard test green)." Green *proves nothing* if the guard's pairing rule skips unmapped files (RT-01/RT-02). A guard that compares zero pairs is also "green." How is the guard's *coverage* itself asserted (e.g., a test that the mapping is non-empty and includes Tutorial 1's `ingest_output.yaml`)?
  2. Metric: "A newcomer can follow Tutorial 1 end-to-end and produce a rendered, evidence-linked document (HITL-verified)." Tutorial 1 is the *evidence-lens* tutorial anchored to a human-gated fixture. Which command in Tutorial 1 actually *renders*? If it only inspects `ingest_output.yaml`, "produce a rendered document" belongs to Tutorial 2, not 1. Is this metric mis-assigned? **(RT-15)**

* **What-If Scenarios:**
  - **All-green, under-covered.** With `EXAMPLES` duplicated (RT-03), a guard with an empty/partial mapping (RT-02), no persona-resolution test (RT-08), and no `output_files` guard (RT-07), it is entirely possible to hit *every* success metric's literal wording while shipping a dangling persona ref, a drifted output sample, and a Tutorial-1 anchor the guard never checked. The metric set is satisfiable without the underlying guarantees.

* **Points for Improvement:**
  - Make each metric name the assertion that proves it: "guard test green" → "guard asserts ≥5 mapped pairs including `ingest_output.yaml` and all four new `tests/data/*.yaml`." "personas/styles resolve" → the new `test_schema_meta_refs.py`. Metrics should reference tests, not adjectives.
  - Reassign the "produce a rendered, evidence-linked document" metric to the tutorial that actually renders (Tutorial 2), or add an explicit render step to Tutorial 1 and state which fixture it renders. **(RT-15)**

---

## Consolidated Finding Ledger (for `/hyper-resolve`)

| ID | Severity | Finding | Suggested disposition |
|---|---|---|---|
| RT-01 | **Critical** | Guard scope is `tests/data/`, but Tutorial 1 anchors to `tests/fixtures/ingest_output.yaml`; guard never checks it. | Extend guard mapping to cover `tests/fixtures/`. |
| RT-02 | **Critical** | Anti-rot guard's reference-discovery + pairing mechanism is unspecified — determines robust vs. theatre. | Spec explicit `EXPECTED_MIRRORS` map + `input_files/` walk; no prose parsing. |
| RT-04 | **Major** | Minimal contract mandates ≥1 evidence ref (`validation.py:106`); casual `blog_post`/`meeting_notes` cannot be evidence-free and still render. | Source casual evidence from a real `input_files/` narrative doc; state this in §5. |
| RT-08 | **Major** | US-005 AC3 (persona/style resolve) has **no** CI surface; typo'd `meta.persona` ships silently. | Add `test_schema_meta_refs.py`. |
| RT-06 | **Major** | `tutorials/` is linted by ruff; new `code_samples/*.py` can sink US-007. | Constrain samples to ruff-clean; forbid dir-level ruff exclusion. |
| RT-07 | **Major** | `output_files/` renders are unguarded; "dogfooded by output_files" claim can rot. | Add determinism guard or declare illustrative-only. |
| RT-05 | **Major** | Tutorial 1 creates an *ungated* replica of a `DDO_FIXTURE_SIGNOFF`-protected fixture. | Guard provenance, not just sameness; document the gate boundary. |
| RT-03 | Minor | `EXAMPLES` duplicated across two files; divergence → silent under-coverage. | Consolidate to one source or add equality guard. |
| RT-11 | Minor | Integration suite subprocess count ~3×; no per-suite time budget (missing NFR). | State budget; consider marker-gated full matrix. |
| RT-12 | Minor | New casual/non-ASCII register untested against Typst font coverage (M3). | Add a non-ASCII fixture value now. |
| RT-14 | Minor | "No content-bearing style imperatives" is HITL-only; §7 overstates `test_styles.py`. | Correct §7 wording or add lexical warn. |
| RT-09 | Minor | Confirm all 4 templates are clock/locale-free (M3b). | Assert purity at authoring. |
| RT-10 | Minor | No binding between example YAML sections and its schema's declared sections. | Add soft schema-conformance check. |
| RT-13 | Minor | Three tutorial naming schemes coexist; discovery must not assume one. | Guard by directory walk, not name pattern. |
| RT-15 | Minor | Success metric assigns "render a document" to the non-rendering Tutorial 1. | Reassign to Tutorial 2 or add a render step. |

---

**Final Action:** Report saved to `spec/active/RedTeam_Report.md`. Run **`/hyper-resolve`** to triage these findings, mediate the Critical/Major items into the final SuperPRD, and compile the MiniPRDs. Prioritize RT-01 and RT-02 — the anti-rot guard is the PRD's only new enforcement surface, and as specified it can pass green while checking nothing.
