# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.0] - 2026-06-26

### Added
- **Project scaffolding**: Initialized `pyproject.toml` with `uv`, `ruff` (Google docstring convention, 88-char line length), and `pytest` dev dependencies.
- **`CLAUDE.md`**: Project-level Claude Code instructions with DDO pipeline overview, 5 design invariants, directory structure, build commands, and schema contract.
- **`PRDs/`**: Initial domain documents — `DDO_PRD.md`, `DETERMINISTIC_DOC_ORCHESTRATOR.md`, skill definitions (`Ingest_Skill.md`, `Render_Skill.md`, `Red_Team_Skill.md`, `Interview_Skill.md`, `Refine_Skill.md`, `Run_Skill_Composite.md`), personas (`Product_Critic_Persona.md`, `Scientific_Reviewer_Persona.md`), YAML schemas (`product_requirements_document_schema.yaml`, `scientific_report_schema.yaml`), and Jinja2/Typst template stubs.
- **Pre-commit hook**: `ruff check` and `ruff format --check` run automatically before every commit.
- **`.gitignore`**: Excludes `hyper-*` HACF toolchain items, `Documents/` generated output, and `spec/`/`tests/` runtime content while preserving `.gitkeep` directory structure.
