# MiniPRD: ProjectReport — self-contained worked example (persona + style + schema + 3 templates + example + evidence)

**Hypergraph Node ID:** `ddo_schemas`, `ddo_templates`, `ddo_personas`, `ddo_styles`, `render_fixture` *(all EXIST — mark needs_review, modify; do NOT add)*
**Parent Node:** `ddo_system`
**DAG:** Blocked-by MP-0. Self-contained. The formal-register anchor of the four (casual→formal
breadth: `blog_post` … `project_report`).

## 1. The Confidence Mandate
- **Confidence Score:** 10/10. Additive domain files only. `validation.py`/`build.py` unchanged.
- **Clarifying Questions:** None.

## 2. Atomic User Stories
- **US-004:** As a user, I want a `project_report` type that renders deterministically.
- **US-005:** As a user, I want it to ship persona `project_stakeholder` + style `executive_formal`.

## 3. Implementation Plan (Task List)
- [ ] **Persona:** `ddo/personas/project_stakeholder.md` (v0.0.4 AV-table). Lens: status honesty,
      risk surfacing, metric traceability, decision-readiness.
- [ ] **Style:** `ddo/styles/executive_formal.md` (v0.0.5 five-section). Concise executive
      register — **phrasing-only** (RT-14). **Must be materially distinct from the shipped
      `formal_professional.md`** (avoid a paraphrase specimen — RT-14 quality note): executive =
      decision-oriented, front-loaded summary, quantified-status framing without inventing
      quantities.
- [ ] **Schema:** `ddo/schemas/project_report.yaml` — minimal contract. `meta.persona: project_stakeholder`,
      `meta.style_profile: executive_formal`, `meta.template: project_report`,
      `output_formats: [pdf, html, md]`. Sections: `executive_summary`, `status`, `milestones`,
      `risks`, `metrics`, `next_steps`.
- [ ] **Narrative source (RT-04):** `tutorials/ddo-v006-authoring-custom-structures/input_files/project_report_source.md`
      — the raw status inputs the metrics/risks trace to.
- [ ] **Templates (×3):** `typst/project_report.typst`, `jinja2/project_report.html.jinja2`,
      `jinja2/project_report.md.jinja2`. Pure functions of the YAML — **no clock/locale (RT-09);
      `metrics`/`milestones` are literal strings, no computed rollups.**
- [ ] **Example YAML:** `tests/data/project_report_example.yaml` — genuine `evidence_bank`
      (≥1 ref) traced to the source; metrics as literal strings.
- [ ] **Enroll in `EXAMPLES`:** `("project_report", "project_report_example.yaml")`.
- [ ] Render all three formats → exit 0 each.
- [ ] `uv run ruff check . && uv run ruff format --check .` → 0; `uv run pytest` green.

## 4. The Negative Space (Constraints)
- **DO NOT** make `executive_formal.md` a paraphrase of `formal_professional.md` — it must teach
  a distinct register (RT-14 quality).
- **DO NOT** compute metric rollups or dates in any template (RT-09).
- **DO NOT** give the example an empty `evidence_bank` (RT-04).
- **DO NOT** modify `validation.py`/`build.py`.

## 5. Integration Tests & Verification
- **Test 1 (Deterministic):** three-format byte-identical repeat renders (M1/M2/M3/M3b).
- **Test 2 (Deterministic):** `test_schema_meta_refs.py` resolves `project_stakeholder` +
  `executive_formal`; section ids ⊆ schema (RT-08/10).
- **Test 3 (Novel):** consuming tutorial prose is a Candidate Artifact → HITL in MP-6.
