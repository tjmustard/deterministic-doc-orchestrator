"""Shared, pure path-derivation helpers for the DDO rendering backbone.

This module is the ``path_deriver`` atomic (SuperPRD §5 "Path safety", Red Team
#2). It is deliberately side-effect free and CLI-agnostic so that both the
``ddo-render`` skill and the deferred ``ddo-ingest`` skill can import it to map a
document's ``meta`` block onto a safe, canonical location under ``Documents/``.

Two guarantees underpin every function here:

* **No escape.** A sanitized slug can contain only ``[a-z0-9-]`` -- never ``..``,
  a path separator, or a leading dot -- so it cannot traverse out of its folder.
* **Fail closed.** :func:`assert_within_documents` resolves the realpath and
  refuses (raising :class:`PathContainmentError`) anything that lands outside the
  repo's ``Documents/`` directory, even if an upstream value was hostile.

``Documents/`` is resolved relative to the repository root (the parent of this
file's ``ddo/`` package), never the caller's current working directory.
"""

import re
from pathlib import Path

# Canonical, host-stable filesystem charset for a slug. Anything else collapses
# to a single hyphen, which structurally forbids ``..`` and path separators.
_SLUG_DISALLOWED_RE = re.compile(r"[^a-z0-9]+")

# Hard length cap (Red Team #2) so a pathological title cannot blow the OS
# filename limit.
_SLUG_MAX_LEN = 80

# Non-empty fallback for empty/degenerate input so a folder name is never blank.
_FALLBACK_SLUG = "untitled"

# ``Documents/`` lives at the repo root: ``.../ddo/paths.py`` -> repo root is two
# parents up. Resolved per call against the realpath to defeat symlink escapes.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_DOCUMENTS_DIRNAME = "Documents"


class PathContainmentError(Exception):
    """Raised when a resolved path escapes the repository ``Documents/`` tree.

    The renderer/ingest skills must fail closed rather than write outside the
    sanctioned output area; this exception signals that breach.
    """


def sanitize_slug(title: str) -> str:
    """Reduce an arbitrary title to a safe, deterministic filename slug.

    The transform is: lowercase -> replace every run of characters outside
    ``[a-z0-9]`` (spaces, ``/``, dots, punctuation, and stray hyphens) with a
    single ``-`` -> strip leading/trailing ``-`` and any leading dots -> cap to
    80 characters. ``..`` is structurally impossible in the output, and an
    empty or degenerate input yields the non-empty fallback ``untitled``.

    Args:
        title: The raw ``meta.title`` value (or anything coercible to ``str``).

    Returns:
        A slug containing only ``[a-z0-9-]``, never empty, never containing
        ``..`` or a path separator.
    """
    text = title if isinstance(title, str) else str(title if title is not None else "")
    slug = _SLUG_DISALLOWED_RE.sub("-", text.lower())
    # Defensive: dots cannot survive the substitution above, but strip leading
    # dots explicitly to make the "no leading dot" guarantee self-evident.
    slug = slug.strip("-").lstrip(".")
    slug = slug[:_SLUG_MAX_LEN].strip("-")
    if not slug or ".." in slug or "/" in slug:
        return _FALLBACK_SLUG
    return slug


def document_dir(meta: dict) -> Path:
    """Compute the canonical document folder for a ``meta`` block.

    Layout (SuperPRD storage layout): ``Documents/<date>_<doc_type>_<slug>/``,
    where the slug is derived from ``meta.title`` via :func:`sanitize_slug`.

    Args:
        meta: The document's ``meta`` mapping (expects ``date``, ``doc_type``,
            ``title``; already structurally validated by the build gate).

    Returns:
        The (unresolved) folder path under ``Documents/``. Callers must pass the
        result through :func:`assert_within_documents` before any filesystem use.
    """
    date = str(meta.get("date", ""))
    doc_type = str(meta.get("doc_type", ""))
    slug = sanitize_slug(meta.get("title", ""))
    return _REPO_ROOT / _DOCUMENTS_DIRNAME / f"{date}_{doc_type}_{slug}"


def output_path(meta: dict, ext: str) -> Path:
    """Compute the rendered-artifact path for one output format.

    Layout: ``<document_dir>/output/<slug>.<ext>``. A leading dot on ``ext`` is
    tolerated (``"html"`` and ``".html"`` are equivalent).

    Args:
        meta: The document's ``meta`` mapping (see :func:`document_dir`).
        ext: The output extension, e.g. ``pdf``, ``html``, or ``md``.

    Returns:
        The (unresolved) output file path under the document folder. Callers
        must pass the result through :func:`assert_within_documents` first.
    """
    slug = sanitize_slug(meta.get("title", ""))
    clean_ext = str(ext).lstrip(".")
    return document_dir(meta) / "output" / f"{slug}.{clean_ext}"


def assert_within_documents(path: Path) -> Path:
    """Assert a path resolves inside the repo ``Documents/`` tree, fail closed.

    The realpath of both ``path`` and ``Documents/`` is computed (resolving
    symlinks and ``..``) and containment is checked structurally. This is the
    mandatory backstop against slug/path traversal (SuperPRD §5, Red Team #2):
    nothing is written until this passes.

    Args:
        path: The candidate output path (typically from :func:`output_path` or
            :func:`document_dir`).

    Returns:
        The resolved, contained path -- safe to hand to ``build.py`` as
        ``--output``.

    Raises:
        PathContainmentError: If the resolved path is not inside ``Documents/``.
    """
    documents_root = (_REPO_ROOT / _DOCUMENTS_DIRNAME).resolve()
    resolved = Path(path).resolve()
    if resolved != documents_root and not resolved.is_relative_to(documents_root):
        raise PathContainmentError(
            f"path escapes Documents/: {resolved} is not inside {documents_root}"
        )
    return resolved
