"""Deterministic validation gate for DDO ``document_data`` dictionaries.

This module is importable (not CLI-only): ``build.py`` and the deferred v0.0.2
loop both call :func:`validate` directly to pre-flight a parsed document before
any render. ``validate`` raises :class:`ValidationError` on the *first* failure
with a single, precise message naming the offending field or ID; it returns
``None`` on success.
"""

import re
import warnings

# Required ``meta`` keys per the DDO minimal contract (v0.0.1).
_REQUIRED_META_KEYS = ("doc_type", "title", "version", "date", "template", "output_formats")

# Dotted date format, e.g. ``2026.06.27`` (NOT ISO hyphens).
_DATE_RE = re.compile(r"^\d{4}\.\d{2}\.\d{2}$")

# Namespaced sentinel token left in place of unfilled source-traced content.
_SENTINEL_TOKEN = "[[DDO::REQUIRES_INPUT:"


class ValidationError(Exception):
    """Raised when a parsed document fails the validation gate.

    The message names the single offending field or ID for the first failure
    encountered; later potential failures are not reported.
    """


def _check_contract(data: dict) -> None:
    """Validate the structural contract of ``meta`` and ``evidence_bank``.

    Args:
        data: The parsed document dictionary.

    Raises:
        ValidationError: If ``meta`` is missing or not a dict, a required
            ``meta`` key is absent, ``title``/``version`` are not non-empty
            strings, ``meta.date`` is not dotted ``YYYY.MM.DD``, or
            ``evidence_bank`` is missing or not a list.
    """
    meta = data.get("meta")
    if meta is None:
        raise ValidationError("meta: required top-level block is missing")
    if not isinstance(meta, dict):
        raise ValidationError("meta: must be a mapping/dict")

    for key in _REQUIRED_META_KEYS:
        if key not in meta:
            raise ValidationError(f"meta.{key}: required key is missing")

    for key in ("title", "version"):
        value = meta[key]
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"meta.{key}: must be a non-empty string")

    date = meta["date"]
    if not isinstance(date, str) or not _DATE_RE.match(date):
        raise ValidationError(
            f"meta.date: must match dotted YYYY.MM.DD (e.g. 2026.06.27), got {date!r}"
        )

    if "evidence_bank" not in data:
        raise ValidationError("evidence_bank: required top-level array is missing")
    if not isinstance(data["evidence_bank"], list):
        raise ValidationError("evidence_bank: must be a list/array")


def _check_evidence_integrity(data: dict) -> None:
    """Validate evidence-bank uniqueness and reference integrity.

    Rejects duplicate ``evidence_bank`` IDs, dangling evidence references, and
    contentless documents (0 sections or 0 total evidence references). Orphan
    ``evidence_bank`` entries (never referenced) are warned about but do not
    raise.

    Args:
        data: The parsed document dictionary.

    Raises:
        ValidationError: On duplicate evidence IDs, a dangling reference, or a
            contentless document.
    """
    evidence_bank = data["evidence_bank"]

    bank_ids: set = set()
    for entry in evidence_bank:
        entry_id = entry.get("id") if isinstance(entry, dict) else None
        if entry_id in bank_ids:
            raise ValidationError(f"evidence_bank: duplicate id {entry_id!r}")
        bank_ids.add(entry_id)

    sections = (data.get("content") or {}).get("sections") or []

    referenced_ids: set = set()
    total_refs = 0
    for section in sections:
        refs = (section.get("evidence") or []) if isinstance(section, dict) else []
        for ref in refs:
            total_refs += 1
            referenced_ids.add(ref)
            if ref not in bank_ids:
                raise ValidationError(f"content.sections[*].evidence: dangling evidence id {ref!r}")

    if len(sections) == 0 or total_refs == 0:
        raise ValidationError(
            "content.sections: contentless document (0 sections or 0 evidence references)"
        )

    orphans = bank_ids - referenced_ids
    if orphans:
        warnings.warn(
            f"evidence_bank: orphan (unreferenced) ids {sorted(map(str, orphans))}",
            stacklevel=2,
        )


def _scan_sentinel(value: object, path: str = "") -> None:
    """Recursively scan parsed string *values* for the unfilled-input sentinel.

    Only string values are inspected. Dict keys, raw bytes, and comments are
    never scanned, per the zero-false-positive contract.

    Args:
        value: The current node (dict, list, str, or scalar) to walk.
        path: Dotted path to ``value`` for use in error messages.

    Raises:
        ValidationError: If ``[[DDO::REQUIRES_INPUT:`` appears in any string
            value.
    """
    if isinstance(value, str):
        if _SENTINEL_TOKEN in value:
            raise ValidationError(
                f"{path or '<root>'}: unfilled sentinel {_SENTINEL_TOKEN} present in value"
            )
    elif isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            _scan_sentinel(child, child_path)
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _scan_sentinel(child, f"{path}[{index}]")


def validate(data: dict) -> None:
    """Validate a parsed DDO document, raising on the first failure.

    Runs three ordered checks and stops at the first failure: (1) structural
    contract of ``meta`` and ``evidence_bank``; (2) evidence-bank uniqueness
    and reference integrity (orphans warn, not fail); (3) sentinel scan of all
    parsed string values for ``[[DDO::REQUIRES_INPUT:``.

    Unknown top-level keys are ignored for forward-compat. ``meta.persona`` is
    optional.

    Args:
        data: The parsed ``document_data`` dictionary.

    Raises:
        ValidationError: On the first contract, evidence-integrity, or sentinel
            failure; the message names the offending field or ID.
    """
    _check_contract(data)
    _check_evidence_integrity(data)
    _scan_sentinel(data)
