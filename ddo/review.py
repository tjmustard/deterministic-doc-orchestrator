"""Critique/interview data layer for the DDO adversarial loop (``ddo.review``).

Owns structural contracts, atomic + contained writes, deterministic view
generation, ``_vN`` derivation, and on-entry torn-pass detection for the
``ddo-red-team``, ``ddo-interview``, and ``ddo-refine`` skills.

All writes delegate to :func:`ddo.ingest.atomic_write` (crash-safe,
overwrite-guarded) and :func:`ddo.paths.assert_within_documents` (containment).
Views are code-generated from stored data only — no wall-clock at generation
time; timestamps come exclusively from stored report/log dicts.

Single-user/no-concurrency is a relied-upon invariant (SuperPRD §3). The
read-modify-write paths in :func:`mark_findings` and :func:`append_history`
are safe only under that guarantee.
"""

from __future__ import annotations

import re
import warnings
from datetime import datetime, timezone
from pathlib import Path

import yaml

from ddo.ingest import atomic_write
from ddo.paths import assert_within_documents

# ---------------------------------------------------------------------------
# Data-contract enums
# ---------------------------------------------------------------------------

SEVERITY_ENUM: frozenset[str] = frozenset({"Critical", "Major", "Minor"})
DECISION_ENUM: frozenset[str] = frozenset(
    {"revise", "add_evidence", "acknowledge", "dispute", "defer"}
)
OP_ENUM: frozenset[str] = frozenset({"set", "append", "delete", "insert"})

# Soft finding-count threshold (warn, not error)
_FINDING_SOFT_CAP = 100

# Filename patterns inside review_history/
_REPORT_RE = re.compile(r"^red_team_report_v(\d+)\.yaml$")
_LOG_RE = re.compile(r"^interview_log_v(\d+)\.yaml$")


class ReportValidationError(Exception):
    """Raised when a report or interview log fails its structural contract."""


# ---------------------------------------------------------------------------
# Contained path helpers (DO NOT add these to ddo.paths / path_deriver)
# ---------------------------------------------------------------------------


def _rh_dir(doc_dir: Path) -> Path:
    """Return the contained ``review_history/`` path for ``doc_dir``."""
    return assert_within_documents(doc_dir / "review_history")


def _report_path(doc_dir: Path, version: int) -> Path:
    return assert_within_documents(doc_dir / "review_history" / f"red_team_report_v{version}.yaml")


def _log_path(doc_dir: Path, version: int) -> Path:
    return assert_within_documents(doc_dir / "review_history" / f"interview_log_v{version}.yaml")


def _view_path(doc_dir: Path, version: int) -> Path:
    return assert_within_documents(doc_dir / "review_history" / f"red_team_view_v{version}.md")


def _history_yaml_path(doc_dir: Path) -> Path:
    return assert_within_documents(doc_dir / "review_history" / "history.yaml")


def _history_md_path(doc_dir: Path) -> Path:
    return assert_within_documents(doc_dir / "review_history" / "history.md")


# ---------------------------------------------------------------------------
# _vN derivation (file-tree authoritative)
# ---------------------------------------------------------------------------


def _existing_report_versions(doc_dir: Path) -> list[int]:
    """Scan review_history/ and return all existing report version numbers."""
    rh = doc_dir / "review_history"
    if not rh.is_dir():
        return []
    return [int(m.group(1)) for f in rh.iterdir() if (m := _REPORT_RE.match(f.name))]


def report_version(doc_dir: Path) -> int:
    """Derive the next report version number as ``max(existing N) + 1``.

    Returns ``1`` when no prior reports exist. Handles gaps in the sequence
    (e.g. v1, v3 present → next is v4).

    Args:
        doc_dir: The document's root directory (under ``Documents/``).

    Returns:
        The next integer version to use for a new pass.
    """
    versions = _existing_report_versions(doc_dir)
    return (max(versions) + 1) if versions else 1


def current_version(doc_dir: Path) -> int | None:
    """Return ``max(N)`` for existing reports, or ``None`` if none exist.

    Used by interview/refine skills to identify the version to operate on.

    Args:
        doc_dir: The document's root directory.

    Returns:
        The highest existing report version, or ``None``.
    """
    versions = _existing_report_versions(doc_dir)
    return max(versions) if versions else None


# ---------------------------------------------------------------------------
# Torn-pass detection
# ---------------------------------------------------------------------------


def detect_incomplete_pass(doc_dir: Path) -> dict | None:
    """Detect a torn (incomplete) prior pass in ``review_history/``.

    A pass is considered torn if any of the following hold:

    1. A ``red_team_report_vN.yaml`` exists without a matching
       ``interview_log_vN.yaml`` (interview never completed).
    2. ``document_data.yaml`` is newer than the latest ``history.yaml`` record
       timestamp (a refine may have been partially applied).

    Args:
        doc_dir: The document's root directory.

    Returns:
        A ``dict`` with keys ``version``, ``reason``, and ``suggestion``
        describing the torn state, or ``None`` if the pass state is clean.
    """
    rh = doc_dir / "review_history"
    if not rh.is_dir():
        return None

    report_versions: set[int] = set()
    log_versions: set[int] = set()

    for f in rh.iterdir():
        m = _REPORT_RE.match(f.name)
        if m:
            report_versions.add(int(m.group(1)))
            continue
        m = _LOG_RE.match(f.name)
        if m:
            log_versions.add(int(m.group(1)))

    # A report without its log = incomplete interview pass
    for v in sorted(report_versions):
        if v not in log_versions:
            return {
                "version": v,
                "reason": (
                    f"red_team_report_v{v}.yaml exists but interview_log_v{v}.yaml is missing"
                ),
                "suggestion": (
                    f"Resume the ddo-interview pass for v{v}, or remove the "
                    f"partial report to start a fresh pass."
                ),
            }

    # Source newer than latest history record
    data_path = doc_dir / "document_data.yaml"
    history_path = rh / "history.yaml"

    if data_path.is_file() and history_path.is_file():
        try:
            raw = history_path.read_text(encoding="utf-8")
            history = yaml.safe_load(raw) or {}
            passes = history.get("passes", [])
            if passes:
                ts_str = passes[-1].get("timestamp")
                if ts_str:
                    latest_ts = datetime.fromisoformat(ts_str)
                    if latest_ts.tzinfo is None:
                        latest_ts = latest_ts.replace(tzinfo=timezone.utc)
                    data_mtime = datetime.fromtimestamp(data_path.stat().st_mtime, tz=timezone.utc)
                    if data_mtime > latest_ts:
                        return {
                            "version": len(passes),
                            "reason": (
                                f"document_data.yaml was modified after the latest "
                                f"history record (data: {data_mtime.isoformat()}, "
                                f"history: {ts_str})"
                            ),
                            "suggestion": (
                                "A partial refine may have been applied without "
                                "completing the audit. Inspect review_history/ and "
                                "reconcile manually if needed."
                            ),
                        }
        except (yaml.YAMLError, KeyError, ValueError, OSError):
            pass

    return None


# ---------------------------------------------------------------------------
# Structural validation
# ---------------------------------------------------------------------------


def validate_report(report: dict) -> None:
    """Validate the in-code structural contract of a ``red_team_report`` dict.

    Enforces: required ``meta`` keys, ``findings[]`` shape, fixed-enum
    ``severity``, required flag fields (``decision_recorded``, ``applied``,
    ``resolution``). ``category`` is free-text and not validated beyond presence.

    Args:
        report: Parsed ``red_team_report_vN.yaml`` dictionary.

    Raises:
        ReportValidationError: On the first structural violation, naming the
            field or index.
    """
    if not isinstance(report, dict):
        raise ReportValidationError("report: must be a mapping/dict")

    meta = report.get("meta")
    if not isinstance(meta, dict):
        raise ReportValidationError("report.meta: required and must be a mapping")
    for key in ("version", "persona", "document", "timestamp"):
        if key not in meta:
            raise ReportValidationError(f"report.meta.{key}: required field is missing")

    findings = report.get("findings")
    if findings is None:
        raise ReportValidationError("report.findings: required field is missing")
    if not isinstance(findings, list):
        raise ReportValidationError("report.findings: must be a list")

    for i, finding in enumerate(findings):
        if not isinstance(finding, dict):
            raise ReportValidationError(f"report.findings[{i}]: must be a mapping")
        for key in ("id", "severity", "category", "location", "description", "suggestion"):
            if key not in finding:
                raise ReportValidationError(
                    f"report.findings[{i}].{key}: required field is missing"
                )
        sev = finding["severity"]
        if sev not in SEVERITY_ENUM:
            raise ReportValidationError(
                f"report.findings[{i}].severity: must be one of "
                f"{sorted(SEVERITY_ENUM)}, got {sev!r}"
            )
        for flag in ("decision_recorded", "applied", "resolution"):
            if flag not in finding:
                raise ReportValidationError(
                    f"report.findings[{i}].{flag}: required field is missing"
                )

    finding_count = len(findings)
    if finding_count > _FINDING_SOFT_CAP:
        warnings.warn(
            f"validate_report: {finding_count} findings exceed the soft cap of "
            f"{_FINDING_SOFT_CAP}. Consider splitting into multiple passes.",
            stacklevel=2,
        )


def validate_interview_log(log: dict) -> None:
    """Validate the in-code structural contract of an ``interview_log`` dict.

    Enforces: required ``meta`` keys, ``resolutions[]`` shape, fixed-enum
    ``decision``, required ``patch`` key (may be ``null``).

    Args:
        log: Parsed ``interview_log_vN.yaml`` dictionary.

    Raises:
        ReportValidationError: On the first structural violation, naming the
            field or index.
    """
    if not isinstance(log, dict):
        raise ReportValidationError("interview_log: must be a mapping/dict")

    meta = log.get("meta")
    if not isinstance(meta, dict):
        raise ReportValidationError("interview_log.meta: required and must be a mapping")
    for key in ("version", "timestamp"):
        if key not in meta:
            raise ReportValidationError(f"interview_log.meta.{key}: required field is missing")

    resolutions = log.get("resolutions")
    if resolutions is None:
        raise ReportValidationError("interview_log.resolutions: required field is missing")
    if not isinstance(resolutions, list):
        raise ReportValidationError("interview_log.resolutions: must be a list")

    for i, res in enumerate(resolutions):
        if not isinstance(res, dict):
            raise ReportValidationError(f"interview_log.resolutions[{i}]: must be a mapping")
        for key in ("finding_id", "decision", "detail"):
            if key not in res:
                raise ReportValidationError(
                    f"interview_log.resolutions[{i}].{key}: required field is missing"
                )
        decision = res["decision"]
        if decision not in DECISION_ENUM:
            raise ReportValidationError(
                f"interview_log.resolutions[{i}].decision: must be one of "
                f"{sorted(DECISION_ENUM)}, got {decision!r}"
            )
        if "patch" not in res:
            raise ReportValidationError(
                f"interview_log.resolutions[{i}].patch: required field is missing"
            )

        patch = res["patch"]
        if patch is not None:
            op = patch.get("op")
            at = patch.get("at")
            has_target = "target" in patch
            has_at = "at" in patch
            has_value = "value" in patch

            # Unknown op
            if op not in OP_ENUM:
                raise ReportValidationError(
                    f"interview_log.resolutions[{i}].patch.op: unknown op {op!r}; "
                    f"must be one of {sorted(OP_ENUM)}"
                )

            # All ops require target
            if op in {"set", "append", "delete", "insert"} and not has_target:
                raise ReportValidationError(
                    f"interview_log.resolutions[{i}].patch.target: required for op {op!r}"
                )

            # insert requires at field
            if op == "insert" and not has_at:
                raise ReportValidationError(
                    f"interview_log.resolutions[{i}].patch.at: required for op 'insert'"
                )

            # Non-insert ops must not have at field
            if op != "insert" and has_at:
                raise ReportValidationError(
                    f"interview_log.resolutions[{i}].patch.at: field not allowed for op {op!r}"
                )

            # delete must not have value field
            if op == "delete" and has_value:
                raise ReportValidationError(
                    f"interview_log.resolutions[{i}].patch.value: field not allowed for op 'delete'"
                )

            # Validate at field type when present
            if has_at:
                if not isinstance(at, int) or isinstance(at, bool) or at < 0:
                    raise ReportValidationError(
                        f"interview_log.resolutions[{i}].patch.at: must be a "
                        f"non-negative integer, not bool/float/None (got {at!r})"
                    )


# ---------------------------------------------------------------------------
# Write operations
# ---------------------------------------------------------------------------


def write_report(doc_dir: Path, report: dict, version: int, *, force: bool = False) -> Path:
    """Write a ``red_team_report`` to ``review_history/red_team_report_vN.yaml``.

    Validates ``report`` before writing. Also generates the derived
    ``red_team_view_vN.md`` (deterministic, from stored data only).

    Args:
        doc_dir: The document's root directory.
        report: The report dict; must satisfy :func:`validate_report`.
        version: The version number ``N`` for the filename.
        force: If ``False`` (default), refuse to overwrite an existing file.

    Returns:
        The resolved, contained path to the written report file.

    Raises:
        ReportValidationError: If the report is structurally invalid.
        ddo.ingest.OverwriteError: If the file exists and ``force=False``.
        ddo.paths.PathContainmentError: If any derived path escapes Documents/.
    """
    validate_report(report)
    target = _report_path(doc_dir, version)
    atomic_write(target, yaml.safe_dump(report, sort_keys=False, allow_unicode=True), force=force)

    view_path = _view_path(doc_dir, version)
    atomic_write(view_path, render_report_view(report), force=force)

    return target


def write_interview_log(doc_dir: Path, log: dict, version: int, *, force: bool = False) -> Path:
    """Write an ``interview_log`` to ``review_history/interview_log_vN.yaml``.

    Args:
        doc_dir: The document's root directory.
        log: The log dict; must satisfy :func:`validate_interview_log`.
        version: The version number ``N``.
        force: If ``False`` (default), refuse to overwrite an existing file.

    Returns:
        The resolved, contained path to the written log file.

    Raises:
        ReportValidationError: If the log is structurally invalid.
        ddo.ingest.OverwriteError: If the file exists and ``force=False``.
        ddo.paths.PathContainmentError: If the path escapes Documents/.
    """
    validate_interview_log(log)
    target = _log_path(doc_dir, version)
    atomic_write(target, yaml.safe_dump(log, sort_keys=False, allow_unicode=True), force=force)
    return target


def mark_findings(doc_dir: Path, version: int, finding_ids: list[str], field: str) -> Path:
    """Atomically update a boolean flag on a set of findings in an existing report.

    Sets ``finding[field] = True`` for each finding whose ``id`` is in
    ``finding_ids``. The view is regenerated after the update.

    This is a read-modify-write operation safe only under the single-user
    invariant (SuperPRD §3); concurrent writers could lose updates silently.

    Args:
        doc_dir: The document's root directory.
        version: The report version ``N`` to update.
        finding_ids: Finding IDs to flip to ``True``.
        field: The field to set — must be ``"decision_recorded"`` or ``"applied"``.

    Returns:
        The path to the updated report file.

    Raises:
        ValueError: If ``field`` is not an allowed flag name.
        ddo.paths.PathContainmentError: If the path escapes Documents/.
    """
    if field not in ("decision_recorded", "applied"):
        raise ValueError(
            f"mark_findings: field must be 'decision_recorded' or 'applied', got {field!r}"
        )

    report_path = _report_path(doc_dir, version)
    report = yaml.safe_load(report_path.read_text(encoding="utf-8"))

    id_set = set(finding_ids)
    for finding in report.get("findings", []):
        if finding.get("id") in id_set:
            finding[field] = True

    atomic_write(
        report_path, yaml.safe_dump(report, sort_keys=False, allow_unicode=True), force=True
    )

    # Regenerate view to reflect updated flags
    view_path = _view_path(doc_dir, version)
    atomic_write(view_path, render_report_view(report), force=True)

    return report_path


# ---------------------------------------------------------------------------
# Deterministic view generation (no wall-clock; stored data only)
# ---------------------------------------------------------------------------


def render_report_view(report: dict) -> str:
    """Generate byte-deterministic Markdown from a stored ``red_team_report`` dict.

    No wall-clock is read. All timestamps come from ``report.meta.timestamp``.
    Findings are grouped Critical → Major → Minor.

    Args:
        report: Parsed ``red_team_report_vN.yaml`` dict.

    Returns:
        A deterministic Markdown string (``str``).
    """
    meta = report.get("meta", {})
    findings: list[dict] = report.get("findings", [])

    lines = [
        f"# Red Team Report v{meta.get('version', '?')}",
        "",
        f"**Persona:** {meta.get('persona', '?')}  ",
        f"**Document:** {meta.get('document', '?')}  ",
        f"**Timestamp:** {meta.get('timestamp', '?')}  ",
        f"**Total Findings:** {len(findings)}",
        "",
        "---",
        "",
    ]

    for severity in ("Critical", "Major", "Minor"):
        group = [f for f in findings if f.get("severity") == severity]
        if not group:
            continue
        lines += [f"## {severity} ({len(group)})", ""]
        for finding in group:
            fid = finding.get("id", "?")
            tags = []
            if finding.get("decision_recorded"):
                tags.append("decision_recorded")
            if finding.get("applied"):
                tags.append("applied")
            tag_str = f" `[{', '.join(tags)}]`" if tags else ""
            lines += [
                f"### {fid}{tag_str}",
                "",
                f"**Category:** {finding.get('category', '?')}  ",
                f"**Location:** {finding.get('location', '?')}",
                "",
                f"**Description:** {finding.get('description', '?')}",
                "",
                f"**Suggestion:** {finding.get('suggestion', '?')}",
                "",
            ]
            if finding.get("resolution"):
                lines += [f"**Resolution:** {finding['resolution']}", ""]

    return "\n".join(lines)


def render_history_view(history: dict) -> str:
    """Generate byte-deterministic Markdown from a stored ``history`` dict.

    No wall-clock is read. All data comes from the stored history dict.

    Args:
        history: Parsed ``history.yaml`` dict.

    Returns:
        A deterministic Markdown string (``str``).
    """
    passes: list[dict] = history.get("passes", [])

    lines = [
        "# Review History",
        "",
        f"**Total Passes:** {len(passes)}",
        "",
        "---",
        "",
    ]

    for p in passes:
        v = p.get("version", "?")
        lines += [
            f"## Pass v{v}",
            "",
            f"**Timestamp:** {p.get('timestamp', '?')}  ",
            f"**Persona:** {p.get('persona', '?')}  ",
            f"**Render:** {p.get('render', '?')}",
            "",
        ]
        findings = p.get("findings", {})
        if isinstance(findings, dict):
            lines.append(
                f"**Findings:** Critical: {findings.get('critical', 0)}, "
                f"Major: {findings.get('major', 0)}, "
                f"Minor: {findings.get('minor', 0)}"
            )
            lines.append("")
        resolutions = p.get("resolutions", {})
        if isinstance(resolutions, dict):
            parts = [f"{k}: {val}" for k, val in resolutions.items() if val]
            if parts:
                lines += [f"**Resolutions:** {', '.join(parts)}", ""]
        applied = p.get("applied", 0)
        lines += [f"**Applied:** {applied}", ""]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# History management
# ---------------------------------------------------------------------------


def append_history(doc_dir: Path, entry: dict) -> None:
    """Append one pass record to ``history.yaml`` and regenerate ``history.md``.

    The file tree is treated as authoritative: loads existing ``history.yaml``
    if present, appends the entry, then writes back atomically.  A phantom
    entry (pass record with no backing artifacts) is flagged with a warning.

    This is a read-modify-write operation safe only under the single-user
    invariant (SuperPRD §3).

    Args:
        doc_dir: The document's root directory.
        entry: Pass record dict (``version``, ``timestamp``, ``persona``,
            ``findings``, ``resolutions``, ``applied``, ``render``).
    """
    history_path = _history_yaml_path(doc_dir)

    if history_path.is_file():
        history = yaml.safe_load(history_path.read_text(encoding="utf-8")) or {}
    else:
        history = {}

    if not isinstance(history.get("passes"), list):
        history["passes"] = []

    # Flag phantom entries (record without backing artifacts in the file tree)
    version = entry.get("version")
    if version is not None:
        rh = doc_dir / "review_history"
        missing = []
        if not (rh / f"red_team_report_v{version}.yaml").is_file():
            missing.append(f"red_team_report_v{version}.yaml")
        if not (rh / f"interview_log_v{version}.yaml").is_file():
            missing.append(f"interview_log_v{version}.yaml")
        if missing:
            warnings.warn(
                f"append_history: pass v{version} is missing backing artifact(s) "
                f"{missing}; marking as phantom.",
                stacklevel=2,
            )
            entry = {**entry, "_phantom": True}

    history["passes"].append(entry)

    content = yaml.safe_dump(history, sort_keys=False, allow_unicode=True)
    atomic_write(history_path, content, force=True)

    md_path = _history_md_path(doc_dir)
    atomic_write(md_path, render_history_view(history), force=True)
