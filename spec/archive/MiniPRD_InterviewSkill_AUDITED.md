# MiniPRD: Interview Skill (`ddo-interview`)

**Hypergraph Node ID:** `skill_interview`
**Parent Node:** `ddo_skills`
**Associated File:** `ddo/skills/ddo-interview.md`
**Source SuperPRD:** `spec/compiled/SuperPRD_v0.0.2_AdversarialLoop.md`

## 1. The Confidence Mandate
- **Confidence Score: 9 / 10.** Batching, decision vocabulary, the flag split, and the in-place atomic update are resolved. Residual: the conversational phrasing of each batch (cognitive).
- **Clarifying Questions:** none blocking.

## 2. Atomic User Stories
- **US-001:** As an author, I want `ddo-interview` to load `red_team_report_vN.yaml`, filter `applied:false`, sort Critical→Major→Minor, and present `batch_size` (default 2) findings per turn, halting at `[WAITING FOR USER RESPONSE]`.
- **US-002:** As an author, I want each resolution to record `finding_id`, `decision ∈ {revise, add_evidence, acknowledge, dispute, defer}`, free-text `detail`, and a structured `patch` (null for acknowledge/dispute/defer), persisted via `ddo.review.write_interview_log`.
- **US-003:** As an author, I want commit to mark the resolved findings **`decision_recorded:true`** (atomic in-place via `ddo.review.mark_findings`) — and explicitly **not** `applied`, which only `ddo-refine` sets after the patch lands.
- **US-004:** As an author, I want partial resolution allowed: `defer` is a first-class decision and un-addressed findings simply stay `applied:false` for a later pass.

## 3. Implementation Plan (Task List)
- [ ] Create `ddo/skills/ddo-interview.md` (HACF skill front-matter + ROLE + paced state machine, mirroring `/hyper-resolve`'s 2-per-turn pacing where apt).
- [ ] Wire load/filter/sort from `red_team_report_vN.yaml` (filter `applied:false`).
- [ ] Specify the `patch` shape (op/target/value, optional `depends_on`) and delegate persistence to `ddo.review.write_interview_log`.
- [ ] On commit, call `ddo.review.mark_findings(..., field="decision_recorded")`; never touch `applied`.
- [ ] Enforce `[WAITING FOR USER RESPONSE]` per batch; never auto-advance.

## 4. The Negative Space (Constraints)
- **DO NOT** set `applied` — that belongs to `ddo-refine` after a successful commit + render.
- **DO NOT** write `document_data.yaml` from this skill; it only writes the interview log and updates report flags.
- **DO NOT** re-implement log writing or the flag update — delegate to `ddo.review`.
- **DO NOT** auto-advance past `[WAITING FOR USER RESPONSE]` or exceed `batch_size` per turn.
- **DO NOT** parse any Markdown view as input; read the machine-readable report YAML only.

## 5. Integration Tests & Verification
- **Test 1 (Deterministic):** given a fixed report, the produced `interview_log_vN.yaml` passes `validate_interview_log`, and `mark_findings` flips only `decision_recorded` (report otherwise byte-stable). → covered in `MiniPRD_LoopTestSuite`.
- **Test 2 (Novel):** resolution `detail`/`patch.value` are **Candidate Artifacts** — assert log structure and flag transitions only, never the user-authored prose.
