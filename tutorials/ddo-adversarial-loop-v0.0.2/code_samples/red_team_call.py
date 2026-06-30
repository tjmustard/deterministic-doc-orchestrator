"""Phase 1 — Red Team: how the ddo-red-team skill delegates to ddo.review.

Reference sketch for tutorial step 2. The *cognitive* work (the actual critique)
is performed by the agent in a FRESH conversation context; every deterministic
mechanic below — torn-pass detection, version derivation, atomic writes, and the
deterministic view — is owned by ddo.review and must never be re-implemented.

This is illustrative, not a runnable CLI: the `findings` list is produced by the
agent applying the persona's attack vectors to the rendered Markdown.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import yaml

from ddo.review import detect_incomplete_pass, report_version, write_report


def run_red_team(doc_dir: Path, render_path: Path, persona: str | None = None) -> Path:
    """Run the ddo-red-team phase and write red_team_report_vN.yaml + view."""
    # 1. Torn-pass check — refuse to stack a new pass on an incomplete one.
    torn = detect_incomplete_pass(doc_dir)
    if torn:
        raise SystemExit(f"Torn pass v{torn['version']}: {torn['reason']}\n{torn['suggestion']}")

    # 2. Derive the version in code (max(existing N) + 1; 1 if none).
    version = report_version(doc_dir)

    # 3. Resolve the persona: explicit arg -> meta.persona -> require selection.
    #    A named-but-missing persona file is a HARD error (no silent fallback).
    meta = yaml.safe_load((doc_dir / "document_data.yaml").read_text(encoding="utf-8"))["meta"]
    persona = persona or meta.get("persona")
    if persona is None:
        raise SystemExit("No persona: pass one explicitly or set meta.persona.")
    persona_file = Path("ddo/personas") / f"{persona}.md"
    if not persona_file.is_file():
        raise SystemExit(f"persona file '{persona_file}' not found.")

    # 4. The agent reads render_path (MD/HTML only — never the PDF) and produces
    #    findings. Severities are the FIXED enum Critical|Major|Minor.
    findings = [
        {
            "id": "F-001",
            "severity": "Critical",
            "category": "Overreaching Conclusions",
            "location": "6. Conclusion",
            "description": "Conclusion recommends PX-104, but the paper's own Z ranks it third.",
            "suggestion": "Tabulate Z for all candidates and recommend the true maximum.",
            "decision_recorded": False,  # always False at emit time
            "applied": False,  # always False at emit time
            "resolution": None,  # always None at emit time
        },
        # ... F-002 .. F-005
    ]

    report = {
        "meta": {
            "version": version,
            "persona": persona,
            "document": str(render_path.relative_to(doc_dir)),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "findings": findings,
    }

    # 5. Delegate persistence + deterministic view generation. force=False so a
    #    concurrent writer fails closed rather than clobbering (single-user
    #    invariant). Writes red_team_report_vN.yaml AND red_team_view_vN.md.
    written = write_report(doc_dir, report, version, force=False)

    # 6. Halt at the gate; instruct the user to open a FRESH context for interview.
    print(f"{written} written. [WAITING FOR USER REVIEW]")
    return written
