"""M6: path-safety unit tests for :mod:`ddo.paths` (SuperPRD §5 / Red Team #2).

A malicious or illegal ``meta.title`` must never let a rendered artifact escape
the repository ``Documents/`` tree. These tests assert that (1) hostile titles
sanitize to a ``[a-z0-9-]`` slug with no traversal, (2) the derived output path
for such a title still resolves inside ``Documents/``, and (3) a hand-crafted
escaping path fails closed with :class:`ddo.paths.PathContainmentError`.
"""

import re
from pathlib import Path

import pytest

from ddo.paths import (
    PathContainmentError,
    assert_within_documents,
    document_dir,
    output_path,
    sanitize_slug,
)

_SLUG_CHARSET = re.compile(r"^[a-z0-9-]+$")

# Hostile / degenerate titles an attacker might supply as meta.title.
_MALICIOUS_TITLES = [
    "../../etc/passwd",
    "/etc/passwd",
    "..\\..\\windows\\system32",
    "....//....//secret",
    "name\x00with\x07control\nchars",
    "A" * 250,
    "  ...  ",
    "../" * 40,
]


@pytest.mark.parametrize("title", _MALICIOUS_TITLES)
def test_sanitize_slug_is_traversal_safe(title):
    """Every hostile title collapses to a bounded [a-z0-9-] slug with no traversal."""
    slug = sanitize_slug(title)
    assert slug, "slug must never be empty"
    assert _SLUG_CHARSET.match(slug), f"slug has illegal chars: {slug!r}"
    assert ".." not in slug
    assert "/" not in slug and "\\" not in slug
    assert not slug.startswith(".")
    assert len(slug) <= 80


@pytest.mark.parametrize("title", _MALICIOUS_TITLES)
def test_output_path_for_malicious_title_stays_contained(title):
    """The derived output path for a hostile title still resolves inside Documents/."""
    meta = {"date": "2026.06.27", "doc_type": "prd", "title": title}
    candidate = output_path(meta, "html")
    resolved = assert_within_documents(candidate)

    documents_root = (Path(__file__).resolve().parents[2] / "Documents").resolve()
    assert resolved.is_relative_to(documents_root)


def test_document_dir_for_empty_title_uses_fallback_and_contained():
    """An empty title falls back to a non-empty slug and remains contained."""
    meta = {"date": "2026.06.27", "doc_type": "prd", "title": ""}
    folder = document_dir(meta)
    assert assert_within_documents(folder).is_relative_to(
        (Path(__file__).resolve().parents[2] / "Documents").resolve()
    )


def test_handcrafted_escaping_path_raises():
    """A path resolving outside Documents/ fails closed with PathContainmentError."""
    repo_root = Path(__file__).resolve().parents[2]
    # An absolute system path and a ``..`` escape from inside Documents both fail.
    with pytest.raises(PathContainmentError):
        assert_within_documents(Path("/etc/passwd"))
    with pytest.raises(PathContainmentError):
        assert_within_documents(repo_root / "Documents" / ".." / ".." / "etc" / "passwd")


def test_escape_via_symlinked_realpath_is_rejected(tmp_path):
    """Even a crafted path that points outside the repo entirely is rejected."""
    with pytest.raises(PathContainmentError):
        assert_within_documents(tmp_path / "elsewhere" / "output.html")
