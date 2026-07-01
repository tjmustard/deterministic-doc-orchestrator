# RedTeam_Report: DDO v0.0.2 — The Adversarial Loop

> **Target:** `spec/active/Draft_PRD.md` (v0.0.2, 2026-06-29)
> **Lens:** Distributed-systems resilience, state-mutation safety, OWASP-style input/path handling, NFR completeness.
> **Context discipline:** Produced in a fresh context per the PRD's own `ddo-red-team` firewall; no authoring/ingest rationale inherited.
> **Verdict (headline):** The architecture is sound and the reuse-not-reinvent discipline is correct. But the central safety claim — *"a bad patch can never corrupt the source of truth"* — is **over-stated** as written, because (a) `validate()` is a minimal contract, not a structural schema, and (b) the source of truth has **no rollback** (gitignored, unversioned, force-overwritten). The highest-value hardening lives at three points: the **validate-completeness gap**, **YAML round-trip fidelity**, and **document_data.yaml durability**. Detail below, section by section.

---

## 1. Introduction & Goals — Analysis

### Clarifying Questions
- The thesis is "improve a document *without corrupting the YAML*." Corruption is defined operationally as "fails `validate()`." But `validate()` (confirmed in `ddo/validation.py`) only enforces: required `meta` keys are non-empty strings, a date regex, `evidence_bank` is a list with unique IDs and no dangling refs, a contentless guard (`0 sections or 0 refs`), and the sentinel scan. **Is "passes `validate()`" actually the project's definition of "uncorrupted"?** A patch that replaces every real section with one junk section carrying one evidence ref passes all of those checks. What is the intended boundary between "contract-clean" and "not corrupted"?
- The intro says the loop "only ever mutates the one mutable artifact through code-enforced safety, never by hand-editing text." But `interview_log_vN.yaml` is also mutated indirectly (the report's `resolved` flag is rewritten in place — US-002 AC3), and `history.yaml` is appended. **Are those not also mutations of state the loop must keep consistent?** "One mutable artifact" undersells the actual set of mutable files (`document_data.yaml`, `red_team_report_vN.yaml` post-interview, `history.yaml`).
- The sentinel string is inconsistent across the project: code scans for `[[DDO::REQUIRES_INPUT:` (`validation.py:20`) but `CLAUDE.md` instructs authors/agents to write the literal `[REQUIRES USER INPUT: <reason>]`. **Which form is authoritative, and does `ddo-ingest` actually emit the form `validate()` scans for?** If ingest writes `[REQUIRES USER INPUT:`, the gap-closing premise of the entire loop (refine replaces sentinels) never triggers on `validate()` and gaps are invisible to the safety scan.

### What-If Scenarios
- **The "valid-but-gutted" document.** A `set` patch on `content.sections` (or a wrong-but-well-formed `revise`) produces a dict that satisfies the minimal contract yet silently deletes or mangles real content. `validate()` passes, the human skims a misleading diff (see §5), `commit_refine` writes. The document is now *worse*, *reproducibly*, and the prior good state is gone. The PRD's promise ("the document improves") has no mechanism that actually verifies improvement — only that the result is contract-clean.
- **The irreversible good-faith mistake.** `Documents/` is gitignored (architecture: `documents_output`) and US-004 AC4 explicitly states `document_data.yaml` is **not** versioned. `commit_refine` uses `force=True` (PRD §5 step 5), so `atomic_write`'s overwrite guard is *intentionally disabled*. Net effect: a single approved-but-wrong refine is **unrecoverable** — no git, no `.bak`, no prior `_vN` of the source. This is the most dangerous property in the whole design and it is nowhere listed as a risk.

### Points for Improvement
- Re-state the safety claim honestly: `validate()` **bounds** the blast radius to "minimal-contract-clean"; it does not guarantee "uncorrupted." Then decide which of two hardening paths to take (this is the single most important decision for the Resolve phase):
  1. **Extend the gate** with a refine-specific structural/type check (e.g., every `content.sections[*].body` is a non-empty string; `meta` has no unexpected type drift) — but note this *modifies* `validation_gate`, contradicting the PRD's "reused, not modified" blast-radius claim.
  2. **Constrain `set`** to a whitelist of safe, leaf, scalar paths so it structurally cannot reach `content.sections` wholesale or change a node's type.
- Add a **pre-write snapshot of `document_data.yaml`** (e.g., copy to `review_history/document_data_pre_vN.yaml`) so the source of truth is recoverable after a valid-but-wrong refine. This directly closes the irreversibility hole and costs one atomic copy.

---

## 2. Confidence Mandate — Analysis

### Clarifying Questions
- Five open questions are listed; they are the right *implementation* questions but they presuppose the safety model holds. **Why is the validate-completeness gap (§1) not among them?** The 8/10 confidence leans on "the importable `validate()` gate caps blast radius regardless" (Risk R1) — but that is exactly the assumption this report challenges. Does the confidence score survive the observation that `validate()` is a presence/uniqueness/sentinel check, not a schema?
- Open question #1 frames patch-grammar risk as "too narrow forces hand-edits; too wide widens corruption surface." **What is the actual expressiveness floor?** Has anyone enumerated the real resolutions a typical red-team pass produces (e.g., "rewrite section 3 body," "qualify a claim," "add a caveat sentence") and mapped each to `set`/`append_evidence`/`append_review_log`? Without that enumeration, the grammar is being guessed at.

### What-If Scenarios
- **Confidence laundering.** The mandate says residual uncertainty "is exactly what the Red Team should stress." If the Red Team surfaces the validate-completeness and durability gaps and they are deferred rather than resolved, the 8/10 was measuring confidence in the *happy path*, not in the *failure modes the loop exists to guard against*.

### Points for Improvement
- Add two open questions to carry into Resolve: **(6) Does `validate()` need extension (or `set` need constraining) so "contract-clean" implies "structurally intact"?** and **(7) What is the rollback story for a valid-but-wrong refine given gitignored, unversioned source?**

---

## 3. Scope — Analysis

### Clarifying Questions
- Out-of-scope explicitly excludes "concurrent/multi-process editing of a single document folder." **Is that assumption enforced anywhere, or merely declared?** Two `ddo-red-team` invocations in two terminals both read `max(N)=2` and both target `v3`. `write_report` with `force=False` (API default) makes the second writer fail closed with `OverwriteError` — good — but `history.yaml` append (read-modify-write) and the in-place report `resolved` update have no such guard and will silently lose updates. Confirm single-user is *relied upon* for these, and say so.
- **Retention/pruning is unscoped.** The skill explicitly hunts for missing NFRs like retention and TTLs. `review_history/` accumulates `_vN` report + view + log per pass forever; `history.yaml` grows unbounded. After N loops you have ~3N files plus N history records. Is there an intended cap, prune, or archive policy, or is unbounded growth accepted for v0.0.2? State the decision explicitly rather than leaving it silent.

### What-If Scenarios
- **`ddo-run` deferral leaks back in via tests.** `ddo-run` is correctly deferred (conflicts with the firewall + HITL gates). But the M5 integration test must drive `report → log → refine → render` end-to-end in one process. That *is* a mini-orchestration — and it cannot invoke the `ddo-render` *skill* (agent cognition) from pytest. So the test will call `build.py` directly, meaning the **skill-mediated render handoff that v0.0.2 ships is never exercised by automated tests** (cross-ref §4 US-006 and §5). The deferral of `ddo-run` does not remove the need to test the chained path.

### Points for Improvement
- Promote "single-user / no concurrency" from an out-of-scope line to an **explicit invariant the read-modify-write paths depend on**, and note which writes fail-closed (`force=False` report/log writes) vs. which silently lose updates (`history.yaml`, in-place `resolved` update) if the invariant is violated.
- Add a one-line **retention decision** to scope (even if the decision is "unbounded, by design, for v0.0.2").

---

## 4. User Stories — Analysis

### Clarifying Questions
- **US-001 (red-team):** Severity must be `∈ persona taxonomy` *and* the data contract hardcodes `Critical|Major|Minor`, *and* `history.yaml` hardcodes `findings: {critical, major, minor}`. So the "persona's taxonomy" is not actually free — the whole stack assumes exactly these three. **Are personas contractually required to use exactly `Critical|Major|Minor`?** If yes, drop the "persona taxonomy" framing (it's a fixed enum). If no, the history schema and contract are wrong.
- **US-001:** Severity is validated against the taxonomy, but `category` is "persona attack-vector name" and is **not** validated against anything. **Should a finding's `category` be checked against the persona's declared attack vectors**, or is it free text? Asymmetric validation invites typo'd/invented categories that the history rollups can't aggregate.
- **US-001:** "persona defaults to `meta.persona` when present." **What happens when `meta.persona` names a persona file that does not exist** (typo, deleted)? Fail closed with a named error, or fall back to explicit selection? Undefined.
- **US-002 (interview):** AC1 says default `batch_size=2`, sorted Critical→Major→Minor. **Is there any upper bound on findings count or total batches?** A pathological 10k-finding report → 5,000 gated batches. `build.py` has a 30s/64 MiB guard; the loop has no analogous bound.
- **US-003 (refine):** AC4 re-renders "via `ddo-render`." `build.py` resolves template strictly from `--template/--format`, *never* `meta` (architecture: `build_orchestrator`). **Where do the re-render flags come from?** `meta` carries `template`/`output_formats` but `build.py` ignores them. So the re-render's template/formats are agent-remembered, not derived — if the agent picks differently than the original render, the re-render silently diverges. What pins re-render flags to the original render?

### What-If Scenarios
- **US-002 + US-003 — the `resolved` flag becomes a lie.** Interview commits, marking findings `resolved:true` in `red_team_report_vN.yaml` (in place). The user then `skip <n>`s that finding's patch at the refine diff gate (US-003 AC3), or refine aborts on validation. The report now says `resolved:true`, but the document was never changed. The next red-team pass re-finds the same defect, while the audit trail claims it was resolved. **`resolved` conflates "decided in interview" with "applied to document" — these can diverge.** Pick one meaning and name the states distinctly (e.g., `decided` vs `applied`).
- **US-003 — `skip` creates a dangling dependency deadlock.** `append_evidence` (patch A) adds `ev_42`; a later `set` (patch B) references `ev_42` in a section. User does `skip A`, keeps B. `validate()` now sees a dangling ref → **the whole refine aborts, writing nothing**, including the patches the user *did* approve. Is there inter-patch dependency awareness, or does any skip risk a full abort? Define `skip` semantics against dependent patches.
- **US-001 — in-place report mutation breaks the "snapshot" framing.** US-004 calls each `_vN` file a per-pass snapshot, but US-002 AC3 mutates `red_team_report_vN.yaml` after creation. The "snapshot" is therefore not immutable, and you lose the original (pre-interview) finding state for audit. `report.resolved=true` while `report.resolution=null` (resolution lives only in the log) — split, partially redundant state across two files that must stay consistent under atomic updates.
- **US-006 — "gap closed" is unassertable as stated.** Content-equality on AI output is forbidden (correctly). So "gap closed" can only be asserted as **sentinel-absence + `validate()`-clean + renders** — *not* "the right content was filled in." State that explicitly so the test isn't expected to prove semantic correctness it cannot.

### Points for Improvement
- US-001: replace "persona taxonomy" with the fixed `Critical|Major|Minor` enum (matching the contract and history schema), and add `category` validation against the persona's declared vectors (or explicitly declare `category` free-text).
- US-002/US-003: split `resolved` into `decision_recorded` (interview) and `patch_applied` (refine), and reconcile the report's flag only *after* `commit_refine` succeeds — so the audit trail never claims a fix that didn't land.
- US-003: define `skip` as either (a) skip-and-its-dependents, or (b) skip forbidden when a later approved patch depends on it; and store the original render's `--template/--format` so re-render is deterministic.

---

## 5. Technical Specifications — Analysis

### Clarifying Questions
- **The `target` path DSL is undefined.** Examples are `content.sections[2].body` and `content.sections[2].body`. **Who parses this, and how?** If it's `eval`/`exec`-adjacent, that is a code-execution surface on attacker-influenced (persona/agent-generated) input — an OWASP-grade flaw. If it's a hand-rolled mini-parser, specify its grammar: dotted keys, `[int]` indices, negative indices, dict keys containing `.` or `[`, missing-path behavior. **An unspecified path DSL is the second-largest risk after validate-completeness.**
- **`set` semantics on a missing or type-changing path.** Does `set content.sections[7].body` on a 3-section doc auto-vivify (corruption) or fail (safe)? Does `set` permit changing a node's *type* (string → dict, list → scalar)? `validate()` will **not** catch `content.sections[2].body` becoming a dict — it only checks evidence refs and the meta/contentless contract — yet the Jinja2/Typst templates expect a string and will break or render garbage. Define `set` as leaf-scalar-only with no auto-vivify, or this is a live corruption path.
- **`commit_refine` serialization is the unspecified lossy step.** `atomic_write(target, content: str, ...)` takes **pre-serialized text** (confirmed in `ingest.py`). So `commit_refine` must `yaml.dump(patched)` to text first. PyYAML `safe_dump` **drops all comments and, by default, sorts keys** (`sort_keys=True`). **Every refine therefore silently strips comments and may reorder keys in the source of truth**, even when content is "correct." For a project whose first invariant is "YAML is the source of truth," this is a major fidelity violation. Which serializer, with what settings, guarantees a lossless round-trip? (PyYAML cannot; round-trip preservation needs `ruamel.yaml` — a *new* dependency the PRD says it doesn't anticipate.)
- **`append_evidence` is a compound, two-site operation** (append to `evidence_bank` + link from a section). **What are its transactional semantics if the section link target is invalid** — does it leave a half-applied dict (evidence added, link missing)? Since `apply_patches` is pure and `validate()` runs after, a half-applied-but-still-contract-valid state could pass. Is `apply_patches` all-or-nothing across its N patches, and atomic within each compound patch?
- **`_vN` parsing contract.** `report_version` = `max(existing N)+1`. Specify the filename regex precisely. How are `red_team_report_v2_backup.yaml`, `..._vABC.yaml`, `..._v0.yaml`, gaps (`v1, v3`), and a half-written prior pass (`report_v2` exists, `interview_log_v2` missing) handled? Does a new red-team pass refuse to start (or warn) when the latest pass has no interview log / unresolved findings, to avoid orphaning an in-flight pass?
- **`review_history/` path derivation has no home yet.** `paths.py` exposes `document_dir`, `output_path`, `document_data_path`, `assert_within_documents` — **no `review_history` helper**. Does the new builder live in `ddo.review` (and call `assert_within_documents`), or is it added to `path_deriver` (which then *is* modified, contradicting the blast-radius claim)? Pin it.

### What-If Scenarios
- **Crash mid-commit-sequence.** §5 lists the refine sequence: apply → validate → diff → approve → `commit_refine` (atomic) → append `history.yaml` → regen `history.md` → invoke render. `atomic_write` makes the `document_data.yaml` write atomic, but the **sequence is not transactional**. Process death *after* the YAML write but *before* the history append (or render) leaves: source at vN+1 content, history at vN, `output/` stale renders. On restart, what reconciles this? There is no described crash-recovery or "torn pass" detection.
- **`history.yaml` corruption or drift.** `append_history` must read `history.yaml` first. If it was hand-edited to invalid YAML, does append fail closed (stuck) or reinitialize (history lost)? And if a `_vN` report file is deleted, `history.yaml` still lists that pass — `history.md` then renders a *phantom* pass. **Which is authoritative for "what passes happened" — `history.yaml` or the file tree?** They can desync, and nothing reconciles them.
- **`render: ok|failed` in `history.yaml` is agent-asserted, not code-verified.** Render runs via the `ddo-render` *skill* (agent action), so its outcome lives in the conversation, not as a return value to `commit_refine`. **How does `append_history` obtain a *truthful* render outcome?** As written, the agent reports it — which violates the project's "code owns truth" principle and lets the audit log record `ok` for a render that actually failed.
- **`atomic_write(force=True)` removes the only overwrite guard on the source of truth.** Legitimate (the target exists), but it means refine *always* overwrites with no second line of defense; combined with no snapshot (§1) and gitignored source, the failure is total and silent.
- **Diff serialization misleads the human gate.** If the Before/After diff is a unified diff of `yaml.dump`ed blocks and `sort_keys` differs from on-disk order (or comments are present on disk but absent in the dump), the human sees a **huge spurious diff** dominated by reordering/comment-stripping noise, burying the one real semantic change. The HITL approval gate — the last human safeguard — is only as good as the diff's signal-to-noise.

### Points for Improvement
- **Specify the path DSL formally** (grammar, indexing, missing-path = hard error, no auto-vivify, leaf-scalar-only for `set`) and confirm it is a parser, not `eval`. This single spec closes most of the patch-grammar corruption surface and answers open question #1.
- **Decide the serializer contract now**, not at MiniPRD time: either accept `ruamel.yaml` round-trip mode as a runtime dependency (preserving comments/key order), or document that refine canonicalizes/strips comments by design — and if the latter, snapshot the pre-refine file so the original formatting is recoverable. Pin `sort_keys=False` regardless.
- **Make the render outcome code-verified:** have `commit_refine` (or a thin wrapper) capture `build.py`'s exit code rather than letting the skill self-report `ok|failed` into `history.yaml`. (This is the one place the "refine never calls `build.py`" rule fights the "code owns truth" rule — resolve the tension explicitly.)
- **Define torn-pass detection:** on entry, each skill should detect an incomplete prior pass (report without log, source-newer-than-history, etc.) and refuse/resume rather than stack a new `_vN` on top.
- **Make `apply_patches` all-or-nothing** across its patch list and atomic within compound patches; document the patch-ordering/index-shift contract.

---

## 6. Negative Constraints — Analysis

### Clarifying Questions
- The constraints are strong on *what not to do* in the data flow, but **silent on source-of-truth fidelity and durability.** Why is there no constraint requiring a lossless YAML round-trip (no comment loss, no key reorder) on `document_data.yaml`? Given the project's first invariant, that omission is conspicuous.
- "DO NOT write `document_data.yaml` from any path other than `ddo.refine`'s validated pipeline" — **does this also forbid `ddo-ingest` from re-writing it?** Ingest created it; can ingest be re-run on an existing folder, and if so, does that path also enforce validate-before-write, or only refine?

### What-If Scenarios
- A future contributor, seeing no constraint against it, swaps the serializer or flips `sort_keys=True` "to make diffs stable" and silently begins reordering the source of truth on every refine — exactly the fidelity loss no constraint forbids.

### Points for Improvement
- Add: **"DO NOT alter `document_data.yaml`'s comments or key order on refine; the dict→YAML serialization must be a lossless round-trip (or snapshot the pre-refine file)."**
- Add: **"DO NOT record a `render` outcome in `history.yaml` that was not observed from `build.py`'s actual exit status."**
- Add: **"DO NOT overwrite `document_data.yaml` without first snapshotting the prior state to `review_history/`"** (pairs with the durability fix).

---

## 7. Risks & Mitigation — Analysis

### Clarifying Questions
- **R2** ("a refine patch silently corrupts `document_data.yaml`") names its mitigation as "mandatory in-memory `validate()` before write." Given that `validate()` is a minimal contract (verified), **does R2's mitigation actually cover its own threat?** A type-changed `body` or a wholesale-replaced `content.sections` is precisely "silent corruption" that `validate()` passes. R2 is currently mitigated only against the subset of corruptions the minimal contract happens to catch.
- **R1** leans on the same gate ("the `validate()`-before-write gate caps blast radius regardless"). Same question: caps it to *contract-clean*, not *intact*.

### What-If Scenarios
- The risk register has **no entry for irreversibility** (gitignored + unversioned + `force=True`), **no entry for YAML fidelity loss** (comment/key-order stripping), **no entry for crash mid-sequence**, and **no entry for history truthfulness**. These are the failure modes most likely to cause silent, unrecoverable damage in real use.

### Points for Improvement
Add and mitigate:
- **R7 — Irreversible valid-but-wrong refine.** Source is gitignored, unversioned, force-overwritten. *Mitigation:* snapshot `document_data.yaml` to `review_history/document_data_pre_vN.yaml` before every commit.
- **R8 — YAML fidelity loss on round-trip.** PyYAML strips comments / reorders keys. *Mitigation:* round-trip-preserving serializer or explicit canonicalization + snapshot; `sort_keys=False`.
- **R9 — Untruthful `history.render`.** Agent-asserted vs code-observed. *Mitigation:* capture real exit status.
- **R10 — Torn pass / crash mid-sequence.** *Mitigation:* on-entry detection of incomplete prior pass; reconcile `history.yaml` against the file tree.
- Re-scope **R2** so its mitigation matches its threat: either extend the gate or constrain `set` (decision required at Resolve).

---

## 8. Success Metrics — Analysis

### Clarifying Questions
- **M3** ("a contract-breaking patch aborts before write and leaves `document_data.yaml` byte-identical") proves the gate rejects *contract-breaking* patches. **It does not prove the gate rejects *corrupting-but-contract-clean* patches** — which §1/§5 show are possible. Does any metric cover the valid-but-gutted case? As written, M3 can pass while the real risk (silent valid corruption) ships untested.
- **M5** asserts "gap closed." **By what observable?** If it's sentinel-absence + validate-clean + renders, say so; "gap closed" implies semantic correctness the suite is forbidden to assert.
- **M2** asserts byte-deterministic view/history generation. **Does any view or history record embed wall-clock time** generated at render-of-view time (vs. the timestamp already stored in the report/log)? If so, determinism breaks. Confirm views derive *only* from stored data.

### What-If Scenarios
- All six metrics pass, lint and suite are green — and yet a refine that strips every comment from `document_data.yaml`, reorders its keys, and is unrecoverable still ships, because **no metric tests round-trip fidelity, rollback, or render-outcome truthfulness.** Green metrics would create false confidence in exactly the areas this report flags.

### Points for Improvement
- Add **M7 (round-trip fidelity):** a `document_data.yaml` with comments and a fixed key order survives an identity refine (e.g., a no-op `append_review_log`) with comments and order preserved (or, if canonicalization is accepted, the pre-refine snapshot exists and is byte-identical to the original).
- Add **M8 (valid-but-corrupting `set` is rejected):** a `set` that changes a `content.sections[*].body` to a non-string (or replaces `content.sections` wholesale) is rejected before write — forcing the §1 path decision (extended gate or constrained `set`) to be made and tested.
- Add **M9 (durability/rollback):** after any `commit_refine`, the prior `document_data.yaml` state is recoverable from `review_history/`.
- Sharpen **M5** to name its real observable (sentinel-absence + validate-clean + 3-format render), and confirm the **skill-mediated render path** has *some* coverage even if the test renders via `build.py` directly (cross-ref §3/§4).

---

## Top-of-stack for `/hyper-resolve` (triage priority)

1. **Validate-completeness vs. `set` reach** (§1, §5, R2, M3, M8) — decide: extend `validation_gate` *or* constrain `set` to leaf-scalar/no-auto-vivify. Everything else's safety claim depends on this.
2. **Source-of-truth durability** (§1, R7, M9) — gitignored + unversioned + `force=True` = irreversible; add a pre-refine snapshot.
3. **YAML round-trip fidelity** (§5, §6, R8, M7) — pin the serializer; PyYAML drops comments and reorders keys on the project's #1 invariant.
4. **Path DSL specification** (§5) — formal grammar, no `eval`, no auto-vivify; answers open question #1 concretely.
5. **`resolved` flag truthfulness & `history.render` truthfulness** (§4, §5, R9) — don't let the audit trail claim fixes/renders that didn't happen.
6. **Torn-pass / crash recovery & `history.yaml` reconciliation** (§5, R10) — detect incomplete prior passes; pick an authority between `history.yaml` and the file tree.

---

**Final Action:** Report saved to `spec/active/RedTeam_Report.md`. Run `/hyper-resolve` to begin triaging these vulnerabilities into the final SuperPRD and MiniPRDs.
