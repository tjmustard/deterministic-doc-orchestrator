"""Integration tests for archive_manager.py.

Covers the 4 deterministic scenarios from MiniPRD_ArchiveManager.md § 5.
"""

import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from archive_manager import archive_draft

# Filename pattern: YYYYMMDD_HHMMSS_ffffff_draft_<module_id>.md
ARCHIVE_PATTERN = re.compile(r"^\d{8}_\d{6}_\d{6}_draft_\w+\.md$")


def _make_draft(workspace: Path, module_id: str) -> Path:
    """Create active/draft_<module_id>.md and return its path."""
    active = workspace / "active"
    active.mkdir(parents=True, exist_ok=True)
    draft = active / f"draft_{module_id}.md"
    draft.write_text(f"# Draft for {module_id}\n", encoding="utf-8")
    return draft


# ---------------------------------------------------------------------------
# Test 1 (MiniPRD) — archive_draft moves the file to archive/
# ---------------------------------------------------------------------------


def test_archive_draft_moves_file(tmp_path: Path) -> None:
    """archive_draft() moves active/draft_novelty.md into archive/ and removes the source."""
    draft = _make_draft(tmp_path, "novelty")
    archive_draft("novelty", tmp_path)

    # Source must be gone.
    assert not draft.exists()

    # Exactly one file in archive/ matching the naming convention.
    archive_dir = tmp_path / "archive"
    assert archive_dir.is_dir()
    archived = list(archive_dir.iterdir())
    assert len(archived) == 1
    assert archived[0].name.endswith("_draft_novelty.md")


# ---------------------------------------------------------------------------
# Test 2 (MiniPRD) — two calls within the same second produce distinct files
# ---------------------------------------------------------------------------


def test_archive_draft_twice_no_collision(tmp_path: Path) -> None:
    """Two rapid archive_draft() calls produce two distinct files — no overwrite."""
    _make_draft(tmp_path, "novelty")
    archive_draft("novelty", tmp_path)

    # Recreate the draft and archive again.
    _make_draft(tmp_path, "novelty")
    archive_draft("novelty", tmp_path)

    archive_dir = tmp_path / "archive"
    archived = sorted(archive_dir.iterdir())
    assert len(archived) == 2
    assert archived[0].name != archived[1].name


# ---------------------------------------------------------------------------
# Test 3 (MiniPRD) — missing source file: INFO logged, no exception
# ---------------------------------------------------------------------------


def test_archive_draft_missing_file_no_exception(tmp_path: Path, capsys) -> None:
    """archive_draft() with no source file prints INFO and returns without error."""
    # Do NOT create a draft file.
    archive_draft("nonexistent", tmp_path)  # must not raise

    captured = capsys.readouterr()
    assert "INFO" in captured.out
    assert "nonexistent" in captured.out


def test_archive_draft_missing_file_no_archive_dir_created(tmp_path: Path) -> None:
    """archive_draft() with no source file does NOT create the archive/ directory."""
    archive_draft("nonexistent", tmp_path)
    # archive/ should not have been created — nothing to archive.
    assert not (tmp_path / "archive").exists()


# ---------------------------------------------------------------------------
# Test 4 (MiniPRD) — filename matches the microsecond-precision pattern
# ---------------------------------------------------------------------------


def test_archive_draft_filename_pattern(tmp_path: Path) -> None:
    """Archived filename matches YYYYMMDD_HHMMSS_ffffff_draft_<id>.md."""
    _make_draft(tmp_path, "novelty")
    archive_draft("novelty", tmp_path)

    archive_dir = tmp_path / "archive"
    archived = list(archive_dir.iterdir())
    assert len(archived) == 1
    assert ARCHIVE_PATTERN.match(archived[0].name), (
        f"Filename '{archived[0].name}' does not match expected pattern."
    )
