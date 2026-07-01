# Draft PRD: DDO v0.0.2 — The Adversarial Loop

> **Status:** DRAFT (output of `/hyper-architect`). Source: `PRDs/{Red_Team,Interview,Refine,Run_Skill_Composite}.md` + `spec/compiled/SuperPRD.md` (v0.0.1) + an Architect interview with the user.
> **Version:** v0.0.2
> **Date:** 2026-06-29
> **Author:** Thomas J. L. Mustard (interviewed) + Architect Agent
> **Parent Node:** `ddo_system`
> **Next step:** Start a new conversation and run `/hyper-redteam`.

---

## 1. Introduction & Goals

### Problem Statement
v0.0.1 delivered a trustworthy, reproducible **YAML → document** core: the renderer adds no word the YAML did not contain, and identical YAML + template yields identical output. But a faithful render of a *flawed* document is still a flawed document. v0.0.1 has no mechanism to make a document *better* — to surface its gaps, ambiguities, and unsupported claims, resolve them with the author, and fold the fixes back into the source of truth without corrupting it.

v0.0.2 closes that loop. It adds the three deferred adversarial-loop skills (`ddo-red-team`, `ddo-interview`, `ddo-refine`) that critique a rendered document against a domain persona, resolve the findings with the human, and safely patch `document_data.yaml` — then re-render. The zero-hallucination, HITL-gated, YAML-is-truth invariants carry forward unchanged; the loop only ever mutates the one mutable artifact (`document_data.yaml`) through code-enforced safety, never by hand-editing text.

### Solution Overview
A manually-driven, HITL-gated loop layered on the v0.0.1 backbone:

```
rendered MD/HTML  →  ddo-red-team   → red_team_report_vN.yaml  (+ derived red_team_view_vN.md)
                  →  ddo-interview  → interview_log_vN.yaml      (resolutions; report findings marked resolved)
                  →  ddo-refine     → validated structured patch → document_data.yaml → re-render
                  →  [loop again, or finalize]
```

- **Two new code modules** under `ddo/`, both reusing v0.0.1 primitives (`ingest.atomic_write`, `paths.assert_within_documents`, `validation.validate`):
  - **`ddo.review`** — owns the critique/interview data layer: in-code structural contracts for `red_team_report` and `interview_log`, their atomic + contained writes, deterministic generation of the `red_team_view` and consolidated `history` Markdown views, and deterministic `_vN` version derivation.
  - **`ddo.refine`** — the mutation layer: applies structured patches to the parsed `document_data.yaml` dict, runs the importable `validate()` **in-memory before any write**, and commits atomically only on contract-clean + human-approved patches.
- **Three new HACF skills** (`ddo-red-team`, `ddo-interview`, `ddo-refine`) that do the cognitive work and delegate every safety-critical mechanic to the two modules — mirroring how `ddo-ingest`/`ddo-render` delegate to `ddo.ingest`/`ddo.paths`/`build.py`.
- **Versioned review history**: each pass is snapshotted as `_vN` files under `review_history/`, with a single concise consolidated `history.yaml` (machine) + derived `history.md` (human).

### Target Audience
Unchanged from v0.0.1: the system's designer and other technical users generating structured documents (PRDs, scientific reports) who require reproducibility, zero hallucination, and now an auditable critique-and-refine loop. Single-user, local-filesystem, Claude Code / HACF-driven; not a SaaS product.

### The Mutation Boundary (carried forward, sharpened)
The single mutable source of truth remains `document_data.yaml`. The loop introduces two **machine-readable** working artifacts (`red_team_report_vN.yaml`, `interview_log_vN.yaml`) and their **read-only, code-generated Markdown views** — but only `ddo-refine`, through `ddo.refine`'s validated pipeline, is ever permitted to write `document_data.yaml`. The Red Team critiques the **MD/HTML render, never the PDF** (text-extraction reliability), and the Markdown views are **never parsed back** into the data layer.

---

## 2. Confidence Mandate

- **Confidence Score: 8 / 10.** Scope, the mutation-safety model, the two-module split, the storage/versioning layout, the cross-contamination firewall, and the Novel-frontier testing strategy were all resolved with the user in the Architect interview. The architecture reuses verified v0.0.1 primitives rather than inventing new ones. Residual uncertainty is implementation-level — chiefly the expressiveness of the structured-patch grammar and the safe presentation of Before/After diffs — and is exactly what the Red Team should stress.
- **Open questions to carry into `/hyper-redteam`:**
  1. **Patch-grammar expressiveness.** The minimal set is `set` (replace a scalar/string at a structured path), `append_evidence` (add an `evidence_bank` entry + link it from a section), and `append_review_log` (acknowledge/dispute trace). Is that sufficient for real `revise` resolutions, or do we need list-insert/delete and nested-path addressing? Over-expressive grammar widens the corruption surface; too narrow forces hand-edits (which are forbidden).
  2. **Diff presentation safety.** The Before/After diff is for human eyes only and must never be parsed back. How is it rendered (unified text diff of serialized YAML blocks) without tempting a re-parse, and without leaking into the data layer?
  3. **Partial refinement.** May `ddo-refine` run when only *some* findings are resolved (the rest `deferred`), or must every finding carry a decision first? Recommendation: allow partial; `deferred` is a first-class decision.
  4. **`_vN` derivation robustness.** Version is derived from existing `review_history/` files. How does it behave under manual tampering, gaps in the sequence, or a half-written prior pass?
  5. **Interview ↔ report coupling.** `ddo-interview` marks findings `resolved: true` in the report. Does it mutate `red_team_report_vN.yaml` in place (atomically) or only the in-memory copy + the log? Recommendation: in-place atomic update so the snapshot reflects final resolution state.

---

## 3. Scope

### In-Scope (v0.0.2)
- **`ddo-red-team`** skill — adversarial critique of a rendered MD/HTML document against a persona; emits `red_team_report_vN.yaml` + derived `red_team_view_vN.md`.
- **`ddo-interview`** skill — paced, batched Q&A resolving findings into `interview_log_vN.yaml`; marks report findings resolved.
- **`ddo-refine`** skill — applies validated structured patches to `document_data.yaml`, presents Before/After for approval, re-renders via `ddo-render`.
- **`ddo.review`** module — report/log structural contracts, atomic + contained writes, deterministic `red_team_view`/`history` Markdown generation, `_vN` derivation.
- **`ddo.refine`** module — pure `apply_patches`, `validate()`-before-write enforcement, atomic contained commit.
- **Versioned `review_history/`** snapshot tree (`_vN` files) + single consolidated `history.yaml` (machine) + derived `history.md` (human).
- **`meta.review_log`** in `document_data.yaml` — durable acknowledge/dispute traceability riding with the source of truth.
- **Personas exercised for real**: `product_critic`, `scientific_reviewer` move from "forward-compat, smoke-tested only" to active inputs of `ddo-red-team`/`ddo-interview`.
- **Tests**: deterministic unit tests for `ddo.review` and `ddo.refine` (incl. the safety linchpin); one human-gated end-to-end loop integration fixture.

### Out-of-Scope (deferred to v0.0.3+)
- **The `ddo-run` composite macro.** Auto-chaining all phases in one context structurally conflicts with the fresh-context firewall and the HITL gates; deferred until an orchestration that pauses-and-rehydrates per gate is designed.
- **Automated quality/accuracy scoring of critique content** (only *structural* validation of the report in v0.0.2).
- **`ddo-create-persona`, `ddo-migrate`, `writing_style.md` enforcement, multi-author interview, DOCX/Pandoc, network/URL ingestion** — all remain out of scope.
- New document types beyond `prd` and `scientific_report`.
- Concurrent/multi-process editing of a single document folder.

---

## 4. User Stories (Atomic)

| ID | User Story | Acceptance Criteria | Priority |
|---|---|---|---|
| US-001 | As a reviewer, I want to run an adversarial critique of a rendered MD/HTML document against a chosen persona, so that findings are captured as machine-readable data without parsing the PDF. | 1. `ddo-red-team` reads the **MD/HTML render** (never PDF) and the persona file; persona defaults to `meta.persona` when present, else explicit selection is required (no silent default).<br>2. Emits `review_history/red_team_report_vN.yaml` with `meta` + a `findings[]` array; each finding has `id, severity, category, location, description, suggestion, resolved(=false), resolution(=null)`.<br>3. Every `severity` ∈ the persona's taxonomy (`Critical\|Major\|Minor`); a non-taxonomy severity is a hard error.<br>4. `red_team_view_vN.md` is **generated deterministically from the report** (code, not hand-authored).<br>5. `vN` is derived in code as `max(existing N)+1`; ends at `[WAITING FOR USER REVIEW]` and instructs a **fresh context** before interview. | High |
| US-002 | As an author, I want a paced, batched Q&A to resolve red-team findings, so that every decision is captured as traceable data. | 1. `ddo-interview` loads `red_team_report_vN.yaml`, filters `resolved:false`, sorts Critical→Major→Minor, presents `batch_size` (default 2) at a time.<br>2. Each resolution records `finding_id`, `decision ∈ {revise, add_evidence, acknowledge, dispute, defer}`, free-text `detail`, and a structured `patch` (null for acknowledge/dispute/defer).<br>3. On commit, writes `review_history/interview_log_vN.yaml` (atomic, contained) and marks the corresponding report findings `resolved:true` (atomic in-place update).<br>4. Halts at `[WAITING FOR USER RESPONSE]` per batch; never auto-advances. | High |
| US-003 | As an author, I want approved resolutions applied to `document_data.yaml` as validated structured patches with a Before/After diff, then auto re-rendered, so the document improves without corrupting the YAML. | 1. `ddo.refine.apply_patches` applies each `patch` to the **parsed dict** (never text), supporting `set`, `append_evidence`, `append_review_log`.<br>2. `validate()` runs on the patched dict **before any write**; on failure → abort, write nothing, surface the precise error.<br>3. A Before/After diff is presented for HITL approval (`approve all` / `skip <n>`); diff is human-only, never re-parsed.<br>4. On approval, the patched YAML is committed via `atomic_write` (containment-asserted); then `ddo-render` is invoked.<br>5. `acknowledge`/`dispute` decisions append to `meta.review_log`. | High |
| US-004 | As an author, I want each pass snapshotted and summarized, so I can audit how the document evolved across loops. | 1. Each pass leaves `red_team_report_vN.yaml`, `red_team_view_vN.md`, `interview_log_vN.yaml` under `review_history/`.<br>2. A single `review_history/history.yaml` holds one record per pass (`version, timestamp, persona, finding counts by severity, resolution counts by decision, render outcome`), appended each pass.<br>3. `review_history/history.md` is **derived read-only** from `history.yaml`.<br>4. `document_data.yaml` itself is **not** versioned (single evolving file). | Medium |
| US-005 | As a maintainer, I want refine to reject any contract-breaking patch before writing, so a bad patch can never corrupt the source of truth. | 1. Given a patch that introduces a dangling evidence ref, a duplicate evidence ID, a contract violation, or a `[[DDO::REQUIRES_INPUT:` sentinel, `ddo.refine` **aborts before write**.<br>2. After such an abort, `document_data.yaml` is **byte-identical** to its pre-refine state.<br>3. The abort message names the offending field/ID (surfaced from `ValidationError`). | High |
| US-006 | As a maintainer, I want a regression suite covering the loop's deterministic mechanics and one end-to-end gap-closing pass, so future changes can't silently break the core guarantees. | 1. Unit tests cover `ddo.review` contracts (pass/fail), `_vN` derivation, and deterministic view/history generation from a fixed report.<br>2. Unit tests cover `ddo.refine` patch-apply, validate-before-write, and the US-005 safety linchpin.<br>3. A **human-gated** integration test drives a seeded-gap `document_data.yaml` + signed-off `interview_log` through refine → asserts `validate()`-clean, renders all 3 formats, gap closed; **skips until `DDO_FIXTURE_SIGNOFF=1`**.<br>4. `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .` all exit 0. | High |

---

## 5. Technical Specifications

### Architecture & Resolved Trade-offs

**The loop (value mutation).** Rendered MD/HTML → persona critique (`red_team_report_vN.yaml`) → human interview (`interview_log_vN.yaml`) → validated structured patch of `document_data.yaml` (`ddo.refine`) → re-render → optionally loop. The single mutable state is `document_data.yaml`; reports/logs/views are derived, disposable-but-archived working artifacts.

**Skills are cognitive; code owns safety.** Exactly as v0.0.1: the agent performs judgment (critique, resolution translation, patch proposal) and the deterministic safety mechanics live in code and are **reused, not re-implemented** — `ingest.atomic_write` (+ `OverwriteError`), `paths.assert_within_documents`, `validation.validate`.

**`ddo.refine` — the mutation pipeline (highest-risk path).**
1. Load `document_data.yaml` (dict) + `interview_log_vN.yaml`.
2. `apply_patches(data, log) -> dict` — **pure**, no I/O; applies `set`/`append_evidence`/`append_review_log` to the parsed structure. Never edits YAML as text.
3. `validate(patched)` — the importable v0.0.1 gate, run **in-memory before any write**; raise → abort, write nothing.
4. Skill renders Before/After diff (human-only) and gates on approval.
5. `commit_refine(...)` — defensively re-`validate()`, then `atomic_write` with realpath containment (force=True, since the target legitimately exists).
6. Append a `history.yaml` record; regenerate `history.md`; invoke the `ddo-render` skill.

> `ddo.refine` **does not call `build.py`**. The `ddo-refine` skill invokes the `ddo-render` skill for the re-render, so output-path routing stays solely in `ddo-render` and `refine_engine` never re-derives paths.

**`ddo.review` — the critique/interview data layer.** Owns report/log structural validation (`validate_report`, `validate_interview_log` → `ReportValidationError`), atomic + contained writes, deterministic `_vN` derivation (`report_version(doc_dir)` = `max(existing N)+1` for a new pass; current `max(N)` for interview/refine), and deterministic Markdown generation (`render_report_view(report) -> str`, `render_history_view(history) -> str`). Views derive from data; data is never derived from views.

**Cross-contamination firewall.** A **fresh context window is mandated only at the `ddo-red-team` boundary** — the critique's value depends on not inheriting the authoring/ingest rationale. `ddo-interview` and `ddo-refine` are collaborative and may share one context; the `red_team_report_vN.yaml` artifact is the clean hand-off.

**Path safety & atomicity (inherited).** Every new write (`review_history/*`, `document_data.yaml`) is composed via `ddo.paths` and asserted inside `Documents/` before writing; all writes go through the temp→fsync→`os.replace` atomic pipeline. Markdown views are code-generated only.

### Data Contracts (in code, not `ddo/schemas/`)

`red_team_report_vN.yaml`:
```yaml
meta:
  version: <int N>
  persona: <persona_name>
  document: <relative path to the critiqued MD/HTML render>
  timestamp: <ISO-8601>
findings:
  - id: <str>
    severity: Critical | Major | Minor      # ∈ persona taxonomy
    category: <persona attack-vector name>
    location: <section ref / quoted span>
    description: <what is wrong>
    suggestion: <how to fix>
    resolved: false
    resolution: null
```

`interview_log_vN.yaml`:
```yaml
meta:
  version: <int N>
  timestamp: <ISO-8601>
resolutions:
  - finding_id: <str>
    decision: revise | add_evidence | acknowledge | dispute | defer
    detail: <free-text from user>
    patch:                                   # null for acknowledge/dispute/defer
      op: set | append_evidence | append_review_log
      target: <structured path, e.g. content.sections[2].body>
      value: <new content | evidence entry | review-log record>
```

`review_history/history.yaml` (single consolidated, appended per pass):
```yaml
passes:
  - version: <int N>
    timestamp: <ISO-8601>
    persona: <persona_name>
    findings: { critical: <int>, major: <int>, minor: <int> }
    resolutions: { revise: <int>, add_evidence: <int>, acknowledge: <int>, dispute: <int>, defer: <int> }
    render: <ok | failed>
```

### Module API (proposed)
```
ddo.review:
  report_version(doc_dir: Path) -> int
  validate_report(report: dict) -> None            # raises ReportValidationError
  validate_interview_log(log: dict) -> None         # raises ReportValidationError
  write_report(doc_dir, report, version, force=False) -> Path     # atomic, contained
  write_interview_log(doc_dir, log, version, force=False) -> Path
  render_report_view(report: dict) -> str           # deterministic MD
  append_history(doc_dir, entry: dict) -> None       # append history.yaml + regen history.md

ddo.refine:
  apply_patches(data: dict, log: dict) -> dict       # PURE, no I/O
  commit_refine(data_path: Path, patched: dict, force=True) -> Path
                                                     # re-validate() + atomic_write + containment
```

### Storage Layout
```
Documents/<meta.date>_<meta.doc_type>_<title-slug>/    # gitignored
├── document_data.yaml                # source of truth (single evolving file)
├── review_history/
│   ├── red_team_report_vN.yaml       # machine, per-pass
│   ├── red_team_view_vN.md           # human view, derived from report_vN
│   ├── interview_log_vN.yaml         # machine, per-pass
│   ├── history.yaml                  # single consolidated history (machine)
│   └── history.md                    # derived read-only human view
└── output/<title-slug>.{pdf,html,md}
```

### System Graph Blast Radius
**New Atomic nodes**
- `review_engine` (`ddo/review.py`) → implements `ddo_core`; depends_on `ingest_helpers`, `path_deriver`.
- `refine_engine` (`ddo/refine.py`) → implements `ddo_core`; depends_on `validation_gate`, `ingest_helpers`, `path_deriver`.
- `skill_red_team` (`ddo/skills/ddo-red-team.md`) → implements `ddo_skills`; depends_on `review_engine`, `ddo_personas`.
- `skill_interview` (`ddo/skills/ddo-interview.md`) → implements `ddo_skills`; depends_on `review_engine`, `ddo_personas`.
- `skill_refine` (`ddo/skills/ddo-refine.md`) → implements `ddo_skills`; depends_on `refine_engine`, `skill_render`.
- `test_review_unit` (`tests/unit/test_review.py`) → implements `tests_unit`; depends_on `review_engine`.
- `test_refine_unit` (`tests/unit/test_refine.py`) → implements `tests_unit`; depends_on `refine_engine`.
- `test_loop_integration` (`tests/integration/test_loop.py`) → implements `tests_integration`; depends_on `refine_engine`, `review_engine`, `render_fixture`.

**Touched existing nodes (→ `needs_review` on build)**
- `ddo_core`, `ddo_skills` (gain children; `ddo_skills` description must drop "Ingest and Render only").
- `ddo_personas` ("forward-compat, unused, smoke-tested only" → **actively exercised**; description/status update).
- `validation_gate`, `ingest_helpers`, `path_deriver`, `build_orchestrator` — **reused, not modified** (new inbound edges only).

> `architecture.yml` is **not** edited by this PRD. It is reconciled by `/hyper-audit` / `/hyper-discover` after the code lands.

### Execution Checklist (MiniPRDs — to be compiled by `/hyper-resolve`)
- [ ] `MiniPRD_ReviewEngine.md` — node `review_engine`
- [ ] `MiniPRD_RefineEngine.md` — node `refine_engine`
- [ ] `MiniPRD_RedTeamSkill.md` — node `skill_red_team`
- [ ] `MiniPRD_InterviewSkill.md` — node `skill_interview`
- [ ] `MiniPRD_RefineSkill.md` — node `skill_refine`
- [ ] `MiniPRD_LoopTestSuite.md` — nodes `test_review_unit`, `test_refine_unit`, `test_loop_integration`

### Dependencies
- **Runtime:** no new runtime dependencies anticipated (`pyyaml`, `jinja2` already pinned in v0.0.1; view generation can reuse Jinja2 or be pure string building). Confirmed at MiniPRD time.
- **Dev:** `pytest`, `ruff` (unchanged).
- **Lint contract:** unchanged from v0.0.1 (ruff line-length 100, Google docstrings, isort first-party `ddo`).
- **Tooling:** `uv` (hermetic). No system Typst, no Pandoc, no network.

---

## 6. Negative Constraints

- **DO NOT** hand-edit `document_data.yaml` as text in `ddo-refine`; mutate the parsed dict via structured patches only.
- **DO NOT** write `document_data.yaml` from any path other than `ddo.refine`'s validated pipeline; the in-memory `validate()` must pass **before** the write.
- **DO NOT** let `ddo.refine` call `build.py` directly; re-render only via the `ddo-render` skill.
- **DO NOT** parse any Markdown view (`red_team_view_vN.md`, `history.md`) back into the data layer; views are read-only and code-generated.
- **DO NOT** critique the PDF; the Red Team reads the MD/HTML render only.
- **DO NOT** let `ddo-red-team` inherit prior-phase conversation context; mandate a fresh context window at that boundary.
- **DO NOT** pick a `_vN` version number by hand; derive it in code from `review_history/`.
- **DO NOT** auto-advance past any phase gate (`[WAITING FOR USER REVIEW]` / `[WAITING FOR USER RESPONSE]`).
- **DO NOT** define `red_team_report`/`interview_log`/`history` schemas in `ddo/schemas/` (author-facing document contracts only); their contracts live in `ddo.review`.
- **DO NOT** let any write escape `Documents/`; containment assertion is mandatory before every write.
- **DO NOT** assert content-equality on AI-generated critique or patch *content* in tests; test structure and safety only.
- **DO NOT** let an agent fabricate or promote the human-gated loop fixture; it requires `DDO_FIXTURE_SIGNOFF`.
- **DO NOT** add network access, new document types, or the `ddo-run` composite in v0.0.2.

---

## 7. Risks & Mitigation

- **R1 — Patch grammar too narrow → forces forbidden hand-edits; too wide → corruption surface.** Mitigation: start minimal (`set`/`append_evidence`/`append_review_log`); the `validate()`-before-write gate (US-005) caps blast radius regardless; Red Team to pressure-test expressiveness (open question #1).
- **R2 — A refine patch silently corrupts `document_data.yaml`.** Mitigation: pure `apply_patches` + mandatory in-memory `validate()` before write + atomic write + the US-005 byte-unchanged-on-abort test (the safety linchpin).
- **R3 — `_vN` derivation breaks under tampering / gaps / half-written passes.** Mitigation: derive in code with explicit handling of non-contiguous/partial sequences; covered by unit tests (open question #4).
- **R4 — Markdown view accidentally treated as a data source.** Mitigation: views are code-generated only; negative constraint + no read path from views into the data layer.
- **R5 — Loop non-determinism leaks into the regression suite.** Mitigation: Candidate Artifact protocol — only structural/safety assertions are automated; the end-to-end fixture is human-signed-off and skips until promoted.
- **R6 — Cross-contamination: critique biased by authoring context.** Mitigation: fresh-context firewall at the `ddo-red-team` boundary; the report YAML is the only hand-off.

---

## 8. Success Metrics (each tied to a named test)

- **M1 (critique structure):** `red_team_report_vN.yaml` is schema-valid with all required finding fields and taxonomy-valid severities; malformed reports fail closed — `test_review_unit::test_report_contract`.
- **M2 (deterministic views & versioning):** `render_report_view` and `history` generation are byte-deterministic for a fixed report; `_vN` derivation is correct across contiguous/partial sequences — `test_review_unit::test_view_and_version`.
- **M3 (refine safety linchpin):** a contract-breaking patch aborts before write and leaves `document_data.yaml` byte-identical — `test_refine_unit::test_bad_patch_aborts_unchanged`.
- **M4 (patch correctness):** `apply_patches` produces a `validate()`-clean dict for `set`/`append_evidence`/`append_review_log` on valid input — `test_refine_unit::test_apply_patches`.
- **M5 (end-to-end loop, human-gated):** a seeded-gap `document_data.yaml` + signed-off `interview_log` refines to a `validate()`-clean YAML that renders all 3 formats with the gap closed; skips until `DDO_FIXTURE_SIGNOFF=1` — `test_loop_integration::test_gap_closing_pass`.
- **M6 (lint/suite):** `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .` all exit 0.

---

## Appendix: Decisions Locked During the Architect Interview

| # | Decision |
|---|---|
| D1 | v0.0.2 = the three core loop skills (`ddo-red-team`, `ddo-interview`, `ddo-refine`) as the **manual** loop; `ddo-run` composite **deferred to v0.0.3** (conflicts with the fresh-context firewall + HITL gates). |
| D2 | `ddo-refine` **never** hand-edits YAML text. New `ddo.refine` module: structured patch → in-memory `validate()` **before write** → diff → atomic contained write. |
| D3 | Two new code modules: `ddo.review` (report/log contracts, atomic writes, view + `_vN` generation) and `ddo.refine` (mutation). Report/log contracts live **in code**, not `ddo/schemas/`. |
| D4 | Full versioned history pulled into v0.0.2: `_vN` snapshots of report/view/log under `review_history/`, plus a single consolidated `history.yaml` (machine) + derived `history.md` (human). `document_data.yaml` stays a single evolving file. `meta.review_log` retained for acknowledge/dispute. |
| D5 | Blast radius: 8 new Atomic nodes; reuse (not modify) `validation_gate`/`ingest_helpers`/`path_deriver`/`build_orchestrator`; `ddo.refine` re-renders via the `ddo-render` skill, not `build.py`. |
| D6 | Single-user/local/no-network inherited. Fresh-context firewall **only** at the `ddo-red-team` boundary; persona defaults to `meta.persona`, else explicit selection. |
| D7 | Novel-frontier testing: structural validation of critique only (no quality scoring); deterministic unit tests for mechanics + the refine safety linchpin; one **human-gated** end-to-end loop fixture under `DDO_FIXTURE_SIGNOFF`. |
