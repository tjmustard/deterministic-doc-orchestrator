"""Reference sketch for the evidence-bank / citation-integrity lens.

This is a read-only inspection script, not a mutation tool — it never writes
`document_data.yaml`. It loads `input_files/ingest_output.yaml` (a teaching
mirror of the human-promoted `tests/fixtures/ingest_output.yaml`) and:

1. Maps every `content.sections[*].evidence` reference to its `evidence_bank`
   entry, printing the citation graph.
2. Calls the real, importable `ddo.validation.validate(...)` gate — the same
   function `build.py` runs before any render — to show it accepting a clean
   document and rejecting one with a dangling evidence reference.

Run with: ``uv run tutorials/ddo-v006-evidence-bank-workflow/code_samples/inspect_evidence_bank.py``
"""

from __future__ import annotations

import copy
from pathlib import Path

import yaml

from ddo.validation import ValidationError, validate

_FIXTURE = Path(__file__).parent.parent / "input_files" / "ingest_output.yaml"


def load_document() -> dict:
    """Load the teaching-mirror fixture as a parsed dict."""
    return yaml.safe_load(_FIXTURE.read_text(encoding="utf-8"))


def print_citation_graph(data: dict) -> None:
    """Print each section's evidence references alongside their bank entries."""
    bank_by_id = {entry["id"]: entry for entry in data["evidence_bank"]}
    for section in data["content"]["sections"]:
        print(f"\n[{section['id']}] {section['title']}")
        for ref in section.get("evidence", []):
            entry = bank_by_id[ref]  # KeyError here would mean a dangling ref.
            print(f"  -> {ref} ({entry['type']}): {entry['source']}")


def demonstrate_dangling_ref_rejection(data: dict) -> None:
    """Show that ``validate()`` rejects a reference to a nonexistent bank id."""
    broken = copy.deepcopy(data)
    broken["content"]["sections"][0]["evidence"].append("ev-does-not-exist")
    try:
        validate(broken)
    except ValidationError as exc:
        print(f"\nRejected dangling reference as expected: {exc}")
    else:  # pragma: no cover - defensive; should never happen
        raise AssertionError("Expected a ValidationError for a dangling evidence id")


def main() -> None:
    """Load the fixture, print its citation graph, then confirm both gates."""
    data = load_document()
    print_citation_graph(data)

    # The clean, unmodified document passes the same gate build.py runs.
    validate(data)
    print("\nClean document passed validate() — every claim traces to a source.")

    demonstrate_dangling_ref_rejection(data)


if __name__ == "__main__":
    main()
