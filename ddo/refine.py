"""Mutation layer for the DDO adversarial loop (``ddo.refine``).

This module is the highest-risk code path in v0.0.2 — it is the only permitted
writer of ``document_data.yaml`` during the refine phase.  Every safety
guarantee lives here, in code, separate from the cognitive ``ddo-refine`` skill:

* :func:`parse_path` — hand-rolled, **never** ``eval``/``exec``.
* :func:`apply_patches` — **pure** (no I/O); constrained ``set`` (leaf-scalar,
  no auto-vivify, no type change).
* :func:`refine_structural_check` — refine-only guard complementing the
  importable :func:`ddo.validation.validate`.
* :func:`snapshot_source` — byte-for-byte copy of ``document_data.yaml``
  **before** any mutation (RT#2).
* :func:`commit_refine` — double-checks, serialises with
  ``safe_dump(sort_keys=False, allow_unicode=True)`` (RT#3), then
  ``atomic_write`` inside ``Documents/``.

No new runtime dependencies are added: ``pyyaml`` and the v0.0.1 primitives
(:mod:`ddo.ingest`, :mod:`ddo.paths`, :mod:`ddo.validation`) are sufficient.
"""

from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any

import yaml

from ddo.ingest import atomic_write
from ddo.paths import assert_within_documents
from ddo.validation import validate

# ---------------------------------------------------------------------------
# Path helper for pre-refine snapshots
# ---------------------------------------------------------------------------


def _snapshot_path(doc_dir: Path, version: int) -> Path:
    """Return the contained path for ``document_data_pre_vN.yaml``."""
    return assert_within_documents(
        doc_dir / "review_history" / f"document_data_pre_v{version}.yaml"
    )


# ---------------------------------------------------------------------------
# Path DSL parser (hand-rolled; NEVER eval/exec)
# ---------------------------------------------------------------------------

# Tokeniser: an IDENT segment, a dotted IDENT, or a bracketed non-negative INT.
_PATH_TOKEN_RE = re.compile(
    r"^([A-Za-z_][A-Za-z0-9_]*)"  # leading IDENT (first segment)
    r"(?:"
    r"\.([A-Za-z_][A-Za-z0-9_]*)"  # .IDENT
    r"|\[(\d+)\]"  # [INT] — non-negative only (no negatives, no slices)
    r")*$"
)

# Individual step pattern for iterative parsing
_STEP_RE = re.compile(r"\.([A-Za-z_][A-Za-z0-9_]*)|(?:^([A-Za-z_][A-Za-z0-9_]*)$)|\[(\d+)\]")


def parse_path(target: str) -> list[str | int]:
    r"""Parse a dot/bracket path expression into a list of keys/indices.

    Grammar (hand-rolled, never ``eval``/``exec``):

    .. code-block::

        path    := segment ( '.' segment | '[' index ']' )*
        segment := [A-Za-z_][A-Za-z0-9_]*
        index   := \d+   # non-negative integer only; no slices, no negatives

    Examples::

        parse_path("meta.title")            -> ["meta", "title"]
        parse_path("content.sections[2].body") -> ["content", "sections", 2, "body"]
        parse_path("evidence_bank")         -> ["evidence_bank"]

    Args:
        target: The path expression to parse.

    Returns:
        An ordered list of string keys and non-negative integer indices.

    Raises:
        ValueError: If the expression is empty, contains invalid characters,
            uses negative/slice indices, has consecutive separators, or
            otherwise does not match the grammar.
    """
    if not target or not isinstance(target, str):
        raise ValueError("parse_path: target must be a non-empty string")

    result: list[str | int] = []
    remaining = target

    # Consume the leading IDENT (mandatory first segment)
    m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)", remaining)
    if not m:
        raise ValueError(f"parse_path: path must start with an identifier (got {target!r})")
    result.append(m.group(1))
    remaining = remaining[m.end() :]

    while remaining:
        if remaining.startswith("."):
            # Dotted segment: .IDENT
            remaining = remaining[1:]
            m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)", remaining)
            if not m:
                raise ValueError(f"parse_path: expected identifier after '.' in {target!r}")
            result.append(m.group(1))
            remaining = remaining[m.end() :]
        elif remaining.startswith("["):
            # Bracketed index: [NON-NEG-INT]
            m = re.match(r"^\[(\d+)\]", remaining)
            if not m:
                # Could be a negative, slice, or non-integer
                raise ValueError(
                    f"parse_path: invalid bracket expression in {target!r} — "
                    f"only non-negative integer indices are allowed (got {remaining!r})"
                )
            result.append(int(m.group(1)))
            remaining = remaining[m.end() :]
        else:
            raise ValueError(f"parse_path: unexpected character {remaining[0]!r} in {target!r}")

    return result


# ---------------------------------------------------------------------------
# Leaf resolution
# ---------------------------------------------------------------------------


def _resolve_leaf(data: dict, segments: list[str | int]) -> tuple[dict | list, str | int]:
    """Traverse ``data`` via ``segments`` and return ``(parent, final_key)``.

    The traversal stops one step before the final key so the caller can inspect
    or replace the leaf value.

    Args:
        data: The root dict to traverse.
        segments: Parsed path segments from :func:`parse_path`.

    Returns:
        A ``(parent, final_key)`` tuple where ``parent[final_key]`` is the
        leaf node.

    Raises:
        ValueError: If any intermediate segment is missing, out-of-range, or
            not the expected container type.
    """
    if not segments:
        raise ValueError("_resolve_leaf: empty segment list")

    node: Any = data
    for seg in segments[:-1]:
        if isinstance(seg, int):
            if not isinstance(node, list):
                raise ValueError(
                    f"_resolve_leaf: expected list at index {seg}, got {type(node).__name__}"
                )
            if seg < 0 or seg >= len(node):
                raise ValueError(
                    f"_resolve_leaf: index {seg} is out of range (list length {len(node)})"
                )
            node = node[seg]
        else:
            if not isinstance(node, dict):
                raise ValueError(
                    f"_resolve_leaf: expected dict at key {seg!r}, got {type(node).__name__}"
                )
            if seg not in node:
                raise ValueError(
                    f"_resolve_leaf: key {seg!r} does not exist (auto-vivify is forbidden)"
                )
            node = node[seg]

    final = segments[-1]
    # Verify the parent container contains the final key/index
    if isinstance(final, int):
        if not isinstance(node, list):
            raise ValueError(
                f"_resolve_leaf: expected list for final index {final}, got {type(node).__name__}"
            )
        if final < 0 or final >= len(node):
            raise ValueError(
                f"_resolve_leaf: final index {final} is out of range (list length {len(node)})"
            )
    else:
        if not isinstance(node, dict):
            raise ValueError(
                f"_resolve_leaf: expected dict for final key {final!r}, got {type(node).__name__}"
            )
        if final not in node:
            raise ValueError(
                f"_resolve_leaf: key {final!r} does not exist (auto-vivify is forbidden)"
            )

    return node, final


# Scalar types that a ``set`` may target (leaf-scalar contract)
_SCALAR_TYPES = (str, int, float, bool, type(None))


# ---------------------------------------------------------------------------
# Pure patch application (no I/O)
# ---------------------------------------------------------------------------


def apply_patches(data: dict, log: dict) -> dict:
    """Apply all patches from an ``interview_log`` to a deep copy of ``data``.

    This function is **pure**: it performs no I/O and does not modify ``data``
    in-place.  It operates on a deep copy and returns the patched result.

    Supported ``op`` values:

    * ``"set"`` — replace an existing leaf scalar; the path must resolve to a
      scalar of the **same type** as the new value; auto-vivify, type changes,
      and non-scalar targets are hard errors.
    * ``"append_evidence"`` — append one entry to ``evidence_bank``.
    * ``"append_review_log"`` — append one record to ``meta.review_log``
      (creates the list if absent).

    ``patch`` is ``null`` (``None``) for ``acknowledge``/``dispute``/``defer``
    resolutions; these are skipped without error.

    ``skip_indices`` (optional): a set of zero-based resolution indices to
    skip (populated by the skill for skip-and-dependents handling).

    Args:
        data: The parsed ``document_data`` dict (source of truth snapshot).
        log: The parsed ``interview_log_vN.yaml`` dict.

    Returns:
        A deep copy of ``data`` with all patches applied.

    Raises:
        ValueError: On any patch error (missing path, type change, bad op,
            auto-vivify attempt, non-scalar ``set`` target).
    """
    patched = copy.deepcopy(data)
    resolutions = log.get("resolutions", [])

    for i, res in enumerate(resolutions):
        patch = res.get("patch")
        if patch is None:
            continue

        op = patch.get("op")
        target = patch.get("target")
        value = patch.get("value")

        if op == "set":
            if not isinstance(target, str):
                raise ValueError(
                    f"apply_patches: resolution[{i}].patch.target must be a string, "
                    f"got {type(target).__name__}"
                )
            segments = parse_path(target)
            parent, final_key = _resolve_leaf(patched, segments)
            existing = parent[final_key]

            # Leaf-scalar check: the existing value must be a scalar
            if not isinstance(existing, _SCALAR_TYPES):
                raise ValueError(
                    f"apply_patches: resolution[{i}] set target {target!r} is not a "
                    f"leaf scalar (got {type(existing).__name__}); "
                    f"structural replacements are not supported in v0.0.2"
                )

            # Type-preservation check: new value must be the same type as the existing value.
            # NoneType and str are distinct types — null→scalar or scalar→null is a type change.
            if type(existing) is not type(value):
                raise ValueError(
                    f"apply_patches: resolution[{i}] set at {target!r} would change "
                    f"type from {type(existing).__name__!r} to {type(value).__name__!r}; "
                    f"type changes are not permitted"
                )

            parent[final_key] = value

        elif op == "append_evidence":
            if not isinstance(value, dict):
                raise ValueError(
                    f"apply_patches: resolution[{i}] append_evidence value must be a "
                    f"dict, got {type(value).__name__}"
                )
            bank = patched.get("evidence_bank")
            if not isinstance(bank, list):
                raise ValueError(
                    f"apply_patches: resolution[{i}] append_evidence: evidence_bank "
                    f"is missing or not a list"
                )
            bank.append(value)

        elif op == "append_review_log":
            if not isinstance(patched.get("meta"), dict):
                raise ValueError(
                    f"apply_patches: resolution[{i}] append_review_log: meta block is missing"
                )
            review_log = patched["meta"].setdefault("review_log", [])
            if not isinstance(review_log, list):
                raise ValueError(
                    f"apply_patches: resolution[{i}] append_review_log: "
                    f"meta.review_log is not a list"
                )
            review_log.append(value)

        else:
            raise ValueError(
                f"apply_patches: resolution[{i}] unknown op {op!r}; "
                f"supported: set, append_evidence, append_review_log"
            )

    return patched


# ---------------------------------------------------------------------------
# Refine-only structural check (NOT in validation_gate; lives here)
# ---------------------------------------------------------------------------


def refine_structural_check(patched: dict) -> None:
    """Refine-only structural assertion complementing the importable ``validate()``.

    Guards against valid-but-corrupting patches that pass the minimal contract
    (SuperPRD RT#1):

    * ``content.sections`` must remain a list (no wholesale replacement).
    * Every section body must be a non-empty string (no type drift to dict/list).
    * ``meta`` must remain a dict; ``content`` must remain a dict.

    This check lives here, **not** in ``ddo.validation``, so ``validation_gate``
    remains unmodified (D5 preserved).

    Args:
        patched: The patched document dict (in-memory; no I/O performed).

    Raises:
        ValueError: On the first structural violation, naming the field.
    """
    meta = patched.get("meta")
    if not isinstance(meta, dict):
        raise ValueError("refine_structural_check: meta is not a dict after patching")

    content = patched.get("content")
    if not isinstance(content, dict):
        raise ValueError("refine_structural_check: content is not a dict after patching")

    sections = content.get("sections")
    if not isinstance(sections, list):
        raise ValueError(
            "refine_structural_check: content.sections is not a list after patching; "
            "wholesale section replacement is not supported in v0.0.2"
        )

    for i, section in enumerate(sections):
        if not isinstance(section, dict):
            raise ValueError(f"refine_structural_check: content.sections[{i}] is not a dict")
        body = section.get("body")
        if body is None:
            # body being absent is not caught here (validation.validate handles contract)
            continue
        if not isinstance(body, str):
            raise ValueError(
                f"refine_structural_check: content.sections[{i}].body is not a string "
                f"(got {type(body).__name__}); type drift is not permitted"
            )
        if not body.strip():
            raise ValueError(
                f"refine_structural_check: content.sections[{i}].body is empty or whitespace-only"
            )


# ---------------------------------------------------------------------------
# Snapshot (byte-for-byte copy, before any mutation)
# ---------------------------------------------------------------------------


def snapshot_source(data_path: Path, doc_dir: Path, version: int) -> Path:
    """Copy ``document_data.yaml`` byte-for-byte to ``document_data_pre_vN.yaml``.

    This snapshot is written **before** any mutation.  It is the recovery
    mechanism for a valid-but-wrong refine (SuperPRD RT#2 / M9).  Uses
    ``atomic_write`` for crash safety; ``force=False`` so a double-snapshot
    fails closed rather than clobbering a prior recovery point.

    Args:
        data_path: Absolute path to ``document_data.yaml`` (source of truth).
        doc_dir: The document's root directory.
        version: The refine version ``N``.

    Returns:
        The resolved, contained path to the snapshot file.

    Raises:
        ddo.ingest.OverwriteError: If the snapshot already exists.
        ddo.paths.PathContainmentError: If the path escapes ``Documents/``.
    """
    snap_path = _snapshot_path(doc_dir, version)
    content = data_path.read_bytes().decode("utf-8")
    atomic_write(snap_path, content, force=False)
    return snap_path


# ---------------------------------------------------------------------------
# Commit (double-check → safe_dump → atomic_write)
# ---------------------------------------------------------------------------


def commit_refine(data_path: Path, patched: dict, *, force: bool = True) -> Path:
    """Serialize and atomically write the patched dict to ``document_data.yaml``.

    Defensively re-runs :func:`refine_structural_check` and the importable
    :func:`ddo.validation.validate` in-memory before any write.  Serialises
    with ``yaml.safe_dump(sort_keys=False, allow_unicode=True)`` to preserve
    key insertion order (RT#3).  Writes via ``atomic_write`` with
    containment-asserted ``data_path`` (``force=True`` because the target
    legitimately exists).

    Args:
        data_path: The resolved, contained path to ``document_data.yaml``.
        patched: The post-patch dict (in-memory; not yet written).
        force: Always ``True`` in production (the file exists); exposed for
            testing.

    Returns:
        The path to the written file.

    Raises:
        ValueError: If the structural check fails.
        ddo.validation.ValidationError: If the importable validate() fails.
        ddo.paths.PathContainmentError: If ``data_path`` escapes ``Documents/``.
    """
    # Ensure containment before writing (defense-in-depth)
    safe_path = assert_within_documents(data_path)

    # Double-check: structural then contract
    refine_structural_check(patched)
    validate(patched)

    content = yaml.safe_dump(patched, sort_keys=False, allow_unicode=True)
    atomic_write(safe_path, content, force=force)
    return safe_path
