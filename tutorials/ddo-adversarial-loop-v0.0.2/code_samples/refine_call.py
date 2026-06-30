"""Phase 3 — Refine: how the ddo-refine skill delegates to ddo.refine / ddo.review.

Reference sketch for tutorial step 4. This is the highest-risk path — the ONLY
permitted writer of document_data.yaml — so every guarantee lives in code:
snapshot-before-write, pure in-memory patching, the constrained `set`, the
double validate-before-write, and the atomic commit. The agent only orchestrates
the HITL diff gate and the ddo-render handoff.
"""

from __future__ import annotations

import difflib
from datetime import datetime, timezone
from pathlib import Path

import yaml

from ddo.refine import apply_patches, commit_refine, refine_structural_check, snapshot_source
from ddo.review import append_history, current_version, detect_incomplete_pass, mark_findings
from ddo.validation import validate


def run_refine(doc_dir: Path, version: int | None = None) -> None:
    """Run the ddo-refine phase: snapshot → patch → validate → commit → render → audit."""
    # 1. Torn-pass check.
    if detect_incomplete_pass(doc_dir):
        raise SystemExit("Torn pass detected; reconcile review_history/ first.")

    # 2. Load source + interview log.
    version = version or current_version(doc_dir)
    data_path = doc_dir / "document_data.yaml"
    data = yaml.safe_load(data_path.read_text(encoding="utf-8"))
    log = yaml.safe_load(
        (doc_dir / "review_history" / f"interview_log_v{version}.yaml").read_text(encoding="utf-8")
    )

    # 3. SNAPSHOT before any mutation (force=False -> double-snapshot fails closed).
    snapshot_source(data_path, doc_dir, version)

    # 4. Apply patches PURELY (deep copy; no I/O). Constrained `set`: leaf-scalar,
    #    no auto-vivify, no type change. Raises on any bad patch -> source untouched.
    patched = apply_patches(data, log)

    # 5. Validate twice IN-MEMORY before any write. Either failure -> abort,
    #    document_data.yaml stays byte-identical.
    refine_structural_check(patched)  # sections stay a list; bodies stay non-empty str
    validate(patched)  # importable v0.0.1 minimal contract

    # 6. Before/After diff — human-only, never re-parsed. HITL gate.
    before = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    after = yaml.safe_dump(patched, sort_keys=False, allow_unicode=True)
    diff = "\n".join(
        difflib.unified_diff(
            before.splitlines(),
            after.splitlines(),
            fromfile="document_data.yaml (before)",
            tofile="document_data.yaml (after)",
            lineterm="",
        )
    )
    print(diff)
    print("approve all / skip <n>   [WAITING FOR USER RESPONSE]")
    # ... on `skip <n>`, cascade to depends_on dependents and re-run apply_patches ...

    # 7. Commit: re-checks structural + validate internally, safe_dump(sort_keys=False),
    #    atomic_write (force=True — the target legitimately exists).
    committed = commit_refine(data_path, patched, force=True)

    # 8. Re-render via the ddo-render SKILL (never build.py directly); flags from meta.
    meta = yaml.safe_load(committed.read_text(encoding="utf-8"))["meta"]
    render_ok = invoke_ddo_render(meta["template"], meta["output_formats"], committed)  # noqa: F821

    # 9. Audit reconcile — ONLY on render success.
    if not render_ok:
        raise SystemExit("Re-render failed: not marking applied, not appending history.")

    applied_ids = ["F-001", "F-004"]  # findings whose patches actually landed
    mark_findings(doc_dir, version, applied_ids, field="applied")
    append_history(
        doc_dir,
        {
            "version": version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "persona": "scientific_reviewer",
            "findings": {"critical": 2, "major": 2, "minor": 1},
            "resolutions": {
                "revise": 1,
                "add_evidence": 1,
                "acknowledge": 2,
                "dispute": 0,
                "defer": 1,
            },
            "applied": len(applied_ids),
            "render": "ok",  # build.py's ACTUAL exit, surfaced by ddo-render
        },
    )
    print("Refine v%d complete. [WAITING FOR USER REVIEW]" % version)
