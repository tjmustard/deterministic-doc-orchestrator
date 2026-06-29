"""Unit tests for the DDO validation gate (:mod:`ddo.validation`)."""

import copy

import pytest

from ddo.validation import ValidationError, validate


def _valid_doc() -> dict:
    """Build a fresh, fully valid ``prd``-shaped document dictionary.

    Returns:
        A deep-copy-safe dict that passes :func:`validate` unmodified.
    """
    return {
        "meta": {
            "doc_type": "prd",
            "title": "Deterministic Doc Orchestrator",
            "version": "0.0.1",
            "date": "2026.06.27",
            "template": "prd_default",
            "output_formats": ["pdf", "html", "md"],
        },
        "content": {
            "sections": [
                {
                    "id": "intro",
                    "title": "Introduction",
                    "body": "The orchestrator transforms YAML into PDFs.",
                    "claims": ["deterministic output"],
                    "evidence": ["ev-1", "ev-2"],
                },
                {
                    "id": "details",
                    "title": "Details",
                    "body": "Pipeline phases are gated.",
                    "claims": [],
                    "evidence": ["ev-2"],
                },
            ]
        },
        "evidence_bank": [
            {"id": "ev-1", "type": "fact", "content": "YAML is source of truth", "source": "spec"},
            {"id": "ev-2", "type": "fact", "content": "HITL gates are mandatory", "source": "spec"},
        ],
    }


# --- pass paths -----------------------------------------------------------


def test_valid_doc_passes():
    """A complete, well-formed prd doc validates without raising."""
    assert validate(_valid_doc()) is None


def test_unknown_top_level_key_ignored():
    """Unknown top-level keys are accepted (forward-compat)."""
    doc = _valid_doc()
    doc["mutation_layer"] = {"future": "v0.0.2"}
    assert validate(doc) is None


def test_persona_optional():
    """``meta.persona`` is optional and its absence does not raise."""
    doc = _valid_doc()
    doc["meta"].pop("persona", None)
    assert validate(doc) is None


def test_requires_user_input_prose_passes():
    """Prose mentioning 'REQUIRES USER INPUT' without the token passes."""
    doc = _valid_doc()
    doc["content"]["sections"][0]["body"] = (
        "Historically authors wrote 'REQUIRES USER INPUT' as a note, but that "
        "is plain prose and must not trip the sentinel."
    )
    assert validate(doc) is None


def test_orphan_evidence_warns_but_passes():
    """An unreferenced evidence_bank entry warns but does not raise."""
    doc = _valid_doc()
    doc["evidence_bank"].append(
        {"id": "ev-orphan", "type": "fact", "content": "unused", "source": "spec"}
    )
    with pytest.warns(UserWarning, match="orphan"):
        result = validate(doc)
    assert result is None


# --- contract fail paths --------------------------------------------------


def test_missing_meta_raises():
    """A document without a ``meta`` block is rejected."""
    doc = _valid_doc()
    del doc["meta"]
    with pytest.raises(ValidationError, match="meta"):
        validate(doc)


def test_empty_title_raises():
    """An empty ``meta.title`` is rejected with a precise message."""
    doc = _valid_doc()
    doc["meta"]["title"] = ""
    with pytest.raises(ValidationError, match="meta.title"):
        validate(doc)


def test_missing_required_meta_key_raises():
    """A missing required ``meta`` key is rejected by name."""
    doc = _valid_doc()
    del doc["meta"]["template"]
    with pytest.raises(ValidationError, match="meta.template"):
        validate(doc)


def test_hyphenated_date_raises():
    """An ISO hyphenated date is rejected in favour of dotted format."""
    doc = _valid_doc()
    doc["meta"]["date"] = "2026-06-27"
    with pytest.raises(ValidationError, match="meta.date"):
        validate(doc)


def test_missing_evidence_bank_raises():
    """A missing ``evidence_bank`` array is rejected."""
    doc = _valid_doc()
    del doc["evidence_bank"]
    with pytest.raises(ValidationError, match="evidence_bank"):
        validate(doc)


def test_evidence_bank_not_a_list_raises():
    """An ``evidence_bank`` that is not a list is rejected."""
    doc = _valid_doc()
    doc["evidence_bank"] = {"id": "ev-1"}
    with pytest.raises(ValidationError, match="evidence_bank"):
        validate(doc)


# --- evidence integrity fail paths ---------------------------------------


def test_duplicate_evidence_id_raises():
    """A duplicate ``evidence_bank`` id is rejected, naming the id."""
    doc = _valid_doc()
    doc["evidence_bank"].append({"id": "ev-1", "type": "fact", "content": "dup", "source": "spec"})
    with pytest.raises(ValidationError, match="ev-1"):
        validate(doc)


def test_dangling_evidence_ref_raises():
    """A reference to a non-existent evidence id is rejected, naming the id."""
    doc = _valid_doc()
    doc["content"]["sections"][0]["evidence"].append("ev-missing")
    with pytest.raises(ValidationError, match="ev-missing"):
        validate(doc)


def test_contentless_no_sections_raises():
    """A document with zero sections is rejected as contentless."""
    doc = _valid_doc()
    doc["content"]["sections"] = []
    with pytest.raises(ValidationError, match="contentless"):
        validate(doc)


def test_contentless_no_evidence_refs_raises():
    """Sections present but with zero evidence references is contentless."""
    doc = _valid_doc()
    for section in doc["content"]["sections"]:
        section["evidence"] = []
    with pytest.raises(ValidationError, match="contentless"):
        validate(doc)


def test_missing_content_block_is_contentless():
    """A document lacking a ``content`` block entirely is contentless."""
    doc = _valid_doc()
    del doc["content"]
    with pytest.raises(ValidationError, match="contentless"):
        validate(doc)


# --- sentinel fail path ---------------------------------------------------


def test_sentinel_token_in_value_raises():
    """The namespaced sentinel token in a string value is rejected."""
    doc = _valid_doc()
    doc["content"]["sections"][0]["body"] = "[[DDO::REQUIRES_INPUT: launch metric]]"
    with pytest.raises(ValidationError, match="REQUIRES_INPUT"):
        validate(doc)


def test_sentinel_token_nested_in_evidence_bank_raises():
    """The sentinel is detected even when nested deep in evidence_bank."""
    doc = _valid_doc()
    doc["evidence_bank"][1]["content"] = "see [[DDO::REQUIRES_INPUT: citation]]"
    with pytest.raises(ValidationError, match="REQUIRES_INPUT"):
        validate(doc)


# --- ordering / determinism ----------------------------------------------


def test_first_failure_wins_contract_before_evidence():
    """Contract failures are reported before evidence-integrity failures."""
    doc = _valid_doc()
    doc["meta"]["title"] = ""  # contract failure
    doc["content"]["sections"][0]["evidence"].append("ev-missing")  # later failure
    with pytest.raises(ValidationError, match="meta.title"):
        validate(doc)


def test_validate_does_not_mutate_input():
    """``validate`` must not mutate the document it is handed."""
    doc = _valid_doc()
    snapshot = copy.deepcopy(doc)
    validate(doc)
    assert doc == snapshot
