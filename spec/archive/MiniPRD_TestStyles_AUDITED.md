# MiniPRD: TestStyles — glob structural validator for `ddo/styles/*.md`

**Hypergraph Node ID:** test_styles_unit  *(NEW — hand-add to architecture.yml)*
**Parent Node:** tests_unit
**Edges:** `implements: [tests_unit]`, `depends_on: [ddo_styles]`.
**DAG:** Blocked-by MP-1 (needs profiles to glob). Feeds MP-7.

## 1. The Confidence Mandate
- **Confidence Score:** 10/10. Contract mirrors `tests/unit/test_personas.py` (glob validator +
  dir-guard + negative parity). No prose-content assertions (D4).
- **Clarifying Questions:** None.

## 2. Atomic User Stories
- **US-005:** As a maintainer, I want the style file contract guarded so profiles stay consistent
  and `create-style` output is auto-covered.

## 3. Implementation Plan (Task List)
- [ ] Create `tests/unit/test_styles.py`.
- [ ] **`test_style_dir_has_files` guard (RT-9):** assert `ddo/styles/*.md` glob discovers ≥1
      file, mirroring `test_persona_dir_has_files`, so an empty dir fails **loudly**, not vacuously.
- [ ] **Glob + parametrize** over every `ddo/styles/*.md`, asserting per profile:
  - [ ] title heading `# **Style Profile: <name>**` present;
  - [ ] all five `##` section headings present (`Register & Audience`, `Voice & Person`,
        `Sentence & Structure`, `Diction`, `Avoid`);
  - [ ] every section body is **non-empty**;
  - [ ] **no sentinel tokens** (`[REQUIRES USER INPUT:` / `[[DDO::REQUIRES_INPUT:`).
- [ ] **Negative parity (RT-9):** add negative cases (via temp fixtures / parametrization) proving
      the validator **fails** on: a missing required heading, an empty section body, and a present
      sentinel token — mirroring `test_personas.py`'s negative suite.
- [ ] Use stdlib `re` only; do **not** assert prose content.
- [ ] Ensure `uv run pytest tests/unit/test_styles.py` is green against the three built-ins.

## 4. The Negative Space (Constraints)
- **DO NOT** hardcode profile names or a section **count** beyond the five required headings —
  glob the directory.
- **DO NOT** add a Markdown-parser dependency — stdlib `re` only.
- **DO NOT** assert prose content or register (that is HITL-judged, not CI-judged) (RT-7).
- **DO NOT** let the suite pass on an empty `ddo/styles/` — the dir-guard prevents vacuous green (RT-9).

## 5. Integration Tests & Verification
- **Test 1 (Deterministic):** all three built-ins pass every assertion; `uv run pytest` green.
- **Test 2 (Deterministic):** a profile missing a heading, with an empty body, or containing a
  sentinel token **fails**; an empty `ddo/styles/` trips `test_style_dir_has_files`.
