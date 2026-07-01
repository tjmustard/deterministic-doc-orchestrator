# MiniPRD: Hypergraph — reconcile `architecture.yml` for v0.0.5

**Hypergraph Node ID:** (maintenance — operates on `spec/compiled/architecture.yml`)
**Parent Node:** ddo_system
**DAG:** **LAST.** Blocked-by MP-1..MP-6 (all nodes must exist/land before reconciliation).

## 1. The Confidence Mandate
- **Confidence Score:** 10/10. Mechanical graph maintenance; node IDs and edges are enumerated in
  SuperPRD §5.3. Run `hypergraph_updater.py` after edits.
- **Clarifying Questions:** None.

## 2. Atomic User Stories
- **US-005/US-006/US-008 (systemic):** As a maintainer, I want the hypergraph to reflect the new
  style module + hardened skills so `/hyper-audit` can verify the blast radius.

## 3. Implementation Plan (Task List)
- [ ] **Hand-add 3 new nodes:**
  - [ ] `ddo_styles` — `dimension: Module`, `associated_file: ddo/styles/`,
        `edges.implements: [ddo_system]`, `status: needs_review` (new until audited).
  - [ ] `skill_create_style` — `dimension: Atomic`,
        `associated_file: ddo/skills/ddo-create-style.md`, `edges.implements: [ddo_skills]`,
        `edges.depends_on: [ddo_styles]`.
  - [ ] `test_styles_unit` — `dimension: Atomic`,
        `associated_file: tests/unit/test_styles.py`, `edges.implements: [tests_unit]`,
        `edges.depends_on: [ddo_styles]`.
- [ ] **Mark modified nodes `needs_review`:**
  - [ ] `ddo_schemas` (`meta.style_profile` + live defaults).
  - [ ] `ddo_skills` (module description + `ddo-ingest.md` injection — no Atomic node; note the
        concrete `ddo-ingest.md` change in the description so the audit targets the diff, per MP-3).
  - [ ] `skill_interview` (revision-prose injection).
  - [ ] `skill_red_team` (RT-3 header + RT-10 persona stem gate).
- [ ] Run `python .agents/scripts/hypergraph_updater.py spec/compiled/architecture.yml <node_id>`
      for each touched node to propagate blast-radius `needs_review`.
- [ ] Confirm the graph stays a DAG (no cycles introduced by the new `depends_on` edges).

## 4. The Negative Space (Constraints)
- **DO NOT** run this before MP-1..MP-6 land — nodes must exist first.
- **DO NOT** mark any node `clean` here — audit (`/hyper-audit`) flips `needs_review` → `clean`.
- **DO NOT** touch nodes outside the blast radius (`skill_refine`, `refine_engine`,
  `review_engine`, `validation_gate`, `build_orchestrator`, `ingest_helpers`, `path_deriver`,
  render/determinism test nodes).
- **DO NOT** add a node for `ddo-ingest.md` — it intentionally lives under the `ddo_skills` Module.

## 5. Integration Tests & Verification
- **Test 1 (Deterministic):** `hypergraph_updater.py` exits 0; the 3 new nodes are present with
  correct edges; the 4 modified nodes are `needs_review`; graph is acyclic.
- **Test 2 (Deterministic):** `/hyper-audit` can enumerate every v0.0.5 change against a concrete
  contract — including the `ddo-ingest.md` diff surfaced in the `ddo_skills` description (MP-3).
