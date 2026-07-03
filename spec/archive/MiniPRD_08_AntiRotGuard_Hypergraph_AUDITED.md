# MiniPRD: AntiRotGuard_Hypergraph — `test_tutorial_refs.py` (EXPECTED_MIRRORS) + `output_files` guard + graph registration

**Hypergraph Node ID:** `test_tutorial_refs_unit` *(NEW — Atomic)*, `tutorials` *(NEW — Module, register)*, `tests_unit`, `ddo_system`
**Parent Node:** `ddo_system`
**DAG:** Last. Blocked-by MP-5, MP-6, MP-7 (all `input_files/` copies and `output_files/`
renders must exist before the guard maps and verifies them). **This MiniPRD builds the PRD's
only new enforcement surface — as originally drafted it could pass green while checking nothing
(RT-01/02); it is specified here so it cannot.**

## 1. The Confidence Mandate
- **Confidence Score:** 10/10. New `tests/*.py` + one `hypergraph_updater.py` run. No `ddo/*.py`
  change. Every mechanism references files that exist by this DAG stage.
- **Clarifying Questions:** None.

## 2. Atomic User Stories
- **US-006:** As a maintainer, I want tutorials guarded against fixture rot so drifted/renamed
  fixtures fail CI loudly.
- **US-008:** As a maintainer, I want committed tutorial renders to stay reproducible.

## 3. Implementation Plan (Task List)

### A. Anti-rot guard — `tests/unit/test_tutorial_refs.py` (RT-01/02/05/13)
- [ ] Define an explicit in-repo `EXPECTED_MIRRORS` mapping `{input_path: source_path}` covering
      **both** source roots:
      - `.../ddo-v006-evidence-bank-workflow/input_files/ingest_output.yaml` → `tests/fixtures/ingest_output.yaml`
      - `.../ddo-v006-authoring-custom-structures/input_files/blog_post_example.yaml` → `tests/data/blog_post_example.yaml`
      - …the other three `tests/data/*_example.yaml` copies.
      - (The two **existing** tutorials' known copies, e.g. `ddo-v001-prd-workflow/input_files/prd_example.yaml`
        → `tests/data/prd_example.yaml`, so the guard covers the whole tree.)
- [ ] **Walk** every `tutorials/*/input_files/` (directory walk — **no prose/regex, no
      name-pattern discovery**, three naming schemes coexist, RT-13). For each `*.yaml` found:
      - if it is in `EXPECTED_MIRRORS`: assert the mapped source **exists** and is **byte-identical**;
      - else: assert it is in an explicit `STANDALONE` allow-set (e.g. the adversarial-loop's
        `document_data.yaml`, which mirrors nothing) — an unmapped, unlisted `*.yaml` is a **hard
        failure**, so a new drift-prone copy cannot be added without a decision (RT-02/05).
- [ ] **Coverage assertions (kills the "green-checks-nothing" path, RT-01):**
      - `EXPECTED_MIRRORS` is **non-empty**;
      - it **includes** `tests/fixtures/ingest_output.yaml` as a source (Tutorial 1 anchor);
      - it **includes** all four new `tests/data/*_example.yaml`.
- [ ] **Referenced-path existence:** for each mapped/standalone entry, assert both endpoints
      exist on disk (renamed fixture → loud failure, US-006 AC1).
- [ ] Ensure the test runs in the **default** suite (`tests/unit/`, unmarked — US-006 AC3).

### B. `output_files/` determinism guard (RT-07/12)
- [ ] For each committed `tutorials/*/output_files/*.{html,md}` that has a known
      (input-YAML, template, format) via an explicit `OUTPUT_RENDERS` map (Tutorial 2's four
      shown types): render fresh with `build.py` and assert **byte-equality**.
- [ ] **Text only** — do **not** assert byte-equality on any `output_files/*.pdf` (illustrative-only,
      RT-12). Mark the full render-and-compare `@pytest.mark.slow` if it adds subprocesses beyond
      the fast budget (RT-11).

### C. `code_samples` lint constraint (RT-06)
- [ ] Confirm all `tutorials/*/code_samples/*.py` pass `uv run ruff check .` /
      `format --check .`. (No config change; `.md`/`.sh` are not linted by ruff.) Do **not** add
      `tutorials/` to `pyproject.toml` `exclude`.

### D. Hypergraph registration (RT-05 blast-radius note, §5.4)
- [ ] Add node `tutorials` — `Module`, `associated_file: tutorials/`, `implements: [ddo_system]`,
      description = meta-documentation demonstrating the pipeline (registers 2 shipped + 3 new).
- [ ] Add node `test_tutorial_refs_unit` — `Atomic`,
      `associated_file: tests/unit/test_tutorial_refs.py`, `implements: [tests_unit]`,
      `depends_on: [tutorials]`.
- [ ] Update descriptions of `ddo_schemas` / `ddo_templates` to drop the stale
      `prd/scientific_report`-only enumerations; verify `ddo_core` prose does **not** enumerate
      the two old types (mark `needs_review` if it does, RT-5 gap).
- [ ] Run `python .agents/scripts/hypergraph_updater.py spec/compiled/architecture.yml tutorials
      test_tutorial_refs_unit` (plus the `needs_review` nodes from SuperPRD §5.4).

## 4. The Negative Space (Constraints)
- **DO NOT** discover references by parsing `tutorial.md` prose or by name pattern — walk
  `input_files/` + explicit `EXPECTED_MIRRORS` (RT-02/13).
- **DO NOT** let the guard pass with an empty/partial map — assert non-empty + `ingest_output.yaml`
  + all four new examples (RT-01).
- **DO NOT** allow an unmapped, non-standalone `input_files/*.yaml` — hard-fail (RT-02/05).
- **DO NOT** byte-compare PDF `output_files/` — text formats only (RT-12).
- **DO NOT** exclude `tutorials/` from ruff (RT-06).
- **DO NOT** author `tests/fixtures/*` — the guard references the promoted fixtures only (RT-05).
- **DO NOT** edit `architecture.yml` by hand — use `hypergraph_updater.py`.

## 5. Integration Tests & Verification
- **Test 1 (Deterministic):** `test_tutorial_refs.py` green on the real tree; a scratch drift
  (edit one `input_files/` copy) turns it **red** (RT-01/02 proof it bites).
- **Test 2 (Deterministic):** removing `EXPECTED_MIRRORS`' `ingest_output.yaml` entry turns the
  coverage assertion **red** (RT-01 — guard can't be gutted silently).
- **Test 3 (Deterministic):** the `output_files/` guard renders each Tutorial-2 type fresh and
  asserts `.html`/`.md` byte-equality (RT-07); a stale committed render turns it red.
- **Test 4 (Deterministic):** `hypergraph_updater.py` run leaves `tutorials` +
  `test_tutorial_refs_unit` registered; `/hyper-audit` reconciles all affected nodes to `clean`.
