"""Unit tests for the DDO refine mutation layer (:mod:`ddo.refine`).

Covers M3 (byte-unchanged-on-abort), M4 (validate-clean output), M7 (key-order
+ snapshot fidelity), M8 (constrained-set corruption rejection), M9 (pre-refine
snapshot rollback). All tests are pure (no subprocess; filesystem side-effects
only within ``tmp_path`` via a monkeypatched ``_REPO_ROOT``).
"""

from __future__ import annotations

import copy

import pytest
import yaml

import ddo.paths as _paths
from ddo.ingest import OverwriteError
from ddo.refine import (
    apply_patches,
    commit_refine,
    parse_path,
    refine_structural_check,
    snapshot_source,
)
from ddo.validation import ValidationError

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def doc_dir(tmp_path, monkeypatch):
    """Return a contained doc_dir under a monkeypatched Documents/ root."""
    monkeypatch.setattr(_paths, "_REPO_ROOT", tmp_path)
    d = tmp_path / "Documents" / "test_doc"
    d.mkdir(parents=True)
    return d


def _valid_doc() -> dict:
    """Minimal document that passes both refine_structural_check and validate()."""
    return {
        "meta": {
            "doc_type": "prd",
            "title": "Test Document",
            "version": "0.0.1",
            "date": "2026.06.29",
            "template": "prd_default",
            "output_formats": ["pdf", "html", "md"],
        },
        "content": {
            "sections": [
                {
                    "id": "intro",
                    "title": "Introduction",
                    "body": "This is the introduction.",
                    "claims": ["claim one"],
                    "evidence": ["ev-1"],
                },
            ]
        },
        "evidence_bank": [
            {"id": "ev-1", "type": "fact", "content": "Source fact.", "source": "spec"},
        ],
    }


def _make_log(resolutions: list[dict], version: int = 1) -> dict:
    return {
        "meta": {"version": version, "timestamp": "2026-06-29T00:00:00Z"},
        "resolutions": resolutions,
    }


# ---------------------------------------------------------------------------
# parse_path — valid inputs
# ---------------------------------------------------------------------------


def test_parse_path_single_segment():
    """A bare identifier parses to a single-element list."""
    assert parse_path("meta") == ["meta"]


def test_parse_path_dotted_segments():
    """Dot-separated identifiers parse to a list of string keys."""
    assert parse_path("meta.title") == ["meta", "title"]


def test_parse_path_bracket_index():
    """A bracketed integer index parses to an int element."""
    assert parse_path("content.sections[2].body") == ["content", "sections", 2, "body"]


def test_parse_path_multiple_brackets():
    """Consecutive bracket indices parse as consecutive int elements."""
    assert parse_path("data[0][1]") == ["data", 0, 1]


def test_parse_path_underscore_in_segment():
    """Identifiers with underscores are valid segment names."""
    assert parse_path("evidence_bank") == ["evidence_bank"]


def test_parse_path_zero_index():
    """Index [0] is a valid non-negative integer."""
    assert parse_path("sections[0]") == ["sections", 0]


# ---------------------------------------------------------------------------
# parse_path — invalid inputs
# ---------------------------------------------------------------------------


def test_parse_path_empty_string_raises():
    """An empty string raises ValueError."""
    with pytest.raises(ValueError, match="non-empty"):
        parse_path("")


def test_parse_path_negative_index_raises():
    """A negative integer index raises ValueError."""
    with pytest.raises(ValueError, match="non-negative"):
        parse_path("sections[-1]")


def test_parse_path_slice_raises():
    """A slice expression raises ValueError."""
    with pytest.raises(ValueError, match="bracket|non-negative"):
        parse_path("sections[1:3]")


def test_parse_path_starts_with_dot_raises():
    """A path starting with '.' raises ValueError (no leading identifier)."""
    with pytest.raises(ValueError, match="identifier"):
        parse_path(".meta")


def test_parse_path_consecutive_dots_raises():
    """Consecutive dots raise ValueError (empty segment between dots)."""
    with pytest.raises(ValueError, match="identifier"):
        parse_path("meta..title")


def test_parse_path_trailing_dot_raises():
    """A trailing dot raises ValueError (empty final segment)."""
    with pytest.raises(ValueError, match="identifier"):
        parse_path("meta.")


def test_parse_path_special_char_raises():
    """A special character like '$' raises ValueError."""
    with pytest.raises(ValueError, match="unexpected|bracket|non-empty|identifier"):
        parse_path("meta$title")


# ---------------------------------------------------------------------------
# apply_patches — happy paths (M4)
# ---------------------------------------------------------------------------


def test_apply_patches_set_leaf_scalar():
    """A set op on an existing leaf scalar replaces the value."""
    data = _valid_doc()
    log = _make_log(
        [
            {
                "finding_id": "F-001",
                "decision": "revise",
                "detail": "Update title.",
                "patch": {"op": "set", "target": "meta.title", "value": "Updated Title"},
            }
        ]
    )
    result = apply_patches(data, log)
    assert result["meta"]["title"] == "Updated Title"


def test_apply_patches_null_patch_skipped():
    """A null/None patch is silently skipped without modifying data."""
    data = _valid_doc()
    log = _make_log(
        [
            {
                "finding_id": "F-001",
                "decision": "acknowledge",
                "detail": "No change needed.",
                "patch": None,
            }
        ]
    )
    result = apply_patches(data, log)
    assert result == data


def test_apply_patches_append_evidence():
    """append_evidence op appends a dict to evidence_bank."""
    data = _valid_doc()
    new_entry = {"id": "ev-2", "type": "fact", "content": "Added fact.", "source": "test"}
    log = _make_log(
        [
            {
                "finding_id": "F-002",
                "decision": "add_evidence",
                "detail": "Add citation.",
                "patch": {"op": "append_evidence", "value": new_entry},
            }
        ]
    )
    result = apply_patches(data, log)
    assert result["evidence_bank"][-1] == new_entry
    assert len(result["evidence_bank"]) == 2


def test_apply_patches_append_review_log_creates_list():
    """append_review_log creates meta.review_log if absent."""
    data = _valid_doc()
    record = {"version": 1, "decision": "acknowledge", "note": "Intentional."}
    log = _make_log(
        [
            {
                "finding_id": "F-001",
                "decision": "acknowledge",
                "detail": "Logged.",
                "patch": {"op": "append_review_log", "value": record},
            }
        ]
    )
    result = apply_patches(data, log)
    assert result["meta"]["review_log"] == [record]


def test_apply_patches_append_review_log_extends_existing():
    """append_review_log extends an existing meta.review_log list."""
    data = _valid_doc()
    data["meta"]["review_log"] = [{"existing": True}]
    record = {"new": True}
    log = _make_log(
        [
            {
                "finding_id": "F-001",
                "decision": "acknowledge",
                "detail": "Extend.",
                "patch": {"op": "append_review_log", "value": record},
            }
        ]
    )
    result = apply_patches(data, log)
    assert len(result["meta"]["review_log"]) == 2


def test_apply_patches_is_pure_does_not_mutate_input():
    """apply_patches must not mutate the original data dict."""
    data = _valid_doc()
    original = copy.deepcopy(data)
    log = _make_log(
        [
            {
                "finding_id": "F-001",
                "decision": "revise",
                "detail": "Update.",
                "patch": {"op": "set", "target": "meta.title", "value": "New Title"},
            }
        ]
    )
    apply_patches(data, log)
    assert data == original


# ---------------------------------------------------------------------------
# apply_patches — M8: constrained-set corruption rejection
# ---------------------------------------------------------------------------


def test_apply_patches_set_on_non_scalar_raises():
    """``set`` targeting a dict (like meta itself) must be rejected."""
    data = _valid_doc()
    log = _make_log(
        [
            {
                "finding_id": "F-001",
                "decision": "revise",
                "detail": "bad patch",
                "patch": {"op": "set", "target": "meta", "value": {"malicious": True}},
            }
        ]
    )
    with pytest.raises(ValueError, match="leaf scalar"):
        apply_patches(data, log)


def test_apply_patches_set_type_change_raises():
    """``set`` must not change str to int."""
    data = _valid_doc()
    log = _make_log(
        [
            {
                "finding_id": "F-001",
                "decision": "revise",
                "detail": "type change",
                "patch": {"op": "set", "target": "meta.title", "value": 42},
            }
        ]
    )
    with pytest.raises(ValueError, match="type"):
        apply_patches(data, log)


def test_apply_patches_set_auto_vivify_raises():
    """``set`` must not create a new key (no auto-vivify)."""
    data = _valid_doc()
    log = _make_log(
        [
            {
                "finding_id": "F-001",
                "decision": "revise",
                "detail": "new key",
                "patch": {"op": "set", "target": "meta.nonexistent_key", "value": "x"},
            }
        ]
    )
    with pytest.raises(ValueError, match="auto-vivify|does not exist"):
        apply_patches(data, log)


def test_apply_patches_set_on_content_sections_list_raises():
    """``set`` targeting ``content.sections`` (a list) must be rejected."""
    data = _valid_doc()
    log = _make_log(
        [
            {
                "finding_id": "F-001",
                "decision": "revise",
                "detail": "wholesale replace",
                "patch": {"op": "set", "target": "content.sections", "value": []},
            }
        ]
    )
    with pytest.raises(ValueError, match="leaf scalar"):
        apply_patches(data, log)


def test_apply_patches_unknown_op_raises():
    """An unrecognized op string raises ValueError."""
    data = _valid_doc()
    log = _make_log(
        [
            {
                "finding_id": "F-001",
                "decision": "revise",
                "detail": "bad op",
                "patch": {"op": "delete", "target": "meta.title", "value": None},
            }
        ]
    )
    with pytest.raises(ValueError, match="unknown op"):
        apply_patches(data, log)


def test_apply_patches_append_evidence_non_dict_raises():
    """append_evidence with a non-dict value raises ValueError."""
    data = _valid_doc()
    log = _make_log(
        [
            {
                "finding_id": "F-001",
                "decision": "add_evidence",
                "detail": "bad value",
                "patch": {"op": "append_evidence", "value": "not a dict"},
            }
        ]
    )
    with pytest.raises(ValueError, match="dict"):
        apply_patches(data, log)


# ---------------------------------------------------------------------------
# refine_structural_check
# ---------------------------------------------------------------------------


def test_refine_structural_check_passes_valid():
    """A valid doc dict passes refine_structural_check without raising."""
    refine_structural_check(_valid_doc())


def test_refine_structural_check_rejects_meta_non_dict():
    """A non-dict meta block raises ValueError."""
    data = _valid_doc()
    data["meta"] = "string"
    with pytest.raises(ValueError, match="meta"):
        refine_structural_check(data)


def test_refine_structural_check_rejects_content_non_dict():
    """A non-dict content block raises ValueError."""
    data = _valid_doc()
    data["content"] = []
    with pytest.raises(ValueError, match="content"):
        refine_structural_check(data)


def test_refine_structural_check_rejects_sections_non_list():
    """M8: Wholesale replacement of content.sections must be rejected."""
    data = _valid_doc()
    data["content"]["sections"] = {"replaced": True}
    with pytest.raises(ValueError, match="sections"):
        refine_structural_check(data)


def test_refine_structural_check_rejects_body_non_string():
    """M8: Type drift in section body (str → int) must be rejected."""
    data = _valid_doc()
    data["content"]["sections"][0]["body"] = 999
    with pytest.raises(ValueError, match="body"):
        refine_structural_check(data)


def test_refine_structural_check_rejects_empty_body():
    """An empty string body raises ValueError."""
    data = _valid_doc()
    data["content"]["sections"][0]["body"] = ""
    with pytest.raises(ValueError, match="body"):
        refine_structural_check(data)


def test_refine_structural_check_whitespace_only_body_raises():
    """A whitespace-only body string raises ValueError."""
    data = _valid_doc()
    data["content"]["sections"][0]["body"] = "   "
    with pytest.raises(ValueError, match="body"):
        refine_structural_check(data)


# ---------------------------------------------------------------------------
# snapshot_source (M9)
# ---------------------------------------------------------------------------


def test_snapshot_source_writes_byte_for_byte_copy(doc_dir):
    """snapshot_source produces a file with identical bytes to the source."""
    data_path = doc_dir / "document_data.yaml"
    content = yaml.safe_dump(_valid_doc(), sort_keys=False, allow_unicode=True)
    data_path.write_text(content, encoding="utf-8")
    snap = snapshot_source(data_path, doc_dir, version=1)
    assert snap.name == "document_data_pre_v1.yaml"
    assert snap.read_bytes() == data_path.read_bytes()


def test_snapshot_source_raises_if_snapshot_exists(doc_dir):
    """snapshot_source raises OverwriteError if the snapshot already exists."""
    data_path = doc_dir / "document_data.yaml"
    data_path.write_text("content", encoding="utf-8")
    snapshot_source(data_path, doc_dir, version=1)
    with pytest.raises(OverwriteError):
        snapshot_source(data_path, doc_dir, version=1)


# ---------------------------------------------------------------------------
# M3: byte-unchanged-on-abort
# ---------------------------------------------------------------------------


def test_apply_patches_abort_leaves_original_unchanged():
    """A bad patch raises without altering the original data."""
    data = _valid_doc()
    original = copy.deepcopy(data)
    log = _make_log(
        [
            {
                "finding_id": "F-001",
                "decision": "revise",
                "detail": "bad",
                "patch": {"op": "set", "target": "meta", "value": {}},
            }
        ]
    )
    with pytest.raises(ValueError):
        apply_patches(data, log)
    assert data == original


def test_commit_refine_raises_without_writing_on_structural_fail(doc_dir):
    """commit_refine halts before writing if refine_structural_check fails (M3)."""
    data_path = doc_dir / "document_data.yaml"
    original_content = yaml.safe_dump(_valid_doc(), sort_keys=False)
    data_path.write_text(original_content, encoding="utf-8")

    bad = _valid_doc()
    bad["content"]["sections"][0]["body"] = 999  # type drift → structural fail

    with pytest.raises(ValueError, match="body"):
        commit_refine(data_path, bad, force=True)

    assert data_path.read_text(encoding="utf-8") == original_content


def test_commit_refine_raises_without_writing_on_validate_fail(doc_dir):
    """commit_refine halts before writing if validate() fails (M3)."""
    data_path = doc_dir / "document_data.yaml"
    original_content = yaml.safe_dump(_valid_doc(), sort_keys=False)
    data_path.write_text(original_content, encoding="utf-8")

    bad = _valid_doc()
    bad["content"]["sections"][0]["body"] = "[[DDO::REQUIRES_INPUT: sentinel]]"

    with pytest.raises(ValidationError, match="REQUIRES_INPUT"):
        commit_refine(data_path, bad, force=True)

    assert data_path.read_text(encoding="utf-8") == original_content


# ---------------------------------------------------------------------------
# M4: validate-clean output
# ---------------------------------------------------------------------------


def test_commit_refine_produces_validate_clean_output(doc_dir):
    """Output written by commit_refine must pass validate() (M4)."""
    from ddo.validation import validate

    data_path = doc_dir / "document_data.yaml"
    data_path.write_text(yaml.safe_dump(_valid_doc(), sort_keys=False))

    patched = _valid_doc()
    patched["meta"]["title"] = "Patched Title"

    commit_refine(data_path, patched, force=True)

    written = yaml.safe_load(data_path.read_text(encoding="utf-8"))
    assert validate(written) is None
    assert written["meta"]["title"] == "Patched Title"


# ---------------------------------------------------------------------------
# M7: key-order preservation and snapshot fidelity
# ---------------------------------------------------------------------------


def test_commit_refine_preserves_key_order(doc_dir):
    """sort_keys=False must be used: key order in the output matches insertion order."""
    data_path = doc_dir / "document_data.yaml"
    # Write a doc with a specific key order
    doc = {
        "meta": {
            "doc_type": "prd",
            "title": "Order Test",
            "version": "0.0.1",
            "date": "2026.06.29",
            "template": "prd_default",
            "output_formats": ["pdf", "html", "md"],
        },
        "content": {
            "sections": [
                {
                    "id": "s1",
                    "title": "Sec",
                    "body": "Body text.",
                    "claims": [],
                    "evidence": ["ev-1"],
                }
            ]
        },
        "evidence_bank": [{"id": "ev-1", "type": "fact", "content": "fact", "source": "spec"}],
    }
    data_path.write_text(yaml.safe_dump(doc, sort_keys=False))

    patched = copy.deepcopy(doc)
    patched["meta"]["title"] = "Order Test Updated"

    commit_refine(data_path, patched, force=True)

    written_text = data_path.read_text(encoding="utf-8")
    # meta must appear before evidence_bank in key order
    assert written_text.index("meta:") < written_text.index("evidence_bank:")
    # Keys within meta: doc_type must appear before title (insertion order)
    assert written_text.index("doc_type:") < written_text.index("title:")


def test_snapshot_source_is_byte_identical(doc_dir):
    """Snapshot bytes must be bit-for-bit identical to the original (M7/M9)."""
    data_path = doc_dir / "document_data.yaml"
    # Write with sort_keys=False to ensure key-order is preserved in snapshot
    content = yaml.safe_dump(_valid_doc(), sort_keys=False, allow_unicode=True)
    data_path.write_text(content, encoding="utf-8")

    snap = snapshot_source(data_path, doc_dir, version=1)

    assert snap.read_bytes() == data_path.read_bytes()
