# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.5] - 2026-06-30

### Added
- **`ddo/styles/` module**: New directory mirroring `ddo/personas/` — three built-in profiles: `formal_professional.md`, `conversational.md`, `technical_precise.md`. Each follows a 5-section free-prose contract (`Register & Audience`, `Voice & Person`, `Sentence & Structure`, `Diction`, `Avoid`); phrasing-only invariant enforced — zero content-bearing, quantitative, or instruction-channel imperatives (RT-1/RT-2).
- **`ddo/skills/ddo-create-style.md`**: New skill for interactive style-profile authoring — paced Q&A loop (≤2 questions/turn) mirroring `ddo-create-persona.md`; slug validated against `^[a-z][a-z0-9_]*$` before any path use; ships a 3–5 example phrasing/content/ambiguous-framing rejection rubric; cognitive overwrite guard with literal-filename re-confirmation; `[WAITING FOR USER REVIEW]` gate before write. No `ddo_core` dependency.
- **`tests/unit/test_styles.py`**: New glob-based structural validator for `ddo/styles/*.md`, mirroring `test_personas.py`. `test_style_dir_has_files` dir-guard prevents a vacuous pass on an empty directory (RT-9); parametrized assertions (title heading, five required `##` sections, non-empty bodies, sentinel-absence) over every discovered profile; negative-case parity (missing heading, empty body, sentinel present). 16 new tests; stdlib `re` only, no prose-content assertions.
- **`meta.style_profile`** (optional): Added to `ddo/schemas/prd.yaml` (default `formal_professional`) and `ddo/schemas/scientific_report.yaml` (default `technical_precise`), placed immediately after `persona`. Render-invisible — ignored as an unknown key by `validation.py`; no Python change.

### Changed
- **`ddo/skills/ddo-ingest.md`** / **`ddo/skills/ddo-interview.md`**: Added an identical style-injection block. Resolves `style_profile` → stem-validates (`^[a-z][a-z0-9_]*$`, re-validated on every read regardless of provenance — a stored value is never trusted, RT-4) → reads the profile once up front as untrusted phrasing-only guidance (RT-2) → scopes it to `content.sections[*].body` only, never `evidence_bank[*]` or `meta.*` (RT-5) → routes any would-be fabrication to `[[DDO::REQUIRES_INPUT: ...]]` instead of inventing it (RT-1) → echoes the resolved profile path at the HITL gate (RT-7). A present-but-invalid value (`""`, `null`/`~`, whitespace) hard-fails identically to a missing file, never a silent no-op (RT-8); a truly absent field remains a clean no-op.
- **`ddo/skills/ddo-red-team.md`**: RT-3 adds a `# Active Style: <stem>` (or `(none)`) header line alongside the persona AV-table echo, plus a documentary aligned-pairing note (e.g. `formal_professional` + `product_critic`) warning that a mismatched pair can oscillate the loop — no schema coupling. RT-10 closes the previously deferred `meta.persona` traversal gap: validates the persona stem against `^[a-z][a-z0-9_]*$` before any Read and hard-fails on a referenced-but-missing persona, identical to the `style_profile` gate — supersedes the prior "A6" deferral.
- **`spec/compiled/architecture.yml`**: 3 new nodes (`ddo_styles`, `skill_create_style`, `test_styles_unit`); 4 directly modified nodes (`ddo_schemas`, `ddo_skills`, `skill_interview`, `skill_red_team`) plus legitimate transitive blast radius (`ddo_system`, `ddo_core`, `tests_unit`, `tests_integration`, `documents_output`) reconciled from `needs_review` to `clean`, with `inputs`/`outputs`/`description` rewritten to match the actual implementation. 35 total nodes, all `clean`.
- **Test suite**: 199 unit tests passing (was 183 in v0.0.4).

## [0.0.4] - 2026-06-30

### Added
- **`ddo/skills/ddo-create-persona.md`**: New `ddo-create-persona` skill — paced Q&A loop (≤2 questions/turn) guiding persona authors through all six sections: Domain, Reviewing Mission, Attack Vectors (as AV-NN table), Severity Taxonomy, Domain-Specific Format Rules, Interview Question Templates. Cognitive overwrite guard with literal-filename re-confirm; `[WAITING FOR USER REVIEW]` gate before write; sentinel resolution required before commit. No `ddo_core` dependency (RT-03/RT-12).
- **AV-NN Attack Vector tables** in `ddo/personas/product_critic.md` and `ddo/personas/scientific_reviewer.md`: `## Attack Vectors` restructured from prose to a 3-column Markdown table `| ID | Name | When to apply |`. `product_critic` rows AV-01–AV-06: `missing_acceptance_criteria`, `unsupported_value_claims`, `scope_creep`, `unmeasurable_success`, `hedging_language`, `contradictory_logic`. `scientific_reviewer` rows AV-01–AV-06: `methodological_vagueness`, `unsupported_assertions`, `statistical_ambiguity`, `overreaching_conclusions`, `missing_limitations`, `result_discussion_bleed`. Names use raw underscores (never `\_`); no literal `|` in cells.

### Changed
- **`ddo/skills/ddo-red-team.md`**: After resolving the persona, echoes the full `## Attack Vectors` table into report context; binds each finding's `category` to the persona's exact `AV-NN: <name>` string (cognitively enforced; free-text in schema, no enum in code). Added hard-fail clause (RT-05): if the resolved persona has no `## Attack Vectors` table, halts and names the persona — no free-text category fallback.
- **`tests/unit/test_personas.py`**: Rewritten from hardcoded name list to glob-based AV-table validator parametrized over `ddo/personas/*.md`. Asserts per-persona: table existence and `| ID | Name | When to apply |` header; sequential AV-NN IDs from AV-01, unique; names match `^[a-z][a-z0-9_]*$`, unique, no escaped `\_`; no literal `|` in cells; all columns non-empty; no sentinel tokens. stdlib `re` only — no Markdown parser dependency.
- **`tests/unit/test_refine.py`**: Flipped 4 legacy-op tests from success-path to rejection — `test_apply_patches_append_evidence`, `test_apply_patches_append_review_log_creates_list`, `test_apply_patches_append_review_log_extends_existing`, `test_apply_patches_append_evidence_non_dict_raises` — all now assert `ValueError(match="unknown op")`.
- **`tests/unit/test_review.py`**: Added 2 rejection tests asserting `validate_interview_log` raises `ReportValidationError` for `op: append_evidence` and `op: append_review_log` (independent surface from `apply_patches`, RT-15).
- **`ddo/skills/ddo-interview.md`**: `op:` line updated to `set | append | delete | insert`; "Legacy Op Deprecation (v0.0.3)" section removed.
- **Test suite**: 183 tests passing.

### Removed
- **`append_evidence` and `append_review_log` ops** removed from `apply_patches` (`ddo/refine.py`) and `OP_ENUM` (`ddo/review.py`). Both were deprecated in v0.0.3.
  - Migrate `append_evidence` → `{op: append, target: "evidence_bank", value: {...}}`
  - Migrate `append_review_log` → `{op: append, target: "meta.review_log", value: {...}}`

### Documentation
- **`tutorials/ddo-adversarial-loop-v0.0.2/code_samples/interview_call.py`**: Migrated `append_evidence` comment and op to `{op: append, target: "evidence_bank", value: {...}}`.
- **`tutorials/ddo-adversarial-loop-v0.0.2/tutorial.md`**: Deprecated-ops rows reworded to past tense ("removed in v0.0.4 — migrate: ..."); rows retained as migration reference.

## [0.0.3] - 2026-06-30

### Added
- **`DanglingRefError(Exception)`** in `ddo/refine.py`: Carries a `paths: list[str]` attribute — the authoritative structured output for `ddo-refine` to surface when a `delete` op targeting `evidence_bank` would leave references dangling in `content.sections[*].evidence[]`.
- **`_dangling_ref_check(doc, index)`** in `ddo/refine.py`: Called before every `delete` on `evidence_bank[N]`; scans `content.sections[*].evidence[]` for the entry's `id`; raises `DanglingRefError` if found. Uses `dict.get()` throughout — never raises `KeyError` on malformed input.
- **`append` op** in `apply_patches` (`ddo/refine.py`): Appends a value to a list target. Rejects `[N]`-terminated paths and non-list targets; never auto-vivifies a missing list.
- **`delete` op** in `apply_patches` (`ddo/refine.py`): Removes `list[index]`. Calls `_dangling_ref_check` when targeting `evidence_bank`; rejects a `value` field on the patch dict; operation is blocked if `DanglingRefError` raises.
- **`insert` op** in `apply_patches` (`ddo/refine.py`): Inserts a value into a list at position `at`. Validates `isinstance(at, int) and not isinstance(at, bool) and at >= 0`; rejects `at > len(list)`; rejects `at: True`, `at: -1`, and `at: 2.0`.
- **NC-13 path whitelist** in `parse_path` (`ddo/refine.py`): Key segments must match `[a-zA-Z_][a-zA-Z0-9_]*`; index brackets must match `\d+` only — `[-1]`, `[*]`, `[0x1f]` all raise `ValueError`.
- **Structural patch syntax** in `ddo/skills/ddo-interview.md`: Full `append`/`delete`/`insert` YAML examples with `target:` field name (not `path:`); sequential-index warning; dangling-ref advisory before the `delete` example; deprecation notice for `append_evidence` and `append_review_log` (deprecated; removed in v0.0.4).
- **`DanglingRefError` handling** in `ddo/skills/ddo-refine.md`: Displays `.paths` list with format `"Refused: evidence_bank[N] is still referenced at: [...]"`; instructs interview agent to issue `set` patches first; multi-line diff note for structural ops; human authorization gate framing (interview prompt = proposal; Before/After diff = human approval).
- **17 new unit tests** in `tests/unit/test_refine.py`: Cover all three new ops (append/delete/insert), atomicity on mid-batch exception, sequential-index shift documentation, and `_dangling_ref_check` edge cases (set-before-delete, malformed doc).
- **11 new unit tests** in `tests/unit/test_review.py`: Cover new `OP_ENUM` acceptance cases and all six invalid per-op field combinations (insert without `at`, delete with `value`, set/append/delete with `at`, insert with negative or bool `at`, unknown op).
- **`tests/fixtures/loop/interview_log_v1_structural.yaml`**: Human-approved structural fixture — exercises `append` (evidence_bank), `delete` (unreferenced evidence entry at `evidence_bank[2]`), and `insert` (content.sections at: 0) through the full refine pipeline.

### Changed
- **`validate_interview_log`** (`ddo/review.py`): Added `OP_ENUM: frozenset[str]` constant with all six valid op strings (`set`, `append`, `delete`, `insert`, `append_evidence`, `append_review_log`). Enforces per-op field rules: `insert` requires `at`; `delete` forbids `value`; `set`/`append`/`delete`/`insert` require `target`; `at` type validated as `isinstance(at, int) and not isinstance(at, bool) and at >= 0`. Unknown ops raise `ReportValidationError`.
- **`test_loop_pass`** (`tests/integration/test_loop.py`): Refactored from two separate test functions into a single `@pytest.mark.parametrize` test with `id="set-based"` and `id="structural"` cases; both cases use `shutil.copy` for per-case fixture isolation.
- **`test_apply_patches_unknown_op_raises`** (`tests/unit/test_refine.py`): Op string changed from `"delete"` to `"replace"` — `"delete"` is now a valid op.
- **`pyproject.toml`**: Version bumped `0.0.2` → `0.0.3`.
- **Test suite**: Expanded from 159 to 188 tests.

### Documentation
- **`tutorials/ddo-v001-prd-workflow/tutorial.md`**: Updated stale test count (`78` → `188`); rewrote the "Related" section entry for the adversarial loop — replaced "v0.0.2 roadmap" future-tense language with present-tense shipped phrasing and a direct link to `tutorials/ddo-adversarial-loop-v0.0.2/tutorial.md`.
- **`tutorials/ddo-adversarial-loop-v0.0.2/tutorial.md`**: Comprehensive v0.0.3 accuracy update — rewrote Phase 2 decision table to mark `append_evidence` and `append_review_log` as deprecated with migration forms; added full `append`/`delete`/`insert` op table with required/forbidden fields; added `validate_interview_log()` pre-validation note; added `DanglingRefError` documentation with resolution pattern and `.paths` format; added sequential-index shift warning in Phase 3; added NC-13 path-whitelist constraint to `parse_path` prose; fixed stale "deferred to v0.0.3" troubleshooting row; added four new troubleshooting rows for `DanglingRefError`, `ValueError` (NC-13), and `ReportValidationError` cases.
- **`tutorials/ddo-adversarial-loop-v0.0.2/output_files/interview_log_v1.yaml`**: Updated F-004 patch block from deprecated `op: append_evidence` to `{op: append, target: "evidence_bank", value: {...}}`.
- **Tutorial audit files** (`tutorials/*/audit_2026-06-30.md`): Structured fix prompts generated via `/hyper-tutorial-audit` documenting staleness findings and fix instructions for each tutorial.
- **`spec/process/process_20260630_152059_session.md`**: Retrospective process document for the tutorial audit session.

## [0.0.2] - 2026-06-29

### Added
- **`ddo/review.py`**: Critique/interview data layer for the adversarial loop. Owns structural contracts (`validate_report`, `validate_interview_log`), `_vN` derivation (`report_version` = max(N)+1, `current_version` = max(N)), torn-pass detection (`detect_incomplete_pass`), atomic contained writes (`write_report`, `write_interview_log`, `mark_findings`, `append_history`), and deterministic view generation (`render_report_view`, `render_history_view`) — no wall-clock at view-gen time; all timestamps come from stored report/log dicts.
- **`ddo/refine.py`**: Mutation layer for the adversarial loop — the only permitted writer of `document_data.yaml` during the refine phase. Hand-rolled path DSL parser (`parse_path`, never `eval`); pure in-memory `apply_patches` (constrained `set`: leaf-scalar only, no auto-vivify, no type change; `append_evidence`; `append_review_log`); `refine_structural_check` (refine-only, distinct from `validation_gate`); `snapshot_source` (`force=False` — byte-for-byte pre-mutation copy, double-snapshot fails closed); `commit_refine` (double-checks + `safe_dump(sort_keys=False, allow_unicode=True)` + `atomic_write`).
- **`ddo/skills/ddo-red-team.md`**: Cognitive node for the Red Team phase. Enforces a fresh-context firewall (prior-phase rationale must not be inherited); runs torn-pass check; resolves persona with hard error on missing file; delegates all mechanics to `ddo.review`; emits `red_team_report_vN.yaml` + `red_team_view_vN.md`; halts at `[WAITING FOR USER REVIEW]`.
- **`ddo/skills/ddo-interview.md`**: Cognitive node for the Interview phase. Loads the machine-readable report (never the `.md` view); filters `applied:false` findings; sorts Critical→Major→Minor; presents `batch_size=2` per turn; writes `interview_log_vN.yaml` via `ddo.review`; marks only `decision_recorded` flag (never `applied` — that is `ddo-refine`'s job).
- **`ddo/skills/ddo-refine.md`**: Cognitive node for the Refine phase. Torn-pass check → `snapshot_source` → `apply_patches` → `refine_structural_check` + `validate` in-memory → unified diff HITL gate → `commit_refine` → `ddo-render` skill. Marks `applied` and appends `history.yaml` only after render succeeds.
- **`tests/unit/test_review.py`** and **`tests/unit/test_refine.py`**: 81 new unit tests covering version derivation, torn-pass detection, structural validation, pure patch application, path DSL parsing, snapshot/commit flow, view rendering, and history management.
- **`tests/integration/test_loop.py`**: End-to-end adversarial loop integration test (gap-closing pass: red-team report → interview log → refine commit → history append).
- **`spec/compiled/SuperPRD_v0.0.2_AdversarialLoop.md`**: Complete adversarial loop specification — 6 user stories, 13 Red Team resolutions (RT1–RT13), data contracts for `red_team_report_vN.yaml` / `interview_log_vN.yaml` / `history.yaml`, full module API, success metrics M1–M9, and negative constraints.
- **`spec/compiled/architecture.yml`**: Updated hypergraph with new nodes for `ddo.review`, `ddo.refine`, `ddo-red-team`, `ddo-interview`, and `ddo-refine`.
- **`tutorials/ddo-adversarial-loop-v0.0.2/tutorial.md`**: 6-section tutorial for the v0.0.2 adversarial loop using the Biodegradable Polyester Optimization Report as a worked example (including a real Critical finding: the paper's own Z-score formula ranks the recommended candidate third).
- **`tutorials/ddo-adversarial-loop-v0.0.2/input_files/`**: `validate()`-clean `document_data.yaml` with intentional flaws intact + representative rendered Markdown.
- **`tutorials/ddo-adversarial-loop-v0.0.2/output_files/`**: Byte-verified `red_team_report_v1.yaml`, `red_team_view_v1.md`, `interview_log_v1.yaml`, `history.yaml`, and `history.md` — all confirmed against the real `ddo.review` / `ddo.refine` / `ddo.validation` modules via an automated verification script.
- **`tutorials/ddo-adversarial-loop-v0.0.2/code_samples/`**: Skill→module delegation reference for all three adversarial-loop phases (`red_team_call.py`, `interview_call.py`, `refine_call.py`).
- **`tutorials/ddo-adversarial-loop-v0.0.2/architecture_evolution/pipeline_v0.0.1_to_v0.0.2.md`**: ASCII before/after pipeline diagrams, what-is-new comparison table, carried-forward invariants, and the fresh-context firewall rationale.

### Changed
- **`pyproject.toml`**: Version bumped `0.0.1` → `0.0.2`.
- **Test suite**: Expanded from 78 to 159 passing tests.

## [0.0.1] - 2026-06-29

### Added
- **`ddo/build.py`**: PEP 723 hermetic build orchestrator. Loads YAML, delegates to `validate()`, resolves templates strictly from `--template`/`--format` CLI flags, renders PDF (in-process Typst, bundled fonts) or HTML/MD (Jinja2, autoescape on for HTML), enforces a 30 s wall-clock timeout and 64 MiB output-size cap via a daemon-thread guard, normalises output to LF + stripped trailing whitespace.
- **`ddo/validation.py`**: Importable validation gate (`validate(data) -> None`). Three ordered checks: (1) structural meta/evidence_bank contract; (2) evidence uniqueness and reference integrity; (3) recursive sentinel scan for `[[DDO::REQUIRES_INPUT:`. Raises `ValidationError` on first failure.
- **`ddo/paths.py`**: Pure path helpers — `sanitize_slug` collapses to `[a-z0-9-]` (structurally forbids `..` and path separators); `document_dir` computes `Documents/<date>_<doc_type>_<slug>/`; `assert_within_documents` raises `PathContainmentError` on traversal.
- **`ddo/ingest.py`**: Atomic write (`tempfile.mkstemp` → `fsync` → `os.replace`), overwrite guard (`OverwriteError` on existing target without `--force`), and advisory `fabrication_tripwire` that surfaces date/number/proper-noun tokens absent from source materials.
- **`ddo/skills/ddo-ingest.md`** and **`ddo/skills/ddo-render.md`**: Cognitive node skill definitions directing the Ingest and Render pipeline phases.
- **`ddo/schemas/prd.yaml`** and **`ddo/schemas/scientific_report.yaml`**: Canonical YAML schema contracts (meta block + evidence_bank required).
- **`ddo/templates/`**: Typst templates (`prd.typst`, `scientific_report.typst`) and Jinja2 templates (`prd.html.jinja2`, `prd.md.jinja2`, `scientific_report.html.jinja2`, `scientific_report.md.jinja2`).
- **`ddo/fonts/`**: Bundled DejaVu font family — hermetic Typst PDF rendering with no system font dependency.
- **`ddo/personas/`**: `product_critic.md` and `scientific_reviewer.md` adversarial review lens definitions.
- **`scripts/fixture_signoff_guard.py`**: Pre-commit/CI guard (SuperPRD RT#13) — rejects staged changes to `tests/fixtures/` unless `DDO_FIXTURE_SIGNOFF=1` is set.
- **`tests/unit/`**: 25 validation-gate tests, slug/containment tests, ingest-helper tests, persona-structure tests, fixture-guard tests.
- **`tests/integration/`**: M1–M4 render-determinism tests (both examples × all formats, byte-identical HTML/MD, text-identical PDF, pinned-timestamp byte-identical PDF, HTML autoescape XSS guard) and M5 ingest-contract test.
- **`tests/fixtures/`**: Promoted golden regression baselines (`prd_example.html`, `prd_example.md`, `prd_example.pdf.txt`, `scientific_report_example.html`, `scientific_report_example.md`, `scientific_report_example.pdf.txt`, `ingest_output.yaml`).
- **`tests/data/`**: `prd_example.yaml` and `scientific_report_example.yaml` test input documents.
- **`spec/compiled/architecture.yml`**: 24-node hypergraph (1 System, 8 Module, 15 Atomic); all nodes `status: clean`.
- **`ddo/build.py.lock`**: PEP 723 script-adjacent lockfile (enforced by `uv run --locked`).
- **`tutorials/ddo-v001-prd-workflow/tutorial.md`**: 9-section hands-on tutorial walking through the full PRD YAML workflow — schema authoring, validation gate, rendering to PDF/HTML/MD, troubleshooting table, and related skills.
- **`tutorials/ddo-v001-prd-workflow/input_files/prd_example.yaml`**: Gate-passing 6-section PRD YAML used as the tutorial starting point.
- **`tutorials/ddo-v001-prd-workflow/output_files/`**: Pre-rendered `prd_example.html` and `prd_example.md` for reference.
- **`tutorials/ddo-v001-prd-workflow/code_samples/render_commands.sh`**: Ready-to-adapt shell script for all three output formats plus the `--timestamp` byte-identical PDF variant.
- **`spec/process/process_20260629_101449_session.md`**: Retrospective process document for the v0.0.1 implementation session — 15 implementation steps, key decisions, artifacts table, and patterns/lessons.

### Fixed
- **HTML autoescape silent failure**: `select_autoescape(enabled_extensions=("html",))` matched on template *filename extension*, so `.jinja2` templates were never matched and autoescape was silently disabled. Fixed by replacing with `autoescape=(fmt == "html")`, which correctly enables escaping for all HTML renders regardless of template filename. Raw `<script>` injection was possible before this fix.

### Changed
- **`.gitignore`**: Surgical matrix — `spec/` and `tests/` unblocked for committed content; `tests/candidate_outputs/` and `spec/archive/` remain gitignored; `Documents/` remains gitignored.
- **`pyproject.toml`**: Version bumped `0.0.0` → `0.0.1`.
- **Typst templates**: Font paths updated to reference bundled `ddo/fonts/` DejaVu family (hermetic, no system Typst install required).

## [0.0.0] - 2026-06-26

### Added
- **Project scaffolding**: Initialized `pyproject.toml` with `uv`, `ruff` (Google docstring convention, 88-char line length), and `pytest` dev dependencies.
- **`CLAUDE.md`**: Project-level Claude Code instructions with DDO pipeline overview, 5 design invariants, directory structure, build commands, and schema contract.
- **`PRDs/`**: Initial domain documents — `DDO_PRD.md`, `DETERMINISTIC_DOC_ORCHESTRATOR.md`, skill definitions (`Ingest_Skill.md`, `Render_Skill.md`, `Red_Team_Skill.md`, `Interview_Skill.md`, `Refine_Skill.md`, `Run_Skill_Composite.md`), personas (`Product_Critic_Persona.md`, `Scientific_Reviewer_Persona.md`), YAML schemas (`product_requirements_document_schema.yaml`, `scientific_report_schema.yaml`), and Jinja2/Typst template stubs.
- **Pre-commit hook**: `ruff check` and `ruff format --check` run automatically before every commit.
- **`.gitignore`**: Excludes `hyper-*` HACF toolchain items, `Documents/` generated output, and `spec/`/`tests/` runtime content while preserving `.gitkeep` directory structure.
