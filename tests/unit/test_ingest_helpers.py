"""Unit tests for the ``ddo-ingest`` deterministic helpers (:mod:`ddo.ingest`).

These cover the safety-critical mechanics the LLM never touches: the overwrite
guard, atomic-write integrity, and the advisory fabrication tripwire. The
integration-level ``test_ingest_contract_and_renderability`` (Wave 4) is
human-fixture-gated and lives elsewhere; it is intentionally not duplicated here.
"""

import pytest

from ddo.ingest import OverwriteError, atomic_write, fabrication_tripwire

# --- overwrite guard (IngestSkill Test 2) ---------------------------------


def test_overwrite_guard_raises_and_preserves_existing(tmp_path):
    """Without ``force``, an existing target is never overwritten or touched."""
    target = tmp_path / "document_data.yaml"
    target.write_text("original contents", encoding="utf-8")

    with pytest.raises(OverwriteError):
        atomic_write(target, "new contents")

    assert target.read_text(encoding="utf-8") == "original contents"


def test_overwrite_error_message_mentions_force(tmp_path):
    """The overwrite guard's message names ``force`` so the abort is precise."""
    target = tmp_path / "document_data.yaml"
    target.write_text("x", encoding="utf-8")

    with pytest.raises(OverwriteError, match="force"):
        atomic_write(target, "y")


def test_force_overwrites_existing(tmp_path):
    """With ``force=True`` the existing target is replaced by the new content."""
    target = tmp_path / "document_data.yaml"
    target.write_text("original contents", encoding="utf-8")

    atomic_write(target, "new contents", force=True)

    assert target.read_text(encoding="utf-8") == "new contents"


# --- atomicity ------------------------------------------------------------


def test_atomic_write_creates_file_with_exact_content(tmp_path):
    """A fresh write creates the file (and parents) with exactly the content."""
    target = tmp_path / "nested" / "dir" / "document_data.yaml"

    atomic_write(target, "meta:\n  title: Example\n")

    assert target.read_text(encoding="utf-8") == "meta:\n  title: Example\n"


def test_atomic_write_leaves_no_temp_files(tmp_path):
    """After a successful write only the target remains -- no stray temp files."""
    target = tmp_path / "document_data.yaml"

    atomic_write(target, "content")

    leftovers = [path.name for path in tmp_path.iterdir() if path != target]
    assert leftovers == []


def test_force_overwrite_leaves_no_temp_files(tmp_path):
    """A forced overwrite also cleans up its temp file (only target remains)."""
    target = tmp_path / "document_data.yaml"
    target.write_text("old", encoding="utf-8")

    atomic_write(target, "new", force=True)

    leftovers = [path.name for path in tmp_path.iterdir() if path != target]
    assert leftovers == []
    assert target.read_text(encoding="utf-8") == "new"


# --- fabrication tripwire (IngestSkill Test 3) ----------------------------


def test_tripwire_flags_unsourced_date_and_number():
    """A date and number present in the YAML but absent from sources are flagged."""
    yaml_text = "meta:\n  date: 2099.12.31\n  metric: 4242 widgets shipped\n"
    sources = ["The project began in 2020 with a team of 5 engineers."]

    flagged = fabrication_tripwire(yaml_text, sources)

    assert "2099.12.31" in flagged
    assert "4242" in flagged


def test_tripwire_does_not_flag_sourced_token():
    """A token present verbatim in a source is not flagged."""
    yaml_text = "meta:\n  founded: 2020\n  growth: 78%\n"
    sources = ["Our company was founded in 2020 and grew revenue by 78%."]

    flagged = fabrication_tripwire(yaml_text, sources)

    assert "2020" not in flagged
    assert "78%" not in flagged


def test_tripwire_flags_unsourced_proper_noun():
    """A Capitalized multi-word proper noun absent from sources is flagged."""
    yaml_text = "meta:\n  authors:\n    - Jane Doe\n"
    sources = ["The report was prepared by the internal research team."]

    flagged = fabrication_tripwire(yaml_text, sources)

    assert "Jane Doe" in flagged


def test_tripwire_never_flags_gap_marker_contents():
    """Tokens inside a ``[[DDO::REQUIRES_INPUT: ...]]`` marker are never flagged."""
    yaml_text = 'date: "[[DDO::REQUIRES_INPUT: launch date 2099.01.01 from Acme Corp unknown]]"\n'
    sources = ["unrelated source text with no overlapping facts"]

    flagged = fabrication_tripwire(yaml_text, sources)

    assert "2099.01.01" not in flagged
    assert "Acme Corp" not in flagged


def test_tripwire_returns_sorted_unique_list():
    """The result is sorted and de-duplicated, and never raises."""
    yaml_text = "a: 9999\nb: 9999\nc: 7777\n"
    sources = ["nothing here matches"]

    flagged = fabrication_tripwire(yaml_text, sources)

    assert flagged == sorted(set(flagged))
    assert flagged.count("9999") == 1


def test_tripwire_clean_yaml_returns_empty():
    """When every fact-shaped token traces to a source, the list is empty."""
    yaml_text = "founded: 2020\nrate: 78%\n"
    sources = ["Founded in 2020, the project reached a 78% adoption rate."]

    assert fabrication_tripwire(yaml_text, sources) == []
