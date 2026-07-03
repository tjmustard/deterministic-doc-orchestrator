# MiniPRD: MeetingAgenda — self-contained worked example (persona + style + schema + 3 templates + example + evidence)

**Hypergraph Node ID:** `ddo_schemas`, `ddo_templates`, `ddo_personas`, `ddo_styles`, `render_fixture` *(all EXIST — mark needs_review, modify; do NOT add)*
**Parent Node:** `ddo_system`
**DAG:** Blocked-by MP-0. Self-contained. **Time-boxed agenda items are string literals — the
sharpest RT-09 clock-purity risk.**

## 1. The Confidence Mandate
- **Confidence Score:** 10/10. Additive domain files only. `validation.py`/`build.py` unchanged.
- **Clarifying Questions:** None.

## 2. Atomic User Stories
- **US-004:** As a user, I want a `meeting_agenda` type that renders deterministically.
- **US-005:** As a user, I want it to ship persona `meeting_facilitator` + style `agenda_directive`.

## 3. Implementation Plan (Task List)
- [ ] **Persona:** `ddo/personas/meeting_facilitator.md` (v0.0.4 AV-table). Lens: objective
      clarity, time-box realism, owner attribution, pre-read sufficiency.
- [ ] **Style:** `ddo/styles/agenda_directive.md` (v0.0.5 five-section). Imperative, scannable,
      directive register — **phrasing-only**, no quantitative content imperatives (RT-14).
- [ ] **Schema:** `ddo/schemas/meeting_agenda.yaml` — minimal contract. `meta.persona: meeting_facilitator`,
      `meta.style_profile: agenda_directive`, `meta.template: meeting_agenda`,
      `output_formats: [pdf, html, md]`. Sections: `meeting_objective`, `agenda_items`
      (time-boxed, owner-attributed), `pre_reads`, `logistics`.
- [ ] **Narrative source (RT-04):** `tutorials/ddo-v006-authoring-custom-structures/input_files/meeting_agenda_source.md`.
- [ ] **Templates (×3):** `typst/meeting_agenda.typst`, `jinja2/meeting_agenda.html.jinja2`,
      `jinja2/meeting_agenda.md.jinja2`. **`agenda_items` durations/times are rendered as the
      literal strings in the YAML — no duration arithmetic, no `now()`, no locale time
      formatting (RT-09).**
- [ ] **Example YAML:** `tests/data/meeting_agenda_example.yaml` — time-boxes as string literals
      (e.g. `"0:00–0:10"`), owners as strings; genuine minimal `evidence_bank` (≥1 ref) traced
      to the source doc.
- [ ] **Enroll in `EXAMPLES`:** `("meeting_agenda", "meeting_agenda_example.yaml")`.
- [ ] Render all three formats → exit 0 each.
- [ ] `uv run ruff check . && uv run ruff format --check .` → 0; `uv run pytest` green.

## 4. The Negative Space (Constraints)
- **DO NOT** compute or sum time-boxes in any template — they are opaque string literals (RT-09).
- **DO NOT** call `now()`/`today()`/locale time in the Typst or Jinja2 templates (RT-09, M3b).
- **DO NOT** give the example an empty `evidence_bank` (RT-04).
- **DO NOT** put quantitative/content imperatives in `agenda_directive.md` (RT-14).

## 5. Integration Tests & Verification
- **Test 1 (Deterministic):** three-format byte-identical repeat renders; M3b timestamp
  determinism proves no clock read (RT-09).
- **Test 2 (Deterministic):** `test_schema_meta_refs.py` resolves `meeting_facilitator` +
  `agenda_directive`; section ids ⊆ schema (RT-08/10).
- **Test 3 (Novel):** consuming tutorial prose is a Candidate Artifact → HITL in MP-6.
