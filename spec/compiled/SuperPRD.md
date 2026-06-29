# SuperPRD: DDO v0.0.1 — Deterministic Rendering Backbone

> **Status:** COMPILED (output of `/hyper-resolve`). Source: `Draft_PRD.md` + `RedTeam_Report.md`, mediated with the user.
> **Version:** v0.0.1
> **Date:** 2026-06-27
> **Author:** Thomas J. L. Mustard (interviewed) + Architect Agent + Red Team + Resolution Agent
> **Parent Node:** `ddo_pipeline`

---

## 1. Introduction & Goals

### Problem Statement
AI-assisted document generation is unreliable: the model is a black box that hallucinates facts, invents citations, and produces output that cannot be verified against a ground truth. DDO eliminates this by separating **data** (YAML, version-controlled, human-verified) from **presentation** (templates, deterministically applied). The AI performs cognitive work (extraction; later critique/refinement) but never writes directly to the final document.

DDO's full vision is a 5-phase pipeline (**Ingest → Render → Red Team → Interview → Refine**). **This PRD scopes only v0.0.1: the deterministic rendering backbone.** Without a trustworthy, reproducible YAML→document core, the adversarial loop downstream has nothing solid to stand on.

### Solution Overview
- A hermetic `build.py` orchestrator (PEP 723, run via `uv run`) that renders a validated `document_data.yaml` to PDF (Typst), HTML (Jinja2), and Markdown (Jinja2), and that owns all deterministic validation.
- The two existing schemas (`prd`, `scientific_report`) and six template stubs, migrated from `PRDs/` into `ddo/` and wired to `build.py`.
- Two HACF cognitive skills: `ddo-ingest` (sources → YAML, zero-hallucination) and `ddo-render` (thin wrapper that derives output paths and invokes `build.py`).
- A regression suite that locks determinism and the validation contract.

### Target Audience
The system's designer and other technical users who generate structured documents (PRDs, scientific reports) and require reproducibility and zero hallucination. DDO is a Claude Code / HACF-driven toolkit — single-user, local-filesystem operation, not a SaaS product.

### The Two Guarantees (Red Team #1 — headline claim split)
The headline promise is split into two **separately-verifiable** claims so the value prop is honest:
- **(A) Render fidelity** — *deterministic, tested.* The renderer adds no word the YAML did not contain; identical YAML + template produces identical output (HTML/MD byte-identical; PDF content-identical). Enforced by the validation gate and the determinism regression suite.
- **(B) Extraction fidelity** — *human-gated, NOT machine-verified in v0.0.1.* Whether `ddo-ingest` faithfully mapped source → YAML is verified by the human at the HITL gate, aided (best-effort, non-blocking) by the fabrication tripwire. This is a **stated limitation**, not an implied guarantee.

---

## 2. Confidence Mandate

- **Confidence Score: 9 / 10.** Scope, boundaries, the deterministic/novel split, and every Red Team finding were resolved with the user. Residual uncertainty is implementation-level and gated by an explicit pre-build spike (see Risk R2 / the timestamp go/no-go).
- **Remaining open items (gated, not blocking compilation):**
  1. **Timestamp spike (go/no-go).** Does the `typst` PyPI package expose creation-timestamp control in-process, or via its vendored CLI entrypoint? Resolved by a pre-build spike; if neither path is hermetic, byte-identical PDF (US-003) is de-scoped from v0.0.1 with a decision record. The package's **vendored CLI counts as hermetic** (in-package, no system install).
  2. **Template/schema field parity.** Do the six migrated stubs render against the canonical schemas unmodified? Verified in MiniPRD 3 before wiring.

---

## 3. Scope

### In-Scope (v0.0.1)
- `ddo/build.py` — hermetic PEP 723 orchestrator with the full deterministic validation gate and three-format rendering.
- `ddo/schemas/{prd,scientific_report}.yaml` — migrated + renamed from `PRDs/` (short doc-type names).
- `ddo/templates/typst/{prd,scientific_report}.typst` — migrated PDF templates.
- `ddo/templates/jinja2/{prd,scientific_report}.{html,md}.jinja2` — migrated HTML/MD templates.
- `ddo/fonts/` — bundled, pinned fonts for Typst (hermeticity, Red Team #3).
- `ddo-ingest` skill (sources → `document_data.yaml`, zero-hallucination, gap-flagging, atomic writes, overwrite guard, advisory fabrication tripwire).
- `ddo-render` skill (thin wrapper: derive output path from `meta`, invoke `build.py`, report result).
- `tests/unit/` + `tests/integration/` — validation-gate tests, determinism regression, ingest contract/render-ability test.
- Migrate the two persona stubs (`product_critic`, `scientific_reviewer`) into `ddo/personas/` for forward-compat (not exercised by any v0.0.1 code path; covered only by a parse/well-formed smoke test).
- Per-script lock (`ddo/build.py.lock`) committed; surgical `.gitignore` correction; fixture sign-off guard.

### Out-of-Scope (deferred to v0.0.2+)
- **The entire adversarial loop:** `ddo-red-team`, `ddo-interview`, `ddo-refine`, the `ddo-run` composite.
- DOCX / Pandoc output; network / URL ingestion; web-source provenance; multi-page HTML; template generation; `ddo-create-persona`; `ddo-migrate`; quality scoring; `review_history/` snapshots; multi-author interview.
- Any document types beyond `prd` and `scientific_report`.
- **Cross-machine** determinism for HTML/MD/PDF beyond the bundled-lockfile-and-fonts contract: determinism is asserted **same-host** (NFR boundary, Red Team #1/#14).

---

## 4. User Stories (Atomic)

| ID | User Story | Acceptance Criteria | Priority |
|---|---|---|---|
| US-001 | As an author, I want to render a valid `document_data.yaml` to PDF, HTML, and Markdown via one command, so that I get reproducible documents from a single source. | 1. `uv run --locked ddo/build.py --data <yaml> --template <t> --format <pdf\|html\|md> --output <path>` produces the file at `<path>`.<br>2. HTML and MD outputs are byte-identical across repeated runs from identical input **(same host; outputs normalized to LF + C.UTF-8)**.<br>3. PDF output is **content-identical** across runs, defined as extracted-text-layer equality (wall-clock timestamp by default). | High |
| US-002 | As an author, I want `build.py` to refuse to render an invalid document, so that I never ship a doc with broken evidence links or unfilled gaps. | 1. Missing/incomplete `meta`, empty `title`/`version`, malformed `date`, or missing `evidence_bank` → nonzero exit + precise message.<br>2. Any `content.sections[*].evidence` ID absent from `evidence_bank`, any duplicate `evidence_bank` ID, or a contentless doc (0 sections / 0 evidence refs) → nonzero exit naming the cause.<br>3. Any remaining `[[DDO::REQUIRES_INPUT:` token in a **parsed string value** → nonzero exit.<br>4. Malformed YAML → one precise message (no stack trace). | High |
| US-003 | As an author, I want byte-identical PDF output on demand, so that I can verify reproducibility when needed. | 1. `--timestamp <value>` pins the Typst creation timestamp (**format/range validated**; bad value → precise error).<br>2. Two runs with the same `--timestamp` produce byte-identical PDFs.<br>3. Omitting `--timestamp` uses wall-clock (default).<br>*Gated by the timestamp spike; de-scoped with a decision record if no hermetic path exists.* | Medium |
| US-004 | As an author, I want to ingest raw local sources into a schema-shaped `document_data.yaml` with gaps flagged, so that I start from structure without hallucinated content. | 1. `ddo-ingest` maps source content to the chosen schema, inventing nothing.<br>2. Every unfillable field becomes `[[DDO::REQUIRES_INPUT: <reason>]]`.<br>3. Output written **atomically** (temp→fsync→`os.replace`) to `Documents/<date>_<doc_type>_<slug>/document_data.yaml`; an existing YAML is **never overwritten without `--force`** (non-interactive default = abort with precise message).<br>4. An advisory **fabrication tripwire** surfaces date/number/proper-noun tokens not found verbatim in any source as "verify these."<br>5. Ends with `[WAITING FOR USER REVIEW]`. | High |
| US-005 | As an author, I want `ddo-render` to compute the correct output path and invoke the build, so that I don't manage paths by hand. | 1. Skill derives `output/<slug>.<ext>` under the document folder from `meta`, using the **sanitized slug** (whitelist `[a-z0-9-]`, strip dots, forbid `..`, length cap).<br>2. Skill derives `--template`/`--format` **from `meta`** and invokes `build.py`; reports success/failure.<br>3. Skill writes no files itself and never hand-edits a rendered artifact. | High |
| US-006 | As a maintainer, I want a regression suite that locks determinism and validation, so that future changes can't silently break the core guarantees. | 1. Unit tests cover all validation checks (pass + fail paths).<br>2. Determinism test renders both example docs to HTML/MD and asserts byte-equality against frozen fixtures; a separate test asserts PDF text-layer equality across runs.<br>3. Ingest test asserts produced YAML passes validation and renders to all three formats (no content equality).<br>4. `uv run ruff check .` and `uv run ruff format --check .` exit 0. | High |

---

## 5. Technical Specifications

### Architecture
**The Core Mutation (value loop).** Raw sources → version-controlled `document_data.yaml` (zero-hallucination, gaps flagged) → deterministic render (Typst PDF / Jinja2 HTML+MD) → [v0.0.2+: red team → interview → refine → re-render]. The single piece of mutable state is `document_data.yaml`; every rendered file is a derived, disposable artifact.

**`build.py` resolution rule.** Given `--template <T> --format <F>`:
- `F=pdf` → `ddo/templates/typst/<T>.typst`, rendered via the **`typst` Python package, in-process** (hermetic; no system Typst install), with `--font-path ddo/fonts/` pinned.
- `F∈{html,md}` → `ddo/templates/jinja2/<T>.<F>.jinja2`, rendered with Jinja2 via `render(**data)` (top-level keys `meta`, `content`, `evidence_bank`); **autoescape on for HTML**; no template re-renders a data string (no SSTI surface).
- **Routing is CLI-authoritative** (Red Team #10): `build.py` routes only off `--template`/`--format`. `meta.template`/`meta.output_formats` are descriptive metadata, never used by `build.py` for routing. `ddo-render` derives the CLI flags *from* `meta`, so the two cannot disagree.

**Validation gate** (`build.py` is the single gate; runs before any render; exits nonzero with a precise message on first failure; the `ddo-render` skill never duplicates it). Exposed as an **importable function**, not CLI-only, so the deferred v0.0.2 loop can reuse it without subprocessing (Red Team §0 #1):
1. **Parse** — malformed YAML → one precise message (no stack trace).
2. **Contract** — `meta` present; `doc_type, title, version, date, template, output_formats` present; `title`/`version` non-empty strings; `meta.date` matches `^\d{4}\.\d{2}\.\d{2}$`. `meta.persona` is **optional** in v0.0.1. `evidence_bank` present as an array. **Unknown top-level keys are ignored** (forward-compat for v0.0.2 mutation layer).
3. **Evidence-ref integrity** — every ID in any `content.sections[*].evidence` exists in `evidence_bank`; **duplicate `evidence_bank` IDs rejected**; **orphan** entries (never referenced) **warn** (non-fatal); a contentless doc (0 sections or 0 evidence refs) is **rejected**.
4. **Unfilled-input scan** — abort if the token `[[DDO::REQUIRES_INPUT:` remains in any **parsed string value** (not raw bytes/keys/comments).

**Render guard** (Red Team #3 tail). The in-process render is bounded by a wall-clock **timeout (default 30s, `--timeout` override)** and an output-size cap; on breach, abort with a precise message so a runaway template/huge YAML can't hang or OOM the orchestrator.

**Path safety** (Red Team #2). Slug = `meta.title` → lowercase → whitelist `[a-z0-9-]` (collapse/replace all else) → strip leading dots → forbid `..` → length cap (80). Before any write, the resolved output path is **asserted to be inside `Documents/`** (realpath containment), failing closed otherwise.

**Hermeticity** (Red Team #3). PEP 723 deps pinned with `==`; a committed lockfile is enforced via `uv run --locked`. (Implementation note: because `build.py` is a PEP 723 script, the lock is the per-script `ddo/build.py.lock` produced by `uv lock --script`, not a project-level `uv.lock`; `uv run --locked ddo/build.py` enforces it identically.) Fonts are **bundled in `ddo/fonts/` and pinned** via Typst's font path. "Hermetic" means **reproducible given the lockfile + bundled fonts**; the one-time PyPI fetch for `uv` resolution is acknowledged. Determinism is asserted **same-host**; outputs are normalized (LF, `C.UTF-8`, stripped trailing whitespace) so fixtures aren't host-specific.

**Storage layout.**
```
ddo/
├── build.py                      # PEP 723 hermetic orchestrator
├── schemas/{prd,scientific_report}.yaml
├── templates/
│   ├── typst/{prd,scientific_report}.typst
│   └── jinja2/{prd,scientific_report}.{html,md}.jinja2
├── fonts/                        # bundled, pinned (hermeticity)
└── personas/{product_critic,scientific_reviewer}.md   # forward-compat, unused; smoke-tested only

Documents/<meta.date>_<meta.doc_type>_<title-slug>/    # gitignored
├── document_data.yaml            # source of truth (root)
└── output/<title-slug>.{pdf,html,md}                  # rendered artifacts
```
`ddo-ingest` creates the folder + writes the YAML (atomically); `ddo-render` computes the `output/` path and passes a fully-resolved `--output` to `build.py` (which stays path-convention-agnostic and `mkdir -p`s the `--output` parent so callers can't trip on a missing dir).

### Resolved Trade-offs Log (Red Team mediation)

| RT # | Sev | Finding | Resolution |
|---|---|---|---|
| 1 | Crit | Sentinel scan false-positives on legit content (incl. DDO's own docs) | Namespaced token `[[DDO::REQUIRES_INPUT: …]]`; scan **parsed string values only**. |
| 2 | Crit | Slug/path traversal, illegal filenames, length | Whitelist slug + strip dots + forbid `..` + length cap + **realpath containment assertion within `Documents/`**. |
| 3 | Crit | "Hermetic" unenforced; no render timeout | `==` pins + committed `uv.lock` (`--locked`) + **bundled/pinned fonts**; redefine "hermetic"; add render **timeout + size cap**. |
| 4 | Crit | "Content-identical PDF" had no definition/test | Define as **text-layer extraction equality**; add a named pytest; byte-identical stays opt-in via `--timestamp`. |
| 5 | High | Zero-hallucination has no automated backstop | Add an **advisory fabrication tripwire** (token-presence vs. sources, surfaced to human) + headline claim split (A)/(B). |
| 6 | High | Gate too permissive (empty doc passes; no type/format/dup/orphan checks; malformed-YAML path) | Non-empty title/version; date regex; ≥1 section+evidence; reject dup IDs; warn orphans; precise malformed-YAML error. |
| 7 | High | HTML/MD byte-identity not guarded vs. clock/host/unordered dict | AC + unit test: no non-deterministic template output; dict iteration via `\|dictsort`; assert byte-equal HTML/MD. |
| 8 | High | `.gitignore` mitigation risked committing `tests/candidate_outputs/` | **Surgical matrix** (below) + acceptance check via `git status --porcelain` + `git check-ignore`. |
| 9 | High | timestamp spike gates US-003 + a metric; in-process vs CLI contradiction | **Pre-build go/no-go spike**; vendored CLI **counts as hermetic**; de-scope byte-identical PDF if no hermetic path. |
| 10 | Med | `meta.{template,output_formats}` vs CLI flags: two sources of truth | **CLI-authoritative** routing; `ddo-render` derives flags from `meta`; `build.py` ignores `meta` for routing. |
| 11 | Med | Non-atomic ingest writes; non-interactive overwrite undefined | **Atomic writes** (temp→fsync→`os.replace`); non-interactive default **abort**; `--force` to overwrite. |
| 12 | Med | Required-but-unused `meta.persona`; no forward-compat reservation | `persona` **optional**; gate **ignores unknown top-level keys**; persona **smoke test**. |
| 13 | Med | Fixture/overwrite "DO NOT"s are prose, not mechanical | **Fixture sign-off CI/pre-commit guard**; overwrite guard lives in `ddo-ingest` **code path**. |
| 14 | Med | Determinism fixtures may be host-specific | Normalize outputs (LF + `C.UTF-8` + strip trailing ws); state **same-host** NFR boundary. |

### Surgical `.gitignore` Matrix (Red Team #8)
- **Track:** `tests/unit/`, `tests/integration/`, `tests/fixtures/`, `spec/compiled/`, `spec/process/`.
- **Keep ignored:** `tests/candidate_outputs/`, `Documents/`, `spec/active/`, `spec/archive/`.
- **Fix:** delete the wholesale `/tests` and `/spec` lines; remove the granular ignores for `spec/compiled`, `spec/process`, `tests/fixtures`, `tests/integration`.
- **Acceptance:** `git status --porcelain` shows new test/spec files stageable **and** `git check-ignore tests/candidate_outputs/ Documents/` confirms both remain ignored.

### System Graph Blast Radius
Greenfield: `spec/compiled/architecture.yml` is empty; v0.0.1 **creates** the initial node set (to be formalized by `/hyper-discover`).
- **System:** `ddo_pipeline`
- **Module:** `build_orchestrator`, `schemas`, `templates`, `skills`, `test_suite`
- **Atomic:** `validation_gate`, `typst_renderer`, `jinja_renderer`, `template_resolver`, `path_deriver`, `skill_ingest`, `skill_render`

### Execution Checklist (MiniPRDs)
- [ ] `spec/compiled/MiniPRD_BuildCore.md` — node `build_orchestrator`
- [ ] `spec/compiled/MiniPRD_ValidationGate.md` — node `validation_gate`
- [ ] `spec/compiled/MiniPRD_SchemaTemplateMigration.md` — nodes `schemas`, `templates`
- [ ] `spec/compiled/MiniPRD_RenderSkill.md` — node `skill_render`
- [ ] `spec/compiled/MiniPRD_IngestSkill.md` — node `skill_ingest`
- [ ] `spec/compiled/MiniPRD_TestSuite.md` — node `test_suite`

### API / CLI Contract
```
uv run --locked ddo/build.py \
  --data    <path/to/document_data.yaml> \
  --template <prd|scientific_report> \
  --format  <pdf|html|md> \
  --output  <path/to/output.ext> \
  [--timestamp <value>]   # pin Typst creation timestamp (validated) for byte-identical PDF
  [--timeout  <seconds>]  # render wall-clock cap (default 30)
```
Exit 0 on success; nonzero with a single precise message on the first validation failure or render error.

### Dependencies
- **Runtime (PEP 723 inline, `==`-pinned + `uv.lock`):** `typst`, `jinja2`, `pyyaml`.
- **Dev (`pyproject.toml` `[dependency-groups]`):** `pytest`, `ruff`.
- **Lint contract:** ruff line-length 100, Google docstring convention (`D` on), isort first-party `ddo`, `PRDs/` excluded.
- **Tooling:** `uv` (hermetic). No system Typst, no Pandoc.

---

## 6. Negative Constraints

- **DO NOT** patch a rendered document directly — always patch `document_data.yaml` then re-render.
- **DO NOT** invent dates, metrics, citations, or technical specifics during ingest; write `[[DDO::REQUIRES_INPUT: <reason>]]` instead.
- **DO NOT** auto-advance past a phase gate; every skill ends at `[WAITING FOR USER REVIEW]`.
- **DO NOT** overwrite an existing `document_data.yaml` without `--force` (guard enforced **in code**, not just instruction).
- **DO NOT** duplicate validation logic in `ddo-render`; `build.py` is the single gate (exposed as an importable function).
- **DO NOT** scan raw file bytes/keys/comments for the sentinel — scan **parsed string values only**.
- **DO NOT** let any slug/path escape `Documents/`; assert realpath containment before writing.
- **DO NOT** add a system-Typst or Pandoc dependency; rendering stays hermetic via PEP 723 + `uv.lock` + bundled fonts.
- **DO NOT** emit non-deterministic content from any Jinja2 template (no clock, host, PRNG, or unordered-dict iteration).
- **DO NOT** assert exact-content equality on `ddo-ingest` output in tests.
- **DO NOT** read `spec/archive/` or `tests/candidate_outputs/`; **DO NOT** let an agent write `tests/fixtures/` (human-promoted only; enforced by the sign-off guard).
- **DO NOT** un-ignore `tests/candidate_outputs/`, `Documents/`, `spec/active/`, or `spec/archive/` when fixing `.gitignore`.
- **DO NOT** add network access in v0.0.1 (local sources only).

---

## 7. Risks & Mitigation

- **R1 — `.gitignore` wholesale-ignores `/tests` + `/spec`** → tests/specs uncommittable. **Mitigation:** apply the surgical matrix (§5) + acceptance check; **keep** `tests/candidate_outputs/`, `Documents/`, `spec/active/`, `spec/archive/` ignored.
- **R2 — `typst` package may not expose timestamp control in-process** → US-003 un-deliverable. **Mitigation:** **pre-build go/no-go spike**; vendored CLI counts as hermetic; de-scope byte-identical PDF with a decision record if no hermetic path exists.
- **R3 — Migrated templates may reference fields the schemas don't provide.** **Mitigation:** MiniPRD 3 verifies each template renders against its schema with a complete example before wiring.
- **R4 — PDF binaries in `tests/fixtures/` bloat git / aren't diffable.** **Mitigation:** store **extracted text + a content hash**, not the PDF binary (PDF determinism is content-level by default); byte-identity is exercised only in the `--timestamp` test.
- **R5 — Ingest non-determinism → silent fabrication.** **Mitigation:** Candidate Artifact protocol (human-verified at the gate; contract-validity + render-ability tests only) **plus** the advisory fabrication tripwire + the explicit (A)/(B) claim split.
- **R6 — Resource exhaustion from pathological YAML/template.** **Mitigation:** render timeout + output-size cap.

---

## 8. Success Metrics (each tied to a named test)

- **M1 (render):** both example docs (`prd`, `scientific_report`) render to PDF, HTML, MD via `build.py` with exit 0 — `test_examples_render_all_formats`.
- **M2 (HTML/MD determinism):** repeated HTML/MD renders are byte-identical (normalized) — `test_html_md_byte_identical`.
- **M3 (PDF content determinism):** repeated PDF renders are text-layer-identical — `test_pdf_content_identical`. **M3b:** `--timestamp` yields byte-identical PDFs — `test_pdf_timestamp_byte_identical` (gated on the spike).
- **M4 (validation):** every validation check fails closed with a precise message on crafted-invalid inputs — `tests/unit/test_validation_gate.py` (pass + fail paths).
- **M5 (ingest):** `ddo-ingest` turns a fixed fixture source into a schema-valid, renderable YAML with gaps flagged and zero invented content (human-verified) — `test_ingest_contract_and_renderability`.
- **M6 (path safety):** a malicious/illegal title cannot escape `Documents/` — `test_slug_containment`.
- **M7 (lint/suite):** `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .` all exit 0.

---

## Appendix: Decisions Locked During the Architect Interview (carried forward)

| # | Decision | Status after Red Team |
|---|---|---|
| Q1 | v0.0.1 = deterministic backbone; adversarial loop deferred to v0.0.2+ | Held. |
| Q2 | HTML/MD byte-identical default; PDF content-identical (wall-clock); byte-identical PDF opt-in; no PDF hash gate | **Refined:** "content-identical" now = text-layer equality with a test (RT #4). |
| Q3 | `ddo/` layout + template resolution; stubs renamed | Held; `fonts/` added (RT #3). |
| Q4 | `build.py` single gate; render skill thin | **Refined:** gate exposed as importable fn; checks hardened (RT #6). |
| Q5 | `Documents/<date>_<doc_type>_<slug>/` + `output/`; build.py path-agnostic | **Refined:** slug sanitized + containment (RT #2); build.py `mkdir -p`s parent. |
| Q6 | Hermetic `typst` Python package, in-process; drop system install | **Refined:** pins + lockfile + fonts (RT #3); vendored CLI counts as hermetic (RT #9). |
| Q7 | `ddo-ingest`: no overwrite without confirmation; local files only | **Refined:** atomic writes + `--force` + abort default (RT #11). |
| Q8 | `ddo-ingest` = sole Candidate Artifact; render-ability tests only; content human-verified | Held + fabrication tripwire + (A)/(B) split (RT #5). |

---

## Appendix: Timestamp Spike Result

> **Decision: GO.** US-003 (byte-identical PDF via `--timestamp`) is **delivered in v0.0.1**, in-process. No de-scope.

**Context (R2 / RT #9 / Confidence Mandate open item #1).** US-003 was gated on whether the `typst` PyPI package exposes creation-timestamp control via a hermetic path (in-process arg, env var, or vendored CLI). The spike was run before wiring `build.py`.

**Evidence.**
- Installed package: `typst==0.15.0` (PyPI wheel, pinned in the PEP 723 header + `ddo/build.py.lock`).
- `typst.compile(...)` exposes an **in-process** `timestamp` parameter. Per the bundled type stub (`typst/__init__.pyi`): `timestamp: Optional[CreationTimestamp]` where `CreationTimestamp = Union[int, datetime.datetime]` — "Creation timestamp as timezone-aware fixed-offset `datetime.datetime` or **UNIX seconds, equivalent to `SOURCE_DATE_EPOCH`**." No CLI subprocess and no system Typst install are required, satisfying the hermeticity definition (§5).
- Empirical verification: rendering `tests/data/prd_example.yaml` to PDF **twice with the same `--timestamp 1719446400` produced byte-identical output** (`cmp` clean); a **different** timestamp produced **different** bytes (confirming the value wires through, not a no-op); omitting `--timestamp` renders successfully on the wall clock (default).

**What was wired.** `build.py` accepts `--timestamp <UNIX seconds>`, validates it as an integer in `[0, 253402300799]` (precise error + nonzero exit on a bad value, per US-003 AC #1), and passes it to `typst.compile(timestamp=...)`. Omitting it uses the wall clock. The PDF renderer uses `root="/"` so the template's absolute `sys.inputs.data_file` virtual path resolves to the real YAML, with `ignore_system_fonts=True` and only the bundled `ddo/fonts/` on the font path.
