# Process Document: DDO v0.0.1 — Architect Interview & Draft PRD

**Generated:** 2026-06-27T10:45:00-07:00
**Session Focus:** Requirements interview for DDO v0.0.1 (deterministic rendering backbone) via `/hyper-architect`, producing `spec/active/Draft_PRD.md`.

## Problem Statement

The Deterministic Document Orchestrator (DDO) existed as a vision and a set of founding briefs in `PRDs/` but had no compiled specification ready for adversarial analysis or build execution. Before any code could be written, all open design decisions needed to be locked — from milestone scope and versioning to hermetic build strategy and determinism guarantees — through a structured requirements interview that grounded every decision in the existing codebase rather than conjecture.

## Starting State

At commit `436f24e` (`initial commit v0.0.0 - PRD documents and framework`), the repository contained:
- `PRDs/DETERMINISTIC_DOC_ORCHESTRATOR.md` (1363 lines) — the founding project brief with origin story (Project Aegis), full 5-phase pipeline spec, YAML schemas for `red_team_report.yaml` and `interview_log.yaml`, persona system, template generation spec, `build.py` reference implementation, and 15 open questions in §11.
- `PRDs/DDO_PRD.md` — a condensed PRD v0.0.2 locking four prior decisions (minimal-contract schema, YAML mutation-layer separation, Red Team reads Jinja2, Typst+Jinja2 formats).
- `PRDs/product_requirements_document_schema.yaml` and `PRDs/scientific_report_schema.yaml` — canonical schema definitions.
- Six template stubs in `PRDs/` (Typst `.typst` and Jinja2 `.jinja2` for both doc types in HTML/MD).
- Two persona stubs in `PRDs/` (`Product_Critic_Persona.md`, `Scientific_Reviewer_Persona.md`).
- `pyproject.toml` at `v0.0.0`, `requires-python = ">=3.10"`, ruff configured.
- `spec/compiled/` — empty (only `.gitkeep`); no architecture.yml, no SuperPRD, no MiniPRDs.
- A `.gitignore` with a latent defect: granular `spec/` and `tests/` rules were present, but the file had not yet been audited for conflicting wholesale ignores.

No `ddo/` source code existed. The HACF framework (`.agents/`) was the development toolchain; the DDO domain layer was unbuilt.

## Approach & Methodology

Spec-driven, following the HACF Phase 1 state machine defined in `.agents/skills/hyper-architect/SKILL.md`. The Architect agent conducted a **codebase-first** interview: every question was asked only after reading all available source material so that the interview resolved genuine unknowns rather than re-confirming facts already derivable from files. The pacing rule was one design decision per turn using `AskUserQuestion`, depth-first (resolve each decision fully before opening the next). The sequencing rationale was: scope and versioning first (most architecture-locking), then boundary and permission decisions (constrain the build), then novel-frontier decisions (AI-output handling). Output target was a complete SuperPRD following the schema in `AGENTS.md`.

## Steps Taken

1. **Loaded the skill and all source material.** Read `hyper-architect/SKILL.md` to load interview instructions, then read all seven files in `PRDs/`, then read `AGENTS.md` (SuperPRD/MiniPRD/hypergraph schemas + always-on coding rules), `CLAUDE.md`, `README.md`, `pyproject.toml`, `.agentignore`, and `.gitignore`. Reason: the codebase-first rule requires exhausting available context before asking the user anything. This step surfaced the latent `.gitignore` defect (lines 45–46: `/tests` and `/spec` wholesale ignores that override the granular rules below them).

2. **Phase 1 — Resolved scope and versioning (Q1).** Proposed a clean v0.0.1 / v0.0.2+ split: v0.0.1 = rendering backbone only (build.py + schemas + templates + ddo-ingest + ddo-render + tests); adversarial loop (ddo-red-team, ddo-interview, ddo-refine, ddo-run) deferred to v0.0.2+. User accepted the split but corrected the versioning label: "v0.0.1" not "v1" (matching the existing `v0.0.0` tag in `pyproject.toml`).

3. **Phase 1 — Resolved determinism contract (Q2).** Proposed byte-identical PDF as the default. User rejected: "No don't pin byte identical for typst. But allow for manual confirmation of byte identical output with the —timestamp argument. Default is wall clock." Resolved to: HTML/MD = byte-identical by default; PDF = content-identical by default (wall-clock timestamp); PDF byte-identical = opt-in via `--timestamp`. No PDF hash-equality regression gate.

4. **Phase 2 — Resolved directory layout + template name resolution (Q3).** Proposed `ddo/` with `schemas/`, `templates/typst/`, `templates/jinja2/`, `personas/`; template resolution rule `<T>.<F>` → `ddo/templates/typst/<T>.typst` (PDF) or `ddo/templates/jinja2/<T>.<F>.jinja2` (HTML/MD). User agreed with recommendation.

5. **Phase 2 — Resolved validation architecture (Q4).** Proposed `build.py` as the single validation gate (3-check sequence: contract → evidence-ref integrity → unfilled-input scan); `ddo-render` skill as a thin wrapper that only derives paths and invokes `build.py`. User agreed with recommendation.

6. **Phase 2 — Resolved output path convention (Q5).** Proposed `Documents/<meta.date>_<meta.doc_type>_<title-slug>/output/<slug>.<ext>` (gitignored, skill computes paths, `build.py` stays path-ignorant). User agreed with recommendation.

7. **Phase 2 — Resolved Typst invocation strategy (Q6).** Proposed hermetic `typst` Python package (in-process, PEP 723 `# /// script` dep declaration) rather than system Typst CLI subprocess, removing the "install Typst" prerequisite. User agreed with recommendation.

8. **Phase 3 — Resolved ingest protection behaviors (Q7).** Proposed no-overwrite protection (refuse if output path exists) + local-files-only constraint (no network ingestion). User agreed with recommendation.

9. **Phase 3 — Resolved Candidate Artifact protocol (Q8).** Proposed `ddo-ingest` as the sole Candidate Artifact (non-deterministic AI output); content human-verified before promotion to `tests/fixtures/`; regression tests assert only contract-validity + render-ability, never content equality. User agreed with recommendation.

10. **Phase 4 — Confirmed readiness and wrote the Draft PRD.** Presented an 8-decision summary and an `AskUserQuestion` gate ("Generate the draft?"). User confirmed. Wrote `spec/active/Draft_PRD.md` following the SuperPRD schema from `AGENTS.md`: 8 sections (Introduction & Goals, Confidence Mandate, Scope, User Stories, Technical Specifications, Negative Constraints, Risks & Mitigation, Success Metrics) plus a Decision Log appendix covering all 8 locked decisions.

## Key Decisions & Rationale

| Decision | Alternatives Considered | Reason Chosen |
|---|---|---|
| Scope = v0.0.1 rendering backbone only; adversarial loop deferred to v0.0.2+ | Single milestone ("v1") covering everything | Adversarial loop has no value until the backbone is trustworthy; split keeps each milestone small and executable |
| Versioning labels: v0.0.1, v0.0.2, v0.0.3 | "v1", "v2", "v3" | Matches the existing v0.0.0 tag in pyproject.toml; semantic versioning patch increments for pre-1.0 milestones |
| PDF determinism = content-identical by default (wall-clock); byte-identical via `--timestamp` opt-in | Byte-identical by default | Routine builds don't need byte-identical PDFs; the flag enables verification when needed without friction in the common case |
| HTML/MD = byte-identical by default | Allow clock drift | Jinja2 templates have no time dependency; byte-identical is free and makes diffing trivial |
| `typst` Python package (in-process, PEP 723) | System Typst CLI subprocess | Removes "install Typst" as a prerequisite; hermetic via PEP 723 inline dep declaration; timestamp control via `typst.compile(timestamp=)` |
| `build.py` as single validation gate (3-check sequence) | Validation split across skill and build.py | Single gate eliminates drift between CLI and skill execution paths; skill becomes a thin wrapper |
| `ddo-ingest` = sole Candidate Artifact; content human-verified | Auto-promote all AI output | Ingest is the only non-deterministic step; all other steps are deterministic transforms of YAML input |
| No-overwrite + local-files-only for ddo-ingest | Auto-overwrite; allow URL ingestion | Prevents accidental data loss; prevents network-side effects in a local-only tool |

## Artifacts Created / Modified

| Artifact | Path | Change |
|---|---|---|
| Draft PRD (SuperPRD format) | `spec/active/Draft_PRD.md` | Created |

## Results & Outcomes

- All 15 open questions from `PRDs/DETERMINISTIC_DOC_ORCHESTRATOR.md §11` resolved or explicitly deferred: 8 locked through the interview, 7 scoped to v0.0.2+ (adversarial loop, multi-page HTML, template generation, DOCX/Pandoc, network ingestion, etc.).
- `spec/active/Draft_PRD.md` is a complete, execution-ready SuperPRD covering: v0.0.1 scope boundaries, 6 atomic user stories (US-001–US-006), CLI contract (`uv run ddo/build.py --data --template --format --output [--timestamp]`), PEP 723 runtime deps, 6 candidate MiniPRDs, 9 negative constraints, 5 risks with mitigations, 5 success metrics.
- One pre-build risk surfaced and logged (Risk #1): `.gitignore` lines 45–46 wholesale-ignore `/tests` and `/spec`, which would prevent v0.0.1 regression tests and specs from being committed. Mitigation: fix `.gitignore` before build phase begins.
- Confidence score: **8/10**. Three implementation-level unknowns deferred to build phase: Typst Python-package timestamp API surface; template-schema field alignment; PDF binary git storage strategy.

## How to Reproduce

Prerequisite state: a clean checkout at commit `436f24e` with all files in `PRDs/` present; `spec/active/` empty (only `.gitkeep`); no `ddo/` source code.

1. In a fresh conversation, run `/hyper-architect using all the files in @PRDs/`.
2. The skill reads `hyper-architect/SKILL.md`, then reads all seven `PRDs/` files, then reads `AGENTS.md`, `CLAUDE.md`, `README.md`, `pyproject.toml`, `.agentignore`, `.gitignore` before asking the first question.
3. **Q1 (scope/versioning):** accept the v0.0.1/v0.0.2+ split; correct "v1" → "v0.0.1" to match the existing pyproject.toml tag.
4. **Q2 (determinism):** reject byte-identical PDF as default; specify wall-clock default + `--timestamp` opt-in for byte-identical.
5. **Q3–Q8:** accept the recommended answers for directory layout, validation gate architecture, output path convention, Typst hermetic package, ingest protections, and Candidate Artifact protocol.
6. Confirm the draft generation gate when presented. Expected output: `spec/active/Draft_PRD.md` written with 8 SuperPRD sections + Decision Log appendix.

Gotchas / order-dependencies:
- The skill must read the actual `.gitignore` (not assume its contents) to accurately report the pre-build risk.
- Do not auto-advance to `/hyper-redteam` in the same conversation — Red Team must not see Architect's history (required isolation per AGENTS.md). Start a new conversation.
- If the user accepts all recommendations except Q1/Q2, the transcript matches this reproduction exactly; diverging on other questions changes the Draft PRD content.

## Patterns & Lessons

- **Codebase-first prevents redundant questions:** reading `.gitignore` before Q1 surfaced the `/tests`+`/spec` defect immediately, so it could be logged as Risk #1 in the Draft PRD without a separate investigation pass during the build phase.
- **One question per turn is the discipline:** each turn's `AskUserQuestion` forces the agent to commit to a specific recommendation before exposing it to the user, eliminating hedge-phrasing and producing a clear decision record.
- **Scope precision is multiplicative:** locking "v0.0.1 = backbone only" in Q1 made every subsequent question simpler — it eliminated entire clusters of options (network ingestion, adversarial loop, multi-page HTML) from subsequent turns.
- **PyPI package over CLI subprocess:** the `typst` Python package makes the hermetic build story clean — no "install Typst" prerequisite, no subprocess PATH dependency, no version drift between system CLI and in-process renderer.
- **Candidate Artifact protocol is the conceptual linchpin:** recognizing `ddo-ingest` as the sole non-deterministic step and routing it through human verification rather than machine assertion is what makes DDO's zero-hallucination invariant enforceable. Every other step is a deterministic transform.
