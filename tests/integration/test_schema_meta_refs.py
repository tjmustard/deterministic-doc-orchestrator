"""Schema/example meta-reference integration tests (RT-08, RT-10).

For every shipped schema in ``ddo/schemas/*.yaml`` and every example document
in ``tests/data/*.yaml``, this module asserts that:

- a present ``meta.persona`` resolves to an existing ``ddo/personas/<stem>.md``;
- a present ``meta.style_profile`` resolves to an existing ``ddo/styles/<stem>.md``;
- the document's declared ``content.sections[*].id`` set is a subset of the
  section-id set declared by its own schema (resolved via
  ``meta.template``/``meta.doc_type``).

Files are discovered via glob, never hardcoded, so new document types enrolled
by later MiniPRDs are automatically covered (see MiniPRD_00_HarnessPrep).
"""

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMAS_DIR = REPO_ROOT / "ddo" / "schemas"
PERSONAS_DIR = REPO_ROOT / "ddo" / "personas"
STYLES_DIR = REPO_ROOT / "ddo" / "styles"
DATA_DIR = REPO_ROOT / "tests" / "data"

# Mirrors the persona/style stem-validation gate documented in
# ddo/skills/ddo-ingest.md and ddo/skills/ddo-interview.md ("validate the stem
# against ^[a-z][a-z0-9_]*$ before any Read"), applied here to every
# meta.persona / meta.style_profile value before it is resolved to a path.
_STEM_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def _discover_yaml_files() -> list[Path]:
    """Return every shipped schema and example YAML path.

    Returns:
        A sorted list of paths under ``ddo/schemas/`` and ``tests/data/``,
        globbed rather than hardcoded so new document types are auto-covered.
    """
    return sorted(SCHEMAS_DIR.glob("*.yaml")) + sorted(DATA_DIR.glob("*.yaml"))


def _load(path: Path) -> dict:
    """Load a YAML file into a plain dict.

    Args:
        path: Absolute path to the YAML file.

    Returns:
        The parsed YAML document as a dict.
    """
    return yaml.safe_load(path.read_text()) or {}


def _test_id(path: Path) -> str:
    """Build a stable, readable pytest parametrize id for a YAML path.

    Args:
        path: Absolute path to a discovered YAML file.

    Returns:
        The path relative to the repository root, as a POSIX string.
    """
    return path.relative_to(REPO_ROOT).as_posix()


def _schema_section_ids() -> dict[str, set[str]]:
    """Map each schema's template/doc_type key to its declared section-id set.

    Returns:
        A dict from every ``meta.template`` and ``meta.doc_type`` value found
        across ``ddo/schemas/*.yaml`` to that schema's set of
        ``content.sections[*].id`` values.
    """
    mapping: dict[str, set[str]] = {}
    for schema_path in sorted(SCHEMAS_DIR.glob("*.yaml")):
        doc = _load(schema_path)
        meta = doc.get("meta", {}) or {}
        section_ids = {s["id"] for s in doc.get("content", {}).get("sections", []) or []}
        for key in filter(None, (meta.get("template"), meta.get("doc_type"))):
            mapping[key] = section_ids
    return mapping


YAML_FILES = _discover_yaml_files()
SCHEMA_SECTION_IDS = _schema_section_ids()


@pytest.mark.parametrize("path", YAML_FILES, ids=_test_id)
def test_persona_reference_resolves(path):
    """meta.persona, when present, must resolve to ddo/personas/<stem>.md."""
    meta = _load(path).get("meta", {}) or {}
    persona = meta.get("persona")
    if not persona:
        pytest.skip(f"{_test_id(path)} has no meta.persona")

    assert _STEM_RE.match(persona), (
        f"{_test_id(path)}: meta.persona {persona!r} fails the stem gate {_STEM_RE.pattern!r}"
    )
    persona_file = PERSONAS_DIR / f"{persona}.md"
    assert persona_file.is_file(), (
        f"{_test_id(path)}: meta.persona {persona!r} does not resolve to "
        f"{persona_file.relative_to(REPO_ROOT)}"
    )


@pytest.mark.parametrize("path", YAML_FILES, ids=_test_id)
def test_style_profile_reference_resolves(path):
    """meta.style_profile, when present, must resolve to ddo/styles/<stem>.md."""
    meta = _load(path).get("meta", {}) or {}
    style_profile = meta.get("style_profile")
    if not style_profile:
        pytest.skip(f"{_test_id(path)} has no meta.style_profile")

    assert _STEM_RE.match(style_profile), (
        f"{_test_id(path)}: meta.style_profile {style_profile!r} fails the stem gate "
        f"{_STEM_RE.pattern!r}"
    )
    style_file = STYLES_DIR / f"{style_profile}.md"
    assert style_file.is_file(), (
        f"{_test_id(path)}: meta.style_profile {style_profile!r} does not resolve to "
        f"{style_file.relative_to(REPO_ROOT)}"
    )


@pytest.mark.parametrize("path", YAML_FILES, ids=_test_id)
def test_section_ids_subset_of_schema(path):
    """content.sections[*].id must be a subset of the schema's declared ids."""
    doc = _load(path)
    meta = doc.get("meta", {}) or {}
    key = meta.get("template") or meta.get("doc_type")
    if key not in SCHEMA_SECTION_IDS:
        pytest.skip(f"{_test_id(path)}: no schema found for template/doc_type {key!r}")

    declared = SCHEMA_SECTION_IDS[key]
    actual = {s["id"] for s in doc.get("content", {}).get("sections", []) or []}
    assert actual <= declared, (
        f"{_test_id(path)}: section ids {sorted(actual - declared)} are not declared by "
        f"schema {key!r} (declared: {sorted(declared)})"
    )
