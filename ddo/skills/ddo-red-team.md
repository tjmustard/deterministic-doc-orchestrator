# **Skill: ddo-red-team**

## **Description**

Adversarially critiques a rendered MD/HTML document against a chosen persona
lens and emits a machine-readable `red_team_report_vN.yaml` plus a
deterministic human-readable view (`red_team_view_vN.md`).  This is the
**Red Team** phase of the DDO v0.0.2 adversarial loop.

> **Fresh-context firewall:** You MUST run in a **fresh conversation context**
> that has not seen the authoring, ingest, or render phases.  The value of the
> critique depends on entering without inherited rationale.  The only hand-off
> from the prior phase is the path to the rendered MD/HTML file.

All structural mechanics (versioning, path derivation, atomic writes, view
generation) are delegated to `ddo.review`.  Never re-implement them here.

## **Inputs**

1. `render_path`: Path to the rendered **MD or HTML** file to critique (never
   the PDF — the Red Team reads the text/HTML layer only).
2. `doc_dir`: Path to the document's root directory (e.g.
   `Documents/2026.06.29_prd_my-title/`) — the `review_history/` subtree lives
   here.
3. `persona` (optional): Name of a persona file in `ddo/personas/` (e.g.
   `product_critic`).  If omitted and `meta.persona` is present in
   `document_data.yaml`, that value is used.  If neither is available, require
   explicit selection.

## **Invariants (read before acting)**

- **Fresh context mandatory.** Do not inherit prior-phase conversation history.
  The `red_team_report_vN.yaml` file is the only authorised hand-off.
- **MD/HTML only.** Read `render_path`.  Never load the PDF.
- **Zero hallucination.** Every finding must be grounded in content actually
  present in (or absent from) the rendered document.
- **Fixed severity enum.** Every finding severity must be `Critical`, `Major`,
  or `Minor`.  Do not invent a per-persona taxonomy.
- **Delegate all mechanics.** Report writing, `_vN` derivation, view generation,
  and torn-pass detection are owned by `ddo.review`.
- **Halt at the gate.** End at `[WAITING FOR USER REVIEW]` and instruct the
  user to open a fresh context before starting `ddo-interview`.

## **Execution Logic**

### 1. Torn-Pass Check

Before deriving a new version, call `detect_incomplete_pass` from `ddo.review`:

```python
from ddo.review import detect_incomplete_pass
torn = detect_incomplete_pass(doc_dir)
if torn:
    # Surface the reason and suggestion; do NOT stack a new vN
    ...
```

If a torn pass is detected, surface its `reason` and `suggestion` and halt.
Never auto-advance past this gate.

### 2. Derive the Version

```python
from ddo.review import report_version
version = report_version(doc_dir)  # max(existing N) + 1; 1 if none exist
```

### 3. Resolve the Persona

```python
import yaml
# Load document_data.yaml to read meta.persona if available
meta_persona = yaml.safe_load((doc_dir / "document_data.yaml").read_text())
                 .get("meta", {}).get("persona")
```

Resolution order:
1. Explicit `persona` argument → load `ddo/personas/<persona>.md`.
2. `meta.persona` from `document_data.yaml` → load `ddo/personas/<value>.md`.
3. Neither → prompt the user to select a persona explicitly.

**Hard failure:** if the resolved persona name points to a file that does not
exist, raise a named error:

```
Error: persona file 'ddo/personas/<name>.md' not found. Possible personas:
  - product_critic   (ddo/personas/product_critic.md)
  - scientific_reviewer (ddo/personas/scientific_reviewer.md)
```

Never silently fall back to a different persona.

**Hard failure (RT-05):** After loading the persona file, scan it for a
`## Attack Vectors` table.  If no such table is present, raise a named error
and halt — do NOT fall back to emitting free-text categories:

```
Error: persona file 'ddo/personas/<name>.md' has no '## Attack Vectors' table.
Red Team requires a structured AV table to enforce the AV-NN category contract.
Add an '## Attack Vectors' section to the persona before running Red Team.
```

**Echo AV table into report context:** Once the persona file is confirmed to
have a `## Attack Vectors` table, extract that table in full and embed it in
the report header comment block so that every `AV-NN: <name>` reference in the
findings is self-documenting for both AI agents and human auditors — without
requiring the reviewer to open the persona file:

```yaml
# --- Active Persona: <persona_name> ---
# Attack Vectors:
# <paste the full ## Attack Vectors table here, verbatim>
# ---------------------------------------
meta:
  version: <int N>
  persona: <persona_name>
  ...
```

### 4. Read the Render

Read the full text of `render_path`.  If the file is HTML, parse it for
text-layer content.  Do not load any external resources.

### 5. Perform the Adversarial Critique

Apply the persona's attack-vector taxonomy to the rendered document.  For each
finding, produce:

| Field | Type | Notes |
|---|---|---|
| `id` | `str` | Unique within this report (e.g. `F-001`) |
| `severity` | `Critical \| Major \| Minor` | **Fixed enum** — hard error if outside it |
| `category` | `str` | The active persona's exact `AV-NN: <name>` from its Attack Vectors table (free-text in the schema; consistency enforced cognitively). |
| `location` | `str` | Section title or quoted span |
| `description` | `str` | What is wrong or missing |
| `suggestion` | `str` | How to fix it |
| `decision_recorded` | `false` | Always `false` at emit time |
| `applied` | `false` | Always `false` at emit time |
| `resolution` | `null` | Always `null` at emit time |

If the total finding count exceeds 100, emit a soft warning (do not hard-fail):
> ⚠️ Warning: {N} findings generated. Consider splitting into priority tiers.

### 6. Emit the Report

Construct the full report dict per the data contract:

```yaml
meta:
  version: <int N>
  persona: <persona_name>
  document: <relative path from doc_dir to render_path>
  timestamp: <ISO-8601 UTC>
findings:
  - id: "F-001"
    severity: Critical
    category: "AV-01: missing_acceptance_criteria"
    location: "Section 2"
    description: "Claim X is unsubstantiated."
    suggestion: "Add evidence entry referencing source Y."
    decision_recorded: false
    applied: false
    resolution: null
  # ...
```

Then delegate persistence and view generation to `ddo.review`:

```python
from ddo.review import write_report
written = write_report(doc_dir, report, version, force=False)
# This also generates red_team_view_vN.md deterministically
```

### 7. Surface the Result

Report:
- `review_history/red_team_report_v{N}.yaml` — machine-readable, {count} findings
- `review_history/red_team_view_v{N}.md` — human-readable view (deterministic)
- Severity breakdown: Critical {C}, Major {M}, Minor {m}

## **Negative Constraints**

- **DO NOT** critique the PDF — read MD/HTML only.
- **DO NOT** inherit prior-phase conversation context.
- **DO NOT** invent per-persona severity labels — use only `Critical`, `Major`,
  `Minor`.
- **DO NOT** derive `_vN` by hand; always use `ddo.review.report_version`.
- **DO NOT** re-implement report writing or view generation — delegate to
  `ddo.review.write_report`.
- **DO NOT** silently fall back when `meta.persona` names a missing file.
- **DO NOT** set `decision_recorded`, `applied`, or `resolution` to anything
  other than `false`, `false`, `null` at emit time.
- **DO NOT** auto-advance past `[WAITING FOR USER REVIEW]`.
- **DO NOT** start a new pass if `detect_incomplete_pass` signals a torn prior
  pass — surface the issue and halt.

## **Post-Condition**

```
[WAITING FOR USER REVIEW]
```

Output the paths to the report and view files, the finding count and severity
breakdown, and the following instruction:

> The red team report has been written to `review_history/red_team_report_v{N}.yaml`.
> Please review `red_team_view_v{N}.md` for a human-readable summary.
>
> **Next step:** Open a **fresh conversation context**, then run `ddo-interview`
> to resolve findings.  The report YAML is the only authorised hand-off.
>
> `[WAITING FOR USER REVIEW]`
