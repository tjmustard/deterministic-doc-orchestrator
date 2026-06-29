
# Product Context
## Purpose
This file contains the high-level "Why" of the project. It defines the goals, user personas, and core value propositions. It is generally read-only for the coding agent but updated during planning phases.

## Project Goals

- **Goal 1 — Zero-hallucination document generation**: Eliminate AI fabrication from document production by making YAML the immutable source of truth and enforcing that every rendered word traces to a version-controlled field.
- **Goal 2 — Reproducible, audit-ready outputs**: Every render from the same YAML must produce byte-identical text outputs and text-layer-identical PDFs, enabling regulatory, scientific, and professional document use cases where repeatability matters.
- **Goal 3 — Human-governed AI workflow**: Keep humans in control at every phase gate. No pipeline phase auto-advances; the human reviews and approves each artifact before the next step begins.
- **Goal 4 — Hermetic build pipeline**: The rendering stack (Typst, Jinja2, bundled fonts) is fully self-contained — no system-level dependencies other than Python 3.10+ and uv.

## User Personas

- **Technical Document Author**: A researcher, engineer, or product manager who needs to produce high-quality structured documents (PRDs, scientific reports) that must be accurate and defensible. They use DDO to eliminate the risk of AI hallucination while still getting AI assistance for extraction and critique.
- **Compliance/Quality Reviewer**: A stakeholder who must verify that a produced document is accurate and traceable. They benefit from DDO's evidence_bank system, which ties every claim to a verifiable source.
- **AI Automation Engineer**: A developer building document pipelines who needs a reliable, deterministic rendering engine. They use `ddo/build.py` and the importable `validate()` gate in their own tooling.

## Core Value Proposition

DDO solves the "last mile" problem of AI document generation: the AI is useful for cognitive work (extraction, critique, refinement suggestions) but untrustworthy for writing final content. DDO separates these concerns:
1. AI extracts → writes to YAML with sentinel tokens for unresolvable fields
2. Human reviews YAML → fills sentinels, approves
3. DDO renders deterministically from human-approved YAML → PDF/HTML/MD

The result is a document the human can stand behind because they reviewed every data field that went into it.

## Success Metrics

- Test suite passes (78+) with 0 failures across unit and integration
- All renders from the same YAML input are byte-identical (HTML/MD) or text-layer-identical (PDF)
- Zero sentinel tokens (`[[DDO::REQUIRES_INPUT:`) in any rendered output (blocked by `validate()`)
- HTML renders are XSS-safe (autoescape confirmed by M4 integration test)
- Fixture promotion requires explicit human sign-off (`DDO_FIXTURE_SIGNOFF=1`)
