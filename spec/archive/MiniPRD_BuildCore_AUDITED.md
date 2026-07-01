# MiniPRD: build.py Core

**Hypergraph Node ID:** `build_orchestrator`
**Parent Node:** `ddo_pipeline`
**Implements (atomics):** `template_resolver`, `typst_renderer`, `jinja_renderer`
**Depends on:** `validation_gate`

## 1. The Confidence Mandate
- **Confidence Score:** 8/10.
- **Clarifying Questions (gated by the timestamp spike, not blocking):**
  1. Does `typst` (PyPI) expose creation-timestamp control in-process, or only via its vendored CLI entrypoint? Run the spike **first**; if neither is hermetic, de-scope `--timestamp` (US-003) with a decision record. The vendored CLI **counts as hermetic**.

## 2. Atomic User Stories
- **US-001:** As an author, I render a validated YAML to PDF/HTML/MD via one `uv run --locked` command.
- **US-003:** As an author, I pin the Typst creation timestamp via `--timestamp` for byte-identical PDFs (gated).
- **US-005 (consumer):** `build.py` accepts a fully-resolved `--output` and stays ignorant of the folder convention.

## 3. Implementation Plan (Task List)
- [ ] Create `ddo/build.py` with the PEP 723 header; pin `typst==`, `jinja2==`, `pyyaml==`; commit `uv.lock`.
- [ ] Add `argparse`: `--data`, `--template`, `--format {pdf,html,md}`, `--output`, optional `--timestamp`, optional `--timeout` (default 30).
- [ ] Load YAML; on parse error emit one precise message (no stack trace), exit nonzero.
- [ ] Call the importable `validate(data)` from `validation_gate`; exit nonzero on first failure.
- [ ] Implement `template_resolver`: `pdf→templates/typst/<T>.typst`; `{html,md}→templates/jinja2/<T>.<F>.jinja2`. Route **only** off CLI flags; never read `meta` for routing.
- [ ] Implement `jinja_renderer`: env with **autoescape on for `.html`**, `render(**data)`; never re-render a data string (no SSTI). Normalize output to LF + stripped trailing whitespace.
- [ ] Implement `typst_renderer`: in-process `typst` package call with `--font-path ddo/fonts/`; apply `--timestamp` when provided (**validate format/range**; bad value → precise error).
- [ ] Wrap render in a wall-clock **timeout** + output-size cap; on breach abort with a precise message.
- [ ] `mkdir -p` the `--output` parent (idempotent); write bytes; exit 0.
- [ ] Spike the timestamp path; record go/no-go result in the SuperPRD appendix.

## 4. The Negative Space (Constraints)
- **DO NOT** add a system-Typst or Pandoc dependency; in-process package only.
- **DO NOT** route off `meta.template`/`meta.output_formats` — CLI flags are authoritative.
- **DO NOT** duplicate the validation checks here — import them from `validation_gate`.
- **DO NOT** emit non-deterministic content; rely on bundled fonts + pinned deps.
- **DO NOT** let a slug/path escape `Documents/` — but path derivation lives in `skill_render`; `build.py` only trusts the resolved `--output` and never invents paths.

## 5. Integration Tests & Verification
- **Test 1 (Deterministic):** valid `prd` YAML + `--format html` twice → byte-identical output (`test_html_md_byte_identical`).
- **Test 2 (Deterministic):** valid YAML + `--format pdf` twice → text-layer-identical (`test_pdf_content_identical`); with same `--timestamp` → byte-identical (`test_pdf_timestamp_byte_identical`, gated).
- **Test 3 (Deterministic):** missing `--output` parent dir → created via `mkdir -p`, render succeeds.
- **Test 4 (Deterministic):** malformed `--timestamp` → nonzero exit + precise message.
