
# System Patterns
## Purpose
This file documents the "How" — architectural decisions, design patterns, tech stack choices, and project conventions for DDO v0.0.1+.

## Architecture

DDO is a 5-phase HITL pipeline: **Ingest → Render → Red Team → Interview → Refine**

```
YAML source (document_data.yaml)
    ↓ validate()
ddo/build.py  →  _render_typst (PDF)  →  Documents/<slug>/output/<slug>.pdf
              →  _render_jinja (HTML)  →  Documents/<slug>/output/<slug>.html
              →  _render_jinja (MD)    →  Documents/<slug>/output/<slug>.md
```

The hypergraph (`spec/compiled/architecture.yml`) has 24 nodes: 1 System, 8 Module, 15 Atomic. All `status: clean` post v0.0.1 audit.

## Tech Stack

- **Python 3.10+** via `uv` (package manager and script runner)
- **PEP 723 script** (`ddo/build.py`): self-contained with embedded dependency metadata; lock file at `ddo/build.py.lock` (NOT repo-root `uv.lock`)
- **Typst** (`typst` PyPI package, version pinned in PEP 723 header): in-process PDF compilation, no system install required
- **Jinja2**: HTML/MD rendering; autoescape enabled for HTML only (`autoescape=(fmt == "html")`)
- **PyYAML** (`yaml.safe_load`): YAML parsing — safe_load only, never full_load
- **Ruff**: linting + formatting (line length 100, Google docstring convention)
- **pytest**: test runner (unit + integration)
- **pypdf**: PDF text extraction in integration tests

## Design Patterns

- **YAML as Source of Truth**: `document_data.yaml` is the immutable data layer. Rendered documents are derived outputs. Never patch a rendered file — always patch YAML and re-render.
- **PEP 723 hermetic script**: `ddo/build.py` runs via `uv run --locked ddo/build.py`, enforcing `ddo/build.py.lock`. All render dependencies are pinned and self-contained.
- **Importable validation gate**: `ddo.validation.validate(data: dict) -> None` is importable by tests and other tools (not just called by `build.py`). Raises `ValidationError` on first failure.
- **Atomic write pattern**: `tempfile.mkstemp(dir=target.parent)` → write → `os.fsync` → `os.replace`. Prevents partial writes on crash.
- **Path containment**: `assert_within_documents(path)` resolves realpath and raises `PathContainmentError` if the path escapes `Documents/`. Structural prevention of directory traversal.
- **Sentinel token**: `[[DDO::REQUIRES_INPUT: <reason>]]` — used in YAML fields that cannot be filled from source material. `validate()` scans all string values recursively and raises if any sentinel is found.
- **Fabrication tripwire**: Advisory scanner in `ingest.py` that collects date/number/proper-noun tokens from rendered YAML and checks if they appear verbatim in source documents. Advisory only — never raises.
- **Human-gated golden fixtures**: `tests/fixtures/` is agent-write-blocked. The `fixture_signoff_guard.py` pre-commit hook rejects any commit touching `tests/fixtures/` unless `DDO_FIXTURE_SIGNOFF=1` is set in the environment.
- **Daemon-thread render guard**: `build.py` runs the render function in a daemon thread with a wall-clock timeout (default 30 s) and a 64 MiB output-size cap. Prevents runaway templates from hanging or OOM-ing the process.
- **CLI-authoritative template routing**: Templates are resolved strictly from `--template` and `--format` CLI flags. `meta.template` in the YAML is never consulted for routing — only the human-supplied CLI flags are trusted.

## Conventions

- **Date format in YAML**: dotted — `"2026.06.29"` (not ISO dashes `"2026-06-26"`)
- **Output path**: `Documents/YYYY.MM.DD_DocType_Title/output/<slug>.<ext>`
- **Test IDs**: Evidence IDs are `ev-001` style. Section IDs are `s1`, `s2`, etc.
- **No repo-root uv.lock for PEP 723 scripts**: The script lock is `ddo/build.py.lock`; a repo-level `uv.lock` may exist for dev deps but is not used by `uv run --locked ddo/build.py`.
- **Red Team reads Jinja2/Markdown, never PDF**: HTML/MD are deterministically derived from YAML and machine-parseable. PDF is not.
- **`tests/candidate_outputs/`**: Blocked from agent reads (`.agentignore`). Unverified AI outputs live here until a human promotes them to `tests/fixtures/`.
- **`spec/archive/`**: Audited MiniPRDs archived here with `_AUDITED` suffix. Blocked from agent reads.
