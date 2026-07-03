# MiniPRD: MeetingNotes — self-contained worked example (persona + style + schema + 3 templates + example + evidence)

**Hypergraph Node ID:** `ddo_schemas`, `ddo_templates`, `ddo_personas`, `ddo_styles`, `render_fixture` *(all EXIST — mark needs_review, modify; do NOT add)*
**Parent Node:** `ddo_system`
**DAG:** Blocked-by MP-0. Self-contained. **Carries the deliberate non-ASCII fixture value (RT-12).**

## 1. The Confidence Mandate
- **Confidence Score:** 10/10. Additive domain files only. `validation.py`/`build.py` unchanged.
- **Clarifying Questions:** None.

## 2. Atomic User Stories
- **US-004:** As a user, I want a `meeting_notes` type that renders deterministically.
- **US-005:** As a user, I want it to ship persona `meeting_recorder` + style `notes_concise`.

## 3. Implementation Plan (Task List)
- [ ] **Persona:** `ddo/personas/meeting_recorder.md` (v0.0.4 AV-table). Lens: fidelity of the
      record, decision/owner capture, no editorializing. Auto-covered by `test_personas.py`.
- [ ] **Style:** `ddo/styles/notes_concise.md` (v0.0.5 five-section). Terse, bulleted, minimal
      connective prose — **register-only**, no content imperatives (RT-14).
- [ ] **Schema:** `ddo/schemas/meeting_notes.yaml` — minimal contract. `meta.persona: meeting_recorder`,
      `meta.style_profile: notes_concise`, `meta.template: meeting_notes`,
      `output_formats: [pdf, html, md]`. Sections: `attendees`, `agenda_covered`, `decisions`,
      `action_items`, `next_steps`.
- [ ] **Narrative source (RT-04):** `tutorials/ddo-v006-authoring-custom-structures/input_files/meeting_notes_source.md`
      — raw meeting notes the example's evidence traces to.
- [ ] **Templates (×3):** `typst/meeting_notes.typst`, `jinja2/meeting_notes.html.jinja2`,
      `jinja2/meeting_notes.md.jinja2`. Pure functions of the YAML — **no computed "today"/
      duration/clock (RT-09).**
- [ ] **Example YAML:** `tests/data/meeting_notes_example.yaml` with a genuine minimal
      `evidence_bank` (≥1 ref) traced to `meeting_notes_source.md`. **Include one deliberately
      non-ASCII value — an accented attendee name (e.g. `José Peña`) — to force the Typst
      font-coverage question now (RT-12).**
- [ ] **Enroll in `EXAMPLES`:** `("meeting_notes", "meeting_notes_example.yaml")`.
- [ ] Render all three formats → exit 0 each. **If the non-ASCII glyph breaks Typst M3
      byte-identity, that is the RT-12 signal to surface now** — resolve via the pinned font set
      before promotion, do not silently drop the accented value.
- [ ] `uv run ruff check . && uv run ruff format --check .` → 0; `uv run pytest` green.

## 4. The Negative Space (Constraints)
- **DO NOT** give the example an empty `evidence_bank` (RT-04).
- **DO NOT** compute times/dates in any template — agenda-covered/next-steps are string literals (RT-09).
- **DO NOT** remove the non-ASCII value to make PDF pass — fix font coverage instead (RT-12).
- **DO NOT** modify `validation.py`/`build.py`.

## 5. Integration Tests & Verification
- **Test 1 (Deterministic):** three-format byte-identical repeat renders (M1/M2/M3/M3b),
  **including the non-ASCII attendee name in PDF** (RT-12 proof).
- **Test 2 (Deterministic):** `test_schema_meta_refs.py` resolves `meeting_recorder` +
  `notes_concise`; section ids ⊆ schema (RT-08/10).
- **Test 3 (Novel):** consuming tutorial prose is a Candidate Artifact → HITL in MP-6.
