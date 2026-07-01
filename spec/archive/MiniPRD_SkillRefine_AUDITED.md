# MiniPRD: SkillRefine
**Hypergraph Node ID:** `skill_refine`
**File:** `ddo/skills/ddo-refine.md`
**Parent Node:** `ddo_skills`
**SuperPRD:** `SuperPRD_v0.0.3_StructuralPatchDSL.md`

## 1. Confidence Mandate
**Score: 10/10.** Cognitive node update — prose additions only. All required content is fully specified.

## 2. Atomic User Stories
- **US-1**: Skill displays `DanglingRefError` clearly when `apply_patches` raises it — showing the `.paths` list and instructing the interview agent to fix refs first.
- **US-2**: Skill handles multi-line Before/After diffs for structural ops (added/removed YAML objects) — displays verbatim without truncation.
- **US-3**: Skill clarifies that it is the human authorization gate (the Before/After diff is where the human approves; the interview prompt was just the AI's proposal).

## 3. Implementation Plan

- [ ] Read `ddo/skills/ddo-refine.md` fully.
- [ ] Update Before/After diff section:
  - Add note: structural ops (`append`, `insert`) produce multi-line diffs showing the full added YAML object; `delete` produces a multi-line removal. Display the full diff verbatim — do not truncate or summarize.
  - Add note: the Before/After diff is the **human authorization gate**. The AI interview agent's display of the `value` in the decision prompt was a proposal; the diff is where the human confirms the actual mutation before commit.
- [ ] Add DanglingRefError handling section:
  - "If `ddo-refine` raises `DanglingRefError`, output the exception's `.paths` list to the human in this format: 'Refused: evidence_bank[N] is still referenced at: [path1, path2, ...]'"
  - "Instruct the interview agent to issue `set` patches to update or remove each referencing path, then resubmit the delete as a later patch entry in the next batch."
  - "Do NOT proceed with the delete. Do NOT modify `document_data.yaml`."
- [ ] Run no tests (cognitive node). Verify the file renders readable Markdown.

## 4. Negative Space (Constraints)

- **DO NOT** change the existing Before/After diff approval flow (`approve all` / `skip <n>`).
- **DO NOT** re-parse the Before/After diff programmatically — it is human-only display.
- **DO NOT** attempt to auto-fix DanglingRefError — surface it and defer to the interview agent.

## 5. Integration Tests & Verification

- **Manual check:** DanglingRefError handling section is present and clear.
- **Manual check:** Multi-line diff note is present in the Before/After diff section.
- **Manual check:** Human authorization gate framing is present.
