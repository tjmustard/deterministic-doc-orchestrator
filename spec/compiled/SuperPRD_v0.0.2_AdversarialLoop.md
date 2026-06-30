# SuperPRD: DDO v0.0.2 — The Adversarial Loop

> **Status:** COMPILED (output of `/hyper-resolve`). Source: `spec/active/Draft_PRD.md` + `spec/active/RedTeam_Report.md`, mediated with the user.
> **Version:** v0.0.2
> **Date:** 2026-06-29
> **Author:** Thomas J. L. Mustard (interviewed) + Architect Agent + Red Team + Resolution Agent
> **Parent Node:** `ddo_system`
> **Graph binding note:** This SuperPRD lives at `spec/compiled/SuperPRD_v0.0.2_AdversarialLoop.md`; the v0.0.1 SuperPRD remains at `spec/compiled/SuperPRD.md`. The `ddo_system` node still points at `SuperPRD.md`; `/hyper-audit` should reconcile the `ddo_system.associated_file` binding (and the new node set below) after the code lands.
> **Next step:** `/hyper-execute` each MiniPRD in `spec/compiled/`, then `hypergraph_updater.py` + `/hyper-audit`.

---

## 1. Introduction & Goals

### Problem Statement
v0.0.1 delivered a trustworthy, reproducible **YAML → document** core: the renderer adds no word the YAML did not contain, and identical YAML + template yields identical output. But a faithful render of a *flawed* document is still a flawed document. v0.0.1 has no mechanism to make a document *better* — to surface its gaps, ambiguities, and unsupported claims, resolve them with the author, and fold the fixes back into the source of truth without corrupting it.

v0.0.2 closes that loop. It adds the three deferred adversarial-loop skills (`ddo-red-team`, `ddo-interview`, `ddo-refine`) that critique a rendered document against a domain persona, resolve the findings with the human, and safely patch `document_data.yaml` — then re-render. The zero-hallucination, HITL-gated, YAML-is-truth invariants carry forward unchanged.

### Solution Overview
A manually-driven, HITL-gated loop layered on the v0.0.1 backbone:

```
rendered MD/HTML  →  ddo-red-team   → red_team_report_vN.yaml  (+ derived red_team_view_vN.md)
                  →  ddo-interview  → interview_log_vN.yaml      (resolutions; findings marked decision_recorded)
                  →  ddo-refine     → pre-refine snapshot → validated structured patch → document_data.yaml → re-render
                  →  [loop again, or finalize]
```

- **Two new code modules** under `ddo/`, both reusing v0.0.1 primitives (`ingest.atomic_write`, `paths.assert_within_documents`, `validation.validate`):
  - **`ddo.review`** — the critique/interview data layer: in-code structural contracts for `red_team_report` and `interview_log`, atomic + contained writes, deterministic generation of `red_team_view` and consolidated `history` Markdown views, deterministic `_vN` derivation, and **on-entry torn-pass detection**.
  - **`ddo.refine`** — the mutation layer: a **hand-rolled path-DSL parser** (never `eval`), a **constrained** `apply_patches` (pure), a **refine-only structural check**, a **pre-refine snapshot**, in-memory `validate()` before any write, and an atomic contained commit.
- **Three new HACF skills** (`ddo-red-team`, `ddo-interview`, `ddo-refine`) that do the cognitive work and delegate every safety-critical mechanic to the two modules — mirroring how `ddo-ingest`/`ddo-render` delegate to `ddo.ingest`/`ddo.paths`/`build.py`.
- **Versioned review history**: each pass is snapshotted as `_vN` files under `review_history/`, plus a single consolidated `history.yaml` (machine) + derived `history.md` (human), plus a **`document_data_pre_vN.yaml`** byte-for-byte snapshot of the source taken before each refine.

### Target Audience
Unchanged from v0.0.1: the system's designer and other technical users generating structured documents (PRDs, scientific reports) who require reproducibility, zero hallucination, and now an auditable critique-and-refine loop. **Single-user, local-filesystem, Claude Code / HACF-driven; not a SaaS product** — and (§3) single-user is now a *relied-upon invariant*, not merely an out-of-scope line.

### The Mutation Boundary (carried forward, sharpened)
The single mutable source of truth remains `document_data.yaml`. The loop introduces machine-readable working artifacts (`red_team_report_vN.yaml`, `interview_log_vN.yaml`) and their **read-only, code-generated Markdown views** — but only `ddo-refine`, through `ddo.refine`'s validated pipeline, is ever permitted to write `document_data.yaml`. The Red Team critiques the **MD/HTML render, never the PDF**, and the Markdown views are **never parsed back** into the data layer.

> **Honest safety claim (Red Team §1).** `validate()` is a **minimal contract** (presence/uniqueness/sentinel), *not* a structural schema. Passing `validate()` therefore bounds the blast radius to "minimal-contract-clean"; it does **not** by itself guarantee "structurally intact." v0.0.2 closes the gap with two independent guards in `ddo.refine` (RT#1) plus a pre-refine snapshot (RT#2) so a valid-but-wrong refine is both *harder to produce* and *always recoverable*.

---

## 2. Confidence Mandate

- **Confidence Score: 9 / 10.** All six Red Team triage items and both NFR groups were resolved with the user in `/hyper-resolve`. The architecture reuses verified v0.0.1 primitives rather than inventing new ones, and the highest-risk path (mutation safety) now has layered, separately-tested defenses. Residual uncertainty is implementation-level (the exact set of leaf paths the `set` whitelist permits, and Before/After diff signal-to-noise) and is gated at MiniPRD time.
- **Resolved at compile (was open in the Draft):**
  1. **Patch-grammar expressiveness** → minimal grammar locked (RT#4); structural resolutions defer to v0.0.3.
  2. **Diff presentation safety** → unified text diff of `sort_keys=False` serialized blocks, human-only, never re-parsed; the snapshot (not the diff) is the recovery source.
  3. **Partial refinement** → allowed; `defer` is a first-class decision; `skip` cascades to dependents (RT Group B).
  4. **`_vN` derivation robustness** → file-tree-authoritative with on-entry torn-pass detection (RT#6).
  5. **Interview ↔ report coupling** → in-place atomic update, but the finding flag is **split** so the report never claims an unapplied fix (RT#5).

---

## 3. Scope

### In-Scope (v0.0.2)
- **`ddo-red-team`** skill — adversarial critique of a rendered MD/HTML document against a persona; emits `red_team_report_vN.yaml` + derived `red_team_view_vN.md`.
- **`ddo-interview`** skill — paced, batched Q&A resolving findings into `interview_log_vN.yaml`; marks findings `decision_recorded`.
- **`ddo-refine`** skill — snapshots the source, applies validated structured patches to `document_data.yaml`, presents Before/After for approval, re-renders via `ddo-render`, then reconciles audit state.
- **`ddo.review`** module — report/log structural contracts, atomic + contained writes, deterministic `red_team_view`/`history` generation, `_vN` derivation, on-entry torn-pass detection.
- **`ddo.refine`** module — hand-rolled path parser, constrained pure `apply_patches`, refine-only structural check, pre-refine snapshot, `validate()`-before-write enforcement, atomic contained commit.
- **Versioned `review_history/`** (`_vN` report/view/log + `document_data_pre_vN.yaml`) + single consolidated `history.yaml` (machine) + derived `history.md` (human).
- **`meta.review_log`** in `document_data.yaml` — durable acknowledge/dispute traceability riding with the source of truth.
- **Personas exercised for real**: `product_critic`, `scientific_reviewer` move from "forward-compat, smoke-tested only" to active inputs of `ddo-red-team`/`ddo-interview`.
- **Tests**: deterministic unit tests for `ddo.review` and `ddo.refine` (incl. the safety linchpins); one human-gated end-to-end loop integration fixture.

### Out-of-Scope (deferred to v0.0.3+)
- **The `ddo-run` composite macro.** Auto-chaining conflicts with the fresh-context firewall + HITL gates; deferred until a pause-and-rehydrate orchestration is designed.
- **Structural patch operations** (list insert/delete, nested addressing, type-changing `set`, wholesale `content.sections` replacement). A resolution needing these is recorded as `acknowledge`/`defer` in v0.0.2.
- **Automated quality/accuracy scoring of critique content** (only *structural* validation of the report).
- **Round-trip-preserving serializer (`ruamel.yaml`)** and any new runtime dependency. v0.0.2 uses PyYAML `sort_keys=False`; comment fidelity is preserved via the pre-refine snapshot, not the live file.
- **Retention/pruning of `review_history/`.** Growth is **unbounded by design** for v0.0.2 (auditability > disk; single-user/local). A future cap/prune is a v0.0.3+ concern.
- **Automated coverage of the skill-mediated render handoff.** Pytest exercises the deterministic `build.py` render path; the `ddo-refine → ddo-render` skill handoff is verified in the human-gated fixture sign-off (RT§3/§4).
- **File locking / concurrency.** Single-user is a relied-upon invariant (below), not enforced with locks.
- `ddo-create-persona`, `ddo-migrate`, `writing_style.md` enforcement, multi-author interview, DOCX/Pandoc, network/URL ingestion, new document types beyond `prd`/`scientific_report`.

### Relied-Upon Invariant: Single-User / No Concurrency (Red Team §3)
Promoted from an out-of-scope line to an **explicit invariant the read-modify-write paths depend on**:
- **Fail-closed writes:** `write_report`/`write_interview_log` use `force=False` by default → a second concurrent writer hits `OverwriteError` rather than clobbering.
- **Lose-update-if-violated (documented, not guarded in v0.0.2):** the `history.yaml` append (read-modify-write) and the in-place finding-flag update can silently lose updates under concurrent writers. These are safe *only* under the single-user invariant.

---

## 4. User Stories (Atomic)

| ID | User Story | Acceptance Criteria | Priority |
|---|---|---|---|
| US-001 | As a reviewer, I want to run an adversarial critique of a rendered MD/HTML document against a chosen persona, so that findings are captured as machine-readable data without parsing the PDF. | 1. `ddo-red-team` reads the **MD/HTML render** (never PDF) and the persona file; persona defaults to `meta.persona` when present, else explicit selection is required (no silent default). **If `meta.persona` names a missing/typo'd file → hard error naming the missing persona (no fallback).**<br>2. Emits `review_history/red_team_report_vN.yaml` with `meta` + a `findings[]` array; each finding has `id, severity, category, location, description, suggestion, decision_recorded(=false), applied(=false), resolution(=null)`.<br>3. Every `severity ∈ {Critical, Major, Minor}` (a **fixed enum**, not a per-persona taxonomy); a non-enum severity is a hard error. `category` is **free-text** (persona attack-vector name), not validated.<br>4. `red_team_view_vN.md` is **generated deterministically from the report** (code, not hand-authored); it embeds only stored data (no wall-clock at view-gen time).<br>5. `vN` derived in code via on-entry detection (`max(existing N)+1`); **refuses/resumes on a detected torn prior pass** rather than stacking a new `_vN`.<br>6. A finding count above a soft threshold (default 100) emits a **warning** (no hard cap).<br>7. Ends at `[WAITING FOR USER REVIEW]` and instructs a **fresh context** before interview. | High |
| US-002 | As an author, I want a paced, batched Q&A to resolve red-team findings, so that every decision is captured as traceable data. | 1. `ddo-interview` loads `red_team_report_vN.yaml`, filters `applied:false`, sorts Critical→Major→Minor, presents `batch_size` (default 2) at a time.<br>2. Each resolution records `finding_id`, `decision ∈ {revise, add_evidence, acknowledge, dispute, defer}`, free-text `detail`, and a structured `patch` (null for acknowledge/dispute/defer).<br>3. On commit, writes `review_history/interview_log_vN.yaml` (atomic, contained) and marks the corresponding findings **`decision_recorded:true`** (atomic in-place update). It does **not** set `applied` — that is `ddo-refine`'s job after the patch lands.<br>4. Halts at `[WAITING FOR USER RESPONSE]` per batch; never auto-advances. | High |
| US-003 | As an author, I want approved resolutions applied to `document_data.yaml` as validated structured patches with a Before/After diff, then auto re-rendered, so the document improves without corrupting the YAML. | 1. `ddo-refine` first **snapshots** `document_data.yaml` → `review_history/document_data_pre_vN.yaml` (byte-for-byte) before any mutation.<br>2. `apply_patches` applies each `patch` to the **parsed dict** (never text), supporting `set` (**leaf-scalar only, no auto-vivify, no type change**), `append_evidence`, `append_review_log`; the path is parsed by a **hand-rolled parser (never `eval`)**, missing path → hard error.<br>3. A **refine-only structural check** + the importable `validate()` both run on the patched dict **before any write**; on failure → abort, write nothing, surface the precise error.<br>4. A Before/After diff (unified text of `sort_keys=False` serialized blocks) is presented for HITL approval (`approve all` / `skip <n>`); `skip <n>` **also skips later approved patches that depend on it** (no self-inflicted dangling-ref abort); diff is human-only, never re-parsed.<br>5. On approval, the patched YAML is serialized with **`yaml.safe_dump(sort_keys=False, allow_unicode=True)`** and committed via `atomic_write` (containment-asserted, `force=True`); re-render flags are derived from **`meta.template` + `meta.output_formats`** and passed explicitly to `ddo-render`.<br>6. After a **successful** re-render, the corresponding findings are marked **`applied:true`** and a `history.yaml` record is appended (`render` set from build.py's actual exit). `acknowledge`/`dispute` decisions append to `meta.review_log`. | High |
| US-004 | As an author, I want each pass snapshotted and summarized, so I can audit how the document evolved across loops. | 1. Each pass leaves `red_team_report_vN.yaml`, `red_team_view_vN.md`, `interview_log_vN.yaml`, and `document_data_pre_vN.yaml` under `review_history/`.<br>2. A single `review_history/history.yaml` holds one record per pass (`version, timestamp, persona, finding counts by severity, resolution counts by decision, applied count, render outcome`), appended each pass **after** the re-render.<br>3. `review_history/history.md` is **derived read-only** from `history.yaml` (byte-deterministic; no wall-clock at view-gen time).<br>4. `document_data.yaml` itself is **not** versioned (single evolving file); the `pre_vN` snapshots are the recovery mechanism.<br>5. The **file tree is authoritative** for "what passes happened"; `history.yaml` is reconciled to it and a phantom entry (record without artifacts) is flagged. | Medium |
| US-005 | As a maintainer, I want refine to reject any contract-breaking OR structurally-corrupting patch before writing, so a bad patch can never corrupt the source of truth. | 1. Given a patch that introduces a dangling evidence ref, a duplicate evidence ID, a contract violation, or a `[[DDO::REQUIRES_INPUT:` sentinel, `ddo.refine` **aborts before write** (importable `validate()`).<br>2. Given a `set` that targets a non-leaf path, auto-vivifies a missing path, or changes a node's type (e.g. `content.sections[*].body` → dict, or `content.sections` wholesale), `ddo.refine` **aborts before write** (constrained `set` + refine-only structural check).<br>3. After any such abort, `document_data.yaml` is **byte-identical** to its pre-refine state.<br>4. The abort message names the offending field/ID/path. | High |
| US-006 | As a maintainer, I want a regression suite covering the loop's deterministic mechanics and one end-to-end gap-closing pass, so future changes can't silently break the core guarantees. | 1. Unit tests cover `ddo.review` contracts (pass/fail), `_vN` derivation, torn-pass detection, and deterministic view/history generation from a fixed report.<br>2. Unit tests cover `ddo.refine`: path parsing, constrained-`set` rejection (US-005 AC2), validate-before-write, the byte-unchanged-on-abort linchpin (US-005 AC3), and the pre-refine snapshot/rollback (M9).<br>3. A **human-gated** integration test drives a seeded-gap `document_data.yaml` + signed-off `interview_log` through refine → asserts **sentinel-absence + `validate()`-clean + renders all 3 formats** (NOT semantic correctness); **skips until `DDO_FIXTURE_SIGNOFF=1`**.<br>4. `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .` all exit 0. | High |

---

## 5. Technical Specifications

### Architecture & Resolved Trade-offs

**The loop (value mutation).** Rendered MD/HTML → persona critique (`red_team_report_vN.yaml`) → human interview (`interview_log_vN.yaml`) → **pre-refine snapshot** → validated structured patch of `document_data.yaml` (`ddo.refine`) → re-render → audit reconcile → optionally loop. The single mutable state is `document_data.yaml`; reports/logs/views are derived working artifacts; `document_data_pre_vN.yaml` snapshots are the recovery layer.

**Skills are cognitive; code owns safety.** Exactly as v0.0.1: the agent performs judgment (critique, resolution translation, patch proposal); the deterministic safety mechanics live in code and are **reused, not re-implemented** — `ingest.atomic_write` (+ `OverwriteError`), `paths.assert_within_documents`, `validation.validate`.

**`ddo.refine` — the mutation pipeline (highest-risk path).**
1. Load `document_data.yaml` (dict) + `interview_log_vN.yaml`.
2. **Snapshot:** copy the on-disk `document_data.yaml` byte-for-byte to `review_history/document_data_pre_vN.yaml` (atomic, contained) **before any mutation**.
3. `apply_patches(data, log) -> dict` — **pure**, no I/O; applies `set`/`append_evidence`/`append_review_log` to the parsed structure via a **hand-rolled path parser**. `set` is **leaf-scalar-only, no auto-vivify, no type change**; missing path → hard error.
4. `refine_structural_check(patched)` — **refine-only** assertion (lives in `ddo.refine`, **not** in `validation_gate`): section bodies remain non-empty strings, no type drift in `meta`/`content`. Raise → abort.
5. `validate(patched)` — the importable v0.0.1 gate, run **in-memory before any write**; raise → abort, write nothing.
6. Skill renders Before/After diff (human-only, `sort_keys=False` blocks) and gates on approval (`approve all` / `skip <n>`, skip-and-dependents).
7. `commit_refine(...)` — defensively re-run the structural check + `validate()`, serialize with `yaml.safe_dump(sort_keys=False, allow_unicode=True)`, then `atomic_write` with realpath containment (`force=True`, since the target legitimately exists).
8. Invoke the `ddo-render` skill with flags derived from `meta.template`/`meta.output_formats`; capture build.py's exit status.
9. **Only on render success:** mark findings `applied:true`; append a `history.yaml` record (`render` = build.py exit); regenerate `history.md`.

> `ddo.refine` **does not call `build.py`**. The `ddo-refine` skill invokes the `ddo-render` skill for the re-render, so output-path routing stays solely in `ddo-render`. The `render` outcome recorded in `history.yaml` is build.py's **actual exit status** (surfaced by `ddo-render`), not a free-form agent claim.

**The path DSL (Red Team §5/§4).** A small, **hand-rolled, non-`eval`** parser:
```
path    := segment ( '.' segment | '[' index ']' )*
segment := IDENT                 # dict key
index   := DIGITS                # list index, non-negative, no slices/negatives
```
`set` resolves the path to an **existing leaf scalar** and replaces it in place, preserving type; a missing path, an out-of-range index, an auto-vivify attempt, or a type change is a **hard error**. `append_evidence` and `append_review_log` are **dedicated ops**, not generic path writes. Anything more expressive (list insert/delete, nested addressing) is **out of scope** (defer to v0.0.3).

**`ddo.review` — the critique/interview data layer.** Owns report/log structural validation (`validate_report`, `validate_interview_log` → `ReportValidationError`), atomic + contained writes, deterministic `_vN` derivation (`report_version(doc_dir)` = `max(existing N)+1` for a new pass; current `max(N)` for interview/refine), **on-entry torn-pass detection** (`detect_incomplete_pass`), and deterministic Markdown generation (`render_report_view`, `render_history_view`). Views derive from stored data; data is never derived from views; **no wall-clock is read at view-generation time** (timestamps come from the stored report/log).

**Torn-pass / crash recovery (Red Team §5/§6).** The sequence (snapshot → commit → render → history) is not transactional. On entry, each skill calls `detect_incomplete_pass(doc_dir)` to spot an incomplete prior pass (report without log, `document_data.yaml` newer than the latest history record, a half-written `_vN`) and **refuses/resumes** rather than stacking a new pass. The **file tree is authoritative** for which passes exist; `history.yaml` is reconciled against it, and a record without backing artifacts is flagged.

**`review_history/` path derivation (Red Team §5).** The `review_history/` path builder lives in **`ddo.review`** and calls `paths.assert_within_documents` — so `path_deriver` is **reused, not modified** (preserving the blast-radius claim).

**Cross-contamination firewall.** A **fresh context window is mandated only at the `ddo-red-team` boundary** — the critique's value depends on not inheriting the authoring/ingest rationale. `ddo-interview` and `ddo-refine` are collaborative and may share one context; the `red_team_report_vN.yaml` artifact is the clean hand-off.

**Path safety & atomicity (inherited).** Every new write (`review_history/*`, `document_data_pre_vN.yaml`, `document_data.yaml`) is composed via `ddo.paths` and asserted inside `Documents/` before writing; all writes go through the temp→fsync→`os.replace` atomic pipeline. Markdown views are code-generated only.

### Resolved Trade-offs Log (Red Team mediation)

| RT # | Sev | Finding | Resolution |
|---|---|---|---|
| 1 | Crit | `validate()` is a minimal contract → a `set` can produce a "valid-but-gutted" document (wholesale `content.sections` replace, `body` → dict) that passes the gate. | **BOTH** guards, both in **new** code so `validation_gate` is untouched (D5 preserved): (a) constrain `set` to leaf-scalar / no-auto-vivify / no-type-change; (b) a **refine-only** `refine_structural_check` inside `ddo.refine`. Drives US-005 AC2 + M8. |
| 2 | Crit | Source of truth is gitignored + unversioned + `force=True` → a valid-but-wrong refine is **irreversible**. | **Pre-refine snapshot**: copy `document_data.yaml` → `review_history/document_data_pre_vN.yaml` (byte-for-byte) before every commit. Drives R7 + M9. Also retains the original comments/key order (feeds RT#3). |
| 3 | Crit | PyYAML `safe_dump` reorders keys (`sort_keys=True`) and drops comments → fidelity loss on the project's #1 invariant. | **`yaml.safe_dump(sort_keys=False, allow_unicode=True)`** — key insertion order preserved; comments normalized on the live file but the **exact original survives in the `pre_vN` snapshot**. No new runtime dep. `sort_keys=False` pinned as a negative constraint + R8 + M7. |
| 4 | Crit | The patch `target` path DSL is undefined (possible `eval` / code-exec surface; unspecified indexing/missing-path). | **Minimal hand-rolled parser, never `eval`** (grammar above): dotted keys + non-negative `[int]` only, missing path = hard error, no auto-vivify, `set` leaf-scalar-only. Structural ops defer to v0.0.3. Answers Draft open-Q#1. |
| 5 | High | `resolved` conflates "decided" with "applied"; `history.render` is agent-asserted. | **Split the finding flag**: `decision_recorded` (set by interview) + `applied` (set by refine **only after `commit_refine` + render succeed**); next pass filters on `applied`. `history.render` = build.py's **actual exit status** surfaced by `ddo-render`, recorded **after** the re-render. Drives R9. |
| 6 | High | Sequence is non-transactional (torn pass); a deleted `_vN` yields a phantom pass; no authority between `history.yaml` and the file tree. | **On-entry `detect_incomplete_pass`** in each skill → refuse/resume, never stack a new `_vN`. **File tree is authoritative**; `history.yaml` reconciled to it; phantom entries flagged. Drives R10. |
| 7 | Med | Concurrency declared out-of-scope but relied upon silently. | Promote **single-user/no-concurrency to a relied-upon invariant** (§3): `force=False` report/log writes fail closed; `history.yaml` append + in-place flag update are documented lose-update paths. No locking in v0.0.2. |
| 8 | Med | `review_history/` retention unscoped (unbounded growth). | **Unbounded by design** for v0.0.2 (auditability > disk; single-user/local), stated explicitly in Scope. Cap/prune is v0.0.3+. |
| 9 | Med | Persona-not-found, `category` validation, finding-count bound undefined. | Persona missing → **hard named error**; `severity` is a **fixed enum** `Critical|Major|Minor` (drop "persona taxonomy" framing); `category` is **free-text** (severity drives history rollups); **no hard finding cap**, soft warning above 100; `batch_size` default 2. |
| 10 | Med | Re-render flags agent-remembered (`build.py` ignores `meta`). | Re-render flags **pinned to `meta.template` + `meta.output_formats`** and passed explicitly to `ddo-render` → deterministic, not agent-remembered. |
| 11 | Med | `skip` of a depended-upon patch causes a full-refine abort on a dangling ref. | `skip <n>` = **skip-and-its-dependents** (with a clear notice) so refine never self-inflicts a dangling-ref abort. |
| 12 | Med | Skill-mediated render handoff is unexercised by pytest. | Pytest covers the deterministic **`build.py`** render path; the **`ddo-refine → ddo-render` handoff** is verified during the human-gated fixture sign-off (logged). Coverage boundary documented (M5). |
| 13 | Low | Sentinel inconsistency: `CLAUDE.md` says `[REQUIRES USER INPUT:` but code + `ddo-ingest` use `[[DDO::REQUIRES_INPUT:`. | **Doc fix only** (not a code change): the namespaced `[[DDO::REQUIRES_INPUT:` is authoritative (ingest already emits it; the gate scans it). Reconcile `CLAUDE.md` wording via `/hyper-document`. |

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
    severity: Critical | Major | Minor      # FIXED enum (not per-persona)
    category: <str>                          # free-text persona attack-vector name
    location: <section ref / quoted span>
    description: <what is wrong>
    suggestion: <how to fix>
    decision_recorded: false                 # set true by ddo-interview
    applied: false                           # set true by ddo-refine AFTER commit + render succeed
    resolution: null                         # short pointer; full detail lives in interview_log_vN.yaml
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
      target: <path DSL, e.g. content.sections[2].body>   # set: leaf-scalar only
      value: <new scalar | evidence entry | review-log record>
      depends_on: [<patch index>, ...]       # optional; drives skip-and-dependents
```

`review_history/history.yaml` (single consolidated, appended per pass after re-render):
```yaml
passes:
  - version: <int N>
    timestamp: <ISO-8601>
    persona: <persona_name>
    findings: { critical: <int>, major: <int>, minor: <int> }
    resolutions: { revise: <int>, add_evidence: <int>, acknowledge: <int>, dispute: <int>, defer: <int> }
    applied: <int>                           # findings marked applied this pass
    render: <ok | failed>                    # from build.py's actual exit status
```

### Module API (proposed)
```
ddo.review:
  report_version(doc_dir: Path) -> int                    # max(existing N)+1 (new pass)
  detect_incomplete_pass(doc_dir: Path) -> dict | None    # torn-pass detection; None = clean
  validate_report(report: dict) -> None                   # raises ReportValidationError
  validate_interview_log(log: dict) -> None               # raises ReportValidationError
  write_report(doc_dir, report, version, force=False) -> Path        # atomic, contained
  write_interview_log(doc_dir, log, version, force=False) -> Path
  mark_findings(doc_dir, version, finding_ids, field) -> Path        # in-place atomic flag update
  render_report_view(report: dict) -> str                 # deterministic MD, stored-data only
  render_history_view(history: dict) -> str               # deterministic MD, stored-data only
  append_history(doc_dir, entry: dict) -> None            # append history.yaml + regen history.md

ddo.refine:
  parse_path(target: str) -> list[str | int]              # hand-rolled, NEVER eval
  apply_patches(data: dict, log: dict) -> dict            # PURE, no I/O; constrained set
  refine_structural_check(patched: dict) -> None          # refine-only; NOT validation_gate
  snapshot_source(data_path: Path, doc_dir: Path, version: int) -> Path   # pre-refine byte copy
  commit_refine(data_path: Path, patched: dict, force=True) -> Path
                                                          # re-check + safe_dump(sort_keys=False) + atomic_write
```

### Storage Layout
```
Documents/<meta.date>_<meta.doc_type>_<title-slug>/    # gitignored
├── document_data.yaml                # source of truth (single evolving file)
├── review_history/
│   ├── red_team_report_vN.yaml       # machine, per-pass
│   ├── red_team_view_vN.md           # human view, derived from report_vN
│   ├── interview_log_vN.yaml         # machine, per-pass
│   ├── document_data_pre_vN.yaml     # byte-for-byte source snapshot BEFORE refine vN (RT#2)
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
- `ddo_system` (`associated_file` binding to reconcile — see header note).
- `validation_gate`, `ingest_helpers`, `path_deriver`, `build_orchestrator` — **reused, not modified** (new inbound edges only).

> `architecture.yml` is **not** edited by this SuperPRD. It is reconciled by `/hyper-audit` / `/hyper-discover` after the code lands.

### Execution Checklist (MiniPRDs)
- [ ] `spec/compiled/MiniPRD_ReviewEngine.md` — node `review_engine`
- [ ] `spec/compiled/MiniPRD_RefineEngine.md` — node `refine_engine`
- [ ] `spec/compiled/MiniPRD_RedTeamSkill.md` — node `skill_red_team`
- [ ] `spec/compiled/MiniPRD_InterviewSkill.md` — node `skill_interview`
- [ ] `spec/compiled/MiniPRD_RefineSkill.md` — node `skill_refine`
- [ ] `spec/compiled/MiniPRD_LoopTestSuite.md` — nodes `test_review_unit`, `test_refine_unit`, `test_loop_integration`

### Dependencies
- **Runtime:** no new runtime dependencies (`pyyaml`, `jinja2` already pinned in v0.0.1; view generation reuses Jinja2 or pure string building; serialization uses PyYAML `safe_dump(sort_keys=False, allow_unicode=True)`). **`ruamel.yaml` explicitly NOT adopted** — comment fidelity is delivered by the `pre_vN` snapshot.
- **Dev:** `pytest`, `ruff` (unchanged).
- **Lint contract:** unchanged from v0.0.1 (ruff line-length 100, Google docstrings, isort first-party `ddo`).
- **Tooling:** `uv` (hermetic). No system Typst, no Pandoc, no network.

---

## 6. Negative Constraints

- **DO NOT** hand-edit `document_data.yaml` as text in `ddo-refine`; mutate the parsed dict via structured patches only.
- **DO NOT** write `document_data.yaml` from any path other than `ddo.refine`'s validated pipeline; the in-memory `validate()` **and** the refine-only structural check must both pass **before** the write.
- **DO NOT** overwrite `document_data.yaml` without first writing the `review_history/document_data_pre_vN.yaml` snapshot.
- **DO NOT** serialize `document_data.yaml` with `sort_keys=True` (it reorders the source of truth); always `safe_dump(sort_keys=False, allow_unicode=True)`.
- **DO NOT** adopt `ruamel.yaml` or any new runtime dependency in v0.0.2; the `pre_vN` snapshot is the comment/format-fidelity mechanism.
- **DO NOT** parse the patch `target` path with `eval`/`exec` or any dynamic-attribute mechanism; use the hand-rolled parser only.
- **DO NOT** let `set` auto-vivify a missing path, change a node's type, or target a non-leaf/non-scalar node.
- **DO NOT** let `ddo.refine` call `build.py` directly; re-render only via the `ddo-render` skill, with flags from `meta.template`/`meta.output_formats`.
- **DO NOT** record a `render` outcome in `history.yaml` that was not observed from build.py's actual exit status.
- **DO NOT** mark a finding `applied:true` before `commit_refine` **and** the re-render succeed.
- **DO NOT** parse any Markdown view (`red_team_view_vN.md`, `history.md`) back into the data layer; views are read-only and code-generated, and read no wall-clock at generation time.
- **DO NOT** critique the PDF; the Red Team reads the MD/HTML render only.
- **DO NOT** let `ddo-red-team` inherit prior-phase conversation context; mandate a fresh context window at that boundary.
- **DO NOT** pick a `_vN` version by hand; derive it in code, and run `detect_incomplete_pass` before stacking a new pass.
- **DO NOT** treat `history.yaml` as authoritative for pass existence over the file tree.
- **DO NOT** silently fall back when `meta.persona` names a missing file; fail closed with a named error.
- **DO NOT** auto-advance past any phase gate (`[WAITING FOR USER REVIEW]` / `[WAITING FOR USER RESPONSE]`).
- **DO NOT** define `red_team_report`/`interview_log`/`history` schemas in `ddo/schemas/`; their contracts live in `ddo.review`.
- **DO NOT** add the `review_history/` path helper to `path_deriver`; it lives in `ddo.review` and calls `assert_within_documents`.
- **DO NOT** let any write escape `Documents/`; containment assertion is mandatory before every write.
- **DO NOT** assert content-equality on AI-generated critique or patch *content* in tests; test structure and safety only.
- **DO NOT** let an agent fabricate or promote the human-gated loop fixture; it requires `DDO_FIXTURE_SIGNOFF`.
- **DO NOT** add network access, new document types, structural patch ops, or the `ddo-run` composite in v0.0.2.

---

## 7. Risks & Mitigation

- **R1 — Patch grammar too narrow → forces forbidden hand-edits; too wide → corruption surface.** *Mitigation:* minimal grammar (`set`/`append_evidence`/`append_review_log`, leaf-scalar set); structural resolutions become `acknowledge`/`defer`; the constrained `set` + refine-only check + `validate()` gate cap blast radius.
- **R2 — A refine patch silently corrupts `document_data.yaml`.** *Mitigation:* pure `apply_patches` + constrained `set` + `refine_structural_check` + mandatory in-memory `validate()` before write + atomic write + the US-005 byte-unchanged-on-abort linchpin.
- **R3 — `_vN` derivation breaks under tampering / gaps / half-written passes.** *Mitigation:* file-tree-authoritative derivation + `detect_incomplete_pass` (refuse/resume); covered by unit tests.
- **R4 — Markdown view treated as a data source.** *Mitigation:* views code-generated only; negative constraint; no read path from views into the data layer.
- **R5 — Loop non-determinism leaks into the regression suite.** *Mitigation:* Candidate Artifact protocol — only structural/safety assertions automated; the end-to-end fixture is human-signed-off and skips until promoted.
- **R6 — Cross-contamination: critique biased by authoring context.** *Mitigation:* fresh-context firewall at the `ddo-red-team` boundary; the report YAML is the only hand-off.
- **R7 — Irreversible valid-but-wrong refine (gitignored + unversioned + `force=True`).** *Mitigation:* `document_data_pre_vN.yaml` byte-for-byte snapshot before every commit (M9).
- **R8 — YAML fidelity loss on round-trip (comment strip / key reorder).** *Mitigation:* `safe_dump(sort_keys=False, allow_unicode=True)` preserves key order; comments preserved in the `pre_vN` snapshot; `sort_keys=True` forbidden (M7).
- **R9 — Untruthful `history.render` / premature `applied`.** *Mitigation:* `render` recorded from build.py's actual exit after re-render; `applied` set only on commit+render success.
- **R10 — Torn pass / crash mid-sequence; `history.yaml` ↔ file-tree drift.** *Mitigation:* on-entry `detect_incomplete_pass`; file tree authoritative; phantom entries flagged.
- **R11 — Concurrent writers under a violated single-user invariant lose updates.** *Mitigation:* `force=False` fail-closed report/log writes; single-user documented as a relied-upon invariant; lose-update paths (`history.yaml` append, in-place flag update) named explicitly.

---

## 8. Success Metrics (each tied to a named test)

- **M1 (critique structure):** `red_team_report_vN.yaml` is structurally valid with all required finding fields and **fixed-enum** severities; malformed reports fail closed — `test_review_unit::test_report_contract`.
- **M2 (deterministic views & versioning):** `render_report_view` and `render_history_view` are byte-deterministic for a fixed report (no wall-clock at view-gen); `_vN` derivation + `detect_incomplete_pass` correct across contiguous/partial/torn sequences — `test_review_unit::test_view_and_version`.
- **M3 (refine safety linchpin):** a contract-breaking patch aborts before write and leaves `document_data.yaml` byte-identical — `test_refine_unit::test_bad_patch_aborts_unchanged`.
- **M4 (patch correctness):** `apply_patches` produces a `validate()`-clean dict for `set`/`append_evidence`/`append_review_log` on valid input — `test_refine_unit::test_apply_patches`.
- **M5 (end-to-end loop, human-gated):** a seeded-gap `document_data.yaml` + signed-off `interview_log` refines to a dict that is **sentinel-absent + `validate()`-clean** and **renders all 3 formats** (NOT semantic correctness); skips until `DDO_FIXTURE_SIGNOFF=1` — `test_loop_integration::test_gap_closing_pass`.
- **M6 (lint/suite):** `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .` all exit 0.
- **M7 (round-trip fidelity):** an identity refine (e.g. a no-op `append_review_log`) preserves key order via `sort_keys=False`, and the `document_data_pre_vN.yaml` snapshot is byte-identical to the original (comments recoverable) — `test_refine_unit::test_roundtrip_fidelity`.
- **M8 (valid-but-corrupting `set` rejected):** a `set` that changes a `content.sections[*].body` to a non-string, auto-vivifies a missing path, or replaces `content.sections` wholesale is rejected before write — `test_refine_unit::test_constrained_set_rejects_corruption`.
- **M9 (durability / rollback):** after any `commit_refine`, the prior `document_data.yaml` is recoverable byte-for-byte from `review_history/document_data_pre_vN.yaml` — `test_refine_unit::test_pre_refine_snapshot_rollback`.

---

## Appendix: Decisions Locked During `/hyper-resolve` (Red Team mediation)

| # | Decision |
|---|---|
| RT1 | Close the valid-but-gutted gap with **BOTH** a constrained `set` (leaf-scalar / no-auto-vivify / no-type-change) **and** a refine-only `refine_structural_check` — both in new code; `validation_gate` untouched (D5 preserved). |
| RT2 | **Pre-refine snapshot** `document_data_pre_vN.yaml` (byte-for-byte) before every commit → reversibility (R7/M9) + comment-fidelity net (R8). |
| RT3 | Serialize with **`safe_dump(sort_keys=False, allow_unicode=True)`**; no `ruamel`/new dep; `sort_keys=True` forbidden (R8/M7). |
| RT4 | **Minimal hand-rolled path DSL, never `eval`**: dotted keys + non-negative `[int]`, missing-path = hard error, no auto-vivify, `set` leaf-scalar-only; structural ops defer to v0.0.3. |
| RT5 | **Split the finding flag**: `decision_recorded` (interview) + `applied` (refine, only after commit+render); next pass filters on `applied`. `history.render` = build.py's actual exit, recorded after re-render (R9). |
| RT6 | **On-entry `detect_incomplete_pass`** (refuse/resume, no stacked `_vN`); **file tree authoritative**, `history.yaml` reconciled to it (R10). |
| RT7 | **Single-user/no-concurrency** = relied-upon invariant; `force=False` report/log fail-closed; `history.yaml` append + in-place flag update are documented lose-update paths; no locking. |
| RT8 | `review_history/` retention **unbounded by design** for v0.0.2. |
| RT9 | Persona-missing → hard named error; `severity` = fixed `Critical|Major|Minor` enum; `category` = free-text; no hard finding cap (soft warn > 100); `batch_size` default 2. |
| RT10 | Re-render flags **pinned to `meta.template` + `meta.output_formats`**, passed explicitly to `ddo-render`. |
| RT11 | `skip <n>` = **skip-and-its-dependents** (no self-inflicted dangling-ref abort). |
| RT12 | Pytest covers the deterministic `build.py` render path; the `ddo-refine → ddo-render` handoff verified in the human-gated fixture sign-off; coverage boundary documented (M5). |
| RT13 | **Doc fix:** `CLAUDE.md`'s `[REQUIRES USER INPUT:` wording is stale; the namespaced `[[DDO::REQUIRES_INPUT:` is authoritative — reconcile via `/hyper-document` (not a code change in this feature). |
| D1–D7 | Architect-interview decisions carried forward unchanged (manual loop; never hand-edit YAML; two modules with in-code contracts; full versioned history; reuse-not-modify blast radius; firewall only at red-team; novel-frontier testing). |
