"""End-to-end render-determinism tests (M1, M2, M3, M3b, M4) via the real build.py.

Every test invokes ``uv run --locked ddo/build.py`` through the ``render``
fixture, so the pinned PEP 723 lockfile is enforced. The core determinism
assertions are self-contained (render-twice-and-compare) and pass with no
human-promoted golden fixture; the optional golden-baseline regression lives in
``test_renders_match_promoted_golden`` and skips gracefully until a human
promotes baselines into ``tests/fixtures/``.
"""

import filecmp
import hashlib

import pytest
import yaml

# (template name, input-YAML basename) for each shipped example document. Defined
# locally so this module is self-contained at collection time.
EXAMPLES = [
    ("prd", "prd_example.yaml"),
    ("scientific_report", "scientific_report_example.yaml"),
]

# Fixed UNIX-seconds timestamp (2024-06-27T00:00:00Z) for byte-identical PDFs.
_PINNED_TIMESTAMP = 1719446400

# Golden baselines a human may later promote into tests/fixtures/.
_FIXTURES_DIRNAME = "fixtures"


def _normalize(raw: bytes) -> bytes:
    """Normalise text bytes to LF endings with trailing whitespace stripped.

    Args:
        raw: Raw file bytes from a rendered HTML/MD artifact.

    Returns:
        Host-agnostic UTF-8 bytes: every line right-stripped, joined with LF,
        with a single trailing LF when non-empty.
    """
    text = raw.decode("utf-8")
    normalized = "\n".join(line.rstrip() for line in text.splitlines())
    if normalized:
        normalized += "\n"
    return normalized.encode("utf-8")


def _pdf_text(pdf_path) -> str:
    """Extract the concatenated text layer from a PDF.

    Args:
        pdf_path: Path to the rendered PDF.

    Returns:
        The text of every page joined with LF (the content-identity surface for
        M3; byte identity is asserted separately under a pinned timestamp).
    """
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


# --- M1: every example renders to every format -----------------------------


@pytest.mark.parametrize("template,basename", EXAMPLES)
@pytest.mark.parametrize("fmt", ["pdf", "html", "md"])
def test_examples_render_all_formats(render, example_path, tmp_path, template, basename, fmt):
    """M1: both example docs render to pdf/html/md with exit 0 and non-empty output."""
    out = tmp_path / f"{template}.{fmt}"
    result = render(template, fmt, example_path(basename), out)

    assert result.returncode == 0, f"build failed ({fmt}): {result.stderr}"
    assert out.is_file(), f"no output produced for {template} {fmt}"
    assert out.stat().st_size > 0, f"empty output for {template} {fmt}"


# --- M2: HTML/MD renders are byte-identical across runs (normalized) --------


@pytest.mark.parametrize("template,basename", EXAMPLES)
@pytest.mark.parametrize("fmt", ["html", "md"])
def test_html_md_byte_identical(render, example_path, tmp_path, template, basename, fmt):
    """M2: rendering the same doc twice yields byte-identical normalized output."""
    data = example_path(basename)
    first = tmp_path / f"first.{fmt}"
    second = tmp_path / f"second.{fmt}"

    r1 = render(template, fmt, data, first)
    r2 = render(template, fmt, data, second)
    assert r1.returncode == 0, r1.stderr
    assert r2.returncode == 0, r2.stderr

    norm_first = _normalize(first.read_bytes())
    norm_second = _normalize(second.read_bytes())
    assert norm_first == norm_second, f"{template} {fmt} not deterministic across runs"


# --- M3: PDF renders are text-layer-identical across runs (wall clock) ------


@pytest.mark.parametrize("template,basename", EXAMPLES)
def test_pdf_content_identical(render, example_path, tmp_path, template, basename):
    """M3: two wall-clock PDF renders share an identical text layer (text + sha256)."""
    data = example_path(basename)
    first = tmp_path / "first.pdf"
    second = tmp_path / "second.pdf"

    r1 = render(template, "pdf", data, first)
    r2 = render(template, "pdf", data, second)
    assert r1.returncode == 0, r1.stderr
    assert r2.returncode == 0, r2.stderr

    text_first = _pdf_text(first)
    text_second = _pdf_text(second)
    assert text_first, f"{template} produced an empty PDF text layer"
    assert text_first == text_second, f"{template} PDF text layer differs across runs"

    sha_first = hashlib.sha256(text_first.encode("utf-8")).hexdigest()
    sha_second = hashlib.sha256(text_second.encode("utf-8")).hexdigest()
    assert sha_first == sha_second


# --- M3b: same --timestamp yields byte-identical PDFs (spike GO) ------------


@pytest.mark.parametrize("template,basename", EXAMPLES)
def test_pdf_timestamp_byte_identical(render, example_path, tmp_path, template, basename):
    """M3b: two PDF renders with the same --timestamp are byte-for-byte identical."""
    data = example_path(basename)
    first = tmp_path / "ts_first.pdf"
    second = tmp_path / "ts_second.pdf"

    r1 = render(template, "pdf", data, first, timestamp=_PINNED_TIMESTAMP)
    r2 = render(template, "pdf", data, second, timestamp=_PINNED_TIMESTAMP)
    assert r1.returncode == 0, r1.stderr
    assert r2.returncode == 0, r2.stderr

    assert filecmp.cmp(first, second, shallow=False), (
        f"{template} pinned-timestamp PDFs are not byte-identical"
    )
    assert first.read_bytes() == second.read_bytes()


# --- M4: HTML autoescape prevents script-tag injection ----------------------


def test_html_autoescape_script_tag(render, tmp_path):
    """M4: <script> in body content must be HTML-escaped, not rendered verbatim."""
    data = {
        "meta": {
            "doc_type": "prd",
            "title": "Autoescape Test",
            "version": "1.0",
            "date": "2026.06.29",
            "template": "prd",
            "output_formats": ["html"],
        },
        "evidence_bank": [
            {"id": "ev-1", "type": "test", "source": "test", "content": "test content"}
        ],
        "content": {
            "sections": [
                {
                    "id": "s1",
                    "title": "Section",
                    "body": "<script>alert(1)</script>",
                    "evidence": ["ev-1"],
                }
            ]
        },
    }
    yaml_path = tmp_path / "autoescape_test.yaml"
    yaml_path.write_text(yaml.dump(data))
    out = tmp_path / "autoescape_test.html"

    result = render("prd", "html", yaml_path, out)
    assert result.returncode == 0, f"render failed: {result.stderr}"

    html = out.read_text()
    assert "<script>" not in html, "Raw <script> tag must not appear in HTML output"
    assert "&lt;script&gt;" in html, "Escaped &lt;script&gt; must appear in HTML output"


# --- Golden-baseline regression (human-promoted fixtures only) --------------


def _promoted_goldens(repo_root):
    """Return the list of promoted golden baseline paths under tests/fixtures/.

    Args:
        repo_root: The repository root path.

    Returns:
        A list of ``(template, fmt, data_basename, golden_path)`` tuples for the
        golden files that currently exist (html/md content, pdf text layer).
    """
    fixtures = repo_root / "tests" / _FIXTURES_DIRNAME
    found = []
    for template, basename in EXAMPLES:
        stem = basename.rsplit(".", 1)[0]
        for fmt, suffix in (("html", ".html"), ("md", ".md"), ("pdf", ".pdf.txt")):
            golden = fixtures / f"{stem}{suffix}"
            if golden.is_file():
                found.append((template, fmt, basename, golden))
    return found


def test_renders_match_promoted_golden(render, example_path, repo_root, tmp_path):
    """Regression: fresh renders equal the human-promoted golden baselines.

    Skips until a human signs off and promotes baselines into ``tests/fixtures/``
    (agents must never write fixtures; see scripts/fixture_signoff_guard.py).
    """
    goldens = _promoted_goldens(repo_root)
    if not goldens:
        pytest.skip(
            "no promoted golden baselines in tests/fixtures/ yet; this regression "
            "activates only after a human signs off (DDO_FIXTURE_SIGNOFF=1) and "
            "promotes the normalized HTML/MD and PDF-text baselines"
        )

    for template, fmt, basename, golden in goldens:
        out = tmp_path / f"{template}.{fmt}.out"
        result = render(template, fmt, example_path(basename), out)
        assert result.returncode == 0, result.stderr
        if fmt == "pdf":
            produced = _pdf_text(out).encode("utf-8")
            expected = _normalize(golden.read_bytes())
            produced = _normalize(produced)
        else:
            produced = _normalize(out.read_bytes())
            expected = _normalize(golden.read_bytes())
        assert produced == expected, f"{golden} drift detected for {template} {fmt}"
