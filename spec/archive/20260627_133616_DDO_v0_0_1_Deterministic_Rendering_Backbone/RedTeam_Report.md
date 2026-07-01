# RedTeam_Report.md — Adversarial Analysis of DDO v0.0.1 Draft PRD

> **Target:** `spec/active/Draft_PRD.md` (SuperPRD: DDO v0.0.1 — Deterministic Rendering Backbone)
> **Blast-radius reference:** `spec/compiled/architecture.yml` — **does not exist / empty (greenfield)**.
> **Agent:** Red Team (`/hyper-redteam`)
> **Date:** 2026-06-27
> **Verdict:** Spec is coherent and well-scoped, but several load-bearing terms ("byte-identical", "content-identical", "hermetic", "zero-hallucination", "the validation gate") are asserted without operational definitions or tests, and the path/slug/sentinel surfaces have concrete failure modes. None are scope-creep; all are execution-resilience gaps. Recommend resolving the **Critical** items below before MiniPRD compilation.

---

## 0. Blast Radius (Greenfield Note)

Because `architecture.yml` is empty, there are **no existing nodes to break** — the blast radius is *temporal*, not lateral. Every contract this PRD locks becomes the foundation the deferred adversarial loop (v0.0.2+) must build on without a migration. The three highest-leverage lock-ins to scrutinize **now**, because they are cheap to change today and expensive after the schema ships:

1. **`build.py` is the *single* validation gate, render skill is a *thin* wrapper.** This is good DRY, but it means the deferred `ddo-interview`/`ddo-refine` loop has **nowhere to put skill-side pre-validation** without either (a) duplicating logic the PRD forbids, or (b) shelling every check through `build.py`'s CLI. Confirm the gate's checks are exposed as an importable function, not only as a CLI side effect, so v0.0.2 can reuse them without subprocessing.
2. **Schema forward-compatibility for the mutation layer.** v0.0.2 introduces `red_team_report.yaml` and `interview_log.yaml` *mutating* `document_data.yaml`. If the v0.0.1 `meta`/`content`/`evidence_bank` shape does not reserve space for review state, refinement provenance, or per-section revision history, v0.0.2 forces a breaking schema migration on documents authored under v0.0.1.
3. **Migrated-but-unused personas.** `product_critic`/`scientific_reviewer` are copied in "forward-compat, unused." Unused, untested code rots. Either exercise them by a smoke test (parse-able / well-formed) or explicitly mark them as un-versioned drafts so a stale persona doesn't silently poison the v0.0.2 Red Team loop.

---

## 1. Introduction & Goals — Analysis

* **Clarifying Questions:**
  1. The headline promise is *"every generated word traces back to a version-controlled YAML source."* The deterministic render guarantees **YAML → document fidelity**. It does **not** guarantee **source → YAML fidelity** (that is `ddo-ingest`, an LLM step with no automated content check — see §5). Is the marketing claim therefore *"the renderer never adds words the YAML didn't contain"* (true & enforced) rather than *"no word is fabricated"* (false in v0.0.1)? The PRD should state which guarantee it actually delivers.
  2. "Deterministic" is scoped to *repeated runs* (US-001 AC2). Is determinism claimed **across machines/OS** or only **same-machine, same-run**? The two are very different engineering commitments (locale, line endings, font metrics, library versions all differ across hosts).
* **What-If Scenarios:**
  - A reviewer at the HITL gate rubber-stamps an ingest that silently fabricated a metric. The render is perfectly faithful to the (wrong) YAML, every check is green, and the document ships with a hallucinated number that now *looks* provenance-backed. The system's core value prop is defeated with zero red flags because **no automated guard sits between source and YAML**.
  - The very first document a new user renders is *this project's own PRD*, which contains the literal sentinel string `[REQUIRES USER INPUT:` as documentation. The validation gate aborts on a fully-valid document (see §5, Check 3). The flagship tool fails on its own dogfood.
* **Points for Improvement:**
  - Split the promise into two explicit, separately-verifiable claims: **(A) Render fidelity** (deterministic, tested) and **(B) Extraction fidelity** (human-gated, *not* machine-verified in v0.0.1). Make (B)'s non-automation a stated limitation, not an implied guarantee.
  - State the determinism boundary (same-host) as an explicit NFR so fixtures and CI are not held to a cross-platform standard the design never promised.

---

## 2. Confidence Mandate — Analysis

* **Clarifying Questions:**
  1. Deferred Q1 (does the `typst` PyPI package expose creation-timestamp control?) is a **hard dependency for US-003 and two success metrics**. If the spike fails, the fallback is "the package's bundled CLI entrypoint" — which is a **subprocess**, directly contradicting the §5 resolution *"rendered via the typst Python package, in-process (hermetic; no system Typst install)."* Is an in-process-Python-package-CLI invocation still "in-process," or does the fallback quietly reintroduce a subprocess boundary the design tried to eliminate?
  2. Deferred Q3 (store golden PDF binary vs. hash + text) is treated as a fixture-bootstrap detail, but it determines whether the determinism *contract is even testable* for PDF (see §8). Should this be resolved at spec time, not deferred?
* **What-If Scenarios:**
  - The typst-timestamp spike fails *and* the CLI fallback is unavailable in the pinned package build → US-003 (Medium) and the "`--timestamp` yields byte-identical PDFs" success metric are silently un-deliverable, discovered only mid-build. A Medium story quietly becomes Won't-Have with no decision record.
* **Points for Improvement:**
  - Promote Q1 to a **pre-build spike with a go/no-go gate**: if neither in-process API nor a hermetic CLI path pins the timestamp, explicitly de-scope byte-identical PDF from v0.0.1 *now* rather than discovering it during the build.
  - Reconcile the Risk-2 mitigation ("fall back to bundled CLI") with the Q6 resolution ("hermetic Python package, drop the install-Typst prerequisite"). State whether the package's vendored CLI counts as hermetic.

---

## 3. Scope — Analysis

* **Clarifying Questions:**
  1. The contract requires `meta.persona`, but personas are explicitly **unused in v0.0.1**. Why is a functionally-dead field *required* by the validation gate? Either it is load-bearing (then what reads it?) or it is vestigial (then it should be optional until v0.0.2).
  2. `meta.output_formats` is a required array, but `build.py` renders exactly **one** `--format` per invocation. What is the relationship — does `ddo-render` iterate `meta.output_formats` and call `build.py` N times? If so, what happens when `--format md` is passed but `md ∉ meta.output_formats` (or vice versa)? Two sources of truth for "which formats" invites drift.
  3. Same redundancy for `meta.template` vs. `--template`: if they disagree, which wins, and is the mismatch an error?
* **What-If Scenarios:**
  - v0.0.2's adversarial loop needs a schema field the v0.0.1 schema didn't reserve → every document authored under v0.0.1 needs migration. "Out of scope" for the *code* does not make the loop out of scope for the *schema's forward shape*.
* **Points for Improvement:**
  - Either make `persona` optional in the v0.0.1 contract or document the single reason it must be present now.
  - Define the precedence rule between `meta.{template,output_formats}` and the CLI flags (recommend: CLI is authoritative for a single render; `ddo-render` derives flags *from* `meta` so they cannot disagree, and build.py never trusts `meta` for routing).
  - Add a one-line "forward-compatibility commitment" to the schema section so MiniPRD 3 reserves the mutation-layer keys the deferred loop will need.

---

## 4. User Stories — Analysis

* **Clarifying Questions:**
  1. US-001 AC2 says HTML/MD are "byte-identical across repeated runs." Does any template embed wall-clock or environment data (a "Generated on …" line, `{{ now() }}`, build host)? If so the claim is **false for HTML/MD** — the PRD only guards the *Typst* timestamp, never the Jinja2 templates.
  2. US-002 AC: is the `[REQUIRES USER INPUT` scan run against the **raw file text** (catches comments, keys) or the **parsed structure** (string values only)? The blast radius of a substring match differs enormously.
  3. US-004 AC3: "never overwritten without explicit confirmation." In a non-interactive / agent-driven run, what *is* "confirmation"? What is the default when no TTY is present — abort or proceed?
  4. US-006 AC3: the ingest test renders "a fixed fixture source." If `ddo-ingest` is an LLM call, its output is **non-deterministic** — how is this asserted without flakiness? Is the LLM mocked, or is a previously-captured ingest output checked in as the fixture?
* **What-If Scenarios:**
  - `ddo-ingest` writes `document_data.yaml`, then crashes mid-write (or is interrupted). A **partial/corrupt YAML** is left on disk. The next `ddo-render` fails with a PyYAML parse error instead of a precise message, and the overwrite guard now blocks re-ingest because a file "exists."
  - Two documents share date + doc_type + title → identical slug → **same folder**. The overwrite guard protects the *YAML* but the second ingest's gap-flagged draft collides with the first's reviewed source.
  - US-003: `--timestamp` accepts an arbitrary "value." Malformed or out-of-range timestamp → Typst error mid-render, or silent acceptance of a garbage date embedded in the PDF.
* **Points for Improvement:**
  - Add an explicit AC: **no Jinja2 template may emit non-deterministic content** (no clock, no host, no PRNG, no unordered-dict iteration without `|dictsort`). Make a unit test assert two renders of the same YAML are byte-equal *for HTML and MD specifically*.
  - Specify **atomic writes** for `ddo-ingest` (write to temp, `fsync`, rename) so a crash never leaves a half-written source-of-truth.
  - Define the non-interactive overwrite default (recommend: **abort** with a precise message; require an explicit `--force`/confirmed flag to overwrite).
  - State how `--timestamp` is validated (format + range) and what error it produces.

---

## 5. Technical Specifications — Analysis

* **Clarifying Questions:**
  1. **Validation Check 3 (unfilled-input scan).** Naive substring match on `[REQUIRES USER INPUT` will **false-positive on legitimate content** that quotes the sentinel (this project's own docs do exactly that). Scope: does it scan raw bytes, all string values, or only values it expects to be fillable? How does a user render a document whose subject matter *discusses* the sentinel?
  2. **Validation Check 2 (evidence-ref integrity).** If `content`, `content.sections`, or every section's `evidence` key is **absent**, there are zero refs to check → the check trivially passes. Does an **empty/contentless document** pass the gate? Is at least one section / one evidence ref required? Are duplicate IDs in `evidence_bank` rejected? Are **orphan** evidence entries (never referenced) flagged or allowed?
  3. **Validation Check 1 (contract).** "Present" vs. "valid": does `title: ""` (present, empty) pass? Is `meta.date` validated against the `YYYY.MM.DD` format the folder convention *depends on*? A `2026-06-27` date silently breaks the slug.
  4. **Malformed YAML.** If the file is not parseable YAML, is the PyYAML exception caught and rendered as one precise message, or does it stack-trace? Is Check 3 run on raw text *before* parse (so a malformed file with a remaining sentinel still fails closed)?
  5. **Slug derivation.** "title lowercased, spaces→hyphens" — what about `/`, `\`, `:`, quotes, leading/trailing dots, `..`, control chars, emoji, and titles exceeding the 255-byte filename limit? `meta.title` originates from ingested arbitrary sources.
  6. **Hermeticity.** PEP 723 inline deps `typst, jinja2, pyyaml` — are they pinned with `==` **and a lockfile/hashes**? `uv run` without a lock resolves transitive deps at runtime → renders are **not reproducible across time** even on one machine. Also: `uv run` must reach PyPI at least once, so "no network in v0.0.1" holds for *sources* but not for the *build itself* — say so.
  7. **Fonts.** Typst falls back to **system fonts** by default. Different installed fonts → different glyph metrics → different line breaks → "content-identical" PDF breaks across machines, and arguably breaks "hermetic." Are fonts bundled and the font path pinned?
  8. **Jinja2 autoescape.** Is autoescape on for the `.html` template? Is ingested content with `<`, `&`, `>` escaped? What is the MD escaping policy? Could any value be re-evaluated as a template (SSTI) via `| safe` or string re-rendering?
  9. **`build.py` and directories.** It receives a fully-resolved `--output`. Does it `mkdir -p` the parent `output/` dir, or fail if absent? It "stays ignorant of the folder convention" — but who guarantees the dir exists at call time?
* **What-If Scenarios:**
  - **Path traversal.** An ingested source yields `meta.title: "../../.ssh/authorized_keys"` (or on Windows, a reserved name like `CON`, or a 300-char title). The slug logic doesn't sanitize `..`/separators → `ddo-ingest` and the `output/` path **escape `Documents/`** and write into the repo or home dir. "Single-user local" mitigates *intent*, not *accidents*; a weird title silently corrupts the workspace.
  - **Floating Typst version.** A `typst` package patch release reflows a table → the determinism regression (HTML/MD frozen fixtures are unaffected, but any text the template derives from Typst-driven values) and the "content-identical PDF" promise drift, with no pin to catch it. Worse if deps float: a `jinja2` whitespace-control change makes previously byte-identical HTML differ → the determinism test fails with no source change.
  - **Resource exhaustion.** A pathological YAML (deeply nested, multi-GB, or a Typst template with an unbounded `while`) makes the in-process render **hang or OOM the whole process** — there is no timeout or size cap. In-process rendering means a runaway template takes down `build.py` itself, not an isolable subprocess.
  - **Empty-but-valid doc.** A YAML with valid `meta`, an empty `evidence_bank: []`, and no `content` passes all three checks and renders an empty document — a "valid" doc that asserts nothing, undermining the contract's intent.
  - **Sentinel in source.** Ingest faithfully copies a source paragraph that *contains* `[REQUIRES USER INPUT: legacy note]`. Now a genuine gap flag and copied source text are indistinguishable, and the gate aborts on real content.
* **Points for Improvement:**
  - **Harden the sentinel scan:** use a unique, namespaced token (e.g., `[[DDO::REQUIRES_USER_INPUT: …]]`) that cannot collide with prose, and/or scan only designated fillable string *values* rather than raw bytes. Document an escape hatch for documents whose subject is DDO itself.
  - **Strengthen Check 1/2:** require non-empty `title`/`version`; validate `meta.date` against `^\d{4}\.\d{2}\.\d{2}$` (the folder convention depends on it); require ≥1 section with ≥1 evidence ref (or explicitly allow empty and say so); reject duplicate `evidence_bank` IDs; decide orphan-evidence policy (recommend warn).
  - **Sanitize slugs:** whitelist `[a-z0-9-]`, collapse/replace everything else, strip leading dots, forbid `..`, cap length, and **assert the resolved output path is within `Documents/`** (realpath containment check) before any write. This closes the traversal vector cheaply.
  - **Make hermeticity real:** pin `==` versions in the PEP 723 block, commit a `uv.lock` (or use `uv run --locked` / `--no-sync`), and bundle + pin fonts for Typst. Restate "hermetic" as "reproducible given the lockfile + bundled fonts," and acknowledge the one-time PyPI fetch.
  - **Expose the gate as an importable function** (not CLI-only) so the deferred loop reuses it — see §0 lock-in #1.
  - **Add an output-size / wall-clock guard** on the in-process render (or render in a bounded subprocess) so a pathological template can't hang the orchestrator. Even single-user, a hung build with no message is a bad failure mode.
  - **Define `build.py`'s directory contract:** it should `mkdir -p` the `--output` parent (idempotent) so callers can't trip on a missing `output/`.
  - **Pin Jinja2 autoescape on for HTML**, document the MD escaping policy, and assert no template re-renders a data string (no SSTI surface).

---

## 6. Negative Constraints — Analysis

* **Clarifying Questions:**
  1. *"DO NOT let an agent write `tests/fixtures/` (human-promoted only)."* How is this **enforced**, not merely requested? An agent with Write access can write anywhere. Is there a pre-commit hook / CI check that fails if `tests/fixtures/` changes without a human-signed marker?
  2. *"DO NOT overwrite an existing `document_data.yaml` without explicit confirmation."* Same enforcement question — is the guard *in `ddo-ingest`'s code path*, or only a behavioral instruction the LLM may forget?
* **What-If Scenarios:**
  - An agent re-baselines a "broken" fixture to make a failing determinism test pass — laundering a real regression into a green build. The constraint is prose; nothing mechanically stops it.
  - The §7 mitigation "fix `.gitignore` so `tests/` and `spec/` are tracked" is applied **too broadly** and un-ignores `tests/candidate_outputs/` — directly violating *"DO NOT read/commit candidate outputs."* The mitigation for one risk creates a violation of a negative constraint.
* **Points for Improvement:**
  - Convert the two highest-stakes "DO NOT"s into **mechanical guards**: a pre-commit/CI check that rejects diffs to `tests/fixtures/` lacking a human sign-off token; an in-code overwrite guard in `ddo-ingest` (not just an instruction).
  - Rewrite the `.gitignore` mitigation to be **surgical** (track `tests/unit`, `tests/integration`, `tests/fixtures`, `spec/compiled`, `spec/process`; **keep ignoring** `tests/candidate_outputs/` and `Documents/`). See §7.

---

## 7. Risks & Mitigation — Analysis

* **Clarifying Questions:**
  1. Risk 1's mitigation "fix `.gitignore` so `tests/` and `spec/` are tracked" — does "tracked" mean *wholesale un-ignore*? That would commit `tests/candidate_outputs/` (forbidden), `spec/active/` working drafts (ephemeral by design), and `Documents/` (must stay gitignored). What is the **exact** intended track/ignore matrix?
  2. Risk 5 (ingest non-determinism → un-automatable hallucination check) names the **single largest hole in the value prop** but mitigates it only with "human verifies at the gate." What backstops the human? Is there *any* cheap automated heuristic (e.g., every numeric/date token in the YAML must appear verbatim in some source file) to flag likely fabrications?
* **What-If Scenarios:**
  - The PDF-binary-in-git decision (Risk 4) is deferred; the team stores the binary "for now," PDFs are non-byte-deterministic by default, so every wall-clock render dirties git → noisy diffs, repo bloat, and a fixture that *can't* be diffed to explain a failure.
  - Risk 2 (timestamp API) and Risk 3 (template/schema mismatch) are both "verify/spike during build" — if both bite simultaneously, MiniPRD 1 and MiniPRD 3 stall together and the critical-path slips with no early-warning gate.
* **Points for Improvement:**
  - Replace Risk 1's mitigation with the **explicit surgical `.gitignore` matrix** above, and add an acceptance check: `git status --porcelain` shows new test/spec files stageable **and** confirms `tests/candidate_outputs/` + `Documents/` remain ignored.
  - Add a cheap **fabrication tripwire** to the ingest risk: assert that every date/number/proper-noun-looking token emitted into the YAML is present in at least one source file; surface mismatches to the human reviewer as "verify these." It won't catch everything, but it gives the human gate something better than a blank stare.
  - Add an **early go/no-go** for Risk 2 (timestamp spike) before MiniPRD 1 commits to an in-process design that may need to change.

---

## 8. Success Metrics — Analysis

* **Clarifying Questions:**
  1. *"Repeated PDF renders are content-identical"* — **how is "content-identical" defined and measured?** The PRD explicitly runs **no PDF hash gate**. As written this metric is **unfalsifiable**: there is no test, no operator (extract-text-and-diff? compare bytes minus the timestamp region?), and no pass/fail criterion. A metric you cannot measure is not a metric.
  2. *"`--timestamp` yields byte-identical PDFs"* **is** testable (hash equality). Is there a corresponding test, and does it depend on the deferred Q1 spike succeeding (§2)?
  3. *"byte-identical HTML/MD"* — measured same-host only? On what runner? (Cross-OS line endings will fail this; see §1/§4.)
* **What-If Scenarios:**
  - The team declares "content-identical PDF" met by eyeballing two PDFs, because no operational definition exists. A later font/Typst change subtly reflows page 3; nothing catches it because the metric was never mechanized.
  - The determinism regression for HTML/MD is generated on the maintainer's Linux box and run in CI on a different image → trailing-newline / locale differences fail the build with **no source change**, eroding trust in the suite.
* **Points for Improvement:**
  - Give "content-identical PDF" an **operational definition + test**, or delete it as a metric. Recommended cheap definition: *extract Typst's text layer (or render with a pinned `--timestamp`) and assert text/structure equality*, since byte-equality is intentionally not the default.
  - Pin the **determinism test environment** (or normalize outputs: force LF, fixed locale `C.UTF-8`, strip trailing whitespace) so fixtures are not silently host-specific.
  - Tie each success metric to a **named test** so "success" is `pytest green`, not human judgment.

---

## Appendix Analysis — Decisions Locked During the Architect Interview

* **Clarifying Questions:**
  1. Q2 locks "no PDF hash gate" — combined with §8, this means PDF determinism is **asserted but never tested**. Is that an accepted, documented limitation, or an oversight?
  2. Q6 ("hermetic Python package, in-process; drop install-Typst") vs. Risk-2's CLI fallback — which one is the **actual** locked decision if the spike fails? A locked decision with a contradicting fallback is not locked.
  3. Q8 says ingest is the *sole* Candidate Artifact with "contract-validity + render-ability tests only, content human-verified." This formally concedes that the **zero-hallucination guarantee has no automated test** — is that concession surfaced to stakeholders, or buried in an appendix?
* **What-If Scenarios:**
  - The locked decisions are treated as immutable by `/hyper-resolve` and compiled straight into MiniPRDs, carrying the §5 path/sentinel/hermeticity gaps into the build unexamined because "the architect already decided."
* **Points for Improvement:**
  - For each locked decision that this report contradicts (Q2 vs. §8 testability; Q6 vs. Risk-2; Q8 vs. the headline guarantee), add an explicit **"open tension"** note so `/hyper-resolve` triages it rather than rubber-stamping the lock.

---

## Triage Summary (suggested severity for `/hyper-resolve`)

| # | Finding | Section | Severity |
|---|---|---|---|
| 1 | Sentinel scan false-positives on legit content (incl. DDO's own docs); raw-vs-parsed scope undefined | §5 | **Critical** |
| 2 | Slug/path derivation unsanitized → path traversal / illegal-filename / length failures | §5, §4 | **Critical** |
| 3 | "Hermetic" without `==` pins + lockfile + bundled fonts → not reproducible; in-process render has no timeout | §5 | **Critical** |
| 4 | "Content-identical PDF" success metric has no definition and no test (Q2 vs §8) | §8, Appendix | **Critical** |
| 5 | Zero-hallucination has no automated backstop; human gate is the sole guard (acknowledged but under-mitigated) | §1, §7 | High |
| 6 | Validation gate: empty doc passes; no type/format/non-empty checks; duplicate/orphan evidence unhandled; malformed-YAML path unspecified | §5 | High |
| 7 | HTML/MD byte-identity not guarded against template-side clock/host/unordered-dict | §4 | High |
| 8 | `.gitignore` mitigation risks committing `tests/candidate_outputs/` (violates a negative constraint) | §6, §7 | High |
| 9 | typst-timestamp spike (Q1) gates US-003 + a metric; in-process vs CLI-fallback contradiction unresolved | §2, Appendix | High |
| 10 | `meta.output_formats`/`meta.template` vs CLI flags: two sources of truth, precedence undefined | §3 | Medium |
| 11 | Non-atomic ingest writes; non-interactive overwrite default undefined | §4 | Medium |
| 12 | Required-but-unused `meta.persona`; schema forward-compat for v0.0.2 mutation layer unstated | §3, §0 | Medium |
| 13 | "human-promoted only" fixtures / overwrite guard are prose, not mechanical enforcement | §6 | Medium |
| 14 | Determinism fixtures may be host-specific (line endings/locale) → flaky CI | §8 | Medium |

---

**Final Action:** Report saved to `spec/active/RedTeam_Report.md`. Run **`/hyper-resolve`** to begin triaging these vulnerabilities and compile the final SuperPRD + MiniPRDs.
