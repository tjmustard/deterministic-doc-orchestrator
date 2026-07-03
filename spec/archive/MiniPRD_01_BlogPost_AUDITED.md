# MiniPRD: BlogPost — self-contained worked example (persona + style + schema + 3 templates + example + evidence)

**Hypergraph Node ID:** `ddo_schemas`, `ddo_templates`, `ddo_personas`, `ddo_styles`, `render_fixture` *(all EXIST — mark needs_review, modify; do NOT add)*
**Parent Node:** `ddo_system`
**DAG:** Blocked-by MP-0 (consolidated `EXAMPLES`, `test_schema_meta_refs.py`). Self-contained:
ships its persona, style, schema, templates, example, and narrative evidence source together —
so `meta.persona`/`meta.style_profile` never dangle (RT-08 ordering hazard eliminated).

## 1. The Confidence Mandate
- **Confidence Score:** 10/10. Additive domain files only; modeled on the proven
  `prd`/`scientific_report` worked examples. `validation.py` and `build.py` unchanged.
- **Clarifying Questions:** None.

## 2. Atomic User Stories
- **US-004:** As a user, I want a `blog_post` type that renders deterministically as a trustworthy example.
- **US-005:** As a user, I want `blog_post` to ship a dedicated persona (`content_editor`) and style (`blog_casual`).

## 3. Implementation Plan (Task List)
- [ ] **Persona:** author `ddo/personas/content_editor.md` in the v0.0.4 AV-table format
      (attribute/value table; mirror `ddo/personas/product_critic.md` structure). Editorial lens:
      clarity, hook strength, reader-CTA integrity. Auto-covered by `test_personas.py`.
- [ ] **Style:** author `ddo/styles/blog_casual.md` in the v0.0.5 five-section format (mirror
      `ddo/styles/conversational.md`). **Phrasing/register-only** — no quantitative/content
      imperatives (v0.0.5 rubric, RT-14). Auto-covered by `test_styles.py`.
- [ ] **Schema:** author `ddo/schemas/blog_post.yaml` — minimal contract (`meta` +
      `content.sections[*]` + `evidence_bank`). `meta.persona: content_editor`,
      `meta.style_profile: blog_casual`, `meta.template: blog_post`,
      `meta.output_formats: [pdf, html, md]`. Sections: `hook`, `context`, `main_point`,
      `supporting_detail`, `conclusion_cta`.
- [ ] **Narrative source (RT-04):** author `tutorials/ddo-v006-authoring-custom-structures/input_files/blog_post_source.md`
      — a short real brief/notes doc that the example's evidence traces to (mirrors the
      adversarial-loop tutorial's `copolyester-optimization.md`). *(Directory created here if
      absent; Tutorial 2 prose is authored in MP-6.)*
- [ ] **Templates (×3):** `ddo/templates/typst/blog_post.typst`,
      `ddo/templates/jinja2/blog_post.html.jinja2`, `ddo/templates/jinja2/blog_post.md.jinja2`.
      Model on the `prd` templates. **Pure functions of the YAML — no `now()`/clock/locale (RT-09).**
- [ ] **Example YAML:** author `tests/data/blog_post_example.yaml` — a complete casual blog with
      a **genuine, minimal `evidence_bank`** whose entries trace to `blog_post_source.md`
      (≥1 referenced entry — must not be evidence-free, `validation.py:106`).
- [ ] **Enroll in `EXAMPLES`:** add `("blog_post", "blog_post_example.yaml")` to the consolidated
      list (MP-0) — inherits M1/M2/M3/M3b.
- [ ] Render all three formats: `uv run ddo/build.py --data tests/data/blog_post_example.yaml
      --template blog_post --format <pdf|html|md> --output <tmp>` → exit 0 each.
- [ ] `uv run ruff check . && uv run ruff format --check .` → 0; `uv run pytest` green.

## 4. The Negative Space (Constraints)
- **DO NOT** give the example an empty `evidence_bank` — casual ≠ citation-free (RT-04).
- **DO NOT** read a clock/locale in any `blog_post` template (RT-09).
- **DO NOT** put quantitative/content-bearing imperatives in `blog_casual.md` (RT-14).
- **DO NOT** modify `validation.py`/`build.py`; the contract is unchanged.
- **DO NOT** ship a partial format set — all three formats required.

## 5. Integration Tests & Verification
- **Test 1 (Deterministic):** `blog_post_example.yaml` renders byte-identically across repeated
  runs for all three formats (M1/M2/M3/M3b via `EXAMPLES`).
- **Test 2 (Deterministic):** `test_schema_meta_refs.py` resolves `content_editor` +
  `blog_casual` and confirms the example's section ids ⊆ `blog_post` schema sections (RT-08/10).
- **Test 3 (Novel):** the `tutorial.md` prose consuming this example is a Candidate Artifact →
  HITL sign-off in MP-6; not parsed programmatically.
