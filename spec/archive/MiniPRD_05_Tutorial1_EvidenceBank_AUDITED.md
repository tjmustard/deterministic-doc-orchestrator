# MiniPRD: Tutorial1_EvidenceBank — citation-integrity lens on `ingest_output.yaml`

**Hypergraph Node ID:** `tutorials` *(NEW node registered in MP-8 — this MiniPRD authors its content)*
**Parent Node:** `ddo_system`
**DAG:** Blocked-by MP-0. Independent of the four doc types (anchors to an existing fixture).

## 1. The Confidence Mandate
- **Confidence Score:** 10/10. Hand-authored Markdown tutorial directory following the shipped
  convention; anchors to the **existing human-promoted** `tests/fixtures/ingest_output.yaml`.
  No new fixtures authored.
- **Clarifying Questions:** None.

## 2. Atomic User Stories
- **US-001:** As a new user, I want an evidence-bank / citation-integrity tutorial so I understand
  how claims trace to sources.

## 3. Implementation Plan (Task List)
- [ ] Create `tutorials/ddo-v006-evidence-bank-workflow/` with the full convention:
      `tutorial.md`, `input_files/`, `output_files/`, `code_samples/`, `screenshots/`.
- [ ] `input_files/ingest_output.yaml` = **byte-identical copy** of
      `tests/fixtures/ingest_output.yaml`. This copy is registered in `EXPECTED_MIRRORS`
      (MP-8) mapping to the **`tests/fixtures/`** source (RT-01).
- [ ] **Provenance note (RT-05):** `tutorial.md` explicitly states the boundary — this copy is a
      teaching mirror of a `DDO_FIXTURE_SIGNOFF`-gated fixture; the fixture is canonical and the
      copy is guarded for sameness (not provenance). Readers must not edit the copy to change
      ground truth.
- [ ] `tutorial.md` teaches: evidence_bank structure, `content.sections[*].evidence` → bank-id
      referencing, the zero-hallucination sentinel, and how `validation.py` rejects dangling /
      contentless evidence. **Framed as a lens, not the loop.**
- [ ] **Falsifiable non-duplication (US-001 AC3 / RT-15):** `tutorial.md` contains **zero**
      `ddo-refine` / `ddo-interview` command invocations; it **links** to
      `ddo-adversarial-loop-v0.0.2` rather than re-walking the loop.
- [ ] `code_samples/*.py` (if any) are ruff-clean runnable snippets (RT-06).
- [ ] Do **not** author any `output_files/` render for Tutorial 1 (it inspects, it does not
      render — the render metric belongs to Tutorial 2, RT-15). If a screenshot is used, place it
      in `screenshots/`.

## 4. The Negative Space (Constraints)
- **DO NOT** invoke `ddo-refine`/`ddo-interview` in `tutorial.md` — that is the loop tutorial (RT-15).
- **DO NOT** author or edit `tests/fixtures/ingest_output.yaml` — reference the promoted fixture only.
- **DO NOT** let the `input_files/` copy drift from the fixture — byte-identical, guarded in MP-8.
- **DO NOT** claim Tutorial 1 renders a document — it does not (RT-15).
- **DO NOT** invent a new tutorial layout.

## 5. Integration Tests & Verification
- **Test 1 (Deterministic):** MP-8's `test_tutorial_refs.py` asserts
  `input_files/ingest_output.yaml` is byte-identical to `tests/fixtures/ingest_output.yaml`
  and that the pair is present in `EXPECTED_MIRRORS` (RT-01).
- **Test 2 (Deterministic):** a grep-style check (in MP-8's guard or a reviewer step) confirms
  zero `ddo-refine`/`ddo-interview` invocations in `tutorial.md` (US-001 AC3, RT-15).
- **Test 3 (Novel):** `tutorial.md` prose is a Candidate Artifact → HITL sign-off; not parsed
  programmatically.
