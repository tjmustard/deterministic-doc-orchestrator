"""RT#12: smoke test that the migrated persona stubs are well-formed.

The two personas (``product_critic``, ``scientific_reviewer``) are migrated into
``ddo/personas/`` for forward-compatibility with the deferred v0.0.2 adversarial
loop. They are not exercised by any v0.0.1 code path, so this is their only
coverage: each file must exist, be non-empty, decode as UTF-8 markdown, and -- if
it carries YAML frontmatter -- have frontmatter that parses.
"""

from pathlib import Path

import pytest
import yaml

_PERSONA_DIR = Path(__file__).resolve().parents[2] / "ddo" / "personas"
_PERSONA_NAMES = ["product_critic", "scientific_reviewer"]


def _parse_frontmatter(text: str):
    """Return parsed YAML frontmatter if the markdown opens with a ``---`` block.

    Args:
        text: The full persona markdown text.

    Returns:
        The parsed frontmatter mapping, or ``None`` when there is no leading
        ``---`` frontmatter block.
    """
    if not text.startswith("---"):
        return None
    _, _, after = text.partition("---")
    block, sep, _ = after.partition("\n---")
    assert sep, "frontmatter opened with --- but was never closed"
    return yaml.safe_load(block)


@pytest.mark.parametrize("name", _PERSONA_NAMES)
def test_persona_file_exists_and_nonempty(name):
    """Each persona markdown file exists and has meaningful content."""
    path = _PERSONA_DIR / f"{name}.md"
    assert path.is_file(), f"missing persona: {path}"
    assert path.stat().st_size > 0, f"empty persona: {path}"


@pytest.mark.parametrize("name", _PERSONA_NAMES)
def test_persona_is_well_formed_markdown(name):
    """Each persona decodes as UTF-8, reads as markdown, and (if any) frontmatter parses."""
    path = _PERSONA_DIR / f"{name}.md"
    text = path.read_text(encoding="utf-8")  # raises UnicodeDecodeError if not UTF-8

    assert text.strip(), "persona has no non-whitespace content"
    assert any(line.lstrip().startswith("#") for line in text.splitlines()), (
        "persona has no markdown heading"
    )

    frontmatter = _parse_frontmatter(text)
    if frontmatter is not None:
        assert isinstance(frontmatter, dict), "frontmatter must parse to a mapping"
