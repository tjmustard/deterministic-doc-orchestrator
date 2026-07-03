#!/usr/bin/env python3
r"""Local sanity-check for a draft persona's Attack Vectors (AV) table.

This is a *convenience* script for use while drafting a persona with the
`ddo-create-persona` skill — it lets you eyeball AV-table structure before
running the authoritative suite:

    uv run pytest tests/unit/test_personas.py

It intentionally re-implements a small, read-only subset of the checks in
`tests/unit/test_personas.py` (which is the real gate; this script is not a
substitute for it and is never invoked by CI). Stdlib only, no third-party
Markdown parser, matching the project's convention in `test_personas.py`.

Usage:
    uv run tutorials/ddo-v006-writing-structured-personas/code_samples/check_persona_av_table.py \\
        ddo/personas/content_editor.md
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_AV_ID_RE = re.compile(r"^AV-(\d+)$")
_AV_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_SENTINEL_TOKENS = ("[REQUIRES USER INPUT:", "[[DDO::REQUIRES_INPUT:")


def parse_av_table(text: str) -> list[dict[str, str]]:
    """Return parsed rows from the ``## Attack Vectors`` table in *text*."""
    lines = text.splitlines()

    section_start: int | None = None
    for i, line in enumerate(lines):
        if re.match(r"^##\s+\**Attack Vectors\**\s*$", line.strip()):
            section_start = i
            break
    if section_start is None:
        return []

    header_idx: int | None = None
    for i in range(section_start + 1, len(lines)):
        line = lines[i]
        if re.match(r"^##", line):
            break
        if "|" in line and "ID" in line and "Name" in line and "When to apply" in line:
            header_idx = i
            break
    if header_idx is None:
        return []

    rows: list[dict[str, str]] = []
    i = header_idx + 1
    while i < len(lines):
        line = lines[i]
        i += 1
        if not line.startswith("|"):
            break
        if "-" in line and re.fullmatch(r"[\|\-\:\s]+", line.rstrip()):
            continue
        if not line.rstrip().endswith("|"):
            break
        parts = [c.strip() for c in line.split("|")[1:-1]]
        if len(parts) >= 3:
            rows.append(
                {
                    "id": parts[0],
                    "name": parts[1],
                    "when_to_apply": "|".join(parts[2:]),
                }
            )

    return rows


def check_persona(path: Path) -> list[str]:
    """Return a list of human-readable problems found in the persona at *path*.

    An empty list means the draft passed every local check.
    """
    problems: list[str] = []
    text = path.read_text(encoding="utf-8")

    for token in _SENTINEL_TOKENS:
        if token in text:
            problems.append(f"contains unfilled sentinel token {token!r}")

    if "## Attack Vectors" not in text:
        problems.append("missing '## Attack Vectors' section")
        return problems

    rows = parse_av_table(text)
    if not rows:
        problems.append("Attack Vectors section contains no parseable data rows")
        return problems

    ids = [r["id"] for r in rows]
    names = [r["name"] for r in rows]

    for av_id in ids:
        if not _AV_ID_RE.match(av_id):
            problems.append(f"ID {av_id!r} does not match AV-\\d+")

    if len(ids) != len(set(ids)):
        problems.append(f"duplicate AV IDs: {ids}")

    expected = [f"AV-{n:02d}" for n in range(1, len(ids) + 1)]
    if ids != expected:
        problems.append(f"IDs {ids} are not sequential from AV-01 (expected {expected})")

    for name in names:
        if r"\_" in name:
            problems.append(f"name {name!r} contains escaped underscore '\\_' — use raw '_'")
        if not _AV_NAME_RE.match(name):
            problems.append(f"name {name!r} does not match ^[a-z][a-z0-9_]*$")
        if "__" in name:
            problems.append(f"name {name!r} contains double underscore '__'")
        if name.endswith("_"):
            problems.append(f"name {name!r} ends with a trailing underscore")

    if len(names) != len(set(names)):
        problems.append(f"duplicate AV names: {names}")

    for row in rows:
        if not row["id"] or not row["name"] or not row["when_to_apply"]:
            problems.append(f"empty cell in row {row}")
        if "|" in row["when_to_apply"]:
            problems.append(f"ID {row['id']!r} 'When to apply' contains a literal '|'")

    return problems


def main() -> int:
    """Parse CLI args, run `check_persona`, and print a pass/fail summary."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("persona_path", type=Path, help="Path to a draft persona .md file")
    args = parser.parse_args()

    if not args.persona_path.exists():
        print(f"error: {args.persona_path} does not exist", file=sys.stderr)
        return 2

    problems = check_persona(args.persona_path)
    if not problems:
        print(f"{args.persona_path}: looks structurally sound (local check only).")
        print("Next: uv run pytest tests/unit/test_personas.py")
        return 0

    print(f"{args.persona_path}: {len(problems)} problem(s) found:")
    for problem in problems:
        print(f"  - {problem}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
