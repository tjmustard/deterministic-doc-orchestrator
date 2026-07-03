"""Anti-rot guard for the ``tutorials/`` tree (MiniPRD_AntiRotGuard_Hypergraph, v0.0.6).

Two independent guards, both driven by explicit in-repo maps rather than prose
parsing or filename pattern-matching (RT-02/13 — three tutorial naming schemes
coexist, so no name pattern is reliable):

1. ``EXPECTED_MIRRORS`` / ``STANDALONE`` — every ``tutorials/*/input_files/*.yaml``
   found by a directory walk must either be a byte-identical mirror of a real
   ``tests/data/`` or ``tests/fixtures/`` source, or be explicitly declared
   standalone. An unmapped, undeclared copy is a hard failure (RT-01/02/05).
2. ``OUTPUT_RENDERS`` — every committed Tutorial 2 ``output_files/*.{html,md}``
   must equal a fresh ``build.py`` render of its source input (RT-07). PDF
   snapshots are illustrative-only and are never byte-compared (RT-12).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_TUTORIALS_DIR = _REPO_ROOT / "tutorials"

# ---------------------------------------------------------------------------
# Guard 1: input_files/ mirrors (RT-01/02/05/13)
# ---------------------------------------------------------------------------

# {input_files copy (relative to repo root): source of truth (relative to repo root)}
EXPECTED_MIRRORS: dict[str, str] = {
    "tutorials/ddo-v001-prd-workflow/input_files/prd_example.yaml": "tests/data/prd_example.yaml",
    "tutorials/ddo-v006-evidence-bank-workflow/input_files/ingest_output.yaml": (
        "tests/fixtures/ingest_output.yaml"
    ),
    "tutorials/ddo-v006-authoring-custom-structures/input_files/blog_post_example.yaml": (
        "tests/data/blog_post_example.yaml"
    ),
    "tutorials/ddo-v006-authoring-custom-structures/input_files/meeting_notes_example.yaml": (
        "tests/data/meeting_notes_example.yaml"
    ),
    "tutorials/ddo-v006-authoring-custom-structures/input_files/meeting_agenda_example.yaml": (
        "tests/data/meeting_agenda_example.yaml"
    ),
    "tutorials/ddo-v006-authoring-custom-structures/input_files/project_report_example.yaml": (
        "tests/data/project_report_example.yaml"
    ),
}

# input_files/*.yaml that deliberately mirror nothing (hand-authored specimens).
STANDALONE: frozenset[str] = frozenset(
    {
        "tutorials/ddo-adversarial-loop-v0.0.2/input_files/document_data.yaml",
    }
)

_NEW_V006_EXAMPLE_SOURCES = {
    "tests/data/blog_post_example.yaml",
    "tests/data/meeting_notes_example.yaml",
    "tests/data/meeting_agenda_example.yaml",
    "tests/data/project_report_example.yaml",
}


def _walk_input_yamls() -> list[Path]:
    """Return every ``tutorials/*/input_files/*.yaml`` on disk, sorted."""
    return sorted(_TUTORIALS_DIR.glob("*/input_files/*.yaml"))


def test_expected_mirrors_is_non_empty() -> None:
    """A guard whose map is empty would pass while checking nothing (RT-01)."""
    assert EXPECTED_MIRRORS, "EXPECTED_MIRRORS must not be empty"


def test_expected_mirrors_includes_ingest_output() -> None:
    """Tutorial 1's fixture anchor must be a covered source (RT-01)."""
    assert "tests/fixtures/ingest_output.yaml" in EXPECTED_MIRRORS.values()


def test_expected_mirrors_includes_all_new_v006_examples() -> None:
    """The four new document-type examples must all be covered (RT-01)."""
    covered = set(EXPECTED_MIRRORS.values())
    missing = _NEW_V006_EXAMPLE_SOURCES - covered
    assert not missing, f"EXPECTED_MIRRORS is missing new v0.0.6 examples: {missing}"


@pytest.mark.parametrize(
    "input_path", _walk_input_yamls(), ids=lambda p: str(p.relative_to(_TUTORIALS_DIR))
)
def test_input_yaml_is_mapped_or_standalone(input_path: Path) -> None:
    """Every real ``input_files/*.yaml`` must be mapped or explicitly standalone (RT-02/05)."""
    rel = str(input_path.relative_to(_REPO_ROOT))
    assert rel in EXPECTED_MIRRORS or rel in STANDALONE, (
        f"{rel} is neither in EXPECTED_MIRRORS nor STANDALONE — an unmapped tutorial "
        "input is an unguarded drift surface. Add it to one of the two sets."
    )


@pytest.mark.parametrize("standalone_rel", sorted(STANDALONE))
def test_standalone_entry_exists(standalone_rel: str) -> None:
    """A declared-standalone entry must still exist on disk (renamed → loud failure, US-006)."""
    assert (_REPO_ROOT / standalone_rel).is_file(), (
        f"STANDALONE entry no longer exists: {standalone_rel} — it was renamed or removed; "
        "update STANDALONE (or EXPECTED_MIRRORS) to match"
    )


@pytest.mark.parametrize(
    "input_rel,source_rel",
    sorted(EXPECTED_MIRRORS.items()),
    ids=lambda v: v if isinstance(v, str) else "",
)
def test_mirrored_copy_is_byte_identical(input_rel: str, source_rel: str) -> None:
    """Each mapped copy must byte-match its declared source (RT-01/02)."""
    input_path = _REPO_ROOT / input_rel
    source_path = _REPO_ROOT / source_rel
    assert source_path.is_file(), f"EXPECTED_MIRRORS source does not exist: {source_rel}"
    assert input_path.is_file(), f"EXPECTED_MIRRORS input copy does not exist: {input_rel}"
    assert input_path.read_bytes() == source_path.read_bytes(), (
        f"{input_rel} has drifted from its source of truth {source_rel}"
    )


# ---------------------------------------------------------------------------
# Guard 2: output_files/ determinism (RT-07/12)
# ---------------------------------------------------------------------------

_T2_DIR = "tutorials/ddo-v006-authoring-custom-structures"

# {output_files/<file> (relative to repo root): (input yaml, template, format)}
OUTPUT_RENDERS: dict[str, tuple[str, str, str]] = {
    f"{_T2_DIR}/output_files/blog_post.html": (
        f"{_T2_DIR}/input_files/blog_post_example.yaml",
        "blog_post",
        "html",
    ),
    f"{_T2_DIR}/output_files/blog_post.md": (
        f"{_T2_DIR}/input_files/blog_post_example.yaml",
        "blog_post",
        "md",
    ),
    f"{_T2_DIR}/output_files/meeting_notes.html": (
        f"{_T2_DIR}/input_files/meeting_notes_example.yaml",
        "meeting_notes",
        "html",
    ),
    f"{_T2_DIR}/output_files/meeting_notes.md": (
        f"{_T2_DIR}/input_files/meeting_notes_example.yaml",
        "meeting_notes",
        "md",
    ),
    f"{_T2_DIR}/output_files/meeting_agenda.html": (
        f"{_T2_DIR}/input_files/meeting_agenda_example.yaml",
        "meeting_agenda",
        "html",
    ),
    f"{_T2_DIR}/output_files/meeting_agenda.md": (
        f"{_T2_DIR}/input_files/meeting_agenda_example.yaml",
        "meeting_agenda",
        "md",
    ),
    f"{_T2_DIR}/output_files/project_report.html": (
        f"{_T2_DIR}/input_files/project_report_example.yaml",
        "project_report",
        "html",
    ),
    f"{_T2_DIR}/output_files/project_report.md": (
        f"{_T2_DIR}/input_files/project_report_example.yaml",
        "project_report",
        "md",
    ),
}


def _render(
    data_path: Path, template: str, fmt: str, out_path: Path
) -> subprocess.CompletedProcess:
    """Render via the real ``uv run --locked ddo/build.py`` subprocess."""
    cmd = [
        "uv",
        "run",
        "--locked",
        "ddo/build.py",
        "--data",
        str(data_path),
        "--template",
        template,
        "--format",
        fmt,
        "--output",
        str(out_path),
    ]
    return subprocess.run(cmd, cwd=str(_REPO_ROOT), capture_output=True, text=True)


@pytest.mark.slow
@pytest.mark.parametrize("output_rel", sorted(OUTPUT_RENDERS), ids=lambda v: v.split("/")[-1])
def test_output_file_matches_fresh_render(output_rel: str, tmp_path: Path) -> None:
    """A committed text render must equal a fresh ``build.py`` render (RT-07).

    PDF snapshots are illustrative-only and intentionally excluded from
    ``OUTPUT_RENDERS`` (RT-07/12) — only ``.html``/``.md`` are byte-compared.
    """
    committed_path = _REPO_ROOT / output_rel
    data_rel, template, fmt = OUTPUT_RENDERS[output_rel]
    data_path = _REPO_ROOT / data_rel
    assert committed_path.is_file(), f"committed output missing: {output_rel}"
    assert data_path.is_file(), f"render input missing: {data_rel}"

    fresh_path = tmp_path / committed_path.name
    result = _render(data_path, template, fmt, fresh_path)
    assert result.returncode == 0, (
        f"fresh render of {output_rel} failed (exit {result.returncode}): {result.stderr}"
    )
    assert fresh_path.read_bytes() == committed_path.read_bytes(), (
        f"{output_rel} has drifted from a fresh build.py render — re-render and re-commit"
    )


def test_output_renders_never_includes_pdf() -> None:
    """PDF byte-equality is never asserted — illustrative-only (RT-07/12)."""
    assert not any(path.endswith(".pdf") for path in OUTPUT_RENDERS), (
        "OUTPUT_RENDERS must not byte-compare PDF snapshots (RT-12)"
    )


if __name__ == "__main__":  # pragma: no cover - manual invocation convenience
    sys.exit(pytest.main([__file__, "-v"]))
