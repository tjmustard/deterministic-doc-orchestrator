"""Structural validator for DDO style profile files (``ddo/styles/*.md``).

Mirrors ``tests/unit/test_personas.py``: a glob-based parametrised suite that
enforces the style profile contract (MiniPRD_TestStyles, v0.0.5) — a title
heading, five required ``##`` sections, non-empty section bodies, and the
absence of unfilled sentinel tokens.

Uses stdlib ``re`` only — no third-party Markdown parser.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Discovery — glob-based, no hardcoded profile names
# ---------------------------------------------------------------------------
_STYLE_DIR = Path(__file__).resolve().parents[2] / "ddo" / "styles"
_STYLE_PATHS = sorted(_STYLE_DIR.glob("*.md"))

# ---------------------------------------------------------------------------
# Validation patterns
# ---------------------------------------------------------------------------
_TITLE_RE = re.compile(r"^# \*\*Style Profile:.+\*\*\s*$", re.MULTILINE)
_HEADING_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
_REQUIRED_SECTIONS = (
    "Register & Audience",
    "Voice & Person",
    "Sentence & Structure",
    "Diction",
    "Avoid",
)
_SENTINEL_TOKENS = ("[REQUIRES USER INPUT:", "[[DDO::REQUIRES_INPUT:")


# ---------------------------------------------------------------------------
# Section parser (stdlib re only — no third-party Markdown library)
# ---------------------------------------------------------------------------


def _extract_sections(text: str) -> dict[str, str]:
    """Return a mapping of ``## heading name`` -> stripped body text for *text*.

    A section's body is everything between its heading line and the start of
    the next ``##`` heading, or the end of the file if it is the last one.
    """
    matches = list(_HEADING_RE.finditer(text))
    sections: dict[str, str] = {}
    for i, m in enumerate(matches):
        name = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[name] = text[start:end].strip()
    return sections


# ---------------------------------------------------------------------------
# Guard: the styles directory must actually contain files
# ---------------------------------------------------------------------------


def test_style_dir_has_files() -> None:
    """The styles directory must contain at least one .md file."""
    assert _STYLE_PATHS, f"no style profile .md files found in {_STYLE_DIR}"


# ---------------------------------------------------------------------------
# Parametrised structural tests — one run per discovered style profile
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path", _STYLE_PATHS, ids=lambda p: p.stem)
def test_title_heading_present(path: Path) -> None:
    """Profile has a ``# **Style Profile: <name>**`` title heading."""
    text = path.read_text(encoding="utf-8")
    assert _TITLE_RE.search(text), (
        f"{path.name}: missing '# **Style Profile: <name>**' title heading"
    )


@pytest.mark.parametrize("path", _STYLE_PATHS, ids=lambda p: p.stem)
def test_required_sections_present(path: Path) -> None:
    """Profile has all five required ``##`` section headings."""
    sections = _extract_sections(path.read_text(encoding="utf-8"))
    for name in _REQUIRED_SECTIONS:
        assert name in sections, f"{path.name}: missing required '## {name}' section"


@pytest.mark.parametrize("path", _STYLE_PATHS, ids=lambda p: p.stem)
def test_section_bodies_nonempty(path: Path) -> None:
    """Every required section's body is non-empty once stripped."""
    sections = _extract_sections(path.read_text(encoding="utf-8"))
    for name in _REQUIRED_SECTIONS:
        assert name in sections, f"{path.name}: missing required '## {name}' section"
        assert sections[name], f"{path.name}: '## {name}' section body is empty"


@pytest.mark.parametrize("path", _STYLE_PATHS, ids=lambda p: p.stem)
def test_no_sentinel_tokens(path: Path) -> None:
    """Style profiles must not contain unfilled placeholder sentinel tokens."""
    text = path.read_text(encoding="utf-8")
    for token in _SENTINEL_TOKENS:
        assert token not in text, f"{path.name}: contains unfilled sentinel token {token!r}"


# ---------------------------------------------------------------------------
# Negative tests — verify parser and assertions correctly detect bad content
# ---------------------------------------------------------------------------


def _write_style(tmp_path: Path, name: str, content: str) -> Path:
    """Write *content* to ``tmp_path/<name>.md`` and return the path."""
    p = tmp_path / f"{name}.md"
    p.write_text(content, encoding="utf-8")
    return p


def test_negative_missing_heading(tmp_path: Path) -> None:
    """A profile missing a required '##' heading is caught by the section assertion."""
    content = (
        "# **Style Profile: bad**\n\n"
        "## Register & Audience\n\nSome text.\n\n"
        "## Voice & Person\n\nSome text.\n\n"
        "## Sentence & Structure\n\nSome text.\n\n"
        "## Diction\n\nSome text.\n"
        # 'Avoid' section intentionally omitted
    )
    p = _write_style(tmp_path, "bad_missing_heading", content)
    sections = _extract_sections(p.read_text(encoding="utf-8"))

    with pytest.raises(AssertionError):
        for name in _REQUIRED_SECTIONS:
            assert name in sections, f"missing required '## {name}' section"


def test_negative_empty_section_body(tmp_path: Path) -> None:
    """A profile with an empty (whitespace-only) section body is caught by the assertion."""
    content = (
        "# **Style Profile: bad**\n\n"
        "## Register & Audience\n\n\n\n"
        "## Voice & Person\n\nSome text.\n\n"
        "## Sentence & Structure\n\nSome text.\n\n"
        "## Diction\n\nSome text.\n\n"
        "## Avoid\n\nSome text.\n"
    )
    p = _write_style(tmp_path, "bad_empty_body", content)
    sections = _extract_sections(p.read_text(encoding="utf-8"))

    with pytest.raises(AssertionError):
        for name in _REQUIRED_SECTIONS:
            assert name in sections, f"missing required '## {name}' section"
            assert sections[name], f"'## {name}' section body is empty"


def test_negative_sentinel_token(tmp_path: Path) -> None:
    """A profile containing a sentinel token is detected by the no-sentinel assertion."""
    content = (
        "# **Style Profile: bad**\n\n"
        "## Register & Audience\n\n[REQUIRES USER INPUT: this field is unfilled]\n"
    )
    p = _write_style(tmp_path, "bad_sentinel", content)
    text = p.read_text(encoding="utf-8")

    with pytest.raises(AssertionError):
        for token in _SENTINEL_TOKENS:
            assert token not in text, f"sentinel token found: {token!r}"
