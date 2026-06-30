"""Phase 2 — Interview: how the ddo-interview skill delegates to ddo.review.

Reference sketch for tutorial step 3. The agent runs a paced, batched Q&A; the
code owns validation, atomic writes, and the in-place flag update. The skill
reads the MACHINE-READABLE report (never the .md view) and sets ONLY
`decision_recorded` — `applied` is ddo-refine's job after the patch lands.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import yaml

from ddo.review import (
    current_version,
    mark_findings,
    validate_interview_log,
    write_interview_log,
)

SEVERITY_ORDER = {"Critical": 0, "Major": 1, "Minor": 2}


def run_interview(doc_dir: Path, version: int | None = None, batch_size: int = 2) -> Path:
    """Run the ddo-interview phase and write interview_log_vN.yaml."""
    version = version or current_version(doc_dir)
    if version is None:
        raise RuntimeError("No red_team_report found in review_history/.")

    report_path = doc_dir / "review_history" / f"red_team_report_v{version}.yaml"
    report = yaml.safe_load(report_path.read_text(encoding="utf-8"))

    # Filter applied:false, sort Critical -> Major -> Minor, present batch_size/turn.
    pending = [f for f in report["findings"] if not f.get("applied", False)]
    pending.sort(key=lambda f: SEVERITY_ORDER.get(f.get("severity", "Minor"), 2))
    # ... agent presents pending[:batch_size], halts at [WAITING FOR USER RESPONSE] ...

    # After the user responds, build the resolutions. acknowledge/dispute/defer
    # carry patch:null; revise -> set, add_evidence -> append (target: evidence_bank).
    log = {
        "meta": {"version": version, "timestamp": datetime.now(timezone.utc).isoformat()},
        "resolutions": [
            {
                "finding_id": "F-001",
                "decision": "revise",
                "detail": "Replace the discussion with the computed Z ranking.",
                "patch": {
                    "op": "set",
                    "target": "content.sections[3].body",  # leaf scalar (str -> str)
                    "value": "Recomputing Z ... PX-104 ranks third ...",
                    "depends_on": [],
                },
            },
            {
                "finding_id": "F-004",
                "decision": "add_evidence",
                "detail": "Attach the GC dataset.",
                "patch": {
                    "op": "append",
                    "target": "evidence_bank",
                    "value": {
                        "id": "gc_monomer_residue",
                        "type": "data",
                        "content": "GC-MS residual-monomer assay for PX-103.",
                        "source": "lab-repo/data/gc_px103.csv",
                    },
                    "depends_on": [],
                },
            },
            # F-002 / F-003 acknowledge (patch:null), F-005 defer (patch:null) ...
        ],
    }

    validate_interview_log(log)  # structural check (raises on bad shape)
    written = write_interview_log(doc_dir, log, version, force=True)  # atomic, contained

    # Mark ONLY decision_recorded — never `applied`.
    resolved_ids = [r["finding_id"] for r in log["resolutions"]]
    mark_findings(doc_dir, version, resolved_ids, field="decision_recorded")

    print(f"{written} written. [WAITING FOR USER RESPONSE]")
    return written
