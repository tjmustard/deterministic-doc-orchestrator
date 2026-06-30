# **Skill: ddo-interview**

## **Description**

Resolves red-team findings into structured, machine-readable resolutions via a
paced, batched Q&A loop.  This is the **Interview** phase of the DDO v0.0.2
adversarial loop.

Each resolution is persisted atomically to `interview_log_vN.yaml` via
`ddo.review`.  The skill marks resolved findings `decision_recorded:true` in the
report (never `applied` — that is `ddo-refine`'s job after the patch lands).

## **Inputs**

1. `doc_dir`: Path to the document's root directory (e.g.
   `Documents/2026.06.29_prd_my-title/`) — `review_history/` lives here.
2. `version` (optional): The `_vN` version number to operate on.  If omitted,
   uses `ddo.review.current_version(doc_dir)` (the highest existing report
   version).
3. `batch_size` (optional): Number of findings to present per turn.  Default:
   **2**.

## **Invariants (read before acting)**

- **Load the machine-readable report, not the view.** Read
  `red_team_report_vN.yaml` directly.  Never parse `red_team_view_vN.md`.
- **Filter `applied:false`.** Only unresolved findings are presented.
- **Sort Critical → Major → Minor** within each batch.
- **Delegate all writes to `ddo.review`.** Never write YAML directly.
- **`decision_recorded` only.** On commit, mark only `decision_recorded:true`
  via `ddo.review.mark_findings(..., field="decision_recorded")`.  Never touch
  `applied`.
- **Halt at the gate.** End at `[WAITING FOR USER RESPONSE]` after each batch.
  Never auto-advance.

## **Execution Logic**

### 1. Load and Filter

```python
import yaml
from ddo.review import current_version

version = version or current_version(doc_dir)
if version is None:
    raise RuntimeError("No red_team_report found in review_history/.")

report_path = doc_dir / "review_history" / f"red_team_report_v{version}.yaml"
report = yaml.safe_load(report_path.read_text(encoding="utf-8"))
```

Filter `applied:false` and sort:

```python
SEVERITY_ORDER = {"Critical": 0, "Major": 1, "Minor": 2}

pending = [
    f for f in report["findings"]
    if not f.get("applied", False)
]
pending.sort(key=lambda f: SEVERITY_ORDER.get(f.get("severity", "Minor"), 2))
```

### 2. Present Batch

Present `batch_size` findings (default 2) per turn.  For each finding, show:

```
Finding {id} [{severity}] — {category}
Location: {location}
Description: {description}
Suggestion: {suggestion}

Resolution options:
  revise         — rewrite the affected content (provide a patch)
  add_evidence   — add a new evidence entry (provide the entry + link patch)
  acknowledge    — accept the finding without changing the document
  dispute        — disagree with the finding (provide reason)
  defer          — skip for now; will be revisited in a later pass

Decision for {id}: ___
Detail (free text): ___
Patch (if revise/add_evidence — see below, else null): ___
```

**Patch shape** (for `revise` or `add_evidence`):

```yaml
patch:
  op: set | append | delete | insert
  target: <path DSL, e.g. content.sections[2].body>   # set: leaf-scalar only
  value: <new scalar | evidence entry | review-log record>
  depends_on: [<patch index>, ...]   # optional; drives skip-and-dependents
```

For `acknowledge` / `dispute` / `defer`, set `patch: null`.

Halt after presenting the batch:

```
[WAITING FOR USER RESPONSE]
```

### 3. Record Resolutions

After the user responds, build the `interview_log_vN.yaml` or extend the
existing one:

```yaml
meta:
  version: <N>
  timestamp: <ISO-8601 UTC>
resolutions:
  - finding_id: "F-001"
    decision: revise
    detail: "Clarify claim with citation from source."
    patch:
      op: set
      target: content.sections[1].body
      value: "Revised body text here."
      depends_on: []
  - finding_id: "F-002"
    decision: acknowledge
    detail: "This is intentional scope exclusion."
    patch: null
```

Persist via `ddo.review`:

```python
from ddo.review import write_interview_log, validate_interview_log

validate_interview_log(log)                  # structural check
write_interview_log(doc_dir, log, version,   # atomic, contained
                    force=True)              # force=True since we may append
```

Then mark the resolved findings in the report:

```python
from ddo.review import mark_findings

resolved_ids = [r["finding_id"] for r in batch_resolutions]
mark_findings(doc_dir, version, resolved_ids, field="decision_recorded")
```

**Do NOT set `applied`.** That field is set by `ddo-refine` only after the patch
is successfully committed and the document re-rendered.

### 4. Continue or Conclude

If pending findings remain after the batch, inform the user and halt again:

```
{remaining} findings remain. Continuing...
[WAITING FOR USER RESPONSE]
```

When all findings have been addressed (or the user explicitly stops), surface
the summary:

```
Interview complete for v{N}.
- Resolutions recorded: {count}
  revise: {n}  add_evidence: {n}  acknowledge: {n}  dispute: {n}  defer: {n}
- interview_log_v{N}.yaml written to review_history/

Next step: Run ddo-refine (same context is fine).
```

## Structural Patch Syntax (v0.0.3+)

Three new generic operations are available for structural mutations. Always use `target:` as the field name (not `path:`).

### Path Grammar Rules

| Segment type | Syntax | Example |
|---|---|---|
| Dict key | `[A-Za-z_][A-Za-z0-9_]*` | `evidence_bank`, `meta` |
| List index | `[N]` (non-negative digits only) | `[0]`, `[2]` |
| Dotted chain | `key.key[N].key` | `content.sections[1].body` |

Negative indices (`[-1]`), slices (`[*]`), and hex (`[0x1]`) are rejected. Index brackets must contain only `\d+`.

### append — add element to end of list

```yaml
patch:
  op: append
  target: evidence_bank        # must resolve to an existing list; must NOT end in [N]
  value:
    id: "ev_new_001"
    type: "reference"
    content: "..."
    source: "..."
```

### delete — remove element at index

> **Dangling-ref advisory:** Before issuing `delete evidence_bank[N]`, search `content.sections[*].evidence[]` for the entry's `id`. If found, first issue `set` patches to update or remove each referencing path, then issue the delete as a later patch entry.

```yaml
patch:
  op: delete
  target: evidence_bank[0]     # must end in [N]; no value field allowed
```

### insert — insert element at position

The `at` field is required and must be a non-negative integer (`isinstance(at, int) and not isinstance(at, bool) and at >= 0`). `at == len(list)` is valid (equivalent to append). `at > len(list)` is a hard error.

```yaml
patch:
  op: insert
  target: content.sections     # must resolve to an existing list; must NOT end in [N]
  at: 0                        # integer >= 0; True/False/2.0 are rejected
  value:
    id: "new_section"
    title: "New Section"
    body: "..."
    claims: []
    evidence: []
```

### Sequential-index warning

**Avoid generating multiple index-bearing patches targeting the same parent list in one batch.** An earlier `insert` or `delete` on a list shifts the indices of all later elements — subsequent patches targeting index `N` on the same list in the same batch will operate on a different element than intended. If sequential index-bearing ops on the same list are unavoidable, list them explicitly in correct sequential order and document the expected index values at each step.

### AI candidate value display

The `value` field in an `append`, `delete`, or `insert` patch is a Candidate Output. Display the full `value` dict in the decision prompt **before** writing it to the interview log, so the human can verify the proposed mutation. The Before/After diff in `ddo-refine` is the human authorization gate — the interview prompt is a proposal only.

## **Negative Constraints**

- **DO NOT** set `applied` — only `ddo-refine` may do that after a successful
  commit + render.
- **DO NOT** write `document_data.yaml` — this skill writes the interview log
  and updates report flags only.
- **DO NOT** parse `red_team_view_vN.md` as input — read the machine-readable
  report YAML.
- **DO NOT** re-implement log writing or flag updates — delegate to `ddo.review`.
- **DO NOT** present more than `batch_size` findings per turn.
- **DO NOT** auto-advance past `[WAITING FOR USER RESPONSE]`.
- **DO NOT** mark `decision_recorded` for a finding the user has not yet
  responded to.

## **Post-Condition**

When all addressed findings are recorded and `mark_findings` has been called:

```
[WAITING FOR USER RESPONSE]
```

Or, when the full loop is complete:

> Interview log written to `review_history/interview_log_v{N}.yaml`.
> Findings marked `decision_recorded:true`: {ids}.
>
> **Next step:** Run `ddo-refine` in the same (or a new) context to apply
> approved patches.
