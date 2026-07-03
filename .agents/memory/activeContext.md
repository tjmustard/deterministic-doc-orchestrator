
# Active Context
## Purpose
This file updates dynamically after *every task completion*. It captures the "Now" of the project: what was just done, what is currently being worked on, and any immediate blockers or open questions.

## Usage
- Agent writes here after completing a task.
- Agent reads this *first* to understand where to pick up.

## Current Sprint Goal
**DDO v0.0.6 — AUDITED, RECONCILED & RELEASED (2026-07-02)**

Expanded Ecosystem Tutorials implemented via 9 fanned-out MiniPRD builder passes
(harness prep + 4 document types + 3 tutorials + anti-rot guard), then audited via 9
parallel fan-out subagents (one per MiniPRD) — all 9 passed Phase 1/2 contract
verification with no punch lists. Hypergraph reconciled (`needs_review` → `clean`,
11 nodes) via a Haiku sub-agent; 11 directly-modified leaf nodes remain `dirty` by
design (Phase 3 only reconciles `needs_review`, per `hyper-audit`'s `SKILL.md`). All
9 MiniPRDs archived to `spec/archive/*_AUDITED.md`. `pyproject.toml` bumped to
`0.0.6`; `CHANGELOG.md` and `README.md` updated. 348 tests collected (324 passed + 4
skipped in the default fast subset, 20 more under `-m slow`), ruff clean.

## v0.0.6 Implementation Summary

### Execution Method
Fanned out one subagent per MiniPRD for the `/hyper-execute` build pass (DAG order
per SuperPRD §5.3: MP-0 harness prep → MP-1..MP-4 document types in parallel →
MP-5..MP-7 tutorials → MP-8 anti-rot guard + hypergraph, done last since it's the
only step registering new nodes). Audit (`/hyper-audit`) then fanned out 9 parallel
read-only subagents, one per MiniPRD, for Phase 1 (Contract Verification) + Phase 2
(Test Validation) — each independently read the MiniPRD, verified the actual files
on disk, ran targeted tests, and rendered examples via `build.py` where applicable.

### New Files
- **Four new document types**, each a complete self-contained worked example:
  `blog_post` (persona `content_editor`, style `blog_casual`), `meeting_notes`
  (persona `meeting_recorder`, style `notes_concise` — carries a deliberate
  non-ASCII attendee name, RT-12), `meeting_agenda` (persona `meeting_facilitator`,
  style `agenda_directive` — time-boxed entries are opaque string literals, no
  computed durations, RT-09), `project_report` (persona `project_stakeholder`,
  style `executive_formal`). Each ships schema + 3 templates (typst/html/md) +
  example YAML (`tests/data/`) + narrative source doc + `EXAMPLES` enrollment.
- `tutorials/ddo-v006-evidence-bank-workflow/` — citation-integrity lens over the
  human-promoted `tests/fixtures/ingest_output.yaml`; zero `ddo-refine`/
  `ddo-interview` invocations (RT-15).
- `tutorials/ddo-v006-authoring-custom-structures/` — walks `blog_post` from scratch
  through to a rendered document; the other three types as worked examples; the
  tutorial that actually renders (RT-15).
- `tutorials/ddo-v006-writing-structured-personas/` — walks the v0.0.4 AV-table
  format and drives `ddo-create-persona` end-to-end using the four new personas as
  specimens.
- `tests/unit/test_tutorial_refs.py` — anti-rot guard: `input_files/` walk +
  explicit `EXPECTED_MIRRORS` map (source in `tests/data/` or `tests/fixtures/`) +
  `STANDALONE` set; byte-identity assertion. `OUTPUT_RENDERS` (`@pytest.mark.slow`)
  re-renders `output_files/*.{html,md}` and byte-compares against committed copies;
  PDF excluded. 26 tests. Independently verified non-vacuous during audit (drift
  was injected in a scratch copy and confirmed to fail the guard).
- `tests/integration/test_schema_meta_refs.py` — asserts every schema's and every
  example's `meta.persona`/`meta.style_profile` resolves to a real file, plus soft
  schema-conformance (example section ids ⊆ schema sections).

### Changed
- `ddo/build.py` — `--template` CLI `choices` extended with the four new types (no
  render/validate logic changed; this diff is a shared mechanical touchpoint across
  all four per-type MiniPRDs, since CLI dispatch requires each new template name to
  be a legal `--template` value).
- `tests/integration/conftest.py` — `EXAMPLES` extended to 6 entries; single source
  of truth (RT-03).
- `tests/integration/test_render_determinism.py` — duplicate local `EXAMPLES`
  literal removed in favor of `from .conftest import EXAMPLES`; `fmt` parametrization
  split into `slow`-marked (`pdf`, `html`) and default (`md`) cases.
- `pyproject.toml` — `markers = ["slow: ..."]` + `addopts = "-m 'not slow'"` (RT-11);
  version `0.0.5` → `0.0.6`.

### Hypergraph (spec/compiled/architecture.yml)
- **2 new nodes:** `tutorials` (Module, `implements: ddo_system`, framed as
  meta-documentation per CLAUDE.md's toolchain-framing discipline), `test_tutorial_refs_unit`
  (Atomic, `implements: tests_unit`, `depends_on: tutorials`).
- **7 nodes marked `dirty`** by direct modification: `ddo_schemas`, `ddo_templates`,
  `ddo_personas`, `ddo_styles`, `render_fixture`, `tests_integration`,
  `test_render_determinism`.
- **11 nodes reconciled `needs_review` → `clean`** via a Haiku sub-agent (blast-radius
  propagation): `ddo_system`, `ddo_core`, `ddo_skills`, `documents_output`,
  `test_ingest_contract`, `skill_red_team`, `test_personas_unit`,
  `test_loop_integration`, `skill_create_persona`, `skill_create_style`,
  `test_styles_unit` — `inputs`/`outputs`/`description` rewritten to match actual
  implementation.
- **Note:** `dirty` leaf nodes are left `dirty` by design — `hyper-audit`'s
  `SKILL.md` Phase 3 only reconciles `needs_review` nodes; `hypergraph_updater.py`'s
  `propagate_blast_radius` never returns a directly-dirtied node to `clean` itself.
- 37 total nodes: 26 `clean`, 11 `dirty`, 0 `needs_review`.

### Verification
- All 9 MiniPRDs (`00_HarnessPrep` through `08_AntiRotGuard_Hypergraph`) passed
  audit with no punch lists.
- `uv run pytest` — 324 passed, 4 skipped (human-gated fixtures, expected), 20
  deselected (slow); `uv run pytest -m slow` — 20 passed. `uv run ruff check .` /
  `ruff format --check .` — both clean.
- No `ddo/*.py` module logic changed (only the `build.py` CLI `choices` tuple) —
  v0.0.6 is domain files + tests + docs only, per SuperPRD negative constraints.

### Audit (2026-07-02)
- Fanned out 9 parallel subagents, one per MiniPRD, for Phase 1 (Contract
  Verification) + Phase 2 (Test Validation). All 9 returned `PASS` — no punch
  lists, no scope violations. `MiniPRD_08`'s auditor independently proved the
  anti-rot guard is not vacuous by simulating a drifted mirror and confirming the
  guard goes red.
- Phase 3 reconciliation delegated to a Haiku sub-agent per `hyper-audit`'s
  `SKILL.md`: rewrote `inputs`/`outputs`/`description` for all 11 `needs_review`
  nodes and flipped each to `clean`.
- Phase 4: all 9 MiniPRDs moved to `spec/archive/` with `_AUDITED` suffix.

### Documentation Updated (v0.0.6)
- `pyproject.toml` — version `0.0.5` → `0.0.6`.
- `CHANGELOG.md` — `## [0.0.6] - 2026-07-02` block added (Added/Changed sections).
- `README.md` — badge v0.0.5 → v0.0.6; Directory Structure adds the 4 new schemas/
  personas/styles and 3 new tutorial dirs; Schema Contract gains a doc-type/
  persona/style table; roadmap gains a v0.0.6 section; test count 216 → 348;
  `Running the Build` documents the `slow` marker split.
- `.agents/memory/activeContext.md` — this file.

### Next Steps
- Scientific report workflow tutorial (`tutorials/ddo-v001-scientific-report-workflow/`)
  remains the only open roadmap item.

## v0.0.5 Summary (superseded by v0.0.6 above as "Current Sprint")

Style & Tone Configuration fully implemented, audited, and released. 216 tests
passing (199 unit + integration, 2 skipped pending human sign-off).

## v0.0.5 Implementation Summary

### Execution Method
Fanned out one subagent per MiniPRD, in 3 DAG-ordered waves (SuperPRD §5.3):
- **Wave 1 (parallel, no blockers):** MP-1 Styles, MP-4 SkillCreateStyle, MP-6 RedTeamStyleAware
- **Wave 2 (parallel, blocked-by MP-1):** MP-2 SchemaStyleField, MP-3 StyleInjection, MP-5 TestStyles
- **Wave 3 (solo, blocked-by all):** MP-7 Hypergraph — done directly in the main thread (not
  delegated) since it's the only step allowed to touch `architecture.yml`, avoiding concurrent-write
  races across the fanned-out agents.

### New Files
- `ddo/styles/formal_professional.md`, `ddo/styles/conversational.md`,
  `ddo/styles/technical_precise.md` — 5-section style profile contract (`Register & Audience`,
  `Voice & Person`, `Sentence & Structure`, `Diction`, `Avoid`); zero content-bearing/quantitative
  imperatives (RT-1/RT-2).
- `ddo/skills/ddo-create-style.md` — interactive paced Q&A skill mirroring
  `ddo-create-persona.md`; ships a phrasing/content/framing rejection rubric; cognitive overwrite
  guard; no `ddo_core` dependency.
- `tests/unit/test_styles.py` — glob-based structural validator mirroring `test_personas.py`;
  `test_style_dir_has_files` dir-guard + negative-case parity (RT-9). 16 new tests.

### Changed
- `ddo/schemas/prd.yaml` / `ddo/schemas/scientific_report.yaml` — optional `meta.style_profile`
  added immediately after `persona`, live defaults `formal_professional` / `technical_precise`
  (landed atomically with the styles module per RT-6).
- `ddo/skills/ddo-ingest.md` / `ddo/skills/ddo-interview.md` — identical style-injection block:
  resolve → stem-validate (`^[a-z][a-z0-9_]*$`, re-validated on every read regardless of
  provenance, RT-4) → Read once up front as untrusted phrasing-only guidance (RT-2) → scope to
  `content.sections[*].body` only, never `evidence_bank[*]`/`meta.*` (RT-5) → sentinel-route
  would-be fabrications via `[[DDO::REQUIRES_INPUT: ...]]` (RT-1) → echo resolved path at the
  HITL gate (RT-7). Present-but-invalid (`""`/`null`/whitespace) hard-fails, never a no-op (RT-8).
- `ddo/skills/ddo-red-team.md` — RT-3: `# Active Style: <stem>` (or `(none)`) header line +
  aligned-pairing note, documentary only, no schema coupling. RT-10: closes the previously
  deferred `meta.persona` traversal gap with the identical stem gate before any Read (supersedes
  prior "A6" deferral).

### Hypergraph (spec/compiled/architecture.yml)
- **3 new nodes:** `ddo_styles` (Module), `skill_create_style` (Atomic, depends_on `ddo_styles`),
  `test_styles_unit` (Atomic, depends_on `ddo_styles`) — all `needs_review`.
- **4 modified nodes → `needs_review`:** `ddo_schemas`, `ddo_skills` (description now names the
  concrete `ddo-ingest.md` diff since it has no dedicated Atomic node), `skill_interview`,
  `skill_red_team`.
- **`hypergraph_updater.py` run** for all 7 touched nodes; natural blast-radius propagation also
  flagged `ddo_system`, `ddo_core`, `tests_unit`, `documents_output` as `needs_review` (legitimate
  transitive consumers) — left as-is for audit.
- **Reverted one propagation:** the script's BFS also flagged `test_render_determinism`
  (a render/determinism test node), which the SuperPRD's negative-space explicitly lists as
  "Explicitly NOT touched" — manually reverted back to `clean` after confirming MP-2/MP-3 are
  fully render-invisible (full suite green, byte-identical).
- Explicitly-forbidden nodes confirmed still `clean`: `skill_refine`, `refine_engine`,
  `review_engine`, `validation_gate`, `build_orchestrator`, `ingest_helpers`, `path_deriver`,
  and all render/determinism test nodes.

### Verification
- `uv run ruff check .` / `ruff format --check .` — both clean.
- `uv run pytest` — 216 passed, 2 skipped (human-gated fixtures, expected), no regressions.
- No Python module was touched (`validation.py`, `build.py`, `review.py`, `refine.py`,
  `ingest.py`, `paths.py` all untouched) — v0.0.5 is cognitive-only per SuperPRD scope.

### Audit (2026-06-30)
- Fanned out 7 parallel subagents, one per MiniPRD (`Styles`, `SchemaStyleField`, `StyleInjection`,
  `SkillCreateStyle`, `TestStyles`, `RedTeamStyleAware`, `Hypergraph`) for Phase 1 (Contract
  Verification) + Phase 2 (Test Validation). All 7 returned `[VERIFICATION: PASSED]` — no punch
  lists, no scope violations.
- Phase 3 reconciliation delegated to a Haiku sub-agent per the `hyper-audit` skill: rewrote
  `inputs`/`outputs`/`description` for all 12 `needs_review` nodes to match actual implementation
  and flipped each to `clean`. `architecture.yml`: 35 nodes, 0 `needs_review`, no dupes, acyclic.
- Phase 4: all 7 MiniPRDs moved to `spec/archive/` with `_AUDITED` suffix. `MiniPRD_Hypergraph.md`
  renamed to `MiniPRD_Hypergraph_v005_AUDITED.md` to avoid colliding with an unrelated v0.0.2-era
  archive file of the same base name.

### Documentation Updated (v0.0.5)
- `pyproject.toml` — version `0.0.3` → `0.0.5` (note: the v0.0.4 release had skipped this bump;
  this pass also catches that up).
- `CHANGELOG.md` — `## [0.0.5] - 2026-06-30` block added (Added/Changed sections; no Python
  module touched, so no Fixed/Removed/Security entries).
- `README.md` — badge v0.0.4 → v0.0.5; Directory Structure adds `ddo/styles/` +
  `ddo-create-style.md`; Pipeline Workflow phases 1/3/4 note style resolution, register-aware
  critique, and the persona stem gate; Schema Contract documents optional `style_profile`; Roadmap
  gains a v0.0.5 section; test count 183 → 216 (199 unit + integration, 2 skipped).
- `.agents/memory/activeContext.md` — this file.

### Next Steps
- Scientific report workflow tutorial (`tutorials/ddo-v001-scientific-report-workflow/`) remains
  the only open roadmap item.

## v0.0.4 Summary (superseded by v0.0.5 above as "Current Sprint")

Structured Persona Nomenclature fully implemented, audited, and released. 183 tests passing.

## v0.0.4 Implementation Summary

### New Files
- `ddo/skills/ddo-create-persona.md` — interactive paced Q&A skill for authoring new personas (AV-NN table format, HITL gated, cognitive overwrite guard, no ddo_core dependency)
- `spec/compiled/SuperPRD_v0.0.4_StructuredPersonaNomenclature.md` — specification for this release

### Changed
- `ddo/personas/product_critic.md` — `## Attack Vectors` restructured to 3-column AV-NN table (AV-01..AV-06)
- `ddo/personas/scientific_reviewer.md` — same AV-NN table restructure (AV-01..AV-06)
- `ddo/skills/ddo-red-team.md` — echoes AV table into report context; binds category to `AV-NN: <name>`; hard-fails on missing table (RT-05)
- `ddo/skills/ddo-interview.md` — op list updated to `set | append | delete | insert`; legacy deprecation section removed
- `ddo/refine.py` — `append_evidence`/`append_review_log` branches removed; unknown-op error lists `set, append, delete, insert` only
- `ddo/review.py` — `OP_ENUM` reduced to `frozenset({"set","append","delete","insert"})`
- `tests/unit/test_personas.py` — rewritten as glob-based AV-table validator (stdlib re; parametrized over ddo/personas/*.md)
- `tests/unit/test_refine.py` — 4 legacy-op tests flipped to ValueError rejection
- `tests/unit/test_review.py` — 2 net-new ReportValidationError rejection tests for removed ops
- `tutorials/ddo-adversarial-loop-v0.0.2/code_samples/interview_call.py` — migrated to `op: append`
- `tutorials/ddo-adversarial-loop-v0.0.2/tutorial.md` — deprecated-ops rows reworded to past tense

### Hypergraph (spec/compiled/architecture.yml)
- `skill_create_persona` node added (Atomic, ddo_skills/ddo_personas deps, no ddo_core)
- All 26 nodes now `status: clean`

### Documentation Updated (v0.0.4)
- `CHANGELOG.md` — `## [0.0.4]` block completed with Added/Changed/Removed/Documentation sections
- `README.md` — badge v0.0.3 → v0.0.4; skills listing adds ddo-create-persona.md; Red Team phase updated; roadmap v0.0.4 section added; test count 188 → 183
- `.agents/memory/activeContext.md` — this file

## v0.0.3 Implementation Summary

### New in `ddo/refine.py`
- `DanglingRefError(Exception)` — carries `paths: list[str]`; raised by `_dangling_ref_check` before a `delete` on `evidence_bank` proceeds
- `_dangling_ref_check(doc, index)` — scans `content.sections[*].evidence[]` for the entry's `id`; uses `dict.get()` throughout (never raises `KeyError` on malformed input)
- `apply_patches` extended with `append`, `delete`, `insert` op branches; all operate on the deep copy; mid-batch exception leaves original dict unchanged (atomicity)
- `parse_path` NC-13 whitelist: key segments `[a-zA-Z_][a-zA-Z0-9_]*`; index brackets `\d+` only

### Changed in `ddo/review.py`
- `validate_interview_log`: `OP_ENUM` constant (frozenset of 6 valid ops); per-op field rules (`insert` requires `at`; `delete` forbids `value`; structural ops require `target`); `at` type validation

### Updated Skills
- `ddo/skills/ddo-interview.md`: structural patch YAML examples (`target:` field); sequential-index warning; dangling-ref advisory; `append_evidence`/`append_review_log` deprecated (removed in v0.0.4)
- `ddo/skills/ddo-refine.md`: `DanglingRefError` handling section; multi-line diff note; human authorization gate framing

### Tests & Spec
- `tests/unit/test_refine.py` — 17 new tests (total ~57): append/delete/insert ops, atomicity, sequential-index shift documentation, dangling ref edge cases
- `tests/unit/test_review.py` — 11 new tests (total ~51): OP_ENUM acceptance + 6 invalid per-op field combination rejections
- `tests/integration/test_loop.py` — refactored to `test_loop_pass[@parametrize]` with `id="set-based"` and `id="structural"` cases; both use `shutil.copy` for isolation
- `tests/fixtures/loop/interview_log_v1_structural.yaml` — human-approved structural fixture (append + delete + insert)
- `spec/compiled/architecture.yml` — 7 nodes reconciled `needs_review` → `clean` (ddo_system, ddo_core, ddo_skills, tests_unit, tests_integration, documents_output, skill_red_team)

### Documentation Updated (v0.0.3)
- `pyproject.toml` — version `0.0.2` → `0.0.3`
- `CHANGELOG.md` — `## [0.0.3] - 2026-06-30` block added
- `README.md` — badge v0.0.2 → v0.0.3; Phase 5 updated with new ops and DanglingRefError; roadmap v0.0.3 section added; test count 159 → 188
- `.agents/memory/activeContext.md` — this file
- `.agents/memory/systemPatterns.md` — v0.0.3 patterns added

## Key Design Decisions (v0.0.3)

| Decision | Rationale |
|---|---|
| `DanglingRefError` has structured `.paths` attribute | `ddo-refine` can display a precise list to the human without string-parsing the exception message |
| `_dangling_ref_check` uses `dict.get()` throughout | Malformed docs (missing `content`/`sections`) must not raise `KeyError` — they produce no dangling refs |
| `at > len(list)` raises in `apply_patches` but `at == len` is valid (append-equivalent) | Matches Python `list.insert` semantics; avoids a confusing special case |
| `isinstance(at, bool)` explicit rejection | `bool` is a subclass of `int` in Python; `True` (=1) and `False` (=0) would be silently accepted without this guard |
| Sequential-index shift documented, not fixed | A batch with `insert at: 0` then `delete [3]` shifts indices — this is intentional and documented via a test |
| `append_evidence`/`append_review_log` deprecated, not removed | Backwards compat for v0.0.3; hardcoded removal planned for v0.0.4 |

### Tutorial Audit & Fixes (2026-06-30)
- `/hyper-tutorial-audit` run on both tutorials; audit files saved to `tutorials/*/audit_2026-06-30.md`
- `tutorials/ddo-v001-prd-workflow/tutorial.md` — fixed stale test count (78→188); Related section updated from "v0.0.2 roadmap" to shipped link
- `tutorials/ddo-adversarial-loop-v0.0.2/tutorial.md` — comprehensive v0.0.3 update: new ops table, `DanglingRefError`, NC-13 whitelist, sequential-index warning, pre-validation note, 4 new troubleshooting rows, stale row fixed
- `tutorials/ddo-adversarial-loop-v0.0.2/output_files/interview_log_v1.yaml` — F-004 migrated from `append_evidence` to `{op: append, target: "evidence_bank"}`
- Both tutorials are now accurate against v0.0.3
