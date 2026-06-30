# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
