# MiniPRD: Red Team Skill (`ddo-red-team`)

**Hypergraph Node ID:** `skill_red_team`
**Parent Node:** `ddo_skills`
**Associated File:** `ddo/skills/ddo-red-team.md`
**Source SuperPRD:** `spec/compiled/SuperPRD_v0.0.2_AdversarialLoop.md`

## 1. The Confidence Mandate
- **Confidence Score: 9 / 10.** The firewall, persona resolution, severity enum, and emission contract are resolved. Residual: prose of the skill's adversarial prompt (cognitive, not mechanical).
- **Clarifying Questions:** none blocking.

## 2. Atomic User Stories
- **US-001:** As a reviewer, I want `ddo-red-team` to read the **MD/HTML render only** (never the PDF) and a persona lens, then emit `review_history/red_team_report_vN.yaml` via `ddo.review.write_report`.
- **US-002:** As a reviewer, I want persona resolution to default to `meta.persona` when present, require explicit selection otherwise, and **fail closed with a named error when `meta.persona` points at a missing file** (no silent fallback).
- **US-003:** As a reviewer, I want every finding to carry `severity ∈ {Critical,Major,Minor}` (fixed enum; non-enum = hard error), free-text `category`, and `decision_recorded:false`, `applied:false`, `resolution:null`.
- **US-004:** As a reviewer, I want `red_team_view_vN.md` generated deterministically by `ddo.review.render_report_view`, `vN` derived in code with `detect_incomplete_pass` run first, a soft warning above 100 findings, and the phase to end at `[WAITING FOR USER REVIEW]` instructing a **fresh context** before interview.

## 3. Implementation Plan (Task List)
- [ ] Create `ddo/skills/ddo-red-team.md` (HACF skill front-matter + ROLE + state machine), mirroring `ddo-ingest`/`ddo-render` structure.
- [ ] Wire persona resolution: `meta.persona` → file load; missing → hard named error; absent → explicit selection.
- [ ] Specify the critique → `findings[]` mapping and delegate persistence to `ddo.review.write_report` + view to `render_report_view`.
- [ ] Mandate the fresh-context firewall at entry; call `detect_incomplete_pass` before deriving `vN`.
- [ ] Add the >100-finding soft-warning instruction; end at `[WAITING FOR USER REVIEW]`.
- [ ] Add a `.claude/commands/` bridge if the project convention requires one.

## 4. The Negative Space (Constraints)
- **DO NOT** critique the PDF; read the MD/HTML render only.
- **DO NOT** inherit prior-phase conversation context; mandate a fresh context window at this boundary.
- **DO NOT** re-implement report writing, `_vN` derivation, or view generation — delegate to `ddo.review`.
- **DO NOT** silently fall back when `meta.persona` names a missing file.
- **DO NOT** invent a per-persona severity taxonomy; severity is the fixed enum.
- **DO NOT** auto-advance past `[WAITING FOR USER REVIEW]`.

## 5. Integration Tests & Verification
- **Test 1 (Deterministic):** the report/view it produces are validated by `ddo.review` contract tests (covered in `MiniPRD_LoopTestSuite`); persona-missing path raises a named error (unit-level via the resolver helper).
- **Test 2 (Novel):** the critique content is a **Candidate Artifact** — human-reviewed at the gate; tests assert only that emitted reports are structurally valid, never the finding prose.
