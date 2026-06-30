# Closing the Loop: Red-Teaming & Refining a DDO Document (v0.0.2)

## Overview

DDO v0.0.1 gave you a *trustworthy* renderer: identical YAML + template always
produces identical output, and the renderer never adds a word the YAML didn't
contain. But a faithful render of a **flawed** document is still flawed. v0.0.2
adds the **adversarial loop** — three skills that critique a rendered document
against a domain persona, resolve the findings with you, and safely patch the
source-of-truth YAML, then re-render.

This tutorial walks the loop end-to-end on a real example: the **Biodegradable
Polyester Optimization Report**, critiqued by the `scientific_reviewer` persona.
You'll watch the loop surface a buried contradiction — *the report recommends a
candidate its own objective function ranks third* — capture the fix as
structured data, and fold it back into `document_data.yaml` without ever
hand-editing the YAML.

```
rendered MD/HTML ─▶ ddo-red-team ─▶ red_team_report_vN.yaml (+ view)
                 ─▶ ddo-interview ─▶ interview_log_vN.yaml   (decisions)
                 ─▶ ddo-refine    ─▶ snapshot ▶ validated patch ▶ document_data.yaml ▶ re-render
                 ─▶ [loop again, or finalize]
```

The single mutable state is `document_data.yaml`. Everything else — reports,
logs, views, snapshots — is a **derived working artifact**. Only `ddo-refine`,
through `ddo.refine`'s validated pipeline, is ever permitted to write the source
of truth.

## Prerequisites

- **A working DDO v0.0.1 install** — `uv`, the `ddo/` package (`ddo.ingest`,
  `ddo.paths`, `ddo.validation`, `build.py`), and the v0.0.2 modules `ddo.review`
  + `ddo.refine`.
- **The example document as a DDO source** — the polyester report ingested into
  a `scientific_report` `document_data.yaml` (provided in `input_files/`) living
  under a document directory. The folder name is auto-derived from `meta`
  (`<date>_<doc_type>_<slug>`, slug from `meta.title`):

  ```
  Documents/2026.06.29_scientific_report_copolyester-optimization/
  └── document_data.yaml
  ```

  > **Date gotcha:** `meta.date` must be **dotted** `YYYY.MM.DD` (e.g.
  > `2026.06.29`), *not* ISO hyphens — the validation gate rejects the hyphenated
  > form. The shipped schema's `[[DDO::REQUIRES_INPUT: ISO-8601]]` placeholder is
  > about *which calendar date*, not the separator.

- **A rendered Markdown artifact to critique** — produced by `ddo-render` (the
  Red Team reads MD/HTML, *never* the PDF):

  ```bash
  uv run ddo/build.py \
    --data     Documents/2026.06.29_scientific_report_copolyester-optimization/document_data.yaml \
    --template scientific_report --format md \
    --output   Documents/2026.06.29_scientific_report_copolyester-optimization/output/copolyester-optimization.md
  ```

- **The `scientific_reviewer` persona** — already shipped at
  `ddo/personas/scientific_reviewer.md`. No need to build one; v0.0.2 is the
  version that promotes it from "forward-compat, smoke-tested only" to an active
  input.
- **A way to open a fresh conversation context** — the Red Team phase has a
  mandatory firewall (below).

## Step-by-Step

### 1. Set the stage — the report as a DDO document

The loop mutates exactly one file: `document_data.yaml`. Before critiquing,
confirm the document renders cleanly so the Red Team reads a faithful surface:

```bash
uv run ddo/build.py --data <doc_dir>/document_data.yaml \
  --template scientific_report --format md \
  --output <doc_dir>/output/copolyester-optimization.md
```

The rendered `copolyester-optimization.md` is the **only** hand-off into the next
phase. Note its path — you'll pass it to `ddo-red-team` as `render_path`.

See `input_files/document_data.yaml` for the source and
`input_files/copolyester-optimization.md` for a representative render.

### 2. Phase 1 — Red Team (fresh context, `scientific_reviewer`)

> **Fresh-context firewall.** You **must** run `ddo-red-team` in a brand-new
> conversation that has not seen the authoring/ingest/render history. The
> critique's value depends on entering without inherited rationale. The rendered
> `.md` path is the only thing carried across.

Open a fresh context and invoke `ddo-red-team` with:

- `render_path` → `<doc_dir>/output/copolyester-optimization.md`
- `doc_dir` → `<doc_dir>`
- `persona` → resolved from `meta.persona` (`scientific_reviewer`); a
  missing/typo'd persona file is a **hard, named error**, never a silent fallback.

The skill delegates every mechanic to `ddo.review`: it runs
`detect_incomplete_pass(doc_dir)` first (refuses to stack a new pass on a torn
one), derives the version with `report_version(doc_dir)` (`max(existing N)+1`, or
`1`), then writes the report and its deterministic view via `write_report(...)`.
See `code_samples/red_team_call.py`.

Applying the persona's attack vectors to this report yields findings like:

| ID | Severity | Category | What the reviewer caught |
|----|----------|----------|--------------------------|
| F-001 | **Critical** | Overreaching Conclusions | The conclusion recommends **PX-104**, but recomputing the paper's own `Z = 0.3·S + 0.4·Y − 0.1·T − 0.2·E` ranks PX-104 **third** (45.96) behind PX-103 (51.12) and PX-105 (46.44). The conclusion is unsupported by the stated methodology. |
| F-002 | **Critical** | Methodological Vagueness | The toxicity term `−w_t·T` is **sign-inverted**: LD50 is *inversely* related to toxicity (higher LD50 = safer), yet the function penalizes high LD50, so it *maximizes* toxicity while claiming to minimize it. |
| F-003 | **Major** | Statistical Ambiguity | "Normalized weights" is asserted, but the raw variables are never normalized; solubility (12–88) dominates ecology (1.8–4.2), so the weighting is not actually balanced. |
| F-004 | **Major** | Unsupported Assertions | "Gas chromatography indicates… unreacted monomer residues" cites no entry in the `evidence_bank`. |
| F-005 | **Minor** | Missing Limitations | No limitations: replicate counts and LD50 confidence intervals for the murine assays are absent. |

The skill ends at the gate:

```
review_history/red_team_report_v1.yaml — 5 findings (Critical 2, Major 2, Minor 1)
review_history/red_team_view_v1.md     — human-readable, deterministic

[WAITING FOR USER REVIEW]
Next step: open a fresh context, then run ddo-interview.
```

Every finding lands as data with `decision_recorded: false`, `applied: false`,
`resolution: null`. The `_v1.md` view is generated from that stored data only —
no wall-clock read at view time, so it's byte-deterministic. See
`output_files/red_team_report_v1.yaml` and `output_files/red_team_view_v1.md`.

### 3. Phase 2 — Interview (paced, batched Q&A)

`ddo-interview` loads the **machine-readable** `red_team_report_v1.yaml` (never
the `.md` view), filters `applied:false`, sorts Critical → Major → Minor, and
presents `batch_size` findings at a time (default **2**). For each finding you
choose one of five decisions:

| Decision | Meaning | Patch op |
|----------|---------|----------|
| `revise` | Rewrite affected content | `set` (leaf-scalar) |
| `add_evidence` | Add an `evidence_bank` entry | `append` (v0.0.3+, see below) |
| `acknowledge` | Accept finding, log it, no body change | `null` → use `append` to `meta.review_log` explicitly (see below) |
| `dispute` | Disagree, with reason | `null` |
| `defer` | Revisit in a later pass | `null` |

**v0.0.3 patch ops — required and forbidden fields:**

| Op | Required fields | Forbidden fields | Notes |
|----|----------------|-----------------|-------|
| `set` | `target` (leaf-scalar path), `value` | `at` | New value must match existing scalar type |
| `append` | `target` (list path, no `[N]` suffix), `value` | `at` | Never auto-vivifies a missing list |
| `delete` | `target` (must end in `[N]`) | `value`, `at` | Triggers `DanglingRefError` if the entry's ID is still referenced |
| `insert` | `target` (list path, no `[N]` suffix), `at` (non-neg int, not bool), `value` | — | `at > len(list)` is a hard error |
| `append_evidence` *(deprecated — removed in v0.0.4)* | `value` | — | Migrate: `{op: append, target: "evidence_bank", value: {...}}` |
| `append_review_log` *(deprecated — removed in v0.0.4)* | `value` | — | Migrate: `{op: append, target: "meta.review_log", value: {...}}` |

A representative resolution set for the findings above:

```yaml
resolutions:
  - finding_id: F-001          # conclusion contradicts its own Z
    decision: revise
    detail: "Correct the recommendation to match the computed Z ranking."
    patch:
      op: set
      target: content.sections[3].body   # Discussion — leaf-scalar string, str→str
      value: "Recomputing Z on the Phase II data ranks PX-103 (51.12) first… [corrected text]"
  - finding_id: F-002          # LD50 sign inversion — deeper model rework
    decision: acknowledge
    detail: "Real flaw; objective-function re-derivation deferred to a model revision. Logged."
    patch: null                # acknowledge carries no body patch; refine appends meta.review_log
  - finding_id: F-004          # uncited GC claim
    decision: add_evidence
    detail: "Attach the GC dataset backing the monomer-residue claim."
    patch:
      op: append
      target: evidence_bank
      value:
        id: gc_monomer_residue
        type: data
        content: "GC-MS residual-monomer assay, PX-103"
        source: "lab-repo/data/gc_px103.csv"
  - finding_id: F-005
    decision: defer
    patch: null
```

(`F-003` resolves the same way as `F-002` — `acknowledge`, logged to
`meta.review_log`, normalization rework deferred. See the full
`output_files/interview_log_v1.yaml`.)

On commit, `ddo-interview` writes `interview_log_v1.yaml` via
`write_interview_log(...)` and calls
`mark_findings(doc_dir, version, ids, field="decision_recorded")`. It **never**
sets `applied` — that's `ddo-refine`'s job after the patch actually lands. It
halts at `[WAITING FOR USER RESPONSE]` after each batch and never auto-advances.
See `code_samples/interview_call.py`.

> **Pre-validation:** `validate_interview_log()` (in `ddo/review.py`) enforces
> per-op field rules — required and forbidden fields per op — before
> `apply_patches` is called. Malformed logs (e.g. `delete` with a `value` field,
> or `insert` without `at`) are caught at validation, not during patching.

### 4. Phase 3 — Refine (snapshot → validate → diff → commit → re-render)

`ddo-refine` is the highest-risk path — the only writer of `document_data.yaml`
— so every guarantee lives in `ddo.refine` code, not the skill's judgment. The
sequence (`code_samples/refine_call.py`):

1. **Torn-pass check** — `detect_incomplete_pass(doc_dir)`; refuse/resume rather
   than stack a pass.
2. **Snapshot first** — `snapshot_source(data_path, doc_dir, version)` copies
   `document_data.yaml` byte-for-byte to
   `review_history/document_data_pre_v1.yaml`. `force=False`, so a
   double-snapshot fails closed. This is your recovery point.
3. **Apply patches (pure, in-memory)** — `apply_patches(data, log)` works on a
   deep copy. `set` is **leaf-scalar only**: the path is parsed by a hand-rolled
   parser (`parse_path`, *never* `eval`), missing paths are hard errors,
   auto-vivify is forbidden, and the new value must match the existing scalar's
   type (str→str ok; str→dict rejected). Path keys must match
   `[A-Za-z_][A-Za-z0-9_]*`; indices must be plain non-negative integers —
   `[-1]`, `[*]`, and hex forms all raise `ValueError`.

   > **DanglingRefError:** `delete evidence_bank[N]` first runs
   > `_dangling_ref_check()`. If the deleted entry's `id` is still referenced in
   > any `content.sections[*].evidence[]`, a `DanglingRefError` is raised with a
   > `.paths` list of every referencing location (e.g.
   > `content.sections[2].evidence[0]`). The entire batch aborts;
   > `document_data.yaml` is byte-identical. Resolution: issue `set` patches to
   > remove the ID from all referencing sections first, then re-run with the
   > `delete` patch.

   > **Warning — index shift:** When multiple `delete` or `insert` ops target the
   > same list in a single interview log, indices shift as patches apply in order.
   > A `delete [2]` followed by another `delete [2]` removes what was originally
   > index 3. Plan index values to account for prior ops in the same batch, or
   > split into separate passes.
4. **Validate twice, in-memory** — `refine_structural_check(patched)` (sections
   stay a list, every body stays a non-empty string) **and** the importable
   `validate(patched)` (the v0.0.1 minimal contract: presence/uniqueness/no
   sentinel). Either failure aborts with **zero** writes; the YAML stays
   byte-identical.
5. **Before/After diff (HITL gate)** — a unified text diff of
   `safe_dump(sort_keys=False)` blocks, shown for approval. `approve all` or
   `skip <n>`; **`skip <n>` cascades to dependents** (via `depends_on`) so refine
   never self-inflicts a dangling reference. The diff is human-only and never
   re-parsed.
6. **Commit** — `commit_refine(data_path, patched)` re-runs both checks
   (defense-in-depth), serializes with
   `safe_dump(sort_keys=False, allow_unicode=True)` (preserves key order;
   `sort_keys=True` is forbidden), and writes atomically.
7. **Re-render via `ddo-render`** — flags derived from `meta.template` +
   `meta.output_formats`. `ddo.refine` **never** calls `build.py` directly.
8. **Audit reconcile — only on render success** —
   `mark_findings(..., field="applied")`, then `append_history(...)`. The
   `render` outcome recorded is build.py's *actual* exit status, never an agent
   claim. `acknowledge`/`dispute` decisions append to `meta.review_log`. If the
   render fails, nothing is marked `applied` and no history record is written.

```
[WAITING FOR USER RESPONSE]   ← Before/After diff approval

Refine v1 complete.
- document_data.yaml updated (2 patches applied: F-001 revise, F-004 add_evidence).
- review_history/document_data_pre_v1.yaml — pre-refine snapshot preserved.
- Re-render: [pdf, html, md] — ok.
- 2 finding(s) marked applied:true.
- review_history/history.yaml updated.
[WAITING FOR USER REVIEW]
```

### 5. Loop again, or finalize

After the pass: `F-001` and `F-004` are `applied:true`; `F-002` and `F-003` are
`decision_recorded:true` but `applied:false` (acknowledged, now visible in
`meta.review_log`); `F-005` is deferred. Run another pass — open a **fresh
context** for `ddo-red-team` again — until the document stabilizes, then declare
it final. Because `report_version` is `max(N)+1`, the next pass is `v2` and the
whole history accretes under `review_history/`.

## Expected Output

After one full pass, the document directory looks like:

```
Documents/2026.06.29_scientific_report_copolyester-optimization/
├── document_data.yaml                    # SOURCE OF TRUTH — patched, re-rendered
├── review_history/
│   ├── red_team_report_v1.yaml           # machine: 5 findings, flags updated
│   ├── red_team_view_v1.md               # human view (deterministic)
│   ├── interview_log_v1.yaml             # 5 resolutions (revise/add_evidence/acknowledge×2/defer)
│   ├── document_data_pre_v1.yaml         # byte-for-byte pre-refine snapshot (recovery)
│   ├── history.yaml                      # one pass record (machine)
│   └── history.md                        # derived read-only summary
└── output/
    └── copolyester-optimization.{pdf,html,md}   # re-rendered from patched YAML
```

`history.yaml` after the pass (see `output_files/history.yaml`):

```yaml
passes:
  - version: 1
    timestamp: 2026-06-29T20:15:00Z
    persona: scientific_reviewer
    findings: {critical: 2, major: 2, minor: 1}
    resolutions: {revise: 1, add_evidence: 1, acknowledge: 2, dispute: 0, defer: 1}
    applied: 2
    render: ok
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `persona file 'ddo/personas/X.md' not found` | `meta.persona` typo or missing file | Fix `meta.persona`; the skill **never** silently falls back. |
| Red Team "sees" the authoring rationale and pulls punches | Ran in the same context as ingest/render | Start a **fresh** conversation; pass only the rendered `.md` path. |
| `red_team_report_vN.yaml exists but interview_log_vN.yaml is missing` | `detect_incomplete_pass` found a torn pass | Resume `ddo-interview` for `vN`, or remove the partial report to restart. |
| `set target ... is not a leaf scalar` / `would change type` | Patch tried a structural edit (e.g. `body`→dict, or replacing `content.sections`) | Use a leaf-scalar `set` for text edits; for structural changes use `append`, `insert`, or `delete` (available in v0.0.3+). |
| `DanglingRefError: dangling references found: [...]` | `delete evidence_bank[N]` while the entry's `id` is still in a section's `evidence` list | Issue `set` patches to remove the ID from all referencing sections (listed in the error's `.paths`), then retry the `delete`. |
| `ValueError: invalid bracket expression` / `unexpected character` | Path key contains characters outside `[A-Za-z_][A-Za-z0-9_]*`, or index is not a plain non-negative integer (e.g. `[-1]`, `[*]`) | Use only alphanumeric/underscore keys and non-negative plain integers in paths. |
| `ReportValidationError: patch.at: required for op 'insert'` | `insert` op is missing the `at` field | Add `at: <non-negative integer>` to the patch. |
| `ReportValidationError: patch.value: field not allowed for op 'delete'` | `delete` op includes a `value` key | Remove the `value` field from the `delete` patch. |
| Refine aborts citing a field/ID and nothing is written | `validate()` or `refine_structural_check` rejected the patched dict | Read the named error; `document_data.yaml` is byte-identical — fix the patch in the interview log and retry. |
| `OverwriteError` on snapshot | `document_data_pre_vN.yaml` already exists | A prior pass left a snapshot; you're likely resuming a torn pass — reconcile `review_history/` first. |
| `meta.date: must match dotted YYYY.MM.DD` | Used ISO hyphens (`2026-06-29`) | Use dots: `2026.06.29`. |
| `skip <n>` left a dangling reference | A depended-upon patch was skipped without its dependents | The skill cascades skips via `depends_on`; ensure dependent patches declare it. |
| Keys reordered in `document_data.yaml` | Serialized with `sort_keys=True` | Always `safe_dump(sort_keys=False, allow_unicode=True)`; exact original survives in the `pre_vN` snapshot. |

## Related

- **Skills:** `ddo/skills/ddo-red-team.md`, `ddo/skills/ddo-interview.md`,
  `ddo/skills/ddo-refine.md`
- **Modules:** `ddo/review.py` (critique/interview data layer), `ddo/refine.py`
  (mutation layer)
- **Spec:** `spec/compiled/SuperPRD_v0.0.2_AdversarialLoop.md` (Red Team
  resolutions RT1–RT13)
- **Persona:** `ddo/personas/scientific_reviewer.md`
- **Foundation:** the v0.0.1 deterministic rendering backbone (`ddo-ingest`,
  `ddo-render`)
- **Architecture tour:** `architecture_evolution/pipeline_v0.0.1_to_v0.0.2.md`
