# MiniPRD: SkillInterview
**Hypergraph Node ID:** `skill_interview`
**File:** `ddo/skills/ddo-interview.md`
**Parent Node:** `ddo_skills`
**SuperPRD:** `SuperPRD_v0.0.3_StructuralPatchDSL.md`

## 1. Confidence Mandate
**Score: 10/10.** This is a cognitive node update — prose additions to a Markdown skill file. All required content is fully specified in §5.1 of the SuperPRD.

## 2. Atomic User Stories
- **US-1**: Skill generates correct `append`/`delete`/`insert` patch YAML when a finding requires structural changes.
- **US-2**: Skill warns against multiple index-bearing patches on the same parent list in one batch.
- **US-3**: Skill marks `append_evidence` and `append_review_log` as deprecated; instructs AI to use generic `append` instead.
- **US-4**: Skill clarifies that the interview decision prompt is the AI's self-declaration; the `skill_refine` Before/After diff is the human authorization gate.
- **US-5**: Skill instructs AI to check for dangling refs before issuing a `delete evidence_bank[N]` patch.

## 3. Implementation Plan

- [ ] Read `ddo/skills/ddo-interview.md` fully.
- [ ] Add new section **"Structural Patch Syntax (v0.0.3+)"** containing:
  - YAML examples for `append`, `delete`, `insert` using the `target:` field name (NOT `path:`).
  - Full path grammar rules table from SuperPRD §5.1.
  - `at` field constraint: `isinstance(at, int) and not isinstance(at, bool) and at >= 0`.
  - Note: AI-generated `value` is a Candidate Output — display full `value` in decision prompt before writing to interview log.
- [ ] Add **dangling-ref advisory** paragraph:
  - "Before issuing `delete evidence_bank[N]`, search `content.sections[*].evidence[]` for the entry's ID. If found, first issue `set` patches to update or remove each referencing path, then issue the delete as a later patch entry."
- [ ] Add **sequential-index warning** paragraph:
  - "Avoid generating multiple index-bearing patches targeting the same parent list in one batch. An earlier `insert` or `delete` on a list shifts the indices of all later elements — subsequent patches targeting index N on the same list in the same batch will operate on a different element than intended. If sequential index-bearing ops on the same list are unavoidable, list them explicitly in correct sequential order and document the expected index values at each step."
- [ ] Add **legacy op deprecation notice**:
  - "`append_evidence` is deprecated. Use `{target: "evidence_bank", op: "append", value: {...}}` instead."
  - "`append_review_log` is deprecated. Use `{target: "meta.review_log", op: "append", value: {...}}` instead."
  - "Both deprecated ops will be removed in v0.0.4."
- [ ] Run no tests (cognitive node — no code). Verify the file renders readable Markdown.

## 4. Negative Space (Constraints)

- **DO NOT** change any existing skill prose that describes `set` or the overall interview flow.
- **DO NOT** remove `append_evidence` or `append_review_log` from the skill's valid op examples in v0.0.3 — they are deprecated but not yet removed.
- **DO NOT** use `path:` as the field name in YAML examples — use `target:` consistently.

## 5. Integration Tests & Verification

- **Manual check:** Skill YAML examples are syntactically valid YAML.
- **Manual check:** Field names in examples use `target:`, not `path:`.
- **Manual check:** Sequential-index warning paragraph is present.
- **Manual check:** Deprecation notice for both legacy ops is present.
- **Manual check:** Dangling-ref advisory is present before the `delete` op description.
