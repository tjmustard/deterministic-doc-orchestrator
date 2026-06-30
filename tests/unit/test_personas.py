"""Structural validator for DDO persona Attack Vector (AV) tables.

Replaces the RT#12 hardcoded smoke test with a glob-based parametrised suite
that enforces the full AV-table contract (MiniPRD_TestPersonas, v0.0.4).

Uses stdlib ``re`` only — no third-party Markdown parser.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Discovery — glob-based, no hardcoded persona names
# ---------------------------------------------------------------------------
_PERSONA_DIR = Path(__file__).resolve().parents[2] / "ddo" / "personas"
_PERSONA_PATHS = sorted(_PERSONA_DIR.glob("*.md"))

# ---------------------------------------------------------------------------
# Validation patterns
# ---------------------------------------------------------------------------
_AV_ID_RE = re.compile(r"^AV-(\d+)$")
_AV_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_SENTINEL_TOKENS = ("[REQUIRES USER INPUT:", "[[DDO::REQUIRES_INPUT:")


# ---------------------------------------------------------------------------
# Table parser (stdlib re only — no third-party Markdown library)
# ---------------------------------------------------------------------------


def _parse_av_table(text: str) -> list[dict[str, str]]:
    """Return parsed rows from the ``## Attack Vectors`` table in *text*.

    Each row is a dict with keys ``id``, ``name``, ``when_to_apply``.
    Returns an empty list when no Attack Vectors section or table is found.
    Extra cells beyond the third are joined back with ``|`` so any embedded
    pipe characters are preserved and remain detectable.
    """
    lines = text.splitlines()

    # Locate '## Attack Vectors' section (tolerates optional bold markers)
    section_start: int | None = None
    for i, line in enumerate(lines):
        if re.match(r"^##\s+\**Attack Vectors\**\s*$", line.strip()):
            section_start = i
            break
    if section_start is None:
        return []

    # Locate the table header row within the section
    header_idx: int | None = None
    for i in range(section_start + 1, len(lines)):
        line = lines[i]
        if re.match(r"^##", line):  # start of the next section — stop
            break
        if "|" in line and "ID" in line and "Name" in line and "When to apply" in line:
            header_idx = i
            break
    if header_idx is None:
        return []

    # Parse data rows; skip the separator row (|---|---|---|)
    rows: list[dict[str, str]] = []
    i = header_idx + 1
    while i < len(lines):
        line = lines[i]
        i += 1
        if not line.startswith("|"):
            break  # end of table
        # Separator row: contains a dash and consists solely of |, -, :, whitespace
        if "-" in line and re.fullmatch(r"[\|\-\:\s]+", line.rstrip()):
            continue
        if not line.rstrip().endswith("|"):
            break  # malformed row — stop parsing
        parts = [c.strip() for c in line.split("|")[1:-1]]
        if len(parts) >= 3:
            rows.append(
                {
                    "id": parts[0],
                    "name": parts[1],
                    # Join extra cells back with '|' so embedded pipes are visible
                    "when_to_apply": "|".join(parts[2:]),
                }
            )

    return rows


# ---------------------------------------------------------------------------
# Guard: the personas directory must actually contain files
# ---------------------------------------------------------------------------


def test_persona_dir_has_files() -> None:
    """The personas directory must contain at least one .md file."""
    assert _PERSONA_PATHS, f"no persona .md files found in {_PERSONA_DIR}"


# ---------------------------------------------------------------------------
# Parametrised structural tests — one run per discovered persona
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path", _PERSONA_PATHS, ids=lambda p: p.stem)
def test_av_table_exists(path: Path) -> None:
    """Persona has an ``## Attack Vectors`` section with a parseable table (req #1)."""
    text = path.read_text(encoding="utf-8")
    assert "## Attack Vectors" in text, f"{path.name}: missing '## Attack Vectors' section"
    rows = _parse_av_table(text)
    assert rows, f"{path.name}: Attack Vectors section contains no data rows"


@pytest.mark.parametrize("path", _PERSONA_PATHS, ids=lambda p: p.stem)
def test_av_ids(path: Path) -> None:
    r"""AV IDs match AV-\d+, start at AV-01, are sequential, and are unique (reqs #2-4)."""
    rows = _parse_av_table(path.read_text(encoding="utf-8"))
    assert rows, f"{path.name}: no AV rows to validate"

    ids = [r["id"] for r in rows]

    # Req #2 — ID format
    for av_id in ids:
        assert _AV_ID_RE.match(av_id), f"{path.name}: ID {av_id!r} does not match AV-\\d+"

    # Req #4 — uniqueness (checked before sequential so the error is clearer)
    assert len(ids) == len(set(ids)), f"{path.name}: duplicate AV IDs: {ids}"

    # Req #3 — sequential from AV-01, no gaps
    expected = [f"AV-{n:02d}" for n in range(1, len(ids) + 1)]
    assert ids == expected, (
        f"{path.name}: IDs {ids} are not sequential from AV-01 (expected {expected})"
    )


@pytest.mark.parametrize("path", _PERSONA_PATHS, ids=lambda p: p.stem)
def test_av_names(path: Path) -> None:
    """AV names satisfy format, contain no escaped underscores, and are unique (reqs #5-7)."""
    rows = _parse_av_table(path.read_text(encoding="utf-8"))
    assert rows, f"{path.name}: no AV rows to validate"

    names = [r["name"] for r in rows]

    for name in names:
        # Req #7 — raw underscores only (no backslash-escaped \_ in the cell)
        assert r"\_" not in name, (
            f"{path.name}: name {name!r} contains escaped underscore '\\_' — use raw '_'"
        )
        # Req #5 — must match base pattern (starts with lowercase letter)
        assert _AV_NAME_RE.match(name), (
            f"{path.name}: name {name!r} does not match ^[a-z][a-z0-9_]*$ "
            "(must start with a lowercase letter)"
        )
        # Req #5 extras — no double underscore, no trailing underscore
        assert "__" not in name, f"{path.name}: name {name!r} contains double underscore '__'"
        assert not name.endswith("_"), f"{path.name}: name {name!r} ends with a trailing underscore"

    # Req #6 — uniqueness
    assert len(names) == len(set(names)), f"{path.name}: duplicate AV names: {names}"


@pytest.mark.parametrize("path", _PERSONA_PATHS, ids=lambda p: p.stem)
def test_av_all_cells_nonempty(path: Path) -> None:
    """All three columns (ID, Name, When to apply) are non-empty for every row (req #9)."""
    rows = _parse_av_table(path.read_text(encoding="utf-8"))
    assert rows, f"{path.name}: no AV rows to validate"

    for row in rows:
        assert row["id"], f"{path.name}: empty ID cell in row {row}"
        assert row["name"], f"{path.name}: empty Name cell for ID {row['id']!r}"
        assert row["when_to_apply"], f"{path.name}: empty 'When to apply' cell for ID {row['id']!r}"


@pytest.mark.parametrize("path", _PERSONA_PATHS, ids=lambda p: p.stem)
def test_av_when_to_apply_no_pipe(path: Path) -> None:
    """'When to apply' cells must not contain a literal '|' character (req #8)."""
    rows = _parse_av_table(path.read_text(encoding="utf-8"))
    assert rows, f"{path.name}: no AV rows to validate"

    for row in rows:
        assert "|" not in row["when_to_apply"], (
            f"{path.name}: ID {row['id']!r} 'When to apply' contains a literal '|': "
            f"{row['when_to_apply']!r}"
        )


@pytest.mark.parametrize("path", _PERSONA_PATHS, ids=lambda p: p.stem)
def test_no_sentinel_tokens(path: Path) -> None:
    """Persona files must not contain unfilled placeholder sentinel tokens (req #10)."""
    text = path.read_text(encoding="utf-8")
    for token in _SENTINEL_TOKENS:
        assert token not in text, f"{path.name}: contains unfilled sentinel token {token!r}"


# ---------------------------------------------------------------------------
# Negative tests — verify parser and assertions correctly detect bad content
# ---------------------------------------------------------------------------


def _write_persona(tmp_path: Path, name: str, content: str) -> Path:
    """Write *content* to ``tmp_path/<name>.md`` and return the path."""
    p = tmp_path / f"{name}.md"
    p.write_text(content, encoding="utf-8")
    return p


def test_negative_sentinel_token(tmp_path: Path) -> None:
    """A persona containing a sentinel token is detected by the no-sentinel assertion."""
    content = (
        "# Persona: bad\n\n"
        "## Attack Vectors\n\n"
        "| ID    | Name      | When to apply |\n"
        "|-------|-----------|---------------|\n"
        "| AV-01 | good_name | Some context  |\n\n"
        "[REQUIRES USER INPUT: this field is unfilled]\n"
    )
    p = _write_persona(tmp_path, "bad_sentinel", content)
    text = p.read_text(encoding="utf-8")

    with pytest.raises(AssertionError):
        for token in _SENTINEL_TOKENS:
            assert token not in text, f"sentinel token found: {token!r}"


def test_negative_escaped_underscore(tmp_path: Path) -> None:
    r"""An escaped underscore (\\_) in a name cell is detected by the name assertion."""
    # '\\' in a Python string literal becomes a single backslash in the file
    content = (
        "# Persona: bad\n\n"
        "## Attack Vectors\n\n"
        "| ID    | Name          | When to apply |\n"
        "|-------|---------------|---------------|\n"
        "| AV-01 | bad\\_name    | Some context  |\n"
    )
    p = _write_persona(tmp_path, "bad_escaped", content)
    rows = _parse_av_table(p.read_text(encoding="utf-8"))
    assert rows, "parser must find rows in the synthetic persona"

    with pytest.raises(AssertionError):
        for row in rows:
            assert r"\_" not in row["name"], f"name {row['name']!r} contains escaped underscore"


def test_negative_nonsequential_ids(tmp_path: Path) -> None:
    """IDs that skip a number (AV-02, AV-04 no AV-03) are caught by the sequential assertion."""
    content = (
        "# Persona: bad\n\n"
        "## Attack Vectors\n\n"
        "| ID    | Name     | When to apply |\n"
        "|-------|----------|---------------|\n"
        "| AV-02 | foo_name | Some context  |\n"
        "| AV-04 | bar_name | Other context |\n"
    )
    p = _write_persona(tmp_path, "bad_nonseq", content)
    rows = _parse_av_table(p.read_text(encoding="utf-8"))
    assert rows, "parser must find rows in the synthetic persona"

    ids = [r["id"] for r in rows]
    expected = [f"AV-{n:02d}" for n in range(1, len(ids) + 1)]

    with pytest.raises(AssertionError):
        assert ids == expected, (
            f"non-sequential IDs {ids} should not equal sequential expected {expected}"
        )
