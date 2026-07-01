# MiniPRD: Refine Skill (`ddo-refine`)

**Hypergraph Node ID:** `skill_refine`
**Parent Node:** `ddo_skills`
**Associated File:** `ddo/skills/ddo-refine.md`
**Source SuperPRD:** `spec/compiled/SuperPRD_v0.0.2_AdversarialLoop.md`

## 1. The Confidence Mandate
- **Confidence Score: 9 / 10.** The full commit sequence, snapshot, diff gate, skip-and-dependents, re-render flag pinning, and audit reconcile order are resolved. Residual: Before/After diff rendering ergonomics (cosmetic, settled in the skill).
- **Clarifying Questions:** none blocking.

## 2. Atomic User Stories
- **US-001:** As an author, I want `ddo-refine` to orchestrate the safe mutation sequence: `detect_incomplete_pass` → `snapshot_source` → `apply_patches` → `refine_structural_check` + `validate()` (in-memory) → Before/After diff → approval → `commit_refine` → re-render → audit reconcile.
- **US-002:** As an author, I want the Before/After diff to be a unified text diff of `sort_keys=False` serialized blocks (human-only, never re-parsed), gated by `approve all` / `skip <n>`, where **`skip <n>` also skips later approved patches that depend on it** (no self-inflicted dangling-ref abort).
- **US-003:** As an author, I want the re-render invoked via the **`ddo-render` skill** with flags derived from **`meta.template` + `meta.output_formats`** (never agent-remembered, never `build.py` directly).
- **US-004:** As an author, I want findings marked **`applied:true`** and the `history.yaml` record appended **only after** `commit_refine` and the re-render succeed, with `render` set from build.py's **actual exit status**; `acknowledge`/`dispute` decisions append to `meta.review_log`.

## 3. Implementation Plan (Task List)
- [ ] Create `ddo/skills/ddo-refine.md` (HACF skill front-matter + ROLE + state machine).
- [ ] Specify the ordered sequence with explicit abort-and-write-nothing semantics on any validate/structural failure.
- [ ] Implement the diff-presentation + `approve all`/`skip <n>` gate; encode skip-and-dependents using each patch's `depends_on`.
- [ ] Pin re-render: derive `--template`/`--format` from `meta.template`/`meta.output_formats`; invoke the `ddo-render` skill; capture exit status.
- [ ] After render success: `mark_findings(..., field="applied")`; build the `history.yaml` entry (incl. `render`, `applied` count); call `ddo.review.append_history`; route `acknowledge`/`dispute` to `meta.review_log` via an `append_review_log` patch.
- [ ] Enforce HITL gate; never auto-advance.

## 4. The Negative Space (Constraints)
- **DO NOT** call `build.py` directly; re-render only via the `ddo-render` skill.
- **DO NOT** mark a finding `applied:true` or append the history record before commit **and** re-render succeed.
- **DO NOT** record a `render` outcome not observed from build.py's actual exit status.
- **DO NOT** commit before the `document_data_pre_vN.yaml` snapshot exists.
- **DO NOT** re-parse the Before/After diff or any Markdown view back into data.
- **DO NOT** hand-pick re-render flags; derive them from `meta`.
- **DO NOT** let a `skip` of a depended-upon patch proceed to a dangling-ref abort; cascade the skip instead.

## 5. Integration Tests & Verification
- **Test 1 (Deterministic):** the engine-level guarantees it relies on (snapshot/rollback, constrained-`set` rejection, byte-unchanged-on-abort) are covered by `MiniPRD_RefineEngine` unit tests.
- **Test 2 (End-to-end, human-gated — M5):** the seeded-gap fixture loop asserts **sentinel-absence + `validate()`-clean + 3-format render**; the skill-mediated `ddo-refine → ddo-render` handoff is verified during the `DDO_FIXTURE_SIGNOFF` sign-off (logged). → `tests/integration/test_loop.py`.
- **Test 3 (Novel):** patch `value` content remains a **Candidate Artifact** — assert structure/safety and the `applied`/`render` truthfulness transitions, never the prose.
