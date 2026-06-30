
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

### v0.0.1 Patterns

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

### v0.0.2 Patterns (Adversarial Loop)

- **`_vN` derivation is file-tree authoritative**: `report_version` = max(existing N) + 1; `current_version` = max(N). Never hand-derive or pass a hardcoded version — always call `ddo.review`.
- **Torn-pass detection before any new pass**: `detect_incomplete_pass` must be called at entry to `ddo-red-team` and `ddo-refine`. A report without its matching log is a torn pass; halt and surface reason + suggestion.
- **Flag split — `decision_recorded` vs `applied`**: `ddo-interview` sets `decision_recorded` only (via `mark_findings`). `ddo-refine` sets `applied` only after commit + render both succeed. Never set `applied` in the interview phase.
- **Pure `apply_patches`**: No I/O; operates on a deep copy; raises on bad patch before any write. `set` is leaf-scalar only (no auto-vivify, no type change); `append_evidence` appends to `evidence_bank`; `append_review_log` appends to `meta.review_log`.
- **Hand-rolled path DSL** (`parse_path`): Grammar is `IDENT(.IDENT|[INT])*`. Never `eval`/`exec` on user-controlled target strings. Non-negative integer indices only; negative indices and slices are hard errors.
- **`refine_structural_check` is refine-local**: Lives in `ddo.refine`, NOT in `ddo.validation`. Ensures sections remain a list and bodies remain non-empty strings after patching. This preserves the `validation_gate` blast radius (D5).
- **Snapshot before mutation** (`snapshot_source`, `force=False`): `document_data_pre_vN.yaml` is a byte-for-byte copy written before `apply_patches`. Double-snapshot fails closed rather than clobbering a recovery point.
- **YAML serialization rule** (`sort_keys=False`): `safe_dump(sort_keys=False, allow_unicode=True)` everywhere in the adversarial loop. `sort_keys=True` is forbidden — it would reorder keys and corrupt deterministic diffs.
- **Deterministic views — no wall-clock**: `render_report_view` and `render_history_view` read only stored data (no `datetime.now()`). Timestamps come exclusively from stored report/log dicts. Views can be regenerated identically at any time.
- **Fresh-context firewall at red-team only**: `ddo-red-team` must run in a new conversation context (critique independence). `ddo-interview` and `ddo-refine` may share one context. The `red_team_report_vN.yaml` artifact is the only authorised hand-off.
- **Audit reconcile gated on render success**: `mark_findings(..., field="applied")` and `append_history` are called only after `ddo-render` returns success. A failed render leaves `document_data.yaml` committed but findings unmarked and history unappended — the torn-pass detector will catch this on next entry.
- **`review_history/` path builder in `ddo.review`**: All artifact paths inside `review_history/` are built and containment-asserted inside `ddo.review`. Skills and callers must never construct these paths manually.

## Conventions

- **Date format in YAML**: dotted — `"2026.06.29"` (not ISO dashes `"2026-06-26"`)
- **Output path**: `Documents/YYYY.MM.DD_DocType_Title/output/<slug>.<ext>`
- **Test IDs**: Evidence IDs are `ev-001` style. Section IDs are `s1`, `s2`, etc.
- **No repo-root uv.lock for PEP 723 scripts**: The script lock is `ddo/build.py.lock`; a repo-level `uv.lock` may exist for dev deps but is not used by `uv run --locked ddo/build.py`.
- **Red Team reads Jinja2/Markdown, never PDF**: HTML/MD are deterministically derived from YAML and machine-parseable. PDF is not.
- **`tests/candidate_outputs/`**: Blocked from agent reads (`.agentignore`). Unverified AI outputs live here until a human promotes them to `tests/fixtures/`.
- **`spec/archive/`**: Audited MiniPRDs archived here with `_AUDITED` suffix. Blocked from agent reads.
