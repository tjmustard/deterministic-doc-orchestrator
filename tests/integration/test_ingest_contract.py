"""M5: the ingest contract + render-ability test (human-fixture-gated).

``ddo-ingest`` is the sole non-deterministic (LLM-authored) output of DDO v0.0.1,
so its correctness is verified by a human at the HITL gate, not by content
equality (SuperPRD claim split (B), negative constraints). This test asserts only
that a *human-promoted* ingest output is contract-valid and renders to all three
formats -- never that its content matches anything.

No promoted ingest fixture exists yet (``tests/fixtures/`` holds only
``.gitkeep``; promotion requires a human sign-off via the fixture guard), so the
test skips with a precise reason rather than fabricating a stand-in.
"""

import pytest
import yaml

# A human promotes a verified ingest output to exactly this path with
# DDO_FIXTURE_SIGNOFF=1; until then the test skips.
_INGEST_FIXTURE_RELPATH = "tests/fixtures/ingest_output.yaml"

# template to use when rendering the promoted ingest fixture (matches its doc).
_INGEST_FIXTURE_TEMPLATE = "prd"


def test_ingest_contract_and_renderability(render, repo_root, tmp_path):
    """M5: a human-promoted ingest YAML passes validate() and renders all 3 formats.

    Asserts contract-validity and render-ability only -- never content equality
    (the ingest output is human-verified at the gate). Skips until the one-time
    human sign-off promotes ``tests/fixtures/ingest_output.yaml``.
    """
    fixture = repo_root / _INGEST_FIXTURE_RELPATH
    if not fixture.is_file():
        pytest.skip(
            f"no promoted ingest fixture at {_INGEST_FIXTURE_RELPATH}; this test "
            "activates only after the one-time human sign-off promotes a verified "
            "ddo-ingest output into tests/fixtures/ (DDO_FIXTURE_SIGNOFF=1). Agents "
            "must not fabricate this fixture."
        )

    from ddo.validation import validate

    data = yaml.safe_load(fixture.read_text(encoding="utf-8"))
    # Contract validity (no content equality): must not raise.
    assert validate(data) is None

    for fmt in ("pdf", "html", "md"):
        out = tmp_path / f"ingest.{fmt}"
        result = render(_INGEST_FIXTURE_TEMPLATE, fmt, fixture, out)
        assert result.returncode == 0, f"ingest fixture failed to render {fmt}: {result.stderr}"
        assert out.is_file() and out.stat().st_size > 0
