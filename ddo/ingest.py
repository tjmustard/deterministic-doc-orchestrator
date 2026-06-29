"""Deterministic, safety-critical write mechanics for the ``ddo-ingest`` skill.

The ``ddo-ingest`` skill is the **sole non-deterministic output** of DDO v0.0.1:
an LLM performs the cognitive source -> YAML mapping. This module owns the parts
that must NOT be left to a language model -- the write path that protects the
single piece of mutable state (``document_data.yaml``):

* :func:`atomic_write` enforces the **overwrite guard** (SuperPRD RT#11: never
  silently overwrite; non-interactive default is abort) and writes **atomically**
  (temp file in the same directory -> ``flush`` -> ``os.fsync`` -> ``os.replace``)
  so a crash can never leave a half-written source of truth.
* :func:`fabrication_tripwire` is the **advisory** zero-hallucination backstop
  (SuperPRD RT#5, claim split (B)): it surfaces date/number/proper-noun tokens
  that do not appear verbatim in any source, as a "verify these" list. It is
  best-effort -- it never raises and never blocks.

Path derivation is delegated to :mod:`ddo.paths` (the shared ``path_deriver``
atomic); this module never re-implements slug or containment logic.
"""

import os
import re
import tempfile
from pathlib import Path

from ddo.paths import assert_within_documents, document_dir

# --- Fabrication tripwire token grammar -----------------------------------
#
# Namespaced gap marker emitted by the skill for unfillable fields. Its inner
# text is intentional (a reason, not a fact) and is stripped out before any
# scan so reasons can mention dates/numbers without being flagged.
_GAP_MARKER_RE = re.compile(r"\[\[DDO::REQUIRES_INPUT:.*?\]\]", re.DOTALL)

# Month names (full or 3+ letter abbreviation) for natural-language dates.
_MONTH = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?"
    r"|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
)

# Date-shaped tokens: numeric (dotted/ISO/slash) and "Month D, YYYY" /
# "D Month YYYY" natural-language forms.
_DATE_RE = re.compile(
    r"\d{4}[./-]\d{1,2}[./-]\d{1,2}"  # 2026.06.27 / 2026-06-27 / 2026/06/27
    r"|\d{1,2}[./-]\d{1,2}[./-]\d{2,4}"  # 27/06/2026
    r"|" + _MONTH + r"\.?\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}"  # June 27, 2026
    r"|\d{1,2}(?:st|nd|rd|th)?\s+" + _MONTH + r"\.?\s+\d{4}"  # 27 June 2026
)

# Standalone numbers: optional currency/percent, grouping commas, decimals.
_NUMBER_RE = re.compile(r"\$?\d[\d,]*(?:\.\d+)?%?")

# Capitalized multi-word proper nouns (two or more consecutive Capitalized
# words), e.g. "Jane Doe", "Annalen der Physik" -> "Annalen" + "Physik" pair.
_PROPER_NOUN_RE = re.compile(r"[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)+")

# Whitespace runs collapse to a single space for verbatim comparison so a token
# split across YAML wrapping/indentation still matches its source.
_WS_RE = re.compile(r"\s+")


class OverwriteError(Exception):
    """Raised when :func:`atomic_write` would clobber an existing target.

    The overwrite guard fails closed: rather than silently destroying a
    version-controlled source of truth, the write is refused unless the caller
    explicitly passes ``force=True`` (the skill's ``--force``).
    """


def atomic_write(target: Path, content: str, *, force: bool = False) -> None:
    """Write ``content`` to ``target`` atomically, refusing silent overwrites.

    The write is crash-safe: ``content`` is written to a temporary file in the
    *same directory* as ``target``, flushed and ``os.fsync``-ed, then
    ``os.replace``-d onto ``target`` (an atomic rename on a single filesystem).
    A reader therefore observes either the old file or the fully written new one
    -- never a partial. The parent directory is created (``mkdir -p``) first. On
    any failure the temporary file is removed, so a partial ``target`` is never
    left behind.

    Args:
        target: Destination path (typically ``.../document_data.yaml``).
        content: Full text to write (UTF-8, written verbatim).
        force: If ``False`` (default) and ``target`` already exists, raise
            :class:`OverwriteError` and leave the existing file untouched. If
            ``True``, overwrite the existing file.

    Raises:
        OverwriteError: If ``target`` exists and ``force`` is ``False``.
    """
    target = Path(target)
    if target.exists() and not force:
        raise OverwriteError(
            f"refusing to overwrite existing file {target} without force=True "
            f"(pass --force to overwrite the source of truth)"
        )

    target.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_name = tempfile.mkstemp(
        dir=str(target.parent), prefix=f".{target.name}.", suffix=".tmp"
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, target)
    except BaseException:
        # Never leave a stray temp file; the original target is untouched
        # because the atomic rename had not yet happened.
        try:
            tmp_path.unlink()
        except OSError:
            pass
        raise


def fabrication_tripwire(yaml_text: str, source_texts: list[str]) -> list[str]:
    """Return date/number/proper-noun tokens not found verbatim in any source.

    A best-effort, **advisory** zero-hallucination backstop (SuperPRD RT#5). It
    scans the produced YAML for three classes of "fact-shaped" token -- dates,
    standalone numbers, and Capitalized multi-word proper nouns -- and returns
    the sorted, de-duplicated set of those that do not appear in *any* of
    ``source_texts``. Comparison is verbatim modulo collapsed whitespace.

    The namespaced ``[[DDO::REQUIRES_INPUT: ...]]`` gap markers are stripped
    before scanning: their inner reason text is intentional, not fabrication.

    This function is purely informational. It **never raises** and **never
    blocks** -- the returned list is a "verify these" prompt for the human at
    the review gate, not a guarantee.

    Args:
        yaml_text: The produced ``document_data.yaml`` text to scan.
        source_texts: Raw text of every local source the YAML was built from.

    Returns:
        Sorted, de-duplicated list of fact-shaped tokens absent from all
        sources. Empty if every scanned token traces to a source.
    """
    scrubbed = _GAP_MARKER_RE.sub(" ", yaml_text)

    candidates: set[str] = set()

    # Dates first; then blank them so their digits are not re-flagged as bare
    # numbers by the number pass.
    for match in _DATE_RE.finditer(scrubbed):
        token = match.group().strip()
        if token:
            candidates.add(token)
    date_blanked = _DATE_RE.sub(lambda m: " " * (m.end() - m.start()), scrubbed)

    for match in _NUMBER_RE.finditer(date_blanked):
        token = match.group().strip().strip(",")
        if token:
            candidates.add(token)

    for match in _PROPER_NOUN_RE.finditer(date_blanked):
        token = _WS_RE.sub(" ", match.group()).strip()
        if token:
            candidates.add(token)

    normalized_sources = [_WS_RE.sub(" ", source) for source in source_texts]

    unsourced = {
        token
        for token in candidates
        if not any(_WS_RE.sub(" ", token) in source for source in normalized_sources)
    }
    return sorted(unsourced)


def document_data_path(meta: dict) -> Path:
    """Compose the contained ``document_data.yaml`` path for a ``meta`` block.

    Convenience wrapper that joins :func:`ddo.paths.document_dir` with the
    canonical ``document_data.yaml`` filename and runs the result through
    :func:`ddo.paths.assert_within_documents`, so the returned path is
    guaranteed to live inside ``Documents/`` (fail closed otherwise).

    Args:
        meta: The document's ``meta`` mapping (``date``, ``doc_type``, ``title``).

    Returns:
        The resolved, containment-checked path to the document's
        ``document_data.yaml``.

    Raises:
        ddo.paths.PathContainmentError: If the derived path escapes ``Documents/``.
    """
    return assert_within_documents(document_dir(meta) / "document_data.yaml")
