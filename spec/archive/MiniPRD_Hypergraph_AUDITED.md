# MiniPRD: Hypergraph — mark dirty, hand-add node, run updater

**Hypergraph Node ID:** architecture_graph
**Parent Node:** (root / spec)

## 1. The Confidence Mandate
- **Confidence Score:** 10/10. RT-01 verified: `hypergraph_updater.propagate_blast_radius` is a
  dict-keyed upsert with **no node-add capability** — node creation is a manual YAML edit; duplicate
  ids are impossible. `test_personas_unit` already exists (448-463).
- **Clarifying Questions:** None.

## 2. Atomic User Stories
- **US-005 (infra):** As a maintainer, I want the architecture graph to reflect the v0.0.4 changes with
  exactly one node per id and correct blast-radius status propagation.

## 3. Implementation Plan (Task List)
- [ ] **Hand-add** the `skill_create_persona` node to `spec/compiled/architecture.yml`:
      `dimension: Atomic`, `status: dirty`, `associated_file: ddo/skills/ddo-create-persona.md`,
      `edges: { implements: [ddo_skills], depends_on: [ddo_personas] }` — **no `ddo_core`** (RT-12).
- [ ] Set `status: dirty` on the existing `test_personas_unit` node (do **not** add a second one — RT-01).
- [ ] Regenerate the 3 prose op-references in node descriptions (lines ≈ 518, 587, 663) to drop
      `append_evidence` / `append_review_log` from the enumerated op lists (RT-14).
- [ ] Run: `python .agents/scripts/hypergraph_updater.py spec/compiled/architecture.yml ddo_personas
      skill_red_team skill_interview review_engine refine_engine test_personas_unit skill_create_persona`
      to propagate `needs_review` across the blast radius.
- [ ] Assert post-run: exactly **one** `test_personas_unit` and **one** `skill_create_persona` node
      (no duplicate ids); dependents are marked `needs_review`.

## 4. The Negative Space (Constraints)
- **DO NOT** pass `test_personas_unit` or `skill_create_persona` to the updater expecting it to *create*
  them — the updater only mutates `status`; nodes are added by hand-editing the YAML first (RT-01).
- **DO NOT** create a duplicate `test_personas_unit` node — it already exists (RT-01).
- **DO NOT** give `skill_create_persona` a `ddo_core` dependency (RT-12).

## 5. Integration Tests & Verification
- **Test 1 (Deterministic):** `grep -c "id: test_personas_unit"` and `grep -c "id: skill_create_persona"`
  on `architecture.yml` each return `1`.
- **Test 2 (Deterministic):** `grep -n "append_evidence\|append_review_log" spec/compiled/architecture.yml`
  returns no matches after regeneration (RT-14).
