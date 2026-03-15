# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning: `0.0.x` = pre-SuperPRD implementation increments. `0.1.0` = first complete SuperPRD fulfilled.

---

## [Unreleased]

---

## [0.0.1] - 2026-03-15

### Added
- `state_graph_schema.py` — canonical state I/O module: `load_state()`, `save_state()` (atomic via `os.replace()`), `get_module()`, `set_module_status()`, `VALID_STATUSES`
- `archive_manager.py` — `archive_draft()` and `archive_compiled()` with microsecond-precision timestamps to prevent collision; CLI entrypoint
- `orchestrator.py` — YAML-driven state machine: lockfile, pre-flight validation (missing files, symlink scan, confidence score warning), persona snapshot, full module lifecycle loop, `--reset` mode
- `README.md` — full usage guide: installation, CLI reference, slash commands, workspace structure, uninstall instructions
- `CHANGELOG.md` — this file
