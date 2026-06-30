"""Unit tests for the DDO review data layer (:mod:`ddo.review`).

Covers M1 (structural contracts pass/fail), M2 (``_vN`` derivation, incl. gaps
and partial sequences), torn-pass detection (report-without-log, source-newer-
than-history), and byte-deterministic view/history generation.

All tests are pure (no subprocess, no filesystem side-effects beyond ``tmp_path``).
The ``doc_dir`` fixture monkeypatches ``ddo.paths._REPO_ROOT`` so that
``assert_within_documents`` accepts paths under ``tmp_path / "Documents"``.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone

import pytest
import yaml

import ddo.paths as _paths
from ddo.review import (
    DECISION_ENUM,
    SEVERITY_ENUM,
    ReportValidationError,
    append_history,
    current_version,
    detect_incomplete_pass,
    mark_findings,
    render_history_view,
    render_report_view,
    report_version,
    validate_interview_log,
    validate_report,
    write_interview_log,
    write_report,
)

# ---------------------------------------------------------------------------
# Shared fixture helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def doc_dir(tmp_path, monkeypatch):
    """Return a contained doc_dir under a monkeypatched Documents/ root."""
    monkeypatch.setattr(_paths, "_REPO_ROOT", tmp_path)
    d = tmp_path / "Documents" / "test_doc"
    d.mkdir(parents=True)
    return d


def _valid_report(version: int = 1) -> dict:
    return {
        "meta": {
            "version": version,
            "persona": "product_critic",
            "document": "output/test_doc.md",
            "timestamp": "2026-06-29T00:00:00Z",
        },
        "findings": [
            {
                "id": "F-001",
                "severity": "Critical",
                "category": "Missing Evidence",
                "location": "Section 1",
                "description": "Claim is unsubstantiated.",
                "suggestion": "Add evidence entry.",
                "decision_recorded": False,
                "applied": False,
                "resolution": None,
            }
        ],
    }


def _valid_log(version: int = 1) -> dict:
    return {
        "meta": {"version": version, "timestamp": "2026-06-29T00:01:00Z"},
        "resolutions": [
            {
                "finding_id": "F-001",
                "decision": "revise",
                "detail": "Revised the body text.",
                "patch": {
                    "op": "set",
                    "target": "content.sections[0].body",
                    "value": "Revised text.",
                    "depends_on": [],
                },
            }
        ],
    }


# ---------------------------------------------------------------------------
# validate_report — pass paths (M1)
# ---------------------------------------------------------------------------


def test_validate_report_passes_valid():
    """A complete, well-formed report dict validates without raising."""
    validate_report(_valid_report())


def test_validate_report_all_severities_accepted():
    """Every value in SEVERITY_ENUM is accepted by validate_report."""
    for sev in SEVERITY_ENUM:
        r = _valid_report()
        r["findings"][0]["severity"] = sev
        validate_report(r)


def test_validate_report_empty_findings_list_passes():
    """An empty findings list is valid (no findings to critique)."""
    r = _valid_report()
    r["findings"] = []
    validate_report(r)


# ---------------------------------------------------------------------------
# validate_report — fail paths (M1)
# ---------------------------------------------------------------------------


def test_validate_report_missing_meta_raises():
    """A report dict without a meta block raises ReportValidationError."""
    with pytest.raises(ReportValidationError, match="meta"):
        validate_report({"findings": []})


def test_validate_report_missing_meta_key_raises():
    """A meta block missing a required key raises ReportValidationError."""
    r = _valid_report()
    del r["meta"]["persona"]
    with pytest.raises(ReportValidationError, match="persona"):
        validate_report(r)


def test_validate_report_invalid_severity_raises():
    """A finding with an unrecognized severity string raises ReportValidationError."""
    r = _valid_report()
    r["findings"][0]["severity"] = "High"
    with pytest.raises(ReportValidationError, match="severity"):
        validate_report(r)


def test_validate_report_missing_finding_flag_raises():
    """A finding missing the 'applied' flag raises ReportValidationError."""
    r = _valid_report()
    del r["findings"][0]["applied"]
    with pytest.raises(ReportValidationError, match="applied"):
        validate_report(r)


def test_validate_report_missing_required_finding_field_raises():
    """A finding missing a required field raises ReportValidationError."""
    r = _valid_report()
    del r["findings"][0]["description"]
    with pytest.raises(ReportValidationError, match="description"):
        validate_report(r)


def test_validate_report_warns_when_findings_exceed_soft_cap():
    """More than 100 findings emits a UserWarning about the soft cap."""
    r = _valid_report()
    r["findings"] = [
        {
            "id": f"F-{i:03d}",
            "severity": "Minor",
            "category": "cat",
            "location": "loc",
            "description": "desc",
            "suggestion": "sug",
            "decision_recorded": False,
            "applied": False,
            "resolution": None,
        }
        for i in range(101)
    ]
    with pytest.warns(UserWarning, match="soft cap"):
        validate_report(r)


# ---------------------------------------------------------------------------
# validate_interview_log — pass / fail (M1)
# ---------------------------------------------------------------------------


def test_validate_interview_log_passes_valid():
    """A complete, well-formed interview log validates without raising."""
    validate_interview_log(_valid_log())


def test_validate_interview_log_null_patch_accepted():
    """A null/None patch is accepted for acknowledge-type resolutions."""
    log = _valid_log()
    log["resolutions"][0]["patch"] = None
    log["resolutions"][0]["decision"] = "acknowledge"
    validate_interview_log(log)


def test_validate_interview_log_all_decisions_accepted():
    """Every value in DECISION_ENUM is accepted by validate_interview_log."""
    for dec in DECISION_ENUM:
        log = _valid_log()
        log["resolutions"][0]["decision"] = dec
        validate_interview_log(log)


def test_validate_interview_log_missing_meta_key_raises():
    """A log meta block missing a required key raises ReportValidationError."""
    log = _valid_log()
    del log["meta"]["timestamp"]
    with pytest.raises(ReportValidationError, match="timestamp"):
        validate_interview_log(log)


def test_validate_interview_log_invalid_decision_raises():
    """An unrecognized decision value raises ReportValidationError."""
    log = _valid_log()
    log["resolutions"][0]["decision"] = "ignore"
    with pytest.raises(ReportValidationError, match="decision"):
        validate_interview_log(log)


def test_validate_interview_log_missing_patch_key_raises():
    """A resolution dict missing the 'patch' key raises ReportValidationError."""
    log = _valid_log()
    del log["resolutions"][0]["patch"]
    with pytest.raises(ReportValidationError, match="patch"):
        validate_interview_log(log)


# ---------------------------------------------------------------------------
# validate_interview_log — op enum and per-op field rules (v0.0.3)
# ---------------------------------------------------------------------------


def test_validate_interview_log_append_op_accepted():
    """A patch with op='append', target, and value is structurally valid."""
    log = _valid_log()
    log["resolutions"][0]["patch"] = {
        "op": "append",
        "target": "evidence_bank",
        "value": {"id": "ev_new", "type": "note", "content": "c", "source": "s"},
    }
    validate_interview_log(log)  # must not raise


def test_validate_interview_log_delete_op_accepted():
    """A patch with op='delete' and target (no value) is structurally valid."""
    log = _valid_log()
    log["resolutions"][0]["patch"] = {
        "op": "delete",
        "target": "evidence_bank[0]",
    }
    validate_interview_log(log)  # must not raise


def test_validate_interview_log_insert_op_with_at_accepted():
    """A patch with op='insert', target, at, and value is structurally valid."""
    log = _valid_log()
    log["resolutions"][0]["patch"] = {
        "op": "insert",
        "target": "content.sections",
        "at": 2,
        "value": {"id": "ev_new", "type": "note", "content": "c", "source": "s"},
    }
    validate_interview_log(log)  # must not raise


def test_validate_interview_log_insert_without_at_raises():
    """A patch with op='insert' missing the 'at' field raises ReportValidationError."""
    log = _valid_log()
    log["resolutions"][0]["patch"] = {
        "op": "insert",
        "target": "content.sections",
        "value": {"id": "ev_new", "type": "note", "content": "c", "source": "s"},
    }
    with pytest.raises(ReportValidationError, match="at"):
        validate_interview_log(log)


def test_validate_interview_log_delete_with_value_raises():
    """A patch with op='delete' that includes a 'value' field raises ReportValidationError."""
    log = _valid_log()
    log["resolutions"][0]["patch"] = {
        "op": "delete",
        "target": "evidence_bank[0]",
        "value": "something",
    }
    with pytest.raises(ReportValidationError, match="value"):
        validate_interview_log(log)


def test_validate_interview_log_set_with_at_raises():
    """A patch with op='set' that includes an 'at' field raises ReportValidationError."""
    log = _valid_log()
    log["resolutions"][0]["patch"] = {
        "op": "set",
        "target": "meta.title",
        "value": "new",
        "at": 0,
    }
    with pytest.raises(ReportValidationError, match="at"):
        validate_interview_log(log)


def test_validate_interview_log_append_with_at_raises():
    """A patch with op='append' that includes an 'at' field raises ReportValidationError."""
    log = _valid_log()
    log["resolutions"][0]["patch"] = {
        "op": "append",
        "target": "evidence_bank",
        "value": {"id": "ev_new", "type": "note", "content": "c", "source": "s"},
        "at": 1,
    }
    with pytest.raises(ReportValidationError, match="at"):
        validate_interview_log(log)


def test_validate_interview_log_delete_with_at_raises():
    """A patch with op='delete' that includes an 'at' field raises ReportValidationError."""
    log = _valid_log()
    log["resolutions"][0]["patch"] = {
        "op": "delete",
        "target": "evidence_bank[0]",
        "at": 0,
    }
    with pytest.raises(ReportValidationError, match="at"):
        validate_interview_log(log)


def test_validate_interview_log_insert_negative_at_raises():
    """A patch with op='insert' and a negative 'at' value raises ReportValidationError."""
    log = _valid_log()
    log["resolutions"][0]["patch"] = {
        "op": "insert",
        "target": "content.sections",
        "at": -1,
        "value": {"id": "ev_new", "type": "note", "content": "c", "source": "s"},
    }
    with pytest.raises(ReportValidationError, match="at"):
        validate_interview_log(log)


def test_validate_interview_log_insert_bool_at_raises():
    """A patch with op='insert' and a bool 'at' value raises ReportValidationError."""
    log = _valid_log()
    log["resolutions"][0]["patch"] = {
        "op": "insert",
        "target": "content.sections",
        "at": True,
        "value": {"id": "ev_new", "type": "note", "content": "c", "source": "s"},
    }
    with pytest.raises(ReportValidationError, match="at"):
        validate_interview_log(log)


def test_validate_interview_log_unknown_op_raises():
    """A patch with an op not in OP_ENUM raises ReportValidationError."""
    log = _valid_log()
    log["resolutions"][0]["patch"] = {
        "op": "replace",
        "target": "meta.title",
        "value": "x",
    }
    with pytest.raises(ReportValidationError, match="op"):
        validate_interview_log(log)


# ---------------------------------------------------------------------------
# _vN derivation — report_version / current_version (M2)
# ---------------------------------------------------------------------------


def test_report_version_returns_1_when_no_reports(doc_dir):
    """With no existing reports, report_version returns 1."""
    assert report_version(doc_dir) == 1


def test_report_version_returns_max_plus_one_contiguous(doc_dir):
    """With v1 and v2 present, report_version returns v3 (max+1)."""
    rh = doc_dir / "review_history"
    rh.mkdir()
    (rh / "red_team_report_v1.yaml").write_text("x")
    (rh / "red_team_report_v2.yaml").write_text("x")
    assert report_version(doc_dir) == 3


def test_report_version_handles_gaps(doc_dir):
    """v1 + v3 present → next is v4 (max+1, not v2 to fill the gap)."""
    rh = doc_dir / "review_history"
    rh.mkdir()
    (rh / "red_team_report_v1.yaml").write_text("x")
    (rh / "red_team_report_v3.yaml").write_text("x")
    assert report_version(doc_dir) == 4


def test_current_version_returns_none_when_no_reports(doc_dir):
    """With no existing reports, current_version returns None."""
    assert current_version(doc_dir) is None


def test_current_version_returns_max_existing(doc_dir):
    """current_version returns the largest existing report version."""
    rh = doc_dir / "review_history"
    rh.mkdir()
    (rh / "red_team_report_v1.yaml").write_text("x")
    (rh / "red_team_report_v3.yaml").write_text("x")
    assert current_version(doc_dir) == 3


def test_current_version_ignores_non_report_files(doc_dir):
    """Interview log files are not counted as report versions."""
    rh = doc_dir / "review_history"
    rh.mkdir()
    (rh / "interview_log_v5.yaml").write_text("x")  # log, not report
    (rh / "red_team_report_v2.yaml").write_text("x")
    assert current_version(doc_dir) == 2


# ---------------------------------------------------------------------------
# Torn-pass detection
# ---------------------------------------------------------------------------


def test_detect_incomplete_pass_returns_none_when_no_review_history(doc_dir):
    """With no review_history directory, detect_incomplete_pass returns None."""
    assert detect_incomplete_pass(doc_dir) is None


def test_detect_incomplete_pass_clean_when_report_and_log_match(doc_dir):
    """Matching report and log for the same version → no torn-pass detected."""
    rh = doc_dir / "review_history"
    rh.mkdir()
    (rh / "red_team_report_v1.yaml").write_text("x")
    (rh / "interview_log_v1.yaml").write_text("x")
    assert detect_incomplete_pass(doc_dir) is None


def test_detect_incomplete_pass_report_without_log(doc_dir):
    """A report without a matching interview log is flagged as torn-pass."""
    rh = doc_dir / "review_history"
    rh.mkdir()
    (rh / "red_team_report_v1.yaml").write_text("x")
    # no matching interview_log_v1.yaml
    result = detect_incomplete_pass(doc_dir)
    assert result is not None
    assert result["version"] == 1
    assert "interview_log_v1.yaml" in result["reason"]
    assert "suggestion" in result


def test_detect_incomplete_pass_source_newer_than_history(doc_dir):
    """document_data.yaml modified after the history.yaml timestamp triggers torn-pass."""
    rh = doc_dir / "review_history"
    rh.mkdir()
    # history.yaml with a timestamp in the past
    past_ts = (datetime.now(tz=timezone.utc) - timedelta(hours=1)).isoformat()
    history = {"passes": [{"version": 1, "timestamp": past_ts}]}
    (rh / "history.yaml").write_text(yaml.safe_dump(history))
    # document_data.yaml modified now (which is after past_ts)
    data = doc_dir / "document_data.yaml"
    data.write_text("meta: {}")
    # Force mtime to be very recent (after the history timestamp)
    now = time.time()
    os.utime(data, (now, now))
    result = detect_incomplete_pass(doc_dir)
    assert result is not None
    assert "document_data.yaml" in result["reason"]


# ---------------------------------------------------------------------------
# write_report / write_interview_log
# ---------------------------------------------------------------------------


def test_write_report_creates_yaml_and_view(doc_dir):
    """write_report creates both the YAML and the human-review Markdown view."""
    report = _valid_report(version=1)
    path = write_report(doc_dir, report, version=1)
    assert path.name == "red_team_report_v1.yaml"
    assert path.is_file()
    # View file should also be created
    view = doc_dir / "review_history" / "red_team_view_v1.md"
    assert view.is_file()
    assert "Red Team Report" in view.read_text()


def test_write_report_refuses_overwrite_by_default(doc_dir):
    """write_report with force=False raises OverwriteError if the file exists."""
    from ddo.ingest import OverwriteError

    report = _valid_report(version=1)
    write_report(doc_dir, report, version=1)
    with pytest.raises(OverwriteError):
        write_report(doc_dir, report, version=1, force=False)


def test_write_interview_log_creates_yaml(doc_dir):
    """write_interview_log creates the YAML and its content round-trips."""
    log = _valid_log(version=1)
    path = write_interview_log(doc_dir, log, version=1)
    assert path.name == "interview_log_v1.yaml"
    assert path.is_file()
    loaded = yaml.safe_load(path.read_text())
    assert loaded["meta"]["version"] == 1


# ---------------------------------------------------------------------------
# mark_findings
# ---------------------------------------------------------------------------


def test_mark_findings_decision_recorded(doc_dir):
    """mark_findings sets decision_recorded=True for named finding IDs."""
    write_report(doc_dir, _valid_report(version=1), version=1)
    mark_findings(doc_dir, version=1, finding_ids=["F-001"], field="decision_recorded")
    rp = doc_dir / "review_history" / "red_team_report_v1.yaml"
    updated = yaml.safe_load(rp.read_text())
    assert updated["findings"][0]["decision_recorded"] is True


def test_mark_findings_applied(doc_dir):
    """mark_findings sets applied=True for named finding IDs."""
    write_report(doc_dir, _valid_report(version=1), version=1)
    mark_findings(doc_dir, version=1, finding_ids=["F-001"], field="applied")
    rp = doc_dir / "review_history" / "red_team_report_v1.yaml"
    updated = yaml.safe_load(rp.read_text())
    assert updated["findings"][0]["applied"] is True


def test_mark_findings_invalid_field_raises(doc_dir):
    """An invalid field name raises ValueError."""
    write_report(doc_dir, _valid_report(version=1), version=1)
    with pytest.raises(ValueError, match="field must be"):
        mark_findings(doc_dir, version=1, finding_ids=["F-001"], field="bogus")


def test_mark_findings_regenerates_view(doc_dir):
    """mark_findings regenerates the Markdown view to reflect updated flags."""
    write_report(doc_dir, _valid_report(version=1), version=1)
    mark_findings(doc_dir, version=1, finding_ids=["F-001"], field="decision_recorded")
    view = (doc_dir / "review_history" / "red_team_view_v1.md").read_text()
    assert "decision_recorded" in view


# ---------------------------------------------------------------------------
# append_history
# ---------------------------------------------------------------------------


def test_append_history_creates_history_yaml_and_md(doc_dir):
    """append_history creates history.yaml and history.md on first call."""
    write_report(doc_dir, _valid_report(version=1), version=1)
    write_interview_log(doc_dir, _valid_log(version=1), version=1)
    entry = {
        "version": 1,
        "timestamp": "2026-06-29T00:05:00Z",
        "persona": "product_critic",
        "findings": {"critical": 1, "major": 0, "minor": 0},
        "resolutions": {
            "revise": 1,
            "add_evidence": 0,
            "acknowledge": 0,
            "dispute": 0,
            "defer": 0,
        },
        "applied": 1,
        "render": "ok",
    }
    append_history(doc_dir, entry)
    hp = doc_dir / "review_history" / "history.yaml"
    assert hp.is_file()
    history = yaml.safe_load(hp.read_text())
    assert len(history["passes"]) == 1
    assert history["passes"][0]["version"] == 1
    assert (doc_dir / "review_history" / "history.md").is_file()


def test_append_history_accumulates_passes(doc_dir):
    """append_history adds successive pass entries to history.yaml."""
    write_report(doc_dir, _valid_report(version=1), version=1)
    write_interview_log(doc_dir, _valid_log(version=1), version=1)
    entry = {
        "version": 1,
        "timestamp": "2026-06-29T00:05:00Z",
        "persona": "product_critic",
        "findings": {"critical": 0, "major": 0, "minor": 0},
        "resolutions": {
            "revise": 0,
            "add_evidence": 0,
            "acknowledge": 0,
            "dispute": 0,
            "defer": 0,
        },
        "applied": 0,
        "render": "ok",
    }
    append_history(doc_dir, entry)
    append_history(doc_dir, {**entry, "version": 2})
    history = yaml.safe_load((doc_dir / "review_history" / "history.yaml").read_text())
    assert len(history["passes"]) == 2


def test_append_history_phantom_warns_when_artifacts_missing(doc_dir):
    """append_history warns and sets _phantom=True when artifacts are missing."""
    entry = {
        "version": 99,
        "timestamp": "2026-06-29T00:00:00Z",
        "persona": "product_critic",
        "findings": {"critical": 0, "major": 0, "minor": 0},
        "resolutions": {
            "revise": 0,
            "add_evidence": 0,
            "acknowledge": 0,
            "dispute": 0,
            "defer": 0,
        },
        "applied": 0,
        "render": "ok",
    }
    with pytest.warns(UserWarning, match="phantom"):
        append_history(doc_dir, entry)
    history = yaml.safe_load((doc_dir / "review_history" / "history.yaml").read_text())
    assert history["passes"][0].get("_phantom") is True


# ---------------------------------------------------------------------------
# Byte-deterministic view generation (M2)
# ---------------------------------------------------------------------------


def test_render_report_view_is_deterministic():
    """render_report_view produces identical output for the same input."""
    report = _valid_report()
    assert render_report_view(report) == render_report_view(report)


def test_render_report_view_groups_by_severity():
    """render_report_view orders Critical before Minor in the output."""
    report = _valid_report()
    report["findings"].append(
        {
            "id": "F-002",
            "severity": "Minor",
            "category": "Style",
            "location": "Section 2",
            "description": "Minor issue.",
            "suggestion": "Fix it.",
            "decision_recorded": False,
            "applied": False,
            "resolution": None,
        }
    )
    view = render_report_view(report)
    critical_pos = view.find("## Critical")
    minor_pos = view.find("## Minor")
    assert critical_pos != -1
    assert minor_pos != -1
    assert critical_pos < minor_pos, "Critical section must precede Minor section"


def test_render_report_view_shows_flags():
    """render_report_view includes flag names (e.g. decision_recorded) in output."""
    report = _valid_report()
    report["findings"][0]["decision_recorded"] = True
    view = render_report_view(report)
    assert "decision_recorded" in view


def test_render_history_view_is_deterministic():
    """render_history_view produces identical output for the same input."""
    history = {
        "passes": [
            {
                "version": 1,
                "timestamp": "2026-06-29T00:00:00Z",
                "persona": "product_critic",
                "render": "ok",
                "findings": {"critical": 1, "major": 0, "minor": 0},
                "resolutions": {
                    "revise": 1,
                    "add_evidence": 0,
                    "acknowledge": 0,
                    "dispute": 0,
                    "defer": 0,
                },
                "applied": 1,
            }
        ]
    }
    assert render_history_view(history) == render_history_view(history)


def test_render_history_view_empty_passes():
    """render_history_view handles an empty passes list gracefully."""
    view = render_history_view({"passes": []})
    assert "0" in view and "Passes" in view
