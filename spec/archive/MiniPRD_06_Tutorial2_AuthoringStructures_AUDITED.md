# MiniPRD: Tutorial2_AuthoringStructures — the four new types; `blog_post` from scratch (renders)

**Hypergraph Node ID:** `tutorials` *(content for the NEW node registered in MP-8)*
**Parent Node:** `ddo_system`
**DAG:** Blocked-by MP-1..MP-4 (needs the four types, their example YAMLs, and their narrative
source docs to exist). **This is the tutorial that renders (RT-15).**

## 1. The Confidence Mandate
- **Confidence Score:** 10/10. Hand-authored tutorial over already-built, already-tested types.
  Renders use the deterministic `build.py` commands already CI-covered via `EXAMPLES`.
- **Clarifying Questions:** None.

## 2. Atomic User Stories
- **US-002:** As a user, I want to author a new document type by example so I can model my own structures.

## 3. Implementation Plan (Task List)
- [ ] Create `tutorials/ddo-v006-authoring-custom-structures/` with the full convention.
      *(The four `input_files/<type>_source.md` narrative docs were authored in MP-1..MP-4; this
      MiniPRD adds `tutorial.md`, the `input_files/*.yaml` copies, `output_files/`,
      `code_samples/`, `screenshots/`.)*
- [ ] `input_files/<type>_example.yaml` = **byte-identical copies** of each
      `tests/data/<type>_example.yaml` (all four). Registered in `EXPECTED_MIRRORS` (MP-8),
      mapping to their `tests/data/` sources (RT-01/02).
- [ ] `tutorial.md`: walk **`blog_post` from scratch** (schema → persona/style choice → sections
      → evidence sourced from `blog_post_source.md`, RT-04). Present the other three
      (`meeting_notes`, `meeting_agenda`, `project_report`) as **worked examples**.
- [ ] **Render step (US-002 AC4 / RT-15):** include a `code_samples/render_commands.sh` (or
      `.py`) block that runs `uv run ddo/build.py --data input_files/blog_post_example.yaml
      --template blog_post --format html --output output_files/blog_post.html` (and `.md`), exit 0.
- [ ] **Author `output_files/` renders for the shown types** (`.html` + `.md`) by running
      `build.py` — these are byte-equality-guarded in MP-8 (RT-07). PDF snapshots, if included,
      are illustrative-only and **not** guarded (RT-07/12).
- [ ] `code_samples/*.py|*.sh` are ruff-clean/runnable (RT-06); no directory-level ruff exclusion.
- [ ] Cross-link: point to Tutorial 3 for persona authoring and to `ddo-create-style` for styles.

## 4. The Negative Space (Constraints)
- **DO NOT** let any `input_files/*.yaml` drift from its `tests/data/` source — byte-identical, guarded (RT-01/02).
- **DO NOT** commit an `output_files/` `.html`/`.md` that isn't a fresh `build.py` render — it is guarded (RT-07).
- **DO NOT** assert/claim PDF `output_files/` byte-equality — illustrative-only (RT-07/12).
- **DO NOT** exclude `tutorials/` from ruff to accommodate a sample — keep samples ruff-clean (RT-06).
- **DO NOT** invent a new tutorial layout.

## 5. Integration Tests & Verification
- **Test 1 (Deterministic):** MP-8's `test_tutorial_refs.py` byte-compares all four
  `input_files/*.yaml` copies to their `tests/data/` sources (RT-01/02).
- **Test 2 (Deterministic):** MP-8's `output_files/` guard renders each shown type fresh and
  asserts `.html`/`.md` byte-equality with the committed snapshot (RT-07).
- **Test 3 (Novel):** `tutorial.md` prose + the from-scratch `blog_post` walkthrough are
  Candidate Artifacts → HITL sign-off; a newcomer following the render step produces an
  evidence-linked document with exit 0 (US-002 AC4 / success metric, RT-15).
