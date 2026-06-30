"""Integration test for the DDO adversarial loop: gap-closing pass (M5).

This test is **human-gated**: it skips unless the ``DDO_FIXTURE_SIGNOFF=1``
environment variable is set by a human reviewer.  The fixtures it requires
(``tests/fixtures/loop/document_data_with_gap.yaml`` and
``tests/fixtures/loop/interview_log_v1.yaml``) must be authored and promoted
by a human under the Candidate Artifact protocol — agents must never write
them (see ``scripts/fixture_signoff_guard.py``).

**What this test asserts (M5 observable):**

1. No ``[[DDO::REQUIRES_INPUT:...]]`` sentinel remains in the committed YAML.
2. The committed YAML passes :func:`ddo.validation.validate` (zero-hallucination
   and evidence-integrity clean).
3. ``ddo/build.py`` renders all three formats (pdf, html, md) from the committed
   YAML with exit code 0.

**What this test does NOT assert:**

- Semantic "the gap is correctly filled" — that is the human reviewer's
  responsibility at sign-off time.
- Anything about the :mod:`ddo.review` skill mediating the handoff — that
  boundary is verified in the human sign-off review, not in automated tests.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
import yaml

from ddo.refine import apply_patches, commit_refine, snapshot_source
from ddo.validation import validate

# ---------------------------------------------------------------------------
# Sign-off guard: skip unless a human has explicitly promoted the fixtures
# ---------------------------------------------------------------------------

_SIGNOFF_VAR = "DDO_FIXTURE_SIGNOFF"
_FIXTURES_LOOP = Path(__file__).resolve().parents[1] / "fixtures" / "loop"

_SIGNOFF_REASON = (
    f"human-gated test: set {_SIGNOFF_VAR}=1 and promote signed-off fixtures "
    f"into tests/fixtures/loop/ before this test can run"
)


def _fixtures_exist() -> bool:
    return (_FIXTURES_LOOP / "document_data_with_gap.yaml").is_file() and (
        _FIXTURES_LOOP / "interview_log_v1.yaml"
    ).is_file()


# ---------------------------------------------------------------------------
# The gap-closing test (M5)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not (os.environ.get(_SIGNOFF_VAR) == "1" and _fixtures_exist()),
    reason=_SIGNOFF_REASON,
)
def test_gap_closing_pass(tmp_path, repo_root):
    """M5: Gap-closing pass asserts sentinel-absence and 3-format render.

    Drives a seeded-gap document_data.yaml + signed-off interview_log through
    refine and asserts sentinel-absence + validate()-clean YAML + render ok for
    all three formats. The fixture files are human-authored and human-promoted;
    this test only confirms the M5 observable.
    """
    # --- Load signed-off fixtures -------------------------------------------
    gap_data_path = _FIXTURES_LOOP / "document_data_with_gap.yaml"
    log_path = _FIXTURES_LOOP / "interview_log_v1.yaml"

    data = yaml.safe_load(gap_data_path.read_text(encoding="utf-8"))
    log = yaml.safe_load(log_path.read_text(encoding="utf-8"))

    # --- Set up a temporary doc_dir that is visible to ddo.paths ------------
    # The test writes output into tmp_path/Documents/loop_test/
    import ddo.paths as _paths  # noqa: PLC0415

    doc_dir = tmp_path / "Documents" / "loop_test"
    doc_dir.mkdir(parents=True)

    # Monkeypatch _REPO_ROOT so assert_within_documents accepts our tmp dir.
    orig_repo_root = _paths._REPO_ROOT
    _paths._REPO_ROOT = tmp_path
    try:
        data_path = doc_dir / "document_data.yaml"
        data_path.write_text(
            yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8"
        )

        # --- Snapshot before mutation (RT#2 / M9) ---------------------------
        snapshot_source(data_path, doc_dir, version=1)

        # --- Apply patches from the interview log (pure, no I/O) ------------
        patched = apply_patches(data, log)

        # M5.1: No sentinel in the patched dict
        patched_text = yaml.safe_dump(patched, sort_keys=False, allow_unicode=True)
        assert "[[DDO::REQUIRES_INPUT:" not in patched_text, (
            "Sentinel [[DDO::REQUIRES_INPUT:...]] found in patched YAML; "
            "the gap-closing interview_log did not resolve all required fields."
        )

        # --- Commit the patched dict (double-validates internally) ----------
        commit_refine(data_path, patched, force=True)

        # M5.2: committed YAML passes validate() (zero-hallucination + evidence)
        committed = yaml.safe_load(data_path.read_text(encoding="utf-8"))
        validate(committed)  # raises ValidationError on failure

    finally:
        _paths._REPO_ROOT = orig_repo_root

    # M5.3: render all 3 formats via the real build.py
    meta = committed.get("meta", {})
    template = meta.get("template", "prd_default")

    for fmt in ("pdf", "html", "md"):
        out_path = tmp_path / f"loop_test_output.{fmt}"
        result = subprocess.run(
            [
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
            ],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"build.py failed for format {fmt!r}: {result.stderr}"
        assert out_path.is_file(), f"No output produced for format {fmt!r}"
        assert out_path.stat().st_size > 0, f"Empty output for format {fmt!r}"
