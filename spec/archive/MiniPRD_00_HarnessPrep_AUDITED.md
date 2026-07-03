# MiniPRD: HarnessPrep — consolidate EXAMPLES, add `slow` marker, add `test_schema_meta_refs.py`

**Hypergraph Node ID:** `test_render_determinism`, `render_fixture`, `tests_integration` *(all EXIST — mark needs_review, modify; do NOT add)*
**Parent Node:** `ddo_system`
**DAG:** First. Blocks MP-1..MP-4 (they enroll in the consolidated `EXAMPLES` and are checked
by `test_schema_meta_refs.py`). No new document types are introduced here — every new test
passes green against the existing `prd` / `scientific_report` examples.

## 1. The Confidence Mandate
- **Confidence Score:** 10/10. Pure test-infrastructure change. `EXAMPLES` is currently a
  duplicated literal (`tests/integration/conftest.py:17` and
  `tests/integration/test_render_determinism.py:19`); both new guards read existing files only.
  No `ddo/*.py` change.
- **Clarifying Questions:** None.

## 2. Atomic User Stories
- **US-004 (partial):** As a user, I want new types enrolled once so determinism coverage
  cannot silently under-cover (RT-03).
- **US-005 (partial):** As a user, I want `meta.persona`/`meta.style_profile` resolution
  CI-enforced so a typo fails loudly (RT-08).
- **US-007 (partial):** As a contributor, I want the default suite fast and the full matrix
  gated so runtime stays bounded (RT-11).

## 3. Implementation Plan (Task List)
- [ ] **Consolidate `EXAMPLES` (RT-03):** keep the single source-of-truth list in
      `tests/integration/conftest.py`; in `test_render_determinism.py` **delete** its local
      `EXAMPLES` literal (line 19) and `from conftest import EXAMPLES` (or `from .conftest import EXAMPLES`
      per the package layout). Confirm the three parametrize sites + the line-201 promotion
      helper still resolve.
- [ ] **Add a guard for the consolidation invariant:** if a full import is undesirable, instead
      add a test asserting the two literals are equal — but the preferred path is a single
      imported definition (only add the equality guard if execution keeps two lists).
- [ ] **Register the `slow` marker (RT-11):** in `pyproject.toml` `[tool.pytest.ini_options]`
      add `markers = ["slow: full determinism cross-product (CI only)"]` and
      `addopts = "-m 'not slow'"` (preserve any existing addopts). Mark the full
      `EXAMPLES × [pdf,html,md]` parametrized determinism tests `@pytest.mark.slow`, leaving one
      fast per-example format (e.g. `md`) unmarked as a smoke subset. Document that CI runs the
      full suite (no `-m` filter, or `-m 'slow or not slow'`).
- [ ] **Add `tests/integration/test_schema_meta_refs.py` (RT-08 + RT-10):** for every
      `ddo/schemas/*.yaml` **and** every `tests/data/*.yaml`:
      - assert `meta.persona` → `ddo/personas/<stem>.md` exists (when `persona` is present);
      - assert `meta.style_profile` → `ddo/styles/<stem>.md` exists (when present);
      - **soft schema-conformance:** assert each example's `content.sections[*].id` set is a
        subset of the section-id set declared by its schema (`meta.template`/`doc_type` → schema).
      - Stem gate: reuse the `^[a-z][a-z0-9_]*$` rule already used for persona/style resolution.
- [ ] Run `uv run pytest tests/integration/test_schema_meta_refs.py` — must pass green against
      the two existing schemas/examples (`product_critic`/`scientific_reviewer` personas,
      `formal_professional`/`technical_precise` styles all resolve today).
- [ ] `uv run ruff check . && uv run ruff format --check .` → 0.

## 4. The Negative Space (Constraints)
- **DO NOT** modify any `ddo/*.py` module — this is a `tests/` + `pyproject.toml` change only.
- **DO NOT** leave two `EXAMPLES` literals unguarded — either one imported definition (preferred)
  or an equality guard.
- **DO NOT** make the fast default suite skip determinism entirely — keep one format per example
  unmarked so a smoke signal survives `-m 'not slow'`.
- **DO NOT** hard-code the current two example basenames in `test_schema_meta_refs.py` — glob
  `ddo/schemas/*.yaml` and `tests/data/*.yaml` so new types are auto-covered.

## 5. Integration Tests & Verification
- **Test 1 (Deterministic):** `EXAMPLES` imported in both files → the existing M1/M2/M3/M3b
  parametrized tests still enumerate `[("prd",...),("scientific_report",...)]` identically.
- **Test 2 (Deterministic):** `test_schema_meta_refs.py` green on the two shipped schemas/examples;
  a deliberately typo'd `meta.persona` (local scratch, not committed) makes it **red** — proving
  the guard bites (RT-08).
- **Test 3 (Deterministic):** `uv run pytest -m 'not slow'` runs the fast subset; `uv run pytest`
  with the `slow` marker included runs the full matrix — both green.
