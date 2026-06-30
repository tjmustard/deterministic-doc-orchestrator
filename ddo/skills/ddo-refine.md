# **Skill: ddo-refine**

## **Description**

Applies validated structured patches from an `interview_log_vN.yaml` to
`document_data.yaml`, presents a Before/After diff for human approval, commits
the change atomically, and re-renders via `ddo-render`.  This is the **Refine**
phase of the DDO v0.0.2 adversarial loop.

All safety-critical mechanics are delegated to `ddo.refine` and `ddo.review`.
This skill performs the cognitive orchestration; the code enforces the
invariants.

## **Inputs**

1. `doc_dir`: Path to the document's root directory (e.g.
   `Documents/2026.06.29_prd_my-title/`) — `review_history/` and
   `document_data.yaml` live here.
2. `version` (optional): The `_vN` version number to refine.  If omitted, uses
   `ddo.review.current_version(doc_dir)`.

## **Invariants (read before acting)**

- **YAML is the source of truth.** Never hand-edit `document_data.yaml` as
  text.  Mutate the parsed dict via `ddo.refine.apply_patches` only.
- **Snapshot before write.** `ddo.refine.snapshot_source` must succeed before
  any mutation begins.
- **Validate before write.** Both `refine_structural_check` and `validate()` run
  in-memory on the patched dict.  A failure aborts the write — `document_data.yaml`
  is left byte-identical.
- **Re-render via `ddo-render`, not `build.py` directly.**  Flags are derived
  from `meta.template` + `meta.output_formats`.
- **`applied` and history ONLY after render success.**  Never mark a finding
  `applied:true` or append a history record before `commit_refine` **and**
  `ddo-render` both succeed.
- **HITL gate.** The Before/After diff must be approved by the user before any
  write.  Never auto-advance.

## **Execution Logic**

### 1. Torn-Pass Check

```python
from ddo.review import detect_incomplete_pass
torn = detect_incomplete_pass(doc_dir)
if torn:
    # Surface reason + suggestion; halt.
    ...
```

### 2. Load Inputs

```python
import yaml
from ddo.review import current_version

version = version or current_version(doc_dir)
if version is None:
    raise RuntimeError("No red_team_report found in review_history/.")

data_path = doc_dir / "document_data.yaml"
data = yaml.safe_load(data_path.read_text(encoding="utf-8"))

log_path = doc_dir / "review_history" / f"interview_log_v{version}.yaml"
log = yaml.safe_load(log_path.read_text(encoding="utf-8"))
```

Filter only resolutions that have a non-null patch and whose finding is not
already `applied`:

```python
# Load the report to check applied status
report_path = doc_dir / "review_history" / f"red_team_report_v{version}.yaml"
report = yaml.safe_load(report_path.read_text(encoding="utf-8"))
applied_ids = {f["id"] for f in report["findings"] if f.get("applied")}

# Only process resolutions with a patch for unapplied findings
active_resolutions = [
    r for r in log["resolutions"]
    if r.get("patch") is not None and r["finding_id"] not in applied_ids
]
```

### 3. Snapshot the Source

Before any mutation:

```python
from ddo.refine import snapshot_source
snap = snapshot_source(data_path, doc_dir, version)
# snap == review_history/document_data_pre_vN.yaml (byte-for-byte copy)
```

If this fails (e.g. the snapshot already exists), halt and surface the error.

### 4. Apply Patches (in-memory)

Handle `skip_and_dependents` for any patch whose `depends_on` patches were
skipped by the user:

```python
from ddo.refine import apply_patches

# Build a filtered log with only the approved resolutions
# (exclude any skipped by the user's 'skip <n>' decision)
filtered_log = {"meta": log["meta"], "resolutions": active_resolutions}
patched = apply_patches(data, filtered_log)
```

If `apply_patches` raises, abort: surface the precise error.
`document_data.yaml` has not been touched (the snapshot exists for recovery).

### 5. Validate In-Memory

```python
from ddo.refine import refine_structural_check
from ddo.validation import validate

try:
    refine_structural_check(patched)
    validate(patched)
except (ValueError, Exception) as exc:
    # Abort: surface the error, write nothing.
    ...
```

### 6. Generate and Present Before/After Diff

```python
import yaml
import difflib

before_text = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
after_text  = yaml.safe_dump(patched, sort_keys=False, allow_unicode=True)

diff = "\n".join(difflib.unified_diff(
    before_text.splitlines(),
    after_text.splitlines(),
    fromfile="document_data.yaml (before)",
    tofile="document_data.yaml (after)",
    lineterm="",
))
```

Present the diff to the user (human-only; never re-parse it):

```
--- Before/After Diff ---
{diff}
-------------------------

Approve and commit? Options:
  approve all   — apply all {N} patches
  skip <n>      — skip patch n (and any patches that depend on it)
```

**Halt here:**

```
[WAITING FOR USER RESPONSE]
```

### 7. Handle skip-and-dependents

If the user types `skip <n>`, identify all patches with `depends_on` referencing
index `n` and cascade the skip to them.  Surface a clear notice:

```
Skipping patch {n} and its dependents ({ids}).
```

Re-run `apply_patches` on the filtered (approved-only) set.

### 8. Commit the Refine

```python
from ddo.refine import commit_refine

committed = commit_refine(data_path, patched, force=True)
```

`commit_refine` re-runs `refine_structural_check` + `validate()` internally
before writing (defense-in-depth).  If it raises, abort.

### 9. Re-render via ddo-render

Derive render flags from `document_data.yaml`'s `meta` block:

```python
import yaml
meta = yaml.safe_load(committed.read_text(encoding="utf-8"))["meta"]
template  = meta["template"]
formats   = meta["output_formats"]
```

Invoke the **`ddo-render` skill** with these flags.  Do NOT call `build.py`
directly.  Capture the exit status reported by `ddo-render`.

```
Invoking ddo-render:
  --template {template}
  --format   {formats}
  --data     {data_path}
```

### 10. Audit Reconcile (on render success only)

Only after `ddo-render` reports a successful exit status:

```python
from ddo.review import mark_findings, append_history

# Mark applied patches' findings as applied
applied_ids = [r["finding_id"] for r in active_approved_resolutions]
mark_findings(doc_dir, version, applied_ids, field="applied")

# Route acknowledge/dispute to meta.review_log (via apply_patches on a
# single-entry log or direct meta manipulation — handled by the agent)

# Append history record
entry = {
    "version": version,
    "timestamp": "<ISO-8601 UTC now>",
    "persona": report["meta"]["persona"],
    "findings": {
        "critical": sum(1 for f in report["findings"] if f["severity"] == "Critical"),
        "major":    sum(1 for f in report["findings"] if f["severity"] == "Major"),
        "minor":    sum(1 for f in report["findings"] if f["severity"] == "Minor"),
    },
    "resolutions": {
        decision: sum(1 for r in log["resolutions"] if r["decision"] == decision)
        for decision in ("revise", "add_evidence", "acknowledge", "dispute", "defer")
    },
    "applied": len(applied_ids),
    "render": "ok",   # or "failed" — from build.py's actual exit status via ddo-render
}
append_history(doc_dir, entry)
```

If the render **failed**, do NOT mark findings `applied` and do NOT append a
history record.  Surface the error and halt.

## **Negative Constraints**

- **DO NOT** call `build.py` directly — re-render only via the `ddo-render` skill.
- **DO NOT** mark any finding `applied:true` or append a history record before
  `commit_refine` AND the re-render both succeed.
- **DO NOT** record a `render` outcome not observed from build.py's actual exit
  status surfaced by `ddo-render`.
- **DO NOT** commit before `snapshot_source` has completed successfully.
- **DO NOT** re-parse the Before/After diff or any Markdown view back into data.
- **DO NOT** hand-pick re-render flags — derive them from `meta.template` and
  `meta.output_formats`.
- **DO NOT** let a `skip` of a depended-upon patch proceed without cascading the
  skip to dependent patches (no self-inflicted dangling-ref abort).
- **DO NOT** serialize `document_data.yaml` with `sort_keys=True`.
- **DO NOT** write `document_data.yaml` from anywhere other than `commit_refine`.
- **DO NOT** auto-advance past any `[WAITING FOR USER RESPONSE]` gate.

## **Post-Condition**

On successful commit + re-render:

> Refine v{N} complete.
> - `document_data.yaml` updated ({N} patches applied).
> - `review_history/document_data_pre_v{N}.yaml` — pre-refine snapshot preserved.
> - Re-render: {formats} — **ok** / **failed**.
> - {applied_count} finding(s) marked `applied:true`.
> - `review_history/history.yaml` updated.
>
> Run `ddo-red-team` in a **fresh context** for another pass, or declare the
> document final.
>
> `[WAITING FOR USER REVIEW]`
